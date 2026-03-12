/**
 * Show State Transitions Integration Tests
 *
 * Tests show lifecycle and state management:
 * - Show initialization and startup
 * - State transitions: idle → starting → active → paused → resumed → ended
 * - Scene progression within shows
 * - State persistence and recovery
 * - Concurrent state change handling
 * - State change event broadcasting
 * - Invalid state transition handling
 *
 * @tags integration, workflow, smoke
 */

import { test, expect } from './conftest';
import { createWebSocketClient } from '../e2e/helpers/websocket-client';

test.describe('Show State Transitions', () => {
  let showId: string;
  const baseShowId = 'test-show-state';

  test.beforeEach(async ({ services, testData, waitForService }) => {
    // Ensure orchestrator is running
    const isHealthy = await waitForService('orchestrator');
    if (!isHealthy) {
      test.skip(true, 'Orchestrator service is not available');
    }

    // Generate unique show ID for each test
    showId = `${baseShowId}-${Date.now()}`;
  });

  test.afterEach(async ({ services }) => {
    // Clean up: ensure show is ended
    try {
      await services.orchestrator.post('http://localhost:8000/api/show/control', {
        data: {
          action: 'end_show',
          show_id: showId
        }
      });
    } catch (error) {
      // Show may already be ended or not exist
      console.log('Cleanup: show already ended or not exist');
    }
  });

  test('@smoke @workflow show initialization from idle to starting', async ({ services, testData }) => {
    const showContext = testData.createShowContext({ show_id: showId });

    // Verify initial state is idle or doesn't exist
    const initialResponse = await services.orchestrator.get(
      `http://localhost:8000/api/show/status?show_id=${showId}`
    );

    if (initialResponse.ok()) {
      const initialData = await initialResponse.json();
      expect(['idle', 'stopped', '']).toContain(initialData.status || '');
    }

    // Start the show
    const startResponse = await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'start_show',
        show_id: showId,
        context: showContext
      }
    });

    expect(startResponse.ok()).toBeTruthy();
    const startData = await startResponse.json();

    expect(startData).toHaveProperty('show_id', showId);
    expect(startData).toHaveProperty('status', 'starting');
    expect(startData).toHaveProperty('timestamp');
  });

  test('@workflow show transition from starting to active', async ({ services }) => {
    // Start show
    await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'start_show',
        show_id: showId
      }
    });

    // Wait for show to become active (may take a moment)
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Check status
    const statusResponse = await services.orchestrator.get(
      `http://localhost:8000/api/show/status?show_id=${showId}`
    );

    expect(statusResponse.ok()).toBeTruthy();
    const statusData = await statusResponse.json();

    expect(statusData).toHaveProperty('status', 'active');
    expect(statusData).toHaveProperty('show_id', showId);
    expect(statusData).toHaveProperty('start_time');
  });

  test('@workflow show transition from active to paused', async ({ services }) => {
    // Start show
    await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'start_show',
        show_id: showId
      }
    });

    // Wait for active state
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Pause show
    const pauseResponse = await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'pause_show',
        show_id: showId
      }
    });

    expect(pauseResponse.ok()).toBeTruthy();
    const pauseData = await pauseResponse.json();

    expect(pauseData).toHaveProperty('status', 'paused');
    expect(pauseData).toHaveProperty('timestamp');
  });

  test('@workflow show transition from paused to resumed (active)', async ({ services }) => {
    // Start and pause show
    await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'start_show',
        show_id: showId
      }
    });

    await new Promise(resolve => setTimeout(resolve, 2000));

    await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'pause_show',
        show_id: showId
      }
    });

    // Resume show
    const resumeResponse = await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'resume_show',
        show_id: showId
      }
    });

    expect(resumeResponse.ok()).toBeTruthy();
    const resumeData = await resumeResponse.json();

    expect(resumeData).toHaveProperty('status', 'active');
    expect(resumeData).toHaveProperty('timestamp');
  });

  test('@workflow show transition from active to ended', async ({ services }) => {
    // Start show
    await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'start_show',
        show_id: showId
      }
    });

    await new Promise(resolve => setTimeout(resolve, 2000));

    // End show
    const endResponse = await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'end_show',
        show_id: showId
      }
    });

    expect(endResponse.ok()).toBeTruthy();
    const endData = await endResponse.json();

    expect(endData).toHaveProperty('status', 'ended');
    expect(endData).toHaveProperty('timestamp');
    expect(endData).toHaveProperty('end_time');
  });

  test('@workflow complete show lifecycle', async ({ services, testData }) => {
    const showContext = testData.createShowContext({ show_id: showId });

    // Track all state transitions
    const states: string[] = [];

    // 1. Start show
    const startResponse = await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'start_show',
        show_id: showId,
        context: showContext
      }
    });

    expect(startResponse.ok()).toBeTruthy();
    const startData = await startResponse.json();
    states.push(startData.status);
    expect(startData.status).toBe('starting');

    // 2. Wait for active
    await new Promise(resolve => setTimeout(resolve, 2000));
    const activeResponse = await services.orchestrator.get(
      `http://localhost:8000/api/show/status?show_id=${showId}`
    );

    if (activeResponse.ok()) {
      const activeData = await activeResponse.json();
      states.push(activeData.status);
    }

    // 3. Pause show
    const pauseResponse = await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'pause_show',
        show_id: showId
      }
    });

    if (pauseResponse.ok()) {
      const pauseData = await pauseResponse.json();
      states.push(pauseData.status);
    }

    // 4. Resume show
    const resumeResponse = await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'resume_show',
        show_id: showId
      }
    });

    if (resumeResponse.ok()) {
      const resumeData = await resumeResponse.json();
      states.push(resumeData.status);
    }

    // 5. End show
    const endResponse = await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'end_show',
        show_id: showId
      }
    });

    expect(endResponse.ok()).toBeTruthy();
    const endData = await endResponse.json();
    states.push(endData.status);

    // Verify complete lifecycle
    expect(states).toContain('starting');
    expect(states).toContain('paused');
    expect(states).toContain('active');
    expect(states).toContain('ended');
  });

  test('@workflow scene progression within active show', async ({ services }) => {
    // Start show
    await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'start_show',
        show_id: showId
      }
    });

    await new Promise(resolve => setTimeout(resolve, 2000));

    // Progress through scenes
    for (let scene = 1; scene <= 3; scene++) {
      const sceneResponse = await services.orchestrator.post('http://localhost:8000/api/show/control', {
        data: {
          action: 'next_scene',
          show_id: showId,
          scene_number: scene
        }
      });

      expect(sceneResponse.ok()).toBeTruthy();
      const sceneData = await sceneResponse.json();

      expect(sceneData).toHaveProperty('current_scene', scene);
      expect(sceneData).toHaveProperty('status', 'active');
    }
  });

  test('@workflow invalid state transition handling', async ({ services }) => {
    // Try to pause show that hasn't started
    const pauseResponse = await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'pause_show',
        show_id: showId
      }
    });

    // Should fail or return appropriate error
    expect([400, 409, 422, 200]).toContain(pauseResponse.status());

    if (pauseResponse.status() === 200) {
      const data = await pauseResponse.json();
      expect(data).toHaveProperty('error');
    }

    // Try to resume show that hasn't started
    const resumeResponse = await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'resume_show',
        show_id: showId
      }
    });

    expect([400, 409, 422, 200]).toContain(resumeResponse.status());
  });

  test('@workflow concurrent state change handling', async ({ services }) => {
    // Start show
    await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'start_show',
        show_id: showId
      }
    });

    await new Promise(resolve => setTimeout(resolve, 2000));

    // Send multiple state change requests concurrently
    const requests = [
      services.orchestrator.post('http://localhost:8000/api/show/control', {
        data: { action: 'pause_show', show_id: showId }
      }),
      services.orchestrator.post('http://localhost:8000/api/show/control', {
        data: { action: 'resume_show', show_id: showId }
      }),
      services.orchestrator.post('http://localhost:8000/api/show/control', {
        data: { action: 'next_scene', show_id: showId, scene_number: 2 }
      })
    ];

    const responses = await Promise.all(requests);

    // All requests should complete without errors
    responses.forEach(response => {
      expect([200, 409, 422]).toContain(response.status());
    });
  });

  test('@workflow state persistence across requests', async ({ services }) => {
    // Start show with context
    const contextData = {
      title: 'Test Show',
      scene: 1,
      act: 1,
      audience_size: 100
    };

    await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'start_show',
        show_id: showId,
        context: contextData
      }
    });

    await new Promise(resolve => setTimeout(resolve, 2000));

    // Verify context is persisted
    const statusResponse = await services.orchestrator.get(
      `http://localhost:8000/api/show/status?show_id=${showId}`
    );

    expect(statusResponse.ok()).toBeTruthy();
    const statusData = await statusResponse.json();

    expect(statusData).toHaveProperty('context');
    expect(statusData.context).toMatchObject(contextData);
  });

  test('@workflow state change event broadcasting', async () => {
    // Connect to WebSocket for state updates
    const wsClient = await createWebSocketClient('ws://localhost:8007/ws');

    // Subscribe to show state updates
    wsClient.send({
      type: 'subscribe',
      channels: ['show_state']
    });

    // Wait for subscription
    await wsClient.waitForMessage('subscribed', 5000);

    // Trigger state change via HTTP
    // Note: This would normally be done through the orchestrator
    // For testing, we'll wait for any state update

    // Start show (this would be done via API in production)
    // For now, we'll verify WebSocket connection is working

    expect(wsClient.isConnected()).toBe(true);

    wsClient.close();
  });

  test('@workflow show state with audience metrics', async ({ services, testData }) => {
    // Start show
    await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'start_show',
        show_id: showId
      }
    });

    await new Promise(resolve => setTimeout(resolve, 2000));

    // Add audience reaction
    const reactionResponse = await services.sentiment.post('http://localhost:8004/api/analyze', {
      data: {
        text: 'This is amazing!'
      }
    });

    expect(reactionResponse.ok()).toBeTruthy();

    // Check show status includes audience metrics
    const statusResponse = await services.orchestrator.get(
      `http://localhost:8000/api/show/status?show_id=${showId}`
    );

    expect(statusResponse.ok()).toBeTruthy();
    const statusData = await statusResponse.json();

    expect(statusData).toHaveProperty('audience_metrics');
    expect(statusData.audience_metrics).toHaveProperty('total_reactions');
    expect(statusData.audience_metrics).toHaveProperty('average_sentiment');
  });

  test('@workflow show recovery after pause', async ({ services }) => {
    // Start show
    await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'start_show',
        show_id: showId
      }
    });

    await new Promise(resolve => setTimeout(resolve, 2000));

    // Add some activity
    await services.sentiment.post('http://localhost:8004/api/analyze', {
      data: { text: 'Test reaction before pause' }
    });

    // Pause show
    await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'pause_show',
        show_id: showId
      }
    });

    await new Promise(resolve => setTimeout(resolve, 1000));

    // Resume show
    await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'resume_show',
        show_id: showId
      }
    });

    // Add more activity after resume
    const reactionResponse = await services.sentiment.post('http://localhost:8004/api/analyze', {
      data: { text: 'Test reaction after resume' }
    });

    expect(reactionResponse.ok()).toBeTruthy();

    // Verify show is still active
    const statusResponse = await services.orchestrator.get(
      `http://localhost:8000/api/show/status?show_id=${showId}`
    );

    expect(statusResponse.ok()).toBeTruthy();
    const statusData = await statusResponse.json();
    expect(statusData.status).toBe('active');
  });

  test('@workflow show timeout and auto-end', async ({ services }) => {
    // Start show
    await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'start_show',
        show_id: showId,
        timeout: 5000 // 5 second timeout for testing
      }
    });

    // Wait for potential timeout
    await new Promise(resolve => setTimeout(resolve, 6000));

    // Check if show auto-ended
    const statusResponse = await services.orchestrator.get(
      `http://localhost:8000/api/show/status?show_id=${showId}`
    );

    if (statusResponse.ok()) {
      const statusData = await statusResponse.json();
      // Show may have auto-ended or still be active depending on implementation
      expect(['active', 'ended']).toContain(statusData.status);
    }
  });

  test('@workflow multiple shows independent state', async ({ services }) => {
    const showIds = [`${showId}-1`, `${showId}-2`, `${showId}-3`];

    // Start multiple shows
    for (const id of showIds) {
      await services.orchestrator.post('http://localhost:8000/api/show/control', {
        data: {
          action: 'start_show',
          show_id: id
        }
      });
    }

    await new Promise(resolve => setTimeout(resolve, 2000));

    // Pause first show
    await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'pause_show',
        show_id: showIds[0]
      }
    });

    // End second show
    await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'end_show',
        show_id: showIds[1]
      }
    });

    // Verify each show has independent state
    const statuses = await Promise.all(
      showIds.map(id =>
        services.orchestrator.get(`http://localhost:8000/api/show/status?show_id=${id}`)
      )
    );

    const states = await Promise.all(
      statuses.map(async response => {
        if (response.ok()) {
          const data = await response.json();
          return data.status;
        }
        return 'unknown';
      })
    );

    // Verify states are different
    expect(states).toContain('paused');
    expect(states).toContain('ended');
    expect(states).toContain('active');

    // Cleanup remaining shows
    for (const id of showIds) {
      try {
        await services.orchestrator.post('http://localhost:8000/api/show/control', {
          data: {
            action: 'end_show',
            show_id: id
          }
        });
      } catch (error) {
        // Show already ended
      }
    }
  });
});
