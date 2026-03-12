/**
 * Latency Performance Tests
 * Project Chimera v0.5.0
 *
 * Tests that verify p95 latency requirements from TRD:
 * - SceneSpeak: <2s
 * - BSL: <1s
 * - Captioning: <500ms
 * - Sentiment: <200ms
 * - End-to-end: <5s
 *
 * These tests measure actual API response times and validate
 * that they meet the performance requirements defined in the TRD.
 */

import { test, expect } from '@playwright/test';
import { ChimeraTestHelper } from '../../e2e/helpers/test-utils';

// TRD latency requirements (p95, in milliseconds)
const TRD_REQUIREMENTS = {
  scenespeak: 2000,
  bsl: 1000,
  captioning: 500,
  sentiment: 200,
  end_to_end: 5000,
};

// Helper function to calculate p95 latency
function calculateP95(latencies: number[]): number {
  const sorted = latencies.sort((a, b) => a - b);
  const index = Math.floor(sorted.length * 0.95);
  return sorted[index] || 0;
}

// Helper function to calculate p99 latency
function calculateP99(latencies: number[]): number {
  const sorted = latencies.sort((a, b) => a - b);
  const index = Math.floor(sorted.length * 0.99);
  return sorted[index] || 0;
}

// Helper function to calculate average latency
function calculateAverage(latencies: number[]): number {
  return latencies.reduce((a, b) => a + b, 0) / latencies.length;
}

