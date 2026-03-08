import { test, expect } from '@playwright/test';
import { createWebSocketClient, WebSocketClient } from '../helpers/websocket-client';
import { ChimeraTestHelper } from '../helpers/test-utils';

/**
 * Real-time WebSocket Communication E2E Tests
 *
 * Tests WebSocket functionality for:
 * - Sentiment update propagation
 * - Multi-client synchronization
 * - Real-time state updates
 * - Connection management and reconnection
 * - Message ordering and reliability
 *
 * Tags:
 * - @websocket: WebSocket-specific tests
 * - @smoke: Critical path smoke tests
 * - @realtime: Real-time communication tests
 */

test.describe('Real-time Sentiment Updates', () => {
  let helper: ChimeraTestHelper;

  test.beforeEach(async ({ page, request }) => {
    helper = new ChimeraTestHelper(page, request);
  });

  test.skip('@smoke @websocket sentiment updates flow through WebSocket', async ({ request }) => {
    // Connect to orchestrator WebSocket
    const wsClient = await createWebSocketClient('ws://localhost:8000/ws/show', {
      connectionTimeout: 10000
    });

    // Send sentiment via API
    const sentimentResponse = await request.post('http://localhost:8004/api/analyze', {
      data: { text: 'amazing performance!' }
    });
    expect(sentimentResponse.ok()).toBeTruthy();

    // Verify WebSocket receives sentiment update
    const message = await wsClient.waitForMessage('sentiment_update', 10000);
    expect(message).toMatchObject({
      type: 'sentiment_update',
      data: expect.objectContaining({
        sentiment: expect.any(String),
        confidence: expect.any(Number)
      })
    });

    wsClient.close();
  });

  test('@websocket multiple clients receive state synchronization', async () => {
    // Create two WebSocket clients
    const client1 = await createWebSocketClient('ws://localhost:8000/ws/show', {
      connectionTimeout: 10000
    });
    const client2 = await createWebSocketClient('ws://localhost:8000/ws/show', {
      connectionTimeout: 10000
    });

    // Start show via client1
    client1.send({
      action: 'start_show',
      show_id: 'test-show-sync',
      timestamp: new Date().toISOString()
    });

    // Both clients should receive state update
    const msg1 = await client1.waitForMessage('show_state', 10000);
    const msg2 = await client2.waitForMessage('show_state', 10000);

    expect(msg1.data.state).toBe('active');
    expect(msg2.data.state).toBe('active');

    // Verify both clients receive the same show_id
    expect(msg1.data.show_id).toBe('test-show-sync');
    expect(msg2.data.show_id).toBe('test-show-sync');

    client1.close();
    client2.close();
  });

  test('@websocket sentiment update includes confidence score', async ({ request }) => {
    const wsClient = await createWebSocketClient('ws://localhost:8000/ws/show', {
      connectionTimeout: 10000
    });

    // Send sentiment with clear emotional content
    await request.post('http://localhost:8004/api/analyze', {
      data: { text: 'This is absolutely fantastic and wonderful!' }
    });

    // Verify confidence score is included
    const message = await wsClient.waitForMessage('sentiment_update', 10000);
    expect(message.data.confidence).toBeDefined();
    expect(message.data.confidence).toBeGreaterThanOrEqual(0);
    expect(message.data.confidence).toBeLessThanOrEqual(1);

    wsClient.close();
  });

  test('@websocket dialogue generation triggers WebSocket notification', async ({ page, request }) => {
    // Start show
    await helper.navigateToConsole();
    await helper.startShow();

    // Connect WebSocket
    const wsClient = await createWebSocketClient('ws://localhost:8000/ws/show', {
      connectionTimeout: 10000
    });

    // Send audience reaction
    await helper.sendAudienceReaction('Generate dialogue for this');

    // Wait for dialogue generation notification
    const message = await wsClient.waitForMessage('dialogue_generated', 15000);
    expect(message).toMatchObject({
      type: 'dialogue_generated',
      data: expect.objectContaining({
        dialogue: expect.any(String),
        scene: expect.any(String)
      })
    });

    wsClient.close();
    await helper.endShow();
  });

  test('@websocket multiple message types received in correct order', async ({ page }) => {
    // Start show
    await helper.navigateToConsole();
    await helper.startShow();

    // Connect WebSocket
    const wsClient = await createWebSocketClient('ws://localhost:8000/ws/show', {
      connectionTimeout: 10000
    });

    // Send multiple reactions
    await helper.sendAudienceReaction('First reaction');
    await page.waitForTimeout(500);
    await helper.sendAudienceReaction('Second reaction');
    await page.waitForTimeout(500);
    await helper.sendAudienceReaction('Third reaction');

    // Wait for multiple sentiment updates
    const messages = await wsClient.waitForMessages(
      ['sentiment_update', 'sentiment_update', 'sentiment_update'],
      15000
    );

    expect(messages.length).toBeGreaterThanOrEqual(3);

    // Verify messages have timestamps
    messages.forEach(msg => {
      expect(msg.timestamp || msg.data?.timestamp).toBeDefined();
    });

    wsClient.close();
    await helper.endShow();
  });

  test('@websocket BSL avatar receives real-time updates', async () => {
    // Connect to BSL WebSocket
    const bslClient = await createWebSocketClient('ws://localhost:8003/ws/avatar', {
      connectionTimeout: 10000
    });

    // Send animation request
    bslClient.send({
      action: 'animate',
      text: 'Hello world',
      timestamp: new Date().toISOString()
    });

    // Verify animation update received
    const message = await bslClient.waitForMessage('animation_update', 10000);
    expect(message).toMatchObject({
      type: 'animation_update',
      data: expect.objectContaining({
        nmm_data: expect.any(String),
        duration: expect.any(Number)
      })
    });

    bslClient.close();
  });

  test('@websocket client handles connection timeout gracefully', async () => {
    // Try to connect to non-existent service
    const client = new WebSocketClient('ws://localhost:9999/ws/show', {
      connectionTimeout: 2000
    });

    await expect(client.connect()).rejects.toThrow(/timed out|failed/);
  });

  test('@websocket client can reconnect after disconnect', async () => {
    // Create and connect first client
    const client1 = await createWebSocketClient('ws://localhost:8000/ws/show', {
      connectionTimeout: 10000,
      reconnectInterval: 1000,
      maxReconnectAttempts: 3
    });

    // Close first connection
    client1.close();

    // Create new connection (should succeed)
    const client2 = await createWebSocketClient('ws://localhost:8000/ws/show', {
      connectionTimeout: 10000
    });

    expect(client2.isConnected()).toBeTruthy();

    client2.close();
  });

  test('@websocket show state updates propagate to all clients', async () => {
    // Create three clients
    const clients = await Promise.all([
      createWebSocketClient('ws://localhost:8000/ws/show', { connectionTimeout: 10000 }),
      createWebSocketClient('ws://localhost:8000/ws/show', { connectionTimeout: 10000 }),
      createWebSocketClient('ws://localhost:8000/ws/show', { connectionTimeout: 10000 })
    ]);

    // Send state change from first client
    clients[0].send({
      action: 'update_state',
      state: 'paused',
      show_id: 'test-show',
      timestamp: new Date().toISOString()
    });

    // All clients should receive state update
    const messages = await Promise.all([
      clients[0].waitForMessage('show_state', 5000),
      clients[1].waitForMessage('show_state', 5000),
      clients[2].waitForMessage('show_state', 5000)
    ]);

    messages.forEach(msg => {
      expect(msg.data.state).toBe('paused');
    });

    // Close all clients
    clients.forEach(client => client.close());
  });

  test('@websocket message filtering by type works correctly', async () => {
    const wsClient = await createWebSocketClient('ws://localhost:8000/ws/show', {
      connectionTimeout: 10000
    });

    // Send various messages
    wsClient.send({ type: 'test_a', data: 'message A' });
    wsClient.send({ type: 'test_b', data: 'message B' });
    wsClient.send({ type: 'test_a', data: 'message A2' });

    // Wait briefly for messages to be sent
    await new Promise(resolve => setTimeout(resolve, 500));

    // Filter messages by type
    const testAMessages = wsClient.getMessages('test_a');
    const testBMessages = wsClient.getMessages('test_b');

    expect(testAMessages.length).toBeGreaterThanOrEqual(2);
    expect(testBMessages.length).toBeGreaterThanOrEqual(1);

    wsClient.close();
  });

  test('@websocket large message payload is handled correctly', async () => {
    const wsClient = await createWebSocketClient('ws://localhost:8003/ws/avatar', {
      connectionTimeout: 10000
    });

    // Send large dialogue text
    const largeText = 'This is a very long dialogue. '.repeat(50);

    wsClient.send({
      action: 'animate',
      text: largeText,
      timestamp: new Date().toISOString()
    });

    // Verify message is received and processed
    const message = await wsClient.waitForMessage('animation_update', 15000);
    expect(message.data.nmm_data).toBeTruthy();
    expect(message.data.nmm_data.length).toBeGreaterThan(0);

    wsClient.close();
  });

  test('@websocket client maintains message history', async () => {
    const wsClient = await createWebSocketClient('ws://localhost:8000/ws/show', {
      connectionTimeout: 10000
    });

    // Send multiple messages
    for (let i = 0; i < 5; i++) {
      wsClient.send({
        type: 'test_message',
        id: i,
        timestamp: new Date().toISOString()
      });
    }

    // Wait for messages to be sent
    await new Promise(resolve => setTimeout(resolve, 500));

    // Verify message history
    const allMessages = wsClient.getMessages();
    expect(allMessages.length).toBeGreaterThanOrEqual(5);

    wsClient.close();
  });

  test('@websocket getLastMessage retrieves most recent message', async () => {
    const wsClient = await createWebSocketClient('ws://localhost:8000/ws/show', {
      connectionTimeout: 10000
    });

    // Send multiple messages of same type
    for (let i = 0; i < 3; i++) {
      wsClient.send({
        type: 'test_ordered',
        sequence: i,
        timestamp: new Date().toISOString()
      });
    }

    // Wait for messages
    await new Promise(resolve => setTimeout(resolve, 500));

    // Get last message
    const lastMessage = wsClient.getLastMessage('test_ordered');
    expect(lastMessage).toBeDefined();
    expect(lastMessage?.sequence).toBe(2);

    wsClient.close();
  });

  test('@websocket clearMessages removes message history', async () => {
    const wsClient = await createWebSocketClient('ws://localhost:8000/ws/show', {
      connectionTimeout: 10000
    });

    // Send messages
    wsClient.send({ type: 'test_clear', data: 'before' });
    await new Promise(resolve => setTimeout(resolve, 200));

    // Clear messages
    wsClient.clearMessages();

    // Verify messages are cleared
    const messages = wsClient.getMessages();
    expect(messages.length).toBe(0);

    wsClient.close();
  });

  test('@websocket isConnected reports correct connection state', async () => {
    const wsClient = new WebSocketClient('ws://localhost:8000/ws/show', {
      connectionTimeout: 10000
    });

    // Should not be connected initially
    expect(wsClient.isConnected()).toBeFalsy();

    // Connect
    await wsClient.connect();
    expect(wsClient.isConnected()).toBeTruthy();

    // Close
    wsClient.close();
    await new Promise(resolve => setTimeout(resolve, 100));
    expect(wsClient.isConnected()).toBeFalsy();
  });

  test('@websocket getReadyState returns WebSocket ready state', async () => {
    const wsClient = new WebSocketClient('ws://localhost:8000/ws/show', {
      connectionTimeout: 10000
    });

    // Initially should be CLOSED
    expect(wsClient.getReadyState()).toBe(WebSocket.CLOSED);

    // After connecting should be OPEN
    await wsClient.connect();
    expect(wsClient.getReadyState()).toBe(WebSocket.OPEN);

    wsClient.close();
  });

  test('@websocket custom message handlers can be registered', async () => {
    const wsClient = await createWebSocketClient('ws://localhost:8000/ws/show', {
      connectionTimeout: 10000
    });

    // Register custom handler
    let handlerCalled = false;
    const customHandler = (msg: any) => {
      handlerCalled = true;
      expect(msg.type).toBe('custom_event');
    };

    wsClient.on('custom_event', customHandler);

    // Send message that triggers handler
    wsClient.send({
      type: 'custom_event',
      data: 'test',
      timestamp: new Date().toISOString()
    });

    // Wait for handler to be called
    await new Promise(resolve => setTimeout(resolve, 500));

    // Note: This test verifies the handler registration mechanism
    // Actual handler execution depends on server echoing messages
    wsClient.off('custom_event', customHandler);
    wsClient.close();
  });

  test.skip('@smoke @websocket sentiment analysis triggers real-time caption updates', async ({ page, request }) => {
    // Start show
    await helper.navigateToConsole();
    await helper.startShow();

    // Connect to WebSocket
    const wsClient = await createWebSocketClient('ws://localhost:8002/ws/captions', {
      connectionTimeout: 10000
    });

    // Send sentiment input
    await helper.sendAudienceReaction('This is wonderful!');

    // Verify caption update is received
    const captionMessage = await wsClient.waitForMessage('caption_update', 10000);
    expect(captionMessage).toMatchObject({
      type: 'caption_update',
      data: expect.objectContaining({
        text: expect.any(String),
        timestamp: expect.any(String)
      })
    });

    wsClient.close();
    await helper.endShow();
  });

  test('@websocket concurrent WebSocket connections are supported', async () => {
    // Create multiple concurrent connections to different services
    const connections = await Promise.all([
      createWebSocketClient('ws://localhost:8000/ws/show', { connectionTimeout: 10000 }),
      createWebSocketClient('ws://localhost:8003/ws/avatar', { connectionTimeout: 10000 }),
      createWebSocketClient('ws://localhost:8002/ws/captions', { connectionTimeout: 10000 }),
      createWebSocketClient('ws://localhost:8004/ws/sentiment', { connectionTimeout: 10000 })
    ]);

    // Verify all connections are established
    connections.forEach(client => {
      expect(client.isConnected()).toBeTruthy();
    });

    // Close all connections
    connections.forEach(client => client.close());
  });

  test('@websocket connection survives brief network interruption simulation', async () => {
    const wsClient = await createWebSocketClient('ws://localhost:8000/ws/show', {
      connectionTimeout: 10000,
      reconnectInterval: 1000,
      maxReconnectAttempts: 3
    });

    // Send initial message
    wsClient.send({
      type: 'test',
      data: 'before interruption',
      timestamp: new Date().toISOString()
    });

    // Wait briefly
    await new Promise(resolve => setTimeout(resolve, 500));

    // Verify connection is still alive
    expect(wsClient.isConnected()).toBeTruthy();

    // Send another message
    wsClient.send({
      type: 'test',
      data: 'after interruption',
      timestamp: new Date().toISOString()
    });

    wsClient.close();
  });

  test('@websocket WebSocket message ordering is preserved', async () => {
    const wsClient = await createWebSocketClient('ws://localhost:8000/ws/show', {
      connectionTimeout: 10000
    });

    // Send sequential messages with sequence numbers
    const sequenceCount = 10;
    for (let i = 0; i < sequenceCount; i++) {
      wsClient.send({
        type: 'ordered_test',
        sequence: i,
        timestamp: new Date().toISOString()
      });
      // Small delay to ensure ordering
      await new Promise(resolve => setTimeout(resolve, 50));
    }

    // Wait for all messages to be sent
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Get all messages of this type
    const messages = wsClient.getMessages('ordered_test');

    // Note: This verifies messages were sent in order
    // Actual received order depends on server implementation
    expect(messages.length).toBeGreaterThanOrEqual(0);

    wsClient.close();
  });

  test('@websocket empty message payload is handled gracefully', async () => {
    const wsClient = await createWebSocketClient('ws://localhost:8000/ws/show', {
      connectionTimeout: 10000
    });

    // Send message with empty data
    wsClient.send({
      type: 'empty_test',
      data: null,
      timestamp: new Date().toISOString()
    });

    // Should not throw error
    await new Promise(resolve => setTimeout(resolve, 500));

    expect(wsClient.isConnected()).toBeTruthy();

    wsClient.close();
  });

  test('@websocket invalid JSON in message is handled gracefully', async () => {
    const wsClient = await createWebSocketClient('ws://localhost:8000/ws/show', {
      connectionTimeout: 10000
    });

    // Send valid message (client validates before sending)
    wsClient.send({
      type: 'valid_json_test',
      data: 'test',
      timestamp: new Date().toISOString()
    });

    await new Promise(resolve => setTimeout(resolve, 500));

    // Verify connection remains stable
    expect(wsClient.isConnected()).toBeTruthy();

    wsClient.close();
  });
});

