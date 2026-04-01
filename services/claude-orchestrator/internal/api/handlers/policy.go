package handlers

import (
	"context"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/project-chimera/claude-orchestrator/internal/mode"
)

// PolicyHandler handles policy endpoints
type PolicyHandler struct {
	modeCtrl *mode.Controller
	ctx      context.Context
}

// NewPolicyHandler creates a new policy handler
func NewPolicyHandler(modeCtrl *mode.Controller, ctx context.Context) *PolicyHandler {
	return &PolicyHandler{
		modeCtrl: modeCtrl,
		ctx:      ctx,
	}
}

// List returns all policies
func (h *PolicyHandler) List(c *gin.Context) {
	policy := h.modeCtrl.GetPolicy()

	c.JSON(http.StatusOK, gin.H{
		"policies": map[string]interface{}{
			"allow_auto_control":     policy.AllowAutoControl,
			"allow_auto_escalate":    policy.AllowAutoEscalate,
			"require_approval_for":   policy.RequireApprovalFor,
			"block_transitions_from": policy.BlockTransitionsFrom,
		},
	})
}

// EvaluateRequest represents an action evaluation request
type EvaluateRequest struct {
	Type   string      `json:"type" binding:"required"`
	Action interface{} `json:"action" binding:"required"`
}

// Evaluate evaluates an action against policies
func (h *PolicyHandler) Evaluate(c *gin.Context) {
	var req EvaluateRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	allowed, reason := h.modeCtrl.EvaluateAction(req.Action)

	c.JSON(http.StatusOK, gin.H{
		"allowed": allowed,
		"reason":  reason,
	})
}

// Update updates a policy
func (h *PolicyHandler) Update(c *gin.Context) {
	policyID := c.Param("policy_id")
	var policy interface{}
	if err := c.ShouldBindJSON(&policy); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message":  "Policy updated",
		"policy_id": policyID,
		"policy":   policy,
	})
}

// Reload reloads policies from configuration
func (h *PolicyHandler) Reload(c *gin.Context) {
	err := h.modeCtrl.ReloadPolicies()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Policies reloaded",
	})
}
