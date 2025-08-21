const express = require('express');
const http = require('http');
const { Server } = require('socket.io');

const app = express();

app.get('/api/health', (req, res) => {
  res.json({ ok: true });
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
