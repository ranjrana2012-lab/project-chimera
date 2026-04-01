package policy

import (
	"fmt"
	"os"
	"path/filepath"
	"sync"

	"github.com/project-chimera/claude-orchestrator/internal/state"
	"gopkg.in/yaml.v3"
)

// Engine represents the policy engine
type Engine struct {
	mu              sync.RWMutex
	policies        map[string]*Policy
	escalationRules []*EscalationRule
	approvalGates   []*ApprovalGate
	configPath      string
}

// Policy represents a governance policy
type Policy struct {
	ID          string           `yaml:"id" json:"id"`
	Name        string           `yaml:"name" json:"name"`
	Description string           `yaml:"description" json:"description"`
	Rules       []*PolicyRule    `yaml:"rules" json:"rules"`
	Constraints []*Constraint    `yaml:"constraints" json:"constraints"`
	Enabled     bool             `yaml:"enabled" json:"enabled"`
}

// PolicyRule represents a single policy rule
type PolicyRule struct {
	ID          string                 `yaml:"id" json:"id"`
	Type        string                 `yaml:"type" json:"type"`
	Condition   string                 `yaml:"condition" json:"condition"`
	Action      string                 `yaml:"action" json:"action"`
	Parameters  map[string]interface{} `yaml:"parameters" json:"parameters"`
}

// Constraint represents a policy constraint
type Constraint struct {
	Type        string      `yaml:"type" json:"type"`
	Value       interface{} `yaml:"value" json:"value"`
	Description string      `yaml:"description" json:"description"`
}

// EscalationRule defines when to escalate issues
type EscalationRule struct {
	ID          string            `yaml:"id" json:"id"`
	Name        string            `yaml:"name" json:"name"`
	Trigger     Trigger           `yaml:"trigger" json:"trigger"`
	Actions     []string          `yaml:"actions" json:"actions"`
	Severity    state.Severity    `yaml:"severity" json:"severity"`
	Timeout     string            `yaml:"timeout" json:"timeout"`
	AutoEscalate bool              `yaml:"auto_escalate" json:"auto_escalate"`
}

// Trigger defines what triggers an escalation
type Trigger struct {
	Type      string                 `yaml:"type" json:"type"`
	Condition string                 `yaml:"condition" json:"condition"`
	Threshold int                    `yaml:"threshold" json:"threshold"`
	Window    string                 `yaml:"window" json:"window"`
	Metadata  map[string]interface{} `yaml:"metadata" json:"metadata"`
}

// ApprovalGate defines approval requirements
type ApprovalGate struct {
	ID          string           `yaml:"id" json:"id"`
	Name        string           `yaml:"name" json:"name"`
	Conditions []GateCondition `yaml:"conditions" json:"conditions"`
	Approvers  []string         `yaml:"approvers" json:"approvers"`
	Timeout    string           `yaml:"timeout" json:"timeout"`
	Escalation string           `yaml:"escalation" json:"escalation"`
}

// GateCondition represents a single approval condition
type GateCondition struct {
	Type       string                 `yaml:"type" json:"type"`
	Field      string                 `yaml:"field" json:"field"`
	Operator   string                 `yaml:"operator" json:"operator"`
	Value      interface{}            `yaml:"value" json:"value"`
	Metadata   map[string]interface{} `yaml:"metadata" json:"metadata"`
}

// NewEngine creates a new policy engine
func NewEngine(configPath string) (*Engine, error) {
	engine := &Engine{
		policies:        make(map[string]*Policy),
		escalationRules: make([]*EscalationRule, 0),
		approvalGates:   make([]*ApprovalGate, 0),
		configPath:      configPath,
	}

	// Load policies from config file
	if err := engine.LoadPolicies(); err != nil {
		return nil, fmt.Errorf("failed to load policies: %w", err)
	}

	return engine, nil
}

// LoadPolicies loads policies from the configuration file
func (e *Engine) LoadPolicies() error {
	e.mu.Lock()
	defer e.mu.Unlock()

	// Read config file
	data, err := os.ReadFile(e.configPath)
	if err != nil {
		return fmt.Errorf("failed to read policy config: %w", err)
	}

	// Parse YAML
	var config PolicyConfig
	if err := yaml.Unmarshal(data, &config); err != nil {
		return fmt.Errorf("failed to parse policy config: %w", err)
	}

	// Load policies
	for _, policy := range config.Policies {
		e.policies[policy.ID] = policy
	}

	// Load escalation rules
	e.escalationRules = config.EscalationPolicies

	// Load approval gates
	e.approvalGates = config.ApprovalGates

	return nil
}

