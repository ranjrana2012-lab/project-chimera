package integration

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/project-chimera/claude-orchestrator/internal/api"
	"github.com/project-chimera/claude-orchestrator/internal/config"
	"github.com/project-chimera/claude-orchestrator/internal/health"
	"github.com/project-chimera/claude-orchestrator/internal/state"
)

func TestAPIServerHealthEndpoints(t *testing.T) {
	// Create temp directory for state
	tmpDir, err := os.MkdirTemp("", "claude-orchestrator-integration-test")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tmpDir)

	// Create store
	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	// Create server
	cfg := &config.Config{
		ServiceName:        "test-orchestrator",
		Port:               8010,
		Host:               "localhost",
		NemoClawBaseURL:     "http://localhost:8000",
		RedisURL:           "",
		StateDir:           tmpDir,
		HealthCheckInterval: 30 * time.Second,
		HealthCheckTimeout:  10 * time.Second,
	}

	ctx := context.Background()
	server, err := api.NewServerWithContext(ctx, cfg, store)
	if err != nil {
		t.Fatalf("Failed to create server: %v", err)
	}

	// Set gin to test mode
	gin.SetMode(gin.TestMode)

	// Create test server
	testServer := httptest.NewServer(server.Engine())
	defer testServer.Close()

	// Test /health/live
	resp, err := http.Get(testServer.URL + "/health/live")
	if err != nil {
		t.Fatalf("Failed to get /health/live: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	// Test /health/ready
	resp, err = http.Get(testServer.URL + "/health/ready")
	if err != nil {
		t.Fatalf("Failed to get /health/ready: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}
}

func TestAPIServerModeEndpoints(t *testing.T) {
	tmpDir, err := os.MkdirTemp("", "claude-orchestrator-integration-test")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tmpDir)

	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	cfg := &config.Config{
		ServiceName:    "test-orchestrator",
		Port:           8010,
		Host:           "localhost",
		NemoClawBaseURL: "http://localhost:8000",
		RedisURL:       "",
		StateDir:       tmpDir,
	}

	ctx := context.Background()
	server, err := api.NewServerWithContext(ctx, cfg, store)
	if err != nil {
		t.Fatalf("Failed to create server: %v", err)
	}

	gin.SetMode(gin.TestMode)
	testServer := httptest.NewServer(server.Engine())
	defer testServer.Close()

	// Test GET /mode/current
	resp, err := http.Get(testServer.URL + "/mode/current")
	if err != nil {
		t.Fatalf("Failed to get /mode/current: %v", err)
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	var result map[string]interface{}
	json.Unmarshal(body, &result)

	if result["mode"] != "STANDBY" {
		t.Errorf("Expected mode STANDBY, got %v", result["mode"])
	}

	// Test POST /mode/transition
	resp, err = http.Post(testServer.URL+"/mode/transition", "application/json", nil)
	if err != nil {
		t.Fatalf("Failed to post /mode/transition: %v", err)
	}
	defer resp.Body.Close()
}

func TestHybridStoreStatePersistence(t *testing.T) {
	tmpDir, err := os.MkdirTemp("", "claude-orchestrator-integration-test")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tmpDir)

	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	// Set mode
	err = store.SetMode(state.ModeControl)
	if err != nil {
		t.Logf("Failed to set mode (Redis unavailable): %v", err)
	}

	// Create task
	task := &state.Task{
		ID:        "test-task-1",
		Title:     "Integration Test Task",
		Status:    state.TaskStatusPending,
		CreatedAt: time.Now(),
	}

	err = store.AddTask(task)
	if err != nil {
		t.Logf("Failed to add task (Redis unavailable): %v", err)
	}

	// Get tasks
	tasks, err := store.GetTasks()
	if err != nil {
		t.Logf("Failed to get tasks (Redis unavailable): %v", err)
		return
	}

	if len(tasks) == 0 {
		// Check file store as fallback
		fileStore := store.GetFileStore()
		queueIDs, err := fileStore.ReadQueue()
		if err != nil {
			t.Fatalf("Failed to read queue from file store: %v", err)
		}
		if len(queueIDs) == 0 {
			t.Error("Task was not persisted")
		}
	}

	// Verify task was persisted
	found := false
	for _, t := range tasks {
		if t.ID == "test-task-1" {
			found = true
			break
		}
	}

	if !found {
		t.Error("Task was not persisted")
	}
}

func TestFileStoreStatePersistence(t *testing.T) {
	tmpDir, err := os.MkdirTemp("", "claude-orchestrator-integration-test")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tmpDir)

	fileStore, err := state.NewFileStore(tmpDir)
	if err != nil {
		t.Fatalf("Failed to create file store: %v", err)
	}

	// Create test state
	testState := &state.State{
		Mode:  state.ModeControl,
		Health: state.Health{Overall: state.HealthStatusHealthy},
		Tasks: []*state.Task{
			{
				ID:        "task-1",
				Title:     "Test Task",
				Status:    state.TaskStatusPending,
				CreatedAt: time.Now(),
			},
		},
		Errors: []*state.Error{
			{
				ID:        "error-1",
				Message:   "Test error",
				Severity:  state.SeverityLow,
				CreatedAt: time.Now(),
			},
		},
	}

	// Save state
	err = fileStore.Set("state", testState)
	if err != nil {
		t.Fatalf("Failed to set state: %v", err)
	}

	// Verify state file exists
	stateFile := filepath.Join(tmpDir, "state.json")
	if _, err := os.Stat(stateFile); os.IsNotExist(err) {
		t.Error("State file was not created")
	}

	// Restore state
	resumed, err := fileStore.Restore()
	if err != nil {
		t.Fatalf("Failed to restore state: %v", err)
	}

	if resumed.Mode != testState.Mode {
		t.Errorf("Mode = %v, want %v", resumed.Mode, testState.Mode)
	}

	if len(resumed.Tasks) != len(testState.Tasks) {
		t.Errorf("Tasks count = %d, want %d", len(resumed.Tasks), len(testState.Tasks))
	}

	if len(resumed.Errors) != len(testState.Errors) {
		t.Errorf("Errors count = %d, want %d", len(resumed.Errors), len(testState.Errors))
	}
}

func TestHealthMonitorIntegration(t *testing.T) {
	tmpDir, err := os.MkdirTemp("", "claude-orchestrator-integration-test")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tmpDir)

	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	services := []health.ServiceConfig{
		{Name: "test-service", Host: "localhost", Port: 8080, Protocol: "http", Critical: true},
	}

	monitor := health.NewMonitor(store, services, 30*time.Second, 10*time.Second, "")

	if monitor == nil {
		t.Fatal("NewMonitor returned nil")
	}

	// Test that monitor was created successfully
	// The monitor should be able to start and stop without errors
	go monitor.Start()
	time.Sleep(100 * time.Millisecond)
	monitor.Stop()
}
