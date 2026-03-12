/**
 * Concurrent Users Load Test
 * Project Chimera v0.5.0
 *
 * k6 load test script for testing system performance under load.
 * Tests 50 concurrent users with realistic usage patterns.
 *
 * Run with:
 *   k6 run --vus 50 --duration 5m tests/performance/load/concurrent-users.js
 *
 * Or with custom parameters:
 *   k6 run --vus 100 --duration 10m tests/performance/load/concurrent-users.js
 *
 * Requirements:
 * - k6 installed: https://k6.io/docs/getting-started/installation/
 * - Services running on localhost (ports 8000-8011)
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics for TRD requirements
const sceneSpeakLatency = new Trend('scenespeak_latency_ms');
const bslLatency = new Trend('bsl_latency_ms');
const captioningLatency = new Trend('captioning_latency_ms');
const sentimentLatency = new Trend('sentiment_latency_ms');
const endToEndLatency = new Trend('end_to_end_latency_ms');

const errorRate = new Rate('errors');
const successCount = new Counter('successful_requests');

// Test configuration
export const options = {
  // Number of virtual users
  vus: 50,

  // Test duration
  duration: '5m',

  // Thresholds based on TRD requirements
  thresholds: {
    // SceneSpeak: p95 < 2s
    'scenespeak_latency_ms': ['p(95)<2000'],

    // BSL: p95 < 1s
    'bsl_latency_ms': ['p(95)<1000'],

    // Captioning: p95 < 500ms
    'captioning_latency_ms': ['p(95)<500'],

    // Sentiment: p95 < 200ms
    'sentiment_latency_ms': ['p(95)<200'],

    // End-to-end: p95 < 5s
    'end_to_end_latency_ms': ['p(95)<5000'],

    // Error rate should be below 5%
    'errors': ['rate<0.05'],

    // 95% of requests should succeed
    'http_req_failed': ['rate<0.05'],
  },

  // Stages for ramp-up and ramp-down
  stages: [
    { duration: '30s', target: 10 },   // Ramp up to 10 users
    { duration: '1m', target: 25 },     // Ramp up to 25 users
    { duration: '2m', target: 50 },     // Ramp up to 50 users
    { duration: '1m', target: 50 },     // Stay at 50 users
    { duration: '30s', target: 0 },     // Ramp down to 0
  ],
};

// Base URLs for services
const BASE_URLS = {
  orchestrator: 'http://localhost:8000',
  scenespeak: 'http://localhost:8001',
  captioning: 'http://localhost:8002',
  bsl: 'http://localhost:8003',
  sentiment: 'http://localhost:8004',
  lighting: 'http://localhost:8005',
  safety: 'http://localhost:8006',
  console: 'http://localhost:8007',
  music: 'http://localhost:8011',
};

// Test data
const testPrompts = [
  'Welcome to our show tonight',
  'The hero enters the dark forest',
  'Suddenly, a dragon appears',
  'What secrets lie ahead?',
  'The adventure begins now',
];

const testTexts = [
  'Hello and welcome',
  'How are you today?',
  'This is an amazing show',
  'Thank you for being here',
  'We hope you enjoy',
];

// Random utility
function randomChoice(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

// Helper function to measure request latency
function measureRequest(url, method, body, metric) {
  const startTime = Date.now();
  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
    timeout: '10s',
  };

  let response;
  if (method === 'POST') {
    response = http.post(url, JSON.stringify(body), params);
  } else {
    response = http.get(url, params);
  }

  const latency = Date.now() - startTime;

  // Add to custom metric
  if (metric) {
    metric.add(latency);
  }

  return response;
}

// Main test function
export default function () {
  const scenario = Math.random();

  // Distribute load across different scenarios
  if (scenario < 0.3) {
    // 30%: SceneSpeak dialogue generation
    testSceneSpeak();
  } else if (scenario < 0.5) {
    // 20%: BSL translation
    testBSL();
  } else if (scenario < 0.65) {
    // 15%: Sentiment analysis
    testSentiment();
  } else if (scenario < 0.8) {
    // 15%: Captioning (simplified test)
    testCaptioning();
  } else {
    // 20%: End-to-end workflow
    testEndToEnd();
  }

  // Think time between requests (1-3 seconds)
  sleep(Math.random() * 2 + 1);
}

// Test SceneSpeak Agent
function testSceneSpeak() {
  const response = measureRequest(
    `${BASE_URLS.scenespeak}/api/generate`,
    'POST',
    {
      prompt: randomChoice(testPrompts),
      context: { show_id: `load-test-${__VU}` },
    },
    sceneSpeakLatency
  );

  const success = check(response, {
    'SceneSpeak status is 200': (r) => r.status === 200,
    'SceneSpeak has dialogue': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.dialogue && body.dialogue.length > 0;
      } catch {
        return false;
      }
    },
  });

  errorRate.add(!success);
  if (success) {
    successCount.add(1);
  }
}

// Test BSL Agent
function testBSL() {
  const response = measureRequest(
    `${BASE_URLS.bsl}/api/translate`,
    'POST',
    {
      text: randomChoice(testTexts),
    },
    bslLatency
  );

  const success = check(response, {
    'BSL status is 200': (r) => r.status === 200,
    'BSL has gloss': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.gloss && body.gloss.length > 0;
      } catch {
        return false;
      }
    },
  });

  errorRate.add(!success);
  if (success) {
    successCount.add(1);
  }
}

// Test Sentiment Agent
function testSentiment() {
  const response = measureRequest(
    `${BASE_URLS.sentiment}/api/analyze`,
    'POST',
    {
      text: randomChoice([
        'This is amazing!',
        'I really love this show',
        'What a wonderful performance',
        'Best experience ever',
        'Absolutely fantastic',
      ]),
    },
    sentimentLatency
  );

  const success = check(response, {
    'Sentiment status is 200': (r) => r.status === 200,
    'Sentiment has label': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.sentiment && body.sentiment.length > 0;
      } catch {
        return false;
      }
    },
  });

  errorRate.add(!success);
  if (success) {
    successCount.add(1);
  }
}

// Test Captioning Agent
function testCaptioning() {
  const response = measureRequest(
    `${BASE_URLS.captioning}/v1/transcribe`,
    'POST',
    {
      audio_data: 'base64-encoded-placeholder-for-load-testing',
      format: 'wav',
    },
    captioningLatency
  );

  const success = check(response, {
    'Captioning status is 200 or 400': (r) => r.status === 200 || r.status === 400, // 400 for invalid audio
  });

  errorRate.add(!success);
  if (success) {
    successCount.add(1);
  }
}

// Test End-to-End Workflow
function testEndToEnd() {
  const startTime = Date.now();

  // Step 1: Generate dialogue
  const dialogueResponse = http.post(
    `${BASE_URLS.scenespeak}/api/generate`,
    JSON.stringify({
      prompt: randomChoice(testPrompts),
      context: { show_id: `e2e-load-test-${__VU}` },
    }),
    {
      headers: { 'Content-Type': 'application/json' },
      timeout: '10s',
    }
  );

  if (dialogueResponse.status !== 200) {
    errorRate.add(1);
    return;
  }

  const dialogueData = JSON.parse(dialogueResponse.body);
  const dialogue = dialogueData.dialogue;

  // Step 2: Translate to BSL
  const bslResponse = http.post(
    `${BASE_URLS.bsl}/api/translate`,
    JSON.stringify({ text: dialogue }),
    {
      headers: { 'Content-Type': 'application/json' },
      timeout: '10s',
    }
  );

  if (bslResponse.status !== 200) {
    errorRate.add(1);
    return;
  }

  // Step 3: Generate avatar animation
  const avatarResponse = http.post(
    `${BASE_URLS.bsl}/api/avatar/generate`,
    JSON.stringify({
      text: dialogue,
      expression: 'neutral',
    }),
    {
      headers: { 'Content-Type': 'application/json' },
      timeout: '10s',
    }
  );

  if (avatarResponse.status !== 200) {
    errorRate.add(1);
    return;
  }

  const endTime = Date.now();
  const totalLatency = endTime - startTime;
  endToEndLatency.add(totalLatency);

  const success = check(avatarResponse, {
    'End-to-end completed': (r) => r.status === 200,
  });

  errorRate.add(!success);
  if (success) {
    successCount.add(1);
  }
}

// Setup function - runs once before the test
export function setup() {
  console.log('Starting load test with 50 concurrent users');
  console.log('TRD Requirements:');
  console.log('  SceneSpeak: p95 < 2s');
  console.log('  BSL: p95 < 1s');
  console.log('  Captioning: p95 < 500ms');
  console.log('  Sentiment: p95 < 200ms');
  console.log('  End-to-end: p95 < 5s');

  // Check if services are available
  const healthCheck = http.get(`${BASE_URLS.scenespeak}/health`);
  if (healthCheck.status !== 200) {
    console.warn('Warning: SceneSpeak service may not be available');
  }

  return { startTime: new Date().toISOString() };
}

// Teardown function - runs once after the test
export function teardown(data) {
  console.log('\nLoad test completed');
  console.log(`Start time: ${data.startTime}`);
  console.log(`End time: ${new Date().toISOString()}`);
  console.log(`Successful requests: ${successCount.count}`);
  console.log(`Error rate: ${(errorRate.value * 100).toFixed(2)}%`);
  console.log('\nLatency Summary:');
  console.log(`  SceneSpeak p95: ${sceneSpeakLatency.p(95).toFixed(2)}ms`);
  console.log(`  BSL p95: ${bslLatency.p(95).toFixed(2)}ms`);
  console.log(`  Captioning p95: ${captioningLatency.p(95).toFixed(2)}ms`);
  console.log(`  Sentiment p95: ${sentimentLatency.p(95).toFixed(2)}ms`);
  console.log(`  End-to-end p95: ${endToEndLatency.p(95).toFixed(2)}ms`);
}
