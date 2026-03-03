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

    this.clients.forEach(client => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(message);
      }
    });
  }

  addClient(ws) {
    this.clients.add(ws);
    ws.on('close', () => {
      this.clients.delete(ws);
    });
  }
}
