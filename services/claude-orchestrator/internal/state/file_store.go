package state

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"
)

// FileStore implements file-based persistence
type FileStore struct {
	basePath string
	mu       sync.RWMutex
}

// NewFileStore creates a new file-based store
func NewFileStore(basePath string) (*FileStore, error) {
	if err := os.MkdirAll(basePath, 0755); err != nil {
		return nil, fmt.Errorf("failed to create state directory: %w", err)
	}
	return &FileStore{
		basePath: basePath,
	}, nil
}

// Get retrieves a value from file store
func (f *FileStore) Get(key string) (interface{}, error) {
	f.mu.RLock()
	defer f.mu.RUnlock()

	path := filepath.Join(f.basePath, key+".json")
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, err
	}

	var value interface{}
	if err := json.Unmarshal(data, &value); err != nil {
		return nil, err
	}
	return value, nil
}

// Set stores a value in file store
func (f *FileStore) Set(key string, value interface{}) error {
	f.mu.Lock()
	defer f.mu.Unlock()

	data, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		return err
	}

	path := filepath.Join(f.basePath, key+".json")
	return os.WriteFile(path, data, 0644)
}

// Delete removes a value from file store
func (f *FileStore) Delete(key string) error {
	f.mu.Lock()
	defer f.mu.Unlock()

	path := filepath.Join(f.basePath, key+".json")
	return os.Remove(path)
}

// Snapshot saves the current state to a snapshot file
func (f *FileStore) Snapshot(state *State) error {
	f.mu.Lock()
	defer f.mu.Unlock()

	data, err := json.MarshalIndent(state, "", "  ")
	if err != nil {
		return err
	}

	path := filepath.Join(f.basePath, "state.json")
	return os.WriteFile(path, data, 0644)
}

// Restore loads the state from snapshot file
func (f *FileStore) Restore() (*State, error) {
	f.mu.RLock()
	defer f.mu.RUnlock()

	path := filepath.Join(f.basePath, "state.json")
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, err
	}

	var state State
	if err := json.Unmarshal(data, &state); err != nil {
		return nil, err
	}
	return &state, nil
}

// AppendToQueue appends a task to the queue file
func (f *FileStore) AppendToQueue(task *Task) error {
	f.mu.Lock()
	defer f.mu.Unlock()

	path := filepath.Join(f.basePath, "queue.txt")
	file, err := os.OpenFile(path, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return err
	}
	defer file.Close()

	_, err = fmt.Fprintf(file, "%s\n", task.ID)
	return err
}

// ReadQueue reads all tasks from the queue file
func (f *FileStore) ReadQueue() ([]string, error) {
	f.mu.RLock()
	defer f.mu.RUnlock()

	path := filepath.Join(f.basePath, "queue.txt")
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return []string{}, nil
		}
		return nil, err
	}

	// Parse lines (non-empty)
	var tasks []string
	lines := fmt.Sprintf("%s", data)
	for _, line := range splitLines(lines) {
		if line != "" {
			tasks = append(tasks, line)
		}
	}
	return tasks, nil
}

// RemoveFromQueue removes a task from the queue file
func (f *FileStore) RemoveFromQueue(taskID string) error {
	f.mu.Lock()
	defer f.mu.Unlock()

	path := filepath.Join(f.basePath, "queue.txt")
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}

	// Filter out the task
	lines := splitLines(fmt.Sprintf("%s", data))
	var newLines []string
	for _, line := range lines {
		if line != taskID {
			newLines = append(newLines, line)
		}
	}

	// Write back
	output := ""
	for _, line := range newLines {
		if line != "" {
			output += line + "\n"
		}
	}
	return os.WriteFile(path, []byte(output), 0644)
}

// AppendLearning appends a learning to the learnings file
func (f *FileStore) AppendLearning(learning string) error {
	f.mu.Lock()
	defer f.mu.Unlock()

	path := filepath.Join(f.basePath, "learnings.md")
	file, err := os.OpenFile(path, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return err
	}
	defer file.Close()

	_, err = fmt.Fprintf(file, "## %s\n%s\n\n", time.Now().Format(time.RFC3339), learning)
	return err
}

// ReadLearnings reads all learnings from the learnings file
func (f *FileStore) ReadLearnings() (string, error) {
	f.mu.RLock()
	defer f.mu.RUnlock()

	path := filepath.Join(f.basePath, "learnings.md")
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return "", nil
		}
		return "", err
	}
	return string(data), nil
}

// SaveProgram saves the program constraints
func (f *FileStore) SaveProgram(program string) error {
	f.mu.Lock()
	defer f.mu.Unlock()

	path := filepath.Join(f.basePath, "program.md")
	return os.WriteFile(path, []byte(program), 0644)
}

// LoadProgram loads the program constraints
func (f *FileStore) LoadProgram() (string, error) {
	f.mu.RLock()
	defer f.mu.RUnlock()

	path := filepath.Join(f.basePath, "program.md")
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return "", nil
		}
		return "", err
	}
	return string(data), nil
}

// Helper function to split lines
func splitLines(s string) []string {
	var lines []string
	current := ""
	for _, ch := range s {
		if ch == '\n' {
			lines = append(lines, current)
			current = ""
		} else {
			current += string(ch)
		}
	}
	if current != "" {
		lines = append(lines, current)
	}
	return lines
}
