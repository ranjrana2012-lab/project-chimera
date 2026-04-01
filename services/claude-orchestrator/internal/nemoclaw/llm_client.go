package nemoclaw

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"time"

	"github.com/project-chimera/claude-orchestrator/internal/state"
)

// LLMClient provides AI-powered decision making capabilities
type LLMClient struct {
	apiKey     string
	baseURL    string
	model      string
	httpClient *http.Client
	logger     *log.Logger
}

// DecisionRequest represents a request for an AI decision
type DecisionRequest struct {
	Scenario    string                 `json:"scenario"`
	Context     map[string]interface{} `json:"context"`
	Options     []string               `json:"options"`
	Constraints []string               `json:"constraints"`
	Mode        state.Mode             `json:"mode"`
	ShowState   state.ShowState        `json:"show_state"`
	Errors      []*state.Error         `json:"errors,omitempty"`
}

// DecisionResponse represents an AI decision response
type DecisionResponse struct {
	Decision      string                 `json:"decision"`
	Reasoning     string                 `json:"reasoning"`
	Confidence    float64                `json:"confidence"`
	Alternatives  []string               `json:"alternatives,omitempty"`
	Metadata      map[string]interface{} `json:"metadata,omitempty"`
	SuggestedMode state.Mode             `json:"suggested_mode,omitempty"`
}

// Message represents a chat message for the LLM
type Message struct {
	Role    string `json:"role"`    // "system", "user", "assistant"
	Content string `json:"content"`
}

// NewLLMClient creates a new LLM client
func NewLLMClient(apiKey, baseURL, model string, logger *log.Logger) (*LLMClient, error) {
	if apiKey == "" {
		return nil, fmt.Errorf("API key is required")
	}

	if logger == nil {
		logger = log.Default()
	}

	// Default to Anthropic-compatible API if no base URL provided
	if baseURL == "" {
		baseURL = "https://api.anthropic.com/v1/messages"
	}

	// Default model if not specified
	if model == "" {
		model = "claude-sonnet-4-20250514"
	}

	return &LLMClient{
		apiKey:  apiKey,
		baseURL: baseURL,
		model:   model,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
		logger: logger,
	}, nil
}

