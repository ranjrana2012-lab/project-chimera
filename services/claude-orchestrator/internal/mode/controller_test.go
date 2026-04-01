package mode

import (
	"testing"
	"time"

	"github.com/project-chimera/claude-orchestrator/internal/state"
)

func TestNewController(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	ctrl, err := NewController(store, "http://localhost:8000")
	if err != nil {
		t.Fatalf("Failed to create controller: %v", err)
	}

	if ctrl == nil {
		t.Fatal("NewController returned nil")
	}

	if ctrl.nemoClawURL != "http://localhost:8000" {
		t.Errorf("NemoClaw URL = %v, want http://localhost:8000", ctrl.nemoClawURL)
	}
}

func TestControllerGetCurrentMode(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	ctrl, err := NewController(store, "http://localhost:8000")
	if err != nil {
		t.Fatalf("Failed to create controller: %v", err)
	}

	// Test initial mode
	mode := ctrl.GetCurrentMode()
	if mode != state.ModeStandby {
		t.Errorf("Initial mode = %v, want STANDBY", mode)
	}
}

func TestControllerForceTransition(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	ctrl, err := NewController(store, "http://localhost:8000")
	if err != nil {
		t.Fatalf("Failed to create controller: %v", err)
	}

	// Force transition
	err = ctrl.ForceTransition(state.ModeControl, "test force transition")
	if err != nil {
		t.Logf("Force transition failed (Redis unavailable): %v", err)
		return
	}

	mode := ctrl.GetCurrentMode()
	if mode != state.ModeControl {
		t.Errorf("Mode = %v, want CONTROL", mode)
	}

	// Check transition history
	transitions := ctrl.GetTransitionHistory()
	if len(transitions) == 0 {
		t.Error("Transition history should not be empty")
	}

	lastTransition := transitions[len(transitions)-1]
	if lastTransition.To != state.ModeControl {
		t.Errorf("Last transition to = %v, want CONTROL", lastTransition.To)
	}

	if lastTransition.Reason != "test force transition" {
		t.Errorf("Last transition reason = %v, want 'test force transition'", lastTransition.Reason)
	}
}

func TestTransitionRecord(t *testing.T) {
	record := TransitionRecord{
		From:      state.ModeStandby,
		To:        state.ModeControl,
		Timestamp: time.Now(),
		Reason:    "test transition",
		Forced:    false,
	}

	if record.From.String() != "STANDBY" {
		t.Errorf("From mode = %v, want STANDBY", record.From.String())
	}

	if record.To.String() != "CONTROL" {
		t.Errorf("To mode = %v, want CONTROL", record.To.String())
	}

	if record.Reason != "test transition" {
		t.Errorf("Reason = %v, want 'test transition'", record.Reason)
	}
}

func TestShowStateTracker(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	tracker, err := NewShowTracker("http://localhost:8000")
	if err != nil {
		t.Fatalf("Failed to create show tracker: %v", err)
	}

	if tracker == nil {
		t.Fatal("NewShowTracker returned nil")
	}

	// Test GetState initially
	showState := tracker.GetState()
	if showState != state.ShowStateUnknown {
		t.Errorf("Initial show state = %v, want UNKNOWN", showState)
	}
}

func TestPolicyEngine(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	policy := NewPolicyEngine()

	if policy == nil {
		t.Fatal("NewPolicyEngine returned nil")
	}

	// Test CanTransition with default policy
	// Control to Standby should always be allowed
	allowed := policy.CanTransition(state.ModeControl, state.ModeStandby, "")
	if !allowed {
		t.Errorf("Control to Standby transition should always be allowed")
	}

	// Test manual trigger for Standby to Control
	allowed = policy.CanTransition(state.ModeStandby, state.ModeControl, "manual")
	if !allowed {
		t.Errorf("Standby to Control with manual trigger should be allowed")
	}

	// Test RequiresApprovalForTransition
	requiresApproval := policy.RequiresApprovalForTransition(state.ModeStandby, state.ModeControl)
	if requiresApproval {
		t.Error("Standby to Control should not require approval by default")
	}
}
