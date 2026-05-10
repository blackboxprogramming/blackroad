"""
Planner loop using Ollama tool-calling.

Drives a BrowseSession by sending the conversation + tool schemas to the
fleet-selected Qwen model, parsing tool_calls, dispatching to Playwright,
and looping until the model calls `done` or the step cap is hit.

No external APIs. Local Ollama only.
"""
from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from fleet import Fleet, Pick
from identity import build_system_prompt
from tools import TOOL_SCHEMAS, BrowseSession, dispatch


log = logging.getLogger("cordelia.planner")

MAX_STEPS = 12
HTTP_TIMEOUT = 120.0  # 7B cold-load can be slow per memory


EmitFn = Callable[[dict[str, Any]], Awaitable[None]]


class PlannerError(Exception):
    pass


async def _post_chat(host: str, body: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        r = await client.post(f"http://{host}/api/chat", json=body)
        if r.status_code != 200:
            raise PlannerError(f"ollama {host} /api/chat -> {r.status_code} {r.text[:300]}")
        return r.json()


def _normalize_tool_call(tc: dict[str, Any]) -> tuple[str, dict[str, Any], str]:
    """Ollama returns {function:{name, arguments:{...}}}. Sometimes arguments arrives
    as a JSON string. Normalize both shapes. Returns (name, args, call_id)."""
    fn = tc.get("function") or {}
    name = fn.get("name") or tc.get("name") or ""
    args = fn.get("arguments")
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            args = {}
    if not isinstance(args, dict):
        args = {}
    call_id = tc.get("id") or ""
    return name, args, call_id


async def run(
    text: str,
    session: BrowseSession,
    pick: Pick,
    emit: EmitFn,
    *,
    max_steps: int = MAX_STEPS,
) -> None:
    system = build_system_prompt(operator_name="Alexa", task_hint="version2.html Agent app")
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": text},
    ]

    await emit({"type": "plan", "model": pick.model, "host": pick.host})

    for step_idx in range(max_steps):
        body = {
            "model": pick.model,
            "messages": messages,
            "tools": TOOL_SCHEMAS,
            "stream": False,
            "options": {"temperature": 0.2, "num_ctx": 8192},
        }
        try:
            j = await _post_chat(pick.host, body)
        except PlannerError as e:
            await emit({"type": "error", "msg": str(e)})
            return

        msg = j.get("message") or {}
        content = (msg.get("content") or "").strip()
        tool_calls = msg.get("tool_calls") or []

        if content and not tool_calls:
            await emit({"type": "token", "delta": content})

        if not tool_calls:
            await emit({"type": "done", "summary": content or "(no tool calls; model returned plain text only)"})
            return

        messages.append({"role": "assistant", "content": content, "tool_calls": tool_calls})

        for tc in tool_calls:
            name, args, _call_id = _normalize_tool_call(tc)
            await emit({
                "type": "step",
                "idx": step_idx,
                "verb": (name or "?").upper(),
                "text": json.dumps(args)[:240],
                "status": "active",
            })

            if name == "done":
                summary = str(args.get("summary") or content or "(done)")
                await emit({"type": "step", "idx": step_idx, "verb": "DONE", "text": summary[:240], "status": "done"})
                await emit({"type": "done", "summary": summary})
                return

            result = await dispatch(session, name, args)
            messages.append({
                "role": "tool",
                "content": json.dumps(result)[:6000],
                "name": name,
            })
            await emit({
                "type": "step",
                "idx": step_idx,
                "verb": (name or "?").upper(),
                "text": (result.get("error") or result.get("url") or "ok")[:240],
                "status": "done",
            })
            await asyncio.sleep(0)

    await emit({"type": "error", "msg": f"max steps ({max_steps}) reached without done()"})


async def select_fleet(fleet: Fleet | None = None) -> Pick | None:
    return await (fleet or Fleet()).pick()
