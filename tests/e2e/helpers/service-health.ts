import { spawn, ChildProcess } from 'child_process';
import * as path from 'path';

/**
 * Service configuration interface
 */
interface Service {
  name: string;
  port: number;
  healthEndpoint?: string;
}

/**
 * ServiceHealthHelper - Manage service lifecycle for E2E tests
 *
 * Provides methods for:
 * - Starting/stopping services via Docker Compose
 * - Waiting for services to become healthy
 * - Checking individual service health
 */
export class ServiceHealthHelper {
  private static services: Service[] = [
    { name: 'openclaw-orchestrator', port: 8000, healthEndpoint: '/health/live' },
    { name: 'scenespeak-agent', port: 8001, healthEndpoint: '/health/live' },
    { name: 'captioning-agent', port: 8002, healthEndpoint: '/health/live' },
    { name: 'bsl-agent', port: 8003, healthEndpoint: '/health/live' },
    { name: 'sentiment-agent', port: 8004, healthEndpoint: '/health/live' },
    { name: 'lighting-sound-music', port: 8005, healthEndpoint: '/health/live' },
    { name: 'safety-filter', port: 8006, healthEndpoint: '/health/live' },
    { name: 'operator-console', port: 8007, healthEndpoint: '/health/live' },
    { name: 'music-generation', port: 8011, healthEndpoint: '/health/live' }
  ];

  private static composeProcess: ChildProcess | null = null;

  /**
   * Ensure all services are ready and healthy
   * @param timeout - Maximum time to wait per service in ms (default: 60000)
   * @param optionalServices - Array of service names that are optional (won't fail if not ready)
   * @throws Error if any required service fails to become healthy
   */
  static async ensureServicesReady(
    timeout: number = 60000,
    optionalServices: string[] = ['music-generation']
  ): Promise<void> {
    console.log('\n🔍 Checking service health...');

    const maxAttempts = Math.floor(timeout / 2000);
    const errors: Array<{ service: string; error: string }> = [];
    const warnings: Array<{ service: string; error: string }> = [];

    for (const service of this.services) {
      try {
        await this.waitForService(service.name, service.port, maxAttempts);
        console.log(`✅ ${service.name} (:${service.port}) ready`);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);

        if (optionalServices.includes(service.name)) {
          warnings.push({ service: service.name, error: errorMessage });
          console.warn(`⚠️  ${service.name} (:${service.port}) not available (optional): ${errorMessage}`);
        } else {
          errors.push({ service: service.name, error: errorMessage });
          console.error(`❌ ${service.name} (:${service.port}) failed: ${errorMessage}`);
        }
      }
    }

    if (warnings.length > 0) {
      console.log(`\n⚠️  ${warnings.length} optional service(s) not available:`);
      warnings.forEach(w => console.log(`  - ${w.service}: ${w.error}`));
    }

    if (errors.length > 0) {
      throw new Error(
        `Failed to start required services:\n${errors.map(e => `  - ${e.service}: ${e.error}`).join('\n')}`
      );
    }

