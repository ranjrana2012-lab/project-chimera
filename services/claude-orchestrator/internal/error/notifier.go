package error

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"net/smtp"
	"strings"
	"sync"
	"time"

	"github.com/project-chimera/claude-orchestrator/internal/policy"
	"github.com/project-chimera/claude-orchestrator/internal/state"
)

// Notifier handles sending notifications for various events
type Notifier struct {
	ctx          context.Context
	mu           sync.RWMutex
	channels     map[string]NotificationChannel
	webhooks     map[string]*WebhookConfig
	smtpConfig   *SMTPConfig
}

// NotificationChannel represents a notification channel
type NotificationChannel interface {
	Send(notification *Notification) error
}

// WebhookConfig represents a webhook configuration
type WebhookConfig struct {
	URL        string            `json:"url"`
	Method     string            `json:"method"`
	Headers    map[string]string `json:"headers"`
	Template   string            `json:"template"`
	RetryCount int               `json:"retry_count"`
	Timeout    time.Duration     `json:"timeout"`
}

// SMTPConfig represents SMTP configuration for email notifications
type SMTPConfig struct {
	Host     string `json:"host"`
	Port     int    `json:"port"`
	Username string `json:"username"`
	Password string `json:"password"`
	From     string `json:"from"`
	Subject  string `json:"subject"`
}

// Notification represents a notification message
type Notification struct {
	ID        string                 `json:"id"`
	Type      string                 `json:"type"`
	Severity  string                 `json:"severity"`
	Title     string                 `json:"title"`
	Body      string                 `json:"body"`
	Metadata  map[string]interface{} `json:"metadata"`
	Timestamp time.Time              `json:"timestamp"`
	Channels  []string               `json:"channels"`
}

// NewNotifier creates a new notifier
func NewNotifier(ctx context.Context) *Notifier {
	return &Notifier{
		ctx:      ctx,
		channels: make(map[string]NotificationChannel),
		webhooks: make(map[string]*WebhookConfig),
	}
}

// RegisterChannel registers a notification channel
func (n *Notifier) RegisterChannel(name string, channel NotificationChannel) error {
	n.mu.Lock()
	defer n.mu.Unlock()

	n.channels[name] = channel
	return nil
}

// RegisterWebhook registers a webhook for notifications
func (n *Notifier) RegisterWebhook(name string, config *WebhookConfig) error {
	n.mu.Lock()
	defer n.mu.Unlock()

	n.webhooks[name] = config
	return nil
}

// ConfigureSMTP configures SMTP for email notifications
func (n *Notifier) ConfigureSMTP(config *SMTPConfig) error {
	n.mu.Lock()
	defer n.mu.Unlock()

	n.smtpConfig = config
	return nil
}

// NotifyError sends an error notification
func (n *Notifier) NotifyError(err *state.Error, decision *policy.EscalationDecision) {
	notification := &Notification{
		ID:       fmt.Sprintf("error-%s", err.ID),
		Type:     "error",
		Severity: err.Severity.String(),
		Title:    fmt.Sprintf("Error in %s service", err.Service),
		Body:     err.Message,
		Metadata: map[string]interface{}{
			"error_id":  err.ID,
			"service":   err.Service,
			"severity":  err.Severity.String(),
			"retry_count": err.RetryCount,
		},
		Timestamp: time.Now(),
		Channels:  []string{"web", "email"},
	}

	n.Send(notification)
}

// NotifyErrorResolution sends an error resolution notification
func (n *Notifier) NotifyErrorResolution(err *state.Error, resolution string) {
	notification := &Notification{
		ID:       fmt.Sprintf("resolved-%s", err.ID),
		Type:     "resolution",
		Severity: "info",
		Title:    fmt.Sprintf("Error %s resolved", err.ID),
		Body:     resolution,
		Metadata: map[string]interface{}{
			"error_id":   err.ID,
			"service":    err.Service,
			"resolved_by": err.ResolvedBy,
			"resolved_at": err.ResolvedAt,
		},
		Timestamp: time.Now(),
		Channels:  []string{"web", "email"},
	}

	n.Send(notification)
}

// NotifyEscalation sends an escalation notification
func (n *Notifier) NotifyEscalation(event *EscalationEvent) {
	notification := &Notification{
		ID:       fmt.Sprintf("escalation-%s", event.Error.ID),
		Type:     "escalation",
		Severity: event.Error.Severity.String(),
		Title:    fmt.Sprintf("Escalation required for %s", event.Error.Service),
		Body:     fmt.Sprintf("Error requires escalation: %s\nReason: %s", event.Error.Message, event.Decision.Reason),
		Metadata: map[string]interface{}{
			"error_id":  event.Error.ID,
			"service":   event.Error.Service,
			"decision":  event.Decision,
			"rules":     event.Decision.Rules,
		},
		Timestamp: time.Now(),
		Channels:  []string{"web", "email", "pager"},
	}

	n.Send(notification)
}

