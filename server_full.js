'use strict';

const express = require('express');
const http = require('http');
const Stripe = require('stripe');

// ---------------------------------------------------------------------------
// Config (all via env vars — set in systemd unit or .env)
// ---------------------------------------------------------------------------
const PORT = process.env.PORT || 4000;
const STRIPE_SECRET_KEY = process.env.STRIPE_SECRET_KEY;
const STRIPE_WEBHOOK_SECRET = process.env.STRIPE_WEBHOOK_SECRET;
const STRIPE_PUBLISHABLE_KEY = process.env.STRIPE_PUBLISHABLE_KEY;
const FRONTEND_URL = process.env.FRONTEND_URL || 'https://blackroad.io';

const stripe = STRIPE_SECRET_KEY
  ? new Stripe(STRIPE_SECRET_KEY, { apiVersion: '2024-06-20' })
  : null;

const app = express();
const server = http.createServer(app);

// ---------------------------------------------------------------------------
// Middleware
// ---------------------------------------------------------------------------
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', process.env.CORS_ORIGIN || '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  if (req.method === 'OPTIONS') return res.sendStatus(200);
  next();
});

// Stripe webhooks need the raw body — must come BEFORE express.json()
app.post(
  '/api/stripe/webhook',
  express.raw({ type: 'application/json' }),
  handleStripeWebhook
);

app.use(express.json());

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------
app.get('/health', (_req, res) => {
  res.json({
    status: 'ok',
    service: 'blackroad-api',
    stripe: !!stripe,
    uptime: process.uptime(),
  });
});

app.get('/api/health', (_req, res) => {
  res.json({ ok: true, stripe: !!stripe });
});

// ---------------------------------------------------------------------------
// Stripe — public config
// ---------------------------------------------------------------------------
app.get('/api/stripe/config', (_req, res) => {
  if (!STRIPE_PUBLISHABLE_KEY) {
    return res.status(503).json({ error: 'Stripe not configured' });
  }
  res.json({ publishableKey: STRIPE_PUBLISHABLE_KEY });
});

// ---------------------------------------------------------------------------
// Stripe — create checkout session
// ---------------------------------------------------------------------------
app.post('/api/stripe/create-checkout-session', async (req, res) => {
  if (!stripe) {
    return res.status(503).json({ error: 'Stripe not configured' });
  }

  try {
    const { priceId, mode, quantity, customerId, metadata } = req.body;

    if (!priceId) {
      return res.status(400).json({ error: 'priceId is required' });
    }

    const sessionParams = {
      mode: mode || 'subscription',
      line_items: [{ price: priceId, quantity: quantity || 1 }],
      success_url: `${FRONTEND_URL}/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${FRONTEND_URL}/cancel`,
      metadata: metadata || {},
    };

    if (customerId) {
      sessionParams.customer = customerId;
    }

    const session = await stripe.checkout.sessions.create(sessionParams);
    res.json({ sessionId: session.id, url: session.url });
  } catch (err) {
    console.error('Stripe checkout error:', err.message);
    res.status(400).json({ error: err.message });
  }
});

// ---------------------------------------------------------------------------
// Stripe — create one-time payment intent (for custom amounts)
// ---------------------------------------------------------------------------
app.post('/api/stripe/create-payment-intent', async (req, res) => {
  if (!stripe) {
    return res.status(503).json({ error: 'Stripe not configured' });
  }

  try {
    const { amount, currency, metadata } = req.body;

    if (!amount || amount < 50) {
      return res.status(400).json({ error: 'amount must be >= 50 (in cents)' });
    }

    const paymentIntent = await stripe.paymentIntents.create({
      amount,
      currency: currency || 'usd',
      metadata: metadata || {},
    });

    res.json({
      clientSecret: paymentIntent.client_secret,
      paymentIntentId: paymentIntent.id,
    });
  } catch (err) {
    console.error('Stripe payment intent error:', err.message);
    res.status(400).json({ error: err.message });
  }
});

