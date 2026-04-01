package handlers

import (
	"context"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/project-chimera/claude-orchestrator/internal/state"
)

// TaskHandler handles task-related endpoints
type TaskHandler struct {
	store *state.HybridStore
	ctx   context.Context
}

// NewTaskHandler creates a new task handler
func NewTaskHandler(store *state.HybridStore, ctx context.Context) *TaskHandler {
	return &TaskHandler{
		store: store,
		ctx:   ctx,
	}
}

// List returns all tasks
func (h *TaskHandler) List(c *gin.Context) {
	tasks, err := h.store.GetTasks()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"tasks": tasks,
		"count": len(tasks),
	})
}

// CreateRequest represents a task creation request
type CreateRequest struct {
	Type             string `json:"type" binding:"required"`
	Title            string `json:"title" binding:"required"`
	Description      string `json:"description"`
	Priority         int    `json:"priority"`
	MaxRetries       int    `json:"max_retries"`
	RequiresApproval bool   `json:"requires_approval"`
}

// Create creates a new task
func (h *TaskHandler) Create(c *gin.Context) {
	var req CreateRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	task := &state.Task{
		ID:               uuid.New().String(),
		Type:             req.Type,
		Title:            req.Title,
		Description:      req.Description,
		Priority:         req.Priority,
		Status:           state.TaskStatusPending,
		CreatedAt:        time.Now(),
		UpdatedAt:        time.Now(),
		MaxRetries:       req.MaxRetries,
		RequiresApproval: req.RequiresApproval,
		Approved:         !req.RequiresApproval,
		RetryCount:       0,
	}

	if err := h.store.AddTask(task); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"task": task,
	})
}

// Get returns a specific task
func (h *TaskHandler) Get(c *gin.Context) {
	taskID := c.Param("task_id")

	tasks, _ := h.store.GetTasks()
	for _, task := range tasks {
		if task.ID == taskID {
			c.JSON(http.StatusOK, gin.H{
				"task": task,
			})
			return
		}
	}

	c.JSON(http.StatusNotFound, gin.H{"error": "Task not found"})
}

// Approve approves a task
func (h *TaskHandler) Approve(c *gin.Context) {
	taskID := c.Param("task_id")

	tasks, _ := h.store.GetTasks()
	for _, task := range tasks {
		if task.ID == taskID {
			task.Status = state.TaskStatusApproved
			task.Approved = true
			task.UpdatedAt = time.Now()

			if err := h.store.RemoveTask(taskID); err != nil {
				c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
				return
			}
			if err := h.store.AddTask(task); err != nil {
				c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
				return
			}

			c.JSON(http.StatusOK, gin.H{
				"message": "Task approved",
				"task":    task,
			})
			return
		}
	}

	c.JSON(http.StatusNotFound, gin.H{"error": "Task not found"})
}

// Deny denies a task
func (h *TaskHandler) Deny(c *gin.Context) {
	taskID := c.Param("task_id")

	tasks, _ := h.store.GetTasks()
	for _, task := range tasks {
		if task.ID == taskID {
			task.Status = state.TaskStatusDenied
			task.UpdatedAt = time.Now()

			if err := h.store.RemoveTask(taskID); err != nil {
				c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
				return
			}

			c.JSON(http.StatusOK, gin.H{
				"message": "Task denied",
				"task":    task,
			})
			return
		}
	}

	c.JSON(http.StatusNotFound, gin.H{"error": "Task not found"})
}

// Cancel cancels a task
func (h *TaskHandler) Cancel(c *gin.Context) {
	taskID := c.Param("task_id")

	if err := h.store.RemoveTask(taskID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Task cancelled",
		"task_id": taskID,
	})
}
