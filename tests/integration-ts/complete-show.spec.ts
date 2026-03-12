/**
 * Complete Show Workflow Integration Tests
 *
 * Tests the full end-to-end workflow for Project Chimera shows:
 * - Audience input → Sentiment analysis → Dialogue generation → BSL avatar → Show progression
 * - Cross-service communication
 * - Real-time WebSocket updates
 * - Complete show lifecycle
 *
 * @tags integration, workflow, smoke
 */

import { test, expect } from './conftest';
import { createWebSocketClient } from '../e2e/helpers/websocket-client';

test.describe('Complete Show Workflow', () => {
  test.beforeEach(async ({ waitForService }) => {
    // Ensure critical services are running
    const criticalServices = ['orchestrator', 'scenespeak', 'sentiment', 'bsl', 'safety'];

    for (const service of criticalServices) {
      const isHealthy = await waitForService(service);
      if (!isHealthy) {
        test.skip(true, `Service ${service} is not available`);
      }
    }
  });

  test('@smoke @workflow complete show from audience input to BSL display', async ({ services, testData, helper, page }) => {
    // Step 1: Start the show
    const showContext = testData.createShowContext();
    const startResponse = await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'start_show',
        show_id: showContext.show_id,
        context: showContext
      }
    });

    expect(startResponse.ok()).toBeTruthy();
    const startData = await startResponse.json();
    expect(startData).toHaveProperty('show_id', showContext.show_id);
    expect(startData).toHaveProperty('status', 'starting');

    // Step 2: Simulate audience input
    const audienceReaction = testData.createAudienceReaction({
      text: 'This is amazing! I love the show!',
      sentiment: 'positive'
    });

    // Submit audience reaction
    const reactionResponse = await services.sentiment.post('http://localhost:8004/api/analyze', {
      data: {
        text: audienceReaction.text
      }
    });

    expect(reactionResponse.ok()).toBeTruthy();
    const sentimentData = await reactionResponse.json();
    expect(sentimentData).toHaveProperty('sentiment');
    expect(sentimentData).toHaveProperty('score');
    expect(['positive', 'negative', 'neutral']).toContain(sentimentData.sentiment);

    // Step 3: Generate dialogue based on sentiment
    const dialoguePrompt = testData.createDialoguePrompt({
      prompt: `Generate a response to audience member who said: "${audienceReaction.text}"`,
      context: {
        ...showContext,
        audience_sentiment: sentimentData.sentiment
      }
    });

    const dialogueResponse = await services.scenespeak.post('http://localhost:8001/api/generate', {
      data: dialoguePrompt
    });

    expect(dialogueResponse.ok()).toBeTruthy();
    const dialogueData = await dialogueResponse.json();
    const dialogueText = dialogueData.text || dialogueData.dialogue || '';
    expect(dialogueText.length).toBeGreaterThan(20);

    // Step 4: Translate to BSL
    const bslRequest = testData.createBSLText({
      text: dialogueText
    });

    const bslResponse = await services.bsl.post('http://localhost:8003/v1/translate', {
      data: bslRequest
    });

    expect(bslResponse.ok()).toBeTruthy();
    const bslData = await bslResponse.json();
    expect(bslData).toHaveProperty('gloss');
    expect(bslData.gloss.length).toBeGreaterThan(0);

    // Step 5: Check safety
    const safetyRequest = testData.createSafetyCheck(dialogueText, 'family');
    const safetyResponse = await services.safety.post('http://localhost:8006/api/moderate', {
      data: safetyRequest
    });

    expect(safetyResponse.ok()).toBeTruthy();
    const safetyData = await safetyResponse.json();
    expect(safetyData).toHaveProperty('safe');
    expect(safetyData).toHaveProperty('result');

    // Step 6: Verify BSL avatar receives the translation
    const wsClient = await createWebSocketClient('ws://localhost:8003/ws/avatar');
    const animationMsg = await wsClient.waitForMessage('animation_update', 10000);
    expect(animationMsg).toHaveProperty('nmm_data');
    expect(animationMsg.nmm_data.length).toBeGreaterThan(0);
    wsClient.close();

    // Step 7: End the show
    const endResponse = await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'end_show',
        show_id: showContext.show_id
      }
    });

    expect(endResponse.ok()).toBeTruthy();
    const endData = await endResponse.json();
    expect(endData).toHaveProperty('status', 'ended');
  });

  test('@workflow positive audience sentiment flow', async ({ services, testData }) => {
    // Create positive sentiment context
    const showContext = testData.createShowContext();
    const positiveReaction = testData.createAudienceReaction({
      text: 'Absolutely brilliant performance! The actors are amazing!',
      sentiment: 'positive'
    });

    // Analyze sentiment
    const sentimentResponse = await services.sentiment.post('http://localhost:8004/api/analyze', {
      data: {
        text: positiveReaction.text
      }
    });

    expect(sentimentResponse.ok()).toBeTruthy();
    const sentimentData = await sentimentResponse.json();
    expect(sentimentData.sentiment).toBe('positive');
    expect(sentimentData.score).toBeGreaterThan(0.5);

    // Generate dialogue incorporating positive sentiment
    const dialogueResponse = await services.scenespeak.post('http://localhost:8001/api/generate', {
      data: {
        prompt: 'Acknowledge the audience enthusiasm',
        context: {
          ...showContext,
          audience_sentiment: 'positive',
          sentiment_score: sentimentData.score
        },
        max_tokens: 60,
        temperature: 0.8
      }
    });

    expect(dialogueResponse.ok()).toBeTruthy();
    const dialogueData = await dialogueResponse.json();
    const dialogueText = dialogueData.text || dialogueData.dialogue || '';
    expect(dialogueText.length).toBeGreaterThan(30);

    // Verify BSL translation works
    const bslResponse = await services.bsl.post('http://localhost:8003/v1/translate', {
      data: {
        text: dialogueText,
        include_nmm: true
      }
    });

    expect(bslResponse.ok()).toBeTruthy();
    const bslData = await bslResponse.json();
    expect(bslData).toHaveProperty('gloss');
    expect(bslData).toHaveProperty('confidence');
  });

  test('@workflow negative audience sentiment flow', async ({ services, testData }) => {
    const showContext = testData.createShowContext();
    const negativeReaction = testData.createAudienceReaction({
      text: 'This is confusing and hard to follow. What is happening?',
      sentiment: 'negative'
    });

    // Analyze sentiment
    const sentimentResponse = await services.sentiment.post('http://localhost:8004/api/analyze', {
      data: {
        text: negativeReaction.text
      }
    });

    expect(sentimentResponse.ok()).toBeTruthy();
    const sentimentData = await sentimentResponse.json();
    expect(sentimentData.sentiment).toBe('negative');

    // Generate adaptive dialogue
    const dialogueResponse = await services.scenespeak.post('http://localhost:8001/api/generate', {
      data: {
        prompt: 'Address audience confusion and clarify the plot',
        context: {
          ...showContext,
          audience_sentiment: 'negative',
          sentiment_score: sentimentData.score
        },
        max_tokens: 80,
        temperature: 0.7
      }
    });

    expect(dialogueResponse.ok()).toBeTruthy();
    const dialogueData = await dialogueResponse.json();
    const dialogueText = dialogueData.text || dialogueData.dialogue || '';
    expect(dialogueText.length).toBeGreaterThan(40);

    // Verify safety check passes
    const safetyResponse = await services.safety.post('http://localhost:8006/api/moderate', {
      data: {
        content: dialogueText,
        policy: 'family'
      }
    });

    expect(safetyResponse.ok()).toBeTruthy();
    const safetyData = await safetyResponse.json();
    expect(safetyData.result || safetyData).toHaveProperty('is_safe');
  });

  test('@workflow multiple audience inputs accumulate', async ({ services, testData }) => {
    const showContext = testData.createShowContext();
    const reactions = [
      'This is great!',
      'I love the character development',
      'More please!',
      'Absolutely brilliant!'
    ];

    const sentimentResults = [];

    // Process each reaction
    for (const reactionText of reactions) {
      const sentimentResponse = await services.sentiment.post('http://localhost:8004/api/analyze', {
        data: {
          text: reactionText
        }
      });

      expect(sentimentResponse.ok()).toBeTruthy();
      const sentimentData = await sentimentResponse.json();
      sentimentResults.push({
        text: reactionText,
        sentiment: sentimentData.sentiment,
        score: sentimentData.score
      });
    }

    // Generate dialogue based on accumulated sentiment
    const avgScore = sentimentResults.reduce((sum, r) => sum + r.score, 0) / sentimentResults.length;
    const dominantSentiment = avgScore > 0.5 ? 'positive' : avgScore < 0.3 ? 'negative' : 'neutral';

    const dialogueResponse = await services.scenespeak.post('http://localhost:8001/api/generate', {
      data: {
        prompt: 'Respond to the enthusiastic audience',
        context: {
          ...showContext,
          audience_sentiment: dominantSentiment,
          sentiment_score: avgScore,
          reaction_count: reactions.length
        },
        max_tokens: 70
      }
    });

    expect(dialogueResponse.ok()).toBeTruthy();
    const dialogueData = await dialogueResponse.json();
    expect(dialogueData.text || dialogueData.dialogue).toBeTruthy();
  });

  test('@workflow dialogue generation includes character context', async ({ services, testData }) => {
    const showContext = testData.createShowContext({
      adapter: 'drama',
      scene: 1,
      act: 1
    });

    const dialogueResponse = await services.scenespeak.post('http://localhost:8001/api/generate', {
      data: {
        prompt: 'The hero enters the time machine',
        context: {
          ...showContext,
          character: 'Hamlet',
          mood: 'melancholic',
          scene_setting: 'laboratory'
        },
        max_tokens: 50,
        temperature: 0.7
      }
    });

    expect(dialogueResponse.ok()).toBeTruthy();
    const dialogueData = await dialogueResponse.json();
    expect(dialogueData).toHaveProperty('text');
    expect(dialogueData).toHaveProperty('metadata');
    expect(dialogueData.metadata).toHaveProperty('model');
    expect(dialogueData.metadata).toHaveProperty('latency_ms');
  });

  test('@bsl BSL avatar receives dialogue for translation', async ({ services, testData, websockets }) => {
    const dialogueText = 'Hello, how are you? Welcome to our show!';

    // Connect WebSocket before sending translation request
    const wsClient = await createWebSocketClient('ws://localhost:8003/ws/avatar');

    // Send translation request
    const bslResponse = await services.bsl.post('http://localhost:8003/v1/translate', {
      data: {
        text: dialogueText,
        include_nmm: true
      }
    });

    expect(bslResponse.ok()).toBeTruthy();

    // Wait for animation update
    const animationMsg = await wsClient.waitForMessage('animation_update', 10000);
    expect(animationMsg).toMatchObject({
      type: 'animation_update',
      nmm_data: expect.any(String)
    });
    expect(animationMsg.nmm_data.length).toBeGreaterThan(0);

    wsClient.close();
  });

  test('@workflow show state transitions correctly', async ({ services, testData }) => {
    const showContext = testData.createShowContext();
    const showId = showContext.show_id;

    // Initial state should be idle or stopped
    let statusResponse = await services.orchestrator.get(`http://localhost:8000/api/show/status?show_id=${showId}`);
    expect(statusResponse.ok()).toBeTruthy();
    let statusData = await statusResponse.json();
    expect(['idle', 'stopped', 'active']).toContain(statusData.status);

    // Start show
    const startResponse = await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'start_show',
        show_id: showId
      }
    });

    expect(startResponse.ok()).toBeTruthy();
    const startData = await startResponse.json();
    expect(startData.status).toBe('starting');

    // Verify active state
    statusResponse = await services.orchestrator.get(`http://localhost:8000/api/show/status?show_id=${showId}`);
    statusData = await statusResponse.json();
    expect(statusData.status).toBe('active');

    // Pause show
    const pauseResponse = await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'pause_show',
        show_id: showId
      }
    });

    expect(pauseResponse.ok()).toBeTruthy();
    const pauseData = await pauseResponse.json();
    expect(pauseData.status).toBe('paused');

    // Resume show
    const resumeResponse = await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'resume_show',
        show_id: showId
      }
    });

    expect(resumeResponse.ok()).toBeTruthy();
    const resumeData = await resumeResponse.json();
    expect(resumeData.status).toBe('active');

    // End show
    const endResponse = await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'end_show',
        show_id: showId
      }
    });

    expect(endResponse.ok()).toBeTruthy();
    const endData = await endResponse.json();
    expect(endData.status).toBe('ended');
  });

  test('@workflow show handles rapid audience input', async ({ services, testData }) => {
    const showContext = testData.createShowContext();
    const rapidInputs = ['Great!', 'Amazing!', 'Love it!', 'More!'];

    // Start show
    await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'start_show',
        show_id: showContext.show_id
      }
    });

    // Send rapid inputs
    const promises = rapidInputs.map(input =>
      services.sentiment.post('http://localhost:8004/api/analyze', {
        data: { text: input }
      })
    );

    const results = await Promise.all(promises);

    // All requests should succeed
    for (const result of results) {
      expect(result.ok()).toBeTruthy();
    }

    // Verify show is still active
    const statusResponse = await services.orchestrator.get(`http://localhost:8000/api/show/status?show_id=${showContext.show_id}`);
    expect(statusResponse.ok()).toBeTruthy();
    const statusData = await statusResponse.json();
    expect(statusData.status).toBe('active');
  });

  test('@workflow complete show lifecycle with multiple scenes', async ({ services, testData }) => {
    const showContext = testData.createShowContext();

    // Start show
    await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'start_show',
        show_id: showContext.show_id
      }
    });

    // Scene 1
    const scene1Reaction = 'Scene 1 is great!';
    await services.sentiment.post('http://localhost:8004/api/analyze', {
      data: { text: scene1Reaction }
    });

    // Generate dialogue for scene 1
    const scene1Dialogue = await services.scenespeak.post('http://localhost:8001/api/generate', {
      data: {
        prompt: 'Continue the story in scene 1',
        context: { ...showContext, scene: 1 },
        max_tokens: 50
      }
    });
    expect(scene1Dialogue.ok()).toBeTruthy();

    // Transition to scene 2
    await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'next_scene',
        show_id: showContext.show_id,
        scene_number: 2
      }
    });

    // Scene 2
    const scene2Reaction = 'Scene 2 is even better!';
    await services.sentiment.post('http://localhost:8004/api/analyze', {
      data: { text: scene2Reaction }
    });

    // Generate dialogue for scene 2
    const scene2Dialogue = await services.scenespeak.post('http://localhost:8001/api/generate', {
      data: {
        prompt: 'Continue the story in scene 2',
        context: { ...showContext, scene: 2 },
        max_tokens: 50
      }
    });
    expect(scene2Dialogue.ok()).toBeTruthy();

    // Verify show is still active
    const statusResponse = await services.orchestrator.get(`http://localhost:8000/api/show/status?show_id=${showContext.show_id}`);
    expect(statusResponse.ok()).toBeTruthy();
    const statusData = await statusResponse.json();
    expect(statusData.status).toBe('active');

    // End show
    await services.orchestrator.post('http://localhost:8000/api/show/control', {
      data: {
        action: 'end_show',
        show_id: showContext.show_id
      }
    });
  });
});
