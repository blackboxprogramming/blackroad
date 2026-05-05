# Lucidia — Local Copilot PoC

Lucidia is a local, semi‑autonomous personal Copilot PoC. This repo creates a skeleton for a safe Lucidia that runs on Apple Silicon.

Quickstart:
1. cd lucidia
2. ./setup.sh
3. Place a quantized ggml model into lucidia/models/ and set LUCIDIA_MODEL_PATH env var
4. ./run_server.sh
Endpoints:
- POST /chat { "prompt": "..." }
- POST /suggest_action { "prompt": "..." } -> returns suggested shell command (won't execute without approval)

Safety:
- By default Lucidia suggests actions; execution requires explicit approval.
