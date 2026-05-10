"""
Fleet router for Ollama.

Picks the first reachable host that has the requested model loaded
(`/api/ps`); falls back to a host that has it pulled (`/api/tags`);
falls back to next preferred model.

Env:
  OLLAMA_HOSTS = "127.0.0.1:11434,pi-rack-01.tail-scale.ts.net:11434"
  OLLAMA_MODELS = "roadlm:latest,qwen2.5-coder:7b,qwen2.5:3b,qwen2.5:0.5b"

No external APIs. Local Qwen across the BlackRoad fleet only.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import httpx


DEFAULT_HOSTS = ["127.0.0.1:11434"]
DEFAULT_MODELS = ["roadlm:latest", "qwen2.5-coder:7b", "qwen2.5:3b", "qwen2.5:0.5b"]


def _parse_csv(env: str | None, default: list[str]) -> list[str]:
    if not env:
        return default
    return [s.strip() for s in env.split(",") if s.strip()]


@dataclass
class Pick:
    host: str
    model: str
    loaded: bool


class Fleet:
    def __init__(self, hosts: list[str] | None = None, models: list[str] | None = None):
        self.hosts = hosts or _parse_csv(os.environ.get("OLLAMA_HOSTS"), DEFAULT_HOSTS)
        self.models = models or _parse_csv(os.environ.get("OLLAMA_MODELS"), DEFAULT_MODELS)

    async def _get(self, client: httpx.AsyncClient, host: str, path: str) -> dict | None:
        try:
            r = await client.get(f"http://{host}{path}", timeout=2.0)
            if r.status_code != 200:
                return None
            return r.json()
        except Exception:
            return None

    async def pick(self) -> Pick | None:
        async with httpx.AsyncClient() as client:
            host_state: dict[str, dict] = {}
            for host in self.hosts:
                ps = await self._get(client, host, "/api/ps")
                tags = await self._get(client, host, "/api/tags")
                if ps is None and tags is None:
                    continue
                host_state[host] = {
                    "loaded": {m["name"] for m in (ps or {}).get("models", [])},
                    "pulled": {m["name"] for m in (tags or {}).get("models", [])},
                }
            for model in self.models:
                for host in self.hosts:
                    s = host_state.get(host)
                    if s and model in s["loaded"]:
                        return Pick(host=host, model=model, loaded=True)
            for model in self.models:
                for host in self.hosts:
                    s = host_state.get(host)
                    if s and model in s["pulled"]:
                        return Pick(host=host, model=model, loaded=False)
        return None
