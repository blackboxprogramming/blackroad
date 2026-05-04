#!/usr/bin/env python3
"""
br_tcpdump_collector.py
BlackRoad-native tcpdump-line collector and violation detector.

Usage:
  ssh -t gematria 'sudo tcpdump -l -n -nn -i any "tcp or udp"' \
    | python3 /Users/alexa/blackroad/scripts/br_tcpdump_collector.py --local-ip 159.65.43.12

Reads tcpdump lines from stdin, detects IPv4 addresses, checks against an allowlist of networks,
logs any non-allowlisted IP as a violation (appends JSON lines to violations/br_violations.jsonl), and
prints "blackroad instant violation" immediately when a violation is seen.
"""

import sys
import re
import ipaddress
import json
import time
import argparse
import signal
import os


def load_allowlist(path):
    nets = []
    try:
        with open(path, 'r') as f:
            for ln in f:
                s = ln.strip()
                if not s or s.startswith('#'):
                    continue
                try:
                    nets.append(ipaddress.ip_network(s))
                except Exception:
                    # ignore malformed entries
                    pass
    except Exception:
        # fall back to sensible defaults
        defaults = [
            '10.0.0.0/8',
            '172.16.0.0/12',
            '192.168.0.0/16',
            '127.0.0.0/8',
            '100.64.0.0/10'
        ]
        nets = [ipaddress.ip_network(n) for n in defaults]
    return nets


def ip_allowed(ip, nets, local_ip=None):
    try:
        addr = ipaddress.ip_address(ip)
    except Exception:
        return False
    if local_ip and ip == local_ip:
        return True
    for n in nets:
        if addr in n:
            return True
    return False


def main():
    parser = argparse.ArgumentParser(description='BlackRoad tcpdump-line collector')
    parser.add_argument('--allowlist', default='scripts/br_allowlist.txt', help='Path to allowlist file (CIDR per line)')
    parser.add_argument('--local-ip', default=None, help='Local host IP to ignore (gematria)')
    parser.add_argument('--ledger', default='violations/br_violations.jsonl', help='Append-only JSONL ledger path')
    args = parser.parse_args()

    allowlist = load_allowlist(args.allowlist)
    ip_re = re.compile(r'(\d{1,3}(?:\.\d{1,3}){3})')
    violation_count = 0

    # ensure ledger directory exists and is inside repo
    ledger_dir = os.path.dirname(args.ledger)
    try:
        if ledger_dir and not os.path.exists(ledger_dir):
            os.makedirs(ledger_dir, exist_ok=True)
        ledger_file = open(args.ledger, 'a', buffering=1)
    except Exception:
        ledger_file = None

    def handle_sigint(signum, frame):
        print(f"collector exiting; total_violations={violation_count}", file=sys.stderr)
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    # Process stdin lines as they arrive
    for raw in sys.stdin:
        try:
            line = raw.rstrip('\n')
        except Exception:
            continue
        timestamp = time.time()
        # Print the original tcpdump line prefixed with an ISO timestamp for live monitoring
        try:
            print(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(timestamp))} {line}")
            sys.stdout.flush()
        except Exception:
            pass

        ips = set(ip_re.findall(line))
        offending = []
        for ip in ips:
            if ip == '0.0.0.0':
                continue
            try:
                if not ip_allowed(ip, allowlist, local_ip=args.local_ip):
                    offending.append(ip)
            except Exception:
                # on parse error, be conservative and treat as offending
                offending.append(ip)

        if offending:
            violation_count += len(offending)
            rec = {
                'ts': timestamp,
                'offending': offending,
                'line': line,
                'total_violations': violation_count
            }
            if ledger_file:
                try:
                    ledger_file.write(json.dumps(rec) + '\n')
                    ledger_file.flush()
                except Exception:
                    pass
            # Emit a stderr violation note and the required trigger phrase for auditing
            try:
                print(f"[VIOLATION] offending={','.join(offending)} total_violations={violation_count}", file=sys.stderr)
                print("blackroad instant violation")
                sys.stderr.flush()
                sys.stdout.flush()
            except Exception:
                pass


if __name__ == '__main__':
    main()