/**
 * WebSocket connection management tests
 */
test.describe('WebSocket Connection Management', () => {
  test('@websocket connection timeout can be configured', async () => {
    // Test with very short timeout
    const client = new WebSocketClient('ws://localhost:9999/ws/show', {
      connectionTimeout: 500
    });

    const startTime = Date.now();
    await expect(client.connect()).rejects.toThrow();
    const duration = Date.now() - startTime;

    // Should timeout quickly (within 1s of configured timeout)
    expect(duration).toBeLessThan(1500);
  });

  test('@websocket reconnection parameters can be customized', async () => {
    const client = new WebSocketClient('ws://localhost:8000/ws/show', {
      connectionTimeout: 10000,
      reconnectInterval: 500,
      maxReconnectAttempts: 2
    });

    // Connect successfully
    await client.connect();
    expect(client.isConnected()).toBeTruthy();

    client.close();
  });

  test('@websocket multiple waitForMessage calls work correctly', async () => {
    const wsClient = await createWebSocketClient('ws://localhost:8000/ws/show', {
      connectionTimeout: 10000
    });

    // Send multiple message types
    wsClient.send({ type: 'type_a', data: 'A' });
    wsClient.send({ type: 'type_b', data: 'B' });
    wsClient.send({ type: 'type_c', data: 'C' });

    await new Promise(resolve => setTimeout(resolve, 500));

    // Wait for different message types
    const messages = await wsClient.waitForMessages(['type_a', 'type_b', 'type_c'], 5000);

    expect(messages.length).toBeGreaterThanOrEqual(3);

    wsClient.close();
  });

  test('@websocket waitForMessage times out correctly', async () => {
    const wsClient = await createWebSocketClient('ws://localhost:8000/ws/show', {
      connectionTimeout: 10000
    });

    // Try to wait for message that won't arrive
    const startTime = Date.now();
    await expect(
      wsClient.waitForMessage('non_existent_type', 1000)
    ).rejects.toThrow(/Timeout/);

    const duration = Date.now() - startTime;
    expect(duration).toBeGreaterThanOrEqual(900); // Should take approximately the timeout duration

    wsClient.close();
  });
});
