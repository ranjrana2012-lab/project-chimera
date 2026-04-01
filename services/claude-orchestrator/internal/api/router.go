package api

import (
	"github.com/project-chimera/claude-orchestrator/internal/api/handlers"
)

// Router handles all API routes
type Router struct {
	server   *Server
	health   *handlers.HealthHandler
	mode     *handlers.ModeHandler
	tasks    *handlers.TaskHandler
	ralph    *handlers.RalphHandler
	policy   *handlers.PolicyHandler
	errors   *handlers.ErrorHandler
}

// NewRouter creates a new router
func NewRouter(server *Server) *Router {
	router := &Router{
		server: server,
	}

	// Create handlers with dependencies
	router.health = handlers.NewHealthHandler(server.store, server.healthMon, server.ctx)
	router.mode = handlers.NewModeHandler(server.modeCtrl, server.ctx)
	router.tasks = handlers.NewTaskHandler(server.store, server.ctx)
	router.ralph = handlers.NewRalphHandler(server.store, server.ctx)
	router.policy = handlers.NewPolicyHandler(server.modeCtrl, server.ctx)
	router.errors = handlers.NewErrorHandler(server.store, server.ctx)

	// Register routes
	router.registerRoutes()

	return router
}

// registerRoutes registers all API routes
func (r *Router) registerRoutes() {
	engine := r.server.engine

	// Health & Status
	health := engine.Group("/health")
	{
		health.GET("/live", r.health.Live)
		health.GET("/ready", r.health.Ready)
		health.GET("/status", r.health.Status)
		health.GET("/slo", r.health.SLO)
		health.POST("/check", r.health.Check)
		health.GET("/report", r.health.Report)
		health.GET("/history", r.health.History)
		health.GET("/service/:service", r.health.Service)
	}

	// Mode Control
	mode := engine.Group("/mode")
	{
		mode.GET("/current", r.mode.GetCurrent)
		mode.POST("/transition", r.mode.Transition)
		mode.GET("/history", r.mode.History)
		mode.POST("/override", r.mode.Override)
	}

	// Task Management
	tasks := engine.Group("/tasks")
	{
		tasks.GET("", r.tasks.List)
		tasks.POST("", r.tasks.Create)
		tasks.GET("/:task_id", r.tasks.Get)
		tasks.POST("/:task_id/approve", r.tasks.Approve)
		tasks.POST("/:task_id/deny", r.tasks.Deny)
		tasks.DELETE("/:task_id", r.tasks.Cancel)
	}

	// Ralph Loop Control
	ralphGroup := engine.Group("/ralph")
	{
		ralphGroup.GET("/status", r.ralph.Status)
		ralphGroup.POST("/pause", r.ralph.Pause)
		ralphGroup.POST("/resume", r.ralph.Resume)
		ralphGroup.POST("/iteration", r.ralph.Iteration)
		ralphGroup.GET("/queue", r.ralph.Queue)
	}

	// Policy Management
	policy := engine.Group("/policies")
	{
		policy.GET("", r.policy.List)
		policy.POST("/evaluate", r.policy.Evaluate)
		policy.PUT("/:policy_id", r.policy.Update)
		policy.POST("/reload", r.policy.Reload)
	}

	// Error Management
	errors := engine.Group("/errors")
	{
		errors.GET("", r.errors.List)
		errors.GET("/:error_id", r.errors.Get)
		errors.POST("/:error_id/resolve", r.errors.Resolve)
		errors.GET("/history", r.errors.History)
	}

	// WebSocket
	engine.GET("/ws/events", r.server.wsServer.HandleWebSocket)
}
