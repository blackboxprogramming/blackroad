export interface Env {
  ROOMS: DurableObjectNamespace;
}

export class RealtimeRoom {
  state: DurableObjectState;
  sessions: Map<WebSocket, { portal: string }>;
  journeys: Map<string, any>;

  constructor(state: DurableObjectState) {
    this.state = state;
    this.sessions = new Map();
    this.journeys = new Map();
  }

  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);

    if (request.headers.get("Upgrade") === "websocket") {
      const pair = new WebSocketPair();
      const [client, server] = Object.values(pair);
      const portal = url.searchParams.get("portal") || "universal";

      this.sessions.set(server, { portal });
      server.accept();

      server.addEventListener("message", (event) => {
        try {
          const msg = JSON.parse(event.data as string);
          this.handleMessage(server, portal, msg);
        } catch (e) {
          console.error("Invalid message");
        }
      });

      server.addEventListener("close", () => {
        this.sessions.delete(server);
      });

      // Send initial state
      server.send(JSON.stringify({
        type: "connected",
        portal,
        journeys: Array.from(this.journeys.values())
      }));

      return new Response(null, { status: 101, webSocket: client });
    }

    // REST endpoints
    if (url.pathname === "/status") {
      const counts: Record<string, number> = {};
      this.sessions.forEach((meta) => {
        counts[meta.portal] = (counts[meta.portal] || 0) + 1;
      });
      return Response.json({ status: "ok", clients: counts, journeys: this.journeys.size });
    }

    if (url.pathname === "/journey" && request.method === "POST") {
      const body = await request.json() as any;
      const journey = {
        id: body.id || `journey-${Date.now()}`,
        user: body.user || "Anonymous",
        coordinates: body.coordinates || [],
        live: body.live !== false,
        color: body.color || "#FF1D6C"
      };
      this.journeys.set(journey.id, journey);
      this.broadcast("roadview", { type: "journey_update", journey });
      return Response.json({ success: true, journey });
    }

    return new Response("BlackRoad Realtime API", { status: 200 });
  }

  handleMessage(ws: WebSocket, portal: string, msg: any) {
    switch (msg.type) {
      case "location_update":
        let journey = this.journeys.get(msg.journeyId);
        if (!journey) {
          journey = { id: msg.journeyId, user: msg.user, coordinates: [], live: true, color: msg.color || "#FF1D6C" };
        }
        journey.coordinates.push(msg.coordinates);
        this.journeys.set(msg.journeyId, journey);
        this.broadcast("roadview", { type: "journey_update", journey });
        break;

      case "chat":
        this.broadcast("roadie", { type: "chat", from: msg.from, text: msg.text, timestamp: Date.now() });
        break;

      case "broadcast":
        this.broadcastAll({ type: "broadcast", from: portal, payload: msg.payload });
        break;
    }
  }

  broadcast(portal: string, data: any) {
    const json = JSON.stringify(data);
    this.sessions.forEach((meta, ws) => {
      if (meta.portal === portal) {
        try { ws.send(json); } catch {}
      }
    });
  }

  broadcastAll(data: any) {
    const json = JSON.stringify(data);
    this.sessions.forEach((_, ws) => {
      try { ws.send(json); } catch {}
    });
  }
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const id = env.ROOMS.idFromName("global");
    const room = env.ROOMS.get(id);
    return room.fetch(request);
  }
};
