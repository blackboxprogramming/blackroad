// /api/proxy · agent fetch tool.
//
// Cordelia's agent loop in version2.hosted.html does
// `fetch(AGENT_PROXY + '?url=' + encodeURIComponent(u))` to read a public
// page, then folds the response into the next turn. Locally that hit a
// Python proxy on :8096; in production we run it as a Pages function.
//
// Returns: { ok, url, status, content_type, body }
//   - body is text (HTML/JSON/plain), truncated to 32 KB to keep prompts small
//   - private/loopback hosts and non-http(s) schemes are refused
//   - non-2xx upstream still resolves with ok:false so the agent can react

const ALLOW_SCHEMES = new Set(["http:", "https:"]);
const MAX_BYTES = 32 * 1024;
const TIMEOUT_MS = 10_000;

function isPrivateHost(h) {
  if (!h) return true;
  const host = h.toLowerCase();
  if (host === "localhost" || host.endsWith(".local") || host.endsWith(".internal")) return true;
  // IPv4 literals
  const m = host.match(/^(\d+)\.(\d+)\.(\d+)\.(\d+)$/);
  if (m) {
    const [a, b] = m.slice(1).map(Number);
    if (a === 10) return true;
    if (a === 127) return true;
    if (a === 0) return true;
    if (a === 169 && b === 254) return true;
    if (a === 172 && b >= 16 && b <= 31) return true;
    if (a === 192 && b === 168) return true;
  }
  // IPv6 loopback
  if (host === "::1" || host === "[::1]") return true;
  return false;
}

function json(data, init = {}) {
  return new Response(JSON.stringify(data), {
    ...init,
    headers: {
      "content-type": "application/json",
      "cache-control": "no-store",
      "access-control-allow-origin": "*",
      ...(init.headers || {}),
    },
  });
}

export const onRequestGet = async ({ request }) => {
  const url = new URL(request.url);
  const target = url.searchParams.get("url");
  if (!target) return json({ ok: false, error: "url required" }, { status: 400 });

  let u;
  try { u = new URL(target); } catch { return json({ ok: false, url: target, error: "invalid url" }, { status: 400 }); }
  if (!ALLOW_SCHEMES.has(u.protocol)) return json({ ok: false, url: target, error: "scheme not allowed" }, { status: 400 });
  if (isPrivateHost(u.hostname)) return json({ ok: false, url: target, error: "private host blocked" }, { status: 400 });

  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  let r;
  try {
    r = await fetch(u.toString(), {
      method: "GET",
      redirect: "follow",
      signal: ctrl.signal,
      headers: { "user-agent": "BlackRoad-AgentProxy/1.0 (+https://blackroad.io)" },
    });
  } catch (e) {
    clearTimeout(timer);
    return json({ ok: false, url: target, error: e.message || "fetch failed" });
  }
  clearTimeout(timer);

  const contentType = r.headers.get("content-type") || "";
  const reader = r.body?.getReader();
  let body = "";
  if (reader) {
    const dec = new TextDecoder();
    let total = 0;
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      total += value.byteLength;
      if (total > MAX_BYTES) {
        body += dec.decode(value.slice(0, MAX_BYTES - (total - value.byteLength)), { stream: false });
        try { reader.cancel(); } catch {}
        break;
      }
      body += dec.decode(value, { stream: true });
    }
    body += dec.decode();
  }

  return json({
    ok: r.ok,
    url: u.toString(),
    status: r.status,
    content_type: contentType,
    body,
    truncated: body.length >= MAX_BYTES,
  });
};

export const onRequestOptions = () =>
  new Response(null, {
    headers: {
      "access-control-allow-origin": "*",
      "access-control-allow-methods": "GET, OPTIONS",
      "access-control-allow-headers": "content-type",
    },
  });
