package main

import (
	"bufio"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strings"
	"time"
)

const (
	defaultAPIURL = "http://localhost:8010"
)

// CLI represents the command-line interface
type CLI struct {
	apiURL    string
	authToken string
	client    *http.Client
}

// Response represents a standard API response
type Response struct {
	Success bool        `json:"success"`
	Data    interface{} `json:"data"`
	Error   string      `json:"error,omitempty"`
}

func main() {
	apiURL := flag.String("api", defaultAPIURL, "API base URL")
	token := flag.String("token", "", "Authentication token")
	flag.Parse()

	cli := &CLI{
		apiURL:    *apiURL,
		authToken: *token,
		client:    &http.Client{Timeout: 30 * time.Second},
	}

	if cli.authToken == "" {
		cli.authToken = os.Getenv("ORCHESTRATOR_AUTH_TOKEN")
		if cli.authToken == "" {
			fmt.Println("Warning: No auth token provided. Set ORCHESTRATOR_AUTH_TOKEN environment variable.")
		}
	}

	// Start interactive CLI
	cli.run()
}

// run starts the interactive CLI loop
func (c *CLI) run() {
	fmt.Println("Claude Orchestrator CLI")
	fmt.Println("------------------------")
	fmt.Println("Type 'help' for available commands, 'quit' to exit")
	fmt.Println()

	scanner := bufio.NewScanner(os.Stdin)

	for {
		fmt.Printf("orchestrator> ")

		if !scanner.Scan() {
			break
		}

		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}

		parts := strings.Fields(line)
		command := parts[0]
		args := parts[1:]

		switch command {
		case "help", "h", "?":
			c.showHelp()

		case "quit", "exit", "q":
			fmt.Println("Goodbye!")
			return

		case "status", "s":
			c.showStatus()

		case "mode", "m":
			if len(args) == 0 {
				c.getCurrentMode()
			} else {
				c.transitionTo(strings.ToUpper(args[0]))
			}

		case "health", "he":
			c.showHealth()

		case "errors", "e":
			c.showErrors()

		case "tasks", "t":
			if len(args) > 0 && args[0] == "create" {
				c.createTask(args[1:])
			} else {
				c.showTasks()
			}

		case "approve", "a":
			if len(args) == 0 {
				fmt.Println("Usage: approve <task-id>")
			} else {
				c.approveTask(args[0])
			}

		case "show", "sh":
			c.showShowInfo()

		case "check", "c":
			c.runHealthCheck()

		case "standby":
			c.transitionTo("STANDBY")

		case "control":
			c.transitionTo("CONTROL")

		case "pause", "p":
			c.transitionTo("PAUSED")

		case "resume", "r":
			c.transitionTo("CONTROL")

		default:
			fmt.Printf("Unknown command: %s. Type 'help' for available commands.\n", command)
		}

		fmt.Println()
	}

	if err := scanner.Err(); err != nil {
		log.Fatalf("Error reading input: %v", err)
	}
}

// showHelp displays available commands
func (c *CLI) showHelp() {
	fmt.Println("Available Commands:")
	fmt.Println("  status, s              - Show current system status")
	fmt.Println("  mode, m [MODE]         - Show or set operational mode")
	fmt.Println("  health, he             - Show service health status")
	fmt.Println("  errors, e              - Show active errors")
	fmt.Println("  tasks, t               - Show active tasks")
	fmt.Println("  tasks create [ARGS]    - Create a new task")
	fmt.Println("  approve, a <task-id>   - Approve a pending task")
	fmt.Println("  show, sh               - Show show information")
	fmt.Println("  check, c               - Run health check on all services")
	fmt.Println("  standby                - Transition to STANDBY mode")
	fmt.Println("  control                - Transition to CONTROL mode")
	fmt.Println("  pause, p               - Transition to PAUSED mode")
	fmt.Println("  resume, r              - Resume from PAUSED mode")
	fmt.Println("  help, h, ?             - Show this help message")
	fmt.Println("  quit, exit, q          - Exit the CLI")
	fmt.Println()
	fmt.Println("Operational Modes:")
	fmt.Println("  STANDBY  - Idle mode, minimal activity")
	fmt.Println("  CHECKING - Running health checks")
	fmt.Println("  CONTROL  - Active show control")
	fmt.Println("  ESCALATED - Error handling mode")
	fmt.Println("  PAUSED   - Temporarily paused")
}

