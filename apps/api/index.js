const express = require('express');
const http = require('http');
const { Server } = require('socket.io');

const app = express();
app.use(express.json());

// Simple CORS setup to allow cross-origin requests
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.sendStatus(200);
  next();
});

const homeworks = [];

app.get('/api/health', (req, res) => {
  res.json({ ok: true });
});

app.get('/api/homework', (req, res) => {
  res.json(homeworks);
});

app.post('/api/homework', (req, res) => {
  const { title, description } = req.body;
  if (!title || !description) {
    return res.status(400).json({ error: 'Title and description are required' });
  }
  const hw = { id: Date.now(), title, description };
  homeworks.push(hw);
  res.status(201).json(hw);
});

const server = http.createServer(app);
const io = new Server(server, {
  path: '/socket.io'
});

io.on('connection', socket => {
  // placeholder for socket events
});

const PORT = process.env.PORT || 4000;
server.listen(PORT, () => {
  console.log(`API listening on port ${PORT}`);
});
