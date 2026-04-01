package config

import (
	"os"
	"testing"
	"time"
)

func TestLoadConfig(t *testing.T) {
	// Set environment variables for testing
	os.Setenv("CLAUDE_SERVICE_NAME", "test-service")
	os.Setenv("CLAUDE_PORT", "9090")
	os.Setenv("CLAUDE_HOST", "127.0.0.1")
	os.Setenv("CLAUDE_NEMOCLAW_BASE_URL", "http://localhost:9000")
	os.Setenv("CLAUDE_REDIS_URL", "redis://localhost:6379")
	os.Setenv("CLAUDE_STATE_DIR", "/tmp/test-state")
	os.Setenv("CLAUDE_HEALTH_CHECK_INTERVAL", "60s")
	os.Setenv("CLAUDE_HEALTH_CHECK_TIMEOUT", "30s")
	os.Setenv("CLAUDE_RALPH_LOOP_ENABLED", "true")
	os.Setenv("CLAUDE_LOG_LEVEL", "debug")
	defer func() {
		// Clean up environment variables
		os.Unsetenv("CLAUDE_SERVICE_NAME")
		os.Unsetenv("CLAUDE_PORT")
		os.Unsetenv("CLAUDE_HOST")
		os.Unsetenv("CLAUDE_NEMOCLAW_BASE_URL")
		os.Unsetenv("CLAUDE_REDIS_URL")
		os.Unsetenv("CLAUDE_STATE_DIR")
		os.Unsetenv("CLAUDE_HEALTH_CHECK_INTERVAL")
		os.Unsetenv("CLAUDE_HEALTH_CHECK_TIMEOUT")
		os.Unsetenv("CLAUDE_RALPH_LOOP_ENABLED")
		os.Unsetenv("CLAUDE_LOG_LEVEL")
	}()

	cfg, err := LoadConfig()
	if err != nil {
		t.Fatalf("LoadConfig failed: %v", err)
	}

	if cfg.ServiceName != "test-service" {
		t.Errorf("ServiceName = %v, want test-service", cfg.ServiceName)
	}

	if cfg.Port != 9090 {
		t.Errorf("Port = %v, want 9090", cfg.Port)
	}

	if cfg.Host != "127.0.0.1" {
		t.Errorf("Host = %v, want 127.0.0.1", cfg.Host)
	}

	if cfg.NemoClawBaseURL != "http://localhost:9000" {
		t.Errorf("NemoClawBaseURL = %v, want http://localhost:9000", cfg.NemoClawBaseURL)
	}

	if cfg.RedisURL != "redis://localhost:6379" {
		t.Errorf("RedisURL = %v, want redis://localhost:6379", cfg.RedisURL)
	}

	if cfg.StateDir != "/tmp/test-state" {
		t.Errorf("StateDir = %v, want /tmp/test-state", cfg.StateDir)
	}

	if cfg.HealthCheckInterval != 60*time.Second {
		t.Errorf("HealthCheckInterval = %v, want 60s", cfg.HealthCheckInterval)
	}

	if cfg.HealthCheckTimeout != 30*time.Second {
		t.Errorf("HealthCheckTimeout = %v, want 30s", cfg.HealthCheckTimeout)
	}

	if !cfg.RalphLoopEnabled {
		t.Error("RalphLoopEnabled should be true")
	}

	if cfg.LogLevel != "debug" {
		t.Errorf("LogLevel = %v, want debug", cfg.LogLevel)
	}
}

func TestLoadConfigDefaults(t *testing.T) {
	// Clean environment
	os.Unsetenv("CLAUDE_SERVICE_NAME")
	os.Unsetenv("CLAUDE_PORT")
	os.Unsetenv("CLAUDE_HOST")
	os.Unsetenv("CLAUDE_NEMOCLAW_BASE_URL")
	os.Unsetenv("CLAUDE_REDIS_URL")
	os.Unsetenv("CLAUDE_STATE_DIR")
	os.Unsetenv("CLAUDE_HEALTH_CHECK_INTERVAL")
	os.Unsetenv("CLAUDE_HEALTH_CHECK_TIMEOUT")
	os.Unsetenv("CLAUDE_RALPH_LOOP_ENABLED")
	os.Unsetenv("CLAUDE_LOG_LEVEL")

	cfg, err := LoadConfig()
	if err != nil {
		t.Fatalf("LoadConfig failed: %v", err)
	}

	if cfg.ServiceName != "claude-orchestrator" {
		t.Errorf("Default ServiceName = %v, want claude-orchestrator", cfg.ServiceName)
	}

	if cfg.Port != 8010 {
		t.Errorf("Default Port = %v, want 8010", cfg.Port)
	}

	if cfg.Host != "0.0.0.0" {
		t.Errorf("Default Host = %v, want 0.0.0.0", cfg.Host)
	}

	if cfg.NemoClawBaseURL != "http://localhost:8000" {
		t.Errorf("Default NemoClawBaseURL = %v, want http://localhost:8000", cfg.NemoClawBaseURL)
	}

	if cfg.RedisURL != "redis://localhost:6379" {
		t.Errorf("Default RedisURL = %v, want redis://localhost:6379", cfg.RedisURL)
	}

	if cfg.StateDir != "/state/claude-orchestrator" {
		t.Errorf("Default StateDir = %v, want /state/claude-orchestrator", cfg.StateDir)
	}

	if cfg.HealthCheckInterval != 5*time.Minute {
		t.Errorf("Default HealthCheckInterval = %v, want 5m", cfg.HealthCheckInterval)
	}

	if cfg.HealthCheckTimeout != 30*time.Second {
		t.Errorf("Default HealthCheckTimeout = %v, want 30s", cfg.HealthCheckTimeout)
	}

	if !cfg.RalphLoopEnabled {
		t.Error("Default RalphLoopEnabled should be true")
	}

	if cfg.LogLevel != "info" {
		t.Errorf("Default LogLevel = %v, want info", cfg.LogLevel)
	}
}

