package ralph

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"time"
)

// LearningsSystem manages insights and learnings from Ralph Loop iterations
type LearningsSystem struct {
	stateDir string
	mu       sync.RWMutex
	filePath string
}

// NewLearningsSystem creates a new learnings system
func NewLearningsSystem(stateDir string) *LearningsSystem {
	filePath := filepath.Join(stateDir, "learnings.md")

	return &LearningsSystem{
		stateDir: stateDir,
		filePath: filePath,
	}
}

// Learning represents a single learning entry
type Learning struct {
	ID        string    `json:"id"`
	Type      string    `json:"type"`
	Content   string    `json:"content"`
	Tags      []string  `json:"tags"`
	Timestamp time.Time `json:"timestamp"`
	Source    string    `json:"source"`
}

// LearningFilter defines criteria for filtering learnings
type LearningFilter struct {
	Type      string
	Tags      []string
	StartDate time.Time
	EndDate   time.Time
	Source    string
}

// AddLearning adds a new learning
func (l *LearningsSystem) AddLearning(learning *Learning) error {
	l.mu.Lock()
	defer l.mu.Unlock()

	// Set defaults
	if learning.ID == "" {
		learning.ID = generateLearningID()
	}
	if learning.Timestamp.IsZero() {
		learning.Timestamp = time.Now()
	}

	// Format learning entry
	entry := l.formatLearning(learning)

	// Append to learnings file
	f, err := os.OpenFile(l.filePath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return fmt.Errorf("failed to open learnings file: %w", err)
	}
	defer f.Close()

	_, err = fmt.Fprintln(f, entry)
	return err
}

// formatLearning formats a learning as markdown
func (l *LearningsSystem) formatLearning(learning *Learning) string {
	var sb strings.Builder

	sb.WriteString(fmt.Sprintf("## [%s] %s\n", learning.Timestamp.Format("2006-01-02T15:04:05Z"), learning.Type))
	sb.WriteString(fmt.Sprintf("**ID:** %s\n", learning.ID))
	sb.WriteString(fmt.Sprintf("**Source:** %s\n", learning.Source))

	if len(learning.Tags) > 0 {
		sb.WriteString("**Tags:** ")
		sb.WriteString(strings.Join(learning.Tags, ", "))
		sb.WriteString("\n")
	}

	sb.WriteString(fmt.Sprintf("\n%s\n\n", learning.Content))

	return sb.String()
}

// GetLearnings retrieves all learnings
func (l *LearningsSystem) GetLearnings(filter *LearningFilter) ([]*Learning, error) {
	l.mu.RLock()
	defer l.mu.RUnlock()

	// Read learnings file
	content, err := os.ReadFile(l.filePath)
	if err != nil {
		if os.IsNotExist(err) {
			return []*Learning{}, nil
		}
		return nil, err
	}

	// Parse learnings
	learnings := l.parseLearnings(string(content))

	// Apply filter
	if filter != nil {
		learnings = l.applyFilter(learnings, filter)
	}

	// Sort by timestamp (newest first)
	sort.Slice(learnings, func(i, j int) bool {
		return learnings[i].Timestamp.After(learnings[j].Timestamp)
	})

	return learnings, nil
}

// parseLearnings parses learnings from markdown content
func (l *LearningsSystem) parseLearnings(content string) []*Learning {
	var learnings []*Learning

	// Split by learning entries (marked with ##)
	entries := strings.Split(content, "\n## ")

	for _, entry := range entries {
		if strings.TrimSpace(entry) == "" {
			continue
		}

		learning := l.parseLearningEntry("## " + entry)
		if learning != nil {
			learnings = append(learnings, learning)
		}
	}

	return learnings
}

// parseLearningEntry parses a single learning entry
func (l *LearningsSystem) parseLearningEntry(entry string) *Learning {
	lines := strings.Split(entry, "\n")
	if len(lines) < 2 {
		return nil
	}

	learning := &Learning{}

	// Parse header
	header := strings.TrimPrefix(lines[0], "## ")
	header = strings.TrimSpace(header)

	// Extract timestamp and type
	if idx := strings.Index(header, "] "); idx > 0 {
		timestampStr := header[1:idx]
		if timestamp, err := time.Parse("2006-01-02T15:04:05Z", timestampStr); err == nil {
			learning.Timestamp = timestamp
		}

		rest := header[idx+2:]
		if idx := strings.Index(rest, " **ID:**"); idx > 0 {
			learning.Type = strings.TrimSpace(rest[:idx])
		}
	}

	// Parse metadata fields
	var contentLines []string
	inContent := false

	for _, line := range lines[1:] {
		if strings.HasPrefix(line, "**ID:**") {
			learning.ID = strings.TrimPrefix(line, "**ID:** ")
			learning.ID = strings.TrimSpace(learning.ID)
		} else if strings.HasPrefix(line, "**Source:**") {
			learning.Source = strings.TrimPrefix(line, "**Source:** ")
			learning.Source = strings.TrimSpace(learning.Source)
		} else if strings.HasPrefix(line, "**Tags:**") {
			tagsStr := strings.TrimPrefix(line, "**Tags:** ")
			tagsStr = strings.TrimSpace(tagsStr)
			if tagsStr != "" {
				learning.Tags = strings.Split(tagsStr, ", ")
				for i, tag := range learning.Tags {
					learning.Tags[i] = strings.TrimSpace(tag)
				}
			}
		} else if line == "" {
			if inContent {
				break
			}
			inContent = true
		} else if inContent {
			contentLines = append(contentLines, line)
		}
	}

	learning.Content = strings.Join(contentLines, "\n")
	return learning
}

