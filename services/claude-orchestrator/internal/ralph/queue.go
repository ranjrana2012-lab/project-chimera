package ralph

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/project-chimera/claude-orchestrator/internal/state"
)

// QueueManager manages the task queue for the Ralph Loop
type QueueManager struct {
	store    *state.HybridStore
	ctx      context.Context
	mu       sync.RWMutex
	queue    []*state.Task
	priority map[string]int
}

// NewQueueManager creates a new queue manager
func NewQueueManager(store *state.HybridStore, ctx context.Context) *QueueManager {
	return &QueueManager{
		store:    store,
		ctx:      ctx,
		queue:    make([]*state.Task, 0),
		priority: make(map[string]int),
	}
}

// Start begins the queue manager
func (q *QueueManager) Start() {
	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			q.refreshQueue()

		case <-q.ctx.Done():
			return
		}
	}
}

// refreshQueue reloads the queue from storage
func (q *QueueManager) refreshQueue() {
	q.mu.Lock()
	defer q.mu.Unlock()

	tasks, err := q.store.GetTasks()
	if err != nil {
		return
	}

	// Filter pending and approved tasks
	q.queue = make([]*state.Task, 0)
	for _, task := range tasks {
		if task.Status == state.TaskStatusPending || task.Status == state.TaskStatusApproved {
			q.queue = append(q.queue, task)
		}
	}

	// Sort by priority
	q.sortByPriority()
}

// sortByPriority sorts the queue by task priority
func (q *QueueManager) sortByPriority() {
	// Simple bubble sort by priority (higher priority first)
	for i := 0; i < len(q.queue)-1; i++ {
		for j := 0; j < len(q.queue)-i-1; j++ {
			if q.queue[j].Priority < q.queue[j+1].Priority {
				q.queue[j], q.queue[j+1] = q.queue[j+1], q.queue[j]
			}
		}
	}
}

// Enqueue adds a task to the queue
func (q *QueueManager) Enqueue(task *state.Task) error {
	q.mu.Lock()
	defer q.mu.Unlock()

	// Set initial state
	task.Status = state.TaskStatusPending
	task.CreatedAt = time.Now()
	task.UpdatedAt = time.Now()

	// Add to store
	if err := q.store.AddTask(task); err != nil {
		return fmt.Errorf("failed to add task to store: %w", err)
	}

	// Add to queue
	q.queue = append(q.queue, task)
	q.sortByPriority()

	return nil
}

// Dequeue removes and returns the next task from the queue
func (q *QueueManager) Dequeue() (*state.Task, error) {
	q.mu.Lock()
	defer q.mu.Unlock()

	if len(q.queue) == 0 {
		return nil, fmt.Errorf("queue is empty")
	}

	// Get first task
	task := q.queue[0]
	q.queue = q.queue[1:]

	return task, nil
}

// Peek returns the next task without removing it
func (q *QueueManager) Peek() *state.Task {
	q.mu.RLock()
	defer q.mu.RUnlock()

	if len(q.queue) == 0 {
		return nil
	}

	return q.queue[0]
}

// GetQueue returns a copy of the current queue
func (q *QueueManager) GetQueue() []*state.Task {
	q.mu.RLock()
	defer q.mu.RUnlock()

	result := make([]*state.Task, len(q.queue))
	copy(result, q.queue)
	return result
}

// GetSize returns the current queue size
func (q *QueueManager) GetSize() int {
	q.mu.RLock()
	defer q.mu.RUnlock()
	return len(q.queue)
}

// ApproveTask approves a task for execution
func (q *QueueManager) ApproveTask(taskID string) error {
	tasks, err := q.store.GetTasks()
	if err != nil {
		return err
	}

	for _, task := range tasks {
		if task.ID == taskID {
			task.Status = state.TaskStatusApproved
			task.Approved = true
			task.UpdatedAt = time.Now()

			// Update in store
			if err := q.store.RemoveTask(taskID); err != nil {
				return err
			}
			if err := q.store.AddTask(task); err != nil {
				return err
			}

			// Refresh queue
			q.refreshQueue()
			return nil
		}
	}

	return fmt.Errorf("task not found: %s", taskID)
}

// DenyTask denies a task
func (q *QueueManager) DenyTask(taskID string) error {
	tasks, err := q.store.GetTasks()
	if err != nil {
		return err
	}

	for _, task := range tasks {
		if task.ID == taskID {
			task.Status = state.TaskStatusDenied
			task.UpdatedAt = time.Now()

			// Update in store
			if err := q.store.RemoveTask(taskID); err != nil {
				return err
			}
			if err := q.store.AddTask(task); err != nil {
				return err
			}

			// Refresh queue
			q.refreshQueue()
			return nil
		}
	}

	return fmt.Errorf("task not found: %s", taskID)
}

// CancelTask cancels a task
func (q *QueueManager) CancelTask(taskID string) error {
	if err := q.store.RemoveTask(taskID); err != nil {
		return err
	}

	q.refreshQueue()
	return nil
}

// PrioritizeTask updates the priority of a task
func (q *QueueManager) PrioritizeTask(taskID string, priority int) error {
	tasks, err := q.store.GetTasks()
	if err != nil {
		return err
	}

	for _, task := range tasks {
		if task.ID == taskID {
			task.Priority = priority
			task.UpdatedAt = time.Now()

			// Update in store
			if err := q.store.RemoveTask(taskID); err != nil {
				return err
			}
			if err := q.store.AddTask(task); err != nil {
				return err
			}

			// Refresh queue
			q.refreshQueue()
			return nil
		}
	}

	return fmt.Errorf("task not found: %s", taskID)
}

// GetTask retrieves a specific task from the queue
func (q *QueueManager) GetTask(taskID string) *state.Task {
	q.mu.RLock()
	defer q.mu.RUnlock()

	for _, task := range q.queue {
		if task.ID == taskID {
			return task
		}
	}

	return nil
}
