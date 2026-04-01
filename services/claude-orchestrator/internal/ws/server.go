package ws

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
	"github.com/project-chimera/claude-orchestrator/internal/state"
)

// Message types for WebSocket communication
const (
	MessageTypeHealth       = "health"
	MessageTypeMode         = "mode"
	MessageTypeError        = "error"
	MessageTypeTask         = "task"
	MessageTypeNotification = "notification"
	MessageTypePing         = "ping"
)

// Message represents a WebSocket message
type Message struct {
	Type      string                 `json:"type"`
	Timestamp time.Time              `json:"timestamp"`
	Data      map[string]interface{} `json:"data"`
}

// Client represents a WebSocket client connection
type Client struct {
	ID        string
	conn      *websocket.Conn
	send      chan *Message
	hub       *Hub
	authToken string
}

// Hub maintains the set of active clients
type Hub struct {
	clients    map[string]*Client
	broadcast  chan *Message
	register   chan *Client
	unregister chan *Client
	mu         sync.RWMutex
}

// Server represents the WebSocket server
type Server struct {
	hub        *Hub
	state      *state.HybridStore
	upgrader   websocket.Upgrader
	ctx        context.Context
	cancel     context.CancelFunc
	mu         sync.RWMutex
}

// NewServer creates a new WebSocket server
func NewServer(store *state.HybridStore) *Server {
	ctx, cancel := context.WithCancel(context.Background())

	return &Server{
		hub: &Hub{
			clients:    make(map[string]*Client),
			broadcast:  make(chan *Message, 256),
			register:   make(chan *Client),
			unregister: make(chan *Client),
		},
		state: store,
		upgrader: websocket.Upgrader{
			ReadBufferSize:  1024,
			WriteBufferSize: 1024,
			CheckOrigin: func(r *http.Request) bool {
				// In production, implement proper origin checking
				return true
			},
		},
		ctx:    ctx,
		cancel: cancel,
	}
}

// Start starts the WebSocket server
func (s *Server) Start() {
	// Start hub
	go s.hub.Run()

	// Start state change broadcaster
	go s.broadcastStateChanges()
}

// Stop stops the WebSocket server
func (s *Server) Stop() {
	s.cancel()
}

// HandleWebSocket handles WebSocket connection upgrades
func (s *Server) HandleWebSocket(c *gin.Context) {
	// Get auth token from query parameter
	authToken := c.Query("auth")

	conn, err := s.upgrader.Upgrade(c.Writer, c.Request, nil)
	if err != nil {
		log.Printf("Failed to upgrade WebSocket connection: %v", err)
		return
	}

	// Create client
	client := &Client{
		ID:        fmt.Sprintf("client_%d", time.Now().UnixNano()),
		conn:      conn,
		send:      make(chan *Message, 256),
		hub:       s.hub,
		authToken: authToken,
	}

	// Register client
	s.hub.register <- client

	// Start client goroutines
	go client.readPump()
	go client.writePump()

	// Send initial state
	s.sendInitialState(client)
}

// sendInitialState sends the current state to a newly connected client
func (s *Server) sendInitialState(client *Client) {
	currentState, err := s.state.Restore()
	if err != nil {
		return
	}

	if currentState == nil {
		return
	}

	// Send current mode
	modeMsg := &Message{
		Type:      MessageTypeMode,
		Timestamp: time.Now(),
		Data: map[string]interface{}{
			"mode": currentState.Mode.String(),
		},
	}
	client.send <- modeMsg

	// Send current health
	healthMsg := &Message{
		Type:      MessageTypeHealth,
		Timestamp: time.Now(),
		Data: map[string]interface{}{
			"overall":   currentState.Health.Overall.String(),
			"services":  currentState.Health.Services,
			"slo_pass":  currentState.Health.SLOPass,
			"last_check": currentState.Health.LastCheck,
		},
	}
	client.send <- healthMsg

	// Send active errors
	if len(currentState.Errors) > 0 {
		errorMsg := &Message{
			Type:      MessageTypeError,
			Timestamp: time.Now(),
			Data: map[string]interface{}{
				"errors": currentState.Errors,
			},
		}
		client.send <- errorMsg
	}

	// Send active tasks
	if len(currentState.Tasks) > 0 {
		taskMsg := &Message{
			Type:      MessageTypeTask,
			Timestamp: time.Now(),
			Data: map[string]interface{}{
				"tasks": currentState.Tasks,
			},
		}
		client.send <- taskMsg
	}
}

