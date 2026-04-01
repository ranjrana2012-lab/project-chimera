package policy

import (
	"os"
	"testing"
	"time"

	"github.com/project-chimera/claude-orchestrator/internal/state"
)

func TestNewEngine(t *testing.T) {
	tmpDir := t.TempDir()
	configPath := tmpDir + "/policies.yaml"

	// Create minimal policy config
	configContent := `
policies: []
escalation_policies: []
approval_gates: []
mode_transitions: []
`
	if err := os.WriteFile(configPath, []byte(configContent), 0644); err != nil {
		t.Fatalf("Failed to create policy config: %v", err)
	}

	engine, err := NewEngine(configPath)
	if err != nil {
		t.Fatalf("Failed to create engine: %v", err)
	}

	if engine == nil {
		t.Fatal("NewEngine returned nil")
	}
}

func TestLoadPolicies(t *testing.T) {
	tmpDir := t.TempDir()
	configPath := tmpDir + "/policies.yaml"

	// Create policy config
	configContent := `
policies:
  - id: test-policy
    name: Test Policy
    description: A test policy
    enabled: true
    rules:
      - id: test-rule
        type: validation
        condition: field == "test"
        action: ALLOW
    constraints: []
escalation_policies:
  - id: test-escalation
    name: Test Escalation
    trigger:
      type: severity_threshold
    actions:
      - notify
    severity: CRITICAL
    auto_escalate: false
approval_gates: []
mode_transitions: []
`
	if err := os.WriteFile(configPath, []byte(configContent), 0644); err != nil {
		t.Fatalf("Failed to create policy config: %v", err)
	}

	engine, err := NewEngine(configPath)
	if err != nil {
		t.Fatalf("Failed to create engine: %v", err)
	}

	if len(engine.policies) != 1 {
		t.Errorf("Policies count = %d, want 1", len(engine.policies))
	}

	if len(engine.escalationRules) != 1 {
		t.Errorf("Escalation rules count = %d, want 1", len(engine.escalationRules))
	}
}

func TestEvaluateAction(t *testing.T) {
	tmpDir := t.TempDir()
	configPath := tmpDir + "/policies.yaml"

	configContent := `
policies: []
escalation_policies: []
approval_gates: []
mode_transitions: []
`
	if err := os.WriteFile(configPath, []byte(configContent), 0644); err != nil {
		t.Fatalf("Failed to create policy config: %v", err)
	}

	engine, err := NewEngine(configPath)
	if err != nil {
		t.Fatalf("Failed to create engine: %v", err)
	}

	decision := engine.EvaluateAction("test action")
	if decision == nil {
		t.Fatal("EvaluateAction returned nil")
	}

	if decision.Action != ActionAllow {
		t.Errorf("Action = %v, want ALLOW", decision.Action)
	}
}

func TestCheckEscalation(t *testing.T) {
	tmpDir := t.TempDir()
	configPath := tmpDir + "/policies.yaml"

	configContent := `
policies: []
escalation_policies:
  - id: critical-escalation
    name: Critical Error Escalation
    trigger:
      type: severity_threshold
    actions:
      - escalate
    severity: CRITICAL
    auto_escalate: true
approval_gates: []
mode_transitions: []
`
	if err := os.WriteFile(configPath, []byte(configContent), 0644); err != nil {
		t.Fatalf("Failed to create policy config: %v", err)
	}

	engine, err := NewEngine(configPath)
	if err != nil {
		t.Fatalf("Failed to create engine: %v", err)
	}

	// Test critical error
	testErr := &state.Error{
		ID:        "test-error-1",
		Service:   "test-service",
		Severity:  state.SeverityCritical,
		Message:   "Critical error",
		Status:    state.ErrorStatusActive,
		CreatedAt: time.Now(),
	}

	decision := engine.CheckEscalation(testErr)
	if decision == nil {
		t.Fatal("CheckEscalation returned nil")
	}

	if !decision.ShouldEscalate {
		t.Error("Critical error should trigger escalation")
	}

	if !decision.AutoEscalate {
		t.Error("Critical error should auto-escalate")
	}

	// Test low severity error
	errLow := &state.Error{
		ID:        "test-error-2",
		Service:   "test-service",
		Severity:  state.SeverityLow,
		Message:   "Low severity error",
		Status:    state.ErrorStatusActive,
		CreatedAt: time.Now(),
	}

	decisionLow := engine.CheckEscalation(errLow)
	if decisionLow.ShouldEscalate {
		t.Error("Low severity error should not trigger escalation")
	}
}

func TestCheckApproval(t *testing.T) {
	tmpDir := t.TempDir()
	configPath := tmpDir + "/policies.yaml"

	configContent := `
policies: []
escalation_policies: []
approval_gates:
  - id: production-approval
    name: Production Changes Approval
    conditions:
      - type: field
        field: environment
        operator: equals
        value: production
    approvers:
      - ops-team
      - lead-developer
    timeout: 1h
    escalation: ops-manager
mode_transitions: []
`
	if err := os.WriteFile(configPath, []byte(configContent), 0644); err != nil {
		t.Fatalf("Failed to create policy config: %v", err)
	}

	engine, err := NewEngine(configPath)
	if err != nil {
		t.Fatalf("Failed to create engine: %v", err)
	}

	decision := engine.CheckApproval("test action")
	if decision == nil {
		t.Fatal("CheckApproval returned nil")
	}

	// Currently no approval gates match by default
	if decision.RequiresApproval {
		t.Error("Test action should not require approval by default")
	}
}

func TestAddPolicy(t *testing.T) {
	tmpDir := t.TempDir()
	configPath := tmpDir + "/policies.yaml"

	configContent := `
policies: []
escalation_policies: []
approval_gates: []
mode_transitions: []
`
	if err := os.WriteFile(configPath, []byte(configContent), 0644); err != nil {
		t.Fatalf("Failed to create policy config: %v", err)
	}

	engine, err := NewEngine(configPath)
	if err != nil {
		t.Fatalf("Failed to create engine: %v", err)
	}

	policy := &Policy{
		ID:          "new-policy",
		Name:        "New Policy",
		Description: "A new test policy",
		Enabled:     true,
		Rules:       []*PolicyRule{},
		Constraints: []*Constraint{},
	}

	err = engine.AddPolicy(policy)
	if err != nil {
		t.Fatalf("Failed to add policy: %v", err)
	}

	if len(engine.policies) != 1 {
		t.Errorf("Policies count = %d, want 1", len(engine.policies))
	}
}

func TestDeletePolicy(t *testing.T) {
	tmpDir := t.TempDir()
	configPath := tmpDir + "/policies.yaml"

	configContent := `
policies:
  - id: test-policy
    name: Test Policy
    description: A test policy
    enabled: true
    rules: []
    constraints: []
escalation_policies: []
approval_gates: []
mode_transitions: []
`
	if err := os.WriteFile(configPath, []byte(configContent), 0644); err != nil {
		t.Fatalf("Failed to create policy config: %v", err)
	}

	engine, err := NewEngine(configPath)
	if err != nil {
		t.Fatalf("Failed to create engine: %v", err)
	}

	if len(engine.policies) != 1 {
		t.Errorf("Initial policies count = %d, want 1", len(engine.policies))
	}

	err = engine.DeletePolicy("test-policy")
	if err != nil {
		t.Fatalf("Failed to delete policy: %v", err)
	}

	if len(engine.policies) != 0 {
		t.Errorf("Policies count after delete = %d, want 0", len(engine.policies))
	}
}
