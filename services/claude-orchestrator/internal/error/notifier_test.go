package error

import (
	"context"
	"testing"
	"time"

	"github.com/project-chimera/claude-orchestrator/internal/state"
)

func TestNewNotifier(t *testing.T) {
	ctx := context.Background()
	notifier := NewNotifier(ctx)

	if notifier == nil {
		t.Fatal("NewNotifier returned nil")
	}
}

func TestRegisterChannel(t *testing.T) {
	ctx := context.Background()
	notifier := NewNotifier(ctx)

	channel := &LogChannel{}
	if err := notifier.RegisterChannel("log", channel); err != nil {
		t.Fatalf("Failed to register channel: %v", err)
	}

	// Test sending notification
	notification := &Notification{
		ID:        "test-1",
		Type:      "test",
		Severity:  "info",
		Title:     "Test Notification",
		Body:      "Test notification body",
		Timestamp: time.Now(),
		Channels:  []string{"log"},
	}

	// This should not crash
	notifier.Send(notification)
}

func TestNotifyError(t *testing.T) {
	ctx := context.Background()
	notifier := NewNotifier(ctx)

	// Register log channel to capture notifications
	channel := &LogChannel{}
	notifier.RegisterChannel("test", channel)

	err := &state.Error{
		ID:        "test-error-1",
		Service:   "test-service",
		Severity:  state.SeverityMedium,
		Message:   "Test error",
		Status:    state.ErrorStatusActive,
		CreatedAt: time.Now(),
	}

	// This should not crash
	notifier.NotifyError(err, nil)
}

func TestNotifyErrorResolution(t *testing.T) {
	ctx := context.Background()
	notifier := NewNotifier(ctx)

	channel := &LogChannel{}
	notifier.RegisterChannel("test", channel)

	now := time.Now()
	err := &state.Error{
		ID:         "test-error-1",
		Service:    "test-service",
		Severity:   state.SeverityMedium,
		Message:    "Test error",
		Status:     state.ErrorStatusResolved,
		ResolvedAt: &now,
		ResolvedBy: "test-operator",
	}

	// This should not crash
	notifier.NotifyErrorResolution(err, "Fixed the issue")
}

func TestNotifyModeChange(t *testing.T) {
	ctx := context.Background()
	notifier := NewNotifier(ctx)

	channel := &LogChannel{}
	notifier.RegisterChannel("test", channel)

	// This should not crash
	notifier.NotifyModeChange(state.ModeStandby, state.ModeControl, "Test transition")
}

func TestNotifyTaskCompletion(t *testing.T) {
	ctx := context.Background()
	notifier := NewNotifier(ctx)

	channel := &LogChannel{}
	notifier.RegisterChannel("test", channel)

	task := &state.Task{
		ID:        "test-task-1",
		Title:     "Test Task",
		Status:    state.TaskStatusCompleted,
		Result:    "Task completed successfully",
		CreatedAt: time.Now(),
	}

	// This should not crash
	notifier.NotifyTaskCompletion(task)
}

func TestNotifyHealthChange(t *testing.T) {
	ctx := context.Background()
	notifier := NewNotifier(ctx)

	channel := &LogChannel{}
	notifier.RegisterChannel("test", channel)

	// This should not crash
	notifier.NotifyHealthChange("test-service", state.HealthStatusHealthy, state.HealthStatusUnhealthy)
}

func TestWebhookChannel(t *testing.T) {
	config := &WebhookConfig{
		URL:        "http://localhost:9999/test",
		Method:     "POST",
		Headers:    map[string]string{"Content-Type": "application/json"},
		RetryCount: 2,
		Timeout:    5,
	}

	channel := NewWebhookChannel(config)

	if channel == nil {
		t.Fatal("NewWebhookChannel returned nil")
	}

	// Test sending notification (will fail to connect but that's expected)
	notification := &Notification{
		ID:        "test-1",
		Type:      "test",
		Severity:  "info",
		Title:     "Test",
		Body:      "Test body",
		Timestamp: time.Now(),
	}

	// This will fail to connect but shouldn't crash
	_ = channel.Send(notification)
}

func TestLogChannel(t *testing.T) {
	channel := NewLogChannel(nil)

	if channel == nil {
		t.Fatal("NewLogChannel returned nil")
	}

	notification := &Notification{
		ID:        "test-1",
		Type:      "test",
		Severity:  "info",
		Title:     "Test",
		Body:      "Test body",
		Timestamp: time.Now(),
	}

	err := channel.Send(notification)
	if err != nil {
		t.Fatalf("Failed to send notification: %v", err)
	}
}

func TestRegisterWebhook(t *testing.T) {
	ctx := context.Background()
	notifier := NewNotifier(ctx)

	config := &WebhookConfig{
		URL:        "http://localhost:9999/test",
		Method:     "POST",
		Headers:    map[string]string{"Content-Type": "application/json"},
		RetryCount: 1,
		Timeout:    5,
	}

	err := notifier.RegisterWebhook("test-webhook", config)
	if err != nil {
		t.Fatalf("Failed to register webhook: %v", err)
	}

	// Verify webhook was registered
	if notifier.webhooks["test-webhook"] == nil {
		t.Error("Webhook was not registered")
	}
}

func TestConfigureSMTP(t *testing.T) {
	ctx := context.Background()
	notifier := NewNotifier(ctx)

	config := &SMTPConfig{
		Host:     "localhost",
		Port:     25,
		Username: "test",
		Password: "test",
		From:     "test@example.com",
		Subject:  "[{{Type}}] {{Title}}",
	}

	err := notifier.ConfigureSMTP(config)
	if err != nil {
		t.Fatalf("Failed to configure SMTP: %v", err)
	}

	// Verify config was set
	if notifier.smtpConfig == nil {
		t.Error("SMTP config was not set")
	}
}
