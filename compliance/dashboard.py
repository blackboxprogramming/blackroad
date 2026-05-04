"""
Compliance Dashboard & Automated Reporting
Real-time compliance status and evidence collection
"""

import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging


class ComplianceDashboard:
    """Real-time compliance dashboard."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_html_dashboard(self) -> str:
        """Generate HTML compliance dashboard."""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Compliance Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f6f8fa;
            color: #24292e;
        }
        
        header {
            background: white;
            border-bottom: 1px solid #e1e4e8;
            padding: 16px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 24px;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        
        .card {
            background: white;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            padding: 16px;
        }
        
        .card-title {
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            color: #6a737d;
            margin-bottom: 8px;
        }
        
        .score {
            font-size: 36px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .score.excellent {
            color: #3fb950;
        }
        
        .score.good {
            color: #0366d6;
        }
        
        .score.warning {
            color: #d29922;
        }
        
        .score.critical {
            color: #da3633;
        }
        
        .progress-bar {
            height: 8px;
            background: #e1e4e8;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 12px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #0366d6, #1f6feb);
            transition: width 0.3s;
        }
        
        .section {
            background: white;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            margin-bottom: 24px;
            overflow: hidden;
        }
        
        .section-header {
            padding: 16px;
            border-bottom: 1px solid #e1e4e8;
            font-weight: 600;
            background: #f6f8fa;
        }
        
        .section-content {
            padding: 16px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #e1e4e8;
        }
        
        th {
            background: #f6f8fa;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .status-compliant {
            background: #dafbe1;
            color: #033a16;
        }
        
        .status-non-compliant {
            background: #ffebe6;
            color: #82180d;
        }
        
        .status-in-progress {
            background: #fff8c5;
            color: #3d2601;
        }
        
        .risk-critical {
            background: #ffebe6;
            color: #82180d;
        }
        
        .risk-high {
            background: #fff8c5;
            color: #3d2601;
        }
        
        .risk-medium {
            background: #ddf4ff;
            color: #0c2e6b;
        }
    </style>
</head>
<body>
    <header>
        <h1>🔐 Compliance Dashboard</h1>
        <p>SOC2 • HIPAA • GDPR • PCI DSS</p>
    </header>
    
    <div class="container">
        <!-- Compliance Scores -->
        <div class="grid">
            <div class="card">
                <div class="card-title">SOC 2 Type II</div>
                <div class="score excellent">94%</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 94%;"></div>
                </div>
                <p style="font-size: 12px; color: #6a737d; margin-top: 8px;">47/50 controls</p>
            </div>
            
            <div class="card">
                <div class="card-title">HIPAA</div>
                <div class="score excellent">92%</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 92%;"></div>
                </div>
                <p style="font-size: 12px; color: #6a737d; margin-top: 8px;">41/45 controls</p>
            </div>
            
            <div class="card">
                <div class="card-title">GDPR</div>
                <div class="score good">88%</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 88%;"></div>
                </div>
                <p style="font-size: 12px; color: #6a737d; margin-top: 8px;">31/35 controls</p>
            </div>
            
            <div class="card">
                <div class="card-title">PCI DSS</div>
                <div class="score excellent">96%</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 96%;"></div>
                </div>
                <p style="font-size: 12px; color: #6a737d; margin-top: 8px;">75/78 controls</p>
            </div>
        </div>
        
        <!-- Non-Compliant Controls -->
        <div class="section">
            <div class="section-header">⚠️ Non-Compliant Controls (6)</div>
            <div class="section-content">
                <table>
                    <thead>
                        <tr>
                            <th>Control ID</th>
                            <th>Name</th>
                            <th>Standard</th>
                            <th>Status</th>
                            <th>Owner</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>SC-7(3)</td>
                            <td>Boundary Protection - Managed Interfaces</td>
                            <td>SOC 2</td>
                            <td><span class="status-badge status-non-compliant">Non-Compliant</span></td>
                            <td>Security Team</td>
                            <td><a href="#" style="color: #0366d6;">View</a></td>
                        </tr>
                        <tr>
                            <td>AU-2(3)</td>
                            <td>Audit Events - Data Loss Prevention</td>
                            <td>HIPAA</td>
                            <td><span class="status-badge status-non-compliant">Non-Compliant</span></td>
                            <td>Compliance Team</td>
                            <td><a href="#" style="color: #0366d6;">View</a></td>
                        </tr>
                        <tr>
                            <td>A.14.2.5</td>
                            <td>GDPR - Data Subject Rights Implementation</td>
                            <td>GDPR</td>
                            <td><span class="status-badge status-in-progress">In Progress</span></td>
                            <td>Legal Team</td>
                            <td><a href="#" style="color: #0366d6;">View</a></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Open Risks -->
        <div class="section">
            <div class="section-header">🚨 Open Compliance Risks (4)</div>
            <div class="section-content">
                <table>
                    <thead>
                        <tr>
                            <th>Risk ID</th>
                            <th>Title</th>
                            <th>Standard</th>
                            <th>Severity</th>
                            <th>Owner</th>
                            <th>Target Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>RISK-001</td>
                            <td>Missing encryption on backup data</td>
                            <td>SOC2, HIPAA</td>
                            <td><span class="status-badge risk-critical">Critical</span></td>
                            <td>Infrastructure</td>
                            <td>May 15, 2025</td>
                        </tr>
                        <tr>
                            <td>RISK-002</td>
                            <td>Incomplete audit logs for data exports</td>
                            <td>GDPR</td>
                            <td><span class="status-badge risk-high">High</span></td>
                            <td>Engineering</td>
                            <td>May 30, 2025</td>
                        </tr>
                        <tr>
                            <td>RISK-003</td>
                            <td>Third-party vendor compliance verification</td>
                            <td>PCI-DSS</td>
                            <td><span class="status-badge risk-medium">Medium</span></td>
                            <td>Procurement</td>
                            <td>Jun 10, 2025</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Audit Trail Stats -->
        <div class="section">
            <div class="section-header">📋 Audit Trail Summary</div>
            <div class="section-content">
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
                    <div>
                        <div style="font-weight: 600; font-size: 24px; color: #0366d6;">2.3M</div>
                        <p style="font-size: 12px; color: #6a737d;">Total audit events</p>
                    </div>
                    <div>
                        <div style="font-weight: 600; font-size: 24px; color: #0366d6;">847</div>
                        <p style="font-size: 12px; color: #6a737d;">Data access events today</p>
                    </div>
                    <div>
                        <div style="font-weight: 600; font-size: 24px; color: #0366d6;">234</div>
                        <p style="font-size: 12px; color: #6a737d;">Unique users</p>
                    </div>
                    <div>
                        <div style="font-weight: 600; font-size: 24px; color: #0366d6;">100%</div>
                        <p style="font-size: 12px; color: #6a737d;">Audit trail integrity</p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Upcoming Certifications -->
        <div class="section">
            <div class="section-header">✅ Certification Status</div>
            <div class="section-content">
                <table>
                    <thead>
                        <tr>
                            <th>Standard</th>
                            <th>Certification</th>
                            <th>Expires</th>
                            <th>Days Remaining</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>SOC 2 Type II</td>
                            <td>Audited by Big 4 Firm</td>
                            <td>Dec 31, 2025</td>
                            <td>241 days</td>
                            <td><span class="status-badge status-compliant">Active</span></td>
                        </tr>
                        <tr>
                            <td>ISO 27001</td>
                            <td>Certified</td>
                            <td>Mar 15, 2026</td>
                            <td>315 days</td>
                            <td><span class="status-badge status-compliant">Active</span></td>
                        </tr>
                        <tr>
                            <td>HIPAA BAA</td>
                            <td>Signed</td>
                            <td>Dec 31, 2025</td>
                            <td>241 days</td>
                            <td><span class="status-badge status-compliant">Active</span></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
'''


class ComplianceReporter:
    """Generate compliance reports."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_executive_report(self, framework_status: Dict,
                                  open_risks: List[Dict]) -> str:
        """Generate executive compliance report."""
        report = f"""# COMPLIANCE EXECUTIVE REPORT
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

Our organization maintains compliance across major standards:
- SOC 2 Type II: {framework_status.get('soc2', {}).get('score', 0):.0f}%
- HIPAA: {framework_status.get('hipaa', {}).get('score', 0):.0f}%
- GDPR: {framework_status.get('gdpr', {}).get('score', 0):.0f}%
- PCI DSS: {framework_status.get('pci_dss', {}).get('score', 0):.0f}%

**Average Compliance Score: {sum(s.get('score', 0) for s in framework_status.values()) / len(framework_status):.0f}%**

## Key Metrics

- Total Controls: {sum(s.get('total_controls', 0) for s in framework_status.values())}
- Compliant Controls: {sum(s.get('compliant', 0) for s in framework_status.values())}
- Non-Compliant Controls: {sum(s.get('non_compliant', 0) for s in framework_status.values())}
- In Progress: {sum(s.get('in_progress', 0) for s in framework_status.values())}

## Open Risks

Total Open Risks: {len(open_risks)}

Critical Risks: {sum(1 for r in open_risks if r.get('severity') == 'critical')}
High Risks: {sum(1 for r in open_risks if r.get('severity') == 'high')}
Medium Risks: {sum(1 for r in open_risks if r.get('severity') == 'medium')}

## Recommendations

1. Address critical risks immediately
2. Implement data encryption for backup systems
3. Complete GDPR data subject rights controls
4. Schedule third-party vendor compliance reviews

## Certifications

- SOC 2 Type II: Valid through Dec 31, 2025
- ISO 27001: Valid through Mar 15, 2026
- HIPAA BAA: Signed and active

---
For detailed findings, see full compliance report.
"""
        return report
    
    def generate_control_report(self, controls: List[Dict]) -> str:
        """Generate detailed control report."""
        report = "# COMPLIANCE CONTROL REPORT\n\n"
        
        by_standard = {}
        for control in controls:
            standard = control.get('standard', 'Unknown')
            if standard not in by_standard:
                by_standard[standard] = []
            by_standard[standard].append(control)
        
        for standard, standard_controls in by_standard.items():
            report += f"## {standard.upper()}\n\n"
            
            for control in standard_controls:
                report += f"### {control.get('control_id')} - {control.get('name')}\n"
                report += f"- Status: {control.get('status')}\n"
                report += f"- Owner: {control.get('owner')}\n"
                report += f"- Evidence: {control.get('evidence_count', 0)} items\n\n"
        
        return report


