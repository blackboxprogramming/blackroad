"""Rate limiting dashboard."""


def generate_dashboard(stats: dict, metrics: dict = None, top_rejected: list = None, hourly_stats: list = None) -> str:
    """Generate rate limiting dashboard HTML."""
    metrics = metrics or {}
    top_rejected = top_rejected or []
    hourly_stats = hourly_stats or []
    
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Rate Limiting Dashboard</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            color: white;
            margin-bottom: 30px;
        }
        .header h1 {
            margin: 0;
            font-size: 32px;
        }
        .header p {
            margin: 5px 0 0 0;
            opacity: 0.9;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .card h3 {
            margin: 0 0 10px 0;
            color: #0891b2;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .card .value {
            font-size: 32px;
            font-weight: bold;
            color: #1e293b;
        }
        .card .subtext {
            color: #64748b;
            font-size: 12px;
            margin-top: 5px;
        }
        .metric-card {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            background: #f8fafc;
            border-radius: 6px;
            margin-bottom: 10px;
        }
        .metric-card .label {
            color: #475569;
            font-size: 14px;
        }
        .metric-card .value {
            color: #0891b2;
            font-weight: bold;
            font-size: 16px;
        }
        .section {
            margin-bottom: 30px;
        }
        .section h2 {
            color: white;
            margin: 0 0 15px 0;
            font-size: 20px;
        }
        .table {
            width: 100%;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .table thead {
            background: #f1f5f9;
            border-bottom: 2px solid #e2e8f0;
        }
        .table th {
            padding: 12px 15px;
            text-align: left;
            font-weight: 600;
            color: #475569;
            font-size: 12px;
            text-transform: uppercase;
        }
        .table td {
            padding: 12px 15px;
            border-bottom: 1px solid #e2e8f0;
            color: #1e293b;
        }
        .table tr:hover {
            background: #f8fafc;
        }
        .status-allowed {
            color: #16a34a;
            font-weight: 600;
        }
        .status-rejected {
            color: #dc2626;
            font-weight: 600;
        }
        .progress-bar {
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
            margin: 5px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #06b6d4 0%, #0891b2 100%);
        }
        .timestamp {
            color: #94a3b8;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⏱️ Rate Limiting Dashboard</h1>
            <p>Real-time rate limit monitoring and analytics</p>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>Total Checks</h3>
                <div class="value">""" + str(stats.get('total_checks', 0)) + """</div>
                <div class="subtext">All rate limit evaluations</div>
            </div>
            
            <div class="card">
                <h3>Allowed Requests</h3>
                <div class="value">""" + str(stats.get('allowed', 0)) + """</div>
                <div class="subtext">Passed rate limit</div>
            </div>
            
            <div class="card">
                <h3>Rejected Requests</h3>
                <div class="value">""" + str(stats.get('rejected', 0)) + """</div>
                <div class="subtext">Exceeded rate limit</div>
            </div>
            
            <div class="card">
                <h3>Active Limiters</h3>
                <div class="value">""" + str(stats.get('active_limiters', 0)) + """</div>
                <div class="subtext">Currently tracked identifiers</div>
            </div>
            
            <div class="card">
                <h3>Active Penalties</h3>
                <div class="value">""" + str(stats.get('active_penalties', 0)) + """</div>
                <div class="subtext">Clients in penalty cooldown</div>
            </div>
            
            <div class="card">
                <h3>Rejection Rate</h3>
                <div class="value">"""
    
    total_checks = stats.get('total_checks', 0)
    if total_checks > 0:
        rejection_rate = (stats.get('rejected', 0) / total_checks) * 100
        html += f"{rejection_rate:.1f}%"
    else:
        html += "0%"
    
    html += """</div>
                <div class="subtext">Of all requests</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 Metrics Summary</h2>
            <div class="card">
"""
    
    for key, value in metrics.items():
        if isinstance(value, float):
            html += f'<div class="metric-card"><div class="label">{key.replace("_", " ").title()}</div><div class="value">{value:.2f}</div></div>'
        elif isinstance(value, int):
            html += f'<div class="metric-card"><div class="label">{key.replace("_", " ").title()}</div><div class="value">{value}</div></div>'
    
    html += """            </div>
        </div>
        
        <div class="section">
            <h2>🚫 Top Rejected Clients</h2>
            <table class="table">
                <thead>
                    <tr>
                        <th>Identifier</th>
                        <th>Total Requests</th>
                        <th>Rejected</th>
                        <th>Rejection Rate</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    if top_rejected:
        for item in top_rejected[:10]:
            identifier = item.get('identifier', 'Unknown')
            total = item.get('total_requests', 0)
            rejected = item.get('rejected_requests', 0)
            rate = item.get('rejection_rate', 0)
            html += f"""                    <tr>
                        <td>{identifier}</td>
                        <td>{total}</td>
                        <td><span class="status-rejected">{rejected}</span></td>
                        <td>
                            <div>{rate:.1%}</div>
                            <div class="progress-bar"><div class="progress-fill" style="width: {rate*100}%"></div></div>
                        </td>
                    </tr>
"""
    else:
        html += """                    <tr>
                        <td colspan="4" style="text-align: center; color: #94a3b8;">No data available</td>
                    </tr>
"""
    
    html += """                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>📈 Hourly Statistics (Last 24 Hours)</h2>
            <table class="table">
                <thead>
                    <tr>
                        <th>Hour</th>
                        <th>Total Requests</th>
                        <th>Rejections</th>
                        <th>Rejection Rate</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    if hourly_stats:
        for stat in hourly_stats[-24:]:
            hour = stat.get('hour', 'Unknown')
            requests = stat.get('requests', 0)
            rejections = stat.get('rejections', 0)
            rate = stat.get('rejection_rate', 0)
            html += f"""                    <tr>
                        <td><span class="timestamp">{hour}</span></td>
                        <td>{requests}</td>
                        <td><span class="status-rejected">{rejections}</span></td>
                        <td>
                            <div>{rate:.1%}</div>
                            <div class="progress-bar"><div class="progress-fill" style="width: {rate*100}%"></div></div>
                        </td>
                    </tr>
"""
    else:
        html += """                    <tr>
                        <td colspan="4" style="text-align: center; color: #94a3b8;">No data available</td>
                    </tr>
"""
    
    html += """                </tbody>
            </table>
        </div>
    </div>
</body>
</html>"""
    
    return html