test.describe('Latency Performance Tests', () => {
  let helper: ChimeraTestHelper;
  let page: any;
  let request: any;

  test.beforeAll(async ({ playwright }) => {
    // Initialize test helper
    const browser = await playwright.chromium.launch();
    page = await browser.newPage();
    const context = page.request;
    helper = new ChimeraTestHelper(page, context);
  });

  test.describe('SceneSpeak Agent', () => {
    const service = 'scenespeak-agent';
    const port = 8001;
    const latencies: number[] = [];
    const iterations = 20; // Number of samples to collect

    test.beforeAll(async () => {
      // Wait for service to be ready
      await helper.waitForService(service, port);
    });

    test(`collect ${iterations} latency samples`, async () => {
      for (let i = 0; i < iterations; i++) {
        const startTime = Date.now();

        try {
          const response = await helper.page.request.post(
            `http://localhost:${port}/api/generate`,
            {
              timeout: 10000,
              json: {
                prompt: 'Test prompt for latency measurement',
                context: { show_id: 'latency-test' },
              },
            }
          );

          const endTime = Date.now();
          const latency = endTime - startTime;

          expect(response.ok()).toBeTruthy();
          latencies.push(latency);
        } catch (error) {
          console.error(`Request ${i + 1} failed:`, error);
        }
      }
    });

    test('validate p95 latency < 2s', () => {
      const p95 = calculateP95(latencies);
      const requirement = TRD_REQUIREMENTS.scenespeak;
      const avg = calculateAverage(latencies);
      const p99 = calculateP99(latencies);

      console.log(`SceneSpeak Latency Statistics:`);
      console.log(`  Average: ${avg.toFixed(2)}ms`);
      console.log(`  p95: ${p95.toFixed(2)}ms`);
      console.log(`  p99: ${p99.toFixed(2)}ms`);
      console.log(`  Min: ${Math.min(...latencies).toFixed(2)}ms`);
      console.log(`  Max: ${Math.max(...latencies).toFixed(2)}ms`);

      expect(p95).toBeLessThan(requirement);
      expect(latencies.length).toBeGreaterThanOrEqual(iterations * 0.9); // At least 90% success rate
    });
  });

  test.describe('BSL Agent', () => {
    const service = 'bsl-agent';
    const port = 8003;
    const latencies: number[] = [];
    const iterations = 20;

    test.beforeAll(async () => {
      await helper.waitForService(service, port);
    });

    test(`collect ${iterations} latency samples`, async () => {
      for (let i = 0; i < iterations; i++) {
        const startTime = Date.now();

        try {
          const response = await helper.page.request.post(
            `http://localhost:${port}/api/translate`,
            {
              timeout: 10000,
              json: {
                text: 'Hello, how are you?',
              },
            }
          );

          const endTime = Date.now();
          const latency = endTime - startTime;

          expect(response.ok()).toBeTruthy();
          latencies.push(latency);
        } catch (error) {
          console.error(`Request ${i + 1} failed:`, error);
        }
      }
    });

    test('validate p95 latency < 1s', () => {
      const p95 = calculateP95(latencies);
      const requirement = TRD_REQUIREMENTS.bsl;
      const avg = calculateAverage(latencies);
      const p99 = calculateP99(latencies);

      console.log(`BSL Agent Latency Statistics:`);
      console.log(`  Average: ${avg.toFixed(2)}ms`);
      console.log(`  p95: ${p95.toFixed(2)}ms`);
      console.log(`  p99: ${p99.toFixed(2)}ms`);
      console.log(`  Min: ${Math.min(...latencies).toFixed(2)}ms`);
      console.log(`  Max: ${Math.max(...latencies).toFixed(2)}ms`);

      expect(p95).toBeLessThan(requirement);
      expect(latencies.length).toBeGreaterThanOrEqual(iterations * 0.9);
    });
  });

  test.describe('Captioning Agent', () => {
    const service = 'captioning-agent';
    const port = 8002;
    const latencies: number[] = [];
    const iterations = 20;

    test.beforeAll(async () => {
      await helper.waitForService(service, port);
    });

    test(`collect ${iterations} latency samples`, async () => {
      for (let i = 0; i < iterations; i++) {
        const startTime = Date.now();

        try {
          const response = await helper.page.request.post(
            `http://localhost:${port}/v1/transcribe`,
            {
              timeout: 10000,
              json: {
                audio_data: 'base64-encoded-audio-data-placeholder',
                format: 'wav',
              },
            }
          );

          const endTime = Date.now();
          const latency = endTime - startTime;

          expect(response.ok()).toBeTruthy();
          latencies.push(latency);
        } catch (error) {
          console.error(`Request ${i + 1} failed:`, error);
        }
      }
    });

    test('validate p95 latency < 500ms', () => {
      const p95 = calculateP95(latencies);
      const requirement = TRD_REQUIREMENTS.captioning;
      const avg = calculateAverage(latencies);
      const p99 = calculateP99(latencies);

      console.log(`Captioning Agent Latency Statistics:`);
      console.log(`  Average: ${avg.toFixed(2)}ms`);
      console.log(`  p95: ${p95.toFixed(2)}ms`);
      console.log(`  p99: ${p99.toFixed(2)}ms`);
      console.log(`  Min: ${Math.min(...latencies).toFixed(2)}ms`);
      console.log(`  Max: ${Math.max(...latencies).toFixed(2)}ms`);

      expect(p95).toBeLessThan(requirement);
      expect(latencies.length).toBeGreaterThanOrEqual(iterations * 0.9);
    });
  });

  test.describe('Sentiment Agent', () => {
    const service = 'sentiment-agent';
    const port = 8004;
    const latencies: number[] = [];
    const iterations = 50; // More iterations for fast service

    test.beforeAll(async () => {
      await helper.waitForService(service, port);
    });

    test(`collect ${iterations} latency samples`, async () => {
      for (let i = 0; i < iterations; i++) {
        const startTime = Date.now();

        try {
          const response = await helper.page.request.post(
            `http://localhost:${port}/api/analyze`,
            {
              timeout: 5000,
              json: {
                text: 'This is a great show!',
              },
            }
          );

          const endTime = Date.now();
          const latency = endTime - startTime;

          expect(response.ok()).toBeTruthy();
          latencies.push(latency);
        } catch (error) {
          console.error(`Request ${i + 1} failed:`, error);
        }
      }
    });

    test('validate p95 latency < 200ms', () => {
      const p95 = calculateP95(latencies);
      const requirement = TRD_REQUIREMENTS.sentiment;
      const avg = calculateAverage(latencies);
      const p99 = calculateP99(latencies);

      console.log(`Sentiment Agent Latency Statistics:`);
      console.log(`  Average: ${avg.toFixed(2)}ms`);
      console.log(`  p95: ${p95.toFixed(2)}ms`);
      console.log(`  p99: ${p99.toFixed(2)}ms`);
      console.log(`  Min: ${Math.min(...latencies).toFixed(2)}ms`);
      console.log(`  Max: ${Math.max(...latencies).toFixed(2)}ms`);

      expect(p95).toBeLessThan(requirement);
      expect(latencies.length).toBeGreaterThanOrEqual(iterations * 0.9);
    });
  });

  test.describe('End-to-End Workflow', () => {
    const latencies: number[] = [];
    const iterations = 10; // Fewer iterations for complex workflow

    test.beforeAll(async () => {
      // Ensure all services are ready
      await helper.waitForService('openclaw-orchestrator', 8000);
      await helper.waitForService('scenespeak-agent', 8001);
      await helper.waitForService('bsl-agent', 8003);
    });

    test(`collect ${iterations} end-to-end latency samples`, async () => {
      for (let i = 0; i < iterations; i++) {
        const startTime = Date.now();

        try {
          // Step 1: Generate dialogue
          const dialogueResponse = await helper.page.request.post(
            'http://localhost:8001/api/generate',
            {
              timeout: 10000,
              json: {
                prompt: 'Welcome to the show',
                context: { show_id: `e2e-test-${i}` },
              },
            }
          );

          expect(dialogueResponse.ok()).toBeTruthy();
          const dialogueData = await dialogueResponse.json();
          const dialogue = dialogueData.dialogue;

          // Step 2: Translate to BSL
          const bslResponse = await helper.page.request.post(
            'http://localhost:8003/api/translate',
            {
              timeout: 10000,
              json: {
                text: dialogue,
              },
            }
          );

          expect(bslResponse.ok()).toBeTruthy();

          // Step 3: Generate avatar animation
          const avatarResponse = await helper.page.request.post(
            'http://localhost:8003/api/avatar/generate',
            {
              timeout: 10000,
              json: {
                text: dialogue,
                expression: 'neutral',
              },
            }
          );

          expect(avatarResponse.ok()).toBeTruthy();

          const endTime = Date.now();
          const latency = endTime - startTime;
          latencies.push(latency);

        } catch (error) {
          console.error(`End-to-end workflow ${i + 1} failed:`, error);
        }
      }
    });

    test('validate p95 end-to-end latency < 5s', () => {
      const p95 = calculateP95(latencies);
      const requirement = TRD_REQUIREMENTS.end_to_end;
      const avg = calculateAverage(latencies);
      const p99 = calculateP99(latencies);

      console.log(`End-to-End Latency Statistics:`);
      console.log(`  Average: ${avg.toFixed(2)}ms`);
      console.log(`  p95: ${p95.toFixed(2)}ms`);
      console.log(`  p99: ${p99.toFixed(2)}ms`);
      console.log(`  Min: ${Math.min(...latencies).toFixed(2)}ms`);
      console.log(`  Max: ${Math.max(...latencies).toFixed(2)}ms`);

      expect(p95).toBeLessThan(requirement);
      expect(latencies.length).toBeGreaterThanOrEqual(iterations * 0.8);
    });
  });

  test.describe('Performance Summary', () => {
    test('generate performance report', async () => {
      const summary: Record<string, any> = {
        timestamp: new Date().toISOString(),
        requirements: TRD_REQUIREMENTS,
        services: {},
      };

      // Collect health information from all services
      const services = [
        { name: 'scenespeak-agent', port: 8001 },
        { name: 'bsl-agent', port: 8003 },
        { name: 'captioning-agent', port: 8002 },
        { name: 'sentiment-agent', port: 8004 },
        { name: 'safety-filter', port: 8006 },
      ];

      for (const service of services) {
        try {
          const response = await helper.page.request.get(
            `http://localhost:${service.port}/health`
          );

          if (response.ok()) {
            const health = await response.json();
            summary.services[service.name] = {
              status: 'healthy',
              health,
            };
          }
        } catch (error) {
          summary.services[service.name] = {
            status: 'unhealthy',
            error: String(error),
          };
        }
      }

      console.log('\n=== Performance Test Summary ===');
      console.log(JSON.stringify(summary, null, 2));
      console.log('================================\n');

      // Write summary to file
      const fs = require('fs');
      const path = require('path');
      const reportPath = path.join(
        __dirname,
        `../../test-results/performance-summary-${Date.now()}.json`
      );

      fs.mkdirSync(path.dirname(reportPath), { recursive: true });
      fs.writeFileSync(reportPath, JSON.stringify(summary, null, 2));

      console.log(`Performance report saved to: ${reportPath}`);
    });
  });
});
