# CarKeys migration plan

**Status:** plan only. No secrets touched, no rotation triggered, no code deployed.
**Authority:** this is a roadmap, not authority to delete or rotate. Each phase ends with explicit operator approval.
**Source principle:** *"We don't pass keys around. We pass permission."*

---

## Phase 1 — Inventory (read-only)

Goal: locate every credential currently used by BlackRoad, without exposing any.

What we know already (from the live audits in this session):

- `~/.ssh/id_ed25519` — operator key. Authorized on 5 hosts (cecilia, alice, aria, anastasia, lucidia, gematria). Long-lived. **Not rotated.**
- `~/.lucidia-ssh/{id_rsa, id_octavia, id_do_ed25519, id_shellfish_ed25519, id_sandbox_ed25519, archive/blackroad_key, ...}` — 11 additional private keys, none of which unlock anything currently reachable. Likely retired but not removed.
- `~/.blackroad/backups/alice-20260315/ssh-keys/id_ed25519` — alice's *own* private key in a backup. **Backup contains a private key.**
- `~/.cloudflare_origin_ca_key`, `~/.cloudflare_global_api_key` — Cloudflare credentials at home directory root.
- `~/.cloudflared/cert.pem`, `~/.lucidia-cloudflared/cert*.pem` — Cloudflare Tunnel certs.
- `gematria:/home/blackroad/blackroad/.git/config` — **GitHub PAT (`gho_*`) embedded in a remote URL on disk.** Flagged earlier in this session. Highest-priority leak.
- `~/.ssh/config.d/blackroad-fleet` — SSH config with stale + correct host mappings. No secret, but it's the discovery surface.
- 8 sshid.io public keys for `@blackroad-sandbox` — published. Their private counterparts are not on this Mac.
- `~/Downloads/ssh-ed25519-blackroad-master` — a "master" key, **mode 0644 (world-readable on disk).** Permissions issue.

What still needs inventory (read-only, not yet done):

1. `.env*`, `.envrc`, `.netrc`, `.pgpass`, `.aws/credentials`, `.npmrc` (auth tokens), `.docker/config.json`, `~/.config/gh/hosts.yml`.
2. Every `*.git/config` on every node — search for `https://gho_*@`, `https://ghp_*@`, `https://oauth2:*@`.
3. JSON config files referencing `Bearer `, `Authorization`, `password`, `secret`, `token`, `apikey`.
4. macOS Keychain entries owned by BlackRoad apps (search `security find-generic-password -s blackroad*`).
5. Tailscale auth keys lying in shell history.
6. Stripe keys, Cloudflare API tokens, GitHub PATs, OpenAI/Anthropic keys (if any), Resend / SES / Twilio etc.
7. Webhook signing secrets.
8. SSH known_hosts entries for hosts no longer in service (housekeeping, not security).

Output: `~/.blackroad-autonomy/secret-inventory-<date>.tsv` with columns `path | type | last_modified | needs_rotation | classification`. **Hashes only, never the secret bytes.**

## Phase 2 — Classification

Each discovered credential gets exactly one tag:

| class | example | policy |
|---|---|---|
| `public-config` | host names, ports, public keys | OK in repos and logs |
| `local-only` | `~/.ssh/id_ed25519`, macOS keychain entries | never leaves the machine; never in repo, never in logs |
| `rotating-secret` | GitHub PATs, Stripe keys, Cloudflare API tokens | short-lived; CarKeys-managed; receipt on every use |
| `provider-handle` | OAuth refresh tokens, Tailscale device keys | scoped, revocable; ingested via OneWay |
| `legacy-secret` | hardcoded API keys in old code | scheduled for removal; flagged in receipts |
| `compromised` | the `gho_*` token in `gematria:.git/config`; the world-readable `ssh-ed25519-blackroad-master` | **rotate immediately, then move to CarKeys** |

## Phase 3 — Allowed storage locations

