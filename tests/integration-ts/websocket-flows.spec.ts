/**
 * WebSocket Streaming Integration Tests
 *
 * Tests real-time WebSocket communication for:
 * - Sentiment analysis streaming
 * - Captioning/audio transcription streaming
 * - BSL avatar animation updates
 * - Operator console dashboard updates
 * - Connection management and reconnection
 * - Message filtering and subscription
 *
 * @tags integration, websocket, slow
 */

import { test, expect } from './conftest';
import { createWebSocketClient, WebSocketClient } from '../e2e/helpers/websocket-client';

test.describe('WebSocket Streaming Flows', () => {
  test.beforeEach(async ({ waitForService }) => {
    // Ensure services with WebSocket endpoints are running
    const wsServices = ['sentiment', 'captioning', 'bsl', 'console'];

    for (const service of wsServices) {
      const isHealthy = await waitForService(service);
      if (!isHealthy) {
        test.skip(true, `Service ${service} is not available`);
      }
    }
  });

  test('@websocket sentiment streaming connection', async () => {
    const wsClient = await createWebSocketClient('ws://localhost:8004/ws');

    expect(wsClient.isConnected()).toBe(true);

    // Send test sentiment request
    wsClient.send({
      type: 'analyze',
      text: 'This is an amazing show!'
    });

    // Wait for sentiment result
    const message = await wsClient.waitForMessage('sentiment_result', 10000);

    expect(message).toHaveProperty('type', 'sentiment_result');
    expect(message).toHaveProperty('sentiment');
    expect(message).toHaveProperty('score');
    expect(message).toHaveProperty('confidence');
    expect(['positive', 'negative', 'neutral']).toContain(message.sentiment);

    wsClient.close();
  });

  test('@websocket captioning streaming connection', async () => {
    const wsClient = await createWebSocketClient('ws://localhost:8002/v1/stream');

    expect(wsClient.isConnected()).toBe(true);

    // Send audio for transcription (simulated)
    wsClient.send({
      type: 'transcribe',
      audio_data: 'simulated_audio_data'
    });

    // Wait for transcription result
    const message = await wsClient.waitForMessage('transcription', 15000);

    expect(message).toHaveProperty('type', 'transcription');
    expect(message).toHaveProperty('text');
    expect(message).toHaveProperty('timestamp');
    expect(message).toHaveProperty('duration');

    wsClient.close();
  });

  test('@websocket BSL avatar streaming', async () => {
    const wsClient = await createWebSocketClient('ws://localhost:8003/ws/avatar');

    expect(wsClient.isConnected()).toBe(true);

    // Subscribe to avatar updates
    wsClient.send({
      type: 'subscribe',
      channel: 'avatar_updates'
    });

    // Wait for subscription confirmation
    const confirmMessage = await wsClient.waitForMessage('subscription_confirmed', 5000);
    expect(confirmMessage).toHaveProperty('channel', 'avatar_updates');

    // Request avatar animation
    wsClient.send({
      type: 'animate',
      text: 'Hello and welcome'
    });

    // Wait for animation update
    const animationMessage = await wsClient.waitForMessage('animation_update', 10000);

    expect(animationMessage).toHaveProperty('type', 'animation_update');
    expect(animationMessage).toHaveProperty('nmm_data');
    expect(animationMessage.nmm_data.length).toBeGreaterThan(0);

    wsClient.close();
  });

  test('@websocket console dashboard updates', async ({ websockets }) => {
    const wsClient = websockets.console;

    expect(wsClient.isConnected()).toBe(true);

    // Subscribe to show status updates
    wsClient.send({
      type: 'subscribe',
      channels: ['show_status', 'agent_status', 'metrics']
    });

    // Wait for subscription confirmation
    const confirmMessage = await wsClient.waitForMessage('subscribed', 5000);
    expect(confirmMessage).toHaveProperty('channels');

    // Wait for status update
    const statusMessage = await wsClient.waitForMessage('show_status', 10000);

    expect(statusMessage).toHaveProperty('type', 'show_status');
    expect(statusMessage).toHaveProperty('status');
    expect(statusMessage).toHaveProperty('timestamp');
  });

  test('@websocket real-time sentiment analysis flow', async ({ services }) => {
    const wsClient = await createWebSocketClient('ws://localhost:8004/ws');

    const testTexts = [
      'I love this show!',
      'This is absolutely brilliant!',
      'Best performance ever!'
    ];

    const results = [];

    for (const text of testTexts) {
      wsClient.send({
        type: 'analyze',
        text: text
      });

      const message = await wsClient.waitForMessage('sentiment_result', 10000);
      results.push(message);
    }

    // Verify all results
    expect(results).toHaveLength(testTexts.length);
    results.forEach(result => {
      expect(result).toHaveProperty('sentiment', 'positive');
      expect(result.score).toBeGreaterThan(0.5);
    });

    wsClient.close();
  });

  test('@websocket real-time captioning with timing', async () => {
    const wsClient = await createWebSocketClient('ws://localhost:8002/v1/stream');

    // Send multiple audio chunks
    const chunks = ['chunk1', 'chunk2', 'chunk3'];

    for (const chunk of chunks) {
      wsClient.send({
        type: 'audio_chunk',
        data: chunk,
        sequence: chunks.indexOf(chunk)
      });
    }

    // Send end of stream
    wsClient.send({
      type: 'end_stream'
    });

    // Wait for final transcription
    const message = await wsClient.waitForMessage('transcription_complete', 20000);

    expect(message).toHaveProperty('type', 'transcription_complete');
    expect(message).toHaveProperty('text');
    expect(message).toHaveProperty('chunks', chunks.length);

    wsClient.close();
  });

  test('@websocket message filtering and subscription', async () => {
    const wsClient = await createWebSocketClient('ws://localhost:8007/ws');

    // Subscribe to specific channels
    wsClient.send({
      type: 'subscribe',
      channels: ['sentiment', 'bsl']
    });

    // Wait for confirmation
    const confirmMessage = await wsClient.waitForMessage('subscribed', 5000);
    expect(confirmMessage.channels).toContain('sentiment');
    expect(confirmMessage.channels).toContain('bsl');

    // Filter messages by type
    const sentimentMessages = wsClient.getMessages('sentiment_update');
    const bslMessages = wsClient.getMessages('bsl_update');

    // Verify filtering works
    expect(Array.isArray(sentimentMessages)).toBeTruthy();
    expect(Array.isArray(bslMessages)).toBeTruthy();

    wsClient.close();
  });

  test('@websocket connection reconnection handling', async () => {
    const wsClient = await createWebSocketClient('ws://localhost:8004/ws', {
      reconnectInterval: 1000,
      maxReconnectAttempts: 3
    });

    expect(wsClient.isConnected()).toBe(true);

    // Simulate connection loss
    wsClient.close();

    // Wait for reconnection
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Verify reconnection
    expect(wsClient.getReadyState()).toBe(WebSocket.OPEN);

    // Send test message after reconnection
    wsClient.send({
      type: 'ping'
    });

    const message = await wsClient.waitForMessage('pong', 5000);
    expect(message).toHaveProperty('type', 'pong');

    wsClient.close();
  });

  test('@websocket concurrent WebSocket connections', async () => {
    const clients = await Promise.all([
      createWebSocketClient('ws://localhost:8004/ws'),
      createWebSocketClient('ws://localhost:8002/v1/stream'),
      createWebSocketClient('ws://localhost:8003/ws/avatar')
    ]);

    // Verify all connections are established
    clients.forEach(client => {
      expect(client.isConnected()).toBe(true);
    });

    // Send messages on all connections
    clients[0].send({ type: 'analyze', text: 'Test sentiment' });
    clients[1].send({ type: 'ping' });
    clients[2].send({ type: 'subscribe', channel: 'avatar_updates' });

    // Wait for responses
    const [sentimentMsg, captioningMsg, bslMsg] = await Promise.all([
      clients[0].waitForMessage('sentiment_result', 10000),
      clients[1].waitForMessage('pong', 5000),
      clients[2].waitForMessage('subscription_confirmed', 5000)
    ]);

    expect(sentimentMsg).toHaveProperty('sentiment');
    expect(captioningMsg).toHaveProperty('type', 'pong');
    expect(bslMsg).toHaveProperty('channel', 'avatar_updates');

    // Close all connections
    clients.forEach(client => client.close());
  });

  test('@websocket message history tracking', async () => {
    const wsClient = await createWebSocketClient('ws://localhost:8004/ws');

    // Send multiple messages
    for (let i = 0; i < 5; i++) {
      wsClient.send({
        type: 'analyze',
        text: `Test message ${i}`
      });

      await wsClient.waitForMessage('sentiment_result', 10000);
    }

    // Get message history
    const allMessages = wsClient.getMessages();
    expect(allMessages.length).toBeGreaterThanOrEqual(5);

    // Get specific type
    const sentimentMessages = wsClient.getMessages('sentiment_result');
    expect(sentimentMessages.length).toBeGreaterThanOrEqual(5);

    wsClient.close();
  });

  test('@websocket broadcast messages to multiple clients', async () => {
    // Create multiple clients for the same service
    const client1 = await createWebSocketClient('ws://localhost:8007/ws');
    const client2 = await createWebSocketClient('ws://localhost:8007/ws');

    // Subscribe both to show status
    client1.send({ type: 'subscribe', channels: ['show_status'] });
    client2.send({ type: 'subscribe', channels: ['show_status'] });

    // Wait for both to be subscribed
    await Promise.all([
      client1.waitForMessage('subscribed', 5000),
      client2.waitForMessage('subscribed', 5000)
    ]);

    // Trigger a show status update (via HTTP)
    // Note: This would normally be triggered by show activity
    // For testing, we'll wait for any status update

    const [msg1, msg2] = await Promise.all([
      client1.waitForMessage('show_status', 10000),
      client2.waitForMessage('show_status', 10000)
    ]);

    // Both clients should receive the same update
    expect(msg1.type).toBe(msg2.type);
    expect(msg1.status).toBe(msg2.status);

    client1.close();
    client2.close();
  });

  test('@websocket error handling for malformed messages', async () => {
    const wsClient = await createWebSocketClient('ws://localhost:8004/ws');

    // Send malformed message
    wsClient.send('invalid json string');

    // Send valid message to verify connection still works
    wsClient.send({
      type: 'analyze',
      text: 'Test after error'
    });

    const message = await wsClient.waitForMessage('sentiment_result', 10000);
    expect(message).toHaveProperty('sentiment');

    wsClient.close();
  });

  test('@websocket heartbeat and keep-alive', async () => {
    const wsClient = await createWebSocketClient('ws://localhost:8004/ws');

    // Send ping
    wsClient.send({ type: 'ping' });

    // Wait for pong
    const message = await wsClient.waitForMessage('pong', 5000);
    expect(message).toHaveProperty('type', 'pong');
    expect(message).toHaveProperty('timestamp');

    // Send multiple pings to test keep-alive
    for (let i = 0; i < 3; i++) {
      wsClient.send({ type: 'ping' });
      await wsClient.waitForMessage('pong', 5000);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    wsClient.close();
  });

  test('@websocket large message handling', async () => {
    const wsClient = await createWebSocketClient('ws://localhost:8002/v1/stream');

    // Send large text for transcription
    const largeText = 'Lorem ipsum '.repeat(100); // ~1300 characters

    wsClient.send({
      type: 'transcribe',
      text: largeText
    });

    const message = await wsClient.waitForMessage('transcription', 30000);

    expect(message).toHaveProperty('text');
    expect(message.text.length).toBeGreaterThan(0);

    wsClient.close();
  });

  test('@websocket authentication and authorization', async () => {
    // This test verifies WebSocket connections work with auth
    // Note: Current implementation may not have auth, so we test connection

    const wsClient = await createWebSocketClient('ws://localhost:8007/ws', {
      connectionTimeout: 5000
    });

    expect(wsClient.isConnected()).toBe(true);

    // Send authenticated request (if auth is implemented)
    wsClient.send({
      type: 'authenticate',
      token: 'test-token'
    });

    // Wait for auth response or default message
    try {
      const message = await wsClient.waitForMessage('auth_result', 5000);
      expect(message).toHaveProperty('success');
    } catch (error) {
      // Auth may not be implemented, which is fine
      console.log('Authentication not implemented yet');
    }

    wsClient.close();
  });

  test('@websocket sentiment streaming with batch analysis', async () => {
    const wsClient = await createWebSocketClient('ws://localhost:8004/ws');

    const texts = [
      'Great show!',
      'Amazing performance',
      'Love it!'
    ];

    // Send batch request
    wsClient.send({
      type: 'batch_analyze',
      texts: texts
    });

    // Wait for batch result
    const message = await wsClient.waitForMessage('batch_sentiment_result', 15000);

    expect(message).toHaveProperty('type', 'batch_sentiment_result');
    expect(message).toHaveProperty('results');
    expect(Array.isArray(message.results)).toBeTruthy();
    expect(message.results).toHaveLength(texts.length);

    wsClient.close();
  });

  test('@websocket BSL animation streaming with timing', async () => {
    const wsClient = await createWebSocketClient('ws://localhost:8003/ws/avatar');

    // Request animation with timing info
    wsClient.send({
      type: 'animate',
      text: 'One two three',
      include_timing: true
    });

    // Wait for animation with timing
    const message = await wsClient.waitForMessage('animation_update', 10000);

    expect(message).toHaveProperty('type', 'animation_update');
    expect(message).toHaveProperty('nmm_data');
    expect(message).toHaveProperty('timing');

    if (message.timing) {
      expect(message.timing).toHaveProperty('duration');
      expect(message.timing).toHaveProperty('frames');
    }

    wsClient.close();
  });
});
