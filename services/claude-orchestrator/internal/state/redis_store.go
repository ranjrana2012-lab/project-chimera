package state

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/go-redis/redis/v8"
)

// RedisStore implements Redis-based persistence
type RedisStore struct {
	client *redis.Client
	ctx    context.Context
}

// NewRedisStore creates a new Redis store
func NewRedisStore(addr string) (*RedisStore, error) {
	client := redis.NewClient(&redis.Options{
		Addr:     addr,
		Password: "",
		DB:       0,
		PoolSize: 10,
	})

	// Test connection
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := client.Ping(ctx).Err(); err != nil {
		return nil, fmt.Errorf("failed to connect to Redis: %w", err)
	}

	return &RedisStore{
		client: client,
		ctx:    context.Background(),
	}, nil
}

// Get retrieves a value from Redis
func (r *RedisStore) Get(key string) (interface{}, error) {
	val, err := r.client.Get(r.ctx, key).Result()
	if err != nil {
		if err == redis.Nil {
			return nil, nil
		}
		return nil, err
	}

	var result interface{}
	if err := json.Unmarshal([]byte(val), &result); err != nil {
		return nil, err
	}
	return result, nil
}

// Set stores a value in Redis
func (r *RedisStore) Set(key string, value interface{}) error {
	data, err := json.Marshal(value)
	if err != nil {
		return err
	}

	return r.client.Set(r.ctx, key, data, 0).Err()
}

// Delete removes a value from Redis
func (r *RedisStore) Delete(key string) error {
	return r.client.Del(r.ctx, key).Err()
}

// SetWithTTL stores a value with TTL in Redis
func (r *RedisStore) SetWithTTL(key string, value interface{}, ttl time.Duration) error {
	data, err := json.Marshal(value)
	if err != nil {
		return err
	}

	return r.client.Set(r.ctx, key, data, ttl).Err()
}

// GetMode retrieves the current mode from Redis
func (r *RedisStore) GetMode() (Mode, error) {
	val, err := r.client.Get(r.ctx, "mode:current").Result()
	if err != nil {
		if err == redis.Nil {
			return ModeStandby, nil
		}
		return "", err
	}
	return Mode(val), nil
}

// SetMode sets the current mode in Redis
func (r *RedisStore) SetMode(mode Mode) error {
	return r.client.Set(r.ctx, "mode:current", string(mode), 0).Err()
}

// GetHealthStatus retrieves health status from Redis
func (r *RedisStore) GetHealthStatus() (*Health, error) {
	val, err := r.client.Get(r.ctx, "health:status").Result()
	if err != nil {
		if err == redis.Nil {
			return &Health{
				Services: make(map[string]ServiceHealth),
				Overall:  HealthStatusUnknown,
				SLOPass:  true,
			}, nil
		}
		return nil, err
	}

	var health Health
	if err := json.Unmarshal([]byte(val), &health); err != nil {
		return nil, err
	}
	return &health, nil
}

// SetHealthStatus sets health status in Redis
func (r *RedisStore) SetHealthStatus(health *Health) error {
	data, err := json.Marshal(health)
	if err != nil {
		return err
	}
	return r.client.Set(r.ctx, "health:status", data, 0).Err()
}

// GetShowState retrieves show state from Redis
func (r *RedisStore) GetShowState() (ShowState, error) {
	val, err := r.client.Get(r.ctx, "show:state").Result()
	if err != nil {
		if err == redis.Nil {
			return ShowStateUnknown, nil
		}
		return ShowStateUnknown, err
	}

	var state ShowState
	if err := json.Unmarshal([]byte(val), &state); err != nil {
		return ShowStateUnknown, err
	}
	return state, nil
}

// SetShowState sets show state in Redis
func (r *RedisStore) SetShowState(state ShowState) error {
	data, err := json.Marshal(state)
	if err != nil {
		return err
	}
	return r.client.Set(r.ctx, "show:state", data, 0).Err()
}

// AddTask adds a task to the pending tasks list in Redis
func (r *RedisStore) AddTask(task *Task) error {
	data, err := json.Marshal(task)
	if err != nil {
		return err
	}
	return r.client.LPush(r.ctx, "tasks:pending", data).Err()
}

// GetPendingTasks retrieves all pending tasks from Redis
func (r *RedisStore) GetPendingTasks() ([]*Task, error) {
 vals, err := r.client.LRange(r.ctx, "tasks:pending", 0, -1).Result()
	if err != nil {
		return nil, err
	}

	var tasks []*Task
	for _, val := range vals {
		var task Task
		if err := json.Unmarshal([]byte(val), &task); err != nil {
			continue
		}
		tasks = append(tasks, &task)
	}
	return tasks, nil
}

// RemoveTask removes a task from pending tasks in Redis
func (r *RedisStore) RemoveTask(taskID string) error {
	tasks, err := r.GetPendingTasks()
	if err != nil {
		return err
	}

	// Filter out the task
	var updated []*Task
	for _, task := range tasks {
		if task.ID != taskID {
			updated = append(updated, task)
		}
	}

	// Clear and re-add
	if err := r.client.Del(r.ctx, "tasks:pending").Err(); err != nil {
		return err
	}

	for _, task := range updated {
		data, err := json.Marshal(task)
		if err != nil {
			return err
		}
		if err := r.client.LPush(r.ctx, "tasks:pending", data).Err(); err != nil {
			return err
		}
	}

	return nil
}

// AddError adds an error to the active errors list in Redis
func (r *RedisStore) AddError(err *Error) error {
	data, marshalErr := json.Marshal(err)
	if marshalErr != nil {
		return marshalErr
	}
	return r.client.LPush(r.ctx, "errors:active", data).Err()
}

// GetActiveErrors retrieves all active errors from Redis
func (r *RedisStore) GetActiveErrors() ([]*Error, error) {
	vals, err := r.client.LRange(r.ctx, "errors:active", 0, -1).Result()
	if err != nil {
		return nil, err
	}

	var errors []*Error
	for _, val := range vals {
		var e Error
		if err := json.Unmarshal([]byte(val), &e); err != nil {
			continue
		}
		errors = append(errors, &e)
	}
	return errors, nil
}

// RemoveError removes an error from active errors in Redis
func (r *RedisStore) RemoveError(errorID string) error {
	errors, err := r.GetActiveErrors()
	if err != nil {
		return err
	}

	// Filter out the error
	var updated []*Error
	for _, e := range errors {
		if e.ID != errorID {
			updated = append(updated, e)
		}
	}

	// Clear and re-add
	if err := r.client.Del(r.ctx, "errors:active").Err(); err != nil {
		return err
	}

	for _, e := range updated {
		data, err := json.Marshal(e)
		if err != nil {
			return err
		}
		if err := r.client.LPush(r.ctx, "errors:active", data).Err(); err != nil {
			return err
		}
	}

	return nil
}

// Close closes the Redis connection
func (r *RedisStore) Close() error {
	return r.client.Close()
}
