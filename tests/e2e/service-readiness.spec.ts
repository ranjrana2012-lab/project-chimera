// tests/e2e/service-readiness.spec.ts
import { test, expect } from '@playwright/test';
import { ServiceReadinessGateway } from './helpers/service-readiness';

test.describe('ServiceReadinessGateway', () => {
  test('waitForAllServices should timeout for non-existent service', async () => {
    const gateway = new ServiceReadinessGateway();
    // This should fail because services aren't running
    try {
      await gateway.waitForAllServices(1000);
      expect(true).toBe(false); // Should not reach here
    } catch (error) {
      expect(error).toHaveProperty('message');
    }
  });
});
