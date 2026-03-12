import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for integration tests
 *
 * This configuration is optimized for integration testing of Project Chimera services.
 * It focuses on API testing and WebSocket communication rather than UI testing.
 */
export default defineConfig({
  testDir: './',
  testMatch: '**/*.spec.ts',
  fullyParallel: false, // Integration tests should run sequentially
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1, // Run tests sequentially to avoid port conflicts
  reporter: [
    ['html'],
    ['list'],
    ['json', { outputFile: 'test-results/results.json' }]
  ],
  timeout: 60000, // 60 seconds per test
  expect: {
    timeout: 10000
  },
  use: {
    baseURL: 'http://localhost:8007',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10000,
    navigationTimeout: 30000
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] }
    }
  ],
  webServer: {
    // Don't start a web server - services should already be running
    command: 'echo "Services should be started before running integration tests"',
    port: 8007,
    reuseExistingServer: !process.env.CI,
    timeout: 120000
  }
});
