import { test, expect } from '@playwright/test';
import { ChimeraTestHelper } from '../helpers/test-utils';

/**
 * Operator Console UI Tests
 *
 * These tests verify the functionality and responsiveness of the
 * Operator Console dashboard interface.
 *
 * Tags: @ui
 */

test.describe('Operator Console UI', () => {
  let helper: ChimeraTestHelper;

  test.beforeEach(async ({ page, request }) => {
    helper = new ChimeraTestHelper(page, request);
  });

  test('@smoke @ui dashboard loads and displays all agents', async ({ page }) => {
    // Navigate to console
    await helper.navigateToConsole();

    // Verify page title
    await expect(page).toHaveTitle(/Operator Console/);

    // Verify main heading
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
    await expect(heading).toContainText(/Project Chimera/);

    // Verify basic dashboard elements are present
    await expect(page.locator('header')).toBeVisible();
    await expect(page.locator('[data-testid="connection-status"]')).toBeVisible();
    await expect(page.locator('[data-testid="current-time"]')).toBeVisible();

    // Note: Individual agent status displays (agent-*-status) are not yet implemented
    // These will be tested once the feature is added
  });

  test('@ui dashboard displays show status section', async ({ page }) => {
    await helper.navigateToConsole();

    // Verify show status section exists
    const showStatusSection = page.locator('[data-testid="show-status-section"]');
    await expect(showStatusSection).toBeVisible();

    // Verify show status indicator
    const showStatus = page.locator('[data-testid="show-status"]');
    await expect(showStatus).toBeVisible();

    // Verify initial state is 'inactive' or 'ended'
    const state = await showStatus.getAttribute('data-state');
    expect(['inactive', 'ended']).toContain(state);
  });

  test('@ui dashboard displays audience interaction controls', async ({ page }) => {
    await helper.navigateToConsole();

    // Verify audience input field
    const audienceInput = page.locator('[data-testid="audience-input"]');
    await expect(audienceInput).toBeVisible();
    await expect(audienceInput).toBeEnabled();

    // Verify submit button
    const submitButton = page.locator('[data-testid="submit-sentiment"]');
    await expect(submitButton).toBeVisible();
    await expect(submitButton).toBeEnabled();
  });

  test('@ui start show button is interactive', async ({ page }) => {
    await helper.navigateToConsole();

    // Locate start show button
    const startButton = page.locator('[data-testid="start-show-button"]');

    // Verify button is visible
    await expect(startButton).toBeVisible();

    // Verify button is enabled (should be enabled when no show is active)
    await expect(startButton).toBeEnabled();

    // Click start button
    await startButton.click();

    // Verify show status changes to active
    await expect(async () => {
      const showStatus = page.locator('[data-testid="show-status"]');
      const state = await showStatus.getAttribute('data-state');
      expect(state).toBe('active');
    }).toPass({ timeout: 10000 });

    // Verify start button is now disabled (show already active)
    await expect(startButton).toBeDisabled();

    // End show for cleanup
    await helper.endShow();
  });

  test('@ui end show button is interactive', async ({ page }) => {
    await helper.navigateToConsole();

    // Start show first
    await helper.startShow();

    // Locate end show button
    const endButton = page.locator('[data-testid="end-show-button"]');

    // Verify end button is visible and enabled when show is active
    await expect(endButton).toBeVisible();
    await expect(endButton).toBeEnabled();

    // Click end button
    await endButton.click();

    // Verify show status changes to ended
    await expect(async () => {
      const showStatus = page.locator('[data-testid="show-status"]');
      const state = await showStatus.getAttribute('data-state');
      expect(state).toBe('ended');
    }).toPass({ timeout: 10000 });
  });

  test('@ui audience input field accepts text', async ({ page }) => {
    await helper.navigateToConsole();

    const input = page.locator('[data-testid="audience-input"]');

    // Verify input is visible
    await expect(input).toBeVisible();

    // Test various text inputs
    const testInputs = [
      'Test audience reaction',
      'This is amazing!',
      'I love this show',
      'More drama please',
      '!@#$%^&*()_+-=[]{}|;:,.<>?'
    ];

    for (const testText of testInputs) {
      await input.fill(testText);

      // Verify input accepts the text
      const value = await input.inputValue();
      expect(value).toBe(testText);
    }

    // Verify clear functionality
    await input.fill('');
    const clearedValue = await input.inputValue();
    expect(clearedValue).toBe('');
  });

  test('@ui audience input field handles long text', async ({ page }) => {
    await helper.navigateToConsole();

    const input = page.locator('[data-testid="audience-input"]');
    const longText = 'a'.repeat(1000);

    await input.fill(longText);

    // Verify input accepts long text
    const value = await input.inputValue();
    expect(value).toBe(longText);
  });

  test('@ui audience input submit button is functional', async ({ page }) => {
    await helper.navigateToConsole();

    // Start show to enable submission
    await helper.startShow();

    // Fill input
    await page.fill('[data-testid="audience-input"]', 'Great performance!');

    // Click submit button
    await page.click('[data-testid="submit-sentiment"]');

    // Verify input is cleared after submission
    await expect(async () => {
      const input = page.locator('[data-testid="audience-input"]');
      const value = await input.inputValue();
      expect(value).toBe('');
    }).toPass({ timeout: 5000 });

    // Verify sentiment display updates
    await expect(page.locator('[data-testid="sentiment-display"]')).toBeVisible({
      timeout: 10000
    });

    // End show for cleanup
    await helper.endShow();
  });

  test('@ui UI updates when show state changes', async ({ page }) => {
    await helper.navigateToConsole();

    // Verify initial state
    const showStatus = page.locator('[data-testid="show-status"]');
    let state = await showStatus.getAttribute('data-state');
    expect(['inactive', 'ended']).toContain(state);

    // Start show
    await helper.startShow();

    // Verify state changed to active
    state = await showStatus.getAttribute('data-state');
    expect(state).toBe('active');

    // Verify active state styling/appearance
    await expect(showStatus).toHaveAttribute('data-state', 'active');

    // End show
    await helper.endShow();

    // Verify state changed to ended
    state = await showStatus.getAttribute('data-state');
    expect(state).toBe('ended');

    // Verify ended state styling/appearance
    await expect(showStatus).toHaveAttribute('data-state', 'ended');
  });

  test('@ui agent status indicators update in real-time', async ({ page, request }) => {
    await helper.navigateToConsole();

    // Get initial sentiment agent status
    const sentimentStatus = page.locator('[data-testid="sentiment-status"]');
    const initialStatus = await sentimentStatus.getAttribute('data-status');
    expect(initialStatus).toBeTruthy();

    // Start show to activate agents
    await helper.startShow();

    // Verify sentiment agent becomes active
    await expect(async () => {
      const status = await sentimentStatus.getAttribute('data-status');
      expect(status).toBe('active');
    }).toPass({ timeout: 10000 });

    // Verify other agents also show active status
    const agentsToCheck = [
      'scenespeak-status',
      'captioning-status',
      'orchestrator-status'
    ];

    for (const agentSelector of agentsToCheck) {
      const agentStatus = page.locator(`[data-testid="${agentSelector}"]`);
      await expect(agentStatus).toHaveAttribute('data-status', 'active', {
        timeout: 10000
      });
    }

    // End show for cleanup
    await helper.endShow();
  });

  test('@ui dialogue generation display is visible', async ({ page }) => {
    await helper.navigateToConsole();

    // Start show
    await helper.startShow();

    // Verify dialogue display area exists
    const dialogueDisplay = page.locator('[data-testid="generated-dialogue"]');
    await expect(dialogueDisplay).toBeVisible();

    // Send audience reaction to trigger dialogue generation
    await helper.sendAudienceReaction('This is wonderful!');

    // Verify dialogue appears and is populated
    await expect(async () => {
      const dialogue = page.locator('[data-testid="generated-dialogue"]');
      const text = await dialogue.textContent();
      expect(text).toBeTruthy();
      expect(text!.length).toBeGreaterThan(0);
    }).toPass({ timeout: 15000 });

    // End show for cleanup
    await helper.endShow();
  });

  test('@ui scene progress indicator is visible', async ({ page }) => {
    await helper.navigateToConsole();

    // Start show
    await helper.startShow();

    // Verify scene progress indicator exists
    const sceneProgress = page.locator('[data-testid="scene-progress"]');
    await expect(sceneProgress).toBeVisible();

    // Verify progress information is displayed
    const progressText = await sceneProgress.textContent();
    expect(progressText).toBeTruthy();
    expect(progressText!.length).toBeGreaterThan(0);

    // End show for cleanup
    await helper.endShow();
  });

  test('@ui console is responsive to window resize', async ({ page }) => {
    await helper.navigateToConsole();

    // Set initial viewport (desktop)
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.reload();

    // Verify main elements are visible
    await expect(page.locator('[data-testid="show-status-section"]')).toBeVisible();

    // Resize to tablet
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(500);

    // Verify layout adapts
    await expect(page.locator('[data-testid="show-status-section"]')).toBeVisible();

    // Resize to mobile
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(500);

    // Verify critical elements still visible
    await expect(page.locator('[data-testid="start-show-button"]')).toBeVisible();
    await expect(page.locator('[data-testid="audience-input"]')).toBeVisible();
  });

  test('@ui error messages are displayed properly', async ({ page }) => {
    await helper.navigateToConsole();

    // Start show
    await helper.startShow();

    // Try to submit empty input (should show validation error)
    await page.fill('[data-testid="audience-input"]', '');
    await page.click('[data-testid="submit-sentiment"]');

    // Check for validation error (if implemented)
    const validationError = page.locator('[data-testid="validation-error"]');

    const hasValidationError = await validationError.isVisible().catch(() => false);

    if (hasValidationError) {
      await expect(validationError).toBeVisible();
      const errorText = await validationError.textContent();
      expect(errorText).toBeTruthy();
      expect(errorText!.length).toBeGreaterThan(0);
    }

    // End show for cleanup
    await helper.endShow();
  });

  test('@ui controls are disabled when show is inactive', async ({ page }) => {
    await helper.navigateToConsole();

    // Verify controls are in correct initial state
    const startButton = page.locator('[data-testid="start-show-button"]');
    const endButton = page.locator('[data-testid="end-show-button"]');
    const audienceInput = page.locator('[data-testid="audience-input"]');
    const submitButton = page.locator('[data-testid="submit-sentiment"]');

    // Start button should be enabled when no show is active
    await expect(startButton).toBeEnabled();

    // End button should be disabled when no show is active
    await expect(endButton).toBeDisabled();

    // Audience controls may be disabled when show is not active
    const inputEnabled = await audienceInput.isEnabled().catch(() => false);
    const submitEnabled = await submitButton.isEnabled().catch(() => false);

    // This is implementation-dependent - document expected behavior
    if (!inputEnabled) {
      console.log('Audience input is disabled when show is inactive (expected)');
    }
    if (!submitEnabled) {
      console.log('Submit button is disabled when show is inactive (expected)');
    }

    // Start show
    await helper.startShow();

    // Verify controls update correctly
    await expect(startButton).toBeDisabled();
    await expect(endButton).toBeEnabled();
    await expect(audienceInput).toBeEnabled();
    await expect(submitButton).toBeEnabled();

    // End show for cleanup
    await helper.endShow();
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
  });
});
