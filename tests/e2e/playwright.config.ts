import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E Testing Configuration for Project Chimera
 *
 * This configuration supports:
 * - Testing all 9 microservices (ports 8000-8007, 8011)
 * - WebSocket real-time communication testing
 * - API contract testing
 * - UI testing for Operator Console
 * - Ralph Mode autonomous agent integration
 */
export default defineConfig({
  // Test directory location
  testDir: './',

  // Run tests in parallel for faster execution
  fullyParallel: true,

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry on CI only
  retries: process.env.CI ? 2 : 0,

  // Limit workers on CI for resource constraints
  workers: process.env.CI ? 1 : undefined,

  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['list']
  ],

  // Shared settings for all tests
  use: {
    // Base URL for tests - uses localhost by default, configurable via BASE_URL env var
    baseURL: process.env.BASE_URL || 'http://localhost:8000',

    // Collect trace when retrying a test for debugging
    trace: 'on-first-retry',

    // Screenshot configuration
    screenshot: 'only-on-failure',

    // Video recording configuration
    video: 'retain-on-failure',

    // Action timeout for slower services
    actionTimeout: 10000,

    // Navigation timeout
    navigationTimeout: 30000,
  },

  // Configure projects for different browsers
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // Global setup - runs before all tests
  globalSetup: require.resolve('./global-setup'),

  // Global teardown - runs after all tests
  globalTeardown: require.resolve('./global-teardown'),

  // Test timeout - 30 seconds for most tests
  timeout: 30 * 1000,
});
