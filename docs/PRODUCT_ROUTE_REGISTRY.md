# Product Route Registry (human-readable)

**Source of truth:** `infra/routes/blackroad-routes.yaml`. This file is a flattened view for humans. When they conflict, the YAML wins.

**Status legend:**
- `needs-origin-confirmation` — placeholder origin; must be confirmed on the Pi before cutover.
- `ready` — origin confirmed, health-checks pass.
- `live` — running through the new edge.

---

| # | name | host | runtime | origin (Pi · port) | health | repo guess | owner org guess | status |
|---|---|---|---|---|---|---|---|---|
| 1  | RoadOS      | os.blackroad.io          | static + node | anastasia · 3000 | /health      | computer-95              | BlackRoad-OS       | needs-origin-confirmation |
| 2  | RoadCode    | roadcode.blackroad.io    | node          | anastasia · 3000 | /api/health  | computer-95/api/roadcode | Road-Code          | needs-origin-confirmation |
| 3  | RoadTrip    | roadtrip.blackroad.io    | node          | anastasia · 3000 | /api/health  | computer-95/api/roadtrip | BlackRoad-AI       | needs-origin-confirmation |
| 4  | PitStop     | pitstop.blackroad.io     | node          | anastasia · 3000 | /api/health  | computer-95/api/pitstop  | BlackRoad-Education| needs-origin-confirmation |
| 5  | RoadWork    | roadwork.blackroad.io    | node          | anastasia · 3000 | /api/health  | computer-95/api/work     | BlackRoad-OS       | needs-origin-confirmation |
| 6  | BackRoad    | backroad.blackroad.io    | node          | anastasia · 3000 | /api/health  | computer-95/api/backroad | BlackRoad-Media    | needs-origin-confirmation |
| 7  | CarKeys     | carkeys.blackroad.io     | node          | anastasia · 3000 | /api/health  | computer-95/api/carkeys  | BlackRoad-Security | needs-origin-confirmation |
| 8  | RoadBook    | roadbook.blackroad.io    | node          | anastasia · 3000 | /api/health  | computer-95/api/roadbook | BlackRoad-Archive  | needs-origin-confirmation |
| 9  | RoadWorld   | roadworld.blackroad.io   | node          | cecilia   · 3000 | /api/health  | computer-95/api/world    | BlackRoad-Interactive | needs-origin-confirmation |
| 10 | RoadView    | roadview.blackroad.io    | node          | anastasia · 3000 | /api/health  | computer-95/api/search   | BlackRoad-Index    | needs-origin-confirmation |
| 11 | RoadChain   | roadchain.blackroad.io   | node          | anastasia · 3000 | /api/health  | computer-95/api/chain    | BlackRoad-Memory   | needs-origin-confirmation |
| 12 | RoadSide    | roadside.blackroad.io    | node          | anastasia · 3000 | /api/health  | computer-95/api/roadside | BlackRoad-Web      | needs-origin-confirmation |
| 13 | RoadCoin    | roadcoin.blackroad.io    | node          | anastasia · 3000 | /api/health  | computer-95/api/coin     | BlackRoad-Ventures | needs-origin-confirmation |
| 14 | CarPool     | carpool.blackroad.io     | node          | anastasia · 3000 | /api/health  | computer-95/api/carpool  | BlackRoad-Agents   | needs-origin-confirmation |
| 15 | BlackBoard  | blackboard.blackroad.io  | node          | anastasia · 3000 | /api/health  | computer-95/api/blackboard | BlackRoad-Studio | needs-origin-confirmation |
| 16 | OneWay      | oneway.blackroad.io      | node          | anastasia · 3000 | /api/health  | computer-95/api/oneway   | BlackRoad-Data     | needs-origin-confirmation |
| 17 | RoadBand    | roadband.blackroad.io    | node          | cecilia   · 3000 | /api/health  | computer-95/api/roadband | BlackRoad-Media    | needs-origin-confirmation |
| 18 | HighWay     | highway.blackroad.io     | node          | anastasia · 3000 | /api/health  | computer-95/api/highway  | BlackRoad-Cloud    | needs-origin-confirmation |
| 19 | RoadSport   | roadsport.blackroad.io   | node          | cecilia   · 3000 | /api/health  | computer-95/api/sport    | BlackRoad-Hardware | needs-origin-confirmation |
| 20 | OfficeRoad  | officeroad.blackroad.io  | node          | anastasia · 3000 | /api/health  | computer-95/api/office   | BlackRoad-Network  | needs-origin-confirmation |
| 21 | RoadStream  | roadstream.blackroad.io  | node          | cecilia   · 3000 | /api/health  | computer-95/api/stream   | BlackRoad-Media    | needs-origin-confirmation |
| 22 | RoadShow    | roadshow.blackroad.io    | node          | anastasia · 3000 | /api/health  | computer-95/api/roadshow | BlackRoad-Sandbox  | needs-origin-confirmation |
| 23 | RoundAbout  | roundabout.blackroad.io  | node          | anastasia · 3000 | /api/health  | computer-95/api/roundabout | BlackRoad-Agents | needs-origin-confirmation |
| 24 | GloveBox    | glovebox.blackroad.io    | node          | anastasia · 3000 | /api/health  | computer-95/api/glovebox | BlackRoad-Security | needs-origin-confirmation |
| 25 | RoadMap     | roadmap.blackroad.io     | node          | anastasia · 3000 | /api/health  | computer-95/api/roadmap  | BlackRoad-Foundation | needs-origin-confirmation |
| 26 | RoadWire    | roadwire.blackroad.io    | node          | anastasia · 3000 | /api/health  | computer-95/api/wire     | BlackRoad-Network  | needs-origin-confirmation |
| 27 | Detour      | detour.blackroad.io      | node          | anastasia · 3000 | /api/health  | computer-95/api/detour   | BlackRoad-Forge    | needs-origin-confirmation |

## Notes per product class

- **Single-monolith reality.** All 27 hosts currently route to the **same** Node process (the `computer-95` monolith) on `anastasia:3000` (or `cecilia:3000` for Hailo-aware media products). Caddy uses the `Host:` header to distinguish products. We can split per-product later without changing the edge.
- **Cecilia-routed products** (RoadWorld, RoadBand, RoadSport, RoadStream) are placed there because cecilia has the Hailo-8 + agent-react service and tends to handle media-adjacent workloads. Confirm before cutover; this is a guess.
- **Splitting later.** When a product gets its own deploy (e.g., RoadCode standalone), update `infra/routes/blackroad-routes.yaml` and regenerate. The product host doesn't change; only the origin does.

## Apex and root domains

These are **not** in the registry above (which is product subdomains). They get their own row in `infra/dns/records.blackroad.example.tsv`.

- `blackroad.io` apex → redirect to `https://www.blackroad.io/`
- `www.blackroad.io` → static landing or RoadSide proxy
- All other root domains (`blackroad.company`, `blackroad.me`, etc.) → park or redirect, decided per domain in DNS plan
