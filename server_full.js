'use strict';

const express = require('express');
const http = require('http');
const { loadConfig, getMissingKeys } = require('./config');
const { getAllProducts, getActiveProducts, getProductById, getProductsByTier } = require('./config/products');

const app = express();
const server = http.createServer(app);
const config = loadConfig();

app.use(express.json());

// Hello World
app.get('/api/hello', (req, res) => {
  res.json({ message: 'Hello World from BlackRoad.io + Lucidia 🚀' });
});

// Health
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'blackroad-api' });
});

// ── Config status (production readiness check) ──────────────
app.get('/api/config/status', (req, res) => {
  const missing = getMissingKeys();
  res.json({
    ready: missing.length === 0,
    environment: config.nodeEnv,
    missing_keys: missing
  });
});

// ── Products ─────────────────────────────────────────────────
app.get('/api/products', (req, res) => {
  const { tier, active } = req.query;
  let result;
  if (tier) {
    result = getProductsByTier(tier);
  } else if (active === 'true') {
    result = getActiveProducts();
  } else {
    result = getAllProducts();
  }
  res.json({ products: result, count: result.length });
});

app.get('/api/products/:id', (req, res) => {
  const product = getProductById(req.params.id);
  if (!product) {
    return res.status(404).json({ error: 'Product not found' });
  }
  res.json(product);
});

// ── Stripe products sync endpoint ────────────────────────────
app.post('/api/stripe/products/sync', async (req, res) => {
  if (!config.stripe.secretKey) {
    return res.status(503).json({ error: 'STRIPE_SECRET_KEY not configured' });
  }
  try {
    const stripe = require('stripe')(config.stripe.secretKey);
    const catalog = getActiveProducts();
    const synced = [];

    for (const product of catalog) {
      const created = await stripe.products.create({
        name: product.name,
        description: product.description,
        active: product.active,
        metadata: { blackroad_id: product.id, tier: product.tier, ...product.metadata }
      });
      synced.push({ id: product.id, stripe_id: created.id });
    }

    res.json({ synced, count: synced.length });
  } catch (err) {
    console.error('Stripe sync error:', err);
    res.status(500).json({ error: 'Stripe sync failed' });
  }
});

// ── Drive status endpoint ────────────────────────────────────
app.get('/api/drive/status', (req, res) => {
  const configured = !!(config.drive.clientId && config.drive.clientSecret);
  res.json({
    configured,
    folder_id: config.drive.folderId || null,
    redirect_uri: config.drive.redirectUri
  });
});

// Chat bridge
app.post('/api/llm/chat', async (req, res) => {
  try {
    const { message } = req.body ?? {};
    if (typeof message !== 'string' || !message.trim()) {
      return res.status(400).json({ error: 'message (string) required' });
    }
    const llmUrl = config.llm.baseUrl.replace(/\/$/, '');
    const r = await fetch(`${llmUrl}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
    const data = await r.json();
    return res.json({ reply: data.reply ?? data });
  } catch (err) {
    console.error('LLM error:', err);
    return res.status(502).json({ error: 'Lucidia LLM not reachable' });
  }
});

const PORT = config.port;
server.listen(PORT, () => {
  const missing = getMissingKeys();
  console.log(`BlackRoad API listening on port ${PORT}`);
  if (missing.length > 0) {
    console.warn(`⚠ Missing env keys: ${missing.join(', ')}`);
  }
});
