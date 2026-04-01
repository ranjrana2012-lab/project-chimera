package nemoclaw

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/project-chimera/claude-orchestrator/internal/state"
)

// Tracker tracks the state of shows from Nemo Claw
type Tracker struct {
	client       *Client
	currentState state.ShowState
	showInfo     *ShowState
	mu           sync.RWMutex
	logger       *log.Logger
	subscribers  []chan state.ShowState
	subMu        sync.Mutex
	ctx          context.Context
	cancel       context.CancelFunc
}

// ShowEvent represents a show lifecycle event
type ShowEvent struct {
	Type      state.ShowState  `json:"type"`
	ShowID    string           `json:"show_id"`
	Title     string           `json:"title"`
	Timestamp time.Time        `json:"timestamp"`
	Previous  state.ShowState  `json:"previous"`
	Metadata  map[string]interface{} `json:"metadata"`
}

// NewTracker creates a new show state tracker
func NewTracker(client *Client, logger *log.Logger) *Tracker {
	if logger == nil {
		logger = log.Default()
	}

	ctx, cancel := context.WithCancel(context.Background())

	return &Tracker{
		client:      client,
		currentState: state.ShowStateInactive,
		logger:      logger,
		subscribers: make([]chan state.ShowState, 0),
		ctx:         ctx,
		cancel:      cancel,
	}
}

// Start begins tracking show state
func (t *Tracker) Start() error {
	t.logger.Printf("Starting show state tracker")

	// Subscribe to state updates from client
	go t.watchStateChanges()

	// Initial state fetch
	if err := t.fetchInitialState(); err != nil {
		t.logger.Printf("Failed to fetch initial state: %v", err)
		// Don't fail - we'll get updates via WebSocket
	}

	return nil
}

// Stop stops tracking show state
func (t *Tracker) Stop() {
	t.cancel()
	t.notifySubscribers(state.ShowStateInactive)
}

// GetState returns the current show state
func (t *Tracker) GetState() state.ShowState {
	t.mu.RLock()
	defer t.mu.RUnlock()
	return t.currentState
}

// GetShowInfo returns information about the current show
func (t *Tracker) GetShowInfo() *ShowState {
	t.mu.RLock()
	defer t.mu.RUnlock()
	return t.showInfo
}

// Subscribe registers a channel to receive state updates
func (t *Tracker) Subscribe() <-chan state.ShowState {
	t.subMu.Lock()
	defer t.subMu.Unlock()

	ch := make(chan state.ShowState, 10)
	t.subscribers = append(t.subscribers, ch)
	return ch
}

// Unsubscribe removes a subscriber channel
func (t *Tracker) Unsubscribe(ch <-chan state.ShowState) {
	t.subMu.Lock()
	defer t.subMu.Unlock()

	for i, subscriber := range t.subscribers {
		if subscriber == ch {
			t.subscribers = append(t.subscribers[:i], t.subscribers[i+1:]...)
			close(subscriber)
			break
		}
	}
}

// IsActive returns true if a show is currently active
func (t *Tracker) IsActive() bool {
	return t.GetState() == state.ShowStateActive
}

// IsStarting returns true if a show is starting (in STARTING state)
func (t *Tracker) IsStarting() bool {
	return t.GetState() == state.ShowStateStarting
}

// IsEnding returns true if a show is ending (in ENDING state)
func (t *Tracker) IsEnding() bool {
	return t.GetState() == state.ShowStateEnding
}

// watchStateChanges watches for state changes from the client
func (t *Tracker) watchStateChanges() {
	stateCh := t.client.StateChannel()

	for {
		select {
		case <-t.ctx.Done():
			return

		case newState, ok := <-stateCh:
			if !ok {
				t.logger.Printf("State channel closed")
				return
			}
			t.updateState(newState)
		}
	}
}

// fetchInitialState fetches the initial show state from Nemo Claw
func (t *Tracker) fetchInitialState() error {
	ctx, cancel := context.WithTimeout(t.ctx, 10*time.Second)
	defer cancel()

	showInfo, err := t.client.GetShowInfo(ctx)
	if err != nil {
		return fmt.Errorf("failed to get show info: %w", err)
	}

	t.mu.Lock()
	t.showInfo = showInfo
	t.currentState = showInfo.State
	t.mu.Unlock()

	t.logger.Printf("Initial show state: %s", showInfo.State)

	return nil
}

// updateState updates the current show state and notifies subscribers
func (t *Tracker) updateState(newState state.ShowState) {
	t.mu.Lock()
	oldState := t.currentState
	t.currentState = newState

	// Update show info if we have it
	if t.showInfo != nil {
		t.showInfo.State = newState
		t.showInfo.UpdatedAt = time.Now()
	}
	t.mu.Unlock()

	if oldState != newState {
		t.logger.Printf("Show state changed: %s -> %s", oldState, newState)

		// Create event
		event := &ShowEvent{
			Type:      newState,
			Timestamp: time.Now(),
			Previous:  oldState,
		}

		if t.showInfo != nil {
			event.ShowID = t.showInfo.ShowID
			event.Title = t.showInfo.Title
			event.Metadata = t.showInfo.Metadata
		}

		// Log significant transitions
		t.logTransition(event)

		// Notify subscribers
		t.notifySubscribers(newState)
	}
}

// notifySubscribers notifies all subscribers of a state change
func (t *Tracker) notifySubscribers(newState state.ShowState) {
	t.subMu.Lock()
	defer t.subMu.Unlock()

	for _, ch := range t.subscribers {
		select {
		case ch <- newState:
		default:
			t.logger.Printf("Subscriber channel full, dropping notification")
		}
	}
}

// logTransition logs significant show state transitions
func (t *Tracker) logTransition(event *ShowEvent) {
	switch event.Type {
	case state.ShowStateStarting:
		t.logger.Printf("SHOW STARTING: %s - %s", event.ShowID, event.Title)

	case state.ShowStateActive:
		t.logger.Printf("SHOW STARTED: %s - %s", event.ShowID, event.Title)

	case state.ShowStateEnding:
		t.logger.Printf("SHOW ENDING: %s - %s", event.ShowID, event.Title)

	case state.ShowStateInactive:
		if event.Previous == state.ShowStateActive || event.Previous == state.ShowStateEnding {
			t.logger.Printf("SHOW ENDED: %s - %s", event.ShowID, event.Title)
		}
	}
}

// GetEvent returns a ShowEvent for the current state transition
func (t *Tracker) GetEvent() *ShowEvent {
	t.mu.RLock()
	defer t.mu.RUnlock()

	return &ShowEvent{
		Type:      t.currentState,
		ShowID:    t.getShowID(),
		Title:     t.getShowTitle(),
		Timestamp: time.Now(),
		Metadata:  t.getShowMetadata(),
	}
}

func (t *Tracker) getShowID() string {
	if t.showInfo != nil {
		return t.showInfo.ShowID
	}
	return ""
}

func (t *Tracker) getShowTitle() string {
	if t.showInfo != nil {
		return t.showInfo.Title
	}
	return ""
}

func (t *Tracker) getShowMetadata() map[string]interface{} {
	if t.showInfo != nil {
		return t.showInfo.Metadata
	}
	return nil
}
