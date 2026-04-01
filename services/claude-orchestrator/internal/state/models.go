package state

import "time"

// Mode represents the operational mode of the orchestrator
type Mode string

const (
	ModeUnknown      Mode = "UNKNOWN"
	ModeDisabled     Mode = "DISABLED"
	ModeStandby      Mode = "STANDBY"
	ModeChecking     Mode = "CHECKING"
	ModePlanning     Mode = "PLANNING"
	ModeControl      Mode = "CONTROL"
	ModeEscalated    Mode = "ESCALATED"
	ModePaused       Mode = "PAUSED"
	ModeShuttingDown Mode = "SHUTTING_DOWN"
)

// String returns the string representation of Mode
func (m Mode) String() string {
	return string(m)
}

// ModeFromString parses a Mode from a string
func ModeFromString(s string) Mode {
	switch s {
	case "DISABLED":
		return ModeDisabled
	case "STANDBY":
		return ModeStandby
	case "CHECKING":
		return ModeChecking
	case "PLANNING":
		return ModePlanning
	case "CONTROL":
		return ModeControl
	case "ESCALATED":
		return ModeEscalated
	case "PAUSED":
		return ModePaused
	case "SHUTTING_DOWN":
		return ModeShuttingDown
	default:
		return ModeUnknown
	}
}

// (Additional transient states managed internally)
// WaitingForApproval, Executing, Verifying, RetryBackoff

// State represents the current state of the orchestrator
type State struct {
	Mode        Mode         `json:"mode"`
	Since       time.Time    `json:"since"`
	Previous    Mode         `json:"previous,omitempty"`
	Reason      string       `json:"reason,omitempty"`
	Health      Health       `json:"health"`
	ShowState   ShowState    `json:"show_state"`
	Tasks       []*Task      `json:"pending_tasks"`
	Errors      []*Error     `json:"active_errors"`
	LastUpdated time.Time    `json:"last_updated"`
}

// Health represents aggregated health status
type Health struct {
	Services  map[string]ServiceHealth `json:"services"`
	Overall   HealthStatus            `json:"overall"`
	SLOPass   bool                     `json:"slo_pass"`
	LastCheck time.Time                `json:"last_check"`
	NextCheck time.Time                `json:"next_check"`
}

// ServiceHealth represents health of a single service
type ServiceHealth struct {
	Name      string        `json:"name"`
	Live      bool          `json:"live"`
	Ready     bool          `json:"ready"`
	Latency   time.Duration `json:"latency_ms"`
	Error     string        `json:"error,omitempty"`
	LastCheck time.Time     `json:"last_check"`
}

// HealthStatus represents overall health status
type HealthStatus string

const (
	HealthStatusHealthy   HealthStatus = "HEALTHY"
	HealthStatusDegraded  HealthStatus = "DEGRADED"
	HealthStatusUnhealthy HealthStatus = "UNHEALTHY"
	HealthStatusUnknown   HealthStatus = "UNKNOWN"
)

// String returns the string representation of HealthStatus
func (h HealthStatus) String() string {
	return string(h)
}

// ShowState represents the state of a show
type ShowState string

const (
	ShowStateInactive   ShowState = "INACTIVE"
	ShowStateNotStarted ShowState = "NOT_STARTED"
	ShowStateStarting   ShowState = "STARTING"
	ShowStateActive     ShowState = "ACTIVE"
	ShowStateIntermission ShowState = "INTERMISSION"
	ShowStateEnding     ShowState = "ENDING"
	ShowStateEnded      ShowState = "ENDED"
	ShowStateUnknown    ShowState = "UNKNOWN"
)

// String returns the string representation of ShowState
func (s ShowState) String() string {
	return string(s)
}

// ShowStateFromString parses a ShowState from a string
func ShowStateFromString(s string) ShowState {
	switch s {
	case "INACTIVE":
		return ShowStateInactive
	case "NOT_STARTED":
		return ShowStateNotStarted
	case "STARTING":
		return ShowStateStarting
	case "ACTIVE":
		return ShowStateActive
	case "INTERMISSION":
		return ShowStateIntermission
	case "ENDING":
		return ShowStateEnding
	case "ENDED":
		return ShowStateEnded
	default:
		return ShowStateUnknown
	}
}

// Task represents a task in the queue
type Task struct {
	ID               string        `json:"id"`
	Type             string        `json:"type"`
	Priority         int           `json:"priority"`
	Title            string        `json:"title"`
	Description      string        `json:"description"`
	Status           TaskStatus    `json:"status"`
	CreatedAt        time.Time     `json:"created_at"`
	UpdatedAt        time.Time     `json:"updated_at"`
	StartedAt        *time.Time    `json:"started_at,omitempty"`
	CompletedAt      *time.Time    `json:"completed_at,omitempty"`
	Result           string        `json:"result,omitempty"`
	Error            string        `json:"error,omitempty"`
	RetryCount       int           `json:"retry_count"`
	MaxRetries       int           `json:"max_retries"`
	RequiresApproval bool          `json:"requires_approval"`
	Approved         bool          `json:"approved"`
}

// TaskStatus represents the status of a task
type TaskStatus string

const (
	TaskStatusPending    TaskStatus = "PENDING"
	TaskStatusApproved   TaskStatus = "APPROVED"
	TaskStatusDenied     TaskStatus = "DENIED"
	TaskStatusInProgress TaskStatus = "IN_PROGRESS"
	TaskStatusCompleted  TaskStatus = "COMPLETED"
	TaskStatusFailed     TaskStatus = "FAILED"
	TaskStatusCancelled TaskStatus = "CANCELLED"
)

// String returns the string representation of TaskStatus
func (t TaskStatus) String() string {
	return string(t)
}

// Error represents an error in the system
type Error struct {
	ID         string       `json:"id"`
	Service    string       `json:"service"`
	Severity   Severity     `json:"severity"`
	Message    string       `json:"message"`
	Details    string       `json:"details,omitempty"`
	Status     ErrorStatus  `json:"status"`
	CreatedAt  time.Time    `json:"created_at"`
	UpdatedAt  time.Time    `json:"updated_at"`
	ResolvedAt *time.Time   `json:"resolved_at,omitempty"`
	ResolvedBy string       `json:"resolved_by,omitempty"`
	RetryCount int          `json:"retry_count"`
	MaxRetries int          `json:"max_retries"`
}

// Severity represents the severity level of an error
type Severity string

const (
	SeverityCritical Severity = "CRITICAL"
	SeverityHigh     Severity = "HIGH"
	SeverityMedium   Severity = "MEDIUM"
	SeverityLow      Severity = "LOW"
)

// String returns the string representation of Severity
func (s Severity) String() string {
	return string(s)
}

// ErrorStatus represents the status of an error
type ErrorStatus string

const (
	ErrorStatusActive    ErrorStatus = "ACTIVE"
	ErrorStatusEscalated ErrorStatus = "ESCALATED"
	ErrorStatusResolving ErrorStatus = "RESOLVING"
	ErrorStatusResolved  ErrorStatus = "RESOLVED"
)

// String returns the string representation of ErrorStatus
func (e ErrorStatus) String() string {
	return string(e)
}

// Transition represents a mode transition
type Transition struct {
	ID        string    `json:"id"`
	From      Mode      `json:"from"`
	To        Mode      `json:"to"`
	Reason    string    `json:"reason"`
	Timestamp time.Time `json:"timestamp"`
	Trigger   string    `json:"trigger"`
}

