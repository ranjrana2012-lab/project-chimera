package health

import (
	"context"
	"net"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/project-chimera/claude-orchestrator/internal/state"
)

func TestNewMonitor(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	services := []ServiceConfig{
		{
			Name:     "test-service",
			Host:     "localhost",
			Port:     8080,
			Protocol: "http",
			Critical: true,
		},
	}

	monitor := NewMonitor(store, services, 30*time.Second, 10*time.Second, "http://localhost:9090/slo")

	if monitor == nil {
		t.Fatal("NewMonitor returned nil")
	}

	if len(monitor.services) != 1 {
		t.Errorf("Monitor has %d services, want 1", len(monitor.services))
	}

	if monitor.checkInterval != 30*time.Second {
		t.Errorf("Check interval = %v, want 30s", monitor.checkInterval)
	}
}

func TestDetermineOverallHealth(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	services := []ServiceConfig{
		{Name: "critical", Host: "localhost", Port: 8080, Protocol: "http", Critical: true},
		{Name: "non-critical", Host: "localhost", Port: 8081, Protocol: "http", Critical: false},
	}

	monitor := NewMonitor(store, services, 30*time.Second, 10*time.Second, "")

	t.Run("AllHealthy", func(t *testing.T) {
		healthMap := map[string]ServiceHealth{
			"critical":     {Name: "critical", Live: true, Ready: true, Latency: 100 * time.Millisecond},
			"non-critical": {Name: "non-critical", Live: true, Ready: true, Latency: 100 * time.Millisecond},
		}

		status := monitor.determineOverallHealth(healthMap)
		if status != state.HealthStatusHealthy {
			t.Errorf("Overall health = %v, want HEALTHY", status)
		}
	})

	t.Run("CriticalUnhealthy", func(t *testing.T) {
		healthMap := map[string]ServiceHealth{
			"critical":     {Name: "critical", Live: false, Ready: false, Latency: 0},
			"non-critical": {Name: "non-critical", Live: true, Ready: true, Latency: 100 * time.Millisecond},
		}

		status := monitor.determineOverallHealth(healthMap)
		if status != state.HealthStatusUnhealthy {
			t.Errorf("Overall health = %v, want UNHEALTHY", status)
		}
	})

	t.Run("NonCriticalUnhealthy", func(t *testing.T) {
		healthMap := map[string]ServiceHealth{
			"critical":     {Name: "critical", Live: true, Ready: true, Latency: 100 * time.Millisecond},
			"non-critical": {Name: "non-critical", Live: false, Ready: false, Latency: 0},
		}

		status := monitor.determineOverallHealth(healthMap)
		if status != state.HealthStatusDegraded {
			t.Errorf("Overall health = %v, want DEGRADED", status)
		}
	})

	t.Run("HighLatency", func(t *testing.T) {
		healthMap := map[string]ServiceHealth{
			"critical":     {Name: "critical", Live: true, Ready: true, Latency: 2 * time.Second},
			"non-critical": {Name: "non-critical", Live: true, Ready: true, Latency: 100 * time.Millisecond},
		}

		status := monitor.determineOverallHealth(healthMap)
		if status != state.HealthStatusDegraded {
			t.Errorf("Overall health = %v, want DEGRADED", status)
		}
	})
}

func TestCheckService(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	// Create test server that responds to health checks
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/health/live" {
			w.WriteHeader(http.StatusOK)
			w.Write([]byte("OK"))
		} else if r.URL.Path == "/health/ready" {
			w.WriteHeader(http.StatusOK)
			w.Write([]byte("Ready"))
		} else {
			w.WriteHeader(http.StatusNotFound)
		}
	}))
	defer server.Close()

	services := []ServiceConfig{
		{
			Name:     "test-service",
			Host:     "localhost",
			Port:     server.Listener.Addr().(*net.TCPAddr).Port,
			Protocol: "http",
			Critical: false,
		},
	}

	monitor := NewMonitor(store, services, 30*time.Second, 10*time.Second, "")

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	health := monitor.checkService(ctx, services[0])

	if health.Name != "test-service" {
		t.Errorf("Service name = %s, want test-service", health.Name)
	}

	if !health.Live {
		t.Error("Expected service to be live")
	}

	if !health.Ready {
		t.Error("Expected service to be ready")
	}

	if health.Error != "" {
		t.Errorf("Unexpected error: %s", health.Error)
	}
}

func TestCheckServiceUnhealthy(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	// Create test server that returns error
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte("Internal Server Error"))
	}))
	defer server.Close()

	services := []ServiceConfig{
		{
			Name:     "unhealthy-service",
			Host:     "localhost",
			Port:     server.Listener.Addr().(*net.TCPAddr).Port,
			Protocol: "http",
			Critical: false,
		},
	}

	monitor := NewMonitor(store, services, 30*time.Second, 10*time.Second, "")

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	health := monitor.checkService(ctx, services[0])

	if health.Live {
		t.Error("Expected service to be not live")
	}

	if health.Ready {
		t.Error("Expected service to be not ready")
	}

	if health.Error == "" {
		t.Error("Expected an error message")
	}
}

func TestCheckServiceTimeout(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	// Create test server that times out
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(100 * time.Millisecond)
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	services := []ServiceConfig{
		{
			Name:     "timeout-service",
			Host:     "localhost",
			Port:     server.Listener.Addr().(*net.TCPAddr).Port,
			Protocol: "http",
			Critical: false,
		},
	}

	monitor := NewMonitor(store, services, 5*time.Millisecond, 10*time.Second, "")

	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel()

	health := monitor.checkService(ctx, services[0])

	if health.Live {
		t.Error("Expected service to be not live due to timeout")
	}

	if health.Error == "" {
		t.Error("Expected timeout error message")
	}
}

