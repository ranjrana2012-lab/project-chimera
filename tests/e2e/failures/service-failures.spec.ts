import { test, expect } from '@playwright/test';
import { execSync } from 'child_process';
import { ChimeraTestHelper } from '../helpers/test-utils';
import { ServiceHealthHelper } from '../helpers/service-health';

/**
 * Service Failure Resilience Tests
 *
 * These tests verify that the Project Chimera platform degrades gracefully
 * when components fail and can recover properly.
 *
 * Tags: @failure
 */

test.describe('Service Failure Resilience', () => {
  let helper: ChimeraTestHelper;

  test.beforeEach(async ({ page, request }) => {
    helper = new ChimeraTestHelper(page, request);
  });

  test.skip('@failure @smoke show continues when sentiment agent is unavailable', async ({ page }) => {
    // Navigate to console and start show
    await helper.navigateToConsole();
    await helper.startShow();

    // Verify show is active
    await expect(page.locator('[data-testid="show-status"][data-state="active"]')).toBeVisible();

    // Stop sentiment agent service
    test.step('Stop sentiment agent service', () => {
      execSync('docker-compose stop sentiment-agent', {
        cwd: process.cwd(),
        stdio: 'pipe'
      });
    });

    // Verify fallback behavior - show should continue with degraded sentiment
    await expect(async () => {
      const sentimentStatus = page.locator('[data-testid="sentiment-status"]');
      const status = await sentimentStatus.getAttribute('data-status');
      expect(status).toMatch(/fallback|degraded|unavailable/);
    }).toPass({ timeout: 10000 });

    // Verify show is still active despite sentiment failure
    await expect(page.locator('[data-testid="show-status"][data-state="active"]')).toBeVisible();

    // Verify other agents still working (dialogue generation)
    await helper.sendAudienceReaction('Test reaction during sentiment outage');

    // Restart sentiment agent service for cleanup
    test.step('Restart sentiment agent service', () => {
      execSync('docker-compose start sentiment-agent', {
        cwd: process.cwd(),
        stdio: 'pipe'
      });
    });

    // Wait for sentiment agent to recover
    await helper.waitForService('sentiment', 8004, 30, 2000);

    // Verify recovery - sentiment status should return to active
    await expect(async () => {
      const sentimentStatus = page.locator('[data-testid="sentiment-status"]');
      const status = await sentimentStatus.getAttribute('data-status');
      expect(status).toBe('active');
    }).toPass({ timeout: 15000 });

    // End show
    await helper.endShow();
  });

  test.skip('@failure graceful degradation when GPU is unavailable - show control UI not implemented', async ({ page, request }) => {
    // Navigate to console
    await helper.navigateToConsole();

    // Check if BSL agent is healthy (BSL uses GPU for avatar rendering)
    const bslHealthy = await helper.checkServiceHealth('bsl', 8003);
    expect(bslHealthy).toBeTruthy();

    // Start show
    await helper.startShow();

    // Stop BSL agent (simulates GPU failure)
    test.step('Stop BSL agent to simulate GPU failure', () => {
      execSync('docker-compose stop bsl-agent', {
        cwd: process.cwd(),
        stdio: 'pipe'
      });
    });

    // Verify fallback - avatar should show placeholder or error state
    await expect(async () => {
      const avatarStatus = page.locator('[data-testid="bsl-avatar-status"]');
      const status = await avatarStatus.getAttribute('data-status');
      expect(status).toMatch(/unavailable|fallback|placeholder|degraded/);
    }).toPass({ timeout: 10000 });

    // Verify show continues without BSL avatar
    await expect(page.locator('[data-testid="show-status"][data-state="active"]')).toBeVisible();

    // Verify captioning still works (alternative accessibility)
    const captioningStatus = page.locator('[data-testid="captioning-status"]');
    await expect(captioningStatus).toHaveAttribute('data-status', 'active');

    // Restart BSL agent for cleanup
    test.step('Restart BSL agent', () => {
      execSync('docker-compose start bsl-agent', {
        cwd: process.cwd(),
        stdio: 'pipe'
      });
    });

    // Wait for BSL agent to recover
    await helper.waitForService('bsl', 8003, 30, 2000);

    // Verify avatar recovery
    await expect(async () => {
      const avatarStatus = page.locator('[data-testid="bsl-avatar-status"]');
      const status = await avatarStatus.getAttribute('data-status');
      expect(status).toBe('active');
    }).toPass({ timeout: 15000 });

    // End show
    await helper.endShow();
  });

  test.skip('@failure service restart and recovery - show control UI not implemented', async ({ page }) => {
    // Navigate to console
    await helper.navigateToConsole();

    // Get initial SceneSpeak agent health
    const initialHealth = await helper.checkServiceHealth('scenespeak', 8001);
    expect(initialHealth).toBeTruthy();

    // Start show
    await helper.startShow();

    // Verify dialogue generation working
    await helper.sendAudienceReaction('Initial reaction before restart');

    // Restart SceneSpeak agent
    test.step('Restart SceneSpeak agent', () => {
      execSync('docker-compose restart scenespeak-agent', {
        cwd: process.cwd(),
        stdio: 'pipe'
      });
    });

    // Verify show continues during restart (may have brief interruption)
    await page.waitForTimeout(5000);

    // Wait for SceneSpeak to recover
    await helper.waitForService('scenespeak', 8001, 45, 2000);

    // Verify dialogue generation working after restart
    await helper.sendAudienceReaction('Reaction after restart');

    // Verify dialogue generated
    await expect(page.locator('[data-testid="generated-dialogue"]')).toBeVisible({
      timeout: 15000
    });

    // End show
    await helper.endShow();
  });

  test.skip('@failure invalid input handling - extremely long input - show control UI not implemented', async ({ page }) => {
    // Navigate to console
    await helper.navigateToConsole();

    // Start show
    await helper.startShow();

    // Attempt to send extremely long input (100,000 characters)
    const longInput = 'a'.repeat(100000);

    await page.fill('[data-testid="audience-input"]', longInput);
    await page.click('[data-testid="submit-sentiment"]');

    // Should show validation error or truncate input
    const validationError = page.locator('[data-testid="validation-error"]');
    const errorMessage = page.locator('[data-testid="error-message"]');

    // Either validation error appears or input is truncated
    const hasValidationError = await validationError.isVisible().catch(() => false);
    const hasErrorMessage = await errorMessage.isVisible().catch(() => false);

    expect(hasValidationError || hasErrorMessage).toBeTruthy();

    // Verify show still running despite invalid input
    await expect(page.locator('[data-testid="show-status"][data-state="active"]')).toBeVisible();

    // End show
    await helper.endShow();
  });

  test.skip('@failure invalid input handling - special characters - show control UI not implemented', async ({ page }) => {
    // Navigate to console
    await helper.navigateToConsole();

    // Start show
    await helper.startShow();

    // Send input with potentially dangerous special characters
    const dangerousInputs = [
      '<script>alert("xss")</script>',
      '../../etc/passwd',
      '"; DROP TABLE shows; --',
      '\x00\x01\x02\x03',
      '{{7*7}}',
      '${7*7}'
    ];

    for (const input of dangerousInputs) {
      await page.fill('[data-testid="audience-input"]', input);
      await page.click('[data-testid="submit-sentiment"]');

      // Brief wait for processing
      await page.waitForTimeout(500);

      // Verify no crash - show still active
      await expect(page.locator('[data-testid="show-status"][data-state="active"]')).toBeVisible();
    }

    // End show
    await helper.endShow();
  });

  test('@failure malformed API requests', async ({ request }) => {
    // Test malformed JSON
    const response1 = await request.post('http://localhost:8004/api/analyze', {
      headers: { 'Content-Type': 'application/json' },
      data: '{invalid json}'
    });

    expect(response1.status()).toBeGreaterThanOrEqual(400);
    expect(response1.status()).toBeLessThan(500);

    // Test missing required fields
    const response2 = await request.post('http://localhost:8004/api/analyze', {
      headers: { 'Content-Type': 'application/json' },
      data: JSON.stringify({ wrong_field: 'data' })
    });

    expect(response2.status()).toBe(422);

    // Test invalid content type
    const response3 = await request.post('http://localhost:8004/api/analyze', {
      headers: { 'Content-Type': 'text/plain' },
      data: 'plain text data'
    });

    expect(response3.status()).toBeGreaterThanOrEqual(400);

    // Test empty request body
    const response4 = await request.post('http://localhost:8004/api/analyze', {
      headers: { 'Content-Type': 'application/json' },
      data: '{}'
    });

    expect(response4.status()).toBe(422);

    // Verify API still responsive after malformed requests
    const validResponse = await request.post('http://localhost:8004/api/analyze', {
      data: { text: 'valid test request' }
    });

    expect(validResponse.ok()).toBeTruthy();
  });

  test.skip('@failure orchestrator handles agent failures gracefully - show control UI not implemented', async ({ page, request }) => {
    // Navigate to console
    await helper.navigateToConsole();

    // Start show
    await helper.startShow();

    // Stop multiple agents simultaneously
    test.step('Stop multiple agents', () => {
      execSync('docker-compose stop sentiment-agent captioning-agent', {
        cwd: process.cwd(),
        stdio: 'pipe'
      });
    });

    // Verify orchestrator detects failures and updates status
    await expect(async () => {
      const sentimentStatus = page.locator('[data-testid="sentiment-status"]');
      const captioningStatus = page.locator('[data-testid="captioning-status"]');

      const sentimentAttr = await sentimentStatus.getAttribute('data-status');
      const captioningAttr = await captioningStatus.getAttribute('data-status');

      expect(sentimentAttr).toMatch(/unavailable|fallback/);
      expect(captioningAttr).toMatch(/unavailable|fallback/);
    }).toPass({ timeout: 10000 });

    // Verify show continues with degraded functionality
    await expect(page.locator('[data-testid="show-status"][data-state="active"]')).toBeVisible();

    // Restart stopped agents
    test.step('Restart stopped agents', () => {
      execSync('docker-compose start sentiment-agent captioning-agent', {
        cwd: process.cwd(),
        stdio: 'pipe'
      });
    });

    // Wait for agents to recover
    await helper.waitForService('sentiment', 8004, 30, 2000);
    await helper.waitForService('captioning', 8002, 30, 2000);

    // Verify recovery
    await expect(async () => {
      const sentimentStatus = page.locator('[data-testid="sentiment-status"]');
      const captioningStatus = page.locator('[data-testid="captioning-status"]');

      const sentimentAttr = await sentimentStatus.getAttribute('data-status');
      const captioningAttr = await captioningStatus.getAttribute('data-status');

      expect(sentimentAttr).toBe('active');
      expect(captioningAttr).toBe('active');
    }).toPass({ timeout: 15000 });

    // End show
    await helper.endShow();
  });

  test('@failure network timeout handling', async ({ page, request }) => {
    // Test with short timeout to simulate network issues (100ms is realistic for testing)
    const response = await request.post('http://localhost:8001/api/generate', {
      timeout: 100,
      data: {
        prompt: 'This should timeout due to slow processing',
        context: { scene: 'test' }
      }
    });

    // Should handle timeout gracefully
    expect(response.status()).toBeGreaterThanOrEqual(400);

    // Verify service still healthy after timeout
    const healthCheck = await request.get('http://localhost:8001/health');
    expect(healthCheck.ok()).toBeTruthy();
  });

  test.afterEach(async ({ page }) => {
    // Ensure show is ended after each test
    try {
      const showStatus = page.locator('[data-testid="show-status"]');
      const isVisible = await showStatus.isVisible().catch(() => false);

      if (isVisible) {
        const state = await showStatus.getAttribute('data-state');
        if (state === 'active') {
          await helper.endShow();
        }
      }
    } catch (error) {
      console.log('Show cleanup not needed or already cleaned up');
    }

    // Ensure all services are running after failure tests
    const services = ['sentiment-agent', 'bsl-agent', 'scenespeak-agent', 'captioning-agent'];
    for (const service of services) {
      try {
        execSync(`docker-compose start ${service}`, {
          cwd: process.cwd(),
          stdio: 'pipe'
        });
      } catch (error) {
        console.log(`Service ${service} may already be running`);
      }
    }
  });
});
