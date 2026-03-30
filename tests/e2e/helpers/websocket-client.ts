/**
 * WebSocket message interface
 */
export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

/**
 * WebSocket connection options
 */
export interface WebSocketOptions {
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  connectionTimeout?: number;
}

/**
 * Node.js WebSocket type for the ws package
 */
type NodeWebSocket = import('ws').WebSocket;

/**
 * ReadyState constants for WebSocket (matching browser API)
 */
const READY_STATE = {
  CONNECTING: 0,
  OPEN: 1,
  CLOSING: 2,
  CLOSED: 3
};

/**
 * WebSocketClient - Wrapper for WebSocket with enhanced features
 *
 * Provides:
 * - Promise-based connection
 * - Automatic message parsing
 * - Message filtering by type
 * - Reconnection support
 * - Message history
 * - Node.js compatibility via ws package
 */
export class WebSocketClient {
  private ws: NodeWebSocket | null = null;
  private messages: WebSocketMessage[] = [];
  private messageHandlers: Map<string, Array<(msg: WebSocketMessage) => void>> = new Map();
  private reconnectAttempts: number = 0;
  private isManualClose: boolean = false;
  private connectionPromise: Promise<void> | null = null;

  constructor(
    private url: string,
    private options: WebSocketOptions = {}
  ) {
    // Set default options
    this.options = {
      reconnectInterval: 2000,
      maxReconnectAttempts: 5,
      connectionTimeout: 10000,
      ...options
    };
  }

