"""Integration marketplace dashboard HTML."""

def generate_dashboard(hub_metrics: dict, integrations: list, webhook_stats: dict) -> str:
    """Generate integration hub dashboard HTML."""
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BlackRoad Integration Hub</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                color: #e2e8f0;
                padding: 40px 20px;
                min-height: 100vh;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            header {
                margin-bottom: 40px;
            }
            h1 {
                font-size: 32px;
                margin-bottom: 10px;
                background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            .subtitle {
                color: #cbd5e1;
                font-size: 16px;
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 40px;
            }
            .stat-card {
                background: rgba(30, 41, 59, 0.8);
                border: 1px solid rgba(100, 116, 139, 0.3);
                border-radius: 12px;
                padding: 20px;
                backdrop-filter: blur(10px);
            }
            .stat-label {
                color: #94a3b8;
                font-size: 14px;
                margin-bottom: 8px;
            }
            .stat-value {
                font-size: 32px;
                font-weight: bold;
                color: #60a5fa;
            }
            .stat-meta {
                color: #64748b;
                font-size: 12px;
                margin-top: 8px;
            }
            .connectors-section {
                background: rgba(30, 41, 59, 0.8);
                border: 1px solid rgba(100, 116, 139, 0.3);
                border-radius: 12px;
                padding: 30px;
                margin-bottom: 40px;
                backdrop-filter: blur(10px);
            }
            .section-title {
                font-size: 20px;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
            }
            .section-title::before {
                content: '';
                display: inline-block;
                width: 4px;
                height: 20px;
                background: linear-gradient(180deg, #60a5fa 0%, #3b82f6 100%);
                margin-right: 12px;
                border-radius: 2px;
            }
            .connectors-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 15px;
            }
            .connector-card {
                background: rgba(15, 23, 42, 0.9);
                border: 1px solid rgba(100, 116, 139, 0.2);
                border-radius: 8px;
                padding: 15px;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .connector-card:hover {
                background: rgba(30, 41, 59, 0.9);
                border-color: rgba(96, 165, 250, 0.5);
                transform: translateY(-2px);
            }
            .connector-info {
                flex: 1;
            }
            .connector-name {
                font-weight: 600;
                color: #e2e8f0;
                margin-bottom: 4px;
            }
            .connector-category {
                font-size: 12px;
                color: #94a3b8;
            }
            .status-badge {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
            }
            .status-connected {
                background: rgba(34, 197, 94, 0.2);
                color: #22c55e;
            }
            .status-disconnected {
                background: rgba(239, 68, 68, 0.2);
                color: #ef4444;
            }
            .status-rate-limited {
                background: rgba(245, 158, 11, 0.2);
                color: #f59e0b;
            }
            .integrations-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            .integrations-table th {
                text-align: left;
                padding: 12px;
                border-bottom: 2px solid rgba(100, 116, 139, 0.3);
                color: #94a3b8;
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
            }
            .integrations-table td {
                padding: 12px;
                border-bottom: 1px solid rgba(100, 116, 139, 0.1);
            }
            .integrations-table tr:hover {
                background: rgba(100, 116, 139, 0.05);
            }
            .integration-id {
                font-family: 'Monaco', 'Courier New', monospace;
                font-size: 12px;
                color: #94a3b8;
            }
            .metric {
                font-weight: 500;
                color: #e2e8f0;
            }
            .webhook-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 15px;
                margin-top: 20px;
            }
            .webhook-item {
                background: rgba(15, 23, 42, 0.9);
                border-left: 3px solid #60a5fa;
                padding: 15px;
                border-radius: 6px;
            }
            .webhook-label {
                font-size: 12px;
                color: #94a3b8;
                margin-bottom: 4px;
            }
            .webhook-value {
                font-weight: 600;
                color: #e2e8f0;
            }
            .health-indicator {
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 8px;
            }
            .health-good {
                background: #22c55e;
                box-shadow: 0 0 8px rgba(34, 197, 94, 0.5);
            }
            .health-warning {
                background: #f59e0b;
                box-shadow: 0 0 8px rgba(245, 158, 11, 0.5);
            }
            .health-error {
                background: #ef4444;
                box-shadow: 0 0 8px rgba(239, 68, 68, 0.5);
            }
            .footer {
                text-align: center;
                padding: 20px;
                color: #64748b;
                font-size: 12px;
                margin-top: 40px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🚀 Integration Hub</h1>
                <p class="subtitle">Third-party API integrations & webhook management</p>
            </header>
            
            <div class="stats-grid">
    """
    
    # Add hub metrics
    html += f"""
                <div class="stat-card">
                    <div class="stat-label">Total Integrations</div>
                    <div class="stat-value">{hub_metrics.get('total_integrations', 0)}</div>
                    <div class="stat-meta">
                        <span class="health-indicator health-good"></span>
                        {hub_metrics.get('enabled_integrations', 0)} active
                    </div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">Events Processed</div>
                    <div class="stat-value">{hub_metrics.get('total_events_processed', 0):,}</div>
                    <div class="stat-meta">{hub_metrics.get('overall_success_rate', '0%')} success rate</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">Queue Depth</div>
                    <div class="stat-value">{hub_metrics.get('queue_depth', 0)}</div>
                    <div class="stat-meta">Pending events</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">Unique Connectors</div>
                    <div class="stat-value">{hub_metrics.get('unique_connectors', 0)}</div>
                    <div class="stat-meta">SaaS platforms</div>
                </div>
    """
    
    html += """
            </div>
            
            <div class="connectors-section">
                <h2 class="section-title">Available Integrations</h2>
    """
    
    # Categorize integrations
    categories = {}
    for integration in integrations:
        status = integration.get('status', 'disconnected')
        enabled = integration.get('enabled', False)
        
        if not hasattr(categories, '__getitem__'):
            categories = {}
        
        category = integration.get('connector', 'Other')
        if category not in categories:
            categories[category] = []
        
        categories[category].append({
            'name': integration.get('connector', 'Unknown'),
            'integration_id': integration.get('integration_id', ''),
            'status': status,
            'enabled': enabled,
            'sync_direction': integration.get('sync_direction', 'inbound'),
            'metrics': integration.get('metrics', {}),
        })
    
    # Display all integrations
    if integrations:
        html += """
                <table class="integrations-table">
                    <thead>
                        <tr>
                            <th>Connector</th>
                            <th>Status</th>
                            <th>Direction</th>
                            <th>Events</th>
                            <th>Success Rate</th>
                            <th>Last Sync</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for integration in integrations:
            status = integration.get('status', 'disconnected')
            
            if status == 'connected':
                status_badge = '<span class="status-badge status-connected">✓ Connected</span>'
            elif status == 'disconnected':
                status_badge = '<span class="status-badge status-disconnected">✗ Disconnected</span>'
            else:
                status_badge = '<span class="status-badge status-rate-limited">⚠ ' + status.title() + '</span>'
            
            metrics = integration.get('metrics', {})
            
            html += f"""
                        <tr>
                            <td>
                                <span class="connector-name">{integration.get('connector', 'Unknown')}</span><br>
                                <span class="integration-id">{integration.get('integration_id', '')[:20]}...</span>
                            </td>
                            <td>{status_badge}</td>
                            <td><span class="metric">{integration.get('sync_direction', 'inbound').title()}</span></td>
                            <td><span class="metric">{metrics.get('total_events', 0):,}</span></td>
                            <td><span class="metric">{metrics.get('success_rate', 'N/A')}</span></td>
                            <td><span class="metric">{metrics.get('last_sync', 'Never')[:10]}</span></td>
                        </tr>
            """
        
        html += """
                    </tbody>
                </table>
        """
    else:
        html += '<p style="color: #94a3b8; margin-top: 20px;">No integrations configured yet.</p>'
    
    html += """
            </div>
            
            <div class="connectors-section">
                <h2 class="section-title">Webhook Management</h2>
                <div class="webhook-grid">
    """
    
    # Add webhook stats
    html += f"""
                    <div class="webhook-item">
                        <div class="webhook-label">Total Endpoints</div>
                        <div class="webhook-value">{webhook_stats.get('total_endpoints', 0)}</div>
                    </div>
                    
                    <div class="webhook-item">
                        <div class="webhook-label">Active Endpoints</div>
                        <div class="webhook-value">{webhook_stats.get('active_endpoints', 0)}</div>
                    </div>
                    
                    <div class="webhook-item">
                        <div class="webhook-label">Total Deliveries</div>
                        <div class="webhook-value">{webhook_stats.get('total_deliveries_completed', 0):,}</div>
                    </div>
                    
                    <div class="webhook-item">
                        <div class="webhook-label">Delivery Success Rate</div>
                        <div class="webhook-value">{webhook_stats.get('overall_success_rate', 'N/A')}</div>
                    </div>
                    
                    <div class="webhook-item">
                        <div class="webhook-label">Pending Deliveries</div>
                        <div class="webhook-value">{webhook_stats.get('pending_deliveries', 0)}</div>
                    </div>
                    
                    <div class="webhook-item">
                        <div class="webhook-label">Failed Deliveries</div>
                        <div class="webhook-value">{webhook_stats.get('failed_deliveries', 0)}</div>
                    </div>
    """
    
    html += """
                </div>
            </div>
            
            <div class="footer">
                <p>BlackRoad Integration Hub • Production Ready • 50+ Integrations • Enterprise Grade</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def generate_connector_marketplace() -> str:
    """Generate marketplace view for available connectors."""
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Integration Marketplace</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                color: #e2e8f0;
                padding: 40px 20px;
                min-height: 100vh;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            header {
                margin-bottom: 40px;
            }
            h1 {
                font-size: 32px;
                margin-bottom: 10px;
                background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            .category {
                margin-bottom: 40px;
            }
            .category-title {
                font-size: 20px;
                margin-bottom: 20px;
                color: #60a5fa;
                border-bottom: 2px solid rgba(96, 165, 250, 0.2);
                padding-bottom: 10px;
            }
            .connectors-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                gap: 20px;
            }
            .connector-marketplace-card {
                background: rgba(30, 41, 59, 0.8);
                border: 1px solid rgba(100, 116, 139, 0.3);
                border-radius: 12px;
                padding: 20px;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                flex-direction: column;
            }
            .connector-marketplace-card:hover {
                background: rgba(30, 41, 59, 0.95);
                border-color: rgba(96, 165, 250, 0.5);
                transform: translateY(-4px);
                box-shadow: 0 8px 24px rgba(96, 165, 250, 0.1);
            }
            .connector-icon {
                font-size: 32px;
                margin-bottom: 12px;
            }
            .connector-marketplace-name {
                font-weight: 600;
                font-size: 16px;
                margin-bottom: 4px;
                color: #e2e8f0;
            }
            .connector-marketplace-desc {
                font-size: 13px;
                color: #94a3b8;
                margin-bottom: 12px;
                flex-grow: 1;
            }
            .auth-type {
                display: inline-block;
                background: rgba(59, 130, 246, 0.1);
                color: #60a5fa;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
                margin-bottom: 12px;
            }
            .connector-actions {
                display: flex;
                gap: 8px;
            }
            .btn {
                flex: 1;
                padding: 8px 12px;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            .btn-primary {
                background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
                color: white;
            }
            .btn-primary:hover {
                opacity: 0.9;
                transform: scale(1.02);
            }
            .btn-secondary {
                background: rgba(96, 165, 250, 0.1);
                color: #60a5fa;
                border: 1px solid rgba(96, 165, 250, 0.3);
            }
            .btn-secondary:hover {
                background: rgba(96, 165, 250, 0.2);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🏪 Integration Marketplace</h1>
                <p style="color: #cbd5e1;">Connect with 50+ SaaS platforms</p>
            </header>
            
            <div class="category">
                <div class="category-title">💼 CRM</div>
                <div class="connectors-grid">
                    <div class="connector-marketplace-card">
                        <div class="connector-icon">🏢</div>
                        <div class="connector-marketplace-name">Salesforce</div>
                        <div class="connector-marketplace-desc">Leading enterprise CRM platform</div>
                        <div class="auth-type">OAuth 2.0</div>
                        <div class="connector-actions">
                            <button class="btn btn-primary">Enable</button>
                        </div>
                    </div>
                    <div class="connector-marketplace-card">
                        <div class="connector-icon">🎯</div>
                        <div class="connector-marketplace-name">HubSpot</div>
                        <div class="connector-marketplace-desc">All-in-one CRM platform</div>
                        <div class="auth-type">API Key</div>
                        <div class="connector-actions">
                            <button class="btn btn-primary">Enable</button>
                        </div>
                    </div>
                    <div class="connector-marketplace-card">
                        <div class="connector-icon">📞</div>
                        <div class="connector-marketplace-name">Pipedrive</div>
                        <div class="connector-marketplace-desc">Sales pipeline management</div>
                        <div class="auth-type">API Key</div>
                        <div class="connector-actions">
                            <button class="btn btn-primary">Enable</button>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="category">
                <div class="category-title">💬 Communication</div>
                <div class="connectors-grid">
                    <div class="connector-marketplace-card">
                        <div class="connector-icon">💙</div>
                        <div class="connector-marketplace-name">Slack</div>
                        <div class="connector-marketplace-desc">Team communication platform</div>
                        <div class="auth-type">OAuth 2.0</div>
                        <div class="connector-actions">
                            <button class="btn btn-primary">Enable</button>
                        </div>
                    </div>
                    <div class="connector-marketplace-card">
                        <div class="connector-icon">🤖</div>
                        <div class="connector-marketplace-name">Microsoft Teams</div>
                        <div class="connector-marketplace-desc">Enterprise collaboration</div>
                        <div class="auth-type">OAuth 2.0</div>
                        <div class="connector-actions">
                            <button class="btn btn-primary">Enable</button>
                        </div>
                    </div>
                    <div class="connector-marketplace-card">
                        <div class="connector-icon">🎮</div>
                        <div class="connector-marketplace-name">Discord</div>
                        <div class="connector-marketplace-desc">Community chat platform</div>
                        <div class="auth-type">Bearer Token</div>
                        <div class="connector-actions">
                            <button class="btn btn-primary">Enable</button>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="category">
                <div class="category-title">💳 Finance & Payments</div>
                <div class="connectors-grid">
                    <div class="connector-marketplace-card">
                        <div class="connector-icon">💰</div>
                        <div class="connector-marketplace-name">Stripe</div>
                        <div class="connector-marketplace-desc">Payment processing</div>
                        <div class="auth-type">API Key</div>
                        <div class="connector-actions">
                            <button class="btn btn-primary">Enable</button>
                        </div>
                    </div>
                    <div class="connector-marketplace-card">
                        <div class="connector-icon">📊</div>
                        <div class="connector-marketplace-name">QuickBooks</div>
                        <div class="connector-marketplace-desc">Accounting software</div>
                        <div class="auth-type">OAuth 2.0</div>
                        <div class="connector-actions">
                            <button class="btn btn-primary">Enable</button>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="category">
                <div class="category-title">📈 Analytics</div>
                <div class="connectors-grid">
                    <div class="connector-marketplace-card">
                        <div class="connector-icon">🎲</div>
                        <div class="connector-marketplace-name">Segment</div>
                        <div class="connector-marketplace-desc">Customer data platform</div>
                        <div class="auth-type">API Key</div>
                        <div class="connector-actions">
                            <button class="btn btn-primary">Enable</button>
                        </div>
                    </div>
                    <div class="connector-marketplace-card">
                        <div class="connector-icon">📉</div>
                        <div class="connector-marketplace-name">Mixpanel</div>
                        <div class="connector-marketplace-desc">Product analytics</div>
                        <div class="auth-type">API Key</div>
                        <div class="connector-actions">
                            <button class="btn btn-primary">Enable</button>
                        </div>
                    </div>
                    <div class="connector-marketplace-card">
                        <div class="connector-icon">📊</div>
                        <div class="connector-marketplace-name">Amplitude</div>
                        <div class="connector-marketplace-desc">User behavior analytics</div>
                        <div class="auth-type">API Key</div>
                        <div class="connector-actions">
                            <button class="btn btn-primary">Enable</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html