| location | what may live there |
|---|---|
| macOS Keychain / Linux Secret Service / Keyring | `local-only` and `rotating-secret` (encrypted at rest) |
| `~/.ssh/` (mode 0700, files 0600) | SSH private keys, never world-readable |
| CarKeys service (per `blackroad_carkeys.md`): `brk_*` API keys, `brg_*` delegated grants, scoped to product + verb | the *only* place a long-lived secret should be issued from |
| OneWay redaction proxy | the only place external tokens may be exchanged for internal grants |
| OS-level systemd `LoadCredential=` / `EnvironmentFile=` (mode 0600) | runtime credentials for services |

## Phase 4 — Forbidden storage locations (enforced by selftest)

- **Any file the daemon writes**: `events.jsonl`, `decisions.jsonl`, `snapshots.jsonl`, `replay_report.txt`, `calibration_report.txt`, `tiles/*.bin`. *Already enforced — selftest `snapshot-no-secret-smell` checks for known prefixes (`gho_`, `ghp_`, `sk-`, `Bearer `, `private_key`, `ssh-rsa `, `ssh-ed25519 `).*
- Any prompt sent to any LLM, anywhere.
- Any chat log, transcript, or screenshot.
- Any commit message or PR body.
- Any browser-side JavaScript or HTML attribute.
- RoadChain receipts (only hashes / refs / ids — never raw secret bytes).
- `*.bash_history`, `~/.zsh_history` — shell-history hygiene script needed.

## Phase 5 — Short-lived capability tokens (CarKeys design)

Two token types, already defined in CarKeys:

- **`brk_*`** — API keys. Long-lived; can be revoked any time. Scoped to a product + verb set (`{product}:{verb}`, e.g. `roadcoin:read`).
- **`brg_*`** — delegated grants. Short-lived (default 24h, max 7d). Created by an existing token to delegate a *subset* of its scope, with a callback URL or webhook constraint.

New token type to add: **`brc_*`** — capability token. Single-use, ≤ 5-minute TTL, **bound to a request hash**. Use case: ESCALATE wants Qwen to summarize a snapshot; CarPool mints a `brc_*` good for one call against the snapshot SHA, expiring in 5 minutes. After use, the token is dead.

