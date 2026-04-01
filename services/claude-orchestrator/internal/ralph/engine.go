package ralph

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/project-chimera/claude-orchestrator/internal/state"
)

// Engine manages the Ralph Loop continuous execution
type Engine struct {
	store          *state.HybridStore
	ctx            context.Context
	cancel         context.CancelFunc
	mu             sync.RWMutex
	iteration      int
	maxIterations  int
	active         bool
	paused         bool
	lastAction     string
	lastResult     string
	progressStreak int
	stateDir       string
	completionPromise string
}

// Config represents Ralph Loop configuration
type Config struct {
	StateDir          string        `json:"state_dir"`
	MaxIterations     int           `json:"max_iterations"`
	CheckInterval     time.Duration `json:"check_interval"`
	CompletionPromise string        `json:"completion_promise"`
}

// NewEngine creates a new Ralph Loop engine
func NewEngine(store *state.HybridStore, cfg Config) (*Engine, error) {
	ctx, cancel := context.WithCancel(context.Background())

	// Ensure state directory exists
	if err := os.MkdirAll(cfg.StateDir, 0755); err != nil {
		cancel()
		return nil, fmt.Errorf("failed to create state directory: %w", err)
	}

	return &Engine{
		store:            store,
		ctx:              ctx,
		cancel:           cancel,
		iteration:        0,
		maxIterations:    cfg.MaxIterations,
		active:           false,
		paused:           false,
		stateDir:         cfg.StateDir,
		completionPromise: cfg.CompletionPromise,
	}, nil
}

// Start begins the Ralph Loop execution
func (e *Engine) Start() {
	e.mu.Lock()
	if e.active {
		e.mu.Unlock()
		return
	}
	e.active = true
	e.mu.Unlock()

	// Start main loop
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			if e.paused {
				continue
			}
			e.runIteration()

		case <-e.ctx.Done():
			e.mu.Lock()
			e.active = false
			e.mu.Unlock()
			return
		}
	}
}

// Stop stops the Ralph Loop
func (e *Engine) Stop() {
	e.cancel()
}

// Pause pauses the Ralph Loop
func (e *Engine) Pause() {
	e.mu.Lock()
	defer e.mu.Unlock()
	e.paused = true
}

// Resume resumes the Ralph Loop
func (e *Engine) Resume() {
	e.mu.Lock()
	defer e.mu.Unlock()
	e.paused = false
}

// runIteration executes a single Ralph Loop iteration
func (e *Engine) runIteration() {
	e.mu.Lock()
	e.iteration++
	currentIteration := e.iteration
	e.mu.Unlock()

	// Check max iterations
	if e.maxIterations > 0 && currentIteration > e.maxIterations {
		e.Stop()
		return
	}

	// Get tasks from queue
	tasks, err := e.store.GetTasks()
	if err != nil {
		e.lastResult = fmt.Sprintf("Failed to get tasks: %v", err)
		return
	}

	// Process pending tasks
	for _, task := range tasks {
		if task.Status == state.TaskStatusPending && task.Approved {
			e.executeTask(task)
		}
	}

	// Check completion promise
	if e.completionPromise != "" {
		if e.checkCompletion() {
			e.Stop()
			e.logLearning(fmt.Sprintf("Completion promise met: %s", e.completionPromise))
			return
		}
	}

	e.lastAction = fmt.Sprintf("Iteration %d completed", currentIteration)
	e.lastResult = fmt.Sprintf("Processed %d tasks", len(tasks))
}

