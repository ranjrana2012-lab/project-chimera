import { test, expect } from '@playwright/test';
import { ChimeraTestHelper } from '../helpers/test-utils';
import { createWebSocketClient } from '../helpers/websocket-client';

/**
 * Complete Show Workflow E2E Tests
 *
 * Tests the full end-to-end workflow for Project Chimera shows:
 * - Audience input → Sentiment analysis → Dialogue generation → BSL avatar → Show progression
 * - Cross-service communication
 * - Operator Console UI interactions
 * - Real-time WebSocket updates
 *
 * Tags:
 * - @workflow: Full end-to-end workflow tests
 * - @smoke: Critical path smoke tests
 * - @sentiment: Sentiment pipeline tests
 * - @dialogue: Dialogue generation tests
 * - @bsl: BSL avatar tests
 */

test.describe('Complete Show Workflow', () => {
  let helper: ChimeraTestHelper;

  // Initialize helper before each test
  test.beforeEach(async ({ page, request }) => {
    helper = new ChimeraTestHelper(page, request);
  });

  test.skip('@smoke @workflow full show workflow from audience input to BSL avatar', async ({ page, request }) => {
    // 1. Navigate to Operator Console
    await helper.navigateToConsole();
    await expect(page).toHaveTitle(/Operator Console/);

    // 2. Start a new show
    await page.click('[data-testid="start-show-button"]');
    await helper.waitForShowState('active', 30000);

    // 3. Simulate audience sentiment input
    await helper.sendAudienceReaction('The audience loves this scene!');

    // 4. Verify sentiment is processed and displayed
    await expect(page.locator('[data-testid="sentiment-display"]')).toBeVisible({
      timeout: 10000
    });
    const sentiment = await page.textContent('[data-testid="sentiment-display"]');
    expect(sentiment).toBeTruthy();
    expect(sentiment?.length).toBeGreaterThan(0);

    // 5. Verify dialogue is generated based on sentiment
    await expect(page.locator('[data-testid="generated-dialogue"]')).toBeVisible({
      timeout: 15000
    });
    const dialogue = await page.textContent('[data-testid="generated-dialogue"]');
    expect(dialogue).toBeTruthy();
    expect(dialogue?.length).toBeGreaterThan(50); // Dialogue should be substantial

    // 6. Connect WebSocket to verify BSL avatar update
    const wsClient = await createWebSocketClient('ws://localhost:8003/ws/avatar', {
      connectionTimeout: 10000
    });
    const animationMsg = await wsClient.waitForMessage('animation_update', 10000);
    expect(animationMsg.nmm_data).toBeTruthy();
    wsClient.close();

    // 7. Verify scene progress tracking
    await expect(page.locator('[data-testid="scene-progress"]')).toBeVisible({
      timeout: 30000
    });
    const progress = await page.textContent('[data-testid="scene-progress"]');
    expect(progress).toBeTruthy();

    // 8. End show gracefully
    await page.click('[data-testid="end-show-button"]');
    await helper.waitForShowState('ended', 30000);
  });

  test.skip('@workflow sentiment to dialogue pipeline - UI not implemented', async ({ page, request }) => {
    // Start show
    await helper.navigateToConsole();
    await helper.startShow();

    // Send positive sentiment input
    const positiveReaction = 'This is amazing! I love it!';
    await helper.sendAudienceReaction(positiveReaction);

    // Verify sentiment analysis API response
    const sentimentResponse = await request.post('http://localhost:8004/api/analyze', {
      data: { text: positiveReaction }
    });
    expect(sentimentResponse.ok()).toBeTruthy();

    const sentimentData = await sentimentResponse.json();
    expect(sentimentData).toMatchObject({
      sentiment: expect.any(String),
      score: expect.any(Number),
      confidence: expect.any(Number)
    });
    expect(['positive', 'negative', 'neutral']).toContain(sentimentData.sentiment);

    // Verify dialogue is generated incorporating sentiment
    await expect(page.locator('[data-testid="generated-dialogue"]')).toBeVisible({
      timeout: 15000
    });
    const dialogue = await page.textContent('[data-testid="generated-dialogue"]');
    expect(dialogue).toBeTruthy();
    expect(dialogue?.length).toBeGreaterThan(50);

    // Verify sentiment is displayed in UI
    await expect(page.locator('[data-testid="sentiment-display"]')).toBeVisible();
    const displayedSentiment = await page.textContent('[data-testid="sentiment-display"]');
    expect(displayedSentiment).toBeTruthy();

    // End show
    await helper.endShow();
  });

  test.skip('@workflow negative sentiment triggers adaptive response - UI not implemented', async ({ page, request }) => {
    // Start show
    await helper.navigateToConsole();
    await helper.startShow();

    // Send negative sentiment
    const negativeReaction = 'This is boring and confusing';
    await helper.sendAudienceReaction(negativeReaction);

    // Verify sentiment is detected as negative
    const sentimentResponse = await request.post('http://localhost:8004/api/analyze', {
      data: { text: negativeReaction }
    });
    const sentimentData = await sentimentResponse.json();
    expect(sentimentData.sentiment).toBe('negative');

    // Verify dialogue adapts to negative sentiment
    await expect(page.locator('[data-testid="generated-dialogue"]')).toBeVisible({
      timeout: 15000
    });
    const dialogue = await page.textContent('[data-testid="generated-dialogue"]');
    expect(dialogue).toBeTruthy();

    // Verify show continues despite negative sentiment
    await expect(page.locator('[data-testid="show-status"][data-state="active"]')).toBeVisible();

    // End show
    await helper.endShow();
  });

  test.skip('@workflow multiple audience inputs accumulate - UI not implemented', async ({ page }) => {
    // Start show
    await helper.navigateToConsole();
    await helper.startShow();

    // Send multiple audience reactions
    const reactions = [
      'This is great!',
      'I love the character development',
      'More please!',
      'Absolutely brilliant!'
    ];

    for (const reaction of reactions) {
      await helper.sendAudienceReaction(reaction);
      // Wait for sentiment analysis response instead of hard-coded delay
      await page.waitForResponse(resp => resp.url().includes('/api/analyze'), { timeout: 5000 });
    }

    // Verify sentiment history is tracked
    await expect(page.locator('[data-testid="sentiment-history"]')).toBeVisible({
      timeout: 10000
    });

    // Verify multiple dialogue responses generated
    await expect(page.locator('[data-testid="generated-dialogue"]')).toBeVisible();

    // End show
    await helper.endShow();
  });

  test.skip('@dialogue dialogue generation includes character context - UI not implemented', async ({ page, request }) => {
    // Start show
    await helper.navigateToConsole();
    await helper.startShow();

    // Send audience reaction
    await helper.sendAudienceReaction('Tell me more about the hero');

    // Verify dialogue generation request includes context
    const dialogueResponse = await request.post('http://localhost:8001/api/generate', {
      data: {
        prompt: 'The hero enters the room',
        context: {
          scene: 'act1_scene1',
          character: 'Hamlet',
          mood: 'melancholic'
        }
      }
    });

    expect(dialogueResponse.ok()).toBeTruthy();
    const dialogueData = await dialogueResponse.json();
    expect(dialogueData).toMatchObject({
      dialogue: expect.any(String),
      metadata: expect.objectContaining({
        model: expect.any(String),
        latency_ms: expect.any(Number)
      })
    });

    // Verify dialogue is displayed
    await expect(page.locator('[data-testid="generated-dialogue"]')).toBeVisible({
      timeout: 15000
    });

    // End show
    await helper.endShow();
  });

  test.skip('@bsl BSL avatar receives dialogue for translation - UI not implemented', async ({ page }) => {
    // Start show
    await helper.navigateToConsole();
    await helper.startShow();

    // Connect to BSL WebSocket before sending input
    const wsClient = await createWebSocketClient('ws://localhost:8003/ws/avatar', {
      connectionTimeout: 10000
    });

    // Send audience reaction
    await helper.sendAudienceReaction('Hello, how are you?');

    // Wait for animation update
    const animationMsg = await wsClient.waitForMessage('animation_update', 10000);
    expect(animationMsg).toMatchObject({
      type: 'animation_update',
      nmm_data: expect.any(String)
    });

    // Verify animation data is valid
    expect(animationMsg.nmm_data.length).toBeGreaterThan(0);

    wsClient.close();

    // End show
    await helper.endShow();
  });

  test.skip('@workflow show state transitions correctly - UI not implemented', async ({ page }) => {
    await helper.navigateToConsole();

    // Verify initial state is 'idle' or 'stopped'
    const initialState = await helper.getCurrentShowState();
    expect(['idle', 'stopped', '']).toContain(initialState);

    // Start show and verify 'active' state
    await helper.startShow();
    const activeState = await helper.getCurrentShowState();
    expect(activeState).toBe('active');

    // End show and verify 'ended' state
    await helper.endShow();
    const endedState = await helper.getCurrentShowState();
    expect(endedState).toBe('ended');
  });

  test.skip('@workflow show handles rapid audience input - UI not implemented', async ({ page }) => {
    // Start show
    await helper.navigateToConsole();
    await helper.startShow();

    // Send rapid inputs
    const rapidInputs = ['Great!', 'Amazing!', 'Love it!', 'More!'];

    for (const input of rapidInputs) {
      await helper.sendAudienceReaction(input);
      // Wait for response before sending next input
      await page.waitForResponse(resp => resp.url().includes('/api/analyze'), { timeout: 5000 });
    }

    // Verify system remains stable
    await expect(page.locator('[data-testid="show-status"][data-state="active"]')).toBeVisible();

    // Verify dialogue is still being generated
    await expect(page.locator('[data-testid="generated-dialogue"]')).toBeVisible({
      timeout: 20000 // Longer timeout for processing
    });

    // End show
    await helper.endShow();
  });

  test.skip('@workflow cross-service metrics are tracked - UI not implemented', async ({ page, request }) => {
    // Start show
    await helper.navigateToConsole();
    await helper.startShow();

    // Send audience reaction
    await helper.sendAudienceReaction('Test sentiment');

    // Wait for processing to complete
    await expect(page.locator('[data-testid="sentiment-display"]')).toBeVisible({ timeout: 5000 });

    // Verify metrics are being tracked (may not exist in dev environment)
    try {
      const sentimentMetric = await helper.getMetric('chimera_sentiment_analysis_total');
      expect(sentimentMetric).toBeGreaterThanOrEqual(0);
    } catch (error) {
      // Metrics may not be available in all environments
      console.log('Metrics not available, skipping metric verification');
    }

    // End show
    await helper.endShow();
  });

  test.skip('@smoke @workflow operator console UI is responsive during show', async ({ page }) => {
    // Start show
    await helper.navigateToConsole();
    await helper.startShow();

    // Verify all key UI elements are visible and responsive
    await expect(page.locator('[data-testid="show-status"]')).toBeVisible();
    await expect(page.locator('[data-testid="sentiment-display"]')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('[data-testid="audience-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="submit-sentiment"]')).toBeVisible();
    await expect(page.locator('[data-testid="end-show-button"]')).toBeVisible();
    await expect(page.locator('[data-testid="start-show-button"]')).toBeDisabled();

    // Verify agent status indicators are visible
    const agents = ['orchestrator', 'scenespeak', 'captioning', 'bsl', 'sentiment'];
    for (const agent of agents) {
      await expect(page.locator(`[data-testid="agent-${agent}-status"]`)).toBeVisible();
    }

    // End show
    await helper.endShow();
  });

  test.skip('@workflow show recovery after brief pause - UI not implemented', async ({ page }) => {
    // Start show
    await helper.navigateToConsole();
    await helper.startShow();

    // Send initial reaction
    await helper.sendAudienceReaction('First reaction');

    // Wait for first response
    await page.waitForResponse(resp => resp.url().includes('/api/analyze'), { timeout: 10000 });

    // Send another reaction
    await helper.sendAudienceReaction('Second reaction after pause');

    // Verify system recovered and processed second input
    await expect(page.locator('[data-testid="sentiment-display"]')).toBeVisible({
      timeout: 10000
    });

    // End show
    await helper.endShow();
  });

  test.skip('@workflow complete show lifecycle with multiple scenes - UI not implemented', async ({ page }) => {
    // Start show
    await helper.navigateToConsole();
    await helper.startShow();

    // Simulate audience reactions for scene 1
    await helper.sendAudienceReaction('Scene 1 is great!');
    await expect(page.locator('[data-testid="generated-dialogue"]')).toBeVisible({
      timeout: 15000
    });

    // Wait for scene progression
    await expect(page.locator('[data-testid="scene-progress"]')).toBeVisible({ timeout: 10000 });

    // Simulate reactions for scene 2
    await helper.sendAudienceReaction('Scene 2 is even better!');
    await expect(page.locator('[data-testid="scene-progress"]')).toBeVisible();

    // Verify show remains active throughout
    await expect(page.locator('[data-testid="show-status"][data-state="active"]')).toBeVisible();

    // End show
    await helper.endShow();

    // Verify show ended cleanly
    const finalState = await helper.getCurrentShowState();
    expect(finalState).toBe('ended');
  });
});

/**
 * Test helpers and utilities
 */
test.describe('Show Workflow Helpers', () => {
  test('verify test helper utilities are available', async ({ page, request }) => {
    const helper = new ChimeraTestHelper(page, request);

    // Verify helper methods exist
    expect(typeof helper.checkServiceHealth).toBe('function');
    expect(typeof helper.createWebSocketClient).toBe('function');
    expect(typeof helper.waitForShowState).toBe('function');
    expect(typeof helper.sendAudienceReaction).toBe('function');
    expect(typeof helper.getMetric).toBe('function');
    expect(typeof helper.navigateToConsole).toBe('function');
    expect(typeof helper.startShow).toBe('function');
    expect(typeof helper.endShow).toBe('function');
  });
});
