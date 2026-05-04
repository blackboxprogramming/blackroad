Installation instructions — systemd service for gematria

1. Copy files to the target server (gematria) and place services in /etc/systemd/system:

   scp deploy/systemd/br_tcpdump_collector.service deploy/systemd/br_tcpdump_rotate.service \
       deploy/systemd/br_tcpdump_rotate.timer root@gematria:/etc/systemd/system/

2. Place the repository on gematia at the path referenced by REPO_DIR in the unit files.
   By default the units expect REPO_DIR=/opt/blackroad. Either install the repo there or edit the
   service files and set Environment=REPO_DIR=/path/to/blackroad.

3. Make the helper scripts executable on gematia:

   ssh root@gematia 'chmod +x /opt/blackroad/scripts/br_local_capture.sh /opt/blackroad/scripts/br_rotate_ledger.sh'

4. tcpdump privileges:
   - Preferred: allow non-root capture by granting capabilities to tcpdump:
       sudo setcap cap_net_raw,cap_net_admin+eip $(which tcpdump)
   - Or run the service as root (not recommended if you can avoid it).

5. Reload systemd and enable services/timer:

   ssh root@gematia 'systemctl daemon-reload && systemctl enable --now br_tcpdump_collector.service br_tcpdump_rotate.timer'

6. Verify:
   - Follow journal: ssh root@gematia 'journalctl -u br_tcpdump_collector -f'
   - Check ledger: ssh root@gematia 'tail -f /opt/blackroad/violations/br_violations.jsonl'

Notes:
- Rotation uses copy-truncate; for a zero-loss rotation the collector would need to reopen the ledger on signal.
- Do not place ledger in /tmp per BlackRoad policy — ledger lives under the repo at violations/.
