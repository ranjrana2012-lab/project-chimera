package api

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/project-chimera/claude-orchestrator/internal/config"
	"github.com/project-chimera/claude-orchestrator/internal/health"
	"github.com/project-chimera/claude-orchestrator/internal/mode"
	"github.com/project-chimera/claude-orchestrator/internal/state"
	"github.com/project-chimera/claude-orchestrator/internal/ws"
)

// Server represents the API server
type Server struct {
	engine       *gin.Engine
	config       *config.Config
	store        *state.HybridStore
	modeCtrl     *mode.Controller
	healthMon    *health.Monitor
	wsServer     *ws.Server
	router       *Router
	ctx          context.Context
	cancel       context.CancelFunc
}

// NewServer creates a new API server
func NewServer(cfg *config.Config, store *state.HybridStore) (*Server, error) {
	return NewServerWithContext(context.Background(), cfg, store)
}

// NewServerWithContext creates a new API server with a given context (for testing)
func NewServerWithContext(ctx context.Context, cfg *config.Config, store *state.HybridStore) (*Server, error) {
	gin.SetMode(gin.ReleaseMode)

	engine := gin.Default()
	engine.Use(gin.Recovery())
	engine.Use(gin.Logger())
	engine.Use(corsMiddleware())

	serverCtx, cancel := context.WithCancel(ctx)

	// Create mode controller
	modeCtrl, err := mode.NewController(store, cfg.NemoClawBaseURL)
	if err != nil {
		cancel()
		return nil, fmt.Errorf("failed to create mode controller: %w", err)
	}

	// Create health monitor
	serviceConfigs := make([]health.ServiceConfig, len(cfg.Services))
	for i, svc := range cfg.Services {
		serviceConfigs[i] = health.ServiceConfig(svc)
	}
	healthMon := health.NewMonitor(store, serviceConfigs, cfg.HealthCheckInterval, cfg.HealthCheckTimeout, cfg.SLOGateURL)

	// Create WebSocket server
	wsServer := ws.NewServer(store)

	server := &Server{
		engine:    engine,
		config:    cfg,
		store:     store,
		modeCtrl:  modeCtrl,
		healthMon: healthMon,
		wsServer:  wsServer,
		ctx:       serverCtx,
		cancel:    cancel,
	}

	// Setup routes
	server.router = NewRouter(server)

	return server, nil
}

// Start starts the API server
func (s *Server) Start(addr string) error {
	// Start background services
	go s.modeCtrl.Start()
	go s.healthMon.Start()
	go s.wsServer.Start()

	// Start HTTP server
	if err := s.engine.Run(addr); err != nil {
		return err
	}

	return nil
}

// Stop stops the API server
func (s *Server) Stop() {
	s.cancel()
	s.wsServer.Stop()
	s.modeCtrl.Stop()
	s.healthMon.Stop()
	s.store.Close()
}

// corsMiddleware adds CORS headers
func corsMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(http.StatusNoContent)
			return
		}

		c.Next()
	}
}

// respondJSON responds with JSON
func (s *Server) respondJSON(c *gin.Context, code int, data interface{}) {
	c.JSON(code, gin.H{
		"success": code < 400,
		"data":    data,
		"timestamp": time.Now().Unix(),
	})
}

// respondError responds with an error
func (s *Server) respondError(c *gin.Context, code int, message string) {
	s.respondJSON(c, code, gin.H{
		"error": message,
	})
}

// Engine returns the Gin engine for testing
func (s *Server) Engine() *gin.Engine {
	return s.engine
}
