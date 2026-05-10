"""
Full-flow smoke: send {type:'message', text} and watch the planner drive tools
via local Qwen until done. Override OLLAMA_MODELS to test specific models.
"""
import asyncio
import json
import os
import sys
import time


async def main():
    try:
        from websockets.asyncio.client import connect  # type: ignore
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "websockets"])
        from websockets.asyncio.client import connect  # type: ignore

    prompt = sys.argv[1] if len(sys.argv) > 1 else (
        "Open example.com and tell me the H1 heading text. Use the browser tools."
    )

    counts = {"step": 0, "screenshot": 0, "token": 0, "done": 0, "error": 0, "plan": 0, "ready": 0}
    transcript: list[str] = []
    t0 = time.time()

    async with connect("ws://127.0.0.1:8769/ws", max_size=8 * 1024 * 1024) as ws:
        await ws.send(json.dumps({"type": "message", "text": prompt}))

        while True:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=180.0)
            except asyncio.TimeoutError:
                print("\n[timeout]")
                break
            msg = json.loads(raw)
            t = msg.get("type", "?")
            counts[t] = counts.get(t, 0) + 1
            elapsed = f"{time.time() - t0:5.1f}s"
            if t == "step":
                print(f"[{elapsed}] step  {msg.get('verb')} status={msg.get('status')} text={msg.get('text','')[:120]}")
                transcript.append(f"step {msg.get('verb')} {msg.get('status')}")
            elif t == "plan":
                print(f"[{elapsed}] plan  model={msg.get('model')} host={msg.get('host')}")
            elif t == "token":
                d = msg.get("delta", "")
                print(f"[{elapsed}] token {d[:200]}")
            elif t == "done":
                print(f"[{elapsed}] DONE  {msg.get('summary','')[:400]}")
                break
            elif t == "error":
                print(f"[{elapsed}] ERROR {msg.get('msg')}")
                break
            elif t == "screenshot":
                if counts["screenshot"] % 10 == 0:
                    print(f"[{elapsed}] screenshot {counts['screenshot']}  url={msg.get('url','')[:80]}")
            elif t == "ready":
                print(f"[{elapsed}] ready")

    print()
    print("counts:", counts)
    print("ok" if counts.get("done") and not counts.get("error") else "FAIL")


if __name__ == "__main__":
    asyncio.run(main())
