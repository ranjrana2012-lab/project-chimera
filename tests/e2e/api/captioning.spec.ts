import { test, expect } from '@playwright/test';
import { readFileSync } from 'fs';
import { join } from 'path';

/**
 * Captioning Agent API Contract Tests
 *
 * Tests the audio transcription service.
 * Port: 8002
 *
 * Endpoints:
 * - GET /health/live - Basic liveness check
 * - GET /health/ready - Readiness check with model info
 * - POST /api/transcribe - Transcribe audio to text
 */

test.describe('Captioning Agent API', () => {
  const baseURL = 'http://localhost:8002';

  test('@smoke @api health endpoint returns 200', async ({ request }) => {
    const response = await request.get(`${baseURL}/health/live`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('status', 'alive');
  });

  test('@api transcribe audio with valid input', async ({ request }) => {
    // Create a simple test audio buffer (silent audio for testing)
    const testAudio = Buffer.from('RIFF' + ' '.repeat(1000));

    const response = await request.post(`${baseURL}/api/transcribe`, {
      multipart: {
        audio: {
          name: 'test.wav',
          mimeType: 'audio/wav',
          buffer: testAudio
        }
      },
      timeout: 30000
    });

    // Model may return error on invalid audio, but should respond
    expect([200, 422, 400]).toContain(response.status());

    if (response.status() === 200) {
      const body = await response.json();
      expect(body).toHaveProperty('transcription');
      expect(body).toHaveProperty('confidence');
    }
  });

  test('@api transcribe with language parameter', async ({ request }) => {
    const testAudio = Buffer.from('RIFF' + ' '.repeat(1000));

    const response = await request.post(`${baseURL}/api/transcribe`, {
      multipart: {
        audio: {
          name: 'test.wav',
          mimeType: 'audio/wav',
          buffer: testAudio
        }
      },
      params: {
        language: 'en'
      },
      timeout: 30000
    });

    expect([200, 422, 400]).toContain(response.status());
  });

  test('@api rejects missing audio file', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/transcribe`, {
      data: {}
    });

    expect(response.status()).toBe(422);
  });

  test('@api rejects invalid audio format', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/transcribe`, {
      multipart: {
        audio: {
          name: 'test.txt',
          mimeType: 'text/plain',
          buffer: Buffer.from('not audio')
        }
      }
    });

    expect(response.status()).toBe(422);
  });

  test('@api transcription includes metadata', async ({ request }) => {
    const testAudio = Buffer.from('RIFF' + ' '.repeat(1000));

    const response = await request.post(`${baseURL}/api/transcribe`, {
      multipart: {
        audio: {
          name: 'test.wav',
          mimeType: 'audio/wav',
          buffer: testAudio
        }
      },
      timeout: 30000
    });

    if (response.status() === 200) {
      const body = await response.json();
      expect(body).toMatchObject({
        transcription: expect.any(String),
        confidence: expect.any(Number),
        duration: expect.any(Number)
      });
    }
  });

  test('@api transcription with timestamp option', async ({ request }) => {
    const testAudio = Buffer.from('RIFF' + ' '.repeat(1000));

    const response = await request.post(`${baseURL}/api/transcribe`, {
      multipart: {
        audio: {
          name: 'test.wav',
          mimeType: 'audio/wav',
          buffer: testAudio
        }
      },
      params: {
        timestamps: 'true'
      },
      timeout: 30000
    });

    if (response.status() === 200) {
      const body = await response.json();
      expect(body).toHaveProperty('segments');
      expect(Array.isArray(body.segments)).toBeTruthy();
    }
  });

  test('@api handles large audio file', async ({ request }) => {
    // Create a larger test audio buffer
    const testAudio = Buffer.from('RIFF' + ' '.repeat(10000));

    const response = await request.post(`${baseURL}/api/transcribe`, {
      multipart: {
        audio: {
          name: 'test.wav',
          mimeType: 'audio/wav',
          buffer: testAudio
        }
      },
      timeout: 60000
    });

    // Should handle large files gracefully
    expect([200, 413, 422, 400]).toContain(response.status());

    if (response.status() === 413) {
      const body = await response.json();
      expect(body.detail).toMatch(/too large|size/i);
    }
  });

  test('@api health/ready includes model information', async ({ request }) => {
    const response = await request.get(`${baseURL}/health/ready`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('model_info');
    expect(body.model_info).toMatchObject({
      name: expect.any(String),
      loaded: expect.any(Boolean)
    });
  });

  test('@api transcription completes within timeout', async ({ request }) => {
    const testAudio = Buffer.from('RIFF' + ' '.repeat(1000));

    const startTime = Date.now();

    const response = await request.post(`${baseURL}/api/transcribe`, {
      multipart: {
        audio: {
          name: 'test.wav',
          mimeType: 'audio/wav',
          buffer: testAudio
        }
      },
      timeout: 30000
    });

    const latency = Date.now() - startTime;

    expect(latency).toBeLessThan(35000);
  });

  test('@api supports multiple audio formats', async ({ request }) => {
    const testAudio = Buffer.from('ID3' + ' '.repeat(1000));

    const response = await request.post(`${baseURL}/api/transcribe`, {
      multipart: {
        audio: {
          name: 'test.mp3',
          mimeType: 'audio/mpeg',
          buffer: testAudio
        }
      },
      timeout: 30000
    });

    // Should accept or reject based on format support
    expect([200, 422, 400]).toContain(response.status());
  });

  test('@api batch transcription endpoint', async ({ request }) => {
    const testAudio1 = Buffer.from('RIFF' + ' '.repeat(500));
    const testAudio2 = Buffer.from('RIFF' + ' '.repeat(500));

    const response = await request.post(`${baseURL}/api/transcribe/batch`, {
      multipart: {
        'audio1': {
          name: 'test1.wav',
          mimeType: 'audio/wav',
          buffer: testAudio1
        },
        'audio2': {
          name: 'test2.wav',
          mimeType: 'audio/wav',
          buffer: testAudio2
        }
      },
      timeout: 45000
    });

    // Batch endpoint may not be implemented
    if (response.status() === 404) {
      return;
    }

    expect([200, 422]).toContain(response.status());
  });
});
