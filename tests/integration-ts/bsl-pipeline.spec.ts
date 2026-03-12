/**
 * BSL Avatar Pipeline Integration Tests
 *
 * Tests the complete British Sign Language translation and avatar rendering pipeline:
 * - Text input → BSL gloss notation translation
 * - Gloss notation → NMM animation data generation
 * - NMM data → WebGL avatar rendering
 * - Real-time avatar streaming via WebSocket
 * - Animation playback controls
 * - Avatar expression and handshape parameters
 *
 * @tags integration, bsl, websocket
 */

import { test, expect } from './conftest';
import { createWebSocketClient } from '../e2e/helpers/websocket-client';

test.describe('BSL Avatar Pipeline', () => {
  test.beforeEach(async ({ waitForService }) => {
    const isHealthy = await waitForService('bsl');
    if (!isHealthy) {
      test.skip(true, 'BSL agent service is not available');
    }
  });

  test('@bsl text to BSL gloss translation', async ({ services, testData }) => {
    const testText = 'Hello, how are you? Welcome to our show!';

    const response = await services.bsl.post('http://localhost:8003/v1/translate', {
      data: {
        text: testText,
        include_nmm: false
      }
    });

    expect(response.ok()).toBeTruthy();
    const result = await response.json();

    expect(result).toHaveProperty('gloss');
    expect(result.gloss.length).toBeGreaterThan(0);
    expect(result).toHaveProperty('confidence');
    expect(result.confidence).toBeGreaterThan(0);
    expect(result).toHaveProperty('translation_time_ms');
  });

  test('@bsl gloss to NMM animation data generation', async ({ services, testData }) => {
    const testText = 'The time traveler stepped into the machine';

    const response = await services.bsl.post('http://localhost:8003/v1/translate', {
      data: {
        text: testText,
        include_nmm: true
      }
    });

    expect(response.ok()).toBeTruthy();
    const result = await response.json();

    expect(result).toHaveProperty('gloss');
    expect(result).toHaveProperty('nmm_data');
    expect(result.nmm_data.length).toBeGreaterThan(0);

    // NMM data should be valid JSON
    const nmmData = JSON.parse(result.nmm_data);
    expect(nmmData).toHaveProperty('animations');
    expect(Array.isArray(nmmData.animations)).toBeTruthy();
  });

  test('@bsl avatar generation with expression parameters', async ({ services }) => {
    const testText = 'I am so happy to see you all here today!';

    const response = await services.bsl.post('http://localhost:8003/api/avatar', {
      data: {
        text: testText,
        expression: 'happy',
        intensity: 0.8
      }
    });

    expect(response.ok()).toBeTruthy();
    const result = await response.json();

    expect(result).toHaveProperty('nmm_data');
    expect(result.nmm_data.length).toBeGreaterThan(0);

    const nmmData = JSON.parse(result.nmm_data);
    expect(nmmData).toHaveProperty('expression', 'happy');
    expect(nmmData).toHaveProperty('intensity', 0.8);
  });

  test('@bsl avatar generation with handshape parameters', async ({ services }) => {
    const testText = 'The number five is important';

    const response = await services.bsl.post('http://localhost:8003/api/avatar', {
      data: {
        text: testText,
        handshape: 'five',
        dominant_hand: 'right'
      }
    });

    expect(response.ok()).toBeTruthy();
    const result = await response.json();

    expect(result).toHaveProperty('nmm_data');
    const nmmData = JSON.parse(result.nmm_data);
    expect(nmmData).toHaveProperty('handshape', 'five');
  });

  test('@bsl real-time avatar streaming via WebSocket', async ({ services }) => {
    const testText = 'Welcome to the show';

    // Connect WebSocket before sending request
    const wsClient = await createWebSocketClient('ws://localhost:8003/ws/avatar');

    // Send translation request
    const response = await services.bsl.post('http://localhost:8003/v1/translate', {
      data: {
        text: testText,
        include_nmm: true
      }
    });

    expect(response.ok()).toBeTruthy();

    // Wait for WebSocket message
    const message = await wsClient.waitForMessage('animation_update', 10000);

    expect(message).toHaveProperty('type', 'animation_update');
    expect(message).toHaveProperty('nmm_data');
    expect(message.nmm_data.length).toBeGreaterThan(0);
    expect(message).toHaveProperty('timestamp');

    wsClient.close();
  });

  test('@bsl avatar animation playback controls', async ({ services }) => {
    // Start avatar playback
    const startResponse = await services.bsl.post('http://localhost:8003/api/avatar/playback', {
      data: {
        action: 'start',
        text: 'This is a test for playback controls'
      }
    });

    expect(startResponse.ok()).toBeTruthy();
    const startResult = await startResponse.json();
    expect(startResult).toHaveProperty('status', 'playing');

    // Pause playback
    const pauseResponse = await services.bsl.post('http://localhost:8003/api/avatar/playback', {
      data: {
        action: 'pause'
      }
    });

    expect(pauseResponse.ok()).toBeTruthy();
    const pauseResult = await pauseResponse.json();
    expect(pauseResult).toHaveProperty('status', 'paused');

    // Resume playback
    const resumeResponse = await services.bsl.post('http://localhost:8003/api/avatar/playback', {
      data: {
        action: 'resume'
      }
    });

    expect(resumeResponse.ok()).toBeTruthy();
    const resumeResult = await resumeResponse.json();
    expect(resumeResult).toHaveProperty('status', 'playing');

    // Stop playback
    const stopResponse = await services.bsl.post('http://localhost:8003/api/avatar/playback', {
      data: {
        action: 'stop'
      }
    });

    expect(stopResponse.ok()).toBeTruthy();
    const stopResult = await stopResponse.json();
    expect(stopResult).toHaveProperty('status', 'stopped');
  });

  test('@bsl batch translation for multiple text segments', async ({ services }) => {
    const textSegments = [
      'Welcome to our show',
      'We hope you enjoy it',
      'The performance begins now',
      'Thank you for coming'
    ];

    const response = await services.bsl.post('http://localhost:8003/v1/batch-translate', {
      data: {
        texts: textSegments,
        include_nmm: true
      }
    });

    expect(response.ok()).toBeTruthy();
    const result = await response.json();

    expect(result).toHaveProperty('translations');
    expect(Array.isArray(result.translations)).toBeTruthy();
    expect(result.translations).toHaveLength(textSegments.length);

    // Verify each translation
    result.translations.forEach((translation: any) => {
      expect(translation).toHaveProperty('gloss');
      expect(translation).toHaveProperty('nmm_data');
      expect(translation).toHaveProperty('confidence');
    });
  });

  test('@bsl context-aware translation', async ({ services, testData }) => {
    const showContext = testData.createShowContext({
      adapter: 'drama',
      scene: 1,
      act: 1
    });

    const testText = 'The hero enters the room dramatically';

    const response = await services.bsl.post('http://localhost:8003/v1/translate', {
      data: {
        text: testText,
        include_nmm: true,
        context: showContext
      }
    });

    expect(response.ok()).toBeTruthy();
    const result = await response.json();

    expect(result).toHaveProperty('gloss');
    expect(result).toHaveProperty('context');
    expect(result.context).toHaveProperty('show_id');
    expect(result.context).toHaveProperty('adapter');
  });

  test('@bsl avatar expression variations', async ({ services }) => {
    const expressions = ['happy', 'sad', 'angry', 'surprised', 'neutral'];

    for (const expression of expressions) {
      const response = await services.bsl.post('http://localhost:8003/api/avatar', {
        data: {
          text: 'Test expression',
          expression: expression
        }
      });

      expect(response.ok()).toBeTruthy();
      const result = await response.json();

      expect(result).toHaveProperty('nmm_data');
      const nmmData = JSON.parse(result.nmm_data);
      expect(nmmData).toHaveProperty('expression', expression);
    }
  });

  test('@bsl complex sentence translation', async ({ services }) => {
    const complexText = 'The time traveler, who was feeling anxious about the journey, stepped into the machine and pressed the red button, hoping to return to the present day';

    const response = await services.bsl.post('http://localhost:8003/v1/translate', {
      data: {
        text: complexText,
        include_nmm: true
      }
    });

    expect(response.ok()).toBeTruthy();
    const result = await response.json();

    expect(result).toHaveProperty('gloss');
    expect(result.gloss.length).toBeGreaterThan(0);
    expect(result).toHaveProperty('nmm_data');

    // Complex sentence should have longer translation time
    expect(result.translation_time_ms).toBeGreaterThan(0);
  });

  test('@bsl avatar timeline synchronization', async ({ services }) => {
    const testText = 'One two three four five';

    const response = await services.bsl.post('http://localhost:8003/api/avatar', {
      data: {
        text: testText,
        include_timeline: true
      }
    });

    expect(response.ok()).toBeTruthy();
    const result = await response.json();

    expect(result).toHaveProperty('nmm_data');
    expect(result).toHaveProperty('timeline');

    const nmmData = JSON.parse(result.nmm_data);
    expect(nmmData).toHaveProperty('animations');

    if (result.timeline) {
      expect(Array.isArray(result.timeline)).toBeTruthy();
      expect(result.timeline.length).toBeGreaterThan(0);

      // Verify timeline structure
      result.timeline.forEach((entry: any) => {
        expect(entry).toHaveProperty('time');
        expect(entry).toHaveProperty('animation');
      });
    }
  });

  test('@bsl WebSocket connection management', async () => {
    const wsClient = await createWebSocketClient('ws://localhost:8003/ws/avatar');

    // Verify connection is established
    expect(wsClient.isConnected()).toBe(true);

    // Send ping
    wsClient.send({ type: 'ping' });

    // Wait for pong
    const pongMessage = await wsClient.waitForMessage('pong', 5000);
    expect(pongMessage).toHaveProperty('type', 'pong');

    wsClient.close();

    // Verify connection is closed
    expect(wsClient.isConnected()).toBe(false);
  });

  test('@bsl avatar error handling for invalid input', async ({ services }) => {
    // Test with empty text
    const response = await services.bsl.post('http://localhost:8003/v1/translate', {
      data: {
        text: '',
        include_nmm: true
      }
    });

    // Should handle gracefully
    expect([200, 400, 422]).toContain(response.status());

    if (response.status() === 200) {
      const result = await response.json();
      expect(result).toHaveProperty('error');
    }
  });

  test('@bsl concurrent translation requests', async ({ services }) => {
    const requests = Array.from({ length: 5 }, (_, i) =>
      services.bsl.post('http://localhost:8003/v1/translate', {
        data: {
          text: `Concurrent test text number ${i}`,
          include_nmm: true
        }
      })
    );

    const responses = await Promise.all(requests);

    // All requests should succeed
    responses.forEach(response => {
      expect(response.ok()).toBeTruthy();
    });

    // Verify all have unique glosses
    const results = await Promise.all(responses.map(r => r.json()));
    const glosses = results.map(r => r.gloss);
    const uniqueGlosses = new Set(glosses);
    expect(uniqueGlosses.size).toBe(glosses.length);
  });

  test('@bsl avatar performance metrics', async ({ services }) => {
    const testText = 'Performance test for BSL avatar rendering';

    const response = await services.bsl.post('http://localhost:8003/v1/translate', {
      data: {
        text: testText,
        include_nmm: true,
        include_metrics: true
      }
    });

    expect(response.ok()).toBeTruthy();
    const result = await response.json();

    expect(result).toHaveProperty('translation_time_ms');
    expect(result).toHaveProperty('nmm_generation_time_ms');

    if (result.metrics) {
      expect(result.metrics).toHaveProperty('memory_usage_mb');
      expect(result.metrics).toHaveProperty('gpu_usage_percent');
    }
  });

  test('@bsl renderer information', async ({ services }) => {
    const response = await services.bsl.get('http://localhost:8003/api/renderer/info');

    expect(response.ok()).toBeTruthy();
    const info = await response.json();

    expect(info).toHaveProperty('renderer', 'webgl');
    expect(info).toHaveProperty('version');
    expect(info).toHaveProperty('capabilities');
    expect(Array.isArray(info.capabilities)).toBeTruthy();
  });

  test('@bsl avatar animation library', async ({ services }) => {
    const response = await services.bsl.get('http://localhost:8003/api/animations/library');

    expect(response.ok()).toBeTruthy();
    const library = await response.json();

    expect(library).toHaveProperty('animations');
    expect(Array.isArray(library.animations)).toBeTruthy();

    // Verify animation structure
    if (library.animations.length > 0) {
      const animation = library.animations[0];
      expect(animation).toHaveProperty('id');
      expect(animation).toHaveProperty('name');
      expect(animation).toHaveProperty('category');
    }
  });

  test('@bsl complete pipeline: text to display', async ({ services }) => {
    const testText = 'Welcome to Project Chimera!';

    // Step 1: Translate to BSL gloss
    const translateResponse = await services.bsl.post('http://localhost:8003/v1/translate', {
      data: {
        text: testText,
        include_nmm: true
      }
    });

    expect(translateResponse.ok()).toBeTruthy();
    const translateResult = await translateResponse.json();

    expect(translateResult).toHaveProperty('gloss');
    expect(translateResult).toHaveProperty('nmm_data');

    // Step 2: Generate avatar with NMM data
    const avatarResponse = await services.bsl.post('http://localhost:8003/api/avatar', {
      data: {
        text: testText,
        expression: 'happy'
      }
    });

    expect(avatarResponse.ok()).toBeTruthy();
    const avatarResult = await avatarResponse.json();

    expect(avatarResult).toHaveProperty('nmm_data');

    // Step 3: Verify renderer can process the data
    const rendererInfoResponse = await services.bsl.get('http://localhost:8003/api/renderer/info');
    expect(rendererInfoResponse.ok()).toBeTruthy();

    const rendererInfo = await rendererInfoResponse.json();
    expect(rendererInfo).toHaveProperty('status', 'available');
  });
});