    console.log('\n✅ All required services ready!\n');
  }

  /**
   * Wait for a specific service to become healthy
   * @param name - Service name
   * @param port - Service port
   * @param maxAttempts - Maximum number of polling attempts (default: 30)
   * @param interval - Delay between attempts in ms (default: 2000)
   * @throws Error if service doesn't become healthy
   */
  static async waitForService(
    name: string,
    port: number,
    maxAttempts: number = 30,
    interval: number = 2000
  ): Promise<void> {
    const startTime = Date.now();

    // Get the specific health endpoint for this service
    const service = this.getService(name);
    const healthEndpoint = service?.healthEndpoint || '/health/live';

    for (let i = 0; i < maxAttempts; i++) {
      try {
        const response = await fetch(`http://localhost:${port}${healthEndpoint}`, {
          method: 'GET',
          signal: AbortSignal.timeout(5000)
        });

        if (response.ok) {
          const elapsed = Date.now() - startTime;
          console.log(`  → ${name} responded in ${elapsed}ms`);
          return;
        }
      } catch (error) {
        // Connection failed, will retry
      }

      // Show progress for services taking longer
      if (i < maxAttempts - 1) {
        process.stdout.write(`  ⏳ Waiting for ${name}... ${i + 1}/${maxAttempts}\r`);
        await new Promise(resolve => setTimeout(resolve, interval));
      }
    }

    // Clear the progress line
    process.stdout.write('\r');

    throw new Error(
      `Service ${name}:${port} failed to start after ${maxAttempts} attempts (${maxAttempts * interval}ms)`
    );
  }

  /**
   * Start all services using Docker Compose
   * @param composeFiles - Array of docker-compose files to use
   * @param cwd - Working directory for docker-compose command
   * @throws Error if docker-compose fails to start
   */
  static async startServices(
    composeFiles: string[] = ['docker-compose.yml', 'docker-compose.prod.yml'],
    cwd: string = process.cwd()
  ): Promise<void> {
    console.log('🚀 Starting services with Docker Compose...');

    // Build the docker-compose command with multiple -f flags
    const args: string[] = [];
    composeFiles.forEach(file => {
      args.push('-f', file);
    });
    args.push('up', '-d');

    return new Promise((resolve, reject) => {
      const compose = spawn('docker', ['compose', ...args], {
        cwd,
        stdio: 'inherit',
        shell: true
      });

      this.composeProcess = compose;

      compose.on('close', (code) => {
        if (code === 0) {
          console.log('✅ Docker Compose started successfully');
          resolve();
        } else {
          reject(new Error(`docker compose exited with code ${code}`));
        }
      });

      compose.on('error', (error) => {
        reject(new Error(`Failed to start docker compose: ${error.message}`));
      });
    });
  }

  /**
   * Stop all services using Docker Compose
   * @param cwd - Working directory for docker-compose command
   * @param removeVolumes - Whether to remove volumes (default: false)
   * @throws Error if docker-compose fails to stop
   */
  static async stopServices(
    cwd: string = process.cwd(),
    removeVolumes: boolean = false
  ): Promise<void> {
    console.log('🛑 Stopping services...');

    const args = ['down'];
    if (removeVolumes) {
      args.push('-v');
    }

    return new Promise((resolve, reject) => {
      const compose = spawn('docker', ['compose', ...args], {
        cwd,
        stdio: 'inherit',
        shell: true
      });

      compose.on('close', (code) => {
        if (code === 0) {
          console.log('✅ Services stopped successfully');
          resolve();
        } else {
          // Don't fail if services are already stopped
          console.log('ℹ️ Services may already be stopped');
          resolve();
        }
      });

      compose.on('error', (error) => {
        reject(new Error(`Failed to stop docker compose: ${error.message}`));
      });
    });
  }

  /**
   * Restart a specific service
   * @param serviceName - Name of the service to restart
   * @param cwd - Working directory for docker-compose command
   * @throws Error if restart fails
   */
  static async restartService(serviceName: string, cwd: string = process.cwd()): Promise<void> {
    console.log(`🔄 Restarting service: ${serviceName}`);

    return new Promise((resolve, reject) => {
      const compose = spawn('docker', ['compose', 'restart', serviceName], {
        cwd,
        stdio: 'inherit',
        shell: true
      });

      compose.on('close', (code) => {
        if (code === 0) {
          console.log(`✅ ${serviceName} restarted successfully`);
          resolve();
        } else {
          reject(new Error(`${serviceName} restart exited with code ${code}`));
        }
      });

      compose.on('error', (error) => {
        reject(new Error(`Failed to restart ${serviceName}: ${error.message}`));
      });
    });
  }

  /**
   * Check if any services are already running
   * @returns Promise<boolean> - true if at least one service is running
   */
  static async areServicesRunning(): Promise<boolean> {
    try {
      // Check orchestrator as the primary service - use /health/live endpoint
      const response = await fetch('http://localhost:8000/health/live', {
        method: 'GET',
        signal: AbortSignal.timeout(2000)
      });
      return response.ok;
    } catch {
      return false;
    }
  }

  /**
   * Get list of all configured services
   * @returns Array of service configurations
   */
  static getServices(): Service[] {
    return [...this.services];
  }

  /**
   * Get a specific service configuration by name
   * @param name - Service name
   * @returns Service configuration or undefined
   */
  static getService(name: string): Service | undefined {
    return this.services.find(s => s.name === name);
  }

  /**
   * Check health of a specific service
   * @param name - Service name
   * @returns Promise<boolean> - true if healthy, false otherwise
   */
  static async checkServiceHealth(name: string): Promise<boolean> {
    const service = this.getService(name);
    if (!service) {
      throw new Error(`Unknown service: ${name}`);
    }

    const healthEndpoint = service.healthEndpoint || '/health/live';

    try {
      const response = await fetch(`http://localhost:${service.port}${healthEndpoint}`, {
        method: 'GET',
        signal: AbortSignal.timeout(5000)
      });
      return response.ok;
    } catch {
      return false;
    }
  }

  /**
   * Wait for multiple services to become healthy (parallel)
   * @param serviceNames - Array of service names to wait for
   * @param maxAttempts - Maximum attempts per service (default: 30)
   * @param interval - Delay between attempts in ms (default: 2000)
   * @throws Error if any service fails to become healthy
   */
  static async waitForServices(
    serviceNames: string[],
    maxAttempts: number = 30,
    interval: number = 2000
  ): Promise<void> {
    const promises = serviceNames.map(name => {
      const service = this.getService(name);
      if (!service) {
        throw new Error(`Unknown service: ${name}`);
      }
      return this.waitForService(name, service.port, maxAttempts, interval);
    });

    await Promise.all(promises);
  }
}
