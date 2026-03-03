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

server.on('upgrade', (request, socket, head) => {
  wss.handleUpgrade(request, socket, head, (ws) => {
    wss.emit('connection', ws, request);
  });
});

// Start context update loop
setInterval(async () => {
  const context = await contextCalculator.getGlobalContext();
  await wsBroadcaster.broadcast(context);
}, config.contextUpdateInterval * 1000);

export { app, wss };
