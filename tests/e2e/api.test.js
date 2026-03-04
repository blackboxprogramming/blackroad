'use strict';

const { describe, it, before, after } = require('node:test');
const assert = require('node:assert/strict');
const http = require('http');

// ---------------------------------------------------------------------------
// Boot the server on a random port for testing
// ---------------------------------------------------------------------------
let baseUrl;
let server;

function request(method, path, body) {
  return new Promise((resolve, reject) => {
    const url = new URL(path, baseUrl);
    const opts = {
      method,
      hostname: url.hostname,
      port: url.port,
      path: url.pathname + url.search,
      headers: {},
    };

    if (body && typeof body === 'object' && !Buffer.isBuffer(body)) {
      body = JSON.stringify(body);
      opts.headers['Content-Type'] = 'application/json';
    } else if (Buffer.isBuffer(body)) {
      opts.headers['Content-Type'] = 'application/json';
    }

    const req = http.request(opts, (res) => {
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => {
        const raw = Buffer.concat(chunks).toString();
        let json;
        try {
          json = JSON.parse(raw);
        } catch {
          json = null;
        }
        resolve({ status: res.statusCode, headers: res.headers, body: json, raw });
      });
    });
    req.on('error', reject);
    if (body) req.write(typeof body === 'string' ? body : body);
    req.end();
  });
}

before(async () => {
  // Clear any cached modules so env changes take effect
  delete require.cache[require.resolve('../../server_full')];

  // Unset Stripe keys so the server boots in "no-stripe" mode for safe testing
  delete process.env.STRIPE_SECRET_KEY;
  delete process.env.STRIPE_WEBHOOK_SECRET;
  delete process.env.STRIPE_PUBLISHABLE_KEY;

  // Use port 0 so the OS picks a free port
  process.env.PORT = '0';

  const mod = require('../../server_full');
  server = mod.server;

  // Wait for listening
  await new Promise((resolve) => {
    if (server.listening) {
      resolve();
    } else {
      server.once('listening', resolve);
    }
  });

  const addr = server.address();
  baseUrl = `http://127.0.0.1:${addr.port}`;
});

after(async () => {
  if (server) {
    await new Promise((resolve) => server.close(resolve));
  }
});

// ===========================================================================
// Health checks
// ===========================================================================
describe('Health endpoints', () => {
  it('GET /health returns ok', async () => {
    const res = await request('GET', '/health');
    assert.equal(res.status, 200);
    assert.equal(res.body.status, 'ok');
    assert.equal(res.body.service, 'blackroad-api');
    assert.equal(typeof res.body.uptime, 'number');
  });

  it('GET /api/health returns ok', async () => {
    const res = await request('GET', '/api/health');
    assert.equal(res.status, 200);
    assert.equal(res.body.ok, true);
  });
});

// ===========================================================================
// Hello
// ===========================================================================
describe('Hello endpoint', () => {
  it('GET /api/hello returns message', async () => {
    const res = await request('GET', '/api/hello');
    assert.equal(res.status, 200);
    assert.ok(res.body.message);
  });
});

// ===========================================================================
// CORS
// ===========================================================================
describe('CORS', () => {
  it('OPTIONS returns 200 with CORS headers', async () => {
    const res = await request('OPTIONS', '/api/health');
    assert.equal(res.status, 200);
    assert.ok(res.headers['access-control-allow-origin']);
    assert.ok(res.headers['access-control-allow-methods']);
  });
});

// ===========================================================================
// Stripe — no keys configured (503 responses)
// ===========================================================================
describe('Stripe endpoints (no keys)', () => {
  it('GET /api/stripe/config returns 503 when unconfigured', async () => {
    const res = await request('GET', '/api/stripe/config');
    assert.equal(res.status, 503);
    assert.ok(res.body.error.includes('not configured'));
  });

  it('POST /api/stripe/create-checkout-session returns 503', async () => {
    const res = await request('POST', '/api/stripe/create-checkout-session', {
      priceId: 'price_test123',
    });
    assert.equal(res.status, 503);
  });

  it('POST /api/stripe/create-payment-intent returns 503', async () => {
    const res = await request('POST', '/api/stripe/create-payment-intent', {
      amount: 1000,
    });
    assert.equal(res.status, 503);
  });

  it('POST /api/stripe/customer-portal returns 503', async () => {
    const res = await request('POST', '/api/stripe/customer-portal', {
      customerId: 'cus_test',
    });
    assert.equal(res.status, 503);
  });

  it('GET /api/stripe/prices returns 503', async () => {
    const res = await request('GET', '/api/stripe/prices');
    assert.equal(res.status, 503);
  });

  it('POST /api/stripe/webhook returns 503 when Stripe not configured', async () => {
    const payload = Buffer.from(JSON.stringify({
      id: 'evt_test',
      type: 'payment_intent.succeeded',
      data: { object: { id: 'pi_test', amount: 2000 } },
    }));
    const res = await request('POST', '/api/stripe/webhook', payload);
    assert.equal(res.status, 503);
  });
});

// ===========================================================================
// LLM chat bridge — expect 502 since no LLM server running in test
// ===========================================================================
describe('LLM chat bridge', () => {
  it('POST /api/llm/chat rejects empty message', async () => {
    const res = await request('POST', '/api/llm/chat', { message: '' });
    assert.equal(res.status, 400);
  });

  it('POST /api/llm/chat rejects missing message', async () => {
    const res = await request('POST', '/api/llm/chat', {});
    assert.equal(res.status, 400);
  });

  it('POST /api/llm/chat returns 502 when LLM offline', async () => {
    const res = await request('POST', '/api/llm/chat', { message: 'hello' });
    assert.equal(res.status, 502);
    assert.ok(res.body.error.includes('not reachable'));
  });
});
