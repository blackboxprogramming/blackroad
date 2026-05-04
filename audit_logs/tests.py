"""Tests for audit logging system."""

import pytest
from datetime import datetime, timedelta
from audit_logs.logger import AuditLogger, ActionType, ResourceType, AuditEntry
from audit_logs.compliance import ComplianceAnalyzer


class TestAuditEntry:
    """Test audit entry."""

    def test_create_entry(self):
        """Test creating audit entry."""
        entry = AuditEntry(
            entry_id='e1',
            timestamp=datetime.utcnow(),
            user_id='user1',
            action=ActionType.CREATE,
            resource_type=ResourceType.USER,
            resource_id='res1',
            changes={'name': 'test'}
        )
        assert entry.entry_id == 'e1'
        assert entry.user_id == 'user1'

    def test_entry_hash(self):
        """Test entry hash calculation."""
        entry = AuditEntry(
            entry_id='e1',
            timestamp=datetime(2026, 5, 1, 12, 0, 0),
            user_id='user1',
            action=ActionType.CREATE,
            resource_type=ResourceType.USER,
            resource_id='res1',
            changes={'name': 'test'}
        )
        hash1 = entry.calculate_hash()
        hash2 = entry.calculate_hash()
        
        assert hash1 == hash2  # Hashes should be consistent

    def test_entry_to_dict(self):
        """Test converting entry to dict."""
        entry = AuditEntry(
            entry_id='e1',
            timestamp=datetime.utcnow(),
            user_id='user1',
            action=ActionType.CREATE,
            resource_type=ResourceType.USER,
            resource_id='res1',
            changes={'name': 'test'}
        )
        d = entry.to_dict()
        assert d['entry_id'] == 'e1'
        assert d['user_id'] == 'user1'