Token format (no secret in the token itself; the secret lives in CarKeys' DB):
```
brc_<8-char-prefix>_<16-char-id>
```
The prefix is a checkable category; the id is the lookup key. The actual secret is HMAC'd inside CarKeys. **No raw secret ever leaves the issuing service.**

## Phase 6 — Receipt schema (proves access without leaking)

Every secret use writes a RoadChain receipt of this shape:

```json
{
  "ref":         "carkeys:use:<token_id>",
  "ts":          <unix>,
  "actor":       "<user_id or service_id>",
  "scope":       ["roadcoin:read"],
  "target":      "<product>:<verb>:<resource_hash>",
  "purpose":     "ESCALATE | sync | export | manual | ...",
  "result":      "ok | denied | rate-limited | revoked",
  "secret_kind": "brk | brg | brc",
  "secret_fp":   "<sha256(token)[:12]>",
  "snapshot_tile_sha": "<sha256 or null>",
  "via":         "OneWay | direct | CarPool"
}
```

Note: `secret_fp` is a fingerprint of the token, NOT the token. Anyone reading the receipt can verify *which* token was used (by computing the same fingerprint when revoking) but cannot recover the token.

## Phase 7 — Rotation policy

| class | rotation cadence |
|---|---|
| `compromised` | now, then immediately after this plan ships |
| `rotating-secret` | 30 days default; CI checks age, alerts at 25 |
| `provider-handle` | per provider; OneWay refreshes; daemon never sees it |
| `local-only` | event-driven (lost laptop → revoke + re-issue); no calendar rotation |

Rotation receipt: same schema as Phase 6, with `result: "rotated"` and `purpose: "rotation"`.

## Phase 8 — Revocation policy

- Any operator can revoke any token they issued. Revocation is **synchronous**: token marked dead in CarKeys DB, then a RoadChain receipt is emitted before the API returns OK.
- Compromise drill: a single `carkeys revoke --secret-fp <fp>` should kill that token everywhere within 10 seconds. Test this drill quarterly.
- Cascading revocation: revoking a `brk_*` revokes every `brg_*` and `brc_*` derived from it (already specified in CarKeys `requireAuth(scopes)` semantics).

## Phase 9 — Local-first fallback when no external key is available

Critical for the no-LLM-by-default architecture: if CarKeys can't issue a token (offline, throttled, or operator paused all external use), the daemon must keep working.

- Reflex daemon: **already** runs without any external key. Verified by the selftest *running on cecilia today*.
- ESCALATE: writes to `decisions.jsonl` with `decision=ESCALATE` and a snapshot SHA. A separate consumer (`carpool-escalate-worker`, *out of process*) is the one that asks CarKeys for a `brc_*` and calls Qwen. If CarKeys is down, the worker waits and retries; events queue. Nothing in the reflex path blocks.
- TileStore: has no external dep. Already proven durable across processes today.

## Phase 10 — Selftests for redaction (to add to the daemon and to CI)

Already added to `blackroad_reflex_daemon.py` selftest #26 (`snapshot-no-secret-smell`). Extend with:

| test | input | pass condition |
|---|---|---|
| `event-secret-rejected` | event with `text: "Bearer abc"` or `text: "gho_…"` | reflex produces `FORGET` with `reason: "secret-shape detected"`, **does NOT write the text to JSONL or tiles** |
| `decision-no-secret` | grep generated decisions for known prefixes | zero matches |
| `snapshot-no-secret` | grep snapshot tile bytes for known prefixes | zero matches |
| `replay-no-secret` | grep `replay_report.txt` | zero matches |
| `tilestore-receipt-fingerprint-only` | a put() call with secret-shaped payload | refused with `reason: secret-shape; not stored` |

The redaction patterns themselves live in a small allowlist file `~/.blackroad-autonomy/secret-shapes.json` so the patterns can be updated without code changes.

---

## What this changes about the architecture

Before:
```
agent → API key in env → provider call → result → log everywhere
```

After:
```
agent → CarKeys issues brc_* (scoped, ≤5min) → OneWay-routed call → CarPool decision →
RoadChain receipt (fingerprint only) → TileStore (memory body, no secret) → daemon (no provider key, ever)
```

## What this does NOT solve

- It does not prevent screenshots/photos of credentials.
- It does not protect against a compromised laptop with operator key access — that's why local-only credentials still need full-disk encryption + screen lock.
- It does not give us secrets-management for production secrets owned by partners (Stripe webhooks, Cloudflare DNS API): those still need to live in *some* vault (CarKeys is the proposed vault).
- It does not retroactively scrub git history — for the `gho_*` token already in `gematria:.git/config`, the rotation step is mandatory; history scrubbing is a separate hygiene task.

## First moves (each requires explicit operator OK)

1. **Rotate the `gho_*` PAT** in `gematria:/home/blackroad/blackroad/.git/config`. Replace remote URL with SSH-form. Receipt.
2. **Tighten** `~/Downloads/ssh-ed25519-blackroad-master` to 0600 or move it into `~/.ssh/`. Receipt.
3. **Run the inventory script** (Phase 1) read-only and produce the TSV.
4. **Decide a CarKeys backend**: existing BlackRoad CarKeys service vs an interim 1Password / macOS Keychain / Bitwarden + scripts. Don't build a new vault.
5. **Wire the secret-shape allowlist** into the reflex daemon (Phase 10) so any leakage attempts get caught at the boundary.

Nothing on this list calls an LLM. Nothing requires SSHing into another node. Nothing rotates without operator OK.
