const WebSocket = require('ws');
const express = require('express');
const cors = require('cors');
const http = require('http');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(cors());
app.use(express.json());

const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// Channel directory
const CHANNEL_DIR = path.join(process.env.HOME || '/tmp', '.blackroad/channel');

// Connected clients by portal
const clients = {
  roadview: new Set(),
  lucidia: new Set(),
  roadcode: new Set(),
  radius: new Set(),
  roadworld: new Set(),
  roadcoin: new Set(),
  roadchain: new Set(),
  roadie: new Set(),
  universal: new Set(),
};

// Live journey data
const journeys = new Map();

wss.on('connection', (ws, req) => {
  const url = new URL(req.url, 'http://localhost');
  const portal = url.searchParams.get('portal') || 'universal';

  if (clients[portal]) {
    clients[portal].add(ws);
  }

  const count = clients[portal] ? clients[portal].size : 0;
  console.log(`[${portal}] Client connected. Total: ${count}`);

  // Send initial state
  ws.send(JSON.stringify({
    type: 'connected',
    portal,
    timestamp: Date.now(),
    journeys: Array.from(journeys.values())
  }));

  ws.on('message', (data) => {
    try {
      const msg = JSON.parse(data);
      handleMessage(ws, portal, msg);
    } catch (e) {
      console.error('Invalid message:', e);
    }
  });

  ws.on('close', () => {
    if (clients[portal]) {
      clients[portal].delete(ws);
    }
    console.log(`[${portal}] Client disconnected`);
  });
});

function handleMessage(ws, portal, msg) {
  switch (msg.type) {
    case 'location_update':
      const journey = journeys.get(msg.journeyId) || {
        id: msg.journeyId,
        user: msg.user || 'Anonymous',
        coordinates: [],
        live: true,
        color: msg.color || '#FF1D6C'
      };
      journey.coordinates.push(msg.coordinates);
      journeys.set(msg.journeyId, journey);
      broadcast('roadview', { type: 'journey_update', journey });
      break;

    case 'chat':
      broadcast('roadie', {
        type: 'chat',
        from: msg.from,
        text: msg.text,
        timestamp: Date.now()
      });
      break;

    case 'broadcast':
      Object.keys(clients).forEach(p => {
        broadcast(p, {
          type: 'broadcast',
          from: portal,
          payload: msg.payload
        });
      });
      break;

    case 'channel_write':
      writeToChannel(msg.channel, msg.data);
      break;
  }
}

function broadcast(portal, data) {
  const json = JSON.stringify(data);
  const portalClients = clients[portal];
  if (portalClients) {
    portalClients.forEach(client => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(json);
      }
    });
  }
}

function writeToChannel(channel, data) {
  const filepath = path.join(CHANNEL_DIR, channel, `${Date.now()}.json`);
  try {
    fs.mkdirSync(path.dirname(filepath), { recursive: true });
    fs.writeFileSync(filepath, JSON.stringify(data, null, 2));
  } catch (e) {
    console.error('Channel write error:', e);
  }
}

// REST API
app.get('/status', (req, res) => {
  const clientCounts = {};
  Object.keys(clients).forEach(k => {
    clientCounts[k] = clients[k].size;
  });
  res.json({
    status: 'ok',
    clients: clientCounts,
    journeys: journeys.size
  });
});

app.post('/journey', (req, res) => {
  const journey = {
    id: req.body.id || `journey-${Date.now()}`,
    user: req.body.user || 'Anonymous',
    coordinates: req.body.coordinates || [],
    live: req.body.live !== false,
    color: req.body.color || '#FF1D6C'
  };
  journeys.set(journey.id, journey);
  broadcast('roadview', { type: 'journey_update', journey });
  res.json({ success: true, journey });
});

app.get('/journeys', (req, res) => {
  res.json(Array.from(journeys.values()));
});

// Simulate live movement for demo journeys
setInterval(() => {
  journeys.forEach((journey) => {
    if (journey.live && journey.coordinates.length > 0) {
      const last = journey.coordinates[journey.coordinates.length - 1];
      const newCoord = [
        last[0] + (Math.random() - 0.5) * 0.005,
        last[1] + (Math.random() - 0.5) * 0.005
      ];
      journey.coordinates.push(newCoord);
      broadcast('roadview', { type: 'journey_update', journey });
    }
  });
}, 3000);

const PORT = process.env.PORT || 8080;
server.listen(PORT, () => {
  console.log(`\n  BlackRoad Realtime Server`);
  console.log(`  -------------------------`);
  console.log(`  WebSocket: ws://localhost:${PORT}`);
  console.log(`  REST API:  http://localhost:${PORT}`);
  console.log(`  Status:    http://localhost:${PORT}/status\n`);
});
