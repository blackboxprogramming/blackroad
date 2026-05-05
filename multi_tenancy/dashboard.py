"""
Multi-Tenant Dashboard
Real-time tenant management and billing visualization
"""

from datetime import datetime
from isolation import MultiTenantOrchestrator, TenantTier


class MultiTenantDashboard:
    """Generate HTML dashboard for multi-tenant operations."""
    
    def __init__(self):
        self.generated_at = datetime.utcnow().isoformat()
    
    def generate_html(self, orchestrator: MultiTenantOrchestrator) -> str:
        """Generate comprehensive multi-tenant dashboard HTML."""
        
        total_tenants = len(orchestrator.tenants)
        total_monthly_revenue = sum(t.monthly_cost for t in orchestrator.tenants.values())
        total_api_calls = sum(t.monthly_api_calls for t in orchestrator.tenants.values())
        total_storage = sum(t.storage_gb for t in orchestrator.tenants.values())
        
        # Tier distribution
        tier_counts = {'starter': 0, 'professional': 0, 'enterprise': 0}
        for tenant in orchestrator.tenants.values():
            tier_counts[tenant.tier.value] += 1
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Multi-Tenant Management Dashboard</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                margin: 0; padding: 20px; background: #f5f7fa; }}
        .dashboard {{ max-width: 1400px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                  color: white; padding: 30px; border-radius: 8px; margin-bottom: 30px; }}
        .header h1 {{ margin: 0; font-size: 32px; }}
        .header p {{ margin: 5px 0 0 0; opacity: 0.9; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                gap: 20px; margin-bottom: 30px; }}
        .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .card h3 {{ margin: 0 0 10px 0; color: #333; font-size: 14px; text-transform: uppercase; 
                   letter-spacing: 1px; opacity: 0.7; }}
        .metric {{ font-size: 32px; font-weight: bold; color: #667eea; margin: 10px 0; }}
        .metric-small {{ font-size: 13px; color: #666; margin-top: 10px; }}
        .table {{ width: 100%; border-collapse: collapse; }}
        .table th {{ background: #f8f9fa; padding: 12px; text-align: left; 
                    font-weight: 600; border-bottom: 1px solid #ddd; font-size: 13px; }}
        .table td {{ padding: 12px; border-bottom: 1px solid #eee; font-size: 13px; }}
        .table tr:hover {{ background: #f8f9fa; }}
        .tier-starter {{ background: #e8f4f8; color: #0277bd; }}
        .tier-professional {{ background: #f3e5f5; color: #6a1b9a; }}
        .tier-enterprise {{ background: #fff3e0; color: #e65100; }}
        .usage-bar {{ background: #e0e0e0; height: 6px; border-radius: 3px; overflow: hidden; margin: 5px 0; }}
        .usage-fill {{ height: 100%; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); }}
        .status-active {{ color: #27ae60; font-weight: 600; }}
        .status-warning {{ color: #f39c12; font-weight: 600; }}
        .status-critical {{ color: #e74c3c; font-weight: 600; }}
        .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 40px; 
                  padding-top: 20px; border-top: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>🏢 Multi-Tenant Management Dashboard</h1>
            <p>Tenant Provisioning, Billing, and Isolation Control</p>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>Total Tenants</h3>
                <div class="metric">{total_tenants}</div>
                <div class="metric-small">
                    Starter: {tier_counts['starter']}<br>
                    Pro: {tier_counts['professional']}<br>
                    Enterprise: {tier_counts['enterprise']}
                </div>
            </div>
            
            <div class="card">
                <h3>Monthly Revenue</h3>
                <div class="metric">${total_monthly_revenue:,.0f}</div>
                <div class="metric-small">
                    Avg: ${total_monthly_revenue/max(1, total_tenants):,.0f}/tenant
                </div>
            </div>
            
            <div class="card">
                <h3>API Calls (Month)</h3>
                <div class="metric">{total_api_calls:,.0f}</div>
                <div class="metric-small">
                    Avg: {total_api_calls//max(1, total_tenants):,.0f}/tenant
                </div>
            </div>
            
            <div class="card">
                <h3>Storage Used</h3>
                <div class="metric">{total_storage:.1f} GB</div>
                <div class="metric-small">
                    Avg: {total_storage/max(1, total_tenants):.1f} GB/tenant
                </div>
            </div>
        </div>
        
        <div class="card">
            <h3>Tenant Directory</h3>
            <table class="table">
                <tr>
                    <th>Company</th>
                    <th>Tier</th>
                    <th>Seats</th>
                    <th>API Usage</th>
                    <th>Storage</th>
                    <th>Monthly Cost</th>
                </tr>
"""
        
        for tenant in sorted(orchestrator.tenants.values(), key=lambda t: t.monthly_cost, reverse=True):
            tier_class = f"tier-{tenant.tier.value}"
            usage_pct = (tenant.monthly_api_calls / tenant.api_call_limit * 100) if tenant.api_call_limit > 0 else 0
            storage_pct = (tenant.storage_gb / tenant.storage_limit_gb * 100) if tenant.storage_limit_gb > 0 else 0
            
            usage_status = "status-critical" if usage_pct > 90 else "status-warning" if usage_pct > 70 else "status-active"
            storage_status = "status-critical" if storage_pct > 90 else "status-warning" if storage_pct > 70 else "status-active"
            
            html += f"""
                <tr>
                    <td><strong>{tenant.company_name}</strong></td>
                    <td><span class="{tier_class}"><strong>{tenant.tier.value.upper()}</strong></span></td>
                    <td>{tenant.seats}</td>
                    <td>
                        <div class="{usage_status}">{usage_pct:.1f}%</div>
                        <div class="usage-bar"><div class="usage-fill" style="width: {min(usage_pct, 100)}%"></div></div>
                        {tenant.monthly_api_calls:,} / {tenant.api_call_limit:,}
                    </td>
                    <td>
                        <div class="{storage_status}">{storage_pct:.1f}%</div>
                        <div class="usage-bar"><div class="usage-fill" style="width: {min(storage_pct, 100)}%"></div></div>
                        {tenant.storage_gb:.1f} / {tenant.storage_limit_gb} GB
                    </td>
                    <td><strong>${tenant.monthly_cost:,.2f}</strong></td>
                </tr>
"""
        
        html += """
            </table>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>Isolation Levels</h3>
"""
        
        isolation_levels = {
            'CRYPTOGRAPHIC': len([t for t in orchestrator.tenants.values() if t.isolation_level.value == 'cryptographic']),
            'SCHEMA': len([t for t in orchestrator.tenants.values() if t.isolation_level.value == 'schema_isolation']),
            'DATABASE': len([t for t in orchestrator.tenants.values() if t.isolation_level.value == 'database_isolation']),
            'ROW-LEVEL': len([t for t in orchestrator.tenants.values() if t.isolation_level.value == 'database_row']),
        }
        
        for level, count in isolation_levels.items():
            if count > 0:
                html += f"<div style='padding: 8px; background: #f8f9fa; margin: 5px 0; border-left: 3px solid #667eea;'><strong>{level}</strong>: {count} tenants</div>"
        
        html += """
            </div>
            
            <div class="card">
                <h3>Billing Models</h3>
"""
        
        billing_models = {}
        for tenant in orchestrator.tenants.values():
            model = tenant.billing_model.value
            billing_models[model] = billing_models.get(model, 0) + 1
        
        for model, count in billing_models.items():
            if count > 0:
                html += f"<div style='padding: 8px; background: #f8f9fa; margin: 5px 0; border-left: 3px solid #764ba2;'><strong>{model.upper()}</strong>: {count} tenants</div>"
        
        html += f"""
            </div>
        </div>
        
        <div class="card">
            <h3>Audit Summary</h3>
            <table class="table">
                <tr>
                    <th>Event</th>
                    <th>Count</th>
                    <th>Severity</th>
                </tr>
"""
        
        # Count audit events
        audit_events = {}
        for log in orchestrator.context_manager.audit_logs:
            event = log.get('event', 'UNKNOWN')
            audit_events[event] = audit_events.get(event, 0) + 1
        
        for event, count in sorted(audit_events.items(), key=lambda x: x[1], reverse=True)[:10]:
            severity = "CRITICAL" if "VIOLATION" in event else "HIGH" if "INVALID" in event else "INFO"
            severity_class = "status-critical" if severity == "CRITICAL" else "status-warning" if severity == "HIGH" else "status-active"
            html += f'<tr><td>{event}</td><td>{count}</td><td class="{severity_class}">{severity}</td></tr>'
        
        html += f"""
            </table>
        </div>
        
        <div class="footer">
            Generated {self.generated_at} UTC<br>
            Multi-Tenant Isolation Engine v1.0 | Phase 12
        </div>
    </div>
</body>
</html>
"""
        return html
