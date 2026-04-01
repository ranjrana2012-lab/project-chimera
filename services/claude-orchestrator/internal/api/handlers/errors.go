package handlers

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/project-chimera/claude-orchestrator/internal/state"
)

// ErrorHandler handles error-related endpoints
type ErrorHandler struct {
	store *state.HybridStore
	ctx   context.Context
}

// NewErrorHandler creates a new error handler
func NewErrorHandler(store *state.HybridStore, ctx context.Context) *ErrorHandler {
	return &ErrorHandler{
		store: store,
		ctx:   ctx,
	}
}

// List returns all active errors
func (h *ErrorHandler) List(c *gin.Context) {
	errors, err := h.store.GetErrors()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"errors": errors,
		"count":  len(errors),
	})
}

// Get returns a specific error
func (h *ErrorHandler) Get(c *gin.Context) {
	errorID := c.Param("error_id")

	errors, _ := h.store.GetErrors()
	for _, err := range errors {
		if err.ID == errorID {
			c.JSON(http.StatusOK, gin.H{
				"error": err,
			})
			return
		}
	}

	c.JSON(http.StatusNotFound, gin.H{"error": "Error not found"})
}

// ResolveRequest represents an error resolution request
type ResolveRequest struct {
	Resolution string `json:"resolution" binding:"required"`
	ResolvedBy string `json:"resolved_by" binding:"required"`
}

// Resolve marks an error as resolved
func (h *ErrorHandler) Resolve(c *gin.Context) {
	errorID := c.Param("error_id")

	var req ResolveRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	errors, _ := h.store.GetErrors()
	for _, e := range errors {
		if e.ID == errorID {
			now := time.Now()
			e.Status = state.ErrorStatusResolved
			e.ResolvedBy = req.ResolvedBy
			e.ResolvedAt = &now

			if err := h.store.RemoveError(errorID); err != nil {
				c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
				return
			}

			// Log resolution
			_ = h.store.AddLearning(fmt.Sprintf("# Error Resolved: %s\nResolution: %s\nResolved by: %s\nResolved at: %s",
				errorID, req.Resolution, req.ResolvedBy, now.Format("2006-01-02T15:04:05Z")))

			c.JSON(http.StatusOK, gin.H{
				"message":  "Error resolved",
				"error_id": errorID,
			})
			return
		}
	}

	c.JSON(http.StatusNotFound, gin.H{"error": "Error not found"})
}

// History returns error history
func (h *ErrorHandler) History(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"history": []interface{}{},
		"message": "Error history not yet implemented",
	})
}