func TestCheck(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	// Create test servers
	criticalServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Critical service returns OK for both live and ready
		w.WriteHeader(http.StatusOK)
	}))
	defer criticalServer.Close()

	nonCriticalServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Non-critical service returns OK for both
		w.WriteHeader(http.StatusOK)
	}))
	defer nonCriticalServer.Close()

	criticalAddr := criticalServer.Listener.Addr().(*net.TCPAddr)
	nonCriticalAddr := nonCriticalServer.Listener.Addr().(*net.TCPAddr)

	services := []ServiceConfig{
		{
			Name:     "critical-service",
			Host:     "localhost",
			Port:     criticalAddr.Port,
			Protocol: "http",
			Critical: true,
		},
		{
			Name:     "non-critical-service",
			Host:     "localhost",
			Port:     nonCriticalAddr.Port,
			Protocol: "http",
			Critical: false,
		},
	}

	monitor := NewMonitor(store, services, 30*time.Second, 10*time.Second, "")

	ctx := context.Background()
	report := monitor.Check(ctx)

	if report == nil {
		t.Fatal("Check returned nil report")
	}

	if report.ID == "" {
		t.Error("Report ID should not be empty")
	}

	if report.Timestamp.IsZero() {
		t.Error("Report timestamp should not be zero")
	}

	if len(report.Services) != 2 {
		t.Errorf("Report has %d services, want 2", len(report.Services))
	}

	// Check critical service health
	criticalHealth, exists := report.Services["critical-service"]
	if !exists {
		t.Error("Critical service health missing from report")
	} else if !criticalHealth.Live {
		t.Error("Critical service should be live")
	}

	// Check non-critical service health
	nonCriticalHealth, exists := report.Services["non-critical-service"]
	if !exists {
		t.Error("Non-critical service health missing from report")
	} else if !nonCriticalHealth.Live {
		t.Error("Non-critical service should be live")
	}

	if report.Overall != state.HealthStatusHealthy {
		t.Errorf("Overall health = %v, want HEALTHY", report.Overall)
	}
}

func TestCheckWithFailure(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	// Create test server that fails
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer server.Close()

	addr := server.Listener.Addr().(*net.TCPAddr)

	services := []ServiceConfig{
		{
			Name:     "failing-service",
			Host:     "localhost",
			Port:     addr.Port,
			Protocol: "http",
			Critical: true,
		},
	}

	monitor := NewMonitor(store, services, 30*time.Second, 10*time.Second, "")

	ctx := context.Background()
	report := monitor.Check(ctx)

	if report == nil {
		t.Fatal("Check returned nil report")
	}

	if report.Overall != state.HealthStatusUnhealthy {
		t.Errorf("Overall health = %v, want UNHEALTHY", report.Overall)
	}

	// When SLO gate URL is empty, SLOPass is false by default
	if report.SLOPass {
		t.Error("SLO pass should be false when no SLO gate URL is configured")
	}
}

func TestStartStop(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	services := []ServiceConfig{
		{Name: "test-service", Host: "localhost", Port: 8080, Protocol: "http", Critical: false},
	}

	monitor := NewMonitor(store, services, 100*time.Millisecond, 50*time.Millisecond, "")

	// Start the monitor in a goroutine
	done := make(chan bool)
	go func() {
		monitor.Start()
		close(done)
	}()

	// Wait a bit for it to run
	time.Sleep(200 * time.Millisecond)

	// Stop the monitor
	monitor.Stop()

	// Wait for goroutine to finish
	select {
	case <-done:
	case <-time.After(500 * time.Millisecond):
		t.Error("Monitor did not stop within timeout")
	}

	// Verify we can call Stop multiple times safely
	monitor.Stop()
	monitor.Stop()
}

func TestNewMonitorWithDefaultServices(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	monitor := NewMonitor(store, nil, 30*time.Second, 10*time.Second, "")

	if monitor == nil {
		t.Fatal("NewMonitor returned nil")
	}

	// When passing nil services, the monitor has an empty service map
	if len(monitor.services) != 0 {
		t.Errorf("Monitor has %d services, want 0 when nil is passed", len(monitor.services))
	}
}

func TestCheckWithSLOGate(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	// Create test server with SLO endpoint
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/health/live" {
			w.WriteHeader(http.StatusOK)
		} else if r.URL.Path == "/slo/gate" {
			w.WriteHeader(http.StatusOK)
			w.Write([]byte(`{"pass": true}`))
		} else {
			w.WriteHeader(http.StatusNotFound)
		}
	}))
	defer server.Close()

	addr := server.Listener.Addr().(*net.TCPAddr)

	services := []ServiceConfig{
		{
			Name:     "slo-service",
			Host:     "localhost",
			Port:     addr.Port,
			Protocol: "http",
			Critical: true,
		},
	}

	monitor := NewMonitor(store, services, 30*time.Second, 10*time.Second, "http://"+server.Listener.Addr().String()+"/slo/gate")

	ctx := context.Background()
	report := monitor.Check(ctx)

	if report == nil {
		t.Fatal("Check returned nil report")
	}

	if !report.SLOPass {
		t.Error("SLO should pass when endpoint returns pass=true")
	}

	if report.SLODetails == nil {
		t.Error("SLO details should be populated")
	}
}
