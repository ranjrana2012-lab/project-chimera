import { FullConfig } from '@playwright/test';
import { ServiceHealthHelper } from './helpers/service-health';

/**
 * Global Teardown for Project Chimera E2E Tests
 *
 * This script runs after all tests and:
 * - Stops services if they were started by the test suite
 * - Cleans up test artifacts
 *
 * NOTE: By default, services are NOT stopped to allow for:
 * - Manual testing after test run
 * - Re-running tests without service restart
 * - Inspection of service state
 *
 * Set STOP_SERVICES=true environment variable to stop services after tests.
 */
async function globalTeardown(config: FullConfig) {
  console.log('\n🧹 Cleaning up after E2E tests...');
  console.log('=====================================\n');

  const shouldStopServices = process.env.STOP_SERVICES === 'true';

  if (!shouldStopServices) {
    console.log('ℹ️  Services will remain running for manual testing');
    console.log('To stop services automatically, set STOP_SERVICES=true');
    console.log('Or stop manually with: docker-compose down\n');
    return;
  }

  console.log('⏹️  Stopping services...\n');

  try {
    // The docker-compose.yml is in the project root, not tests/e2e
    const projectRoot = process.cwd().replace(/\/tests\/e2e$/, '');
    await ServiceHealthHelper.stopServices(projectRoot, false);
    console.log('✅ Services stopped successfully\n');
  } catch (error) {
    console.error('❌ Failed to stop services:', error);
    console.error('\nYou may need to stop services manually: docker-compose down');
  }
}

export default globalTeardown;
