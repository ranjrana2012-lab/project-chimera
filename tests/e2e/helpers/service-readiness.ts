// tests/helpers/service-readiness.ts
export interface ServiceHealth {
  url: string;
  name: string;
  expectedStatus?: string;
}

export class ServiceReadinessGateway {
  private services: ServiceHealth[] = [
    { url: 'http://localhost:8000/health/ready', name: 'orchestrator' },
    { url: 'http://localhost:8001/health/ready', name: 'scenespeak-agent' },
    { url: 'http://localhost:8002/health/ready', name: 'captioning-agent' },
    { url: 'http://localhost:8003/health/ready', name: 'bsl-agent' },
    { url: 'http://localhost:8004/health/ready', name: 'sentiment-agent' },
    { url: 'http://localhost:8005/health/ready', name: 'lighting-sound-music' },
    { url: 'http://localhost:8006/health/ready', name: 'safety-filter' },
    { url: 'http://localhost:8007/health/ready', name: 'operator-console' },
    { url: 'http://localhost:8011/health/ready', name: 'music-generation' },
  ];

  async waitForAllServices(timeout: number = 60000): Promise<boolean> {
    console.log('Waiting for all services to be ready...');
    const startTime = Date.now();

    for (const service of this.services) {
      await this.waitForService(service, timeout - (Date.now() - startTime));
    }

    console.log('All services ready!');
    return true;
  }

  private async waitForService(service: ServiceHealth, timeout: number): Promise<void> {
    const startTime = Date.now();
    const deadline = startTime + timeout;

    while (Date.now() < deadline) {
      try {
        const response = await fetch(service.url);
        if (response.ok) {
          const body = await response.json();
          if (body.status === 'ready' || body.status === 'alive') {
            console.log(`✓ ${service.name} is ready`);
            return;
          }
        }
      } catch (error) {
        // Service not ready yet, continue waiting
      }
      await this.sleep(500);
    }

    throw new Error(`Service ${service.name} not ready at ${service.url} after ${timeout}ms`);
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async checkAllServices(): Promise<Map<string, boolean>> {
    const results = new Map<string, boolean>();

    for (const service of this.services) {
      try {
        const response = await fetch(service.url);
        results.set(service.name, response.ok);
      } catch {
        results.set(service.name, false);
      }
    }

    return results;
  }
}

export const serviceReadiness = new ServiceReadinessGateway();