// showStatus displays overall system status
func (c *CLI) showStatus() {
	resp, err := c.doRequest("GET", "/api/status", nil)
	if err != nil {
		fmt.Printf("Error getting status: %v\n", err)
		return
	}

	if resp.Success {
		data := resp.Data.(map[string]interface{})
		fmt.Printf("Mode: %v\n", data["mode"])
		fmt.Printf("Show State: %v\n", data["show_state"])
		fmt.Printf("Connected Clients: %v\n", data["connected_clients"])
	} else {
		fmt.Printf("Error: %s\n", resp.Error)
	}
}

// getCurrentMode displays the current operational mode
func (c *CLI) getCurrentMode() {
	resp, err := c.doRequest("GET", "/api/mode", nil)
	if err != nil {
		fmt.Printf("Error getting mode: %v\n", err)
		return
	}

	if resp.Success {
		data := resp.Data.(map[string]interface{})
		fmt.Printf("Current Mode: %v\n", data["mode"])
		fmt.Printf("Since: %v\n", data["since"])
	} else {
		fmt.Printf("Error: %s\n", resp.Error)
	}
}

// transitionTo transitions to a new operational mode
func (c *CLI) transitionTo(mode string) {
	body := map[string]interface{}{
		"mode":   mode,
		"reason": "Manual transition from CLI",
	}

	resp, err := c.doRequest("POST", "/api/mode/transition", body)
	if err != nil {
		fmt.Printf("Error transitioning mode: %v\n", err)
		return
	}

	if resp.Success {
		fmt.Printf("Successfully transitioned to %s mode\n", mode)
	} else {
		fmt.Printf("Error: %s\n", resp.Error)
	}
}

// showHealth displays service health status
func (c *CLI) showHealth() {
	resp, err := c.doRequest("GET", "/api/health", nil)
	if err != nil {
		fmt.Printf("Error getting health: %v\n", err)
		return
	}

	if resp.Success {
		data := resp.Data.(map[string]interface{})
		health := data["health"].(map[string]interface{})

		fmt.Printf("Overall Health: %v\n", health["overall"])
		fmt.Printf("SLO Pass: %v\n", health["slo_pass"])
		fmt.Printf("Last Check: %v\n", health["last_check"])
		fmt.Println()

		services := health["services"].(map[string]interface{})
		for name, svc := range services {
			service := svc.(map[string]interface{})
			status := "healthy"
			if !service["live"].(bool) || !service["ready"].(bool) {
				status = "unhealthy"
			}
			fmt.Printf("  %s: %s (latency: %vms)\n", name, status, service["latency_ms"])
		}
	} else {
		fmt.Printf("Error: %s\n", resp.Error)
	}
}

// showErrors displays active errors
func (c *CLI) showErrors() {
	resp, err := c.doRequest("GET", "/api/errors", nil)
	if err != nil {
		fmt.Printf("Error getting errors: %v\n", err)
		return
	}

	if resp.Success {
		data := resp.Data.(map[string]interface{})
		errors := data["errors"].([]interface{})

		if len(errors) == 0 {
			fmt.Println("No active errors")
			return
		}

		fmt.Printf("Active Errors (%d):\n", len(errors))
		for _, e := range errors {
			err := e.(map[string]interface{})
			fmt.Printf("  [%s] %s: %s\n", err["severity"], err["service"], err["message"])
		}
	} else {
		fmt.Printf("Error: %s\n", resp.Error)
	}
}