// EvaluateAction evaluates an action against all policies
func (e *Engine) EvaluateAction(action interface{}) *PolicyDecision {
	e.mu.RLock()
	defer e.mu.RUnlock()

	decision := &PolicyDecision{
		Action:    ActionAllow,
		Reason:    "No policies prohibit this action",
		Escalate:  false,
		Policies:  make([]string, 0),
		Violations: make([]*PolicyViolation, 0),
	}

	// Evaluate against all enabled policies
	for _, policy := range e.policies {
		if !policy.Enabled {
			continue
		}

		policyDecision := e.evaluatePolicy(policy, action)
		if policyDecision.Action == ActionDeny || policyDecision.Action == ActionSanitize {
			decision.Action = policyDecision.Action
			decision.Reason = fmt.Sprintf("Blocked by policy %s: %s", policy.Name, policyDecision.Reason)
			decision.Escalate = policyDecision.Escalate
			decision.Policies = append(decision.Policies, policy.ID)
			decision.Violations = append(decision.Violations, policyDecision.Violations...)
		}
	}

	return decision
}

// evaluatePolicy evaluates a single policy against an action
func (e *Engine) evaluatePolicy(policy *Policy, action interface{}) *PolicyDecision {
	decision := &PolicyDecision{
		Action:     ActionAllow,
		Reason:     "Policy allows this action",
		Escalate:   false,
		Violations: make([]*PolicyViolation, 0),
	}

	for _, rule := range policy.Rules {
		if e.matchesRule(rule, action) {
			decision.Action = PolicyAction(rule.Action)
			decision.Reason = fmt.Sprintf("Rule %s matched: %s", rule.ID, rule.Condition)
			decision.Escalate = rule.Parameters["escalate"] == true

			violation := &PolicyViolation{
				RuleID:     rule.ID,
				RuleType:   rule.Type,
				Condition:  rule.Condition,
				Severity:   "medium",
				Suggestion: "Review action against policy requirements",
			}
			decision.Violations = append(decision.Violations, violation)
		}
	}

	return decision
}

// matchesRule checks if an action matches a policy rule
func (e *Engine) matchesRule(rule *PolicyRule, action interface{}) bool {
	// TODO: Implement rule matching logic
	// This would check if the action meets the rule's condition
	return false
}

// GetEscalationRules returns all escalation rules
func (e *Engine) GetEscalationRules() []*EscalationRule {
	e.mu.RLock()
	defer e.mu.RUnlock()
	return e.escalationRules
}

// GetApprovalGates returns all approval gates
func (e *Engine) GetApprovalGates() []*ApprovalGate {
	e.mu.RLock()
	defer e.mu.RUnlock()
	return e.approvalGates
}

// CheckEscalation checks if an error should be escalated
func (e *Engine) CheckEscalation(err *state.Error) *EscalationDecision {
	e.mu.RLock()
	defer e.mu.RUnlock()

	decision := &EscalationDecision{
		ShouldEscalate: false,
		Reason:         "No escalation rules matched",
		Rules:          make([]string, 0),
	}

	for _, rule := range e.escalationRules {
		if e.matchesEscalationRule(rule, err) {
			decision.ShouldEscalate = true
			decision.Reason = fmt.Sprintf("Matched escalation rule %s", rule.Name)
			decision.Rules = append(decision.Rules, rule.ID)

			if rule.AutoEscalate {
				decision.AutoEscalate = true
			}
		}
	}

	return decision
}

// matchesEscalationRule checks if an error matches an escalation rule
func (e *Engine) matchesEscalationRule(rule *EscalationRule, err *state.Error) bool {
	// Check severity
	if rule.Severity != "" && err.Severity != rule.Severity {
		return false
	}

	// Check trigger condition
	switch rule.Trigger.Type {
	case "error_count":
		// TODO: Implement error count checking
	case "retry_exceeded":
		if err.RetryCount >= err.MaxRetries {
			return true
		}
	case "severity_threshold":
		if err.Severity == state.SeverityCritical || err.Severity == state.SeverityHigh {
			return true
		}
	}

	return false
}

