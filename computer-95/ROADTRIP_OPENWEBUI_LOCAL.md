# RoadTrip × Open WebUI — Local AI Cockpit

RoadTrip is the **solo command room** where one operator works with their
27 native BlackRoad agents. Open WebUI is **not** RoadTrip — it is the
local model cockpit (Ollama UI) that RoadTrip can launch or embed when
running locally.

## Roles

- **RoadTrip** — BlackRoad agent dispatch / control surface (this UI).
- **CarPool** — collaboration surface for other people + outside agents.
- **Open WebUI** — local model runtime UI (chat with Ollama models).
- **Ollama** — local model server backing Open WebUI.

RoadTrip should **launch and control** Open WebUI; it does not become
Open WebUI.

## Local URLs

| Service     | URL                       |
|-------------|---------------------------|
| Open WebUI  | `http://localhost:3000`   |
| Gitea       | `http://localhost:3030`   |

Gitea avoids port `3000` (Open WebUI owns it). The `docker-compose.yml`
in `blackroad-gitea` already maps Gitea to host `3030` → container `3000`.

## How the launcher works

In `roadtrip.html` the topbar shows an **AI Cockpit** button. Clicking it:

1. If the page is being served from `localhost` / `127.0.0.1` / `file://`,
   it opens a modal with an `<iframe>` of `http://localhost:3000` and a
   visible "Open in new tab" link as a fallback.
2. If the page is served from a public host (Cloudflare Pages, etc.),
   the button simply opens `http://localhost:3000` in a new tab — the
   public page never tries to fetch localhost from its own context.
3. If the iframe cannot reach Open WebUI, a fallback panel appears with
   a direct link and model suggestions.

The launcher is additive and reversible — if Open WebUI is offline the
rest of RoadTrip is unaffected.

## Suggested local models

- `qwen2.5-coder:7b` — coding
- `qwen2.5:3b` — lighter chat
- `roadlm:latest` — BlackRoad-flavored local responses
- `nomic-embed-text:latest` — embeddings / search (not chat)

## Safety notes

- Do **not** expose local Open WebUI publicly without auth, a tunnel,
  and a security review.
- Do **not** commit `.env`, tokens, model weights, or Docker data.
- This integration intentionally does **not** copy Open WebUI source
  code — it links/embeds the running local instance.
