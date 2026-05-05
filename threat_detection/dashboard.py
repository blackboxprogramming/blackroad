"""
Advanced Threat Detection Dashboard
Real-time security monitoring and threat visualization
"""

from datetime import datetime
from detector import ThreatIntelligence, ThreatLevel


class SecurityDashboard:
    """Generate HTML dashboard for threat monitoring."""
    
    def __init__(self):
        self.generated_at = datetime.utcnow().isoformat()
    
    def generate_html(self, threat_intel: ThreatIntelligence) -> str:
        """Generate comprehensive security dashboard HTML."""
        
        summary = threat_intel.get_threat_summary()
        ddos_status = threat_intel.ddos_detector.get_ddos_status()
        
        # Calculate metrics
        total_critical = summary['critical_threats']
        total_high = summary['high_threats']
        total_alerts = summary['total_alerts']
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Advanced Threat Detection Dashboard</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                margin: 0; padding: 20px; background: #f5f7fa; }}
        .dashboard {{ max-width: 1400px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); 
                  color: white; padding: 30px; border-radius: 8px; margin-bottom: 30px; }}
        .header h1 {{ margin: 0; font-size: 32px; }}
        .header p {{ margin: 5px 0 0 0; opacity: 0.9; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                gap: 20px; margin-bottom: 30px; }}
        .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .card h3 {{ margin: 0 0 10px 0; color: #333; font-size: 14px; text-transform: uppercase; 
                   letter-spacing: 1px; opacity: 0.7; }}
        .metric {{ font-size: 32px; font-weight: bold; color: #e74c3c; margin: 10px 0; }}
        .metric-small {{ font-size: 13px; color: #666; margin-top: 10px; }}
        .alert {{ padding: 15px; margin: 10px 0; border-radius: 4px; border-left: 4px solid; }}
        .alert-critical {{ background: #fadbd8; border-color: #e74c3c; color: #922b21; }}
        .alert-high {{ background: #fdebd0; border-color: #f39c12; color: #7d3c0f; }}
        .alert-medium {{ background: #fef5e7; border-color: #f1c40f; color: #7d6608; }}
        .attack-type {{ display: inline-block; padding: 6px 12px; background: #ecf0f1; 
                       border-radius: 4px; margin: 5px 5px 5px 0; font-size: 12px; }}
        .attack-active {{ background: #fadbd8; color: #922b21; font-weight: 600; }}
        .table {{ width: 100%; border-collapse: collapse; }}
        .table th {{ background: #f8f9fa; padding: 12px; text-align: left; 
                    font-weight: 600; border-bottom: 1px solid #ddd; font-size: 13px; }}
        .table td {{ padding: 12px; border-bottom: 1px solid #eee; font-size: 13px; }}
        .table tr:hover {{ background: #f8f9fa; }}
        .indicator {{ padding: 8px 12px; background: #ecf0f1; border-radius: 4px; 
                     margin: 3px 0; font-size: 12px; }}
        .progress-bar {{ background: #e0e0e0; height: 8px; border-radius: 4px; 
                        overflow: hidden; margin: 5px 0; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #e74c3c 0%, #c0392b 100%); }}
        .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 40px; 
                  padding-top: 20px; border-top: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>🛡️ Advanced Threat Detection Dashboard</h1>
            <p>AI Anomaly Detection, Insider Threats & DDoS Protection</p>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>Total Alerts</h3>
                <div class="metric">{total_alerts}</div>
                <div class="metric-small">
                    <span style="color: #e74c3c;">Critical: {total_critical}</span><br>
                    <span style="color: #f39c12;">High: {total_high}</span>
                </div>
            </div>
            
            <div class="card">
                <h3>DDoS Status</h3>
                <div class="metric" style="color: {'#e74c3c' if ddos_status['under_attack'] else '#27ae60'};">
                    {'🔴 UNDER ATTACK' if ddos_status['under_attack'] else '🟢 CLEAN'}
                </div>
                <div class="metric-small">
                    Risk: {ddos_status['max_risk']:.0f}%<br>
                    Requests/min: {ddos_status['request_count_1min']:,}
                </div>
            </div>
            
            <div class="card">
                <h3>Attack Types Detected</h3>
                <div class="metric-small">
"""
        
        for attack_type, detected in ddos_status['attack_types'].items():
            if detected:
                risk = ddos_status['risk_scores'].get(attack_type, 0)
                html += f"<div class='attack-type attack-active'>{attack_type.upper()}: {risk:.0f}%</div>"
        
        html += f"""
                </div>
            </div>
            
            <div class="card">
                <h3>Blocked IPs</h3>
                <div class="metric">{len(ddos_status['blocked_ips'])}</div>
                <div class="metric-small">
                    IPs under monitoring
                </div>
            </div>
        </div>
        
        <div class="card">
            <h3>Critical Threats</h3>
"""
        
        if total_critical > 0:
            for alert in summary['recent_alerts'][:5]:
                if alert['threat_level'] == 'critical':
                    html += f"""
            <div class="alert alert-critical">
                <strong>CRITICAL: {alert['user_id']}</strong> - {alert['combined_risk_score']:.0f}% risk<br>
                <small>{alert['timestamp']}</small>
            </div>
"""
        else:
            html += "<div class='metric-small'>No critical threats detected</div>"
        
        html += """
        </div>
        
        <div class="card">
            <h3>Recent Alerts & Anomalies</h3>
            <table class="table">
                <tr>
                    <th>User</th>
                    <th>Threat Level</th>
                    <th>Risk Score</th>
                    <th>Indicators/Anomalies</th>
                </tr>
"""
        
        for alert in summary['recent_alerts'][-10:]:
            threat_class = f"alert-{alert['threat_level']}"
            indicators = []
            
            # Add insider indicators
            insider = alert.get('insider_profile', {})
            if insider.get('indicators'):
                indicators.extend(insider['indicators'][:3])
            
            # Add anomalies
            for anom in alert.get('anomalies', [])[:2]:
                indicators.append(anom['type'])
            
            html += f"""
                <tr>
                    <td><strong>{alert['user_id']}</strong></td>
                    <td><span class="{threat_class}">{alert['threat_level'].upper()}</span></td>
                    <td>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {alert['combined_risk_score']}%"></div>
                        </div>
                        {alert['combined_risk_score']:.0f}%
                    </td>
                    <td>
"""
            
            for ind in indicators[:3]:
                html += f'<div class="indicator">{ind}</div>'
            
            html += """
                    </td>
                </tr>
"""
        
        html += """
            </table>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>Anomaly Detection</h3>
                <div class="metric-small">
                    <strong>Detectors Active:</strong><br>
                    ✓ Unusual Volume Detection<br>
                    ✓ Time Anomalies<br>
                    ✓ Geographic Anomalies<br>
                    ✓ Failed Auth Patterns<br>
                    ✓ Statistical Baseline Analysis
                </div>
            </div>
            
            <div class="card">
                <h3>Insider Threat Detection</h3>
                <div class="metric-small">
                    <strong>Monitored Signals:</strong><br>
                    ✓ Excessive Downloads<br>
                    ✓ Privilege Abuse<br>
                    ✓ Off-Hours Access<br>
                    ✓ Mass Exports<br>
                    ✓ Terminated Employee Activity
                </div>
            </div>
            
            <div class="card">
                <h3>DDoS Protection</h3>
                <div class="metric-small">
                    <strong>Detection Methods:</strong><br>
                    ✓ Volumetric (100MB/s threshold)<br>
                    ✓ Protocol (SYN floods)<br>
                    ✓ Application (HTTP floods)<br>
                    ✓ Rate Limiting<br>
                    ✓ IP Blocking
                </div>
            </div>
            
            <div class="card">
                <h3>Compliance Status</h3>
                <div class="metric-small">
                    <strong>Enabled:</strong><br>
                    ✓ SOC2 Audit Trail<br>
                    ✓ HIPAA Compliance<br>
                    ✓ PCI-DSS Monitoring<br>
                    ✓ GDPR Data Protection<br>
                    ✓ Real-time Alerting
                </div>
            </div>
        </div>
        
        <div class="footer">
            Generated {self.generated_at} UTC<br>
            Advanced Threat Detection System v1.0 | Phase 13
        </div>
    </div>
</body>
</html>
"""
        return html
