import { Page, APIRequestContext } from '@playwright/test';

/**
 * ChimeraTestHelper - Common utility methods for E2E tests
 *
 * Provides helper methods for:
 * - Service health checks
 * - WebSocket client creation
 * - UI state waiting
 * - Audience interaction simulation
 * - Prometheus metric queries
 */
export class ChimeraTestHelper {
  // Service configuration map
  private static readonly SERVICES = {
    'openclaw-orchestrator': { port: 8000, healthEndpoint: '/health/live' },
    'scenespeak-agent': { port: 8001, healthEndpoint: '/health/live' },
    'captioning-agent': { port: 8002, healthEndpoint: '/health/live' },
    'bsl-agent': { port: 8003, healthEndpoint: '/health/live' },
    'sentiment-agent': { port: 8004, healthEndpoint: '/health/live' },
    'lighting-sound-music': { port: 8005, healthEndpoint: '/health/live' },
    'safety-filter': { port: 8006, healthEndpoint: '/health/live' },
    'operator-console': { port: 8007, healthEndpoint: '/health/live' },
    'music-generation': { port: 8011, healthEndpoint: '/health/live' }
  };

  constructor(
    private page: Page,
    private request: APIRequestContext
  ) {}

  /**
   * Check if a service is healthy by querying its health endpoint
   * @param service - Service name (for logging/error messages)
   * @param port - Service port number (optional if service name is known)
   * @returns Promise<boolean> - true if service is healthy, false otherwise
   */
  async checkServiceHealth(service: string, port?: number): Promise<boolean> {
    try {
      // Look up service config if port not provided
      const serviceConfig = port
        ? { port, healthEndpoint: '/health/live' }
        : ChimeraTestHelper.SERVICES[service as keyof typeof ChimeraTestHelper.SERVICES];

      if (!serviceConfig) {
        throw new Error(`Unknown service: ${service}. Known services: ${Object.keys(ChimeraTestHelper.SERVICES).join(', ')}`);
      }

      const healthEndpoint = serviceConfig.healthEndpoint;
      const response = await this.request.get(`http://localhost:${serviceConfig.port}${healthEndpoint}`, {
        timeout: 5000
      });
      return response.ok();
    } catch (error) {
      console.error(`Health check failed for ${service}:${port || 'unknown'}`, error);
      return false;
    }
  }

  /**
   * Create a WebSocket client connection
   * @param url - WebSocket URL to connect to (or use service name)
   * @param path - Optional WebSocket path (if url is a service name)
   * @returns Promise<WebSocket> - Connected WebSocket instance
   * @throws Error if connection fails
   */
  async createWebSocketClient(url: string, path?: string): Promise<WebSocket> {
    // If url looks like a service name (no ws:// or wss://), resolve it
    const wsUrl = url.startsWith('ws://') || url.startsWith('wss://')
      ? url
      : this.getWebSocketUrl(url, path);

    return new Promise((resolve, reject) => {
      const ws = new WebSocket(wsUrl);
      const timeout = setTimeout(() => {
        reject(new Error(`WebSocket connection to ${wsUrl} timed out after 10000ms`));
      }, 10000);

      ws.onopen = () => {
        clearTimeout(timeout);
        resolve(ws);
      };

      ws.onerror = (error) => {
        clearTimeout(timeout);
        reject(new Error(`WebSocket connection to ${wsUrl} failed: ${error}`));
      };
    });
  }

  /**
   * Wait for the show to reach a specific state in the UI
   * @param state - Expected show state (e.g., 'active', 'ended', 'paused')
   * @param timeout - Maximum time to wait in milliseconds (default: 30000)
   * @throws Error if state is not reached within timeout
   */
  async waitForShowState(state: string, timeout: number = 30000): Promise<void> {
    try {
      await this.page.waitForSelector(`[data-testid="show-status"][data-state="${state}"]`, {
        timeout
      });
    } catch (error) {
      throw new Error(
        `Show state "${state}" not reached within ${timeout}ms. ` +
        `Current state: ${await this.getCurrentShowState()}`
      );
    }
  }

  /**
   * Get the current show state from the UI
   * @returns Promise<string> - Current show state
   */
  async getCurrentShowState(): Promise<string> {
    const statusElement = await this.page.locator('[data-testid="show-status"]').first();
    return await statusElement.getAttribute('data-state') || 'unknown';
  }

  /**
   * Simulate sending an audience reaction/input
   * @param reaction - The reaction text to send
   * @throws Error if input or submission fails
   */
  async sendAudienceReaction(reaction: string): Promise<void> {
    try {
      // Fill the audience input field
      await this.page.fill('[data-testid="audience-input"]', reaction);

      // Submit the sentiment
      await this.page.click('[data-testid="submit-sentiment"]');

      // Wait for submission to complete (brief delay)
      await this.page.waitForTimeout(500);
    } catch (error) {
      throw new Error(`Failed to send audience reaction "${reaction}": ${error}`);
    }
  }