// applyFilter applies filter criteria to learnings
func (l *LearningsSystem) applyFilter(learnings []*Learning, filter *LearningFilter) []*Learning {
	var filtered []*Learning

	for _, learning := range learnings {
		if !l.matchesFilter(learning, filter) {
			continue
		}
		filtered = append(filtered, learning)
	}

	return filtered
}

// matchesFilter checks if a learning matches the filter criteria
func (l *LearningsSystem) matchesFilter(learning *Learning, filter *LearningFilter) bool {
	if filter.Type != "" && learning.Type != filter.Type {
		return false
	}

	if !filter.StartDate.IsZero() && learning.Timestamp.Before(filter.StartDate) {
		return false
	}

	if !filter.EndDate.IsZero() && learning.Timestamp.After(filter.EndDate) {
		return false
	}

	if filter.Source != "" && learning.Source != filter.Source {
		return false
	}

	if len(filter.Tags) > 0 {
		hasTag := false
		for _, filterTag := range filter.Tags {
			for _, learningTag := range learning.Tags {
				if learningTag == filterTag {
					hasTag = true
					break
				}
			}
		}
		if !hasTag {
			return false
		}
	}

	return true
}

// SearchLearnings searches for learnings by content
func (l *LearningsSystem) SearchLearnings(query string) ([]*Learning, error) {
	learnings, err := l.GetLearnings(nil)
	if err != nil {
		return nil, err
	}

	var results []*Learning
	queryLower := strings.ToLower(query)

	for _, learning := range learnings {
		content := strings.ToLower(learning.Content)
		if strings.Contains(content, queryLower) {
			results = append(results, learning)
		}
	}

	return results, nil
}

// GetLearningByID retrieves a specific learning by ID
func (l *LearningsSystem) GetLearningByID(id string) (*Learning, error) {
	learnings, err := l.GetLearnings(nil)
	if err != nil {
		return nil, err
	}

	for _, learning := range learnings {
		if learning.ID == id {
			return learning, nil
		}
	}

	return nil, fmt.Errorf("learning not found: %s", id)
}

// ExportLearnings exports learnings to JSON
func (l *LearningsSystem) ExportLearnings(filter *LearningFilter) (string, error) {
	learnings, err := l.GetLearnings(filter)
	if err != nil {
		return "", err
	}

	data, err := json.MarshalIndent(learnings, "", "  ")
	if err != nil {
		return "", err
	}

	return string(data), nil
}

// ImportLearnings imports learnings from JSON
func (l *LearningsSystem) ImportLearnings(jsonData string) error {
	var learnings []*Learning
	if err := json.Unmarshal([]byte(jsonData), &learnings); err != nil {
		return err
	}

	for _, learning := range learnings {
		if err := l.AddLearning(learning); err != nil {
			return err
		}
	}

	return nil
}

// GetTags retrieves all unique tags from learnings
func (l *LearningsSystem) GetTags() ([]string, error) {
	learnings, err := l.GetLearnings(nil)
	if err != nil {
		return nil, err
	}

	tagMap := make(map[string]bool)
	for _, learning := range learnings {
		for _, tag := range learning.Tags {
			tagMap[tag] = true
		}
	}

	tags := make([]string, 0, len(tagMap))
	for tag := range tagMap {
		tags = append(tags, tag)
	}

	sort.Strings(tags)
	return tags, nil
}

// GetStatistics returns statistics about learnings
func (l *LearningsSystem) GetStatistics() (*LearningStatistics, error) {
	learnings, err := l.GetLearnings(nil)
	if err != nil {
		return nil, err
	}

	stats := &LearningStatistics{
		Total:      len(learnings),
		TypeCounts: make(map[string]int),
		TagCounts:  make(map[string]int),
	}

	for _, learning := range learnings {
		stats.TypeCounts[learning.Type]++
		for _, tag := range learning.Tags {
			stats.TagCounts[tag]++
		}
	}

	return stats, nil
}

// LearningStatistics represents statistics about learnings
type LearningStatistics struct {
	Total      int            `json:"total"`
	TypeCounts map[string]int `json:"type_counts"`
	TagCounts  map[string]int `json:"tag_counts"`
}

// generateLearningID generates a unique learning ID
func generateLearningID() string {
	return fmt.Sprintf("learning-%d", time.Now().UnixNano())
}

// AddTaskLearning adds a task-related learning
func (l *LearningsSystem) AddTaskLearning(taskID, content string) error {
	learning := &Learning{
		Type:    "task",
		Content: content,
		Tags:    []string{"task", taskID},
		Source:  "ralph-loop",
	}

	return l.AddLearning(learning)
}

// AddErrorLearning adds an error-related learning
func (l *LearningsSystem) AddErrorLearning(errorID, content string) error {
	learning := &Learning{
		Type:    "error",
		Content: content,
		Tags:    []string{"error", errorID},
		Source:  "ralph-loop",
	}

	return l.AddLearning(learning)
}

// AddSuccessLearning adds a success-related learning
func (l *LearningsSystem) AddSuccessLearning(content string) error {
	learning := &Learning{
		Type:    "success",
		Content: content,
		Tags:    []string{"success"},
		Source:  "ralph-loop",
	}

	return l.AddLearning(learning)
}