// RequestDecision requests an AI decision for a given scenario
func (c *LLMClient) RequestDecision(ctx context.Context, req *DecisionRequest) (*DecisionResponse, error) {
	messages := c.buildMessages(req)

	// Build API request
	apiReq := map[string]interface{}{
		"model":      c.model,
		"max_tokens": 1024,
		"messages":   messages,
		"system":     c.buildSystemPrompt(),
	}

	jsonBody, err := json.Marshal(apiReq)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, "POST", c.baseURL, bytes.NewReader(jsonBody))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("x-api-key", c.apiKey)
	httpReq.Header.Set("anthropic-version", "2023-06-01")

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API request failed with status %d: %s", resp.StatusCode, string(body))
	}

	// Parse response
	var apiResp struct {
		Content []struct {
			Type string `json:"type"`
			Text string `json:"text"`
		} `json:"content"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&apiResp); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	// Extract text from first content block
	if len(apiResp.Content) == 0 {
		return nil, fmt.Errorf("empty response from API")
	}

	responseText := apiResp.Content[0].Text

	// Parse structured response
	return c.parseDecisionResponse(responseText)
}

// buildMessages constructs the messages array for the API request
func (c *LLMClient) buildMessages(req *DecisionRequest) []Message {
	userMsg := fmt.Sprintf(`Scenario: %s

Current Mode: %s
Show State: %s

Context:
`, req.Scenario, req.Mode, req.ShowState)

	// Add context
	for k, v := range req.Context {
		userMsg += fmt.Sprintf("- %s: %v\n", k, v)
	}

	// Add errors if any
	if len(req.Errors) > 0 {
		userMsg += "\nActive Errors:\n"
		for _, err := range req.Errors {
			userMsg += fmt.Sprintf("- [%s] %s: %s\n", err.Severity, err.Service, err.Message)
		}
	}

	// Add options
	userMsg += "\nOptions:\n"
	for i, opt := range req.Options {
		userMsg += fmt.Sprintf("%d. %s\n", i+1, opt)
	}

	// Add constraints
	if len(req.Constraints) > 0 {
		userMsg += "\nConstraints:\n"
		for _, constraint := range req.Constraints {
			userMsg += fmt.Sprintf("- %s\n", constraint)
		}
	}

	userMsg += `
Please analyze this situation and provide:
1. A recommended decision (choose from the options above or suggest an alternative)
2. Your reasoning for this decision
3. A confidence score (0.0 to 1.0)
4. Any alternative approaches you considered
5. Suggested mode if different from current

Respond in JSON format.`

	return []Message{
		{
			Role:    "user",
			Content: userMsg,
		},
	}
}

// buildSystemPrompt creates the system prompt for the LLM
func (c *LLMClient) buildSystemPrompt() string {
	return `You are an AI assistant helping to operate Project Chimera, a live theatre platform with AI-powered services.

Your role is to provide operational decisions based on:
- Current operational mode (STANDBY, CHECKING, CONTROL, ESCALATED, PAUSED)
- Show state (INACTIVE, STARTING, ACTIVE, ENDING)
- Active errors and their severity
- Available options and constraints

Operational Modes:
- STANDBY: Idle mode, minimal activity
- CHECKING: Running health checks on all services
- CONTROL: Active show control mode
- ESCALATED: Error handling mode, critical issues present
- PAUSED: Temporarily paused, awaiting operator intervention

Show States:
- INACTIVE: No show running
- STARTING: Show is starting up
- ACTIVE: Show is in progress
- ENDING: Show is winding down

Decision Guidelines:
- Prioritize show continuity when show is ACTIVE
- Escalate critical errors immediately
- Maintain safety as the highest priority
- Respect operator constraints and preferences
- Provide clear reasoning for decisions

Always respond in valid JSON format with the following structure:
{
  "decision": "chosen option or action",
  "reasoning": "detailed explanation",
  "confidence": 0.0-1.0,
  "alternatives": ["option1", "option2"],
  "suggested_mode": "MODE_NAME"
}`
}

// parseDecisionResponse parses the LLM response into a DecisionResponse
func (c *LLMClient) parseDecisionResponse(text string) (*DecisionResponse, error) {
	// Try to extract JSON from the response
	// The LLM might wrap JSON in markdown code blocks
	var jsonStr string

	// Check for code block
	if len(text) > 0 {
		// Simple extraction - look for { and }
		start := -1
		end := -1
		braceCount := 0

		for i, ch := range text {
			if ch == '{' {
				if start == -1 {
					start = i
				}
				braceCount++
			} else if ch == '}' {
				braceCount--
				if braceCount == 0 && start != -1 {
					end = i + 1
					break
				}
			}
		}

		if start != -1 && end != -1 {
			jsonStr = text[start:end]
		}
	}

	if jsonStr == "" {
		return nil, fmt.Errorf("could not extract JSON from response")
	}

	var response DecisionResponse
	if err := json.Unmarshal([]byte(jsonStr), &response); err != nil {
		return nil, fmt.Errorf("failed to parse decision response: %w", err)
	}

	// Validate required fields
	if response.Decision == "" {
		return nil, fmt.Errorf("decision field is required")
	}

	if response.Reasoning == "" {
		response.Reasoning = "No reasoning provided"
	}

	if response.Confidence == 0 {
		response.Confidence = 0.5 // Default confidence
	}

	// Set metadata if nil
	if response.Metadata == nil {
		response.Metadata = make(map[string]interface{})
	}

	response.Metadata["timestamp"] = time.Now().Format(time.RFC3339)
	response.Metadata["model"] = c.model

	return &response, nil
}

// ShouldEscalate determines if errors warrant escalation
func (c *LLMClient) ShouldEscalate(ctx context.Context, errors []*state.Error, currentMode state.Mode) (bool, string, error) {
	if len(errors) == 0 {
		return false, "", nil
	}

	// Check for critical errors - always escalate
	for _, err := range errors {
		if err.Severity == state.SeverityCritical {
			return true, fmt.Sprintf("Critical error in %s: %s", err.Service, err.Message), nil
		}
	}

	// For non-critical errors, use LLM to decide
	scenario := "Error escalation decision"
	options := []string{"escalate", "monitor", "ignore"}

	req := &DecisionRequest{
		Scenario: scenario,
		Options:  options,
		Mode:     currentMode,
		Errors:   errors,
	}

	resp, err := c.RequestDecision(ctx, req)
	if err != nil {
		// Fallback: escalate on high severity errors
		for _, err := range errors {
			if err.Severity == state.SeverityHigh {
				return true, "High severity error detected (API fallback)", nil
			}
		}
		return false, "", nil
	}

	return resp.Decision == "escalate", resp.Reasoning, nil
}

// SuggestMode suggests an operational mode based on current state
func (c *LLMClient) SuggestMode(ctx context.Context, showState state.ShowState, errors []*state.Error) (state.Mode, string, error) {
	scenario := "Mode suggestion"
	options := []string{
		string(state.ModeStandby),
		string(state.ModeChecking),
		string(state.ModeControl),
		string(state.ModeEscalated),
		string(state.ModePaused),
	}

	req := &DecisionRequest{
		Scenario:  scenario,
		Options:   options,
		ShowState: showState,
		Errors:    errors,
	}

	resp, err := c.RequestDecision(ctx, req)
	if err != nil {
		// Fallback logic
		if len(errors) > 0 {
			return state.ModeEscalated, "Errors detected (fallback)", nil
		}
		switch showState {
		case state.ShowStateActive:
			return state.ModeControl, "Show active (fallback)", nil
		case state.ShowStateStarting:
			return state.ModeChecking, "Show starting (fallback)", nil
		default:
			return state.ModeStandby, "No show (fallback)", nil
		}
	}

	if resp.SuggestedMode != "" {
		return resp.SuggestedMode, resp.Reasoning, nil
	}

	// Parse decision as mode
	suggestedMode := state.ModeFromString(resp.Decision)
	if suggestedMode == state.ModeUnknown {
		suggestedMode = state.ModeStandby
	}

	return suggestedMode, resp.Reasoning, nil
}
