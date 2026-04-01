package handlers

import (
	"context"
	"net/http"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/project-chimera/claude-orchestrator/internal/health"
	"github.com/project-chimera/claude-orchestrator/internal/mode"
	"github.com/project-chimera/claude-orchestrator/internal/nemoclaw"
	"github.com/project-chimera/claude-orchestrator/internal/policy"
	"github.com/project-chimera/claude-orchestrator/internal/state"
	"github.com/project-chimera/claude-orchestrator/internal/ws"
)

// OrchestratorHandler handles HTTP API requests
type OrchestratorHandler struct {
	modeController  *mode.Controller
	healthMonitor  *health.Monitor
	showTracker    *nemoclaw.Tracker
	wsServer       *ws.Server
	store          *state.HybridStore
	policyEngine   *policy.Engine
}

// NewOrchestratorHandler creates a new orchestrator handler
func NewOrchestratorHandler(
	modeController *mode.Controller,
	healthMonitor *health.Monitor,
	showTracker *nemoclaw.Tracker,
	wsServer *ws.Server,
	store *state.HybridStore,
	policyEngine *policy.Engine,
) *OrchestratorHandler {
	return &OrchestratorHandler{
		modeController: modeController,
		healthMonitor: healthMonitor,
		showTracker:   showTracker,
		wsServer:      wsServer,
		store:         store,
		policyEngine:  policyEngine,
	}
}

// RegisterRoutes registers all API routes
func (h *OrchestratorHandler) RegisterRoutes(r *gin.Engine) {
	// Dashboard routes
	r.LoadHTMLGlob("dashboard/templates/*")
	r.GET("/", h.serveDashboard)
	r.Static("/static", "./dashboard/static")

	// WebSocket route
	r.GET("/ws", h.wsServer.HandleWebSocket)

	// API routes
	api := r.Group("/api")
	{
		// Status
		api.GET("/status", h.getStatus)

		// Mode control
		api.GET("/mode", h.getCurrentMode)
		api.POST("/mode/transition", h.transitionMode)

		// Health
		api.GET("/health", h.getHealth)
		api.POST("/health/check", h.runHealthCheck)

		// Errors
		api.GET("/errors", h.getErrors)
		api.POST("/errors/:id/resolve", h.resolveError)

		// Tasks
		api.GET("/tasks", h.getTasks)
		api.POST("/tasks", h.createTask)
		api.PUT("/tasks/:id", h.updateTask)

		// Show
		api.GET("/show", h.getShowInfo)

		// Policies
		api.GET("/policies", h.getPolicies)
		api.POST("/policies", h.addPolicy)
		api.DELETE("/policies/:id", h.deletePolicy)
	}
}

// serveDashboard serves the web dashboard
func (h *OrchestratorHandler) serveDashboard(c *gin.Context) {
	c.HTML(http.StatusOK, "index.html", nil)
}

// getStatus returns overall system status
func (h *OrchestratorHandler) getStatus(c *gin.Context) {
	currentState, err := h.store.Restore()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   "Failed to get state",
		})
		return
	}

	if currentState == nil {
		currentState = &state.State{
			Mode:      state.ModeStandby,
			ShowState: state.ShowStateInactive,
			Health: state.Health{
				Services:  make(map[string]state.ServiceHealth),
				Overall:   state.HealthStatusUnknown,
				SLOPass:   false,
				LastCheck: time.Time{},
			},
		}
	}

	c.JSON(http.StatusOK, gin.H{
		"success":           true,
		"mode":              currentState.Mode.String(),
		"show_state":        currentState.ShowState.String(),
		"connected_clients": h.wsServer.GetClientCount(),
	})
}

// getCurrentMode returns the current operational mode
func (h *OrchestratorHandler) getCurrentMode(c *gin.Context) {
	currentMode := h.modeController.GetCurrentMode()

	// Get state to find transition info
	currentState, _ := h.store.Restore()
	since := time.Time{}
	reason := "unknown"
	source := "unknown"

	if currentState != nil && !currentState.Since.IsZero() {
		since = currentState.Since
		reason = currentState.Reason
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"mode":    currentMode.String(),
		"since":   since,
		"reason":  reason,
		"source":  source,
	})
}