func TestConfigValidate(t *testing.T) {
	t.Run("ValidConfig", func(t *testing.T) {
		cfg := &Config{
			ServiceName:        "test-service",
			Port:               8010,
			Host:               "0.0.0.0",
			NemoClawBaseURL:     "http://localhost:8000",
			RedisURL:           "redis://localhost:6379",
			StateDir:           "/tmp/test",
			HealthCheckInterval: 1 * time.Minute,
			HealthCheckTimeout:  30 * time.Second,
		}

		err := cfg.Validate()
		if err != nil {
			t.Errorf("Validate failed for valid config: %v", err)
		}
	})

	t.Run("InvalidPort", func(t *testing.T) {
		cfg := &Config{
			ServiceName:        "test-service",
			Port:               -1,
			Host:               "0.0.0.0",
			NemoClawBaseURL:     "http://localhost:8000",
			RedisURL:           "redis://localhost:6379",
			StateDir:           "/tmp/test",
			HealthCheckInterval: 1 * time.Minute,
			HealthCheckTimeout:  30 * time.Second,
		}

		err := cfg.Validate()
		if err == nil {
			t.Error("Validate should fail for invalid port")
		}
	})

	t.Run("EmptyServiceName", func(t *testing.T) {
		cfg := &Config{
			ServiceName:        "",
			Port:               8010,
			Host:               "0.0.0.0",
			NemoClawBaseURL:     "http://localhost:8000",
			RedisURL:           "redis://localhost:6379",
			StateDir:           "/tmp/test",
			HealthCheckInterval: 1 * time.Minute,
			HealthCheckTimeout:  30 * time.Second,
		}

		err := cfg.Validate()
		if err == nil {
			t.Error("Validate should fail for empty service name")
		}
	})

	t.Run("InvalidTimeout", func(t *testing.T) {
		cfg := &Config{
			ServiceName:        "test-service",
			Port:               8010,
			Host:               "0.0.0.0",
			NemoClawBaseURL:     "http://localhost:8000",
			RedisURL:           "redis://localhost:6379",
			StateDir:           "/tmp/test",
			HealthCheckInterval: 1 * time.Minute,
			HealthCheckTimeout:  -1 * time.Second,
		}

		err := cfg.Validate()
		if err == nil {
			t.Error("Validate should fail for negative timeout")
		}
	})
}

func TestGetDefaultServices(t *testing.T) {
	services := GetDefaultServices()

	if len(services) == 0 {
		t.Error("Default services should not be empty")
	}

	// Check for critical services
	criticalServices := map[string]bool{
		"safety-filter":       false,
		"nemoclaw-orchestrator": false,
		"scenespeak-agent":     false,
		"captioning-agent":     false,
	}

	for _, svc := range services {
		if _, exists := criticalServices[svc.Name]; exists {
			criticalServices[svc.Name] = true
		}
	}

	for name, found := range criticalServices {
		if !found {
			t.Errorf("Critical service %s not found in default services", name)
		}
	}

	// Check that safety-filter is marked as critical
	for _, svc := range services {
		if svc.Name == "safety-filter" && !svc.Critical {
			t.Error("safety-filter should be marked as critical")
		}
	}
}

func TestParseHealthCheckInterval(t *testing.T) {
	tests := []struct {
		input    string
		expected time.Duration
	}{
		{"30s", 30 * time.Second},
		{"5m", 5 * time.Minute},
		{"1h", 1 * time.Hour},
		{"100ms", 100 * time.Millisecond},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			os.Setenv("CLAUDE_HEALTH_CHECK_INTERVAL", tt.input)
			defer os.Unsetenv("CLAUDE_HEALTH_CHECK_INTERVAL")

			cfg, err := LoadConfig()
			if err != nil {
				t.Fatalf("LoadConfig failed: %v", err)
			}

			if cfg.HealthCheckInterval != tt.expected {
				t.Errorf("HealthCheckInterval = %v, want %v", cfg.HealthCheckInterval, tt.expected)
			}
		})
	}
}

func TestParseRalphLoopEnabled(t *testing.T) {
	tests := []struct {
		input    string
		expected bool
	}{
		{"true", true},
		{"True", true},
		{"TRUE", true},
		{"false", false},
		{"False", false},
		{"FALSE", false},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			os.Setenv("CLAUDE_RALPH_LOOP_ENABLED", tt.input)
			defer os.Unsetenv("CLAUDE_RALPH_LOOP_ENABLED")

			cfg, err := LoadConfig()
			if err != nil {
				t.Fatalf("LoadConfig failed: %v", err)
			}

			if cfg.RalphLoopEnabled != tt.expected {
				t.Errorf("RalphLoopEnabled = %v, want %v", cfg.RalphLoopEnabled, tt.expected)
			}
		})
	}
}

func TestParseLogLevel(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		{"debug", "debug"},
		{"info", "info"},
		{"warn", "warn"},
		{"error", "error"},
		{"DEBUG", "debug"},
		{"INFO", "info"},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			os.Setenv("CLAUDE_LOG_LEVEL", tt.input)
			defer os.Unsetenv("CLAUDE_LOG_LEVEL")

			cfg, err := LoadConfig()
			if err != nil {
				t.Fatalf("LoadConfig failed: %v", err)
			}

			if cfg.LogLevel != tt.expected {
				t.Errorf("LogLevel = %v, want %v", cfg.LogLevel, tt.expected)
			}
		})
	}
}
