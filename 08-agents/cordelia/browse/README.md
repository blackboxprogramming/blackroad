# cordelia/browse — local browsing agent backend

WebSocket server that drives a headless Playwright browser on behalf of the
Agent app in `computer-95/version2.html`.

**Runtime:** local Qwen across the BlackRoad fleet via Ollama. **No external APIs.**
Per Open Model Doctrine + `feedback_no_external_apis.md`. "Cordelia OpenAI runtime"
in canon names her *identity*, not the transport — Cordelia here is Qwen wearing
the Cordelia identity prompt.

## Phase status

- **P1 — backend skeleton:** in progress
- P2 — planner loop (Ollama tool calls, Qwen)
- P3 — wire `version2.html`
- P4 — take-over (forward client mouse/keys)
- P5 — productionize (per-task isolation, error recovery, RoadChain transcript)

## Architecture

```
client (version2.html buildAgent)        server.py (this dir)
  │                                        │
  │  ws://127.0.0.1:8769/ws  ──────────►   │
  │  {type:'message', text}                │  Playwright
  │                                        │  ────────────►  Chromium
  │  ◄────────────────────  {type:'screenshot', png_b64}
  │                                        │
  │                                        │  planner.py (P2)
  │                                        │  ────────────►  Ollama tool calls
  │                                        │                  (fleet router)
```

## Fleet routing (P2)

`OLLAMA_HOSTS` env = comma-separated list, e.g.:
```
127.0.0.1:11434,pi-rack-01.tail-scale.ts.net:11434,pi-rack-02.tail-scale.ts.net:11434
```
On each task the planner picks the **first host that has the requested model
loaded** (`/api/ps` shows loaded models). Falls back through model preference list:
`roadlm:latest → qwen2.5-coder:7b → qwen2.5:3b → qwen2.5:0.5b`.

Smaller models won't reliably tool-call; the planner detects that and surfaces
"this task needs at least qwen2.5-coder:7b loaded somewhere on the fleet."

## Run

```bash
cd /Users/alexa/blackroad/08-agents/cordelia/browse
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
python server.py
```

Server binds `127.0.0.1:8769`. Connect with any WS client.

## Wire protocol

**Client → Server**
```jsonc
{"type":"message", "text":"find capitol hill coffee shops"}
{"type":"pause"} | {"type":"resume"}
{"type":"takeover_on"} | {"type":"takeover_off"}
{"type":"input", "kind":"click", "x_pct":0.42, "y_pct":0.58}    // takeover only
{"type":"input", "kind":"type",  "text":"hello"}                 // takeover only
{"type":"tool", "name":"goto", "args":{"url":"https://..."}}    // P1 manual drive
```

**Server → Client**
```jsonc
{"type":"plan", "steps":["search", "compare", "compile"]}
{"type":"step", "idx":1, "verb":"Searched", "text":"...", "status":"active"|"done"}
{"type":"screenshot", "png_b64":"..."}                          // ~4 fps while active
{"type":"token", "delta":"..."}                                  // P2 — model stream
{"type":"done", "summary":"..."}
{"type":"error", "msg":"..."}
```
