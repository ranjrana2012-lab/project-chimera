/**
 * Integration Test Configuration and Fixtures
 *
 * This module provides test fixtures for integration testing across all services.
 * Fixtures handle service discovery, HTTP clients, WebSocket connections, and test data.
 *
 * @module Integration Tests
 */

import { test as base } from '@playwright/test';
import { ChimeraTestHelper } from '../e2e/helpers/test-utils';
import { createWebSocketClient, WebSocketClient } from '../e2e/helpers/websocket-client';
import { APIRequestContext, APIResponse } from '@playwright/test';

/**
 * Service configuration mapping
 */
interface ServiceConfig {
  name: string;
  port: number;
  baseURL: string;
  wsURL: string;
  healthEndpoint: string;
}

/**
 * Service URLs configuration
 */
const SERVICES: Record<string, ServiceConfig> = {
  orchestrator: {
    name: 'openclaw-orchestrator',
    port: 8000,
    baseURL: 'http://localhost:8000',
    wsURL: 'ws://localhost:8000/ws',
    healthEndpoint: '/health/live'
  },
  scenespeak: {
    name: 'scenespeak-agent',
    port: 8001,
    baseURL: 'http://localhost:8001',
    wsURL: 'ws://localhost:8001/ws',
    healthEndpoint: '/health/live'
  },
  captioning: {
    name: 'captioning-agent',
    port: 8002,
    baseURL: 'http://localhost:8002',
    wsURL: 'ws://localhost:8002/v1/stream',
    healthEndpoint: '/health/live'
  },
  bsl: {
    name: 'bsl-agent',
    port: 8003,
    baseURL: 'http://localhost:8003',
    wsURL: 'ws://localhost:8003/ws/avatar',
    healthEndpoint: '/health/live'
  },
  sentiment: {
    name: 'sentiment-agent',
    port: 8004,
    baseURL: 'http://localhost:8004',
    wsURL: 'ws://localhost:8004/ws',
    healthEndpoint: '/health/live'
  },
  lighting: {
    name: 'lighting-sound-music',
    port: 8005,
    baseURL: 'http://localhost:8005',
    wsURL: 'ws://localhost:8005/ws',
    healthEndpoint: '/health/live'
  },
  safety: {
    name: 'safety-filter',
    port: 8006,
    baseURL: 'http://localhost:8006',
    wsURL: 'ws://localhost:8006/ws',
    healthEndpoint: '/health/live'
  },
  console: {
    name: 'operator-console',
    port: 8007,
    baseURL: 'http://localhost:8007',
    wsURL: 'ws://localhost:8007/ws',
    healthEndpoint: '/health/live'
  },
  music: {
    name: 'music-generation',
    port: 8011,
    baseURL: 'http://localhost:8011',
    wsURL: 'ws://localhost:8011/ws',
    healthEndpoint: '/health/live'
  }
};

/**
 * Test data factories
 */
export class TestDataFactory {
  /**
   * Create test dialogue prompt
   */
  static createDialoguePrompt(overrides?: Partial<DialoguePrompt>): DialoguePrompt {
    return {
      prompt: 'Generate a welcoming line for the audience',
      max_tokens: 50,
      temperature: 0.7,
      context: {
        show_id: 'test-show-001',
        scene_number: 1,
        adapter: 'drama'
      },
      ...overrides
    };
  }

  /**
   * Create test show context
   */
  static createShowContext(overrides?: Partial<ShowContext>): ShowContext {
    return {
      show_id: 'test-show-001',
      title: 'The Time Traveler\'s Dilemma',
      scene: 1,
      act: 1,
      adapter: 'drama',
      audience_size: 150,
      venue: 'Test Theater',
      ...overrides
    };
  }

  /**
   * Create test audience reaction
   */
  static createAudienceReaction(overrides?: Partial<AudienceReaction>): AudienceReaction {
    return {
      text: 'This is amazing! I love it!',
      user_id: 'test-user-001',
      timestamp: Date.now(),
      sentiment: 'positive',
      ...overrides
    };
  }

  /**
   * Create test text for BSL translation
   */
  static createBSLText(overrides?: Partial<BSLTranslationRequest>): BSLTranslationRequest {
    return {
      text: 'The time traveler stepped into the machine, ready for adventure.',
      include_nmm: true,
      context: this.createShowContext(),
      ...overrides
    };
  }

