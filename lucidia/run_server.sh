#!/usr/bin/env bash
set -euo pipefail
# Activate venv if present
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi
export LUCIDIA_MODEL_PATH="${LUCIDIA_MODEL_PATH:-./models/ggml-model.bin}"
exec uvicorn lucidia.api:app --host 127.0.0.1 --port 8080
