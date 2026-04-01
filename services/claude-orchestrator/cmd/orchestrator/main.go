package main

import (
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/project-chimera/claude-orchestrator/internal/api"
	"github.com/project-chimera/claude-orchestrator/internal/config"
	"github.com/project-chimera/claude-orchestrator/internal/state"
)

func main() {
	// Load configuration
	cfg, err := config.LoadConfig()
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	// Validate configuration
	if err := cfg.Validate(); err != nil {
		log.Fatalf("Configuration validation failed: %v", err)
	}

	// Initialize state store
	store, err := state.NewHybridStore(cfg.StateDir, cfg.RedisURL)
	if err != nil {
		log.Fatalf("Failed to initialize state store: %v", err)
	}
	defer store.Close()

	// Create API server
	server, err := api.NewServer(cfg, store)
	if err != nil {
		log.Fatalf("Failed to create API server: %v", err)
	}

	// Setup graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	// Start server in goroutine
	go func() {
		addr := fmt.Sprintf("%s:%d", cfg.Host, cfg.Port)
		log.Printf("Starting Claude Code Orchestrator on %s", addr)
		if err := server.Start(addr); err != nil {
			log.Printf("Server error: %v", err)
		}
	}()

	// Wait for shutdown signal
	sig := <-sigChan
	log.Printf("Received signal %v, shutting down...", sig)

	// Stop server
	server.Stop()

	log.Println("Claude Code Orchestrator stopped gracefully")
}
