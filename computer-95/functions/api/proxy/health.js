// /api/proxy/health · liveness probe for the agent panel.
//
// version2.hosted.html's `probeProxy()` checks that the body is exactly "ok".
// Don't change the body without updating that comparison.

export const onRequestGet = () =>
  new Response("ok", {
    headers: {
      "content-type": "text/plain; charset=utf-8",
      "cache-control": "no-store",
      "access-control-allow-origin": "*",
    },
  });
