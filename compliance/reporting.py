"""
Compliance Reporting & Certification Module
PDF generation, audit readiness, assessment workflows
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import json


class ReportType(Enum):
    EXECUTIVE = "executive"
    DETAILED = "detailed"
    AUDIT_READY = "audit_ready"
    GAP_ANALYSIS = "gap_analysis"
    CERTIFICATION_PREP = "certification_prep"


class CertificationStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    AUDIT_SCHEDULED = "audit_scheduled"
    PENDING_APPROVAL = "pending_approval"
    CERTIFIED = "certified"
    EXPIRED = "expired"


class ComplianceReport:
    """Generate compliance reports."""
    
    def __init__(self):
        self.generated_at = datetime.utcnow()
    
    def generate_pdf_report(self, report_type: ReportType,
                           framework: str,
                           framework_status: Dict,
                           controls: List[Dict],
                           open_risks: List[Dict],
                           recommendations: List[str]) -> str:
        """Generate PDF-formatted compliance report."""
        
        pdf_content = f"""%%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length 2500 >>
stream
BT
/F1 24 Tf
50 750 Td
({framework} Compliance Report) Tj
0 -30 Td
/F1 12 Tf
(Generated: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}) Tj
0 -20 Td
/F1 14 Tf
(Executive Summary) Tj
0 -15 Td
/F1 10 Tf
(Compliance Score: {framework_status.get('score', 0):.0f}%) Tj
0 -12 Td
(Compliant Controls: {framework_status.get('compliant', 0)}/{framework_status.get('total_controls', 0)}) Tj
0 -12 Td
(Status: {framework_status.get('status', 'Unknown')}) Tj
0 -20 Td
/F1 14 Tf
(Key Findings) Tj
0 -15 Td
/F1 10 Tf
(Non-Compliant Controls: {framework_status.get('non_compliant', 0)}) Tj
0 -12 Td
(Open Risks: {len(open_risks)}) Tj
0 -12 Td
(Critical Risks: {sum(1 for r in open_risks if r.get('severity') == 'critical')}) Tj
0 -20 Td
/F1 14 Tf
(Recommendations) Tj
0 -15 Td
/F1 10 Tf
"""
        
        for i, recommendation in enumerate(recommendations[:5], 1):
            pdf_content += f"({i}. {recommendation[:60]}) Tj\n0 -12 Td\n"
        
        pdf_content += """ET
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000233 00000 n 
0000000333 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
2900
%%EOF
"""
        
        return pdf_content
    
    def generate_audit_readiness_report(self, framework: str,
                                      controls_status: Dict,
                                      evidence_status: Dict,
                                      policy_status: Dict) -> Dict:
        """Generate audit readiness assessment."""
        
        readiness = {
            'framework': framework,
            'generated_at': self.generated_at.isoformat(),
            'overall_readiness': 0,
            'dimensions': {
                'controls': {
                    'score': 0,
                    'status': 'Not Started',
                    'details': 'Control implementation progress',
                    'complete': 0,
                    'total': 0,
                },
                'evidence': {
                    'score': 0,
                    'status': 'Not Started',
                    'details': 'Evidence collection and organization',
                    'collected': 0,
                    'needed': 0,
                },
                'policies': {
                    'score': 0,
                    'status': 'Not Started',
                    'details': 'Policy documentation and reviews',
                    'documented': 0,
                    'total': 0,
                },
                'training': {
                    'score': 0,
                    'status': 'Not Started',
                    'details': 'Staff training completion',
                    'trained': 0,
                    'total': 0,
                },
            },
            'readiness_timeline': {
                'weeks_to_ready': 0,
                'recommended_audit_date': None,
                'critical_path': [],
            },
            'gaps': [],
            'recommendations': [],
        }
        
        # Calculate scores
        if controls_status.get('total', 0) > 0:
            controls_score = (controls_status.get('complete', 0) / 
                            controls_status.get('total', 1)) * 100
            readiness['dimensions']['controls']['score'] = int(controls_score)
            readiness['dimensions']['controls']['complete'] = controls_status.get('complete', 0)
            readiness['dimensions']['controls']['total'] = controls_status.get('total', 0)
        
        if evidence_status.get('needed', 0) > 0:
            evidence_score = (evidence_status.get('collected', 0) / 
                            evidence_status.get('needed', 1)) * 100
            readiness['dimensions']['evidence']['score'] = int(evidence_score)
            readiness['dimensions']['evidence']['collected'] = evidence_status.get('collected', 0)
            readiness['dimensions']['evidence']['needed'] = evidence_status.get('needed', 0)
        
        if policy_status.get('total', 0) > 0:
            policy_score = (policy_status.get('documented', 0) / 
                          policy_status.get('total', 1)) * 100
            readiness['dimensions']['policies']['score'] = int(policy_score)
            readiness['dimensions']['policies']['documented'] = policy_status.get('documented', 0)
            readiness['dimensions']['policies']['total'] = policy_status.get('total', 0)
        
        # Calculate overall readiness
        dimension_scores = [d.get('score', 0) for d in readiness['dimensions'].values()]
        readiness['overall_readiness'] = int(sum(dimension_scores) / len(dimension_scores))
        
        # Timeline
        if readiness['overall_readiness'] >= 80:
            readiness['readiness_timeline']['weeks_to_ready'] = 2
            readiness['readiness_timeline']['recommended_audit_date'] = (
                (self.generated_at + timedelta(weeks=2)).isoformat()
            )
        elif readiness['overall_readiness'] >= 60:
            readiness['readiness_timeline']['weeks_to_ready'] = 4
            readiness['readiness_timeline']['recommended_audit_date'] = (
                (self.generated_at + timedelta(weeks=4)).isoformat()
            )
        else:
            readiness['readiness_timeline']['weeks_to_ready'] = 8
            readiness['readiness_timeline']['recommended_audit_date'] = (
                (self.generated_at + timedelta(weeks=8)).isoformat()
            )
        
        # Identify gaps
        for dimension, data in readiness['dimensions'].items():
            if data['score'] < 70:
                readiness['gaps'].append({
                    'dimension': dimension,
                    'current_score': data['score'],
                    'target_score': 90,
                    'priority': 'high' if data['score'] < 50 else 'medium',
                })
        
        # Recommendations
        if readiness['dimensions']['controls']['score'] < 80:
            readiness['recommendations'].append(
                f"Complete remaining {controls_status.get('total', 0) - controls_status.get('complete', 0)} controls"
            )
        if readiness['dimensions']['evidence']['score'] < 80:
            readiness['recommendations'].append(
                f"Collect {evidence_status.get('needed', 0) - evidence_status.get('collected', 0)} missing evidence items"
            )
        if readiness['dimensions']['policies']['score'] < 80:
            readiness['recommendations'].append(
                f"Document {policy_status.get('total', 0) - policy_status.get('documented', 0)} policies"
            )
        
        return readiness


class CertificationTracker:
    """Track compliance certifications."""
    
    def __init__(self):
        self.certifications: Dict[str, Dict] = {}
    
    def add_certification(self, standard: str, status: CertificationStatus,
                         issued_date: Optional[datetime] = None,
                         expiry_date: Optional[datetime] = None,
                         auditor: Optional[str] = None) -> None:
        """Add certification."""
        self.certifications[standard] = {
            'standard': standard,
            'status': status.value,
            'issued_date': issued_date.isoformat() if issued_date else None,
            'expiry_date': expiry_date.isoformat() if expiry_date else None,
            'auditor': auditor,
            'last_updated': datetime.utcnow().isoformat(),
        }
    
    def get_certification(self, standard: str) -> Optional[Dict]:
        """Get certification details."""
        return self.certifications.get(standard)
    
    def get_expiring_certifications(self, days_threshold: int = 90) -> List[Dict]:
        """Get certifications expiring soon."""
        expiring = []
        threshold_date = datetime.utcnow() + timedelta(days=days_threshold)
        
        for cert in self.certifications.values():
            if cert['expiry_date']:
                expiry = datetime.fromisoformat(cert['expiry_date'])
                if datetime.utcnow() < expiry < threshold_date:
                    days_remaining = (expiry - datetime.utcnow()).days
                    cert['days_remaining'] = days_remaining
                    expiring.append(cert)
        
        return sorted(expiring, key=lambda x: x.get('days_remaining', 0))
    
    def get_certification_summary(self) -> Dict:
        """Get certification portfolio summary."""
        return {
            'total_certifications': len(self.certifications),
            'active': sum(1 for c in self.certifications.values() 
                         if c['status'] == 'certified'),
            'in_progress': sum(1 for c in self.certifications.values() 
                              if c['status'] == 'in_progress'),
            'expiring_soon': len(self.get_expiring_certifications()),
            'certifications': self.certifications,
        }


class AssessmentWorkflow:
    """Manage compliance assessments."""
    
    def __init__(self):
        self.assessments: List[Dict] = []
    
    def create_assessment(self, framework: str, assessment_type: str,
                         scope: List[str], scheduled_date: Optional[datetime] = None) -> str:
        """Create assessment."""
        assessment = {
            'id': f"assess_{int(datetime.utcnow().timestamp() * 1000)}",
            'framework': framework,
            'type': assessment_type,  # self-assessment, gap-analysis, audit-prep
            'scope': scope,
            'scheduled_date': scheduled_date.isoformat() if scheduled_date else None,
            'created_at': datetime.utcnow().isoformat(),
            'status': 'planned',
            'findings': [],
            'remediation_items': [],
        }
        
        self.assessments.append(assessment)
        return assessment['id']
    
    def add_finding(self, assessment_id: str, finding_type: str,
                   severity: str, description: str,
                   affected_controls: List[str]) -> None:
        """Add assessment finding."""
        for assessment in self.assessments:
            if assessment['id'] == assessment_id:
                finding = {
                    'id': f"find_{int(datetime.utcnow().timestamp() * 1000)}",
                    'type': finding_type,
                    'severity': severity,  # critical, high, medium, low
                    'description': description,
                    'affected_controls': affected_controls,
                    'found_at': datetime.utcnow().isoformat(),
                    'remediated': False,
                }
                assessment['findings'].append(finding)
    
    def complete_assessment(self, assessment_id: str, summary: str) -> bool:
        """Complete assessment."""
        for assessment in self.assessments:
            if assessment['id'] == assessment_id:
                assessment['status'] = 'completed'
                assessment['completed_at'] = datetime.utcnow().isoformat()
                assessment['summary'] = summary
                return True
        
        return False
    
    def get_assessment_report(self, assessment_id: str) -> Optional[Dict]:
        """Get assessment report."""
        for assessment in self.assessments:
            if assessment['id'] == assessment_id:
                return {
                    'id': assessment['id'],
                    'framework': assessment['framework'],
                    'type': assessment['type'],
                    'status': assessment['status'],
                    'findings_count': len(assessment['findings']),
                    'critical_findings': sum(1 for f in assessment['findings'] 
                                            if f['severity'] == 'critical'),
                    'high_findings': sum(1 for f in assessment['findings'] 
                                        if f['severity'] == 'high'),
                    'summary': assessment.get('summary', 'Assessment in progress'),
                    'findings': assessment['findings'],
                }
        
        return None