class TestAuditLogger:
    """Test audit logger."""

    def test_create_logger(self):
        """Test creating logger."""
        logger = AuditLogger()
        assert len(logger.entries) == 0

    def test_log_entry(self):
        """Test logging entry."""
        logger = AuditLogger()
        entry = logger.log(
            user_id='user1',
            action=ActionType.CREATE,
            resource_type=ResourceType.USER,
            resource_id='res1',
            changes={'name': 'John'}
        )
        
        assert entry.user_id == 'user1'
        assert len(logger.entries) == 1

    def test_log_multiple_entries(self):
        """Test logging multiple entries."""
        logger = AuditLogger()
        logger.log('user1', ActionType.CREATE, ResourceType.USER, 'res1')
        logger.log('user2', ActionType.UPDATE, ResourceType.USER, 'res1')
        logger.log('user1', ActionType.DELETE, ResourceType.USER, 'res2')
        
        assert len(logger.entries) == 3

    def test_get_entry(self):
        """Test retrieving entry."""
        logger = AuditLogger()
        logged = logger.log('user1', ActionType.CREATE, ResourceType.USER, 'res1')
        
        retrieved = logger.get_entry(logged.entry_id)
        assert retrieved is not None
        assert retrieved.user_id == 'user1'

    def test_verify_integrity(self):
        """Test integrity verification."""
        logger = AuditLogger()
        entry = logger.log('user1', ActionType.CREATE, ResourceType.USER, 'res1')
        
        # Should verify successfully
        assert logger.verify_integrity(entry.entry_id) == True

    def test_get_user_activity(self):
        """Test getting user activity."""
        logger = AuditLogger()
        logger.log('user1', ActionType.CREATE, ResourceType.USER, 'res1')
        logger.log('user1', ActionType.UPDATE, ResourceType.USER, 'res1')
        logger.log('user2', ActionType.CREATE, ResourceType.USER, 'res2')
        
        user1_activity = logger.get_user_activity('user1')
        assert len(user1_activity) == 2

    def test_get_resource_activity(self):
        """Test getting resource activity."""
        logger = AuditLogger()
        logger.log('user1', ActionType.CREATE, ResourceType.USER, 'res1')
        logger.log('user2', ActionType.UPDATE, ResourceType.USER, 'res1')
        logger.log('user3', ActionType.READ, ResourceType.USER, 'res1')
        
        res_activity = logger.get_resource_activity('res1')
        assert len(res_activity) == 3

    def test_get_entries_by_action(self):
        """Test getting entries by action."""
        logger = AuditLogger()
        logger.log('user1', ActionType.CREATE, ResourceType.USER, 'res1')
        logger.log('user2', ActionType.CREATE, ResourceType.USER, 'res2')
        logger.log('user3', ActionType.UPDATE, ResourceType.USER, 'res3')
        
        creates = logger.get_entries_by_action(ActionType.CREATE)
        assert len(creates) == 2

    def test_get_entries_by_resource_type(self):
        """Test getting entries by resource type."""
        logger = AuditLogger()
        logger.log('user1', ActionType.CREATE, ResourceType.USER, 'res1')
        logger.log('user2', ActionType.CREATE, ResourceType.PAYMENT, 'res2')
        logger.log('user3', ActionType.CREATE, ResourceType.USER, 'res3')
        
        users = logger.get_entries_by_resource_type(ResourceType.USER)
        assert len(users) == 2

    def test_get_failed_actions(self):
        """Test getting failed actions."""
        logger = AuditLogger()
        logger.log('user1', ActionType.CREATE, ResourceType.USER, 'res1', status='success')
        logger.log('user2', ActionType.CREATE, ResourceType.USER, 'res2', status='failure')
        logger.log('user3', ActionType.CREATE, ResourceType.USER, 'res3', status='failure')
        
        failed = logger.get_failed_actions()
        assert len(failed) == 2

    def test_search_entries(self):
        """Test searching entries."""
        logger = AuditLogger()
        logger.log('user1', ActionType.CREATE, ResourceType.USER, 'res1', status='success')
        logger.log('user1', ActionType.UPDATE, ResourceType.USER, 'res2', status='success')
        logger.log('user2', ActionType.CREATE, ResourceType.PAYMENT, 'res3', status='failure')
        
        # Search by user
        results = logger.search_entries(user_id='user1')
        assert len(results) == 2
        
        # Search by status
        results = logger.search_entries(status='failure')
        assert len(results) == 1

    def test_log_with_ip_and_agent(self):
        """Test logging with IP and user agent."""
        logger = AuditLogger()
        entry = logger.log(
            user_id='user1',
            action=ActionType.LOGIN,
            resource_type=ResourceType.ACCOUNT,
            resource_id='acc1',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0'
        )
        
        assert entry.ip_address == '192.168.1.1'
        assert entry.user_agent == 'Mozilla/5.0'

    def test_get_stats(self):
        """Test getting statistics."""
        logger = AuditLogger()
        logger.log('user1', ActionType.CREATE, ResourceType.USER, 'res1', status='success')
        logger.log('user1', ActionType.UPDATE, ResourceType.USER, 'res2', status='success')
        logger.log('user2', ActionType.DELETE, ResourceType.USER, 'res3', status='failure')
        
        stats = logger.get_stats()
        assert stats['total_entries'] == 3
        assert stats['successful_actions'] == 2
        assert stats['failed_actions'] == 1
        assert stats['unique_users'] == 2

    def test_export_entries(self):
        """Test exporting entries."""
        logger = AuditLogger()
        logger.log('user1', ActionType.CREATE, ResourceType.USER, 'res1')
        logger.log('user2', ActionType.UPDATE, ResourceType.USER, 'res2')
        
        exported = logger.export_entries(user_id='user1')
        assert len(exported) == 1
        assert exported[0]['user_id'] == 'user1'

    def test_max_entries_limit(self):
        """Test max entries limit."""
        logger = AuditLogger(max_entries=2)
        logger.log('user1', ActionType.CREATE, ResourceType.USER, 'res1')
        logger.log('user2', ActionType.CREATE, ResourceType.USER, 'res2')
        
        with pytest.raises(RuntimeError):
            logger.log('user3', ActionType.CREATE, ResourceType.USER, 'res3')


