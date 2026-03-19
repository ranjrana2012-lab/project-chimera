// services/nemoclaw-orchestrator/tests/e2e/show-lifecycle.spec.ts
/**
 * End-to-end Playwright tests for show lifecycle with policy enforcement.
 *
 * These tests verify the complete show flow including:
 * - Complete show lifecycle from IDLE through all states
 * - Policy blocking of dangerous commands
 * - WebSocket real-time updates
 * - Agent coordination with policy enforcement
 *
 * Prerequisites:
 * - Nemo Claw Orchestrator service running on http://localhost:8000
 * - Redis server running on localhost:6379
 * - All agent services available (or mocked)
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.TEST_BASE_URL || 'http://localhost:8000';
const API_BASE = `${BASE_URL}/api/v1`;

interface ShowState {
  show_id: string;
  state: 'IDLE' | 'PRELUDE' | 'ACTIVE' | 'POSTLUDE' | 'CLEANUP';
  created_at: string;
  updated_at: string;
}

interface PolicyCheck {
  action: 'ALLOW' | 'DENY' | 'SANITIZE' | 'ESCALATE';
  reason: string;
  rule_name?: string;
}

interface AgentResponse {
  result?: any;
  error?: string;
}

test.describe('Show Lifecycle E2E', () => {
  let showId: string;
  let ws: WebSocket;

  test.beforeAll(async () => {
    // Setup: Verify service is available
    const response = await fetch(`${BASE_URL}/health`);
    expect(response.ok).toBeTruthy();
  });

  test.afterAll(async () => {
    // Cleanup: Close WebSocket if open
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.close();
    }
  });

  test.afterEach(async () => {
    // Cleanup: Ensure show ends after each test
    if (showId) {
      try {
        await fetch(`${API_BASE}/shows/${showId}/end`, { method: 'POST' });
      } catch (e) {
        // Ignore cleanup errors
      }
    }
  });

  test('complete show flow from IDLE to IDLE', async () => {
    /* Test complete show lifecycle: IDLE -> PRELUDE -> ACTIVE -> POSTLUDE -> CLEANUP -> IDLE */

    // Step 1: Create show (should start in IDLE)
    const createResponse = await fetch(`${API_BASE}/shows`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'E2E Test Show' })
    });

    expect(createResponse.ok).toBeTruthy();
    const showState: ShowState = await createResponse.json();
    showId = showState.show_id;

    expect(showState.state).toBe('IDLE');
    expect(showState.show_id).toBeDefined();

    // Step 2: Start show (IDLE -> PRELUDE)
    const startResponse = await fetch(`${API_BASE}/shows/${showId}/start`, {
      method: 'POST'
    });

    expect(startResponse.ok).toBeTruthy();
    const preludeState: ShowState = await startResponse.json();
    expect(preludeState.state).toBe('PRELUDE');

    // Step 3: Transition to ACTIVE (PRELUDE -> ACTIVE)
    const activeResponse = await fetch(`${API_BASE}/shows/${showId}/transition`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_state: 'ACTIVE' })
    });

    expect(activeResponse.ok).toBeTruthy();
    const activeState: ShowState = await activeResponse.json();
    expect(activeState.state).toBe('ACTIVE');

    // Step 4: Transition to POSTLUDE (ACTIVE -> POSTLUDE)
    const postludeResponse = await fetch(`${API_BASE}/shows/${showId}/transition`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_state: 'POSTLUDE' })
    });

    expect(postludeResponse.ok).toBeTruthy();
    const postludeState: ShowState = await postludeResponse.json();
    expect(postludeState.state).toBe('POSTLUDE');

    // Step 5: End show (POSTLUDE -> CLEANUP -> IDLE)
    const endResponse = await fetch(`${API_BASE}/shows/${showId}/end`, {
      method: 'POST'
    });

    expect(endResponse.ok).toBeTruthy();
    const idleState: ShowState = await endResponse.json();
    expect(idleState.state).toBe('IDLE');
  });

  test('policy blocks dangerous autonomous commands', async () => {
    /* Test that policy blocks dangerous autonomous commands during ACTIVE show */

    // Create and start show
    const createResponse = await fetch(`${API_BASE}/shows`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Policy Test Show' })
    });
    const showState: ShowState = await createResponse.json();
    showId = showState.show_id;

    // Move to ACTIVE state
    await fetch(`${API_BASE}/shows/${showId}/start`, { method: 'POST' });
    await fetch(`${API_BASE}/shows/${showId}/transition`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_state: 'ACTIVE' })
    });

    // Try to execute dangerous command
    const dangerousResponse = await fetch(`${API_BASE}/agents/autonomous/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        show_id: showId,
        command: 'rm -rf /important/data'
      })
    });

    // Should be blocked by policy
    expect(dangerousResponse.status).toBe(403);
    const errorData = await dangerousResponse.json();
    expect(errorData.error).toBe('POLICY_VIOLATION');
    expect(errorData.message).toContain('denied by policy');
  });

  test('policy allows safe sentiment analysis', async () => {
    /* Test that policy allows safe sentiment agent calls */

    // Create show
    const createResponse = await fetch(`${API_BASE}/shows`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Sentiment Test Show' })
    });
    const showState: ShowState = await createResponse.json();
    showId = showState.show_id;

    // Move to ACTIVE state
    await fetch(`${API_BASE}/shows/${showId}/start`, { method: 'POST' });
    await fetch(`${API_BASE}/shows/${showId}/transition`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_state: 'ACTIVE' })
    });

    // Call sentiment agent with safe input
    const sentimentResponse = await fetch(`${API_BASE}/agents/sentiment/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        show_id: showId,
        text: 'This is a wonderful performance!'
      })
    });

    // Should be allowed by policy
    expect(sentimentResponse.ok).toBeTruthy();
    const sentimentData: AgentResponse = await sentimentResponse.json();
    expect(sentimentData.result).toBeDefined();
  });

  test('WebSocket real-time state updates', async () => {
    /* Test WebSocket connection receives real-time state updates */

    // Create show
    const createResponse = await fetch(`${API_BASE}/shows`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'WebSocket Test Show' })
    });
    const showState: ShowState = await createResponse.json();
    showId = showState.show_id;

    // Connect to WebSocket
    const wsUrl = `${BASE_URL.replace('http', 'ws')}/ws/shows/${showId}`;
    const messages: string[] = [];

    await new Promise<void>((resolve, reject) => {
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WebSocket connected');
      };

      ws.onmessage = (event) => {
        messages.push(event.data);
        console.log('WebSocket message:', event.data);

        // After receiving a few messages, close and resolve
        if (messages.length >= 3) {
          ws.close();
          resolve();
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        reject(error);
      };

      // Trigger state changes to generate messages
      setTimeout(async () => {
        await fetch(`${API_BASE}/shows/${showId}/start`, { method: 'POST' });
      }, 100);

      setTimeout(async () => {
        await fetch(`${API_BASE}/shows/${showId}/transition`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ target_state: 'ACTIVE' })
        });
      }, 200);
    });

    // Verify we received state updates
    expect(messages.length).toBeGreaterThanOrEqual(3);

    // Parse and verify messages contain state updates
    const stateUpdates = messages.map((msg) => JSON.parse(msg));
    expect(stateUpdates.some((update) => update.state === 'PRELUDE')).toBeTruthy();
    expect(stateUpdates.some((update) => update.state === 'ACTIVE')).toBeTruthy();
  });

  test('invalid state transition is rejected', async () => {
    /* Test that invalid state transitions are rejected */

    // Create show
    const createResponse = await fetch(`${API_BASE}/shows`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Invalid Transition Test Show' })
    });
    const showState: ShowState = await createResponse.json();
    showId = showState.show_id;

    // Try to skip from IDLE to ACTIVE (invalid)
    const invalidTransition = await fetch(`${API_BASE}/shows/${showId}/transition`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_state: 'ACTIVE' })
    });

    // Should be rejected
    expect(invalidTransition.status).toBe(422);
    const errorData = await invalidTransition.json();
    expect(errorData.error).toBe('STATE_TRANSITION_ERROR');
  });

  test('policy check endpoint validates dangerous commands', async () => {
    /* Test policy check endpoint directly for dangerous commands */

    const dangerousCommands = [
      'rm -rf /',
      'format c:',
      'delete all files',
      'shutdown system'
    ];

    for (const command of dangerousCommands) {
      const checkResponse = await fetch(`${API_BASE}/policy/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent: 'autonomous',
          skill: 'execute',
          input_data: { command }
        })
      });

      expect(checkResponse.ok).toBeTruthy();
      const policyCheck: PolicyCheck = await checkResponse.json();
      expect(policyCheck.action).toBe('DENY');
      expect(policyCheck.rule_name).toBeDefined();
    }
  });

  test('policy check endpoint allows safe operations', async () => {
    /* Test policy check endpoint allows safe operations */

    const checkResponse = await fetch(`${API_BASE}/policy/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agent: 'sentiment',
        skill: 'analyze',
        input_data: { text: 'Happy message' }
      })
    });

    expect(checkResponse.ok).toBeTruthy();
    const policyCheck: PolicyCheck = await checkResponse.json();
    expect(policyCheck.action).toBe('ALLOW');
  });

  test('show state persists across requests', async () => {
    /* Test that show state persists and can be retrieved */

    // Create show
    const createResponse = await fetch(`${API_BASE}/shows`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Persistence Test Show' })
    });
    const showState: ShowState = await createResponse.json();
    showId = showState.show_id;

    // Start show
    await fetch(`${API_BASE}/shows/${showId}/start`, { method: 'POST' });

    // Retrieve state
    const getResponse = await fetch(`${API_BASE}/shows/${showId}`);
    expect(getResponse.ok).toBeTruthy();

    const retrievedState: ShowState = await getResponse.json();
    expect(retrievedState.show_id).toBe(showId);
    expect(retrievedState.state).toBe('PRELUDE');
    expect(retrievedState.created_at).toBeDefined();
    expect(retrievedState.updated_at).toBeDefined();
  });

  test('multiple shows can run independently', async () => {
    /* Test that multiple shows can be managed independently */

    // Create two shows
    const show1Response = await fetch(`${API_BASE}/shows`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Show 1' })
    });
    const show1: ShowState = await show1Response.json();

    const show2Response = await fetch(`${API_BASE}/shows`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Show 2' })
    });
    const show2: ShowState = await show2Response.json();

    // Different show IDs
    expect(show1.show_id).not.toBe(show2.show_id);

    // Start show 1
    await fetch(`${API_BASE}/shows/${show1.show_id}/start`, { method: 'POST' });

    // Start show 2
    await fetch(`${API_BASE}/shows/${show2.show_id}/start`, { method: 'POST' });

    // Both should be in PRELUDE
    const show1State = await (await fetch(`${API_BASE}/shows/${show1.show_id}`)).json();
    const show2State = await (await fetch(`${API_BASE}/shows/${show2.show_id}`)).json();

    expect(show1State.state).toBe('PRELUDE');
    expect(show2State.state).toBe('PRELUDE');

    // Transition show 1 to ACTIVE
    await fetch(`${API_BASE}/shows/${show1.show_id}/transition`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_state: 'ACTIVE' })
    });

    // Show 1 should be ACTIVE, show 2 still PRELUDE
    const show1StateAfter = await (await fetch(`${API_BASE}/shows/${show1.show_id}`)).json();
    const show2StateAfter = await (await fetch(`${API_BASE}/shows/${show2.show_id}`)).json();

    expect(show1StateAfter.state).toBe('ACTIVE');
    expect(show2StateAfter.state).toBe('PRELUDE');

    // Cleanup
    await fetch(`${API_BASE}/shows/${show1.show_id}/end`, { method: 'POST' });
    await fetch(`${API_BASE}/shows/${show2.show_id}/end`, { method: 'POST' });
  });
});

test.describe('Error Handling E2E', () => {
  test('unknown agent returns 404', async () => {
    const response = await fetch(`${API_BASE}/agents/unknown_agent/test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });

    expect(response.status).toBe(404);
  });

  test('unknown show returns 404', async () => {
    const response = await fetch(`${API_BASE}/shows/nonexistent-show-id`);

    expect(response.status).toBe(404);
  });

  test('invalid request body returns 400', async () => {
    const response = await fetch(`${API_BASE}/shows`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ invalid: 'data' })
    });

    expect(response.status).toBe(400);
  });
});
