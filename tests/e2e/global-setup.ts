import { FullConfig } from '@playwright/test';
import { ServiceHealthHelper } from './helpers/service-health';

/**
 * Global Setup for Project Chimera E2E Tests
 *
 * This script runs before all tests and:
 * - Checks if services are already running
 * - Starts services via Docker Compose if needed
 * - Waits for all services to be healthy
 */
async function globalSetup(config: FullConfig) {
  console.log('🎭 Project Chimera E2E Test Setup');
  console.log('=====================================\n');

  // Check if services are already running
  const servicesRunning = await ServiceHealthHelper.areServicesRunning();

  if (servicesRunning) {
    console.log('✅ Services are already running');
    console.log('Skipping Docker Compose startup\n');
  } else {
    console.log('⚠️  Services are not running');
    console.log('Attempting to start services with Docker Compose...\n');

    try {
      // Start services using Docker Compose
      // The docker-compose.yml is in the project root, not tests/e2e
      const projectRoot = process.cwd().replace(/\/tests\/e2e$/, '');
      await ServiceHealthHelper.startServices(
        ['docker-compose.yml'],
        projectRoot
      );
    } catch (error) {
      console.error('❌ Failed to start services:', error);
      console.error('\nPlease start services manually with: docker-compose up -d');
      throw error;
    }
  }

  // Wait for all services to be healthy
  try {
    console.log('\n⏳ Waiting for services to become healthy...\n');
    await ServiceHealthHelper.ensureServicesReady(120000); // 2 minute timeout
    console.log('\n✅ All services are ready for testing!\n');
  } catch (error) {
    console.error('\n❌ Service health check failed:', error);
    console.error('\nPlease check service logs with: docker-compose logs');
    throw error;
  }
}

export default globalSetup;