  /**
   * Create safety check request
   */
  static createSafetyCheck(content: string, policy: SafetyPolicy = 'family'): SafetyCheckRequest {
    return {
      content,
      content_id: `test-${Date.now()}`,
      user_id: 'test-user',
      policy,
      context: this.createShowContext()
    };
  }

  /**
   * Create sentiment analysis request
   */
  static createSentimentRequest(text: string): SentimentRequest {
    return {
      text,
      include_details: true
    };
  }

  /**
   * Create batch sentiment request
   */
  static createBatchSentimentRequest(texts: string[]): BatchSentimentRequest {
    return {
      texts,
      aggregate: true
    };
  }

  /**
   * Create lighting control request
   */
  static createLightingRequest(overrides?: Partial<LightingRequest>): LightingRequest {
    return {
      action: 'set',
      parameters: {
        intensity: 75,
        color: '#FF6B6B',
        transition_time: 1000
      },
      ...overrides
    };
  }

  /**
   * Create show control request
   */
  static createShowControl(action: ShowControlAction): ShowControlRequest {
    return {
      action,
      timestamp: Date.now(),
      user_id: 'test-operator'
    };
  }
}

/**
 * Type definitions for test data
 */
interface DialoguePrompt {
  prompt: string;
  max_tokens: number;
  temperature: number;
  context: ShowContext;
}

interface ShowContext {
  show_id: string;
  title: string;
  scene: number;
  act: number;
  adapter: string;
  audience_size: number;
  venue: string;
}

interface AudienceReaction {
  text: string;
  user_id: string;
  timestamp: number;
  sentiment: string;
}

interface BSLTranslationRequest {
  text: string;
  include_nmm: boolean;
  context: ShowContext;
}

interface SafetyCheckRequest {
  content: string;
  content_id: string;
  user_id: string;
  policy: SafetyPolicy;
  context: ShowContext;
}

type SafetyPolicy = 'family' | 'teen' | 'adult' | 'unrestricted';

interface SentimentRequest {
  text: string;
  include_details?: boolean;
}

interface BatchSentimentRequest {
  texts: string[];
  aggregate?: boolean;
}

interface LightingRequest {
  action: string;
  parameters: {
    intensity?: number;
    color?: string;
    transition_time?: number;
  };
}

type ShowControlAction = 'start_show' | 'end_show' | 'pause_show' | 'resume_show' | 'next_scene';

interface ShowControlRequest {
  action: ShowControlAction;
  timestamp: number;
  user_id: string;
}

/**
 * Service client fixtures
 */
interface ServiceClients {
  orchestrator: APIRequestContext;
  scenespeak: APIRequestContext;
  captioning: APIRequestContext;
  bsl: APIRequestContext;
  sentiment: APIRequestContext;
  lighting: APIRequestContext;
  safety: APIRequestContext;
  console: APIRequestContext;
  music: APIRequestContext;
}

interface WebSocketClients {
  console: WebSocketClient;
  bsl: WebSocketClient;
  captioning: WebSocketClient;
  sentiment: WebSocketClient;
}

/**
 * Extended test fixtures
 */