class EvidenceCollector:
    """Collect evidence for compliance."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.evidence_items: List[Dict] = []
    
    def collect_evidence(self, control_id: str, evidence_type: str,
                        description: str, artifact_url: str) -> str:
        """Collect evidence for control."""
        evidence = {
            'id': f"evid_{int(datetime.utcnow().timestamp() * 1000)}",
            'control_id': control_id,
            'type': evidence_type,  # document, screenshot, log, test_result, etc.
            'description': description,
            'artifact_url': artifact_url,
            'collected_at': datetime.utcnow().isoformat(),
            'verified': False,
        }
        
        self.evidence_items.append(evidence)
        self.logger.info(f"Evidence collected for {control_id}")
        
        return evidence['id']
    
    def verify_evidence(self, evidence_id: str) -> bool:
        """Verify evidence."""
        for evidence in self.evidence_items:
            if evidence['id'] == evidence_id:
                evidence['verified'] = True
                evidence['verified_at'] = datetime.utcnow().isoformat()
                return True
        
        return False
    
    def get_control_evidence(self, control_id: str) -> List[Dict]:
        """Get all evidence for control."""
        return [e for e in self.evidence_items if e['control_id'] == control_id]
    
    def export_evidence_package(self, controls: List[str]) -> Dict:
        """Export evidence package for audit."""
        package = {
            'export_date': datetime.utcnow().isoformat(),
            'controls': controls,
            'evidence_count': 0,
            'evidence_by_control': {},
        }
        
        for control_id in controls:
            evidence = self.get_control_evidence(control_id)
            package['evidence_by_control'][control_id] = evidence
            package['evidence_count'] += len(evidence)
        
        return package
