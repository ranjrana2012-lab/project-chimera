import { test, expect } from '@playwright/test';

/**
 * OpenClaw Orchestrator API Contract Tests
 *
 * Tests the central orchestrator service that coordinates all agents.
 * Port: 8000
 *
 * Endpoints:
 * - GET /health - Service health check
 * - GET /api/skills - List available skills
 * - GET /api/show/status - Get current show status
 */

test.describe('OpenClaw Orchestrator API', () => {
  const baseURL = 'http://localhost:8000';

  test('@smoke @api health endpoint returns 200', async ({ request }) => {
    const response = await request.get(`${baseURL}/health`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toMatchObject({
      status: 'healthy',
      service: 'openclaw-orchestrator'
    });
    expect(body).toHaveProperty('timestamp');
  });

  test('@api health endpoint includes service dependencies', async ({ request }) => {
    const response = await request.get(`${baseURL}/health`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('dependencies');
    expect(Array.isArray(body.dependencies)).toBeTruthy();
  });

  test('@api skills endpoint returns available skills', async ({ request }) => {
    const response = await request.get(`${baseURL}/api/skills`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('skills');
    expect(Array.isArray(body.skills)).toBeTruthy();

    // Verify expected skills exist
    const skillNames = body.skills.map((s: any) => s.name);
    expect(skillNames).toContain('generate_dialogue');
    expect(skillNames).toContain('analyze_sentiment');
  });

  test('@api skills include metadata', async ({ request }) => {
    const response = await request.get(`${baseURL}/api/skills`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    const skill = body.skills.find((s: any) => s.name === 'generate_dialogue');

    expect(skill).toBeDefined();
    expect(skill).toHaveProperty('description');
    expect(skill).toHaveProperty('endpoint');
    expect(skill).toHaveProperty('method');
  });

  test('@api show status endpoint returns current state', async ({ request }) => {
    const response = await request.get(`${baseURL}/api/show/status`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toMatchObject({
      active: expect.any(Boolean),
      scene: expect.any(String)
    });
    expect(body).toHaveProperty('timestamp');
  });

  test('@api show status includes audience metrics', async ({ request }) => {
    const response = await request.get(`${baseURL}/api/show/status`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('audience_metrics');
    expect(body.audience_metrics).toMatchObject({
      total_reactions: expect.any(Number),
      average_sentiment: expect.any(Number)
    });
  });

  test('@api rejects invalid show control requests', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/show/control`, {
      data: { action: 'invalid_action' }
    });

    expect(response.status()).toBe(422);

    const body = await response.json();
    expect(body).toHaveProperty('detail');
  });

  test('@api handles timeout for long-running operations', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/show/control`, {
      data: { action: 'start_show' },
      timeout: 10000
    });

    // Should either succeed or fail gracefully
    expect([200, 202, 409]).toContain(response.status());
  });

  test('@api show control start action', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/show/control`, {
      data: { action: 'start_show' }
    });

    if (response.status() === 409) {
      // Show already active - this is acceptable
      const body = await response.json();
      expect(body.detail).toMatch(/already active|already running/i);
    } else {
      expect([200, 201, 202]).toContain(response.status());

      const body = await response.json();
      expect(body).toHaveProperty('show_id');
      expect(body).toMatchObject({
        status: 'starting'
      });
    }
  });

  test('@api CORS headers are present', async ({ request }) => {
    const response = await request.get(`${baseURL}/api/skills`);

    expect(response.status()).toBe(200);
    expect(response.headers()['access-control-allow-origin']).toBeDefined();
  });
});