// broadcastStateChanges monitors state changes and broadcasts to all clients
func (s *Server) broadcastStateChanges() {
	ticker := time.NewTicker(1 * time.Second)
	defer ticker.Stop()

	lastMode := state.ModeUnknown
	lastHealthCount := 0
	lastErrorCount := 0
	lastTaskCount := 0

	for {
		select {
		case <-s.ctx.Done():
			return
		case <-ticker.C:
			currentState, err := s.state.Restore()
			if err != nil {
				continue
			}

			if currentState == nil {
				continue
			}

			// Check for mode changes
			if currentState.Mode != lastMode {
				s.hub.broadcast <- &Message{
					Type:      MessageTypeMode,
					Timestamp: time.Now(),
					Data: map[string]interface{}{
						"mode": currentState.Mode.String(),
					},
				}
				lastMode = currentState.Mode
			}

			// Check for health changes (simple check: service count)
			currentHealthCount := len(currentState.Health.Services)
			if currentHealthCount != lastHealthCount {
				s.hub.broadcast <- &Message{
					Type:      MessageTypeHealth,
					Timestamp: time.Now(),
					Data: map[string]interface{}{
						"overall":   currentState.Health.Overall.String(),
						"services":  currentState.Health.Services,
						"slo_pass":  currentState.Health.SLOPass,
						"last_check": currentState.Health.LastCheck,
					},
				}
				lastHealthCount = currentHealthCount
			}

			// Check for new errors
			currentErrorCount := len(currentState.Errors)
			if currentErrorCount != lastErrorCount && currentErrorCount > 0 {
				s.hub.broadcast <- &Message{
					Type:      MessageTypeError,
					Timestamp: time.Now(),
					Data: map[string]interface{}{
						"errors": currentState.Errors,
					},
				}
				lastErrorCount = currentErrorCount
			}

			// Check for new tasks
			currentTaskCount := len(currentState.Tasks)
			if currentTaskCount != lastTaskCount && currentTaskCount > 0 {
				s.hub.broadcast <- &Message{
					Type:      MessageTypeTask,
					Timestamp: time.Now(),
					Data: map[string]interface{}{
						"tasks": currentState.Tasks,
					},
				}
				lastTaskCount = currentTaskCount
			}
		}
	}
}

// Broadcast broadcasts a message to all connected clients
func (s *Server) Broadcast(msgType string, data map[string]interface{}) {
	msg := &Message{
		Type:      msgType,
		Timestamp: time.Now(),
		Data:      data,
	}

	s.hub.broadcast <- msg
}

// Run runs the hub's main loop
func (h *Hub) Run() {
	for {
		select {
		case client := <-h.register:
			h.mu.Lock()
			h.clients[client.ID] = client
			h.mu.Unlock()
			log.Printf("Client registered: %s (total: %d)", client.ID, len(h.clients))

		case client := <-h.unregister:
			h.mu.Lock()
			if _, ok := h.clients[client.ID]; ok {
				delete(h.clients, client.ID)
				close(client.send)
				log.Printf("Client unregistered: %s (total: %d)", client.ID, len(h.clients))
			}
			h.mu.Unlock()

		case message := <-h.broadcast:
			h.mu.RLock()
			for _, client := range h.clients {
				select {
				case client.send <- message:
				default:
					// Client's send channel is full, close it
					close(client.send)
					delete(h.clients, client.ID)
				}
			}
			h.mu.RUnlock()
		}
	}
}

// readPump pumps messages from the WebSocket connection to the hub
func (c *Client) readPump() {
	defer func() {
		c.hub.unregister <- c
		c.conn.Close()
	}()

	c.conn.SetReadDeadline(time.Now().Add(60 * time.Second))
	c.conn.SetPongHandler(func(string) error {
		c.conn.SetReadDeadline(time.Now().Add(60 * time.Second))
		return nil
	})

	for {
		_, message, err := c.conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				log.Printf("WebSocket error: %v", err)
			}
			break
		}

		// Handle incoming messages (client commands)
		var msg Message
		if err := json.Unmarshal(message, &msg); err != nil {
			log.Printf("Failed to unmarshal message: %v", err)
			continue
		}

		// Handle different message types
		switch msg.Type {
		case MessageTypePing:
			// Respond with pong
			c.send <- &Message{
				Type:      "pong",
				Timestamp: time.Now(),
				Data:      map[string]interface{}{},
			}
		}
	}
}

// writePump pumps messages from the hub to the WebSocket connection
func (c *Client) writePump() {
	ticker := time.NewTicker(54 * time.Second)
	defer func() {
		ticker.Stop()
		c.conn.Close()
	}()

	for {
		select {
		case message, ok := <-c.send:
			c.conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if !ok {
				// Hub closed the channel
				c.conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}

			data, err := json.Marshal(message)
			if err != nil {
				log.Printf("Failed to marshal message: %v", err)
				continue
			}

			if err := c.conn.WriteMessage(websocket.TextMessage, data); err != nil {
				return
			}

		case <-ticker.C:
			c.conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if err := c.conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}

// GetClientCount returns the number of connected clients
func (s *Server) GetClientCount() int {
	s.hub.mu.RLock()
	defer s.hub.mu.RUnlock()
	return len(s.hub.clients)
}
