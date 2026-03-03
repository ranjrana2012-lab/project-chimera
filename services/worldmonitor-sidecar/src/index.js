import express from 'express';
import { WebSocketServer } from 'ws';
import { config } from './config.js';
import { NewsAggregator } from './news/aggregator.js';
import { ContextCalculator } from './context/calculator.js';
import { WSBroadcaster } from './websocket/broadcaster.js';

const app = express();
app.use(express.json());

// Initialize components
const newsAggregator = new NewsAggregator(config);
const contextCalculator = new ContextCalculator(config);
const wsBroadcaster = new WSBroadcaster(config);

// Health endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'worldmonitor-sidecar' });
});

// Context endpoints
app.get('/api/v1/context/global', async (req, res) => {
  try {
    const context = await contextCalculator.getGlobalContext();
    res.json(context);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/v1/context/country/:code', async (req, res) => {
  try {
    const context = await contextCalculator.getCountryContext(req.params.code);
    res.json(context);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// News sentiment endpoint
app.get('/api/v1/news', async (req, res) => {
  try {
    const { sources, categories, hours = 24 } = req.query;
    const news = await newsAggregator.getNews({ sources, categories, hours });
    res.json(news);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Start server
const server = app.listen(config.port, config.host, () => {
  console.log(`WorldMonitor sidecar listening on ${config.host}:${config.port}`);
});

// WebSocket server for client connections
const wss = new WebSocketServer({ noServer: true });

// Handle WebSocket connections and wire up broadcaster
wss.on('connection', (ws, request) => {
  console.log('New WebSocket connection established');
  wsBroadcaster.addClient(ws);
});

server.on('upgrade', (request, socket, head) => {
  wss.handleUpgrade(request, socket, head, (ws) => {
    wss.emit('connection', ws, request);
  });
});

// Start context update loop
setInterval(async () => {
  try {
    const context = await contextCalculator.getGlobalContext();
    await wsBroadcaster.broadcast(context);
  } catch (error) {
    console.error('Error in context update loop:', error.message);
  }
}, config.contextUpdateInterval * 1000);

// Graceful shutdown handlers
const shutdown = async (signal) => {
  console.log(`Received ${signal}, starting graceful shutdown...`);

  // Stop accepting new connections
  server.close(() => {
    console.log('HTTP server closed');
  });

  // Close all WebSocket connections via broadcaster
  wsBroadcaster.closeAll();

  // Cleanup Redis connection
  try {
    await contextCalculator.cleanup();
  } catch (error) {
    console.error('Error during cleanup:', error.message);
  }

  console.log('Shutdown complete');
  process.exit(0);
};

process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));

export { app, wss };
