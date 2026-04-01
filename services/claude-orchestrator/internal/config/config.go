package config

import (
	"fmt"
	"time"

	"github.com/spf13/viper"
)

// Config represents the application configuration
type Config struct {
	// Service configuration
	ServiceName string `mapstructure:"service_name"`
	Port        int    `mapstructure:"port"`
	Host        string `mapstructure:"host"`

	// Nemo Claw integration
	NemoClawBaseURL string        `mapstructure:"nemoclaw_base_url"`
	NemoClawTimeout  time.Duration `mapstructure:"nemoclaw_timeout"`

	// State persistence
	RedisURL          string `mapstructure:"redis_url"`
	StateDir           string `mapstructure:"state_dir"`

	// Health monitoring
	HealthCheckInterval time.Duration `mapstructure:"health_check_interval"`
	HealthCheckTimeout  time.Duration `mapstructure:"health_check_timeout"`
	SLOGateURL         string `mapstructure:"slo_gate_url"`

	// Ralph Loop
	RalphLoopEnabled bool   `mapstructure:"ralph_loop_enabled"`
	RalphMaxIterations int    `mapstructure:"ralph_max_iterations"`

	// Policy engine
	PolicyConfigPath   string `mapstructure:"policy_config_path"`
	PolicyReloadInterval time.Duration `mapstructure:"policy_reload_interval"`

	// Error handling
	ErrorRetention      time.Duration `mapstructure:"error_retention"`
	ErrorEscalationTimeout time.Duration `mapstructure:"error_escalation_timeout"`

	// Logging
	LogLevel  string `mapstructure:"log_level"`
	LogFormat string `mapstructure:"log_format"`
	LogOutput string `mapstructure:"log_output"`

	// Services to monitor
	Services []ServiceConfig `mapstructure:"services"`
}

// ServiceConfig represents a service configuration for monitoring
type ServiceConfig struct {
	Name     string `mapstructure:"name"`
	Host     string `mapstructure:"host"`
	Port     int    `mapstructure:"port"`
	Protocol string `mapstructure:"protocol"`
	Critical bool   `mapstructure:"critical"`
}

// LoadConfig loads configuration from environment variables and config file
func LoadConfig() (*Config, error) {
	// Set defaults
	viper.SetDefault("service_name", "claude-orchestrator")
	viper.SetDefault("port", 8010)
	viper.SetDefault("host", "0.0.0.0")
	viper.SetDefault("nemoclaw_base_url", "http://localhost:8000")
	viper.SetDefault("nemoclaw_timeout", 30*time.Second)
	viper.SetDefault("redis_url", "redis://localhost:6379")
	viper.SetDefault("state_dir", "/state/claude-orchestrator")
	viper.SetDefault("health_check_interval", 5*time.Minute)
	viper.SetDefault("health_check_timeout", 30*time.Second)
	viper.SetDefault("slo_gate_url", "http://quality-platform:9000/slo-gate")
	viper.SetDefault("ralph_loop_enabled", true)
	viper.SetDefault("ralph_max_iterations", 0)
	viper.SetDefault("policy_config_path", "/config/policies.yaml")
	viper.SetDefault("policy_reload_interval", 5*time.Minute)
	viper.SetDefault("error_retention", 7*24*time.Hour)
	viper.SetDefault("error_escalation_timeout", 5*time.Minute)
	viper.SetDefault("log_level", "info")
	viper.SetDefault("log_format", "json")
	viper.SetDefault("log_output", "stdout")

	// Load from environment
	viper.SetEnvPrefix("CLAUDE")
	viper.AutomaticEnv()

	// Load config file if exists
	viper.SetConfigFile(".env")
	viper.ReadInConfig()

	// Unmarshal
	var cfg Config
	if err := viper.Unmarshal(&cfg); err != nil {
		return nil, fmt.Errorf("failed to unmarshal config: %w", err)
	}

	// Set default services if not configured
	if len(cfg.Services) == 0 {
		cfg.Services = GetDefaultServices()
	}

	return &cfg, nil
}

// GetDefaultServices returns the default list of services to monitor
func GetDefaultServices() []ServiceConfig {
	return []ServiceConfig{
		{Name: "scenespeak-agent", Host: "localhost", Port: 8001, Protocol: "http", Critical: true},
		{Name: "captioning-agent", Host: "localhost", Port: 8002, Protocol: "http", Critical: true},
		{Name: "bsl-agent", Host: "localhost", Port: 8003, Protocol: "http", Critical: true},
		{Name: "sentiment-agent", Host: "localhost", Port: 8004, Protocol: "http", Critical: false},
		{Name: "lighting-sound-music", Host: "localhost", Port: 8005, Protocol: "http", Critical: true},
		{Name: "safety-filter", Host: "localhost", Port: 8006, Protocol: "http", Critical: true},
		{Name: "autonomous-agent", Host: "localhost", Port: 8008, Protocol: "http", Critical: false},
		{Name: "music-generation", Host: "localhost", Port: 8011, Protocol: "http", Critical: false},
		{Name: "nemoclaw-orchestrator", Host: "localhost", Port: 8000, Protocol: "http", Critical: true},
	}
}

// Validate validates the configuration
func (c *Config) Validate() error {
	if c.Port < 1 || c.Port > 65535 {
		return fmt.Errorf("invalid port: %d", c.Port)
	}

	if c.NemoClawBaseURL == "" {
		return fmt.Errorf("nemoclaw_base_url is required")
	}

	if c.RedisURL == "" {
		return fmt.Errorf("redis_url is required")
	}

	return nil
}
