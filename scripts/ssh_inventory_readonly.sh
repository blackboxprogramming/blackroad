#!/usr/bin/env bash
set -euo pipefail

# SSH inventory (readonly) for local devices
# - Only scans 192.168.4.0/24
# - Uses SSH key auth only (BatchMode=yes)
# - Short timeouts
# - Does not modify remote devices
# - Writes results to reports/ssh_inventory_readonly.md and data/ssh_inventory.jsonl

TARGET_IPS=(
  192.168.4.38
  192.168.4.49
  192.168.4.98
  192.168.4.112
  192.168.4.113
)

USERS=(alexa pi)
ALIASES=(lucidia aria alice octavia anastasia cecilia gematria calliope gaia olympia blackroad cadence)

OUT_MD="reports/ssh_inventory_readonly.md"
OUT_JSONL="data/ssh_inventory.jsonl"

mkdir -p reports data

timestamp() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

# utility: allowed subnet check (conservative string prefix check)
ip_allowed() {
  local ip="$1"
  [[ "$ip" == 192.168.4.* ]]
}

# Append a human-readable summary to markdown
append_md() {
  local line="$1"
  printf "%s %s\n" "- [$(timestamp)]" "$line" >> "$OUT_MD"
}

# Write a JSON object to JSONL using python (safe escaping)
write_jsonl_from_tmpdir() {
  local target="$1"
  local type="$2"    # ip or alias
  local tmpdir="$3"
  python3 - "$OUT_JSONL" "$target" "$type" "$tmpdir" <<'PY'
import json,sys,os
out_jsonl, target, type_, tmpdir = sys.argv[1:4]
obj = { 'timestamp': None, 'target': target, 'type': type_, 'port22': None, 'fingerprints': [], 'attempts': [] }
obj['timestamp'] = __import__('datetime').datetime.utcnow().isoformat() + 'Z'
# port status
if os.path.exists(os.path.join(tmpdir,'port_status.txt')):
    with open(os.path.join(tmpdir,'port_status.txt')) as f:
        obj['port22'] = f.read().strip()
# fingerprints
fpfile = os.path.join(tmpdir,'fingerprint.txt')
if os.path.exists(fpfile):
    with open(fpfile) as f:
        obj['fingerprints'] = [l.strip() for l in f if l.strip()]
# attempts
for fname in sorted(os.listdir(tmpdir)):
    if not fname.startswith('attempt_') or not fname.endswith('.out'):
        continue
    user = fname[len('attempt_'):-len('.out')]
    outpath = os.path.join(tmpdir,fname)
    rcpath = os.path.join(tmpdir,f'attempt_{user}.rc')
    with open(outpath,'r',errors='ignore') as f:
        out = f.read()
    rc = None
    if os.path.exists(rcpath):
        try:
            rc = int(open(rcpath).read().strip())
        except Exception:
            rc = None
    obj['attempts'].append({'user': user, 'rc': rc, 'output': out})
# append JSON line
with open(out_jsonl,'a') as f:
    f.write(json.dumps(obj) + '\n')
# also print a short summary to stdout for convenience
print(json.dumps({'target':target,'type':type_,'port22':obj['port22'],'fingerprints':obj['fingerprints'],'attempts':[{'user':a['user'],'rc':a['rc']} for a in obj['attempts']]}))
PY
}

