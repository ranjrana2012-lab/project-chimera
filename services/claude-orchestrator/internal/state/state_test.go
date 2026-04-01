package state

import (
	"testing"
	"time"
)

func TestModeString(t *testing.T) {
	tests := []struct {
		mode     Mode
		expected string
	}{
		{ModeDisabled, "DISABLED"},
		{ModeStandby, "STANDBY"},
		{ModeChecking, "CHECKING"},
		{ModeControl, "CONTROL"},
		{ModeEscalated, "ESCALATED"},
		{ModePaused, "PAUSED"},
		{ModeShuttingDown, "SHUTTING_DOWN"},
		{ModeUnknown, "UNKNOWN"},
	}

	for _, tt := range tests {
		t.Run(tt.expected, func(t *testing.T) {
			if got := tt.mode.String(); got != tt.expected {
				t.Errorf("Mode.String() = %v, want %v", got, tt.expected)
			}
		})
	}
}

func TestModeFromString(t *testing.T) {
	tests := []struct {
		input    string
		expected Mode
	}{
		{"DISABLED", ModeDisabled},
		{"STANDBY", ModeStandby},
		{"CHECKING", ModeChecking},
		{"CONTROL", ModeControl},
		{"ESCALATED", ModeEscalated},
		{"PAUSED", ModePaused},
		{"SHUTTING_DOWN", ModeShuttingDown},
		{"unknown", ModeUnknown},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			if got := ModeFromString(tt.input); got != tt.expected {
				t.Errorf("ModeFromString(%v) = %v, want %v", tt.input, got, tt.expected)
			}
		})
	}
}

func TestHealthStatusString(t *testing.T) {
	tests := []struct {
		status   HealthStatus
		expected string
	}{
		{HealthStatusHealthy, "HEALTHY"},
		{HealthStatusDegraded, "DEGRADED"},
		{HealthStatusUnhealthy, "UNHEALTHY"},
		{HealthStatusUnknown, "UNKNOWN"},
	}

	for _, tt := range tests {
		t.Run(tt.expected, func(t *testing.T) {
			if got := tt.status.String(); got != tt.expected {
				t.Errorf("HealthStatus.String() = %v, want %v", got, tt.expected)
			}
		})
	}
}

func TestShowStateString(t *testing.T) {
	tests := []struct {
		state    ShowState
		expected string
	}{
		{ShowStateNotStarted, "NOT_STARTED"},
		{ShowStateActive, "ACTIVE"},
		{ShowStateIntermission, "INTERMISSION"},
		{ShowStateEnded, "ENDED"},
		{ShowStateUnknown, "UNKNOWN"},
	}

	for _, tt := range tests {
		t.Run(tt.expected, func(t *testing.T) {
			if got := tt.state.String(); got != tt.expected {
				t.Errorf("ShowState.String() = %v, want %v", got, tt.expected)
			}
		})
	}
}

func TestTaskStatusString(t *testing.T) {
	tests := []struct {
		status   TaskStatus
		expected string
	}{
		{TaskStatusPending, "PENDING"},
		{TaskStatusApproved, "APPROVED"},
		{TaskStatusDenied, "DENIED"},
		{TaskStatusInProgress, "IN_PROGRESS"},
		{TaskStatusCompleted, "COMPLETED"},
		{TaskStatusFailed, "FAILED"},
		{TaskStatusCancelled, "CANCELLED"},
	}

	for _, tt := range tests {
		t.Run(tt.expected, func(t *testing.T) {
			if got := tt.status.String(); got != tt.expected {
				t.Errorf("TaskStatus.String() = %v, want %v", got, tt.expected)
			}
		})
	}
}

func TestSeverityString(t *testing.T) {
	tests := []struct {
		severity Severity
		expected string
	}{
		{SeverityCritical, "CRITICAL"},
		{SeverityHigh, "HIGH"},
		{SeverityMedium, "MEDIUM"},
		{SeverityLow, "LOW"},
	}

	for _, tt := range tests {
		t.Run(tt.expected, func(t *testing.T) {
			if got := tt.severity.String(); got != tt.expected {
				t.Errorf("Severity.String() = %v, want %v", got, tt.expected)
			}
		})
	}
}

func TestStateModels(t *testing.T) {
	// Test that we can create basic state structures
	state := &State{
		Mode:      ModeControl,
		Since:     time.Now(),
		Health:    Health{Overall: HealthStatusHealthy},
		ShowState: ShowStateActive,
		Tasks:     []*Task{},
		Errors:    []*Error{},
	}

	if state.Mode != ModeControl {
		t.Errorf("Mode = %v, want CONTROL", state.Mode)
	}

	if state.Health.Overall != HealthStatusHealthy {
		t.Errorf("Overall health = %v, want HEALTHY", state.Health.Overall)
	}

	if state.ShowState != ShowStateActive {
		t.Errorf("ShowState = %v, want ACTIVE", state.ShowState)
	}
}

func TestTaskCreation(t *testing.T) {
	task := &Task{
		ID:        "test-task",
		Type:      "test_type",
		Title:     "Test Task",
		Status:    TaskStatusPending,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	if task.ID != "test-task" {
		t.Errorf("Task ID = %v, want test-task", task.ID)
	}

	if task.Status != TaskStatusPending {
		t.Errorf("Task status = %v, want PENDING", task.Status)
	}
}

func TestErrorCreation(t *testing.T) {
	err := &Error{
		ID:        "test-error",
		Message:   "Test error message",
		Severity:  SeverityLow,
		Status:    ErrorStatusActive,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	if err.ID != "test-error" {
		t.Errorf("Error ID = %v, want test-error", err.ID)
	}

	if err.Severity != SeverityLow {
		t.Errorf("Error severity = %v, want LOW", err.Severity)
	}
}
