'use strict';

const express = require('express');
const http = require('http');

const app = express();
const server = http.createServer(app);

app.use(express.json());

// Hello World
app.get('/api/hello', (req, res) => {
  res.json({ message: 'Hello World from BlackRoad.io + Lucidia 🚀' });
});

// Health
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'blackroad-api' });
});

// Chat bridge
app.post('/api/llm/chat', async (req, res) => {
  try {
    const { message } = req.body ?? {};
    if (typeof message !== 'string' || !message.trim()) {
      return res.status(400).json({ error: 'message (string) required' });
    }
    const r = await fetch('http://127.0.0.1:8000/chat', {
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

const PORT = process.env.PORT || 4000;
server.listen(PORT, () => {
  console.log(`BlackRoad API listening on port ${PORT}`);
});
