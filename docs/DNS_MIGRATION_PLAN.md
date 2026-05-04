# DNS Migration Plan

**Status:** Plan only. **Do not change DNS records yet.** This document describes the order, the records, and the rollback.
**Authoritative target:** DigitalOcean DNS (preferred) **or** the registrar's own DNS (acceptable fallback). Either works; pick one and commit before starting.

## 0. Hard prerequisites (must all be true before any cutover)

- [ ] `edge01` droplet provisioned, Caddy installed, **listening on 80/443 on its public IP**.
- [ ] Pi origins reachable from `edge01` over Tailscale, confirmed via `curl http://<tailnet-host>:<port>/health`.
- [ ] At least one product end-to-end works through `edge01` using `curl --resolve` (so we don't need real DNS to test).
- [ ] Email DNS records (MX/SPF/DKIM/DMARC) for each domain are **inventoried and copied** to the new DNS host. Email outage during a DNS migration is the single most common, most painful failure mode.
- [ ] TTLs on all records to be migrated have been lowered to 60 seconds at least 24 hours before cutover.

If any of these are not true, **stop**.

## 1. Picking a DNS host

Two choices. Pick exactly one.

| option | pros | cons |
|---|---|---|
| **DigitalOcean DNS** (recommended) | Free with a droplet. API is scriptable. Lives next to the edge so one fewer vendor in our path. | Have to migrate nameservers at the registrar (24–48h propagation). |
| Registrar DNS (Namecheap / GoDaddy / wherever each domain lives) | No nameserver change. Per-domain UI. | Records drift across registrars, manual entry per domain, harder to script for 17 root domains. |

**Recommendation:** DigitalOcean DNS for `blackroad.io` (the primary). For the other 16 root domains, defer the decision — most aren't hosting products yet, so they can stay on registrar DNS or sit parked until we need them.

## 2. Record inventory (per domain)

For each root domain, capture what exists today **before changing anything**:

```bash
# read-only — safe to run
for d in blackroad.io blackroad.company blackroad.me blackroad.network blackroad.systems \
         blackroadai.com blackroadinc.us blackroadqi.com blackroadquantum.com \
         blackboxprogramming.io aliceqi.com lucidia.earth lucidia.studio lucidiaqi.com \
         roadchain.io roadcoin.io; do
  echo "=== $d ==="
  dig +short NS  "$d"   @1.1.1.1
  dig +short A   "$d"   @1.1.1.1
  dig +short A   "www.$d" @1.1.1.1
  dig +short MX  "$d"   @1.1.1.1
  dig +short TXT "$d"   @1.1.1.1
  echo
done
```

Save the output to `infra/dns/baseline-$(date +%F).txt` so you can diff later. **This is the rollback reference.**

## 3. Cutover order (blackroad.io product subdomains)

These are the only A/AAAA records that change. They will all point to `edge01`'s public IPv4 (and optionally IPv6).

| batch | subdomains | rationale |
|---|---|---|
| 1 (canary) | `detour.blackroad.io`, `roadshow.blackroad.io` | lowest user impact; experimental products by design |
| 2 | `roadside.blackroad.io`, `roadview.blackroad.io`, `roundabout.blackroad.io` | search/router; user-visible but stateless |
| 3 | `roadtrip.blackroad.io`, `pitstop.blackroad.io`, `roadbook.blackroad.io`, `backroad.blackroad.io` | conversational + content; can tolerate brief blips |
| 4 | `carpool.blackroad.io`, `roadwork.blackroad.io`, `roadmap.blackroad.io`, `officeroad.blackroad.io` | project/ops surfaces |
| 5 | `roadworld.blackroad.io`, `roadsport.blackroad.io`, `roadband.blackroad.io`, `roadstream.blackroad.io`, `roadwire.blackroad.io`, `blackboard.blackroad.io` | media + spatial |
| 6 | `roadcode.blackroad.io`, `glovebox.blackroad.io`, `oneway.blackroad.io`, `roadcoin.blackroad.io`, `roadchain.blackroad.io` | data-bearing — confirm chain receipts pre/post |
| 7 | `carkeys.blackroad.io`, `highway.blackroad.io` | auth + billing — most carefully |
| 8 | `os.blackroad.io` | RoadOS shell |
| 9 | apex `blackroad.io` and `www.blackroad.io` | last |

One batch per day. Watch logs and `scripts/check-domain-health-no-cloudflare.sh` for an hour after each batch before moving on.

## 4. Email records (do not skip)

For each root domain that sends/receives mail (at minimum `blackroad.io`):

- [ ] Copy MX records exactly.
- [ ] Copy SPF (`v=spf1 ...`) exactly.
- [ ] Copy DKIM `<selector>._domainkey` records exactly.
- [ ] Copy DMARC `_dmarc` record exactly.
- [ ] Verify in the new DNS host with `dig`, then **send a test mail to/from the domain** before flipping nameservers.

If Gmail bounces or DMARC starts failing, **stop and roll back** before continuing with product subdomains.

## 5. TTL strategy

| phase | TTL | when |
|---|---|---|
| Pre-flight (T-24h) | 60s | lower TTLs on every record about to migrate |
| Cutover | 60s | flip the value |
| Soak | 60s | leave for at least 7 days post-cutover so rollback is fast |
| Steady state | 3600s | only after the migration is "done" and not coming back |

## 6. Rollback procedure

For any single subdomain:

1. In the DNS host, change the A/AAAA value back to the old origin (the value captured in `infra/dns/baseline-*.txt`).
2. Wait one TTL (60s).
3. Verify with `dig +short <subdomain>` against `1.1.1.1` and `8.8.8.8`.
4. Verify with `curl -I https://<subdomain>/` that the old origin responds.

For a wholesale rollback (e.g., nameserver flip went wrong):

1. At the registrar, point nameservers back to the previous DNS host (Cloudflare or wherever they came from).
2. Wait up to 24h for nameserver propagation.
3. Confirm `dig NS <domain> @<root-server>` returns the old nameservers.

## 7. Records template

See `infra/dns/records.blackroad.example.tsv` for a fillable record sheet (one row per record). It is the script-friendly companion to this plan.