  /**
   * Query a metric from Prometheus
   * @param metricName - Name of the metric to query
   * @returns Promise<number> - Metric value
   * @throws Error if query fails or returns no results
   */
  async getMetric(metricName: string): Promise<number> {
    try {
      const response = await this.request.get(
        `http://localhost:9090/api/v1/query?query=${encodeURIComponent(metricName)}`,
        { timeout: 5000 }
      );

      if (!response.ok()) {
        throw new Error(`Prometheus query failed with status ${response.status()}`);
      }

      const data = await response.json();

      if (data.status !== 'success') {
        throw new Error(`Prometheus query unsuccessful: ${data.error || 'Unknown error'}`);
      }

      if (!data.data.result || data.data.result.length === 0) {
        throw new Error(`No results found for metric: ${metricName}`);
      }

      // Return the value from the first result
      const value = data.data.result[0].value[1];
      return parseFloat(value);
    } catch (error) {
      throw new Error(`Failed to get metric "${metricName}": ${error}`);
    }
  }

  /**
   * Wait for a service to become healthy
   * @param service - Service name
   * @param port - Service port
   * @param maxAttempts - Maximum number of attempts (default: 30)
   * @param interval - Delay between attempts in ms (default: 2000)
   * @throws Error if service doesn't become healthy
   */
  async waitForService(
    service: string,
    port?: number,
    maxAttempts: number = 30,
    interval: number = 2000
  ): Promise<void> {
    for (let i = 0; i < maxAttempts; i++) {
      const isHealthy = await this.checkServiceHealth(service, port);
      if (isHealthy) {
        return;
      }

      if (i < maxAttempts - 1) {
        await this.page.waitForTimeout(interval);
      }
    }

    const serviceConfig = ChimeraTestHelper.SERVICES[service as keyof typeof ChimeraTestHelper.SERVICES];
    const actualPort = port || serviceConfig?.port || 'unknown';

    throw new Error(
      `Service ${service}:${actualPort} did not become healthy after ${maxAttempts} attempts`
    );
  }

  /**
   * Get the base URL for a service
   * @param service - Service name
   * @returns The base URL (e.g., http://localhost:8000)
   */
  getServiceUrl(service: string): string {
    const serviceConfig = ChimeraTestHelper.SERVICES[service as keyof typeof ChimeraTestHelper.SERVICES];
    if (!serviceConfig) {
      throw new Error(`Unknown service: ${service}`);
    }
    return `http://localhost:${serviceConfig.port}`;
  }

  /**
   * Get the WebSocket URL for a service
   * @param service - Service name
   * @param path - WebSocket path (default depends on service)
   * @returns The WebSocket URL (e.g., ws://localhost:8000/ws)
   */
  getWebSocketUrl(service: string, path?: string): string {
    const serviceConfig = ChimeraTestHelper.SERVICES[service as keyof typeof ChimeraTestHelper.SERVICES];
    if (!serviceConfig) {
      throw new Error(`Unknown service: ${service}`);
    }

    // Default WebSocket paths for each service
    const defaultPaths: Record<string, string> = {
      'operator-console': '/ws',
      'bsl-agent': '/ws/avatar',
      'captioning-agent': '/v1/stream',
      'openclaw-orchestrator': '/ws'
    };

    const wsPath = path || defaultPaths[service] || '/ws';
    return `ws://localhost:${serviceConfig.port}${wsPath}`;
  }

  /**
   * Navigate to the Operator Console dashboard
   * @param url - Dashboard URL (default: http://localhost:8007/static/dashboard.html)
   */
  async navigateToConsole(url: string = 'http://localhost:8007/static/dashboard.html'): Promise<void> {
    await this.page.goto(url, { waitUntil: 'networkidle' });
  }

  /**
   * Start a new show from the console
   * @throws Error if start button not found or show doesn't start
   */
  async startShow(): Promise<void> {
    try {
      await this.page.click('[data-testid="start-show-button"]');
      await this.waitForShowState('active');
    } catch (error) {
      throw new Error(`Failed to start show: ${error}`);
    }
  }

  /**
   * End the current show
   * @throws Error if end button not found or show doesn't end
   */
  async endShow(): Promise<void> {
    try {
      await this.page.click('[data-testid="end-show-button"]');
      await this.waitForShowState('ended');
    } catch (error) {
      throw new Error(`Failed to end show: ${error}`);
    }
  }
}