// ---------------------------------------------------------------------------
// Stripe — customer portal (manage subscriptions)
// ---------------------------------------------------------------------------
app.post('/api/stripe/customer-portal', async (req, res) => {
  if (!stripe) {
    return res.status(503).json({ error: 'Stripe not configured' });
  }

  try {
    const { customerId } = req.body;

    if (!customerId) {
      return res.status(400).json({ error: 'customerId is required' });
    }

    const session = await stripe.billingPortal.sessions.create({
      customer: customerId,
      return_url: FRONTEND_URL,
    });

    res.json({ url: session.url });
  } catch (err) {
    console.error('Stripe portal error:', err.message);
    res.status(400).json({ error: err.message });
  }
});

// ---------------------------------------------------------------------------
// Stripe — list products/prices
// ---------------------------------------------------------------------------
app.get('/api/stripe/prices', async (_req, res) => {
  if (!stripe) {
    return res.status(503).json({ error: 'Stripe not configured' });
  }

  try {
    const prices = await stripe.prices.list({
      active: true,
      expand: ['data.product'],
      limit: 50,
    });
    res.json({ prices: prices.data });
  } catch (err) {
    console.error('Stripe prices error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

// ---------------------------------------------------------------------------
// Stripe — webhook handler
// ---------------------------------------------------------------------------
async function handleStripeWebhook(req, res) {
  if (!stripe) {
    return res.status(503).json({ error: 'Stripe not configured' });
  }

  let event;
  try {
    if (STRIPE_WEBHOOK_SECRET) {
      const sig = req.headers['stripe-signature'];
      event = stripe.webhooks.constructEvent(req.body, sig, STRIPE_WEBHOOK_SECRET);
    } else {
      // Dev mode — trust the payload directly
      event = JSON.parse(req.body.toString());
    }
  } catch (err) {
    console.error('Webhook signature verification failed:', err.message);
    return res.status(400).json({ error: 'Webhook signature verification failed' });
  }

  console.log(`Stripe event: ${event.type} [${event.id}]`);

  switch (event.type) {
    case 'checkout.session.completed': {
      const session = event.data.object;
      console.log(`Checkout completed: ${session.id}, customer: ${session.customer}`);
      // TODO: provision access, update DB, send confirmation email
      break;
    }
    case 'payment_intent.succeeded': {
      const intent = event.data.object;
      console.log(`Payment succeeded: ${intent.id}, amount: ${intent.amount}`);
      break;
    }
    case 'customer.subscription.created':
    case 'customer.subscription.updated': {
      const sub = event.data.object;
      console.log(`Subscription ${event.type}: ${sub.id}, status: ${sub.status}`);
      break;
    }
    case 'customer.subscription.deleted': {
      const sub = event.data.object;
      console.log(`Subscription cancelled: ${sub.id}`);
      // TODO: revoke access
      break;
    }
    case 'invoice.payment_failed': {
      const invoice = event.data.object;
      console.log(`Invoice payment failed: ${invoice.id}, customer: ${invoice.customer}`);
      // TODO: notify user, retry logic
      break;
    }
    default:
      console.log(`Unhandled event type: ${event.type}`);
  }

  res.json({ received: true });
}

// ---------------------------------------------------------------------------
// Chat bridge — Lucidia LLM (llama.cpp on port 8083)
// ---------------------------------------------------------------------------
app.post('/api/llm/chat', async (req, res) => {
  try {
    const { message } = req.body ?? {};
    if (typeof message !== 'string' || !message.trim()) {
      return res.status(400).json({ error: 'message (string) required' });
    }
    const r = await fetch('http://127.0.0.1:8083/v1/chat/completions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: [{ role: 'user', content: message }],
        max_tokens: 512,
      }),
    });
    const data = await r.json();
    const reply = data.choices?.[0]?.message?.content ?? JSON.stringify(data);
    return res.json({ reply });
  } catch (err) {
    console.error('LLM error:', err);
    return res.status(502).json({ error: 'Lucidia LLM not reachable' });
  }
});

// ---------------------------------------------------------------------------
// Hello (backwards compat)
// ---------------------------------------------------------------------------
app.get('/api/hello', (_req, res) => {
  res.json({ message: 'BlackRoad API live' });
});

// ---------------------------------------------------------------------------
// Start
// ---------------------------------------------------------------------------
server.listen(PORT, () => {
  console.log(`BlackRoad API listening on :${PORT}`);
  console.log(`  Stripe: ${stripe ? 'enabled' : 'NOT configured (set STRIPE_SECRET_KEY)'}`);
});

module.exports = { app, server };
