# Node Inventory

**Status:** Plan-time inventory. Field values marked `TBD` need on-node confirmation.
**Source of truth:** this file is the human-readable companion to `infra/routes/blackroad-routes.yaml`. When they conflict, the YAML wins for routing; this file wins for ownership/notes.

## Conventions

- `role` — one of `edge` (public TLS proxy), `origin` (private app host), `infra` (private support service), `dev` (operator workstation).
- `mesh_addr` — Tailscale/Headscale address used by the edge to reach the node. Never a public IP.
- `public_addr` — only set for edge nodes.
- `os` — kernel/distro shorthand.
- All disk and capacity values are **as of the last live check noted in memory** and need re-verification before cutover.

---

## Edge layer (DigitalOcean)

| name | role | public_addr | mesh_addr | os | runtime | status |
|---|---|---|---|---|---|---|
| edge01 | edge | TBD (provision) | TBD | Ubuntu 24.04 LTS | Caddy + UFW + Tailscale | not-yet-provisioned |
| edge02 | edge (backup, optional) | TBD | TBD | Ubuntu 24.04 LTS | Caddy + UFW + Tailscale | not-yet-provisioned |

Plan: provision `edge01` first. `edge02` is added only if we want active/passive failover. For 27 products at current traffic, one droplet is enough.

## Origin layer (live inventory — captured 2026-05-01, post Pi reboot)

### Confirmed via `ssh + key=id_ed25519, user=alexa`

| host | hardware | OS | root disk | USB peripherals | tailnet | notes |
|---|---|---|---|---|---|---|
| **anastasia** | **DigitalOcean droplet** (vdb=`iso9660 config-2` cloud-init signature) | CentOS Stream 9 x86_64 | xfs **74%** (6.5G free) | none (VM) | ✅ on `tailf220f7.ts.net` | already a DO droplet — could be edge AND/OR origin. Many services bound `0.0.0.0` — hardening required. |
| **cecilia** | **Pi 5** (`rpt-2712`) + NVMe SSD (boot SD, root NVMe) | Debian 13 trixie | nvme0n1p2 ext4 **55%** (180.1G free) | TONOR TC-777 USB mic | ⚠ tailscaled inactive after reboot | healthiest Pi; agent-react service active. |
| **lucidia** | **Pi 5** (`rpt-2712`) | Debian 12 bookworm | mmcblk0p2 ext4 **37%** (136.2G free) | none | ⚠ shows online via 100.66.235.47 but SSH timeout there; LAN at 192.168.4.38 works | **most underused — best origin candidate.** |
| **alice** | **Pi 400** (built-in keyboard ID 04d9:0007 + microSD reader) | Raspbian 11 bullseye | mmcblk0p2 ext4 **100% FULL** | RPi keyboard, SuperTop microSD reader, VIA Labs USB hub | ⚠ tailscaled active but offline on tailnet | **excluded from serving — disk full**. Reboot did not free anything. |
| **aria** | **Pi 5** (`rpt-2712`) | Debian 12 bookworm | mmcblk0p2 ext4 **92%** (975MB free) | none | ⚠ tailscaled active but offline on tailnet | constrained. |

### Reachable on LAN, SSH not accepting our key

| host | reason | notes |
|---|---|---|
| `gaia` | SSH up, key permission denied | uses a different key — likely Pi-default key. Reachable per earlier interactive ssh. |
| `192.168.4.112` | SSH up, key permission denied for all 5 users | unknown device on LAN; not in our SSH config. |

### Public IP (not LAN), connection refused

| host | IP | what we know |
|---|---|---|
| `gematria` | `159.65.43.12` (DigitalOcean range) | pings 45ms, sshd not listening, no HTTP/HTTPS, no rDNS. Could be: stale/recycled IP, powered-off droplet, or firewalled. **Confirm via DO dashboard / `doctl compute droplet list` whether we own it.** |

### LAN-alive (per Mac ARP) but no SSH after reboot

| host | LAN IP | status |
|---|---|---|
| octavia, calliope, olympia, cadence | `192.168.4.{101,120,111,121}` | ARP `(incomplete)` from this Mac, nmap `-sn -PR` no MAC reply. Could be Wi-Fi isolation, slow boot, or sshd not enabled at boot. **Need physical attention or to wait longer.** |

### Doesn't resolve / unknown

- `colliope` — likely typo for `calliope` (which is one of the timeouts above).

### Bonjour/mDNS gotcha — IMPORTANT

`*.local` hostnames `alice.local`, `aria.local`, `blackroad.local`, `lucidia.local` and `blackroad` (no suffix) **all resolve back to this Mac (`lucidia-operator`)**. SSHing to those names lands on this very machine, not the named Pi. Always use the short hostname (per `~/.ssh/config`) or the LAN IP.

Tailnet: **`tailf220f7.ts.net`** (confirmed from `anastasia tailscale status`).
Operator workstation `alexandria` is on it (this Mac, `100.117.200.23`).

