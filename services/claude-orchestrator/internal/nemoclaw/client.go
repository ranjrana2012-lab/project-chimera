package nemoclaw

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"net/url"
	"sync"
	"time"

	"github.com/project-chimera/claude-orchestrator/internal/state"
	"github.com/gorilla/websocket"
)

const (
	// Default timeout for HTTP requests
	defaultTimeout = 30 * time.Second
	// WebSocket ping interval
	wsPingInterval = 30 * time.Second
	// WebSocket write deadline
	wsWriteDeadline = 10 * time.Second
)

// Client represents a Nemo Claw API client
type Client struct {
	baseURL    string
	httpClient *http.Client
	wsConn     *websocket.Conn
	wsMu       sync.RWMutex
	ctx        context.Context
	cancel     context.CancelFunc
	showState  state.ShowState
	showMu     sync.RWMutex
	stateCh    chan state.ShowState
	logger     *log.Logger
}

// ShowState represents the state of a show
type ShowState struct {
	ShowID     string           `json:"show_id"`
	Title      string           `json:"title"`
	State      state.ShowState  `json:"state"`
	StartTime  *time.Time       `json:"start_time"`
	EndTime    *time.Time       `json:"end_time"`
	UpdatedAt  time.Time        `json:"updated_at"`
	Metadata   map[string]interface{} `json:"metadata"`
}

// ServiceStatus represents the status of a Nemo Claw service
type ServiceStatus struct {
	Name      string    `json:"name"`
	Status    string    `json:"status"`  // "healthy", "degraded", "unhealthy"
	Message   string    `json:"message"`
	Timestamp time.Time `json:"timestamp"`
}

// ErrorResponse represents an error response from Nemo Claw
type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message"`
	Code    int    `json:"code"`
}

// NewClient creates a new Nemo Claw client
func NewClient(baseURL string, logger *log.Logger) (*Client, error) {
	if logger == nil {
		logger = log.Default()
	}

	parsedURL, err := url.Parse(baseURL)
	if err != nil {
		return nil, fmt.Errorf("invalid base URL: %w", err)
	}

	ctx, cancel := context.WithCancel(context.Background())

	return &Client{
		baseURL: parsedURL.String(),
		httpClient: &http.Client{
			Timeout: defaultTimeout,
		},
		ctx:       ctx,
		cancel:    cancel,
		showState: state.ShowStateInactive,
		stateCh:   make(chan state.ShowState, 10),
		logger:    logger,
	}, nil
}

// Start begins the WebSocket connection for real-time updates
func (c *Client) Start() error {
	wsURL := c.wsURL()
	c.logger.Printf("Connecting to Nemo Claw WebSocket: %s", wsURL)

	wsDialer := websocket.DefaultDialer
	wsDialer.HandshakeTimeout = defaultTimeout

	conn, _, err := wsDialer.Dial(wsURL, nil)
	if err != nil {
		return fmt.Errorf("failed to connect to WebSocket: %w", err)
	}

	c.wsMu.Lock()
	c.wsConn = conn
	c.wsMu.Unlock()

	// Start ping/pong handler
	go c.pingLoop()

	// Start message handler
	go c.readMessages()

	c.logger.Printf("Connected to Nemo Claw WebSocket")

	return nil
}

// Stop closes the WebSocket connection
func (c *Client) Stop() error {
	c.cancel()

	c.wsMu.Lock()
	defer c.wsMu.Unlock()

	if c.wsConn != nil {
		// Send close message
		err := c.wsConn.WriteMessage(
			websocket.CloseMessage,
			websocket.FormatCloseMessage(websocket.CloseNormalClosure, ""),
		)
		if err != nil {
			c.logger.Printf("Error sending close message: %v", err)
		}

		// Close connection
		if err := c.wsConn.Close(); err != nil {
			return fmt.Errorf("failed to close WebSocket: %w", err)
		}

		c.wsConn = nil
	}

	close(c.stateCh)
	c.logger.Printf("Disconnected from Nemo Claw WebSocket")

	return nil
}

// GetShowState returns the current show state
func (c *Client) GetShowState() state.ShowState {
	c.showMu.RLock()
	defer c.showMu.RUnlock()
	return c.showState
}

// StateChannel returns the channel for show state updates
func (c *Client) StateChannel() <-chan state.ShowState {
	return c.stateCh
}

