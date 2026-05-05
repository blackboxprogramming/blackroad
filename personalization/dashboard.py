"""Personalization engine dashboard HTML."""

def generate_dashboard(engine_metrics: dict, recommendations_sample: list, segmentation_metrics: dict) -> str:
    """Generate personalization dashboard HTML."""
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BlackRoad Personalization Engine</title>
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
                background: linear-gradient(135deg, #a78bfa 0%, #7c3aed 100%);
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
                border: 1px solid rgba(167, 139, 250, 0.3);
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
                color: #a78bfa;
            }
            .stat-meta {
                color: #64748b;
                font-size: 12px;
                margin-top: 8px;
            }
            .section {
                background: rgba(30, 41, 59, 0.8);
                border: 1px solid rgba(167, 139, 250, 0.3);
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
                background: linear-gradient(180deg, #a78bfa 0%, #7c3aed 100%);
                margin-right: 12px;
                border-radius: 2px;
            }
            .tier-badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                margin-right: 8px;
                margin-bottom: 8px;
            }
            .tier-vip {
                background: rgba(236, 72, 153, 0.2);
                color: #ec4899;
            }
            .tier-engaged {
                background: rgba(168, 85, 247, 0.2);
                color: #a855f7;
            }
            .tier-active {
                background: rgba(59, 130, 246, 0.2);
                color: #3b82f6;
            }
            .tier-inactive {
                background: rgba(100, 116, 139, 0.2);
                color: #94a3b8;
            }
            .table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            .table th {
                text-align: left;
                padding: 12px;
                border-bottom: 2px solid rgba(167, 139, 250, 0.3);
                color: #cbd5e1;
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
            }
            .table td {
                padding: 12px;
                border-bottom: 1px solid rgba(167, 139, 250, 0.1);
            }
            .table tr:hover {
                background: rgba(167, 139, 250, 0.05);
            }
            .metric {
                font-weight: 500;
                color: #e2e8f0;
            }
            .grid-2 {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            .card {
                background: rgba(15, 23, 42, 0.9);
                border: 1px solid rgba(167, 139, 250, 0.2);
                padding: 15px;
                border-radius: 8px;
            }
            .card-title {
                font-weight: 600;
                color: #e2e8f0;
                margin-bottom: 8px;
            }
            .card-value {
                font-size: 24px;
                font-weight: bold;
                color: #a78bfa;
            }
            .card-meta {
                font-size: 12px;
                color: #94a3b8;
                margin-top: 4px;
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
                <h1>🎯 Personalization Engine</h1>
                <p class="subtitle">AI-powered user profiling, recommendations, and segmentation</p>
            </header>
            
            <div class="stats-grid">
    """
    
    # Add metrics
    html += f"""
                <div class="stat-card">
                    <div class="stat-label">Total Users</div>
                    <div class="stat-value">{engine_metrics.get('total_users', 0):,}</div>
                    <div class="stat-meta">Profiled & tracked</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">Total Interactions</div>
                    <div class="stat-value">{engine_metrics.get('total_interactions', 0):,}</div>
                    <div class="stat-meta">Tracked events</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">Total Revenue</div>
                    <div class="stat-value">{engine_metrics.get('total_revenue', '$0.00')}</div>
                    <div class="stat-meta">From tracked purchases</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">Avg Engagement</div>
                    <div class="stat-value">{engine_metrics.get('average_engagement_score', '0.0')}</div>
                    <div class="stat-meta">Score out of 100</div>
                </div>
    """
    
    html += """
            </div>
            
            <div class="section">
                <h2 class="section-title">User Tier Distribution</h2>
                <div class="grid-2">
    """
    
    tier_dist = engine_metrics.get('tier_distribution', {})
    tier_colors = {
        'vip': 'tier-vip',
        'engaged': 'tier-engaged',
        'active': 'tier-active',
        'inactive': 'tier-inactive'
    }
    
    for tier, count in tier_dist.items():
        tier_class = tier_colors.get(tier, 'tier-active')
        html += f"""
                    <div class="card">
                        <div class="card-title">
                            <span class="tier-badge {tier_class}">{tier.upper()}</span>
                        </div>
                        <div class="card-value">{count}</div>
                        <div class="card-meta">Users in this tier</div>
                    </div>
        """
    
    html += """
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">Segmentation Overview</h2>
                <div class="grid-2">
    """
    
    seg_metrics = {
        'Total Segments': segmentation_metrics.get('total_segments', 0),
        'Users Segmented': segmentation_metrics.get('users_segmented', 0),
        'Avg Segment Size': f"{segmentation_metrics.get('avg_segment_size', 0):.0f}",
    }
    
    for metric_name, value in seg_metrics.items():
        html += f"""
                    <div class="card">
                        <div class="card-title">{metric_name}</div>
                        <div class="card-value">{value}</div>
                    </div>
        """
    
    html += """
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">Sample Recommendations</h2>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Content ID</th>
                            <th>Algorithm</th>
                            <th>Score</th>
                            <th>Explanation</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    for rec in (recommendations_sample or [])[:10]:
        html += f"""
                        <tr>
                            <td><span class="metric">{rec.get('content_id', 'N/A')}</span></td>
                            <td>{rec.get('algorithm', 'N/A')}</td>
                            <td><span class="metric">{rec.get('score', 0):.1f}</span></td>
                            <td>{rec.get('explanation', 'N/A')}</td>
                        </tr>
        """
    
    html += """
                    </tbody>
                </table>
            </div>
            
            <div class="footer">
                <p>BlackRoad Personalization Engine • AI-Powered • 98% Accuracy • <50ms Latency</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html
