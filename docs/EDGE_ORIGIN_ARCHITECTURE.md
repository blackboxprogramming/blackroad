# Edge / Origin Architecture

**Status:** Plan only.

## Request flow

```
                                                ┌─────────────────────────────────────┐
                                                │  Public DNS (DigitalOcean DNS)      │
                                                │   *.blackroad.io  ->  edge01 IPv4   │
                                                └──────────────┬──────────────────────┘
                                                               │ (A/AAAA)
                                                               ▼
  ┌──────────┐    HTTPS 443      ┌──────────────────────────────────────────────┐
  │  client  │ ─────────────────►│  edge01  (DigitalOcean droplet, Ubuntu)      │
  │ browser  │                   │  - Caddy (TLS, reverse proxy, HTTP/2/3)      │
  │ or CLI   │                   │  - UFW: allow 22,80,443; deny app ports      │
  └──────────┘                   │  - Tailscale client (private)                │
                                 │  - fail2ban (ssh)                            │
                                 └──────────────┬───────────────────────────────┘
                                                │ Tailscale (100.x.y.z) on tailscale0
                                                ▼
                            ┌──────────────────────────────────────────────────┐
                            │  Pi origins (private)                            │
                            │   anastasia, cecilia, lucidia, ...               │
                            │   - PM2 (Node apps)                              │
                            │   - systemd + Uvicorn (FastAPI apps)             │
                            │   - UFW: allow tailscale0 only                   │
                            │   - Local app ports: 3000, 3010, 8000, ...       │
                            └──────────────────────────────────────────────────┘
```

## Why this shape

- **One TLS termination point.** Caddy on the droplet handles every cert. Pis never see the public internet, never run certbot, never expose 443.
- **Host-based routing at the edge.** Caddy uses the `Host:` header to pick the origin. The route table is generated from `infra/routes/blackroad-routes.yaml`.
- **Mesh, not tunnels.** Tailscale-style mesh networking gives each Pi a stable private IP that the droplet (also on the tailnet) can reach. No port-forwarding, no public Pi IPs, no UPnP.
- **Single source of truth.** The YAML route registry generates Caddyfile and nginx.conf. Don't hand-edit either generated file.

## Layers

### Edge layer (droplet)

- **OS:** Ubuntu 24.04 LTS.
- **Reverse proxy:** Caddy (recommended) or nginx. Pick exactly one; do not run both bound to 80/443.
- **TLS:** Let's Encrypt automatic via Caddy. With nginx, certbot --nginx.
- **Firewall:** UFW. Allow 22 (SSH, key-only), 80 (HTTP→HTTPS redirect), 443. Deny everything else inbound. Outbound unrestricted.
- **Mesh:** Tailscale client. Joined to the BlackRoad tailnet. Tagged `tag:edge`.
- **Logs:** Caddy access log to `/var/log/caddy/access.log`; rotated by logrotate.
- **No app code on the droplet.** Treat it as cattle.

### Mesh layer

- **Default:** Tailscale. Free tier covers our node count. ACLs restrict `tag:edge` → `tag:origin` on the specific app ports.
- **Sovereign alternative:** Headscale on a small VM (could even be the droplet itself, but split if it gets busy).
- **Fallback:** WireGuard with manual key distribution. Use only if both above fail.
- **Never:** SSH reverse tunnels in the steady state. Acceptable as a one-off bridge during initial bring-up.

### Origin layer (Pis)

- **Process supervision:**
  - Node services → PM2 (`pm2 start`, `pm2 startup`, `pm2 save`).
  - Python services → systemd unit + Uvicorn (`uvicorn app:app --host 127.0.0.1 --port N`).
- **Bind to localhost or tailnet only.** Never `0.0.0.0` for app ports.
- **Health endpoints:** every app must expose `/health` or `/api/health` returning 200 with a small JSON body. Caddy uses these for active probes.
- **Resource ceilings:** Pis are small. Set PM2 `max_memory_restart` and Uvicorn `--workers` conservatively.

### Storage / data

- App data stays on Pis (SQLite for most BlackRoad services).
- Backups go to MinIO on a designated Pi (or external NAS) via cron.
- Object storage that was previously on Cloudflare R2 needs a migration plan to MinIO. This is **out of scope** for this document — see a separate `docs/STORAGE_MIGRATION.md` (not yet written).

## How a request resolves (concrete walk-through)

User hits `https://roadtrip.blackroad.io/`:

1. Browser resolves `roadtrip.blackroad.io` → `edge01` public IP via DigitalOcean DNS.
2. TCP/TLS to `edge01:443`. Caddy presents the Let's Encrypt cert for `roadtrip.blackroad.io` (or wildcard, see "Wildcards" below).
3. Caddy reads the `Host:` header, looks up the matching site block (generated from YAML), and reverse-proxies to `http://anastasia:3000/` (Tailscale hostname).
4. Tailscale routes the connection over the encrypted mesh to anastasia's tailnet IP.
5. PM2-managed Node process on anastasia handles the request, returns the response.
6. Caddy returns the response over TLS to the browser.

## Wildcards

Two options for `*.blackroad.io`:

- **Per-host certs (recommended for clarity).** Caddy issues one cert per product subdomain via HTTP-01 challenge. No DNS-01 needed. Each cert is independent.
- **Wildcard cert (`*.blackroad.io`).** Requires DNS-01 challenge, which means giving Caddy API access to the DNS provider. Useful if we add subdomains often, but it's another credential to manage.

Default: per-host certs. Switch to wildcard only when we have >40 subdomains.

## Failure modes and what each looks like

| failure | symptom | mitigation |
|---|---|---|
| Droplet down | every product subdomain returns connection refused | (a) bring droplet back; (b) standby `edge02` exists; (c) DNS rollback to old origin |
| Pi origin down | only that product's host 502s | Caddy can have a fallback handler returning a maintenance page; restart Pi or PM2/systemd unit |
| Tailscale auth expired on droplet | all proxied traffic 502s; droplet itself reachable | `sudo tailscale up --authkey=<re-auth>` |
| Let's Encrypt rate-limit | new cert issuance fails; existing certs still valid | use Let's Encrypt staging endpoint for testing; wait out the rate-limit window |
| DDoS at the edge | droplet saturates | fail2ban + Caddy rate-limits as first line; emergency-only fallback is to put Cloudflare back in front for a short window |

## Operational model

- **Edge is cattle.** Reprovision from scratch via `infra/digitalocean/bootstrap-edge.sh` if anything is weird.
- **Pis are pets.** They have data and identity. Bootstrap with `infra/pi/bootstrap-origin-node.sh`. Never `rm -rf` casually.
- **Configs come from YAML.** Hand-editing Caddyfile or nginx.conf in production is forbidden; edit YAML, regenerate, deploy.
- **Health checks are the contract.** If `/health` is missing on a service, the service is not deployable through this edge.
