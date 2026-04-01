package error

import (
	"context"
	"os"
	"testing"
	"time"

	"github.com/project-chimera/claude-orchestrator/internal/policy"
	"github.com/project-chimera/claude-orchestrator/internal/state"
)

func TestNewHandler(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	configPath := tmpDir + "/policies.yaml"
	configContent := `
policies: []
escalation_policies: []
approval_gates: []
mode_transitions: []
`
	if err := writeConfig(configPath, configContent); err != nil {
		t.Fatalf("Failed to write config: %v", err)
	}

	policyEngine, err := policy.NewEngine(configPath)
	if err != nil {
		t.Fatalf("Failed to create policy engine: %v", err)
	}

	notifier := NewNotifier(context.Background())

	handler := NewHandler(store, policyEngine, notifier, context.Background())

	if handler == nil {
		t.Fatal("NewHandler returned nil")
	}
}

func TestReportError(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	configPath := tmpDir + "/policies.yaml"
	if err := writeConfig(configPath, `
policies: []
escalation_policies: []
approval_gates: []
mode_transitions: []
`); err != nil {
		t.Fatalf("Failed to write config: %v", err)
	}

	policyEngine, _ := policy.NewEngine(configPath)
	notifier := NewNotifier(context.Background())

	handler := NewHandler(store, policyEngine, notifier, context.Background())

	// Test reporting an error
	testError := &state.Error{
		Service:   "test-service",
		Severity:  state.SeverityMedium,
		Message:   "Test error message",
		Status:    state.ErrorStatusActive,
		CreatedAt: time.Now(),
	}

	if err := handler.ReportError(testError); err != nil {
		t.Fatalf("Failed to report error: %v", err)
	}

	// Verify error was tracked
	activeErrors := handler.GetActiveErrors()
	if len(activeErrors) != 1 {
		t.Errorf("Active errors count = %d, want 1", len(activeErrors))
	}
}

func TestResolveError(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	configPath := tmpDir + "/policies.yaml"
	if err := writeConfig(configPath, `
policies: []
escalation_policies: []
approval_gates: []
mode_transitions: []
`); err != nil {
		t.Fatalf("Failed to write config: %v", err)
	}

	policyEngine, _ := policy.NewEngine(configPath)
	notifier := NewNotifier(context.Background())

	handler := NewHandler(store, policyEngine, notifier, context.Background())

	// Report error first
	testError := &state.Error{
		Service:   "test-service",
		Severity:  state.SeverityMedium,
		Message:   "Test error message",
		Status:    state.ErrorStatusActive,
		CreatedAt: time.Now(),
	}

	if err := handler.ReportError(testError); err != nil {
		t.Fatalf("Failed to report error: %v", err)
	}

	// Resolve error
	resolution := "Fixed by restarting service"
	resolvedBy := "test-operator"

	if err := handler.ResolveError(testError.ID, resolution, resolvedBy); err != nil {
		t.Fatalf("Failed to resolve error: %v", err)
	}

	// Verify error is no longer active
	activeErrors := handler.GetActiveErrors()
	if len(activeErrors) != 0 {
		t.Errorf("Active errors count = %d, want 0 after resolution", len(activeErrors))
	}

	// Verify error is in handled errors
	handledErrors := handler.GetHandledErrors()
	if len(handledErrors) != 1 {
		t.Errorf("Handled errors count = %d, want 1", len(handledErrors))
	}
}

func TestGetErrorStatistics(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	configPath := tmpDir + "/policies.yaml"
	if err := writeConfig(configPath, `
policies: []
escalation_policies: []
approval_gates: []
mode_transitions: []
`); err != nil {
		t.Fatalf("Failed to write config: %v", err)
	}

	policyEngine, _ := policy.NewEngine(configPath)
	notifier := NewNotifier(context.Background())

	handler := NewHandler(store, policyEngine, notifier, context.Background())

	// Report multiple errors
	errors := []*state.Error{
		{
			Service:   "service-a",
			Severity:  state.SeverityCritical,
			Message:   "Critical error",
			Status:    state.ErrorStatusActive,
			CreatedAt: time.Now(),
		},
		{
			Service:   "service-b",
			Severity:  state.SeverityHigh,
			Message:   "High severity error",
			Status:    state.ErrorStatusActive,
			CreatedAt: time.Now(),
		},
		{
			Service:   "service-c",
			Severity:  state.SeverityLow,
			Message:   "Low severity error",
			Status:    state.ErrorStatusActive,
			CreatedAt: time.Now(),
		},
	}

	for _, err := range errors {
		if reportErr := handler.ReportError(err); reportErr != nil {
			t.Fatalf("Failed to report error: %v", reportErr)
		}
	}

	// Get statistics
	stats, err := handler.GetErrorStatistics()
	if err != nil {
		t.Fatalf("Failed to get error statistics: %v", err)
	}

	if stats.ActiveCount != 3 {
		t.Errorf("Active count = %d, want 3", stats.ActiveCount)
	}

	if stats.SeverityCounts["CRITICAL"] != 1 {
		t.Errorf("CRITICAL count = %d, want 1", stats.SeverityCounts["CRITICAL"])
	}

	if stats.ServiceCounts["service-a"] != 1 {
		t.Errorf("service-a count = %d, want 1", stats.ServiceCounts["service-a"])
	}
}

func writeConfig(path, content string) error {
	return os.WriteFile(path, []byte(content), 0644)
}
