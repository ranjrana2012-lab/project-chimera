package nemoclaw

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/project-chimera/claude-orchestrator/internal/state"
)

// TestNewClient tests creating a new Nemo Claw client
func TestNewClient(t *testing.T) {
	logger := log.New(os.Stdout, "", log.LstdFlags)

	client, err := NewClient("http://localhost:8000", logger)
	if err != nil {
		t.Fatalf("Failed to create client: %v", err)
	}

	if client == nil {
		t.Fatal("Client is nil")
	}

	if client.baseURL != "http://localhost:8000" {
		t.Errorf("baseURL = %s, want http://localhost:8000", client.baseURL)
	}

	if client.GetShowState() != state.ShowStateInactive {
		t.Errorf("Initial state = %s, want %s", client.GetShowState(), state.ShowStateInactive)
	}
}

// TestNewClientInvalidURL tests creating a client with an invalid URL
func TestNewClientInvalidURL(t *testing.T) {
	logger := log.New(os.Stdout, "", log.LstdFlags)

	_, err := NewClient("://invalid-url", logger)
	if err == nil {
		t.Error("Expected error for invalid URL, got nil")
	}
}

// TestGetShowInfo tests retrieving show information
func TestGetShowInfo(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/api/v1/shows/current" {
			t.Errorf("Unexpected path: %s", r.URL.Path)
		}

		show := ShowState{
			ShowID:    "test-show-1",
			Title:     "Test Show",
			State:     state.ShowStateActive,
			UpdatedAt: time.Now(),
		}

		json.NewEncoder(w).Encode(show)
	}))
	defer server.Close()

	logger := log.New(os.Stdout, "", log.LstdFlags)
	client, err := NewClient(server.URL, logger)
	if err != nil {
		t.Fatalf("Failed to create client: %v", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	show, err := client.GetShowInfo(ctx)
	if err != nil {
		t.Fatalf("Failed to get show info: %v", err)
	}

	if show.ShowID != "test-show-1" {
		t.Errorf("ShowID = %s, want test-show-1", show.ShowID)
	}

	if show.Title != "Test Show" {
		t.Errorf("Title = %s, want Test Show", show.Title)
	}

	if show.State != state.ShowStateActive {
		t.Errorf("State = %s, want %s", show.State, state.ShowStateActive)
	}
}

// TestGetShowInfoNoActiveShow tests when there's no active show
func TestGetShowInfoNoActiveShow(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusNotFound)
	}))
	defer server.Close()

	logger := log.New(os.Stdout, "", log.LstdFlags)
	client, err := NewClient(server.URL, logger)
	if err != nil {
		t.Fatalf("Failed to create client: %v", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	show, err := client.GetShowInfo(ctx)
	if err != nil {
		t.Fatalf("Failed to get show info: %v", err)
	}

	if show.State != state.ShowStateInactive {
		t.Errorf("State = %s, want %s", show.State, state.ShowStateInactive)
	}
}

// TestGetServiceStatus tests retrieving service status
func TestGetServiceStatus(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/api/v1/services/status" {
			t.Errorf("Unexpected path: %s", r.URL.Path)
		}

		statuses := []ServiceStatus{
			{Name: "service-1", Status: "healthy", Message: "OK", Timestamp: time.Now()},
			{Name: "service-2", Status: "degraded", Message: "Slow", Timestamp: time.Now()},
		}

		json.NewEncoder(w).Encode(statuses)
	}))
	defer server.Close()

	logger := log.New(os.Stdout, "", log.LstdFlags)
	client, err := NewClient(server.URL, logger)
	if err != nil {
		t.Fatalf("Failed to create client: %v", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	statuses, err := client.GetServiceStatus(ctx)
	if err != nil {
		t.Fatalf("Failed to get service status: %v", err)
	}

	if len(statuses) != 2 {
		t.Errorf("Got %d statuses, want 2", len(statuses))
	}

	if statuses[0].Name != "service-1" {
		t.Errorf("Service name = %s, want service-1", statuses[0].Name)
	}

	if statuses[1].Status != "degraded" {
		t.Errorf("Service status = %s, want degraded", statuses[1].Status)
	}
}

// TestSendCommand tests sending a command to Nemo Claw
func TestSendCommand(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/api/v1/commands" {
			t.Errorf("Unexpected path: %s", r.URL.Path)
		}

		if r.Method != "POST" {
			t.Errorf("Method = %s, want POST", r.Method)
		}

		var cmd map[string]interface{}
		if err := json.NewDecoder(r.Body).Decode(&cmd); err != nil {
			t.Errorf("Failed to decode command: %v", err)
		}

		if cmd["command"] != "test_command" {
			t.Errorf("Command = %v, want test_command", cmd["command"])
		}

		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	logger := log.New(os.Stdout, "", log.LstdFlags)
	client, err := NewClient(server.URL, logger)
	if err != nil {
		t.Fatalf("Failed to create client: %v", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	err = client.SendCommand(ctx, "test_command", map[string]interface{}{"key": "value"})
	if err != nil {
		t.Fatalf("Failed to send command: %v", err)
	}
}

// TestHandleShowStateUpdate tests handling show state updates
func TestHandleShowStateUpdate(t *testing.T) {
	logger := log.New(os.Stdout, "", log.LstdFlags)
	client, err := NewClient("http://localhost:8000", logger)
	if err != nil {
		t.Fatalf("Failed to create client: %v", err)
	}

	// Simulate state update message
	data := map[string]interface{}{
		"type": "show_state_update",
		"data": map[string]interface{}{
			"state": "ACTIVE",
		},
	}

	jsonData, _ := json.Marshal(data)
	client.handleMessage(jsonData)

	// Give time for async processing
	time.Sleep(10 * time.Millisecond)

	if client.GetShowState() != state.ShowStateActive {
		t.Errorf("State = %s, want %s", client.GetShowState(), state.ShowStateActive)
	}
}

// TestTracker tests the show state tracker
func TestTracker(t *testing.T) {
	logger := log.New(os.Stdout, "", log.LstdFlags)
	client, err := NewClient("http://localhost:8000", logger)
	if err != nil {
		t.Fatalf("Failed to create client: %v", err)
	}

	tracker := NewTracker(client, logger)

	if tracker == nil {
		t.Fatal("Tracker is nil")
	}

	if tracker.GetState() != state.ShowStateInactive {
		t.Errorf("Initial state = %s, want %s", tracker.GetState(), state.ShowStateInactive)
	}

	if tracker.IsActive() {
		t.Error("Tracker should not be active initially")
	}

	if tracker.IsStarting() {
		t.Error("Tracker should not be starting initially")
	}

	if tracker.IsEnding() {
		t.Error("Tracker should not be ending initially")
	}
}

// TestTrackerSubscription tests tracker subscription
func TestTrackerSubscription(t *testing.T) {
	logger := log.New(os.Stdout, "", log.LstdFlags)
	client, err := NewClient("http://localhost:8000", logger)
	if err != nil {
		t.Fatalf("Failed to create client: %v", err)
	}

	tracker := NewTracker(client, logger)

	// Subscribe to state changes
	stateCh := tracker.Subscribe()
	if stateCh == nil {
		t.Fatal("State channel is nil")
	}

	// Simulate state update
	tracker.updateState(state.ShowStateActive)

	// Check for update
	select {
	case newState := <-stateCh:
		if newState != state.ShowStateActive {
			t.Errorf("Received state = %s, want %s", newState, state.ShowStateActive)
		}
	case <-time.After(100 * time.Millisecond):
		t.Error("Timeout waiting for state update")
	}

	// Unsubscribe
	tracker.Unsubscribe(stateCh)
}

// TestTrackerShowInfo tests getting show info from tracker
func TestTrackerShowInfo(t *testing.T) {
	logger := log.New(os.Stdout, "", log.LstdFlags)
	client, err := NewClient("http://localhost:8000", logger)
	if err != nil {
		t.Fatalf("Failed to create client: %v", err)
	}

	tracker := NewTracker(client, logger)

	showInfo := tracker.GetShowInfo()
	if showInfo != nil {
		t.Error("Show info should be nil initially")
	}

	// Set show info
	tracker.mu.Lock()
	tracker.showInfo = &ShowState{
		ShowID:    "test-show",
		Title:     "Test Show",
		State:     state.ShowStateActive,
		UpdatedAt: time.Now(),
	}
	tracker.mu.Unlock()

	showInfo = tracker.GetShowInfo()
	if showInfo == nil {
		t.Fatal("Show info is still nil")
	}

	if showInfo.ShowID != "test-show" {
		t.Errorf("ShowID = %s, want test-show", showInfo.ShowID)
	}

	if showInfo.Title != "Test Show" {
		t.Errorf("Title = %s, want Test Show", showInfo.Title)
	}
}

// TestLLMClient tests the LLM client
func TestLLMClient(t *testing.T) {
	logger := log.New(os.Stdout, "", log.LstdFlags)

	client, err := NewLLMClient("test-api-key", "", "claude-sonnet-4-20250514", logger)
	if err != nil {
		t.Fatalf("Failed to create LLM client: %v", err)
	}

	if client == nil {
		t.Fatal("LLM client is nil")
	}

	if client.apiKey != "test-api-key" {
		t.Errorf("API key = %s, want test-api-key", client.apiKey)
	}

	if client.model != "claude-sonnet-4-20250514" {
		t.Errorf("Model = %s, want claude-sonnet-4-20250514", client.model)
	}
}

// TestLLMClientNoAPIKey tests creating LLM client without API key
func TestLLMClientNoAPIKey(t *testing.T) {
	logger := log.New(os.Stdout, "", log.LstdFlags)

	_, err := NewLLMClient("", "", "", logger)
	if err == nil {
		t.Error("Expected error for missing API key, got nil")
	}

	if !strings.Contains(err.Error(), "API key is required") {
		t.Errorf("Error message = %s, should mention API key", err.Error())
	}
}

// TestLLMClientShouldEscalate tests escalation decision logic
func TestLLMClientShouldEscalate(t *testing.T) {
	logger := log.New(os.Stdout, "", log.LstdFlags)

	// Create mock server that returns escalation decision
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := map[string]interface{}{
			"content": []map[string]interface{}{
				{
					"type": "text",
					"text": `{
						"decision": "monitor",
						"reasoning": "Errors are minor, continue monitoring",
						"confidence": 0.8
					}`,
				},
			},
		}

		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client, err := NewLLMClient("test-key", server.URL, "test-model", logger)
	if err != nil {
		t.Fatalf("Failed to create LLM client: %v", err)
	}

	errors := []*state.Error{
		{
			Service:  "test-service",
			Severity: state.SeverityLow,
			Message:  "Minor error",
		},
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	shouldEscalate, reasoning, err := client.ShouldEscalate(ctx, errors, state.ModeControl)
	if err != nil {
		t.Fatalf("ShouldEscalate failed: %v", err)
	}

	if shouldEscalate {
		t.Error("Should not escalate for minor errors")
	}

	if reasoning == "" {
		t.Error("Reasoning should not be empty")
	}
}

// TestLLMClientShouldEscalateCritical tests critical error escalation
func TestLLMClientShouldEscalateCritical(t *testing.T) {
	logger := log.New(os.Stdout, "", log.LstdFlags)

	client, err := NewLLMClient("test-key", "", "test-model", logger)
	if err != nil {
		t.Fatalf("Failed to create LLM client: %v", err)
	}

	errors := []*state.Error{
		{
			Service:  "critical-service",
			Severity: state.SeverityCritical,
			Message:  "Critical failure",
		},
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	shouldEscalate, reasoning, err := client.ShouldEscalate(ctx, errors, state.ModeControl)
	if err != nil {
		t.Fatalf("ShouldEscalate failed: %v", err)
	}

	if !shouldEscalate {
		t.Error("Should escalate for critical errors")
	}

	if !strings.Contains(reasoning, "Critical") {
		t.Errorf("Reasoning should mention critical error, got: %s", reasoning)
	}
}

// TestLLMClientSuggestMode tests mode suggestion
func TestLLMClientSuggestMode(t *testing.T) {
	logger := log.New(os.Stdout, "", log.LstdFlags)

	// Create mock server
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := map[string]interface{}{
			"content": []map[string]interface{}{
				{
					"type": "text",
					"text": `{
						"decision": "CONTROL",
						"reasoning": "Show is active, enter control mode",
						"confidence": 0.95,
						"suggested_mode": "CONTROL"
					}`,
				},
			},
		}

		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client, err := NewLLMClient("test-key", server.URL, "test-model", logger)
	if err != nil {
		t.Fatalf("Failed to create LLM client: %v", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	mode, reasoning, err := client.SuggestMode(ctx, state.ShowStateActive, nil)
	if err != nil {
		t.Fatalf("SuggestMode failed: %v", err)
	}

	if mode != state.ModeControl {
		t.Errorf("Suggested mode = %s, want %s", mode, state.ModeControl)
	}

	if reasoning == "" {
		t.Error("Reasoning should not be empty")
	}
}

// TestBuildSystemPrompt tests system prompt generation
func TestBuildSystemPrompt(t *testing.T) {
	logger := log.New(os.Stdout, "", log.LstdFlags)
	client, err := NewLLMClient("test-key", "", "test-model", logger)
	if err != nil {
		t.Fatalf("Failed to create LLM client: %v", err)
	}

	prompt := client.buildSystemPrompt()

	if !strings.Contains(prompt, "Project Chimera") {
		t.Error("System prompt should mention Project Chimera")
	}

	if !strings.Contains(prompt, "STANDBY") {
		t.Error("System prompt should mention STANDBY mode")
	}

	if !strings.Contains(prompt, "CONTROL") {
		t.Error("System prompt should mention CONTROL mode")
	}

	if !strings.Contains(prompt, "Show State") {
		t.Error("System prompt should mention Show State")
	}
}
