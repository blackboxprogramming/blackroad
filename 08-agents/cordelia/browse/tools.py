"""
Playwright tool wrappers for cordelia/browse.

Each tool returns {"ok": bool, "result": Any, "url": str, "title": str, "error"?: str}.
The planner (P2) sees these as JSON tool results.
"""
from __future__ import annotations

import asyncio
import base64
from dataclasses import dataclass
from typing import Any

from playwright.async_api import Page, TimeoutError as PWTimeout


SEARCH_URL_TMPL = "https://html.duckduckgo.com/html/?q={q}"


@dataclass
class BrowseSession:
    page: Page

    async def _wrap(self, coro_factory, *, label: str) -> dict[str, Any]:
        try:
            result = await coro_factory()
        except PWTimeout as e:
            return {"ok": False, "error": f"{label} timed out: {e}", "url": self.page.url, "title": ""}
        except Exception as e:
            return {"ok": False, "error": f"{label}: {type(e).__name__}: {e}", "url": self.page.url, "title": ""}
        return {
            "ok": True,
            "result": result,
            "url": self.page.url,
            "title": (await self.page.title()) or "",
        }

    async def goto(self, url: str) -> dict[str, Any]:
        async def run():
            await self.page.goto(url, wait_until="domcontentloaded", timeout=20_000)
            return None
        return await self._wrap(run, label="goto")

    async def search(self, query: str) -> dict[str, Any]:
        from urllib.parse import quote_plus
        return await self.goto(SEARCH_URL_TMPL.format(q=quote_plus(query)))

    async def click(self, x_pct: float, y_pct: float) -> dict[str, Any]:
        async def run():
            vp = self.page.viewport_size or {"width": 1280, "height": 800}
            x = int(vp["width"] * x_pct)
            y = int(vp["height"] * y_pct)
            await self.page.mouse.move(x, y)
            await self.page.mouse.click(x, y)
            await self.page.wait_for_load_state("domcontentloaded", timeout=8_000)
            return {"x": x, "y": y}
        return await self._wrap(run, label="click")

    async def type_text(self, text: str, submit: bool = False) -> dict[str, Any]:
        async def run():
            await self.page.keyboard.type(text, delay=20)
            if submit:
                await self.page.keyboard.press("Enter")
                await self.page.wait_for_load_state("domcontentloaded", timeout=10_000)
            return {"typed": text, "submitted": submit}
        return await self._wrap(run, label="type")

    async def scroll(self, dy: int) -> dict[str, Any]:
        async def run():
            await self.page.mouse.wheel(0, dy)
            await asyncio.sleep(0.15)
            return {"dy": dy}
        return await self._wrap(run, label="scroll")

    async def extract(self, selector: str | None = None, max_chars: int = 4000) -> dict[str, Any]:
        async def run():
            if selector:
                txt = await self.page.locator(selector).first.inner_text(timeout=5_000)
            else:
                txt = await self.page.locator("body").inner_text(timeout=5_000)
            return txt[:max_chars]
        return await self._wrap(run, label="extract")

    async def screenshot_png_b64(self) -> str:
        png = await self.page.screenshot(type="png", full_page=False)
        return base64.b64encode(png).decode("ascii")

    # ── Take-over input replay (P4) ──
    # The client forwards normalized (x_pct, y_pct) coords + key codes from
    # the live screenshot canvas. We translate to viewport pixels and replay
    # via Playwright. No "wait_for_load_state" here — operator drives the
    # cadence and clicks may not navigate.

    def _xy(self, x_pct: float, y_pct: float) -> tuple[int, int]:
        vp = self.page.viewport_size or {"width": 1280, "height": 800}
        return int(vp["width"] * x_pct), int(vp["height"] * y_pct)

    async def takeover_move(self, x_pct: float, y_pct: float) -> None:
        x, y = self._xy(x_pct, y_pct)
        await self.page.mouse.move(x, y)

    async def takeover_click(self, x_pct: float, y_pct: float, button: str = "left") -> None:
        x, y = self._xy(x_pct, y_pct)
        await self.page.mouse.click(x, y, button=button)

    async def takeover_scroll(self, dy: int) -> None:
        await self.page.mouse.wheel(0, dy)

    async def takeover_type(self, text: str) -> None:
        await self.page.keyboard.type(text, delay=15)

    async def takeover_key(self, code: str) -> None:
        # Playwright uses values like "Enter", "Tab", "ArrowDown", "Backspace".
        await self.page.keyboard.press(code)


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "Run a web search and load the results page.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "goto",
            "description": "Navigate to a URL.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "click",
            "description": "Click at a viewport-relative coordinate (0.0-1.0).",
            "parameters": {
                "type": "object",
                "properties": {
                    "x_pct": {"type": "number"},
                    "y_pct": {"type": "number"},
                },
                "required": ["x_pct", "y_pct"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "type",
            "description": "Type text into the focused element. Set submit=true to press Enter after.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "submit": {"type": "boolean"},
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "scroll",
            "description": "Scroll the page by dy pixels (positive=down).",
            "parameters": {
                "type": "object",
                "properties": {"dy": {"type": "integer"}},
                "required": ["dy"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "extract",
            "description": "Read page text. Optional CSS selector, otherwise body.",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string"},
                    "max_chars": {"type": "integer"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "done",
            "description": "Finish the task and report a final summary to the user.",
            "parameters": {
                "type": "object",
                "properties": {"summary": {"type": "string"}},
                "required": ["summary"],
            },
        },
    },
]


async def dispatch(session: BrowseSession, name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "search":
        return await session.search(args["query"])
    if name == "goto":
        return await session.goto(args["url"])
    if name == "click":
        return await session.click(float(args["x_pct"]), float(args["y_pct"]))
    if name == "type":
        return await session.type_text(args["text"], bool(args.get("submit", False)))
    if name == "scroll":
        return await session.scroll(int(args["dy"]))
    if name == "extract":
        return await session.extract(args.get("selector"), int(args.get("max_chars", 4000)))
    return {"ok": False, "error": f"unknown tool: {name}", "url": "", "title": ""}
