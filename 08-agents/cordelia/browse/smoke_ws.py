"""
Quick WS smoke test: connect, send goto tool, count screenshots, decode tool_result.
Run with the venv active. Server must be on 127.0.0.1:8769.
"""
import asyncio
import json
import sys

import httpx


async def main():
    # tiny inline WS client using httpx-ws not available; use websockets if installed,
    # else fall back to a vanilla asyncio implementation.
    try:
        from websockets.asyncio.client import connect  # type: ignore
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "websockets"])
        from websockets.asyncio.client import connect  # type: ignore

    counts = {"screenshot": 0, "tool_result": 0, "step": 0, "ready": 0, "error": 0, "other": 0}
    last_url = ""

    async with connect("ws://127.0.0.1:8769/ws") as ws:
        await ws.send(json.dumps({"type": "tool", "name": "goto", "args": {"url": "https://example.com"}}))

        async def reader():
            async for raw in ws:
                msg = json.loads(raw)
                t = msg.get("type", "other")
                counts[t] = counts.get(t, 0) + 1
                if t == "tool_result":
                    print("tool_result:", json.dumps(msg.get("result", {}), indent=2)[:600])
                if t == "screenshot":
                    nonlocal_url = msg.get("url", "")
                    if nonlocal_url:
                        sys.stdout.write(f"\rscreenshots={counts['screenshot']} url={nonlocal_url[:80]}      ")
                        sys.stdout.flush()
                if t == "error":
                    print("ERROR:", msg)

        try:
            await asyncio.wait_for(reader(), timeout=6.0)
        except asyncio.TimeoutError:
            pass

    print()
    print("counts:", counts)
    if counts["screenshot"] >= 3 and counts["tool_result"] == 1:
        print("SMOKE OK")
        return 0
    print("SMOKE FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()) or 0)