  /**
   * Establish WebSocket connection
   * @returns Promise that resolves when connected
   * @throws Error if connection fails or times out
   */
  connect(): Promise<void> {
    if (this.connectionPromise) {
      return this.connectionPromise;
    }

    this.isManualClose = false;
    this.messages = [];

    this.connectionPromise = new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error(`WebSocket connection to ${this.url} timed out after ${this.options.connectionTimeout}ms`));
      }, this.options.connectionTimeout);

      try {
        // Dynamic import of ws package for Node.js compatibility
        import('ws').then(({ default: WebSocket }) => {
          this.ws = new WebSocket(this.url, {
            followRedirects: true,
            rejectUnauthorized: false // For local development
          });

          // Set up event handlers using ws package API
          this.ws.on('open', () => {
            clearTimeout(timeout);
            this.reconnectAttempts = 0;
            console.log(`✅ WebSocket connected to ${this.url}`);
            resolve();
          });

          this.ws.on('error', (error: Error) => {
            clearTimeout(timeout);
            const errorMessage = `WebSocket error: ${error}`;
            console.error(errorMessage);
            this.handleReconnect().then(resolve).catch(reject);
          });

          this.ws.on('close', () => {
            console.log(`WebSocket closed`);

            if (!this.isManualClose && this.reconnectAttempts < (this.options.maxReconnectAttempts || 5)) {
              this.handleReconnect().then(resolve).catch(reject);
            }
          });

          this.ws.on('message', (data: Buffer) => {
            this.handleMessage(data);
          });

        }).catch((error) => {
          clearTimeout(timeout);
          reject(new Error(`Failed to import WebSocket: ${error}`));
        });

      } catch (error) {
        clearTimeout(timeout);
        reject(new Error(`Failed to create WebSocket: ${error}`));
      }
    });

    return this.connectionPromise;
  }

  /**
   * Handle automatic reconnection
   * @returns Promise that resolves when reconnected
   */
  private async handleReconnect(): Promise<void> {
    if (this.isManualClose) {
      throw new Error('WebSocket was manually closed');
    }

    this.reconnectAttempts++;
    const maxAttempts = this.options.maxReconnectAttempts || 5;

    if (this.reconnectAttempts >= maxAttempts) {
      throw new Error(`Connection failed - max reconnection attempts (${maxAttempts}) reached`);
    }

    const interval = this.options.reconnectInterval || 2000;
    console.log(`🔄 Reconnecting... Attempt ${this.reconnectAttempts}/${maxAttempts} in ${interval}ms`);

    await new Promise(resolve => setTimeout(resolve, interval));

    // Reset connection promise and try again
    this.connectionPromise = null;
    return this.connect();
  }

  /**
   * Handle incoming WebSocket message
   * @param data - Message data (Buffer from ws package)
   */
  private handleMessage(data: Buffer): void {
    try {
      const message: WebSocketMessage = JSON.parse(data.toString());
      this.messages.push(message);

      // Call any registered handlers for this message type
      const handlers = this.messageHandlers.get(message.type) || [];
      handlers.forEach(handler => handler(message));

    } catch (error) {
      console.error(`Failed to parse WebSocket message: ${error}`);
      // Store raw message if parsing fails
      this.messages.push({
        type: 'raw',
        data: data.toString(),
        parseError: String(error)
      });
    }
  }

  /**
   * Send data through the WebSocket
   * @param data - Data to send (will be JSON stringified)
   * @throws Error if WebSocket is not connected
   */
  send(data: any): void {
    if (!this.ws || this.ws.readyState !== READY_STATE.OPEN) {
      throw new Error('WebSocket is not connected. Call connect() first.');
    }

    try {
      const message = typeof data === 'string' ? data : JSON.stringify(data);
      this.ws.send(message);
    } catch (error) {
      throw new Error(`Failed to send WebSocket message: ${error}`);
    }
  }

  /**
   * Wait for a specific message type
   * @param type - Message type to wait for
   * @param timeout - Maximum time to wait in ms (default: 10000)
   * @returns Promise<WebSocketMessage> - The matching message
   * @throws Error if timeout is reached
   */
  waitForMessage(type: string, timeout: number = 10000): Promise<WebSocketMessage> {
    return new Promise((resolve, reject) => {
      // Check if message already exists in history
      const existingMessage = this.messages.find(m => m.type === type);
      if (existingMessage) {
        resolve(existingMessage);
        return;
      }

      const timeoutId = setTimeout(() => {
        // Clean up handler
        const handlers = this.messageHandlers.get(type) || [];
        const index = handlers.indexOf(handler);
        if (index > -1) {
          handlers.splice(index, 1);
        }
        reject(new Error(`Timeout waiting for message type: ${type}`));
      }, timeout);

      const handler = (msg: WebSocketMessage) => {
        clearTimeout(timeoutId);
        resolve(msg);
      };

      // Register handler for this message type
      if (!this.messageHandlers.has(type)) {
        this.messageHandlers.set(type, []);
      }
      this.messageHandlers.get(type)!.push(handler);
    });
  }

  /**
   * Wait for multiple message types
   * @param types - Array of message types to wait for
   * @param timeout - Maximum time to wait for all messages in ms (default: 10000)
   * @returns Promise<WebSocketMessage[]> - Array of matching messages in order
   * @throws Error if timeout is reached
   */
  async waitForMessages(types: string[], timeout: number = 10000): Promise<WebSocketMessage[]> {
    const startTime = Date.now();
    const messages: WebSocketMessage[] = [];

    for (const type of types) {
      const remainingTime = timeout - (Date.now() - startTime);
      if (remainingTime <= 0) {
        throw new Error(`Timeout waiting for messages: ${types.join(', ')}`);
      }

      const message = await this.waitForMessage(type, remainingTime);
      messages.push(message);
    }

    return messages;
  }

  /**
   * Get all received messages
   * @param filterByType - Optional message type filter
   * @returns Array of received messages
   */
  getMessages(filterByType?: string): WebSocketMessage[] {
    if (filterByType) {
      return this.messages.filter(m => m.type === filterByType);
    }
    return [...this.messages];
  }

  /**
   * Get the last message of a specific type
   * @param type - Message type
   * @returns The last message of that type, or undefined
   */
  getLastMessage(type: string): WebSocketMessage | undefined {
    const filtered = this.messages.filter(m => m.type === type);
    return filtered.length > 0 ? filtered[filtered.length - 1] : undefined;
  }

  /**
   * Clear message history
   */
  clearMessages(): void {
    this.messages = [];
  }

  /**
   * Check if WebSocket is connected
   * @returns true if connected, false otherwise
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === READY_STATE.OPEN;
  }

  /**
   * Wait for WebSocket to be ready (OPEN state)
   * @param timeout - Maximum time to wait in ms (default: 5000)
   * @throws Error if timeout is reached
   */
  async waitForReady(timeout: number = 5000): Promise<void> {
    const startTime = Date.now();
    while (Date.now() - startTime < timeout) {
      if (this.ws && this.ws.readyState === READY_STATE.OPEN) {
        return;
      }
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    throw new Error('WebSocket not ready within timeout');
  }

  /**
   * Get WebSocket ready state
   * @returns The ready state constant (0=CONNECTING, 1=OPEN, 2=CLOSING, 3=CLOSED)
   */
  getReadyState(): number {
    return this.ws?.readyState ?? READY_STATE.CLOSED;
  }

  /**
   * Close the WebSocket connection
   * @param code - Close code (default: 1000)
   * @param reason - Close reason
   */
  close(code: number = 1000, reason?: string): void {
    this.isManualClose = true;

    if (this.ws && this.ws.readyState !== READY_STATE.CLOSED) {
      this.ws.close(code, reason);
    }

    // Clear all handlers
    this.messageHandlers.clear();
  }

  /**
   * Register a handler for a specific message type
   * @param type - Message type
   * @param handler - Handler function
   */
  on(type: string, handler: (msg: WebSocketMessage) => void): void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, []);
    }
    this.messageHandlers.get(type)!.push(handler);
  }

  /**
   * Remove a handler for a specific message type
   * @param type - Message type
   * @param handler - Handler function to remove
   */
  off(type: string, handler: (msg: WebSocketMessage) => void): void {
    const handlers = this.messageHandlers.get(type);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }
}

/**
 * Factory function to create and connect a WebSocket client
 * @param url - WebSocket URL
 * @param options - Connection options
 * @returns Promise<WebSocketClient> - Connected client
 */
export async function createWebSocketClient(
  url: string,
  options?: WebSocketOptions
): Promise<WebSocketClient> {
  const client = new WebSocketClient(url, options);
  await client.connect();
  return client;
}
