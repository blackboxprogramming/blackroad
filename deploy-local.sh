#!/usr/bin/env bash
set -euo pipefail

DEPLOY_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$DEPLOY_ROOT"

for tool in docker python3 curl; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "Required tool missing: $tool" >&2
        exit 1
    fi
done
docker compose version >/dev/null

# Resolve and validate before pulling images, building, or starting containers.
# Missing source directories must be restored, not created as empty placeholders.
docker compose -f docker-compose.prod.yml config --format json |
    python3 scripts/deployment_preflight.py --root "$DEPLOY_ROOT"

if [[ "${1:-}" == "--check" ]]; then
    exit 0
fi
if [[ $# -ne 0 ]]; then
    echo "Usage: $0 [--check]" >&2
    exit 2
fi

docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d --wait --wait-timeout 120

# HTTP failures and timeouts must fail deployment verification.
FAILED=0
for port in 8001 8002 8003 8004 8005 8006 8007 8008; do
    if ! curl --fail --silent --show-error --connect-timeout 2 --max-time 5 \
        "http://localhost:$port/health" >/dev/null; then
        echo "Service health check failed on port $port" >&2
        FAILED=1
    fi
done
if [[ "$FAILED" -ne 0 ]]; then
    echo "Deployment verification failed. Inspect containers with docker compose -f docker-compose.prod.yml logs." >&2
    exit 1
fi

echo "Containers started and the eight HTTP health checks passed."
echo "Run integration and application workflow tests before claiming platform readiness."