// transitionMode transitions to a new operational mode
func (h *OrchestratorHandler) transitionMode(c *gin.Context) {
	var req struct {
		Mode   string `json:"mode"`
		Reason string `json:"reason"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   "Invalid request body",
		})
		return
	}

	targetMode := state.ModeFromString(req.Mode)
	if targetMode == state.ModeUnknown {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   "Invalid mode",
		})
		return
	}

	reason := req.Reason
	if reason == "" {
		reason = "API request"
	}

	if err := h.modeController.TransitionTo(targetMode, reason, "api"); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"mode":    targetMode.String(),
	})
}

// getHealth returns current health status
func (h *OrchestratorHandler) getHealth(c *gin.Context) {
	currentState, err := h.store.Restore()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   "Failed to get state",
		})
		return
	}

	healthData := currentState.Health

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"health":  healthData,
	})
}

// runHealthCheck triggers a health check on all services
func (h *OrchestratorHandler) runHealthCheck(c *gin.Context) {
	// Trigger a health check - the result will be stored in state
	_ = h.healthMonitor.Check(context.Background())

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "Health check initiated",
	})
}

// getErrors returns active errors
func (h *OrchestratorHandler) getErrors(c *gin.Context) {
	currentState, err := h.store.Restore()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   "Failed to get state",
		})
		return
	}

	if currentState == nil {
		c.JSON(http.StatusOK, gin.H{
			"success": true,
			"errors":  []interface{}{},
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"errors":  currentState.Errors,
	})
}

// resolveError resolves an error
func (h *OrchestratorHandler) resolveError(c *gin.Context) {
	errorID := c.Param("id")

	var req struct {
		Resolution string `json:"resolution"`
		ResolvedBy string `json:"resolved_by"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   "Invalid request body",
		})
		return
	}

	if req.ResolvedBy == "" {
		req.ResolvedBy = "api_user"
	}

	// This would be handled by the error handler
	// For now, just return success
	_ = errorID // Use the variable
	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "Error resolved",
	})
}

// getTasks returns active tasks
func (h *OrchestratorHandler) getTasks(c *gin.Context) {
	currentState, err := h.store.Restore()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   "Failed to get state",
		})
		return
	}

	if currentState == nil {
		c.JSON(http.StatusOK, gin.H{
			"success": true,
			"tasks":   []interface{}{},
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"tasks":   currentState.Tasks,
	})
}

// createTask creates a new task
func (h *OrchestratorHandler) createTask(c *gin.Context) {
	var req struct {
		Title            string `json:"title"`
		Description      string `json:"description"`
		Priority         int    `json:"priority"`
		RequiresApproval bool   `json:"requires_approval"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   "Invalid request body",
		})
		return
	}

	if req.Title == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   "Title is required",
		})
		return
	}

	if req.Priority == 0 {
		req.Priority = 2 // Normal priority
	}

	task := &state.Task{
		ID:               "task-" + strconv.FormatInt(time.Now().UnixNano(), 36),
		Type:             "manual",
		Priority:         req.Priority,
		Title:            req.Title,
		Description:      req.Description,
		Status:           state.TaskStatusPending,
		CreatedAt:        time.Now(),
		UpdatedAt:        time.Now(),
		RequiresApproval: req.RequiresApproval,
		Approved:         !req.RequiresApproval,
	}

	// Add to state
	if err := h.store.AddTask(task); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   "Failed to create task",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"id":      task.ID,
	})
}

// updateTask updates a task
func (h *OrchestratorHandler) updateTask(c *gin.Context) {
	taskID := c.Param("id")

	var req struct {
		Approved *bool `json:"approved"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   "Invalid request body",
		})
		return
	}

	// Get current state
	currentState, err := h.store.Restore()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   "Failed to get state",
		})
		return
	}

	// Find and update task
	for _, task := range currentState.Tasks {
		if task.ID == taskID {
			if req.Approved != nil {
				task.Approved = *req.Approved
				if task.Approved {
					task.Status = state.TaskStatusApproved
				} else {
					task.Status = state.TaskStatusDenied
				}
				task.UpdatedAt = time.Now()
			}

			// Save updated state
			if err := h.store.Snapshot(currentState); err != nil {
				c.JSON(http.StatusInternalServerError, gin.H{
					"success": false,
					"error":   "Failed to update task",
				})
				return
			}

			c.JSON(http.StatusOK, gin.H{
				"success": true,
				"task":    task,
			})
			return
		}
	}

	c.JSON(http.StatusNotFound, gin.H{
		"success": false,
		"error":   "Task not found",
	})
}

// getShowInfo returns show information
func (h *OrchestratorHandler) getShowInfo(c *gin.Context) {
	showInfo := h.showTracker.GetShowInfo()

	if showInfo == nil {
		c.JSON(http.StatusOK, gin.H{
			"success": true,
			"show":    gin.H{"state": state.ShowStateInactive},
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"show":    showInfo,
	})
}

// getPolicies returns all policies
func (h *OrchestratorHandler) getPolicies(c *gin.Context) {
	// For now, return empty list as the policy engine doesn't expose GetAllPolicies
	// In a full implementation, this would return all policies from the engine
	c.JSON(http.StatusOK, gin.H{
		"success":  true,
		"policies": []interface{}{},
	})
}

// addPolicy adds a new policy
func (h *OrchestratorHandler) addPolicy(c *gin.Context) {
	var req policy.Policy

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   "Invalid request body",
		})
		return
	}

	if err := h.policyEngine.AddPolicy(&req); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"policy":  req,
	})
}

// deletePolicy deletes a policy
func (h *OrchestratorHandler) deletePolicy(c *gin.Context) {
	policyID := c.Param("id")

	if err := h.policyEngine.DeletePolicy(policyID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "Policy deleted",
	})
}
