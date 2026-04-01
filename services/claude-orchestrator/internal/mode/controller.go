package mode

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/project-chimera/claude-orchestrator/internal/state"
)

// TransitionRecord represents a single mode transition event
type TransitionRecord struct {
	From      state.Mode    `json:"from"`
	To        state.Mode    `json:"to"`
	Timestamp time.Time     `json:"timestamp"`
	Reason    string        `json:"reason"`
	Forced    bool          `json:"forced"`
}

// Controller manages operational mode transitions
type Controller struct {
	store             *state.HybridStore
	currentMode       state.Mode
	mu                sync.RWMutex
	ctx               context.Context
	cancel            context.CancelFunc
	showTracker       *ShowTracker
	policyEngine      *PolicyEngine
	transitionHistory []TransitionRecord
	nemoClawURL       string
}

// NewController creates a new mode controller
func NewController(store *state.HybridStore, nemoclawURL string) (*Controller, error) {
	ctx, cancel := context.WithCancel(context.Background())

	showTracker, err := NewShowTracker(nemoclawURL)
	if err != nil {
		cancel()
		return nil, fmt.Errorf("failed to create show tracker: %w", err)
	}

	return &Controller{
		store:             store,
		currentMode:       state.ModeStandby,
		showTracker:       showTracker,
		policyEngine:      NewPolicyEngine(),
		ctx:               ctx,
		cancel:            cancel,
		transitionHistory: []TransitionRecord{},
		nemoClawURL:       nemoclawURL,
	}, nil
}

// Start begins the mode controller loop
func (c *Controller) Start() {
	// Restore previous state
	if previousState, err := c.store.Restore(); err == nil && previousState != nil {
		c.currentMode = previousState.Mode
	}

	// Start show state tracking
	go c.showTracker.Start(c.ctx)

	// Enter main loop
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			c.checkAndAutoTransition()
		case <-c.ctx.Done():
			return
		}
	}
}

// Stop stops the mode controller
func (c *Controller) Stop() {
	c.cancel()
	c.showTracker.Stop()
}

// GetCurrentMode returns the current operational mode
func (c *Controller) GetCurrentMode() state.Mode {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.currentMode
}

// TransitionTo attempts to transition to a new mode
func (c *Controller) TransitionTo(newMode state.Mode, reason string, trigger string) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	// Check if transition is allowed by policy
	if !c.policyEngine.CanTransition(c.currentMode, newMode, trigger) {
		return fmt.Errorf("transition from %s to %s not allowed by policy", c.currentMode, newMode)
	}

	// Check if approval is required
	if c.policyEngine.RequiresApprovalForTransition(c.currentMode, newMode) {
		return fmt.Errorf("transition from %s to %s requires approval", c.currentMode, newMode)
	}

	// Perform transition
	oldMode := c.currentMode
	c.currentMode = newMode

	// Update state
	currentState, _ := c.store.Restore()
	if currentState == nil {
		currentState = &state.State{}
	}

	currentState.Mode = newMode
	currentState.Since = time.Now()
	currentState.Previous = oldMode
	currentState.Reason = reason
	currentState.LastUpdated = time.Now()

	if err := c.store.Snapshot(currentState); err != nil {
		// Rollback
		c.currentMode = oldMode
		return fmt.Errorf("failed to persist state: %w", err)
	}

	// Add to transition history
	c.transitionHistory = append(c.transitionHistory, TransitionRecord{
		From:      oldMode,
		To:        newMode,
		Timestamp: time.Now(),
		Reason:    reason,
		Forced:    false,
	})

	// Log transition
	c.store.AddLearning(fmt.Sprintf("Mode transition: %s → %s (reason: %s, trigger: %s)",
		oldMode, newMode, reason, trigger))

	return nil
}

// ForceTransition forces a mode transition (for emergency overrides)
func (c *Controller) ForceTransition(newMode state.Mode, reason string) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	oldMode := c.currentMode
	c.currentMode = newMode

	// Update state
	currentState, _ := c.store.Restore()
	if currentState == nil {
		currentState = &state.State{}
	}

	currentState.Mode = newMode
	currentState.Since = time.Now()
	currentState.Previous = oldMode
	currentState.Reason = fmt.Sprintf("FORCED: %s", reason)
	currentState.LastUpdated = time.Now()

	if err := c.store.Snapshot(currentState); err != nil {
		c.currentMode = oldMode
		return fmt.Errorf("failed to persist state: %w", err)
	}

	// Add to transition history
	c.transitionHistory = append(c.transitionHistory, TransitionRecord{
		From:      oldMode,
		To:        newMode,
		Timestamp: time.Now(),
		Reason:    reason,
		Forced:    true,
	})

	// Log forced transition
	c.store.AddLearning(fmt.Sprintf("FORCED mode transition: %s → %s (reason: %s)",
		oldMode, newMode, reason))

	return nil
}

// checkAndAutoTransition checks for conditions that trigger automatic mode transitions
func (c *Controller) checkAndAutoTransition() {
	showState := c.showTracker.GetState()

	// Auto-transition based on show state
	if showState == state.ShowStateActive && c.currentMode != state.ModeControl {
		if err := c.TransitionTo(state.ModeControl,
			"Show started - entering control mode",
			"show_state_active"); err != nil {
			// Log error but don't crash
			fmt.Printf("Failed to transition to CONTROL mode: %v\n", err)
		}
	} else if showState != state.ShowStateActive && c.currentMode == state.ModeControl {
		if err := c.TransitionTo(state.ModeStandby,
			"Show ended - entering standby mode",
			"show_state_ended"); err != nil {
			fmt.Printf("Failed to transition to STANDBY mode: %v\n", err)
		}
	}

	// Check for errors that require escalation
	errors, _ := c.store.GetErrors()
	for _, err := range errors {
		if err.Severity == state.SeverityCritical && c.currentMode != state.ModeEscalated {
			if err := c.TransitionTo(state.ModeEscalated,
				fmt.Sprintf("Critical error: %s", err.Message),
				"critical_error"); err != nil {
			fmt.Printf("Failed to transition to ESCALATED mode: %v\n", err)
		}
			break // Only need one critical error to escalate
		}
	}
}

// GetTransitionHistory returns the history of mode transitions
func (c *Controller) GetTransitionHistory() []TransitionRecord {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.transitionHistory
}

// SetTransitionPolicy sets a policy for mode transitions
func (c *Controller) SetTransitionPolicy(policy TransitionPolicy) error {
	c.policyEngine.SetTransitionPolicy(policy)
	return nil
}

// GetPolicy returns the current policy
func (c *Controller) GetPolicy() TransitionPolicy {
	policy := c.policyEngine.transitionPolicies["default"]
	return policy
}

// EvaluateAction evaluates an action against the policy
func (c *Controller) EvaluateAction(action interface{}) (bool, string) {
	decision := c.policyEngine.EvaluateAction(action)
	return decision.Action == ActionAllow, decision.Reason
}

// ReloadPolicies reloads policies from configuration
func (c *Controller) ReloadPolicies() error {
	return c.policyEngine.ReloadPolicies()
}

// TransitionPolicy defines when mode transitions can occur
type TransitionPolicy struct {
	AllowAutoControl      bool          `json:"allow_auto_control"`
	AllowAutoEscalate    bool          `json:"allow_auto_escalate"`
	RequireApprovalFor   []state.Mode  `json:"require_approval_for"`
	BlockTransitionsFrom map[state.Mode]bool `json:"block_transitions_from"`
}