// executeTask executes a single task through the Ralph Loop phases
func (e *Engine) executeTask(task *state.Task) {
	// Update task status
	task.Status = state.TaskStatusInProgress
	task.UpdatedAt = time.Now()
	now := time.Now()
	task.StartedAt = &now
	e.store.AddTask(task)

	// Execute phases: Discuss, Plan, Execute, Verify
	result := e.executePhases(task)

	// Update task with result
	task.UpdatedAt = time.Now()
	if result.Error != nil {
		task.Status = state.TaskStatusFailed
		task.Error = result.Error.Error()
		task.RetryCount++
		e.logLearning(fmt.Sprintf("Task %s failed: %v", task.ID, result.Error))
	} else {
		task.Status = state.TaskStatusCompleted
		task.Result = result.Output
		completedNow := time.Now()
		task.CompletedAt = &completedNow
		e.logLearning(fmt.Sprintf("Task %s completed: %s", task.ID, result.Output))
	}

	e.store.AddTask(task)
}

// executePhases runs the Ralph Loop phases for a task
func (e *Engine) executePhases(task *state.Task) *ExecutionResult {
	result := &ExecutionResult{}

	// Phase 1: Discuss - Generate approach
	discussion, err := e.discussPhase(task)
	if err != nil {
		result.Error = err
		return result
	}

	// Phase 2: Plan - Generate execution plan
	plan, err := e.planPhase(task, discussion)
	if err != nil {
		result.Error = err
		return result
	}

	// Phase 3: Execute - Execute the plan
	output, err := e.executePhase(task, plan)
	if err != nil {
		result.Error = err
		return result
	}
	result.Output = output

	// Phase 4: Verify - Verify the outcome
	if err := e.verifyPhase(task, output); err != nil {
		result.Error = err
		return result
	}

	// Update progress streak
	e.mu.Lock()
	e.progressStreak++
	e.mu.Unlock()

	return result
}

// discussPhase generates approach discussion
func (e *Engine) discussPhase(task *state.Task) (string, error) {
	// TODO: Implement LLM call for discussion
	return fmt.Sprintf("Discussion for task %s: Analyzing requirements and constraints", task.ID), nil
}

// planPhase generates execution plan
func (e *Engine) planPhase(task *state.Task, discussion string) (string, error) {
	// TODO: Implement LLM call for planning
	return fmt.Sprintf("Plan for task %s: Step 1, Step 2, Step 3", task.ID), nil
}

// executePhase executes the plan
func (e *Engine) executePhase(task *state.Task, plan string) (string, error) {
	// TODO: Implement actual execution
	return fmt.Sprintf("Executed task %s successfully", task.ID), nil
}

// verifyPhase verifies the execution outcome
func (e *Engine) verifyPhase(task *state.Task, output string) error {
	// TODO: Implement verification logic
	return nil
}

// checkCompletion checks if the completion promise is met
func (e *Engine) checkCompletion() bool {
	// TODO: Implement completion promise checking
	return false
}

// logLearning appends a learning to the learnings file
func (e *Engine) logLearning(learning string) error {
	learningsFile := filepath.Join(e.stateDir, "learnings.md")
	f, err := os.OpenFile(learningsFile, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return err
	}
	defer f.Close()

	timestamp := time.Now().Format("2006-01-02T15:04:05Z")
	_, err = fmt.Fprintf(f, "## [%s] %s\n\n%s\n\n", timestamp, "Ralph Loop", learning)
	return err
}

// GetStatus returns the current Ralph Loop status
func (e *Engine) GetStatus() *Status {
	e.mu.RLock()
	defer e.mu.RUnlock()

	return &Status{
		Active:         e.active,
		Iteration:      e.iteration,
		MaxIterations:  e.maxIterations,
		Paused:         e.paused,
		LastAction:     e.lastAction,
		LastResult:     e.lastResult,
		ProgressStreak: e.progressStreak,
	}
}

// ExecutionResult represents the result of task execution
type ExecutionResult struct {
	Output string
	Error  error
}

// Status represents the Ralph Loop status
type Status struct {
	Active         bool   `json:"active"`
	Iteration      int    `json:"iteration"`
	MaxIterations  int    `json:"max_iterations"`
	Paused         bool   `json:"paused"`
	LastAction     string `json:"last_action"`
	LastResult     string `json:"last_result"`
	ProgressStreak int    `json:"progress_streak"`
}
