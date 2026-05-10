"""
cordelia/browse — P1 backend skeleton.

FastAPI WebSocket server on 127.0.0.1:8769. One Playwright session per connection.
P1 supports manual tool drive ({type:'tool', name, args}) and continuous screenshot
streaming. P2 will add the planner loop (Ollama tool-calls via fleet.py).

No external APIs. Local Qwen across fleet only.
"""
from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from playwright.async_api import async_playwright, Browser

from fleet import Fleet
from planner import run as planner_run
from tools import BrowseSession, dispatch


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("cordelia.browse")


_browser_lock = asyncio.Lock()
_pw = None
_browser: Browser | None = None


async def get_browser() -> Browser:
    global _pw, _browser
    async with _browser_lock:
        if _browser is None:
            _pw = await async_playwright().start()
            _browser = await _pw.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            log.info("chromium launched")
        return _browser


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    global _pw, _browser
    if _browser is not None:
        await _browser.close()
        _browser = None
    if _pw is not None:
        await _pw.stop()
        _pw = None


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    fleet = Fleet()
    pick = await fleet.pick()
    return {
        "ok": True,
        "fleet": {
            "hosts": fleet.hosts,
            "models": fleet.models,
            "pick": None if pick is None else {"host": pick.host, "model": pick.model, "loaded": pick.loaded},
        },
        "browser_running": _browser is not None,
    }


async def screenshot_loop(ws: WebSocket, session: BrowseSession, stop_evt: asyncio.Event):
    try:
        while not stop_evt.is_set():
            try:
                b64 = await session.screenshot_png_b64()
                await ws.send_text(json.dumps({"type": "screenshot", "png_b64": b64, "url": session.page.url}))
            except Exception as e:
                log.debug("screenshot loop error: %s", e)
            try:
                await asyncio.wait_for(stop_evt.wait(), timeout=0.25)
            except asyncio.TimeoutError:
                pass
    except asyncio.CancelledError:
        pass


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    log.info("ws connected from %s", ws.client)
    browser = await get_browser()
    context = await browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36 cordelia-browse/0.1",
    )
    page = await context.new_page()
    session = BrowseSession(page=page)
    stop_evt = asyncio.Event()
    snap_task = asyncio.create_task(screenshot_loop(ws, session, stop_evt))

    # P4 take-over state. The planner respects pause_evt (set = paused).
    # takeover.on means "operator drives" — planner is auto-paused; new
    # message tasks are rejected; raw input messages are replayed via Playwright.
    pause_evt = asyncio.Event()       # set → paused
    takeover = {"on": False}

    async def emit(payload: dict):
        await ws.send_text(json.dumps(payload))

    try:
        await emit({"type": "ready", "viewport": {"width": 1280, "height": 800}})
        await session.goto("about:blank")

        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await emit({"type": "error", "msg": "invalid json"})
                continue

            mtype = msg.get("type")

            if mtype == "tool":
                name = msg.get("name")
                args = msg.get("args") or {}
                await emit({"type": "step", "verb": name.upper() if name else "?", "text": json.dumps(args), "status": "active"})
                result = await dispatch(session, name, args)
                await emit({"type": "tool_result", "name": name, "result": result})
                await emit({"type": "step", "verb": name.upper() if name else "?", "text": json.dumps(args), "status": "done"})

            elif mtype == "message":
                if takeover["on"]:
                    await emit({"type": "error", "msg": "operator has taken over — release with takeover_off first"})
                    continue
                text = (msg.get("text") or "").strip()
                if not text:
                    await emit({"type": "error", "msg": "empty message"})
                    continue
                fleet = Fleet()
                pick = await fleet.pick()
                if pick is None:
                    await emit({
                        "type": "error",
                        "msg": "no fleet host has any preferred model. "
                               f"hosts={fleet.hosts} models={fleet.models}",
                    })
                    continue
                try:
                    await planner_run(text, session, pick, emit, pause_evt=pause_evt)
                except Exception as e:
                    log.exception("planner failed")
                    await emit({"type": "error", "msg": f"planner: {type(e).__name__}: {e}"})

            elif mtype == "pause":
                pause_evt.set()
                await emit({"type": "paused"})

            elif mtype == "resume":
                pause_evt.clear()
                await emit({"type": "resumed"})

            elif mtype == "takeover_on":
                takeover["on"] = True
                pause_evt.set()
                await emit({"type": "takeover", "on": True})

            elif mtype == "takeover_off":
                takeover["on"] = False
                pause_evt.clear()
                await emit({"type": "takeover", "on": False})

            elif mtype == "input":
                if not takeover["on"]:
                    await emit({"type": "error", "msg": "input ignored — takeover_on first"})
                    continue
                kind = msg.get("kind")
                try:
                    if kind == "move":
                        await session.takeover_move(float(msg["x_pct"]), float(msg["y_pct"]))
                    elif kind == "click":
                        await session.takeover_click(float(msg["x_pct"]), float(msg["y_pct"]),
                                                     button=msg.get("button", "left"))
                    elif kind == "scroll":
                        await session.takeover_scroll(int(msg.get("dy", 0)))
                    elif kind == "type":
                        await session.takeover_type(str(msg.get("text", "")))
                    elif kind == "key":
                        await session.takeover_key(str(msg.get("code", "")))
                    else:
                        await emit({"type": "error", "msg": f"unknown input kind: {kind}"})
                except Exception as e:
                    await emit({"type": "error", "msg": f"input {kind}: {type(e).__name__}: {e}"})

            elif mtype == "ping":
                await emit({"type": "pong"})

            else:
                await emit({"type": "error", "msg": f"unknown type: {mtype}"})

    except WebSocketDisconnect:
        log.info("ws disconnected")
    except Exception as e:
        log.exception("ws error")
        try:
            await ws.send_text(json.dumps({"type": "error", "msg": f"{type(e).__name__}: {e}"}))
        except Exception:
            pass
    finally:
        stop_evt.set()
        snap_task.cancel()
        try:
            await context.close()
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8769, log_level="info")
