/**
 * Safety Filter Integration Tests
 *
 * Tests content moderation across all services and policies:
 * - Family Policy (strict filtering for all ages)
 * - Teen Policy (moderate filtering for 13+)
 * - Adult Policy (minimal filtering for 18+)
 * - Unrestricted Policy (no filtering)
 * - Context-aware moderation
 * - Audit logging
 * - Cross-service content filtering
 *
 * @tags integration, safety, slow
 */

import { test, expect } from './conftest';

test.describe('Safety Filter Integration', () => {
  test.beforeEach(async ({ waitForService }) => {
    const isHealthy = await waitForService('safety');
    if (!isHealthy) {
      test.skip(true, 'Safety filter service is not available');
    }
  });

  test('@safety family policy blocks inappropriate content', async ({ services, testData }) => {
    const inappropriateContent = 'This show is stupid and the actors are terrible';

    const response = await services.safety.post('http://localhost:8006/api/moderate', {
      data: testData.createSafetyCheck(inappropriateContent, 'family')
    });

    expect(response.ok()).toBeTruthy();
    const result = await response.json();

    expect(result).toHaveProperty('safe');
    expect(result).toHaveProperty('result');

    // Content should be flagged
    const isSafe = result.safe ?? result.result?.is_safe ?? true;
    expect(isSafe).toBe(false);

    // Check for flagged categories
    if (result.result) {
      expect(result.result).toHaveProperty('flagged_categories');
      expect(Array.isArray(result.result.flagged_categories)).toBeTruthy();
    }
  });

  test('@safety family policy allows safe content', async ({ services, testData }) => {
    const safeContent = 'Welcome to our wonderful show! We hope you have a great time.';

    const response = await services.safety.post('http://localhost:8006/api/moderate', {
      data: testData.createSafetyCheck(safeContent, 'family')
    });

    expect(response.ok()).toBeTruthy();
    const result = await response.json();

    expect(result).toHaveProperty('safe');
    const isSafe = result.safe ?? result.result?.is_safe ?? false;
    expect(isSafe).toBe(true);
  });

  test('@safety teen policy moderation', async ({ services, testData }) => {
    const mildContent = 'This is really dumb but kind of funny';

    const response = await services.safety.post('http://localhost:8006/api/moderate', {
      data: testData.createSafetyCheck(mildContent, 'teen')
    });

    expect(response.ok()).toBeTruthy();
    const result = await response.json();

    expect(result).toHaveProperty('result');
    expect(result.result).toHaveProperty('policy', 'teen');
    expect(result.result).toHaveProperty('is_safe');
    expect(result.result).toHaveProperty('confidence');
  });

  test('@safety adult policy minimal filtering', async ({ services, testData }) => {
    const adultContent = 'The plot is complex and explores mature themes';

    const response = await services.safety.post('http://localhost:8006/api/moderate', {
      data: testData.createSafetyCheck(adultContent, 'adult')
    });

    expect(response.ok()).toBeTruthy();
    const result = await response.json();

    expect(result).toHaveProperty('result');
    const isSafe = result.result?.is_safe ?? true;
    expect(isSafe).toBe(true);
  });

  test('@safety unrestricted policy allows all content', async ({ services, testData }) => {
    const content = 'Any content should pass unrestricted policy';

    const response = await services.safety.post('http://localhost:8006/api/moderate', {
      data: testData.createSafetyCheck(content, 'unrestricted')
    });

    expect(response.ok()).toBeTruthy();
    const result = await response.json();

    expect(result).toHaveProperty('result');
    expect(result.result.is_safe).toBe(true);
    expect(result.result.policy).toBe('unrestricted');
  });

  test('@safety context-aware moderation', async ({ services, testData }) => {
    const showContext = testData.createShowContext({
      adapter: 'drama',
      scene: 1,
      act: 1
    });

    const content = 'The character expresses frustration with the situation';

    const response = await services.safety.post('http://localhost:8006/api/moderate', {
      data: {
        content,
        content_id: 'test-001',
        user_id: 'test-user',
        policy: 'family',
        context: showContext
      }
    });

    expect(response.ok()).toBeTruthy();
    const result = await response.json();

    expect(result).toHaveProperty('result');
    expect(result.result).toHaveProperty('context');
    expect(result.result.context).toHaveProperty('show_id');
    expect(result.result.context).toHaveProperty('adapter');
  });

  test('@safety audit logging for moderation decisions', async ({ services, testData }) => {
    const content = 'Test content for audit logging';

    const response = await services.safety.post('http://localhost:8006/api/moderate', {
      data: testData.createSafetyCheck(content, 'family')
    });

    expect(response.ok()).toBeTruthy();
    const result = await response.json();

    // Check for audit metadata
    expect(result).toHaveProperty('result');
    expect(result.result).toHaveProperty('timestamp');
    expect(result.result).toHaveProperty('moderation_id');

    // Verify audit log entry exists
    const auditResponse = await services.safety.get(`http://localhost:8006/api/audit/${result.result.moderation_id}`);
    expect(auditResponse.ok()).toBeTruthy();

    const auditLog = await auditResponse.json();
    expect(auditLog).toHaveProperty('content_id');
    expect(auditLog).toHaveProperty('decision');
  });

  test('@safety batch moderation for multiple content items', async ({ services }) => {
    const contentItems = [
      'Safe content for everyone',
      'This is really bad and terrible',
      'Another safe message',
      'Yet another wonderful performance'
    ];

    const response = await services.safety.post('http://localhost:8006/api/batch-moderate', {
      data: {
        items: contentItems.map((content, index) => ({
          content,
          content_id: `batch-test-${index}`,
          policy: 'family'
        }))
      }
    });

    expect(response.ok()).toBeTruthy();
    const result = await response.json();

    expect(result).toHaveProperty('results');
    expect(Array.isArray(result.results)).toBeTruthy();
    expect(result.results).toHaveLength(contentItems.length);

    // Verify each result
    result.results.forEach((itemResult: any) => {
      expect(itemResult).toHaveProperty('content_id');
      expect(itemResult).toHaveProperty('is_safe');
      expect(itemResult).toHaveProperty('confidence');
    });
  });

  test('@safety dialogue generation content filtering', async ({ services, testData }) => {
    // Generate dialogue that might include edge cases
    const dialogueResponse = await services.scenespeak.post('http://localhost:8001/api/generate', {
      data: {
        prompt: 'Generate a dramatic line about conflict',
        max_tokens: 30,
        temperature: 0.7
      }
    });

    expect(dialogueResponse.ok()).toBeTruthy();
    const dialogueData = await dialogueResponse.json();
    const dialogueText = dialogueData.text || dialogueData.dialogue || '';

    // Check the generated dialogue for safety
    const safetyResponse = await services.safety.post('http://localhost:8006/api/moderate', {
      data: {
        content: dialogueText,
        content_id: 'dialogue-test',
        policy: 'family'
      }
    });

    expect(safetyResponse.ok()).toBeTruthy();
    const safetyResult = await safetyResponse.json();

    expect(safetyResult).toHaveProperty('result');
    expect(safetyResult.result).toHaveProperty('is_safe');
  });

  test('@safety audience input moderation', async ({ services, testData }) => {
    const testInputs = [
      { text: 'Great show!', expected: true },
      { text: 'This is stupid and awful', expected: false },
      { text: 'I love it!', expected: true },
      { text: 'Terrible performance', expected: false }
    ];

    for (const input of testInputs) {
      const response = await services.safety.post('http://localhost:8006/api/moderate', {
        data: {
          content: input.text,
          content_id: `audience-test-${input.text.substring(0, 10)}`,
          policy: 'family'
        }
      });

      expect(response.ok()).toBeTruthy();
      const result = await response.json();

      const isSafe = result.safe ?? result.result?.is_safe ?? true;
      if (input.expected === false) {
        expect(isSafe).toBe(false);
      }
    }
  });

  test('@safety BSL translation content safety', async ({ services, testData }) => {
    const dialogueText = 'Welcome to our amazing performance today!';

    // First translate to BSL
    const bslResponse = await services.bsl.post('http://localhost:8003/v1/translate', {
      data: {
        text: dialogueText,
        include_nmm: false
      }
    });

    expect(bslResponse.ok()).toBeTruthy();
    const bslData = await bslResponse.json();

    // Check the original text for safety
    const safetyResponse = await services.safety.post('http://localhost:8006/api/moderate', {
      data: {
        content: dialogueText,
        content_id: 'bsl-safety-test',
        policy: 'family'
      }
    });

    expect(safetyResponse.ok()).toBeTruthy();
    const safetyResult = await safetyResponse.json();
    const isSafe = safetyResult.safe ?? safetyResult.result?.is_safe ?? false;
    expect(isSafe).toBe(true);
  });

  test('@safety cross-service content filtering', async ({ services, testData }) => {
    const showContext = testData.createShowContext();

    // Step 1: Generate dialogue
    const dialogueResponse = await services.scenespeak.post('http://localhost:8001/api/generate', {
      data: {
        prompt: 'Generate a line for the show',
        max_tokens: 40,
        context: showContext
      }
    });

    expect(dialogueResponse.ok()).toBeTruthy();
    const dialogueData = await dialogueResponse.json();
    const dialogueText = dialogueData.text || dialogueData.dialogue || '';

    // Step 2: Check safety before BSL translation
    const safetyResponse = await services.safety.post('http://localhost:8006/api/moderate', {
      data: {
        content: dialogueText,
        content_id: `cross-service-${showContext.show_id}`,
        policy: 'family',
        context: showContext
      }
    });

    expect(safetyResponse.ok()).toBeTruthy();
    const safetyResult = await safetyResponse.json();

    expect(safetyResult).toHaveProperty('result');
    expect(safetyResult.result).toHaveProperty('is_safe');

    // Only proceed to BSL if content is safe
    const isSafe = safetyResult.result.is_safe;
    if (isSafe) {
      const bslResponse = await services.bsl.post('http://localhost:8003/v1/translate', {
        data: {
          text: dialogueText,
          context: showContext
        }
      });

      expect(bslResponse.ok()).toBeTruthy();
    }
  });

  test('@safety custom policy configuration', async ({ services }) => {
    const customPolicy = {
      name: 'custom-test-policy',
      blocked_words: ['testword'],
      allowed_categories: ['general'],
      strictness: 0.7
    };

    const response = await services.safety.post('http://localhost:8006/api/policy/custom', {
      data: {
        policy: customPolicy,
        content: 'This is a test message with testword included'
      }
    });

    expect(response.ok()).toBeTruthy();
    const result = await response.json();

    expect(result).toHaveProperty('result');
    expect(result.result).toHaveProperty('policy_name', 'custom-test-policy');
  });

  test('@safety moderation statistics and metrics', async ({ services }) => {
    const response = await services.safety.get('http://localhost:8006/api/metrics');

    expect(response.ok()).toBeTruthy();
    const metrics = await response.json();

    expect(metrics).toHaveProperty('total_moderations');
    expect(metrics).toHaveProperty('flagged_count');
    expect(metrics).toHaveProperty('safe_count');
    expect(metrics).toHaveProperty('policy_breakdown');
  });

  test('@safety real-time moderation stream', async ({ websockets }) => {
    // Connect to moderation stream
    const wsClient = websockets.console;

    // Send content for moderation
    const testContent = 'Real-time moderation test content';

    // Wait for moderation update
    const message = await wsClient.waitForMessage('moderation_update', 10000);

    expect(message).toHaveProperty('type', 'moderation_update');
    expect(message).toHaveProperty('content_id');
    expect(message).toHaveProperty('is_safe');
  });

  test('@safety error handling for invalid requests', async ({ services }) => {
    // Test with empty content
    const response = await services.safety.post('http://localhost:8006/api/moderate', {
      data: {
        content: '',
        content_id: 'test-empty',
        policy: 'family'
      }
    });

    // Should handle gracefully
    expect([200, 400, 422]).toContain(response.status());

    if (response.status() === 200) {
      const result = await response.json();
      expect(result).toHaveProperty('result');
    }
  });

  test('@safety concurrent moderation requests', async ({ services }) => {
    const requests = Array.from({ length: 10 }, (_, i) =>
      services.safety.post('http://localhost:8006/api/moderate', {
        data: {
          content: `Concurrent test content ${i}`,
          content_id: `concurrent-${i}`,
          policy: 'family'
        }
      })
    );

    const responses = await Promise.all(requests);

    // All requests should succeed
    responses.forEach(response => {
      expect(response.ok()).toBeTruthy();
    });

    // Verify all have unique moderation IDs
    const results = await Promise.all(
      responses.map(r => r.json())
    );

    const moderationIds = results.map(r => r.result?.moderation_id).filter(Boolean);
    const uniqueIds = new Set(moderationIds);
    expect(uniqueIds.size).toBe(moderationIds.length);
  });
});