class TestComplianceAnalyzer:
    """Test compliance analyzer."""

    def setup_method(self):
        """Setup test logger."""
        self.logger = AuditLogger()
        self.analyzer = ComplianceAnalyzer(self.logger)

    def test_create_analyzer(self):
        """Test creating analyzer."""
        assert self.analyzer.logger is not None

    def test_daily_report(self):
        """Test generating daily report."""
        self.logger.log('user1', ActionType.CREATE, ResourceType.USER, 'res1')
        self.logger.log('user2', ActionType.UPDATE, ResourceType.USER, 'res2')
        
        report = self.analyzer.generate_daily_report()
        assert report.total_entries == 2
        assert report.report_type == 'daily'

    def test_monthly_report(self):
        """Test generating monthly report."""
        self.logger.log('user1', ActionType.CREATE, ResourceType.USER, 'res1')
        self.logger.log('user2', ActionType.UPDATE, ResourceType.USER, 'res2')
        
        report = self.analyzer.generate_monthly_report(2026, 5)
        assert report.total_entries >= 0
        assert report.report_type == 'monthly'

    def test_user_report(self):
        """Test generating user report."""
        self.logger.log('user1', ActionType.CREATE, ResourceType.USER, 'res1', status='success')
        self.logger.log('user1', ActionType.UPDATE, ResourceType.USER, 'res2', status='failure')
        
        report = self.analyzer.get_user_report('user1')
        assert report['user_id'] == 'user1'
        assert report['total_actions'] == 2
        assert report['failed_actions'] == 1

    def test_detect_anomalies(self):
        """Test detecting anomalies."""
        # Log many failures
        for i in range(6):
            self.logger.log('attacker', ActionType.AUTHENTICATE, ResourceType.ACCOUNT, 'acc1', status='failure')
        
        anomalies = self.analyzer.detect_anomalies()
        assert len(anomalies) > 0
        assert any(a['type'] == 'multiple_auth_failures' for a in anomalies)

    def test_get_report(self):
        """Test retrieving report."""
        report = self.analyzer.generate_daily_report()
        retrieved = self.analyzer.get_report(report.report_id)
        
        assert retrieved is not None
        assert retrieved.report_id == report.report_id

    def test_list_reports(self):
        """Test listing reports."""
        self.analyzer.generate_daily_report()
        self.analyzer.generate_monthly_report(2026, 5)
        
        reports = self.analyzer.list_reports()
        assert len(reports) == 2

    def test_list_reports_by_type(self):
        """Test filtering reports by type."""
        self.analyzer.generate_daily_report()
        self.analyzer.generate_monthly_report(2026, 5)
        
        daily_reports = self.analyzer.list_reports(report_type='daily')
        assert len(daily_reports) == 1
        assert daily_reports[0].report_type == 'daily'


class TestAuditIntegration:
    """Integration tests."""

    def test_end_to_end_audit(self):
        """Test end-to-end audit workflow."""
        logger = AuditLogger()
        
        # Log various actions
        logger.log('user1', ActionType.LOGIN, ResourceType.ACCOUNT, 'acc1', ip_address='192.168.1.1')
        logger.log('user1', ActionType.CREATE, ResourceType.USER, 'user2')
        logger.log('user1', ActionType.UPDATE, ResourceType.USER, 'user2', changes={'name': 'John'})
        logger.log('user1', ActionType.LOGOUT, ResourceType.ACCOUNT, 'acc1')
        
        # Verify integrity
        for entry in logger.entries:
            assert logger.verify_integrity(entry.entry_id)
        
        # Get stats
        stats = logger.get_stats()
        assert stats['total_entries'] == 4
        assert stats['successful_actions'] == 4

    def test_compliance_workflow(self):
        """Test compliance workflow."""
        logger = AuditLogger()
        analyzer = ComplianceAnalyzer(logger)
        
        # Log actions
        logger.log('user1', ActionType.CREATE, ResourceType.USER, 'res1', status='success')
        logger.log('user1', ActionType.DELETE, ResourceType.USER, 'res1', status='success')
        logger.log('user2', ActionType.AUTHENTICATE, ResourceType.ACCOUNT, 'acc1', status='failure')
        
        # Generate report
        report = analyzer.generate_daily_report()
        assert report.total_entries == 3
        assert report.failed_actions == 1

    def test_audit_with_changes(self):
        """Test auditing with detailed changes."""
        logger = AuditLogger()
        
        changes = {
            'before': {'name': 'Old Name', 'email': 'old@example.com'},
            'after': {'name': 'New Name', 'email': 'new@example.com'}
        }
        
        entry = logger.log(
            'user1',
            ActionType.UPDATE,
            ResourceType.USER,
            'user2',
            changes=changes
        )
        
        assert entry.changes == changes

    def test_audit_export_compliance(self):
        """Test exporting audit logs for compliance."""
        logger = AuditLogger()
        
        start_date = datetime.utcnow()
        logger.log('user1', ActionType.CREATE, ResourceType.USER, 'res1')
        logger.log('user1', ActionType.UPDATE, ResourceType.USER, 'res2')
        end_date = datetime.utcnow()
        
        exported = logger.export_entries(
            user_id='user1',
            start_date=start_date,
            end_date=end_date
        )
        
        assert len(exported) == 2
        assert all(e['user_id'] == 'user1' for e in exported)


# Run tests if executed directly
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