// NotifyModeChange sends a mode change notification
func (n *Notifier) NotifyModeChange(from, to state.Mode, reason string) {
	notification := &Notification{
		ID:       fmt.Sprintf("mode-%d", time.Now().UnixNano()),
		Type:     "mode_change",
		Severity: "info",
		Title:    fmt.Sprintf("Mode transition: %s → %s", from, to),
		Body:     fmt.Sprintf("System mode changed from %s to %s\nReason: %s", from, to, reason),
		Metadata: map[string]interface{}{
			"from":   from.String(),
			"to":     to.String(),
			"reason": reason,
		},
		Timestamp: time.Now(),
		Channels:  []string{"web", "email"},
	}

	n.Send(notification)
}

// NotifyTaskCompletion sends a task completion notification
func (n *Notifier) NotifyTaskCompletion(task *state.Task) {
	severity := "info"
	if task.Status == state.TaskStatusFailed {
		severity = "warning"
	}

	notification := &Notification{
		ID:       fmt.Sprintf("task-%s", task.ID),
		Type:     "task_completion",
		Severity: severity,
		Title:    fmt.Sprintf("Task %s: %s", task.ID, task.Status),
		Body:     fmt.Sprintf("Task '%s' completed with status: %s\nResult: %s", task.Title, task.Status, task.Result),
		Metadata: map[string]interface{}{
			"task_id":    task.ID,
			"task_type":  task.Type,
			"status":     task.Status,
			"priority":   task.Priority,
			"created_at": task.CreatedAt,
		},
		Timestamp: time.Now(),
		Channels:  []string{"web"},
	}

	n.Send(notification)
}

// NotifyHealthChange sends a health status change notification
func (n *Notifier) NotifyHealthChange(service string, oldStatus, newStatus state.HealthStatus) {
	severity := "info"
	if newStatus == state.HealthStatusUnhealthy {
		severity = "critical"
	} else if newStatus == state.HealthStatusDegraded {
		severity = "warning"
	}

	notification := &Notification{
		ID:       fmt.Sprintf("health-%s-%d", service, time.Now().UnixNano()),
		Type:     "health_change",
		Severity: severity,
		Title:    fmt.Sprintf("Health status changed for %s", service),
		Body:     fmt.Sprintf("Service %s health status changed from %s to %s", service, oldStatus, newStatus),
		Metadata: map[string]interface{}{
			"service":    service,
			"old_status": oldStatus.String(),
			"new_status": newStatus.String(),
		},
		Timestamp: time.Now(),
		Channels:  []string{"web", "email"},
	}

	n.Send(notification)
}

// Send sends a notification through all configured channels
func (n *Notifier) Send(notification *Notification) {
	n.mu.RLock()
	defer n.mu.RUnlock()

	// Send to each channel
	for _, channelName := range notification.Channels {
		if channel, exists := n.channels[channelName]; exists {
			if err := channel.Send(notification); err != nil {
				log.Printf("Failed to send notification to channel %s: %v\n", channelName, err)
			}
		}
	}

	// Send to webhooks
	for _, webhook := range n.webhooks {
		n.sendWebhook(webhook, notification)
	}

	// Send email if configured
	if n.smtpConfig != nil {
		n.sendEmail(notification)
	}
}

// sendWebhook sends a notification to a webhook
func (n *Notifier) sendWebhook(webhook *WebhookConfig, notification *Notification) {
	client := &http.Client{
		Timeout: webhook.Timeout * time.Second,
	}

	// Format notification according to template
	body := n.formatNotification(webhook.Template, notification)

	// Create request
	req, err := http.NewRequest(webhook.Method, webhook.URL, strings.NewReader(body))
	if err != nil {
		log.Printf("Failed to create webhook request: %v\n", err)
		return
	}

	// Set headers
	req.Header.Set("Content-Type", "application/json")
	for key, value := range webhook.Headers {
		req.Header.Set(key, value)
	}

	// Send request with retry logic
	for i := 0; i <= webhook.RetryCount; i++ {
		resp, err := client.Do(req)
		if err != nil {
			if i == webhook.RetryCount {
				log.Printf("Webhook %s failed after %d retries: %v\n", webhook.URL, i+1, err)
			}
			time.Sleep(time.Duration(i+1) * time.Second)
			continue
		}
		resp.Body.Close()

		if resp.StatusCode >= 200 && resp.StatusCode < 300 {
			return // Success
		}

		if i == webhook.RetryCount {
			log.Printf("Webhook %s returned status %d\n", webhook.URL, resp.StatusCode)
		}
	}
}

