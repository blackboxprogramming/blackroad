"""Compliance reporting and audit trail generation."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict


@dataclass
class ComplianceReport:
    """Compliance report data."""
    report_id: str
    report_date: datetime
    report_type: str
    period_start: datetime
    period_end: datetime
    total_entries: int
    total_users: int
    failed_actions: int
    integrity_checks_failed: int
    sensitive_actions: int
    findings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'report_id': self.report_id,
            'report_date': self.report_date.isoformat(),
            'report_type': self.report_type,
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'total_entries': self.total_entries,
            'total_users': self.total_users,
            'failed_actions': self.failed_actions,
            'integrity_checks_failed': self.integrity_checks_failed,
            'sensitive_actions': self.sensitive_actions,
            'findings': self.findings,
            'metadata': self.metadata
        }


class ComplianceAnalyzer:
    """Analyze audit logs for compliance."""

    def __init__(self, audit_logger):
        self.logger = audit_logger
        self.sensitive_actions = {'DELETE', 'export', 'AUTHORIZE'}
        self.reports: Dict[str, ComplianceReport] = {}

    def generate_daily_report(self, date: Optional[datetime] = None) -> ComplianceReport:
        """Generate daily compliance report."""
        if date is None:
            date = datetime.utcnow()

        start = datetime(date.year, date.month, date.day)
        end = start + timedelta(days=1)

        entries = [e for e in self.logger.entries if start <= e.timestamp < end]

        report_id = f"daily-{start.strftime('%Y%m%d')}"

        # Calculate metrics
        total_users = len(set(e.user_id for e in entries))
        failed_actions = len([e for e in entries if e.status != "success"])
        sensitive = len([e for e in entries if e.action.value in self.sensitive_actions])

        # Verify integrity
        integrity_failed = sum(1 for e in entries if not self.logger.verify_integrity(e.entry_id))

        # Generate findings
        findings = []
        if failed_actions > len(entries) * 0.1:  # >10% failure rate
            findings.append(f"High failure rate: {failed_actions}/{len(entries)}")

        if integrity_failed > 0:
            findings.append(f"Integrity check failed for {integrity_failed} entries")

        if sensitive > len(entries) * 0.3:  # >30% sensitive
            findings.append(f"High volume of sensitive actions: {sensitive}")

        report = ComplianceReport(
            report_id=report_id,
            report_date=datetime.utcnow(),
            report_type='daily',
            period_start=start,
            period_end=end,
            total_entries=len(entries),
            total_users=total_users,
            failed_actions=failed_actions,
            integrity_checks_failed=integrity_failed,
            sensitive_actions=sensitive,
            findings=findings
        )

        self.reports[report_id] = report
        return report

    def generate_monthly_report(self, year: int, month: int) -> ComplianceReport:
        """Generate monthly compliance report."""
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)

        entries = [e for e in self.logger.entries if start <= e.timestamp < end]

        report_id = f"monthly-{start.strftime('%Y%m')}"

        # Calculate metrics
        total_users = len(set(e.user_id for e in entries))
        failed_actions = len([e for e in entries if e.status != "success"])
        sensitive = len([e for e in entries if e.action.value in self.sensitive_actions])

        # Verify integrity
        integrity_failed = sum(1 for e in entries if not self.logger.verify_integrity(e.entry_id))

        findings = []
        if failed_actions > len(entries) * 0.1:
            findings.append(f"High failure rate: {failed_actions}/{len(entries)}")

        if integrity_failed > 0:
            findings.append(f"Integrity check failed for {integrity_failed} entries")

        report = ComplianceReport(
            report_id=report_id,
            report_date=datetime.utcnow(),
            report_type='monthly',
            period_start=start,
            period_end=end,
            total_entries=len(entries),
            total_users=total_users,
            failed_actions=failed_actions,
            integrity_checks_failed=integrity_failed,
            sensitive_actions=sensitive,
            findings=findings
        )

        self.reports[report_id] = report
        return report

    def get_user_report(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get compliance report for specific user."""
        end = datetime.utcnow()
        start = end - timedelta(days=days)

        entries = [e for e in self.logger.entries if start <= e.timestamp <= end and e.user_id == user_id]

        actions = defaultdict(int)
        resources = defaultdict(int)
        failed = 0
        integrity_failed = 0

        for e in entries:
            actions[e.action.value] += 1
            resources[e.resource_type.value] += 1
            if e.status != "success":
                failed += 1
            if not self.logger.verify_integrity(e.entry_id):
                integrity_failed += 1

        return {
            'user_id': user_id,
            'period_days': days,
            'total_actions': len(entries),
            'actions_breakdown': dict(actions),
            'resources_breakdown': dict(resources),
            'failed_actions': failed,
            'integrity_failures': integrity_failed,
            'success_rate': (
                (len(entries) - failed) / len(entries) * 100
                if entries else 0
            )
        }

    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect suspicious patterns in audit log."""
        anomalies = []

        # Check for failed auth attempts
        auth_failures = [e for e in self.logger.entries if e.action.value == 'authenticate' and e.status != 'success']
        user_failures = defaultdict(int)

        for e in auth_failures:
            user_failures[e.user_id] += 1

        # Flag multiple failures
        for user, count in user_failures.items():
            if count >= 5:
                anomalies.append({
                    'type': 'multiple_auth_failures',
                    'severity': 'high',
                    'user_id': user,
                    'count': count,
                    'description': f'{count} failed authentication attempts'
                })

        # Check for bulk deletions
        deletes = [e for e in self.logger.entries if e.action.value == 'DELETE']
        if len(deletes) > 10:  # More than 10 deletes
            anomalies.append({
                'type': 'bulk_delete',
                'severity': 'high',
                'count': len(deletes),
                'description': f'Bulk delete operation detected: {len(deletes)} deletions'
            })

        # Check for privilege escalation
        auth_changes = [e for e in self.logger.entries if e.action.value == 'AUTHORIZE']
        if len(auth_changes) > 5:
            anomalies.append({
                'type': 'privilege_changes',
                'severity': 'medium',
                'count': len(auth_changes),
                'description': f'Multiple privilege changes detected: {len(auth_changes)}'
            })

        return anomalies

    def get_report(self, report_id: str) -> Optional[ComplianceReport]:
        """Get compliance report by ID."""
        return self.reports.get(report_id)

    def list_reports(self, report_type: Optional[str] = None) -> List[ComplianceReport]:
        """List all reports."""
        reports = list(self.reports.values())

        if report_type:
            reports = [r for r in reports if r.report_type == report_type]

        return sorted(reports, key=lambda r: r.report_date, reverse=True)