// CheckApproval checks if an action requires approval
func (e *Engine) CheckApproval(action interface{}) *ApprovalDecision {
	e.mu.RLock()
	defer e.mu.RUnlock()

	decision := &ApprovalDecision{
		RequiresApproval: false,
		Gates:            make([]string, 0),
		Approvers:        make([]string, 0),
	}

	for _, gate := range e.approvalGates {
		if e.matchesApprovalGate(gate, action) {
			decision.RequiresApproval = true
			decision.Gates = append(decision.Gates, gate.ID)
			decision.Approvers = append(decision.Approvers, gate.Approvers...)
		}
	}

	return decision
}

// matchesApprovalGate checks if an action matches an approval gate
func (e *Engine) matchesApprovalGate(gate *ApprovalGate, action interface{}) bool {
	// TODO: Implement approval gate matching logic
	return false
}

// AddPolicy adds a new policy
func (e *Engine) AddPolicy(policy *Policy) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	e.policies[policy.ID] = policy
	return e.SavePolicies()
}

// UpdatePolicy updates an existing policy
func (e *Engine) UpdatePolicy(policy *Policy) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	if _, exists := e.policies[policy.ID]; !exists {
		return fmt.Errorf("policy not found: %s", policy.ID)
	}

	e.policies[policy.ID] = policy
	return e.SavePolicies()
}

// DeletePolicy deletes a policy
func (e *Engine) DeletePolicy(policyID string) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	delete(e.policies, policyID)
	return e.SavePolicies()
}

// SavePolicies saves policies to the configuration file
func (e *Engine) SavePolicies() error {
	config := PolicyConfig{
		Policies:            make([]*Policy, 0),
		EscalationPolicies:   e.escalationRules,
		ApprovalGates:       e.approvalGates,
		ModeTransitions:     make([]interface{}, 0),
	}

	for _, policy := range e.policies {
		config.Policies = append(config.Policies, policy)
	}

	data, err := yaml.Marshal(config)
	if err != nil {
		return err
	}

	// Ensure directory exists
	if err := os.MkdirAll(filepath.Dir(e.configPath), 0755); err != nil {
		return err
	}

	return os.WriteFile(e.configPath, data, 0644)
}

// PolicyConfig represents the policy configuration structure
type PolicyConfig struct {
	Policies            []*Policy        `yaml:"policies"`
	EscalationPolicies  []*EscalationRule `yaml:"escalation_policies"`
	ApprovalGates       []*ApprovalGate  `yaml:"approval_gates"`
	ModeTransitions      []interface{}     `yaml:"mode_transitions"`
}

// PolicyDecision represents the result of policy evaluation
type PolicyDecision struct {
	Action     PolicyAction      `json:"action"`
	Reason     string            `json:"reason"`
	Escalate   bool              `json:"escalate"`
	Policies   []string          `json:"policies"`
	Violations []*PolicyViolation `json:"violations"`
}

// PolicyViolation represents a policy violation
type PolicyViolation struct {
	RuleID     string `json:"rule_id"`
	RuleType   string `json:"rule_type"`
	Condition  string `json:"condition"`
	Severity   string `json:"severity"`
	Suggestion string `json:"suggestion"`
}

// EscalationDecision represents an escalation decision
type EscalationDecision struct {
	ShouldEscalate bool     `json:"should_escalate"`
	Reason         string   `json:"reason"`
	Rules          []string `json:"rules"`
	AutoEscalate   bool     `json:"auto_escalate"`
}

// ApprovalDecision represents an approval decision
type ApprovalDecision struct {
	RequiresApproval bool     `json:"requires_approval"`
	Gates            []string `json:"gates"`
	Approvers        []string `json:"approvers"`
}

// PolicyAction represents the type of policy action
type PolicyAction string

const (
	ActionAllow    PolicyAction = "ALLOW"
	ActionDeny     PolicyAction = "DENY"
	ActionSanitize PolicyAction = "SANITIZE"
	ActionEscalate PolicyAction = "ESCALATE"
)
