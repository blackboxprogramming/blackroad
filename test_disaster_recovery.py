#!/usr/bin/env python3
"""
Quick smoke test for disaster recovery backup & restore system
Run this to verify the DR system is working
"""

import subprocess
import sys
import json
from datetime import datetime

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    NC = '\033[0m'

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check(name, cmd):
    success, stdout, stderr = run_command(cmd)
    if success:
        print(f"  {Colors.GREEN}✓{Colors.NC} {name}")
        return True
    else:
        print(f"  {Colors.RED}✗{Colors.NC} {name}")
        if stderr:
            print(f"    {stderr[:100]}")
        return False

def main():
    print(f"\n{Colors.BLUE}BlackRoad Disaster Recovery System - Smoke Test{Colors.NC}\n")
    
    all_pass = True
    
    print("1. Infrastructure Checks")
    all_pass &= check("Docker installed", "docker --version")
    all_pass &= check("Docker Compose installed", "docker-compose --version")
    all_pass &= check("PostgreSQL container running", "docker ps | grep postgres")
    all_pass &= check("Redis container running", "docker ps | grep redis")
    
    print("\n2. Backup Scripts")
    all_pass &= check("disaster-recovery.sh exists", "test -f ./disaster-recovery.sh")
    all_pass &= check("disaster-recovery.sh is executable", "test -x ./disaster-recovery.sh")
    all_pass &= check("CLI tool exists", "test -f ./blackroad-cli.sh")
    all_pass &= check("CLI tool is executable", "test -x ./blackroad-cli.sh")
    
    print("\n3. Backup Directory Structure")
    all_pass &= check("Backup directory exists", "test -d /backups")
    all_pass &= check("PostgreSQL backup dir exists", "test -d /backups/postgres/full")
    all_pass &= check("Redis backup dir exists", "test -d /backups/redis/snapshots")
    all_pass &= check("Config backup dir exists", "test -d /backups/config")
    
    print("\n4. Documentation")
    all_pass &= check("Disaster Recovery Plan exists", "test -f ./DISASTER_RECOVERY_PLAN.md")
    all_pass &= check("Setup Guide exists", "test -f ./DISASTER_RECOVERY_SETUP.md")
    all_pass &= check("Runbook 1 exists", "test -f ./disaster-recovery/runbooks/scenario-1-postgres-corruption.md")
    all_pass &= check("Runbook 2 exists", "test -f ./disaster-recovery/runbooks/scenario-2-redis-failure.md")
    all_pass &= check("Runbook 3 exists", "test -f ./disaster-recovery/runbooks/scenario-3-data-center-failure.md")
    
    print("\n5. Monitoring")
    all_pass &= check("Grafana dashboard exists", "test -f ./monitoring/grafana/provisioning/dashboards/backup-monitoring.json")
    
    print("\n6. Quick Feature Test")
    print("  Testing disaster-recovery.sh --help output:")
    success, stdout, stderr = run_command("./disaster-recovery.sh --help 2>&1 | head -5")
    if "USAGE:" in stdout or "USAGE:" in stderr or "Backup" in stdout or "Backup" in stderr:
        print(f"    {Colors.GREEN}✓{Colors.NC} Help command works")
    else:
        print(f"    {Colors.YELLOW}!{Colors.NC} Help output: {(stdout + stderr)[:100]}")
    
    print(f"\n{Colors.BLUE}Test Summary{Colors.NC}")
    if all_pass:
        print(f"{Colors.GREEN}✓ All checks passed!{Colors.NC}")
        print("\nYou can now:")
        print("  1. Run a test backup:     ./disaster-recovery.sh backup-all")
        print("  2. Check backup status:   ./disaster-recovery.sh status")
        print("  3. Set up cron jobs:      crontab disaster-recovery/crontab.conf")
        print("  4. Access Grafana:        http://localhost:3000 (Dashboard: Disaster Recovery & Backups)")
        print("  5. Read the setup guide:  cat DISASTER_RECOVERY_SETUP.md")
        return 0
    else:
        print(f"{Colors.RED}✗ Some checks failed. See above for details.{Colors.NC}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
