package handlers

import (
	"context"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/project-chimera/claude-orchestrator/internal/mode"
	"github.com/project-chimera/claude-orchestrator/internal/state"
)

// ModeHandler handles mode-related endpoints
type ModeHandler struct {
	modeCtrl  *mode.Controller
	ctx       context.Context
}

// NewModeHandler creates a new mode handler
func NewModeHandler(modeCtrl *mode.Controller, ctx context.Context) *ModeHandler {
	return &ModeHandler{
		modeCtrl: modeCtrl,
		ctx:      ctx,
	}
}

// GetCurrent returns the current operational mode
func (h *ModeHandler) GetCurrent(c *gin.Context) {
	mode := h.modeCtrl.GetCurrentMode()
	c.JSON(http.StatusOK, gin.H{
		"mode": mode.String(),
	})
}

// TransitionRequest represents a mode transition request
type TransitionRequest struct {
	ToMode  state.Mode `json:"to_mode" binding:"required"`
	Reason  string    `json:"reason"`
	Trigger string    `json:"trigger"`
}

// Transition attempts to transition to a new mode
func (h *ModeHandler) Transition(c *gin.Context) {
	var req TransitionRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if err := h.modeCtrl.TransitionTo(req.ToMode, req.Reason, req.Trigger); err != nil {
		c.JSON(http.StatusForbidden, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message":  "Mode transition successful",
		"new_mode": req.ToMode.String(),
	})
}

// History returns mode transition history
func (h *ModeHandler) History(c *gin.Context) {
	history := h.modeCtrl.GetTransitionHistory()

	c.JSON(http.StatusOK, gin.H{
		"history": history,
	})
}

// OverrideRequest represents an emergency override request
type OverrideRequest struct {
	Mode   state.Mode `json:"mode" binding:"required"`
	Reason string     `json:"reason" binding:"required"`
}

// Override forces a mode transition (emergency use only)
func (h *ModeHandler) Override(c *gin.Context) {
	var req OverrideRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if err := h.modeCtrl.ForceTransition(req.Mode, req.Reason); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message":  "Mode override successful",
		"current":  req.Mode.String(),
	})
}
