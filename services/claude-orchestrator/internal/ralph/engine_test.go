package ralph

import (
	"testing"
	"time"

	"github.com/project-chimera/claude-orchestrator/internal/state"
)

func TestNewEngine(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	cfg := Config{
		StateDir:      tmpDir,
		MaxIterations: 10,
		CheckInterval: 5 * time.Second,
	}

	engine, err := NewEngine(store, cfg)
	if err != nil {
		t.Fatalf("Failed to create engine: %v", err)
	}

	if engine == nil {
		t.Fatal("NewEngine returned nil")
	}

	if engine.maxIterations != 10 {
		t.Errorf("MaxIterations = %d, want 10", engine.maxIterations)
	}
}

func TestEngineStatus(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	cfg := Config{
		StateDir:      tmpDir,
		MaxIterations: 100,
		CheckInterval: 5 * time.Second,
	}

	engine, err := NewEngine(store, cfg)
	if err != nil {
		t.Fatalf("Failed to create engine: %v", err)
	}

	status := engine.GetStatus()
	if status == nil {
		t.Fatal("GetStatus returned nil")
	}

	if status.Active {
		t.Error("Engine should not be active initially")
	}

	if status.Iteration != 0 {
		t.Errorf("Initial iteration = %d, want 0", status.Iteration)
	}
}

func TestEnginePauseResume(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	cfg := Config{
		StateDir:      tmpDir,
		MaxIterations: 100,
		CheckInterval: 5 * time.Second,
	}

	engine, err := NewEngine(store, cfg)
	if err != nil {
		t.Fatalf("Failed to create engine: %v", err)
	}

	// Test pause
	engine.Pause()
	status := engine.GetStatus()
	if !status.Paused {
		t.Error("Engine should be paused after Pause()")
	}

	// Test resume
	engine.Resume()
	status = engine.GetStatus()
	if status.Paused {
		t.Error("Engine should not be paused after Resume()")
	}
}

func TestQueueManager(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	qm := NewQueueManager(store, nil)

	if qm == nil {
		t.Fatal("NewQueueManager returned nil")
	}

	// Test enqueue
	task := &state.Task{
		ID:       "test-task-1",
		Title:    "Test Task",
		Priority: 5,
	}

	err = qm.Enqueue(task)
	if err != nil {
		t.Fatalf("Failed to enqueue task: %v", err)
	}

	// Test queue size
	if qm.GetSize() != 1 {
		t.Errorf("Queue size = %d, want 1", qm.GetSize())
	}

	// Test peek
	peeked := qm.Peek()
	if peeked == nil {
		t.Fatal("Peek returned nil")
	}

	if peeked.ID != "test-task-1" {
		t.Errorf("Peeked task ID = %s, want test-task-1", peeked.ID)
	}
}

func TestQueueManagerDequeue(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	qm := NewQueueManager(store, nil)

	// Enqueue multiple tasks
	task1 := &state.Task{ID: "task-1", Title: "Task 1", Priority: 5}
	task2 := &state.Task{ID: "task-2", Title: "Task 2", Priority: 10}

	qm.Enqueue(task1)
	qm.Enqueue(task2)

	// Test dequeue - should get higher priority task first
	task, err := qm.Dequeue()
	if err != nil {
		t.Fatalf("Failed to dequeue: %v", err)
	}

	if task.ID != "task-2" {
		t.Errorf("Dequeued task ID = %s, want task-2 (higher priority)", task.ID)
	}

	// Queue size should now be 1
	if qm.GetSize() != 1 {
		t.Errorf("Queue size = %d, want 1", qm.GetSize())
	}
}

func TestGSDOrchestrator(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := state.NewHybridStore(tmpDir, "")
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	gsd := NewGSDOrchestrator(store, nil)

	if gsd == nil {
		t.Fatal("NewGSDOrchestrator returned nil")
	}

	// Clear any existing tasks first
	existingTasks, _ := store.GetTasks()
	for _, task := range existingTasks {
		store.RemoveTask(task.ID)
	}

	// Test create goal
	goal := &Goal{
		Title:       "Test Goal",
		Description: "Test goal description",
		Priority:    5,
	}

	err = gsd.CreateGoal(goal)
	if err != nil {
		t.Fatalf("Failed to create goal: %v", err)
	}

	// Verify goal was created
	tasks, _ := store.GetTasks()
	goalTasks := make([]*state.Task, 0)
	for _, task := range tasks {
		if task.Type == "goal" {
			goalTasks = append(goalTasks, task)
		}
	}

	if len(goalTasks) != 1 {
		t.Errorf("Goal tasks count = %d, want 1", len(goalTasks))
	}

	if len(goalTasks) > 0 && goalTasks[0].Type != "goal" {
		t.Errorf("Task type = %s, want goal", goalTasks[0].Type)
	}
}

func TestLearningsSystem(t *testing.T) {
	tmpDir := t.TempDir()
	ls := NewLearningsSystem(tmpDir)

	if ls == nil {
		t.Fatal("NewLearningsSystem returned nil")
	}

	// Test add learning
	learning := &Learning{
		Type:    "test",
		Content: "Test learning content",
		Tags:    []string{"test", "unit"},
		Source:  "test",
	}

	err := ls.AddLearning(learning)
	if err != nil {
		t.Fatalf("Failed to add learning: %v", err)
	}

	// Test get learnings
	learnings, err := ls.GetLearnings(nil)
	if err != nil {
		t.Fatalf("Failed to get learnings: %v", err)
	}

	if len(learnings) != 1 {
		t.Errorf("Learnings count = %d, want 1", len(learnings))
	}

	if learnings[0].Content != "Test learning content" {
		t.Errorf("Learning content = %s, want 'Test learning content'", learnings[0].Content)
	}
}

func TestLearningsSystemSearch(t *testing.T) {
	tmpDir := t.TempDir()
	ls := NewLearningsSystem(tmpDir)

	// Add multiple learnings
	ls.AddLearning(&Learning{
		Type:    "info",
		Content: "This is about testing",
		Tags:    []string{"test"},
		Source:  "test",
	})

	ls.AddLearning(&Learning{
		Type:    "info",
		Content: "This is about deployment",
		Tags:    []string{"deploy"},
		Source:  "test",
	})

	// Test search
	results, err := ls.SearchLearnings("testing")
	if err != nil {
		t.Fatalf("Failed to search learnings: %v", err)
	}

	if len(results) != 1 {
		t.Errorf("Search results count = %d, want 1", len(results))
	}
}
