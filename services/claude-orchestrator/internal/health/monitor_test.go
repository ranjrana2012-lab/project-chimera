package health

import (
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
