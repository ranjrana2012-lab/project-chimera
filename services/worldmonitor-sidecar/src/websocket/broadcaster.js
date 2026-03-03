import { WebSocket } from 'ws';
import { config } from '../../config.js';

export class WSBroadcaster {
  constructor(config) {
    this.config = config;
    this.clients = new Set();
  }

  broadcast(data) {
    const message = JSON.stringify({
      type: 'context_update',
      data: data
    });

    // Track clients to remove on error
    const clientsToRemove = new Set();

    this.clients.forEach(client => {
      if (client.readyState === WebSocket.OPEN) {
        try {
          client.send(message);
        } catch (error) {
          console.error('Error sending to WebSocket client:', error.message);
          clientsToRemove.add(client);
        }
      }
    });

    // Remove failed clients
    clientsToRemove.forEach(client => this.clients.delete(client));
  }

  addClient(ws) {
    this.clients.add(ws);
    ws.on('close', () => {
      this.clients.delete(ws);
    });
  }

  /**
   * Close all WebSocket connections
   * Used during graceful shutdown
   */
  closeAll() {
    this.clients.forEach(client => {
      if (client.readyState === WebSocket.OPEN) {
        try {
          client.close(1001, 'Server shutdown');
        } catch (error) {
          console.error('Error closing WebSocket connection:', error.message);
        }
      }
    });
    this.clients.clear();
  }
}
