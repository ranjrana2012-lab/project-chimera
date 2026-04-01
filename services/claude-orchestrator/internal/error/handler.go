package error

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/project-chimera/claude-orchestrator/internal/policy"
	"github.com/project-chimera/claude-orchestrator/internal/state"
)

// Handler manages error handling and escalation
type Handler struct {
	store          *state.HybridStore
	policyEngine   *policy.Engine
	notifier      *Notifier
	ctx            context.Context
	mu             sync.RWMutex
	activeErrors   map[string]*state.Error
	handledErrors  map[string]*state.Error
	escalationChan chan *EscalationEvent
}

// EscalationEvent represents an escalation event
type EscalationEvent struct {
	Error      *state.Error      `json:"error"`
	Decision   *policy.EscalationDecision `json:"decision"`
	Timestamp  time.Time         `json:"timestamp"`
	Source     string            `json:"source"`
}

// NewHandler creates a new error handler
func NewHandler(store *state.HybridStore, policyEngine *policy.Engine, notifier *Notifier, ctx context.Context) *Handler {
	return &Handler{
		store:          store,
		policyEngine:   policyEngine,
		notifier:      notifier,
		ctx:            ctx,
		activeErrors:   make(map[string]*state.Error),
		handledErrors:  make(map[string]*state.Error),
		escalationChan: make(chan *EscalationEvent, 100),
	}
}

// Start begins the error handler
func (h *Handler) Start() {
	// Start escalation processor
	go h.processEscalations()

	// Start error cleanup loop
	ticker := time.NewTicker(5 * time.Minute)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			h.cleanupOldErrors()

		case <-h.ctx.Done():
			return
		}
	}
}

// processEscalations processes escalation events
func (h *Handler) processEscalations() {
	for {
		select {
		case event := <-h.escalationChan:
			h.handleEscalation(event)

		case <-h.ctx.Done():
			return
		}
	}
}

// ReportError reports a new error
func (h *Handler) ReportError(err *state.Error) error {
	h.mu.Lock()
	defer h.mu.Unlock()

	// Set defaults
	if err.ID == "" {
		err.ID = generateErrorID()
	}
	if err.CreatedAt.IsZero() {
		err.CreatedAt = time.Now()
	}
	err.UpdatedAt = time.Now()

	// Check for escalation
	decision := h.policyEngine.CheckEscalation(err)

	// Add to store
	if storeErr := h.store.AddError(err); storeErr != nil {
		return fmt.Errorf("failed to add error to store: %w", storeErr)
	}

	// Track active error
	h.activeErrors[err.ID] = err

	// Send notification
	h.notifier.NotifyError(err, decision)

	// Trigger escalation if needed
	if decision.ShouldEscalate {
		event := &EscalationEvent{
			Error:     err,
			Decision:  decision,
			Timestamp: time.Now(),
			Source:    "error_handler",
		}
		select {
		case h.escalationChan <- event:
		default:
			// Channel full, log warning
			fmt.Printf("Warning: escalation channel full, error %s may not be escalated\n", err.ID)
		}
	}

	return nil
}

// ResolveError resolves an error
func (h *Handler) ResolveError(errorID string, resolution string, resolvedBy string) error {
	h.mu.Lock()
	defer h.mu.Unlock()

	// Get error
	err, exists := h.activeErrors[errorID]
	if !exists {
		return fmt.Errorf("error not found: %s", errorID)
	}

	// Update error status
	now := time.Now()
	err.Status = state.ErrorStatusResolved
	err.ResolvedAt = &now
	err.ResolvedBy = resolvedBy

	// Move to handled errors
	h.handledErrors[errorID] = err
	delete(h.activeErrors, errorID)

	// Remove from store
	if storeErr := h.store.RemoveError(errorID); storeErr != nil {
		return fmt.Errorf("failed to remove error from store: %w", storeErr)
	}

	// Log resolution
	learning := fmt.Sprintf("# Error Resolved: %s\nResolution: %s\nResolved by: %s\nResolved at: %s",
		errorID, resolution, resolvedBy, now.Format("2006-01-02T15:04:05Z"))
	if err := h.store.AddLearning(learning); err != nil {
		fmt.Printf("Warning: failed to log resolution: %v\n", err)
	}

	// Send notification
	h.notifier.NotifyErrorResolution(err, resolution)

	return nil
}

