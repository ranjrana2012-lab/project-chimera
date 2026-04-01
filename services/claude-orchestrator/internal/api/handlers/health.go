package handlers

import (
	"context"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/project-chimera/claude-orchestrator/internal/health"
	"github.com/project-chimera/claude-orchestrator/internal/state"
)

// HealthHandler handles health-related endpoints
type HealthHandler struct {
	store      *state.HybridStore
	healthMon  *health.Monitor
	ctx        context.Context
}

// NewHealthHandler creates a new health handler
func NewHealthHandler(store *state.HybridStore, healthMon *health.Monitor, ctx context.Context) *HealthHandler {
	return &HealthHandler{
		store:     store,
		healthMon: healthMon,
		ctx:       ctx,
	}
}

// Live returns liveness status
func (h *HealthHandler) Live(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"status": "alive"})
}

// Ready returns readiness status
func (h *HealthHandler) Ready(c *gin.Context) {
	// Check if critical dependencies are ready
	// TODO: Add actual readiness checks
	c.JSON(http.StatusOK, gin.H{"status": "ready"})
}

// Status returns detailed status
func (h *HealthHandler) Status(c *gin.Context) {
	currentState, _ := h.store.Restore()
	if currentState == nil {
		currentState = &state.State{}
	}

	c.JSON(http.StatusOK, gin.H{
		"mode":           currentState.Mode,
		"since":          currentState.Since,
		"health":         currentState.Health,
		"show_state":     currentState.ShowState,
		"pending_tasks":  currentState.Tasks,
		"active_errors":  currentState.Errors,
		"last_updated":   currentState.LastUpdated,
	})
}

// SLO returns SLO gate status
func (h *HealthHandler) SLO(c *gin.Context) {
	report := h.healthMon.GetStatus()
	c.JSON(http.StatusOK, gin.H{
		"pass":     report.SLOPass,
		"details":  report.SLODetails,
		"timestamp": report.Timestamp,
	})
}

// Check triggers a health check
func (h *HealthHandler) Check(c *gin.Context) {
	report := h.healthMon.Check(h.ctx)
	c.JSON(http.StatusOK, report)
}

// Report returns the latest health report
func (h *HealthHandler) Report(c *gin.Context) {
	report := h.healthMon.GetStatus()
	c.JSON(http.StatusOK, report)
}

// History returns historical health data
func (h *HealthHandler) History(c *gin.Context) {
	// TODO: Implement historical data retrieval
	c.JSON(http.StatusOK, gin.H{
		"history": []interface{}{},
		"message": "Historical data not yet implemented",
	})
}

// Service returns health of a specific service
func (h *HealthHandler) Service(c *gin.Context) {
	serviceName := c.Param("service")
	report := h.healthMon.GetStatus()

	if serviceHealth, ok := report.Services[serviceName]; ok {
		c.JSON(http.StatusOK, serviceHealth)
	} else {
		c.JSON(http.StatusNotFound, gin.H{
			"error": "Service not found",
		})
	}
}