| ssh_target | type | mesh_addr | os | disk | online | role / notes |
|---|---|---|---|---|---|---|
| `anastasia`   | **VM (CentOS Stream 9, x86_64)** — not a Pi | `100.94.33.37` | CentOS 9 | 25G/19G **75%** | ✅ online (up 17 weeks) | Real app: **blackroad-api on :8000** (FastAPI, /health JSON). **:3000 is just `Hello World from shellfish-droplet` — the BlackRoad monolith is NOT running here.** Also: Ollama on :11434, redis-imitator (python3) on `0.0.0.0:6379`, custom DNS on `:53`, several public-bound python services. **Hardening required before fronting any product traffic.** |
| `cecilia`     | Pi 5 (rpi-2712 aarch64) | local (offline tailnet) | Debian 13 trixie | 457G/254G **59%** | ⚠ SSH ok via local LAN; **Tailscale offline 17d** | 8GB RAM. `agent-react.service` active. llama-server on :8081. Many python services on `0.0.0.0:8082..8094`. Not on tailnet → **not reachable from a future DigitalOcean edge** until we re-auth Tailscale. |
| `lucidia`     | Linux node | `100.66.235.47` | TBD | TBD | ✅ online | Lucidia agent stack — needs probe |
| `alice`       | Linux node | `100.77.210.18` | TBD | TBD | ❌ offline 14d on tailnet | Excluded from serving (memory: disk full, Hailo-8 paper) |
| `aria`        | Linux node | `100.109.14.17` | TBD | TBD | ❌ offline 14d on tailnet | Constrained (memory: 96% disk) |
| `octavia`     | Linux node | `100.83.149.86` | TBD | TBD | ❌ offline 41d on tailnet | needs reconnect |
| `gematria`, `colliope`, `calliope`, `gaia`, `olympia`, `blackroad`, `cadence` | TBD | not seen in tailscale status | TBD | TBD | ❓ likely never on this tailnet | needs Tailscale onboarding before any can be an origin |
| `codex-infinity` | Linux node | `100.108.132.8` | TBD | TBD | ✅ online | unknown role, not in original SSH list |
| `iphone171`   | iOS | `100.77.186.122` | iOS | n/a | ✅ online | not an origin |

**Key revision to the plan:** the route registry assumed all 27 products were already served by a Node monolith on `anastasia:3000`. **They aren't.** The `computer-95` Next.js app is currently on **Cloudflare Pages** (per memory: project `blackroad-os-prism`). Before any subdomain can be cut over, the monolith must be deployed onto an origin node.

## Optional infrastructure services

These are private internal services on the Pi side. Not user-facing.

| service | host_candidate | mesh_port | purpose | status |
|---|---|---|---|---|
| MinIO   | TBD (large-disk Pi or NAS) | 9000 / 9001 | S3-compat object store; replaces R2 dependency | optional |
| Gitea   | TBD                        | 3000        | code mirror + private repos                    | optional |
| Ollama  | `anastasia` (already running) | 11434    | local LM serving                                | active   |
| Postgres | TBD                       | 5432        | SQL store if we move off SQLite                | optional |
| Redis   | `anastasia` (running on 0.0.0.0:6379 — **must rebind to tailnet only before adding services**) | 6379 | cache / queues | active-but-needs-hardening |

## Apps that need PM2

These are Node-runtime products and back-ends. Each gets a PM2 entry in `infra/pi/pm2/ecosystem.config.cjs`.

- RoadOS (static shell can be Caddy-served, but PM2 if SSR needed)
- RoadCode, RoadTrip, RoadSide, RoadView, RoadShow, RoadStream, RoadWire, RoadWorld, OfficeRoad, RoadSport, RoadBand, RoadShow, RoadMap, RoundAbout, BackRoad, BlackBoard, GloveBox, OneWay, CarPool, CarKeys, RoadCoin, RoadBook, RoadWork, RoadChain, HighWay, Detour, PitStop — all currently Next.js / Node services in `~/blackroad/computer-95`.

In practice they share **one** Node process today (the computer-95 monolith). The host-based routing happens at Caddy. So PM2 only needs **one** entry per Pi running the monolith — not 27 entries — until we split them.

## Apps that need Uvicorn / FastAPI

- `blackroad-api` (currently running on `anastasia`).
- Any future Python services (RoadMath/TriPascal verifier may end up here).

These get systemd units in `infra/pi/systemd/`. Examples scaffolded in `infra/pi/uvicorn/`.

## Static-only products

- Marketing/landing HTML pages (e.g., `b.html`, `audit.html`, root domain landings) — Caddy can serve these directly from the droplet to skip a Pi hop. Not required, but cheap.

## What needs confirmation before cutover

1. Mesh address per Pi (run discovery script).
2. Free disk per Pi (must clear `aria`).
3. Tailscale tailnet membership (all serving Pis must be in one tailnet).
4. Systemd / PM2 unit names per app.
5. Listening ports per app (none should be on `0.0.0.0` after hardening).
