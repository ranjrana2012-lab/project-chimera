package mode

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"sync"
	"time"

	"github.com/project-chimera/claude-orchestrator/internal/state"
)

// ShowTracker monitors the show state from Nemo Claw
type ShowTracker struct {
	nemoclawURL string
	client      *http.Client
	mu          sync.RWMutex
	current     state.ShowState
	ctx         context.Context
	cancel      context.CancelFunc
	pollInterval time.Duration
}

// NewShowTracker creates a new show tracker
func NewShowTracker(nemoclawURL string) (*ShowTracker, error) {
	return &ShowTracker{
		nemoclawURL:   nemoclawURL,
		client:        &http.Client{Timeout: 10 * time.Second},
		current:       state.ShowStateUnknown,
		pollInterval: 15 * time.Second,
	}, nil
}

// Start begins polling for show state changes
func (s *ShowTracker) Start(ctx context.Context) {
	s.ctx, s.cancel = context.WithCancel(ctx)

	// Initial fetch
	s.fetchShowState()

	ticker := time.NewTicker(s.pollInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			s.fetchShowState()
		case <-s.ctx.Done():
			return
		}
	}
}

// Stop stops polling
func (s *ShowTracker) Stop() {
	s.cancel()
}

// GetState returns the current show state
func (s *ShowTracker) GetState() state.ShowState {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.current
}

// fetchShowState fetches the current show state from Nemo Claw
func (s *ShowTracker) fetchShowState() {
	url := fmt.Sprintf("%s/api/show/state", s.nemoclawURL)
	resp, err := s.client.Get(url)
	if err != nil {
		fmt.Printf("Failed to fetch show state: %v\n", err)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		fmt.Printf("Nemo Claw returned status %d\n", resp.StatusCode)
		return
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		fmt.Printf("Failed to read response body: %v\n", err)
		return
	}

	var showState state.ShowState
	if err := json.Unmarshal(body, &showState); err != nil {
		fmt.Printf("Failed to parse show state: %v\n", err)
		return
	}

	s.mu.Lock()
	s.current = showState
	s.mu.Unlock()
}

// GetShowState returns the current show state (public API)
func (s *ShowTracker) GetShowState() state.ShowState {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.current
}
