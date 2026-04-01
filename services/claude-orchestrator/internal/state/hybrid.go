package state

import (
	"context"
	"fmt"
	"time"
)

// HybridStore coordinates between file and Redis stores
type HybridStore struct {
	fileStore  *FileStore
	redisStore *RedisStore
	ctx        context.Context
}

// NewHybridStore creates a new hybrid store
func NewHybridStore(basePath, redisAddr string) (*HybridStore, error) {
	fileStore, err := NewFileStore(basePath)
	if err != nil {
		return nil, fmt.Errorf("failed to create file store: %w", err)
	}

	redisStore, err := NewRedisStore(redisAddr)
	if err != nil {
		return nil, fmt.Errorf("failed to create Redis store: %w", err)
	}

	return &HybridStore{
		fileStore:  fileStore,
		redisStore: redisStore,
		ctx:        context.Background(),
	}, nil
}

// Get retrieves a value - tries Redis first, falls back to file
func (h *HybridStore) Get(key string) (interface{}, error) {
	// Try Redis first (fast, real-time)
	val, err := h.redisStore.Get(key)
	if err == nil && val != nil {
		return val, nil
	}

	// Fallback to file store (persistent, git-traceable)
	return h.fileStore.Get(key)
}

// Set stores a value in both Redis and file
func (h *HybridStore) Set(key string, value interface{}) error {
	// Set in Redis (real-time access)
	if err := h.redisStore.Set(key, value); err != nil {
		return fmt.Errorf("failed to set in Redis: %w", err)
	}

	// Set in file (persistent, git-traceable)
	// Note: Not all values need to be in files, but state does
	if key == "state" {
		if state, ok := value.(*State); ok {
			return h.fileStore.Snapshot(state)
		}
	}

	return nil
}

// Delete removes a value from both Redis and file
func (h *HybridStore) Delete(key string) error {
	// Delete from Redis
	if err := h.redisStore.Delete(key); err != nil {
		return fmt.Errorf("failed to delete from Redis: %w", err)
	}

	// Delete from file
	return h.fileStore.Delete(key)
}

// Snapshot saves the current state to both stores
func (h *HybridStore) Snapshot(state *State) error {
	// Save to file store (git-traceable)
	if err := h.fileStore.Snapshot(state); err != nil {
		return fmt.Errorf("failed to snapshot to file: %w", err)
	}

	// Save critical state to Redis (real-time)
	if err := h.redisStore.Set("state", state); err != nil {
		return fmt.Errorf("failed to snapshot to Redis: %w", err)
	}

	// Also set mode, health, show state individually for quick access
	if err := h.redisStore.SetMode(state.Mode); err != nil {
		return fmt.Errorf("failed to set mode in Redis: %w", err)
	}

	if err := h.redisStore.SetHealthStatus(&state.Health); err != nil {
		return fmt.Errorf("failed to set health in Redis: %w", err)
	}

	if err := h.redisStore.SetShowState(state.ShowState); err != nil {
		return fmt.Errorf("failed to set show state in Redis: %w", err)
	}

	return nil
}

// Restore loads the state from file store
func (h *HybridStore) Restore() (*State, error) {
	// Try to restore from file first (most complete)
	state, err := h.fileStore.Restore()
	if err != nil {
		return nil, fmt.Errorf("failed to restore from file: %w", err)
	}

	if state == nil {
		// No previous state, return default
		return &State{
			Mode:        ModeStandby,
			Since:       time.Now(),
			Health:      Health{Services: make(map[string]ServiceHealth), Overall: HealthStatusUnknown},
			ShowState:   ShowStateUnknown,
			LastUpdated: time.Now(),
		}, nil
	}

	// Sync to Redis
	if err := h.redisStore.Set("state", state); err != nil {
		return nil, fmt.Errorf("failed to sync state to Redis: %w", err)
	}

	return state, nil
}

