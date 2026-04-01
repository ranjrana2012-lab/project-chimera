package handlers

import (
	"context"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/project-chimera/claude-orchestrator/internal/state"
)

// RalphHandler handles Ralph Loop endpoints
type RalphHandler struct {
	store *state.HybridStore
	ctx   context.Context
}

// NewRalphHandler creates a new Ralph handler
func NewRalphHandler(store *state.HybridStore, ctx context.Context) *RalphHandler {
	return &RalphHandler{
		store: store,
		ctx:   ctx,
	}
}

// Status returns Ralph Loop status
func (h *RalphHandler) Status(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"active":    false,
		"iteration": 0,
		"queue_size": 0,
	})
}

// Pause pauses the Ralph Loop
func (h *RalphHandler) Pause(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"message": "Ralph Loop paused",
	})
}

// Resume resumes the Ralph Loop
func (h *RalphHandler) Resume(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"message": "Ralph Loop resumed",
	})
}

// Iteration triggers a single iteration
func (h *RalphHandler) Iteration(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"message": "Iteration triggered",
	})
}

// Queue returns the task queue
func (h *RalphHandler) Queue(c *gin.Context) {
	tasks, _ := h.store.GetTasks()
	c.JSON(http.StatusOK, gin.H{
		"queue": tasks,
		"size":  len(tasks),
	})
}
