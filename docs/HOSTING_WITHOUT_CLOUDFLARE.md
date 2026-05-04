# Hosting BlackRoad Without Cloudflare

**Status:** Plan only. No production changes yet.
**Owner:** alexa (amundsonalexa@gmail.com / alexa@blackroad.io)
**Hard rule:** Cloudflare, Cloudflare Workers, Cloudflare Pages, and `wrangler` are **not** in the production request path of the new architecture. Old files may still mention them; the target topology must work without them.

---

## 1. Why move off Cloudflare

- Sovereignty: BlackRoad is a sovereign-stack initiative. Cloudflare sits on the critical path between every user and every product. If their account/edge/policies change, all 27 products go dark at once.
- Auditability: chain receipts and CarKeys grants want a request path we fully control. Cloudflare adds opaque hops we can't inspect.
- Cost shape: Pages + Workers + DNS + Tunnel licensing creeps. A single $6–$24/mo DigitalOcean droplet plus our own Pis is bounded and predictable.
- Vendor coupling: avoid `wrangler`-shaped tooling. Reduce a class of "it works locally / it broke in CF" failures.

This is not anti-Cloudflare on the merits. It is a deliberate move toward a topology we own end-to-end.

## 2. Target architecture (one paragraph)

Public traffic enters one or more **DigitalOcean droplets** that run **Caddy** (preferred) or **nginx** as the TLS edge and reverse proxy. The droplets terminate TLS via Let's Encrypt, then forward each request over a **private mesh** (Tailscale, Headscale, WireGuard, or SSH reverse tunnels) to a **Raspberry Pi** or local node that hosts the app. Pis are never exposed directly to the public internet. A canonical YAML registry (`infra/routes/blackroad-routes.yaml`) is the single source of truth and generates both Caddy and nginx configs.

```
[ User ]
   │
   │ HTTPS (443)
   ▼
[ DigitalOcean droplet · Caddy ]   ← public IPv4/IPv6, UFW, Let's Encrypt
   │
   │ Tailscale / Headscale / WG (private)
   ▼
[ Pi origin · PM2 / Uvicorn ]      ← app runtime, local-only ports
```

## 3. What runs where (at a glance)

- **Droplets** run only: Caddy or nginx, UFW, fail2ban, Tailscale client, Node Exporter (optional). **No app code.** The droplet is dumb on purpose — it just proxies.
- **Pis** run all the apps: Node services under PM2, FastAPI services under Uvicorn + systemd, optional MinIO/Gitea/Ollama as private internal services.
- **Static-only products** (RoadOS shell, BlackBoard atlas viewer, marketing pages) can be served by the droplet itself out of `/var/www/<product>/` if we want, but the default is "static or dynamic, doesn't matter — Pi hosts it, droplet proxies it." This keeps one model.

See `docs/PRODUCT_ROUTE_REGISTRY.md` for the per-product breakdown and `infra/routes/blackroad-routes.yaml` for the machine-readable form.

## 4. Migration approach

We are not flipping all 27 products at once. Phased:

1. **Stand up edge droplet** (`edge01.blackroad.network`) with Caddy. No DNS pointed at it yet. Health-check on droplet's bare IP.
2. **Bring two Pi origins online** through Tailscale (start with `cecilia` and `anastasia`, since they're already serving traffic).
3. **Pick one low-traffic subdomain** (recommend `detour.blackroad.io` or `roadshow.blackroad.io`). Lower its TTL to 60s 24h ahead. Cut over. Watch for an hour. Roll back if needed by re-pointing DNS to the old origin.
4. **Cut over remaining product subdomains** in batches of 3–5, one batch per day.
5. **Apex + www.blackroad.io last.**
6. **Decommission Cloudflare** only after every product has been on the new edge for 7 clean days.

Rollback at any point = repoint DNS back to the old origin. Because TTLs are 60s during cutover, rollback is observable within minutes.

## 5. What's at risk

- **Origin confidentiality of Pi IPs** — the Tailscale tailnet must be the only reachable path from droplet to Pi. UFW on the Pi must drop everything except Tailscale interface (`tailscale0`).
- **TLS automation outages** — Caddy will hit Let's Encrypt rate limits if we churn certificates during testing. Use the staging endpoint for dry runs.
- **DDoS surface** — without Cloudflare in front, the droplet IP is the absorber. Mitigations: DigitalOcean's network protections, fail2ban for SSH, rate-limits in Caddy. If a real DDoS happens, **the rollback is to put Cloudflare back in front temporarily**, accepting the violation of the hard rule as an emergency measure.
- **Email + DNS** — moving DNS off Cloudflare must not break Gmail MX, SPF, DKIM, DMARC for `blackroad.io`. These records must be migrated to whatever DNS host we pick (DigitalOcean DNS, registrar DNS) **before** flipping nameservers.

## 6. What is not changing

- Domain registrar accounts.
- Stripe, ORCID, Clerk, Gmail, Google Drive integrations (all sit at app layer, not edge layer).
- The 27-product canon.
- The chain ledger.
- Any local Pi data.

## 7. References

- `docs/NODE_INVENTORY.md` — Pis, droplets, what runs where.
- `docs/DNS_MIGRATION_PLAN.md` — record-by-record migration order.
- `docs/EDGE_ORIGIN_ARCHITECTURE.md` — diagrams and request flow.
- `docs/PRODUCT_ROUTE_REGISTRY.md` — human-readable product table.
- `infra/routes/blackroad-routes.yaml` — machine-readable canonical registry.
- `BlackRoad/infra/migration/` — prior CF→Pi migration plan (Phase 0 only). This document supersedes that plan for the *edge* layer; the prior plan still governs the *Pi readiness* prerequisites.