// GetMode retrieves current mode from Redis (fast)
func (h *HybridStore) GetMode() (Mode, error) {
	return h.redisStore.GetMode()
}

// SetMode sets the mode in Redis
func (h *HybridStore) SetMode(mode Mode) error {
	return h.redisStore.SetMode(mode)
}

// GetHealthStatus retrieves health from Redis
func (h *HybridStore) GetHealthStatus() (*Health, error) {
	return h.redisStore.GetHealthStatus()
}

// SetHealthStatus sets health in Redis
func (h *HybridStore) SetHealthStatus(health *Health) error {
	return h.redisStore.SetHealthStatus(health)
}

// GetShowState retrieves show state from Redis
func (h *HybridStore) GetShowState() (ShowState, error) {
	return h.redisStore.GetShowState()
}

// SetShowState sets show state in Redis
func (h *HybridStore) SetShowState(showState ShowState) error {
	return h.redisStore.SetShowState(showState)
}

// AddTask adds a task to both stores
func (h *HybridStore) AddTask(task *Task) error {
	// Add to Redis (real-time)
	if err := h.redisStore.AddTask(task); err != nil {
		return fmt.Errorf("failed to add task to Redis: %w", err)
	}

	// Add to file (persistent)
	return h.fileStore.AppendToQueue(task)
}

// GetTasks retrieves tasks from Redis
func (h *HybridStore) GetTasks() ([]*Task, error) {
	return h.redisStore.GetPendingTasks()
}

// RemoveTask removes a task from both stores
func (h *HybridStore) RemoveTask(taskID string) error {
	// Remove from Redis
	if err := h.redisStore.RemoveTask(taskID); err != nil {
		return fmt.Errorf("failed to remove task from Redis: %w", err)
	}

	// Remove from file
	return h.fileStore.RemoveFromQueue(taskID)
}

// AddError adds an error to both stores
func (h *HybridStore) AddError(err *Error) error {
	// Add to Redis (real-time)
	if err := h.redisStore.AddError(err); err != nil {
		return fmt.Errorf("failed to add error to Redis: %w", err)
	}

	// Log to learnings file
	learning := fmt.Sprintf("# Error: %s\nService: %s\nSeverity: %s\nMessage: %s",
		err.ID, err.Service, err.Severity, err.Message)
	return h.fileStore.AppendLearning(learning)
}

// GetErrors retrieves errors from Redis
func (h *HybridStore) GetErrors() ([]*Error, error) {
	return h.redisStore.GetActiveErrors()
}

// RemoveError removes an error from both stores
func (h *HybridStore) RemoveError(errorID string) error {
	// Remove from Redis
	if err := h.redisStore.RemoveError(errorID); err != nil {
		return fmt.Errorf("failed to remove error from Redis: %w", err)
	}

	// Log resolution to learnings
	learning := fmt.Sprintf("# Error Resolved: %s\nResolved at: %s",
		errorID, time.Now().Format(time.RFC3339))
	return h.fileStore.AppendLearning(learning)
}

// AddLearning adds a learning to the file store
func (h *HybridStore) AddLearning(learning string) error {
	return h.fileStore.AppendLearning(learning)
}

// GetLearnings retrieves learnings from the file store
func (h *HybridStore) GetLearnings() (string, error) {
	return h.fileStore.ReadLearnings()
}

// SaveProgram saves program constraints to file
func (h *HybridStore) SaveProgram(program string) error {
	return h.fileStore.SaveProgram(program)
}

// LoadProgram loads program constraints from file
func (h *HybridStore) LoadProgram() (string, error) {
	return h.fileStore.LoadProgram()
}

// Close closes both stores
func (h *HybridStore) Close() error {
	// Close Redis connection
	if err := h.redisStore.Close(); err != nil {
		return err
	}
	return nil
}

// GetFileStore returns the file store for direct access
func (h *HybridStore) GetFileStore() *FileStore {
	return h.fileStore
}