export const test = base.extend<{
  testData: TestDataFactory;
  services: ServiceClients;
  websockets: WebSocketClients;
  helper: ChimeraTestHelper;
  waitForService: (serviceName: string, maxAttempts?: number) => Promise<boolean>;
  cleanup: () => Promise<void>;
}>({
  /**
   * Test data factory fixture
   */
  testData: async ({}, use) => {
    await use(TestDataFactory);
  },

  /**
   * Service client fixture - creates HTTP clients for all services
   */
  services: async ({ request }, use) => {
    const clients: ServiceClients = {
      orchestrator: request,
      scenespeak: request,
      captioning: request,
      bsl: request,
      sentiment: request,
      lighting: request,
      safety: request,
      console: request,
      music: request
    };
    await use(clients);
  },

  /**
   * WebSocket clients fixture
   */
  websockets: async ({}, use) => {
    const clients: WebSocketClients = {
      console: await createWebSocketClient('ws://localhost:8007/ws'),
      bsl: await createWebSocketClient('ws://localhost:8003/ws/avatar'),
      captioning: await createWebSocketClient('ws://localhost:8002/v1/stream'),
      sentiment: await createWebSocketClient('ws://localhost:8004/ws')
    };

    await use(clients);

    // Cleanup: close all WebSocket connections
    Object.values(clients).forEach(client => client.close());
  },

  /**
   * Helper fixture for common test operations
   */
  helper: async ({ page, request }, use) => {
    const helper = new ChimeraTestHelper(page, request);
    await use(helper);
  },

  /**
   * Wait for service to be healthy
   */
  waitForService: async ({ request }, use) => {
    const waitForService = async (serviceName: string, maxAttempts: number = 30): Promise<boolean> => {
      const service = SERVICES[serviceName];
      if (!service) {
        throw new Error(`Unknown service: ${serviceName}`);
      }

      for (let i = 0; i < maxAttempts; i++) {
        try {
          const response = await request.get(`${service.baseURL}${service.healthEndpoint}`, {
            timeout: 5000
          });
          if (response.ok()) {
            return true;
          }
        } catch (error) {
          // Service not ready yet, continue waiting
        }

        // Wait before retrying
        await new Promise(resolve => setTimeout(resolve, 2000));
      }

      return false;
    };

    await use(waitForService);
  },

  /**
   * Cleanup fixture - runs after each test
   */
  cleanup: async ({}, use) => {
    await use(async () => {
      // Cleanup logic can be added here
      // For now, this is a placeholder for any cleanup operations
    });
  }
});

/**
 * Test markers and tags
 */
export const tags = {
  integration: '@integration',
  slow: '@slow',
  websocket: '@websocket',
  requiresDocker: '@requires-docker',
  smoke: '@smoke',
  workflow: '@workflow',
  sentiment: '@sentiment',
  dialogue: '@dialogue',
  bsl: '@bsl',
  safety: '@safety',
  lighting: '@lighting',
  music: '@music'
};

/**
 * Helper function to check service health
 */
export async function checkServiceHealth(
  request: APIRequestContext,
  serviceName: string
): Promise<boolean> {
  const service = SERVICES[serviceName];
  if (!service) {
    throw new Error(`Unknown service: ${serviceName}`);
  }

  try {
    const response = await request.get(`${service.baseURL}${service.healthEndpoint}`, {
      timeout: 5000
    });
    return response.ok();
  } catch (error) {
    return false;
  }
}

/**
 * Helper function to wait for multiple services
 */
export async function waitForServices(
  request: APIRequestContext,
  serviceNames: string[],
  maxAttempts: number = 30
): Promise<Record<string, boolean>> {
  const results: Record<string, boolean> = {};

  for (const serviceName of serviceNames) {
    results[serviceName] = await waitForServiceHelper(request, serviceName, maxAttempts);
  }

  return results;
}

/**
 * Internal helper for waiting on a single service
 */
async function waitForServiceHelper(
  request: APIRequestContext,
  serviceName: string,
  maxAttempts: number
): Promise<boolean> {
  const service = SERVICES[serviceName];
  if (!service) {
    throw new Error(`Unknown service: ${serviceName}`);
  }

  for (let i = 0; i < maxAttempts; i++) {
    const isHealthy = await checkServiceHealth(request, serviceName);
    if (isHealthy) {
      return true;
    }

    await new Promise(resolve => setTimeout(resolve, 2000));
  }

  return false;
}

/**
 * Helper function to create show workflow
 */
export async function createShowWorkflow(
  request: APIRequestContext,
  showContext: ShowContext
): Promise<string> {
  // Start show
  const startResponse = await request.post('http://localhost:8000/api/show/control', {
    data: {
      action: 'start_show',
      show_id: showContext.show_id
    }
  });

  if (!startResponse.ok()) {
    throw new Error('Failed to start show');
  }

  const startData = await startResponse.json();
  return startData.show_id || showContext.show_id;
}

/**
 * Helper function to end show workflow
 */
export async function endShowWorkflow(
  request: APIRequestContext,
  showId: string
): Promise<void> {
  await request.post('http://localhost:8000/api/show/control', {
    data: {
      action: 'end_show',
      show_id: showId
    }
  });
}

export { SERVICES, ServiceConfig };