// GetServiceStatus queries the status of all services
func (c *Client) GetServiceStatus(ctx context.Context) ([]ServiceStatus, error) {
	url := fmt.Sprintf("%s/api/v1/services/status", c.baseURL)

	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to get service status: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	var statuses []ServiceStatus
	if err := json.NewDecoder(resp.Body).Decode(&statuses); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return statuses, nil
}

// GetShowInfo retrieves information about the current show
func (c *Client) GetShowInfo(ctx context.Context) (*ShowState, error) {
	url := fmt.Sprintf("%s/api/v1/shows/current", c.baseURL)

	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to get show info: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		// No active show
		return &ShowState{
			State:     state.ShowStateInactive,
			UpdatedAt: time.Now(),
		}, nil
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	var show ShowState
	if err := json.NewDecoder(resp.Body).Decode(&show); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &show, nil
}

// SendCommand sends a command to Nemo Claw
func (c *Client) SendCommand(ctx context.Context, command string, payload map[string]interface{}) error {
	url := fmt.Sprintf("%s/api/v1/commands", c.baseURL)

	body := map[string]interface{}{
		"command":   command,
		"payload":   payload,
		"timestamp": time.Now().UTC().Format(time.RFC3339),
	}

	jsonBody, err := json.Marshal(body)
	if err != nil {
		return fmt.Errorf("failed to marshal command: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewReader(jsonBody))
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("failed to send command: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		var errResp ErrorResponse
		if err := json.NewDecoder(resp.Body).Decode(&errResp); err != nil {
			return fmt.Errorf("command failed with status %d", resp.StatusCode)
		}
		return fmt.Errorf("command failed: %s", errResp.Message)
	}

	return nil
}

// wsURL converts HTTP base URL to WebSocket URL
func (c *Client) wsURL() string {
	u, err := url.Parse(c.baseURL)
	if err != nil {
		return c.baseURL
	}

	switch u.Scheme {
	case "https":
		u.Scheme = "wss"
	case "http":
		u.Scheme = "ws"
	}

	u.Path = "/api/v1/ws"
	return u.String()
}

// pingLoop sends periodic ping messages
func (c *Client) pingLoop() {
	ticker := time.NewTicker(wsPingInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			c.wsMu.RLock()
			conn := c.wsConn
			c.wsMu.RUnlock()

			if conn == nil {
				return
			}

			conn.SetWriteDeadline(time.Now().Add(wsWriteDeadline))
			if err := conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				c.logger.Printf("WebSocket ping failed: %v", err)
				return
			}

		case <-c.ctx.Done():
			return
		}
	}
}

// readMessages reads messages from the WebSocket connection
func (c *Client) readMessages() {
	for {
		select {
		case <-c.ctx.Done():
			return
		default:
		}

		c.wsMu.RLock()
		conn := c.wsConn
		c.wsMu.RUnlock()

		if conn == nil {
			return
		}

		messageType, data, err := conn.ReadMessage()
		if err != nil {
			c.logger.Printf("WebSocket read error: %v", err)
			return
		}

		if messageType == websocket.TextMessage {
			c.handleMessage(data)
		}
	}
}

// handleMessage processes incoming WebSocket messages
func (c *Client) handleMessage(data []byte) {
	var msg struct {
		Type string                 `json:"type"`
		Data map[string]interface{} `json:"data"`
	}

	if err := json.Unmarshal(data, &msg); err != nil {
		c.logger.Printf("Failed to unmarshal message: %v", err)
		return
	}

	switch msg.Type {
	case "show_state_update":
		c.handleShowStateUpdate(msg.Data)

	case "service_status_update":
		// Service status updates are handled by the health monitor
		c.logger.Printf("Service status update: %v", msg.Data)

	case "error":
		c.logger.Printf("Nemo Claw error: %v", msg.Data)

	default:
		c.logger.Printf("Unknown message type: %s", msg.Type)
	}
}

// handleShowStateUpdate processes show state update messages
func (c *Client) handleShowStateUpdate(data map[string]interface{}) {
	stateStr, ok := data["state"].(string)
	if !ok {
		c.logger.Printf("Invalid show state update: missing state field")
		return
	}

	newState := state.ShowStateFromString(stateStr)
	if newState == state.ShowStateUnknown {
		c.logger.Printf("Unknown show state: %s", stateStr)
		return
	}

	c.showMu.Lock()
	oldState := c.showState
	c.showState = newState
	c.showMu.Unlock()

	if oldState != newState {
		c.logger.Printf("Show state changed: %s -> %s", oldState, newState)

		select {
		case c.stateCh <- newState:
		default:
			c.logger.Printf("State channel full, dropping update")
		}
	}
}
