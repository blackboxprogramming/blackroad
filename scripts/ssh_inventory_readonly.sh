#!/usr/bin/env bash
# ssh_inventory_readonly.sh
# Read-only SSH inventory using key-only auth (BatchMode=yes).
# Tries users: alexa, pi
# Writes JSONL to data/ssh_inventory.jsonl and a markdown report to reports/ssh_inventory_readonly.md

set -uo pipefail
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd "$script_dir/.." && pwd)
DATA_DIR="$repo_root/data"
REPORT_DIR="$repo_root/reports"
OUT_JSON="$DATA_DIR/ssh_inventory.jsonl"
OUT_MD="$REPORT_DIR/ssh_inventory_readonly.md"

mkdir -p "$DATA_DIR" "$REPORT_DIR"

USERS=(alexa pi)
IPS=("$@")
if [ ${#IPS[@]} -eq 0 ]; then
  IPS=(192.168.4.38 192.168.4.49 192.168.4.98 192.168.4.112 192.168.4.113)
fi

# Helper: safe json dump via python (reads env vars to avoid complex escaping)
write_json_line() {
  # expects env vars: IP,SSH_STATUS,SSH_USER,HOSTNAME_OUT,WHOAMI_OUT,UNAME_OUT,UPTIME_OUT,PWD_OUT,IFACES_OUT,LSUSB_OUT,SYSTEMCTL_OUT,PY_VER,NODE_VER,OLLAMA_VER,PM2_VER,DOCKER_VER,NOTE
  python3 - <<'PY'
import os,sys,json
env=os.environ
obj={
  'ip': env.get('IP'),
  'ssh_status': env.get('SSH_STATUS'),
  'ssh_user': env.get('SSH_USER'),
  'hostname': env.get('HOSTNAME_OUT'),
  'whoami': env.get('WHOAMI_OUT'),
  'uname': env.get('UNAME_OUT'),
  'uptime': env.get('UPTIME_OUT'),
  'pwd': env.get('PWD_OUT'),
  'interfaces': env.get('IFACES_OUT'),
  'lsusb': env.get('LSUSB_OUT'),
  'systemctl': env.get('SYSTEMCTL_OUT'),
  'python3_version': env.get('PY_VER'),
  'node_version': env.get('NODE_VER'),
  'ollama_version': env.get('OLLAMA_VER'),
  'pm2_version': env.get('PM2_VER'),
  'docker_version': env.get('DOCKER_VER'),
  'note': env.get('NOTE')
}
# remove None keys
obj = {k:v for k,v in obj.items() if v is not None}
print(json.dumps(obj))
PY
}

# Overwrite output file
: > "$OUT_JSON"

for ip in "${IPS[@]}"; do
  export IP="$ip"
  ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  SSH_STATUS="unknown"
  SSH_USER=""
  HOSTNAME_OUT=""
  WHOAMI_OUT=""
  UNAME_OUT=""
  UPTIME_OUT=""
  PWD_OUT=""
  IFACES_OUT=""
  LSUSB_OUT=""
  SYSTEMCTL_OUT=""
  PY_VER=""
  NODE_VER=""
  OLLAMA_VER=""
  PM2_VER=""
  DOCKER_VER=""
  NOTE=""

  # First test port 22 using nc -vz -w 2 as requested
  PORT22_OK=0
  if command -v nc >/dev/null 2>&1; then
    if nc -vz -w 2 "$ip" 22 >/dev/null 2>&1; then
      PORT22_OK=1
    else
      PORT22_OK=0
    fi
  else
    # fallback to /dev/tcp
    if (exec 3>/dev/tcp/"$ip"/22) >/dev/null 2>&1; then
      PORT22_OK=1
      exec 3>&-
    else
      PORT22_OK=0
    fi
  fi

  if [ "$PORT22_OK" -ne 1 ]; then
    SSH_STATUS="ssh_closed"
    export SSH_STATUS SSH_USER HOSTNAME_OUT WHOAMI_OUT UNAME_OUT UPTIME_OUT PWD_OUT IFACES_OUT LSUSB_OUT SYSTEMCTL_OUT PY_VER NODE_VER OLLAMA_VER PM2_VER DOCKER_VER NOTE
    write_json_line >> "$OUT_JSON"
    continue
  fi

  # Port open — try users
  AUTH_OK=0
  for user in "${USERS[@]}"; do
    KNOWN_FILE=$(mktemp /tmp/br_known.XXXX)
    # ensure temp cleaned
    trap 'rm -f "$KNOWN_FILE"' RETURN
    SSH_OPTS=( -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile="$KNOWN_FILE" -o PreferredAuthentications=publickey -o PasswordAuthentication=no -o LogLevel=ERROR )
    # attempt simple auth check
    if ssh "${SSH_OPTS[@]}" "${user}@${ip}" 'echo __BR_SSH_OK__' >/dev/null 2>&1; then
      AUTH_OK=1
      SSH_STATUS="auth_ok"
      SSH_USER="$user"

      # run allowed remote commands (each is safe, no file reads beyond those commands)
      HOSTNAME_OUT=$(ssh "${SSH_OPTS[@]}" "${user}@${ip}" 'hostname' 2>/dev/null || true)
      WHOAMI_OUT=$(ssh "${SSH_OPTS[@]}" "${user}@${ip}" 'whoami' 2>/dev/null || true)
      UNAME_OUT=$(ssh "${SSH_OPTS[@]}" "${user}@${ip}" 'uname -a' 2>/dev/null || true)
      UPTIME_OUT=$(ssh "${SSH_OPTS[@]}" "${user}@${ip}" 'uptime' 2>/dev/null || true)
      PWD_OUT=$(ssh "${SSH_OPTS[@]}" "${user}@${ip}" 'pwd' 2>/dev/null || true)
      IFACES_OUT=$(ssh "${SSH_OPTS[@]}" "${user}@${ip}" 'ip -br addr 2>/dev/null || ifconfig 2>/dev/null' 2>/dev/null || true)
      LSUSB_OUT=$(ssh "${SSH_OPTS[@]}" "${user}@${ip}" 'command -v lsusb >/dev/null 2>&1 && lsusb 2>/dev/null || true' 2>/dev/null || true)
      SYSTEMCTL_OUT=$(ssh "${SSH_OPTS[@]}" "${user}@${ip}" 'command -v systemctl >/dev/null 2>&1 && systemctl --version 2>/dev/null || true' 2>/dev/null || true)
      PY_VER=$(ssh "${SSH_OPTS[@]}" "${user}@${ip}" 'command -v python3 >/dev/null 2>&1 && python3 --version 2>/dev/null || true' 2>/dev/null || true)
      NODE_VER=$(ssh "${SSH_OPTS[@]}" "${user}@${ip}" 'command -v node >/dev/null 2>&1 && node --version 2>/dev/null || true' 2>/dev/null || true)
      OLLAMA_VER=$(ssh "${SSH_OPTS[@]}" "${user}@${ip}" 'command -v ollama >/dev/null 2>&1 && ollama --version 2>/dev/null || true' 2>/dev/null || true)
      PM2_VER=$(ssh "${SSH_OPTS[@]}" "${user}@${ip}" 'command -v pm2 >/dev/null 2>&1 && pm2 --version 2>/dev/null || true' 2>/dev/null || true)
      DOCKER_VER=$(ssh "${SSH_OPTS[@]}" "${user}@${ip}" 'command -v docker >/dev/null 2>&1 && docker --version 2>/dev/null || true' 2>/dev/null || true)

      # done with known file
      rm -f "$KNOWN_FILE" 2>/dev/null || true
      trap - RETURN

      # export and write JSON
      export SSH_STATUS SSH_USER HOSTNAME_OUT WHOAMI_OUT UNAME_OUT UPTIME_OUT PWD_OUT IFACES_OUT LSUSB_OUT SYSTEMCTL_OUT PY_VER NODE_VER OLLAMA_VER PM2_VER DOCKER_VER NOTE
      write_json_line >> "$OUT_JSON"
      break
    else
      # auth failed for this user, remove known file and try next
      rm -f "$KNOWN_FILE" 2>/dev/null || true
      trap - RETURN
      continue
    fi
  done

  if [ "$AUTH_OK" -ne 1 ]; then
    SSH_STATUS="auth_failed_key_only"
    export SSH_STATUS SSH_USER HOSTNAME_OUT WHOAMI_OUT UNAME_OUT UPTIME_OUT PWD_OUT IFACES_OUT LSUSB_OUT SYSTEMCTL_OUT PY_VER NODE_VER OLLAMA_VER PM2_VER DOCKER_VER NOTE
    write_json_line >> "$OUT_JSON"
  fi

done

# Generate a summary markdown
python3 - <<'PY'
import json,os
infile='data/ssh_inventory.jsonl'
out='reports/ssh_inventory_readonly.md'
items=[]
if os.path.exists(infile):
    with open(infile) as f:
        for l in f:
            try:
                items.append(json.loads(l))
            except:
                pass
lines=[]
lines.append('# SSH inventory (read-only)')
lines.append('')
for it in items:
    ip=it.get('ip')
    status=it.get('ssh_status')
    user=it.get('ssh_user')
    hostname=it.get('hostname')
    uname=it.get('uname')
    ports11434='11434' in ' '.join(it.get('interfaces','')) if it.get('interfaces') else False
    lines.append(f'- {ip}: status={status}, user={user}, hostname={hostname}, uname={uname}, port11434={ports11434}')
open(out,'w').write('\n'.join(lines))
print('Wrote',out)
PY

# end script