// GetActiveErrors returns all active errors
func (h *Handler) GetActiveErrors() []*state.Error {
	h.mu.RLock()
	defer h.mu.RUnlock()

	errors := make([]*state.Error, 0, len(h.activeErrors))
	for _, err := range h.activeErrors {
		errors = append(errors, err)
	}

	// Sort by severity and time
	h.sortErrors(errors)

	return errors
}

// GetHandledErrors returns all handled errors
func (h *Handler) GetHandledErrors() []*state.Error {
	h.mu.RLock()
	defer h.mu.RUnlock()

	errors := make([]*state.Error, 0, len(h.handledErrors))
	for _, err := range h.handledErrors {
		errors = append(errors, err)
	}

	return errors
}

// GetErrorByID retrieves a specific error
func (h *Handler) GetErrorByID(errorID string) (*state.Error, error) {
	h.mu.RLock()
	defer h.mu.RUnlock()

	if err, exists := h.activeErrors[errorID]; exists {
		return err, nil
	}

	if err, exists := h.handledErrors[errorID]; exists {
		return err, nil
	}

	return nil, fmt.Errorf("error not found: %s", errorID)
}

// cleanupOldErrors removes old resolved errors from memory
func (h *Handler) cleanupOldErrors() {
	h.mu.Lock()
	defer h.mu.Unlock()

	cutoff := time.Now().Add(-24 * time.Hour) // Keep for 24 hours

	for id, err := range h.handledErrors {
		if err.ResolvedAt != nil && err.ResolvedAt.Before(cutoff) {
			delete(h.handledErrors, id)
		}
	}
}

// sortErrors sorts errors by severity and timestamp
func (h *Handler) sortErrors(errors []*state.Error) {
	// Sort by severity (critical first) then by time (newest first)
	for i := 0; i < len(errors)-1; i++ {
		for j := 0; j < len(errors)-i-1; j++ {
			if h.compareErrors(errors[j], errors[j+1]) < 0 {
				errors[j], errors[j+1] = errors[j+1], errors[j]
			}
		}
	}
}

// compareErrors compares two errors for sorting
func (h *Handler) compareErrors(a, b *state.Error) int {
	// Compare by severity
	severityOrder := map[state.Severity]int{
		state.SeverityCritical: 4,
		state.SeverityHigh:     3,
		state.SeverityMedium:   2,
		state.SeverityLow:      1,
	}

	aSeverity := severityOrder[a.Severity]
	bSeverity := severityOrder[b.Severity]

	if aSeverity != bSeverity {
		return bSeverity - aSeverity // Higher severity first
	}

	// Same severity, sort by time (newest first)
	return int(b.CreatedAt.Unix() - a.CreatedAt.Unix())
}

// handleEscalation handles an escalation event
func (h *Handler) handleEscalation(event *EscalationEvent) {
	if event.Decision.AutoEscalate {
		// Automatically escalate
		h.escalateError(event.Error)
	} else {
		// Request manual escalation
		h.notifier.NotifyEscalation(event)
	}
}

// escalateError escalates an error to the appropriate mode
func (h *Handler) escalateError(err *state.Error) {
	// TODO: Implement actual mode transition
	// This would call the mode controller to transition to ESCALATED mode
	fmt.Printf("Escalating error %s to ESCALATED mode\n", err.ID)
}

// GetErrorStatistics returns error statistics
func (h *Handler) GetErrorStatistics() (*ErrorStatistics, error) {
	h.mu.RLock()
	defer h.mu.RUnlock()

	stats := &ErrorStatistics{
		ActiveCount:      len(h.activeErrors),
		HandledCount:     len(h.handledErrors),
		SeverityCounts:   make(map[string]int),
		ServiceCounts:    make(map[string]int),
		TypeCounts:       make(map[string]int),
	}

	for _, err := range h.activeErrors {
		stats.SeverityCounts[err.Severity.String()]++
		stats.ServiceCounts[err.Service]++
		stats.TypeCounts[err.Service]++
	}

	for _, err := range h.handledErrors {
		stats.SeverityCounts[err.Severity.String()]++
		stats.ServiceCounts[err.Service]++
		stats.TypeCounts[err.Service]++
	}

	return stats, nil
}

// ErrorStatistics represents error statistics
type ErrorStatistics struct {
	ActiveCount    int            `json:"active_count"`
	HandledCount   int            `json:"handled_count"`
	SeverityCounts map[string]int `json:"severity_counts"`
	ServiceCounts  map[string]int `json:"service_counts"`
	TypeCounts     map[string]int `json:"type_counts"`
}

// generateErrorID generates a unique error ID
func generateErrorID() string {
	return fmt.Sprintf("error-%d", time.Now().UnixNano())
}
