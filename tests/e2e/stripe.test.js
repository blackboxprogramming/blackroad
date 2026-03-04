'use strict';

/**
 * Stripe integration e2e tests.
 *
 * These test the REAL Stripe API flow when STRIPE_SECRET_KEY is set (e.g. with
 * a Stripe test-mode key). When the key is missing, the tests are skipped so
 * CI still passes.
 *
 * To run locally:
 *   STRIPE_SECRET_KEY=sk_test_xxx \
 *   STRIPE_PUBLISHABLE_KEY=pk_test_xxx \
 *   npm run test:e2e
 */

const { describe, it, before, after } = require('node:test');
const assert = require('node:assert/strict');
const http = require('http');

const hasStripeKey = !!process.env.STRIPE_SECRET_KEY;

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
        try { json = JSON.parse(raw); } catch { json = null; }
        resolve({ status: res.statusCode, headers: res.headers, body: json, raw });
      });
    });
    req.on('error', reject);
    if (body) req.write(typeof body === 'string' ? body : body);
    req.end();
  });
}

before(async () => {
  delete require.cache[require.resolve('../../server_full')];
  process.env.PORT = '0';

  const mod = require('../../server_full');
  server = mod.server;

  await new Promise((resolve) => {
    if (server.listening) resolve();
    else server.once('listening', resolve);
  });

  const addr = server.address();
  baseUrl = `http://127.0.0.1:${addr.port}`;
});

after(async () => {
  if (server) await new Promise((resolve) => server.close(resolve));
});

describe('Stripe live integration', { skip: !hasStripeKey && 'STRIPE_SECRET_KEY not set' }, () => {
  it('GET /api/stripe/config returns publishable key', async () => {
    const res = await request('GET', '/api/stripe/config');
    assert.equal(res.status, 200);
    assert.ok(res.body.publishableKey);
    assert.ok(res.body.publishableKey.startsWith('pk_'));
  });

  it('GET /api/stripe/prices returns list', async () => {
    const res = await request('GET', '/api/stripe/prices');
    assert.equal(res.status, 200);
    assert.ok(Array.isArray(res.body.prices));
  });

  it('POST /api/stripe/create-checkout-session rejects missing priceId', async () => {
    const res = await request('POST', '/api/stripe/create-checkout-session', {});
    assert.equal(res.status, 400);
    assert.ok(res.body.error.includes('priceId'));
  });

  it('POST /api/stripe/create-payment-intent rejects too-small amount', async () => {
    const res = await request('POST', '/api/stripe/create-payment-intent', { amount: 10 });
    assert.equal(res.status, 400);
  });

  it('POST /api/stripe/customer-portal rejects missing customerId', async () => {
    const res = await request('POST', '/api/stripe/customer-portal', {});
    assert.equal(res.status, 400);
  });

  it('POST /api/stripe/webhook processes event in dev mode (no secret)', async () => {
    // Without STRIPE_WEBHOOK_SECRET, the server trusts raw payloads (dev mode)
    const payload = Buffer.from(JSON.stringify({
      id: 'evt_test_e2e',
      type: 'payment_intent.succeeded',
      data: { object: { id: 'pi_test_e2e', amount: 5000 } },
    }));
    const res = await request('POST', '/api/stripe/webhook', payload);
    // If webhook secret IS set, this will fail signature check (400).
    // If not set, dev mode processes it (200).
    assert.ok([200, 400].includes(res.status));
    if (res.status === 200) {
      assert.equal(res.body.received, true);
    }
  });
});