// showTasks displays active tasks
func (c *CLI) showTasks() {
	resp, err := c.doRequest("GET", "/api/tasks", nil)
	if err != nil {
		fmt.Printf("Error getting tasks: %v\n", err)
		return
	}

	if resp.Success {
		data := resp.Data.(map[string]interface{})
		tasks := data["tasks"].([]interface{})

		if len(tasks) == 0 {
			fmt.Println("No active tasks")
			return
		}

		fmt.Printf("Active Tasks (%d):\n", len(tasks))
		for _, t := range tasks {
			task := t.(map[string]interface{})
			fmt.Printf("  [%s] %s (priority: %v)\n", task["status"], task["title"], task["priority"])
		}
	} else {
		fmt.Printf("Error: %s\n", resp.Error)
	}
}

// createTask creates a new task
func (c *CLI) createTask(args []string) {
	if len(args) < 1 {
		fmt.Println("Usage: tasks create <title> [description]")
		return
	}

	title := args[0]
	description := ""
	if len(args) > 1 {
		description = strings.Join(args[1:], " ")
	}

	body := map[string]interface{}{
		"title":       title,
		"description": description,
		"priority":    2, // Normal priority
	}

	resp, err := c.doRequest("POST", "/api/tasks", body)
	if err != nil {
		fmt.Printf("Error creating task: %v\n", err)
		return
	}

	if resp.Success {
		data := resp.Data.(map[string]interface{})
		fmt.Printf("Task created: %s\n", data["id"])
	} else {
		fmt.Printf("Error: %s\n", resp.Error)
	}
}

// approveTask approves a pending task
func (c *CLI) approveTask(taskID string) {
	body := map[string]interface{}{
		"approved": true,
	}

	resp, err := c.doRequest("PUT", "/api/tasks/"+taskID, body)
	if err != nil {
		fmt.Printf("Error approving task: %v\n", err)
		return
	}

	if resp.Success {
		fmt.Printf("Task %s approved\n", taskID)
	} else {
		fmt.Printf("Error: %s\n", resp.Error)
	}
}

// showShowInfo displays show information
func (c *CLI) showShowInfo() {
	resp, err := c.doRequest("GET", "/api/show", nil)
	if err != nil {
		fmt.Printf("Error getting show info: %v\n", err)
		return
	}

	if resp.Success {
		data := resp.Data.(map[string]interface{})
		show := data["show"].(map[string]interface{})

		fmt.Printf("Show ID: %v\n", show["show_id"])
		fmt.Printf("Title: %v\n", show["title"])
		fmt.Printf("State: %v\n", show["state"])
		if start, ok := show["start_time"].(string); ok && start != "" {
			fmt.Printf("Start Time: %v\n", start)
		}
	} else {
		fmt.Printf("Error: %s\n", resp.Error)
	}
}

// runHealthCheck triggers a health check on all services
func (c *CLI) runHealthCheck() {
	resp, err := c.doRequest("POST", "/api/health/check", nil)
	if err != nil {
		fmt.Printf("Error running health check: %v\n", err)
		return
	}

	if resp.Success {
		fmt.Println("Health check initiated")
		fmt.Println("Use 'health' command to view results")
	} else {
		fmt.Printf("Error: %s\n", resp.Error)
	}
}

// doRequest makes an HTTP request to the API
func (c *CLI) doRequest(method, path string, body interface{}) (*Response, error) {
	var bodyReader io.Reader

	if body != nil {
		jsonBody, err := json.Marshal(body)
		if err != nil {
			return nil, fmt.Errorf("failed to marshal request: %w", err)
		}
		bodyReader = strings.NewReader(string(jsonBody))
	}

	url := c.apiURL + path
	req, err := http.NewRequest(method, url, bodyReader)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	if c.authToken != "" {
		req.Header.Set("Authorization", "Bearer "+c.authToken)
	}

	resp, err := c.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	var apiResp Response
	if err := json.Unmarshal(respBody, &apiResp); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &apiResp, nil
}
