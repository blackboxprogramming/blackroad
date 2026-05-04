BlackRoad — Local-first device discovery (prototype)

Summary
-------
This prototype scans your local LAN (read-only) to "see" devices and produce fingerprints. It does NOT log in, does not change system settings, and does not rely on any external cloud service.

Quickstart (read-only inventory)
--------------------------------
1. Ensure optional tools are installed for better results (recommended but not required): nmap, ssh-keyscan
   - macOS: dns-sd is usually available
   - Linux: ip, arp, tcpdump (optional)
2. Run discovery (safe, ping-only scan if nmap present):
   bash scripts/discover_lan.sh
   -> appends JSONL records to data/seen_devices.jsonl
3. Fingerprint a specific device (example):
   bash scripts/fingerprint_device.sh 192.168.1.42 > data/fingerprints.jsonl
4. Merge into registry:
   python3 src/device_registry.py
   -> writes data/known_devices.json

Notes on commands
- All scripts are read-only. The passive observer requires sudo explicitly and is opt-in.
- Do NOT run these scripts against networks you don't control or have permission to scan.

Confidence levels
-----------------
- low: only IP observed. Not enough to identify a device.
- medium: IP + hostname or MAC observed. Better but still forgeable.
- high: SSH host key fingerprint or repeated stable identity observed.
- trusted: device was claimed using the BlackRoad claim protocol (CarKeys) and marked trusted by the user.

What is collected
- IP address
- MAC address (if visible from ARP)
- MAC vendor (when locally derivable)
- hostnames, mDNS names
- open local services (ports)
- SSH host key fingerprint (if port 22 is open) — collected via ssh-keyscan without logging in
- observed_at / first_seen / last_seen timestamps

Privacy and safety
- No external API keys are required.
- Passive observation does NOT save packet payloads; it only emits metadata counts.
- The scripts are intended for local/private networks you control.

Next steps
- Implement device-side claiming (CarKeys) and the server-side claim flow.
- Optionally integrate RoadChain for immutable claim recording.

For more details, see src/claim_protocol.md and src/device_registry.py
