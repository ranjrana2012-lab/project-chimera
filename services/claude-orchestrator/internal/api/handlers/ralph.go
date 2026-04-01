package handlers

import (
	"context"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/project-chimera/claude-orchestrator/internal/ralph"
	"github.com/project-chimera/claude-orchestrator/internal/state"
)

// RalphHandler handles Ralph Loop endpoints
type RalphHandler struct {
	store         *state.HybridStore
	engine        *ralph.Engine
	queueManager  *ralph.QueueManager
	learnings     *ralph.LearningsSystem
	gsd           *ralph.GSDOrchestrator
	ctx           context.Context
}

// NewRalphHandler creates a new Ralph handler
func NewRalphHandler(store *state.HybridStore, ctx context.Context) *RalphHandler {
	cfg := ralph.Config{
		StateDir:      "/state/ralph",
		MaxIterations: 0, // Unlimited
		CheckInterval: 5 * 1000000000, // 5 seconds in nanoseconds
	}

	engine, _ := ralph.NewEngine(store, cfg)
	queueManager := ralph.NewQueueManager(store, ctx)
	learnings := ralph.NewLearningsSystem("/state/ralph")
	gsd := ralph.NewGSDOrchestrator(store, ctx)

	return &RalphHandler{
		store:        store,
		engine:       engine,
		queueManager: queueManager,
		learnings:    learnings,
		gsd:          gsd,
		ctx:          ctx,
	}
}

// Status returns Ralph Loop status
func (h *RalphHandler) Status(c *gin.Context) {
	status := h.engine.GetStatus()

	c.JSON(http.StatusOK, gin.H{
		"active":          status.Active,
		"iteration":       status.Iteration,
		"max_iterations":  status.MaxIterations,
		"paused":          status.Paused,
		"last_action":     status.LastAction,
		"last_result":     status.LastResult,
		"progress_streak": status.ProgressStreak,
	})
}

// Pause pauses the Ralph Loop
func (h *RalphHandler) Pause(c *gin.Context) {
	h.engine.Pause()

	c.JSON(http.StatusOK, gin.H{
		"message": "Ralph Loop paused",
	})
}

// Resume resumes the Ralph Loop
func (h *RalphHandler) Resume(c *gin.Context) {
	h.engine.Resume()

	c.JSON(http.StatusOK, gin.H{
		"message": "Ralph Loop resumed",
	})
}

// Iteration triggers a single iteration
func (h *RalphHandler) Iteration(c *gin.Context) {
	// This is handled automatically by the engine
	c.JSON(http.StatusOK, gin.H{
		"message": "Iteration triggered",
	})
}

// Queue returns the task queue
func (h *RalphHandler) Queue(c *gin.Context) {
	queue := h.queueManager.GetQueue()

	c.JSON(http.StatusOK, gin.H{
		"queue": queue,
		"size":  len(queue),
	})
}

// CreateTaskRequest represents a task creation request
type CreateTaskRequest struct {
	Type             string `json:"type" binding:"required"`
	Title            string `json:"title" binding:"required"`
	Description      string `json:"description"`
	Priority         int    `json:"priority"`
	MaxRetries       int    `json:"max_retries"`
	RequiresApproval bool   `json:"requires_approval"`
}

// CreateTask creates a new task in the Ralph Loop queue
func (h *RalphHandler) CreateTask(c *gin.Context) {
	var req CreateTaskRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	task := &state.Task{
		Type:             req.Type,
		Title:            req.Title,
		Description:      req.Description,
		Priority:         req.Priority,
		MaxRetries:       req.MaxRetries,
		RequiresApproval: req.RequiresApproval,
		Approved:         !req.RequiresApproval,
	}

	if err := h.queueManager.Enqueue(task); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"message": "Task created",
		"task":    task,
	})
}

// ApproveTask approves a task for execution
func (h *RalphHandler) ApproveTask(c *gin.Context) {
	taskID := c.Param("task_id")

	if err := h.queueManager.ApproveTask(taskID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Task approved",
		"task_id": taskID,
	})
}

// DenyTask denies a task
func (h *RalphHandler) DenyTask(c *gin.Context) {
	taskID := c.Param("task_id")

	if err := h.queueManager.DenyTask(taskID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Task denied",
		"task_id": taskID,
	})
}

// PrioritizeTask updates task priority
func (h *RalphHandler) PrioritizeTask(c *gin.Context) {
	taskID := c.Param("task_id")

	var req struct {
		Priority int `json:"priority" binding:"required"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if err := h.queueManager.PrioritizeTask(taskID, req.Priority); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Task prioritized",
		"task_id": taskID,
		"priority": req.Priority,
	})
}

// Learnings returns all learnings
func (h *RalphHandler) Learnings(c *gin.Context) {
	learnings, err := h.learnings.GetLearnings(nil)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"learnings": learnings,
		"count":    len(learnings),
	})
}

// SearchLearnings searches for learnings
func (h *RalphHandler) SearchLearnings(c *gin.Context) {
	query := c.Query("q")
	if query == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Query parameter 'q' is required"})
		return
	}

	results, err := h.learnings.SearchLearnings(query)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"results": results,
		"count":   len(results),
	})
}

// GetTags returns all learning tags
func (h *RalphHandler) GetTags(c *gin.Context) {
	tags, err := h.learnings.GetTags()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"tags": tags,
	})
}

// GetStatistics returns learning statistics
func (h *RalphHandler) GetStatistics(c *gin.Context) {
	stats, err := h.learnings.GetStatistics()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, stats)
}

// CreateGoal creates a new goal
func (h *RalphHandler) CreateGoal(c *gin.Context) {
	var goal ralph.Goal
	if err := c.ShouldBindJSON(&goal); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if err := h.gsd.CreateGoal(&goal); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"message": "Goal created",
		"goal_id": goal.ID,
	})
}

// CreateScenario creates a new scenario
func (h *RalphHandler) CreateScenario(c *gin.Context) {
	goalID := c.Param("goal_id")

	var scenario ralph.Scenario
	if err := c.ShouldBindJSON(&scenario); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if err := h.gsd.CreateScenario(goalID, &scenario); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"message":    "Scenario created",
		"scenario_id": scenario.ID,
	})
}

// CreateDeliverable creates a new deliverable
func (h *RalphHandler) CreateDeliverable(c *gin.Context) {
	scenarioID := c.Param("scenario_id")

	var deliverable ralph.Deliverable
	if err := c.ShouldBindJSON(&deliverable); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if err := h.gsd.CreateDeliverable(scenarioID, &deliverable); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"message":        "Deliverable created",
		"deliverable_id": deliverable.ID,
	})
}