// sendEmail sends an email notification
func (n *Notifier) sendEmail(notification *Notification) {
	if n.smtpConfig == nil {
		return
	}

	// Format email subject and body
	subject := n.formatNotification(n.smtpConfig.Subject, notification)
	body := n.formatEmailBody(notification)

	// Send email
	err := smtp.SendMail(
		fmt.Sprintf("%s:%d", n.smtpConfig.Host, n.smtpConfig.Port),
		smtp.PlainAuth("", n.smtpConfig.Username, n.smtpConfig.Password, ""),
		n.smtpConfig.From,
		[]string{"operator@project-chimera.local"}, // TODO: Make configurable
		[]byte(fmt.Sprintf("Subject: %s\r\n\r\n%s", subject, body)),
	)

	if err != nil {
		log.Printf("Failed to send email: %v\n", err)
	}
}

// formatNotification formats a notification string using a template
func (n *Notifier) formatNotification(template string, notification *Notification) string {
	result := template
	result = strings.ReplaceAll(result, "{{ID}}", notification.ID)
	result = strings.ReplaceAll(result, "{{Type}}", notification.Type)
	result = strings.ReplaceAll(result, "{{Severity}}", notification.Severity)
	result = strings.ReplaceAll(result, "{{Title}}", notification.Title)
	result = strings.ReplaceAll(result, "{{Body}}", notification.Body)
	result = strings.ReplaceAll(result, "{{Timestamp}}", notification.Timestamp.Format(time.RFC3339))

	return result
}

// formatEmailBody formats an email body
func (n *Notifier) formatEmailBody(notification *Notification) string {
	var sb strings.Builder

	sb.WriteString(fmt.Sprintf("Notification Type: %s\n", notification.Type))
	sb.WriteString(fmt.Sprintf("Severity: %s\n", notification.Severity))
	sb.WriteString(fmt.Sprintf("Title: %s\n", notification.Title))
	sb.WriteString(fmt.Sprintf("Timestamp: %s\n\n", notification.Timestamp.Format(time.RFC3339)))
	sb.WriteString(notification.Body)
	sb.WriteString("\n\n---\n")
	sb.WriteString("Sent by Claude Code Orchestrator\n")

	return sb.String()
}

// WebhookChannel is a webhook-based notification channel
type WebhookChannel struct {
	config *WebhookConfig
	client *http.Client
}

// NewWebhookChannel creates a new webhook channel
func NewWebhookChannel(config *WebhookConfig) *WebhookChannel {
	return &WebhookChannel{
		config: config,
		client: &http.Client{
			Timeout: config.Timeout * time.Second,
		},
	}
}

// Send sends a notification through the webhook
func (w *WebhookChannel) Send(notification *Notification) error {
	// Format notification
	body := w.formatBody(notification)

	// Create request
	req, err := http.NewRequest("POST", w.config.URL, strings.NewReader(body))
	if err != nil {
		return err
	}

	// Set headers
	req.Header.Set("Content-Type", "application/json")
	for key, value := range w.config.Headers {
		req.Header.Set(key, value)
	}

	// Send with retry logic
	for i := 0; i <= w.config.RetryCount; i++ {
		resp, err := w.client.Do(req)
		if err != nil {
			if i == w.config.RetryCount {
				return err
			}
			time.Sleep(time.Duration(i+1) * time.Second)
			continue
		}

		resp.Body.Close()

		if resp.StatusCode >= 200 && resp.StatusCode < 300 {
			return nil
		}

		if i == w.config.RetryCount {
			return fmt.Errorf("webhook returned status %d", resp.StatusCode)
		}
	}

	return nil
}

// formatBody formats the notification body for the webhook
func (w *WebhookChannel) formatBody(notification *Notification) string {
	data := map[string]interface{}{
		"id":        notification.ID,
		"type":      notification.Type,
		"severity":  notification.Severity,
		"title":     notification.Title,
		"body":      notification.Body,
		"metadata":  notification.Metadata,
		"timestamp": notification.Timestamp.Format(time.RFC3339),
	}

	jsonData, _ := json.Marshal(data)
	return string(jsonData)
}

// LogChannel is a logging-based notification channel
type LogChannel struct {
	logger *log.Logger
}

// NewLogChannel creates a new log channel
func NewLogChannel(logger *log.Logger) *LogChannel {
	return &LogChannel{
		logger: logger,
	}
}

// Send logs a notification
func (l *LogChannel) Send(notification *Notification) error {
	logger := l.logger
	if logger == nil {
		logger = log.Default()
	}
	logger.Printf("[NOTIFICATION] Type=%s Severity=%s Title=%s",
		notification.Type, notification.Severity, notification.Title)
	return nil
}