# Helper: scan a single IP
scan_ip() {
  local ip="$1"
  local tmpdir
  tmpdir=$(mktemp -d)
  printf "" > "$tmpdir/port_status.txt"

  # Port check using nc if available
  if command -v nc >/dev/null 2>&1; then
    if nc -z -w 2 "$ip" 22 >/dev/null 2>&1; then
      echo "open" > "$tmpdir/port_status.txt"
    else
      echo "closed" > "$tmpdir/port_status.txt"
      append_md "$ip: ssh_closed"
      write_jsonl_from_tmpdir "$ip" ip "$tmpdir"
      rm -rf "$tmpdir"
      return
    fi
  else
    # fallback: try ssh quick probe (BatchMode to avoid password prompts)
    if ssh -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o PreferredAuthentications=publickey -o LogLevel=ERROR "${USERS[0]}@$ip" exit >/dev/null 2>&1; then
      echo "open" > "$tmpdir/port_status.txt"
    else
      echo "closed" > "$tmpdir/port_status.txt"
      append_md "$ip: ssh_closed (nc not available)"
      write_jsonl_from_tmpdir "$ip" ip "$tmpdir"
      rm -rf "$tmpdir"
      return
    fi
  fi

  # gather host key fingerprint (ssh-keyscan -> ssh-keygen)
  if command -v ssh-keyscan >/dev/null 2>&1 && command -v ssh-keygen >/dev/null 2>&1; then
    ssh-keyscan -T 3 -p 22 "$ip" 2>/dev/null > "$tmpdir/hostkey.raw" || true
    if [ -s "$tmpdir/hostkey.raw" ]; then
      # produce human-readable fingerprints
      ssh-keygen -lf "$tmpdir/hostkey.raw" 2>/dev/null | sed -E 's/^[0-9]+ //' > "$tmpdir/fingerprint.txt" || true
    fi
  fi

  # Use a temporary known_hosts file so we don't modify user's real file
  local tmp_known
  tmp_known=$(mktemp)

  # Attempt SSH with allowed users only
  for u in "${USERS[@]}"; do
    # Run only the identity commands required; BatchMode=yes prevents password prompts
    ssh -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile="$tmp_known" -o PreferredAuthentications=publickey -o LogLevel=ERROR "$u@$ip" "hostname; whoami; uname -a; uptime" > "$tmpdir/attempt_${u}.out" 2>&1 || true
    echo $? > "$tmpdir/attempt_${u}.rc"
    # if rc==0 then success — do not try other users
    if [ "$(cat "$tmpdir/attempt_${u}.rc")" -eq 0 ]; then
      append_md "$ip: ssh_ok as $u"
      write_jsonl_from_tmpdir "$ip" ip "$tmpdir"
      rm -rf "$tmpdir" "$tmp_known"
      return
    fi
  done

  # if we reach here, auth failed for allowed users
  append_md "$ip: auth_failed_key_only (no allowed-user succeeded)"
  write_jsonl_from_tmpdir "$ip" ip "$tmpdir"
  rm -rf "$tmpdir" "$tmp_known"
}

# Helper: scan an alias present in user's SSH config if it maps to an IP in allowed subnet
scan_alias() {
  local alias="$1"
  # get effective hostname from ssh -G (does not connect)
  if ! command -v ssh >/dev/null 2>&1; then
    return
  fi
  local cfg_host
  cfg_host=$(ssh -G "$alias" 2>/dev/null | awk '/^hostname /{print $2; exit}') || true
  if [ -z "$cfg_host" ]; then
    return
  fi
  # only proceed if hostname is an IPv4 literal in allowed subnet
  if [[ "$cfg_host" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]] && ip_allowed "$cfg_host"; then
    scan_ip "$cfg_host"
  else
    append_md "alias $alias skipped (hostname=$cfg_host not in 192.168.4.0/24 or not an IPv4 literal)"
  fi
}

# Start report
echo "# SSH inventory (readonly)" > "$OUT_MD"
echo "Generated: $(timestamp)" >> "$OUT_MD"
echo >> "$OUT_MD"

# Scan explicit IP targets
for ip in "${TARGET_IPS[@]}"; do
  if ! ip_allowed "$ip"; then
    append_md "$ip: skipped (not in 192.168.4.0/24)"
    continue
  fi
  append_md "$ip: probing"
  scan_ip "$ip"
done

# Scan aliases (only if they map to IPv4 in the allowed subnet)
if [ -f "$HOME/.ssh/config" ]; then
  for a in "${ALIASES[@]}"; do
    # quick existence check in config
    if grep -qE "^Host[[:space:]]+$a(\s|")?" "$HOME/.ssh/config" 2>/dev/null; then
      append_md "alias $a: present in SSH config — evaluating"
      scan_alias "$a"
    fi
  done
fi

append_md "scan complete"

echo "Wrote human report to $OUT_MD"
echo "Wrote machine-readable JSONL to $OUT_JSONL"

exit 0
