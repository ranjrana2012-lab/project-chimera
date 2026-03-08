import { test, expect } from '@playwright/test';

/**
 * Operator Console API Contract Tests
 *
 * Tests the operator console service for show control.
 * Port: 8007
 *
 * Endpoints:
 * - GET /health - Service health check
 * - GET /api/show/status - Get show status
 * - POST /api/show/control - Control show
 */

test.describe('Operator Console API', () => {
  const baseURL = 'http://localhost:8007';

  test('@smoke @api health endpoint returns 200', async ({ request }) => {
    const response = await request.get(`${baseURL}/health`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toMatchObject({
      status: 'healthy',
      service: 'operator-console'
    });
    expect(body).toHaveProperty('dashboard_ready');
  });

  test('@api get show status', async ({ request }) => {
    const response = await request.get(`${baseURL}/api/show/status`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toMatchObject({
      active: expect.any(Boolean),
      state: expect.any(String),
      scene: expect.any(String)
    });
    expect(body).toHaveProperty('timestamp');
  });

  test('@api show status includes agent status', async ({ request }) => {
    const response = await request.get(`${baseURL}/api/show/status`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('agents');
    expect(Array.isArray(body.agents)).toBeTruthy();

    const expectedAgents = ['orchestrator', 'scenespeak', 'captioning', 'bsl', 'sentiment'];
    const agentNames = body.agents.map((a: any) => a.name);
    expectedAgents.forEach(agent => {
      expect(agentNames).toContain(agent);
    });
  });

  test('@api start show control', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/show/control`, {
      data: {
        action: 'start',
        show_id: 'test-show-001'
      }
    });

    // May return 409 if show already running
    expect([200, 201, 202, 409]).toContain(response.status());

    if (response.status() === 409) {
      const body = await response.json();
      expect(body.detail).toMatch(/already running|already active/i);
    } else {
      const body = await response.json();
      expect(body).toHaveProperty('show_id');
    }
  });

  test('@api stop show control', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/show/control`, {
      data: {
        action: 'stop'
      }
    });

    // May return 409 if no show running
    expect([200, 202, 409]).toContain(response.status());

    const body = await response.json();
    expect(body).toHaveProperty('action');
  });

  test('@api pause show control', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/show/control`, {
      data: {
        action: 'pause'
      }
    });

    // May return 409 if no show running or already paused
    expect([200, 202, 409]).toContain(response.status());
  });

  test('@api resume show control', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/show/control`, {
      data: {
        action: 'resume'
      }
    });

    // May return 409 if no show running or not paused
    expect([200, 202, 409]).toContain(response.status());
  });

  test('@api rejects invalid action', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/show/control`, {
      data: {
        action: 'invalid_action'
      }
    });

    expect(response.status()).toBe(422);

    const body = await response.json();
    expect(body.detail).toMatch(/action/i);
  });

  test('@api rejects missing action', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/show/control`, {
      data: {}
    });

    expect(response.status()).toBe(422);
  });

  test('@api get agent status list', async ({ request }) => {
    const response = await request.get(`${baseURL}/api/agents/status`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('agents');
    expect(Array.isArray(body.agents)).toBeTruthy();

    body.agents.forEach((agent: any) => {
      expect(agent).toMatchObject({
        name: expect.any(String),
        status: expect.any(String),
        port: expect.any(Number)
      });
    });
  });

  test('@api send audience reaction', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/audience/reaction`, {
      data: {
        reaction: 'amazing',
        sentiment: 'positive'
      }
    });

    // May return 404 if no show running
    expect([200, 202, 404]).toContain(response.status());

    if (response.status() === 404) {
      const body = await response.json();
      expect(body.detail).toMatch(/no active show/i);
    }
  });

  test('@api get show configuration', async ({ request }) => {
    const response = await request.get(`${baseURL}/api/show/config`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toMatchObject({
      max_duration: expect.any(Number),
      scenes: expect.any(Array)
    });
  });

  test('@api update show configuration', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/show/config`, {
      data: {
        max_duration: 3600,
        auto_advance: true
      }
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('updated');
  });

  test('@api health includes dashboard information', async ({ request }) => {
    const response = await request.get(`${baseURL}/health`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('dashboard_info');
    expect(body.dashboard_info).toMatchObject({
      url: expect.any(String),
      ready: expect.any(Boolean)
    });
  });

  test('@api get show metrics', async ({ request }) => {
    const response = await request.get(`${baseURL}/api/show/metrics`);

    // May return 404 if no show data yet
    expect([200, 404]).toContain(response.status());

    if (response.status() === 200) {
      const body = await response.json();
      expect(body).toMatchObject({
        audience_reactions: expect.any(Number),
        avg_sentiment: expect.any(Number),
        duration: expect.any(Number)
      });
    }
  });

  test('@api restart specific agent', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/agents/restart`, {
      data: {
        agent: 'sentiment'
      }
    });

    // May not be implemented or requires admin
    expect([200, 202, 401, 403, 404]).toContain(response.status());
  });

  test('@api WebSocket connection endpoint info', async ({ request }) => {
    const response = await request.get(`${baseURL}/api/ws/info`);

    // May not be implemented
    if (response.status() === 404) {
      return;
    }

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('ws_url');
    expect(body.ws_url).toMatch(/^ws:\/\/localhost:8007/);
  });

  test('@api get logs endpoint', async ({ request }) => {
    const response = await request.get(`${baseURL}/api/logs`, {
      params: {
        limit: '10',
        level: 'INFO'
      }
    });

    // May not be implemented or requires auth
    expect([200, 401, 403, 404]).toContain(response.status());

    if (response.status() === 200) {
      const body = await response.json();
      expect(body).toHaveProperty('logs');
      expect(Array.isArray(body.logs)).toBeTruthy();
    }
  });
});
