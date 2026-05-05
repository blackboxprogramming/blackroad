"""Agent memory dashboard."""


def generate_dashboard(agent_id: str, metrics: dict = None, timeline: list = None, 
                      distribution: dict = None, top_tags: list = None) -> str:
    """Generate agent memory dashboard HTML."""
    metrics = metrics or {}
    timeline = timeline or []
    distribution = distribution or {}
    top_tags = top_tags or []
    
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Agent Memory Dashboard</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1400px;
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
        .agent-id {
            background: rgba(255,255,255,0.2);
            padding: 8px 16px;
            border-radius: 4px;
            display: inline-block;
            margin-top: 10px;
            font-family: monospace;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }
        .card {
            background: white;
            border-radius: 8px;
            padding: 18px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .card h3 {
            margin: 0 0 10px 0;
            color: #667eea;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .card .value {
            font-size: 28px;
            font-weight: bold;
            color: #1a1a2e;
        }
        .card .subtext {
            color: #666;
            font-size: 12px;
            margin-top: 5px;
        }
        .section {
            margin-bottom: 30px;
        }
        .section h2 {
            color: white;
            margin: 0 0 15px 0;
            font-size: 18px;
        }
        .two-column {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .chart-container {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .table {
            width: 100%;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .table thead {
            background: #f5f5f5;
            border-bottom: 2px solid #e0e0e0;
        }
        .table th {
            padding: 12px 15px;
            text-align: left;
            font-weight: 600;
            color: #333;
            font-size: 12px;
            text-transform: uppercase;
        }
        .table td {
            padding: 12px 15px;
            border-bottom: 1px solid #e0e0e0;
            color: #1a1a2e;
        }
        .table tr:hover {
            background: #f9f9f9;
        }
        .memory-type {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }
        .type-fact {
            background: #e3f2fd;
            color: #1976d2;
        }
        .type-decision {
            background: #f3e5f5;
            color: #7b1fa2;
        }
        .type-learning {
            background: #e8f5e9;
            color: #388e3c;
        }
        .type-reasoning {
            background: #fff3e0;
            color: #f57c00;
        }
        .bar {
            height: 6px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 3px;
            margin: 5px 0;
        }
        .tag {
            display: inline-block;
            background: #e0e0e0;
            padding: 4px 8px;
            margin: 2px;
            border-radius: 12px;
            font-size: 12px;
        }
        .metric-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #f0f0f0;
        }
        .metric-row:last-child {
            border-bottom: none;
        }
        .metric-label {
            color: #666;
            font-size: 14px;
        }
        .metric-value {
            color: #667eea;
            font-weight: 600;
            font-size: 16px;
        }
        @media (max-width: 900px) {
            .two-column {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 Agent Memory Dashboard</h1>
            <p>Real-time memory, context, and learning analytics</p>
            <div class="agent-id">Agent ID: """ + agent_id + """</div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>Total Memories</h3>
                <div class="value">""" + str(metrics.get('total_memories', 0)) + """</div>
                <div class="subtext">All stored memories</div>
            </div>
            
            <div class="card">
                <h3>Sessions</h3>
                <div class="value">""" + str(metrics.get('total_sessions', 0)) + """</div>
                <div class="subtext">Conversation sessions</div>
            </div>
            
            <div class="card">
                <h3>Total Accesses</h3>
                <div class="value">""" + str(metrics.get('total_accesses', 0)) + """</div>
                <div class="subtext">Memory retrievals</div>
            </div>
            
            <div class="card">
                <h3>Avg Relevance</h3>
                <div class="value">""" + f"{metrics.get('avg_relevance', 0):.2f}" + """</div>
                <div class="subtext">Out of 1.0</div>
            </div>
            
            <div class="card">
                <h3>Dominant Type</h3>
                <div class="value">""" + metrics.get('most_common_type', 'N/A').replace('_', ' ').title() + """</div>
                <div class="subtext">Most stored type</div>
            </div>
            
            <div class="card">
                <h3>Avg Session</h3>
                <div class="value">""" + f"{metrics.get('avg_session_duration', 0):.0f}s" + """</div>
                <div class="subtext">Duration</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 Memory Composition</h2>
            <div class="two-column">
                <div class="chart-container">
                    <h3 style="margin-top: 0; color: #667eea;">Memory Types Distribution</h3>
"""
    
    # Add memory type distribution
    if distribution:
        total = sum(distribution.values())
        for mtype, count in sorted(distribution.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total * 100) if total > 0 else 0
            html += f"""                    <div class="metric-row">
                        <div class="metric-label"><span class="memory-type type-{mtype}">{mtype.replace('_', ' ').title()}</span></div>
                        <div class="metric-value">{count}</div>
                    </div>
                    <div class="bar" style="width: {percentage}%"></div>
"""
    
    html += """                </div>
                <div class="chart-container">
                    <h3 style="margin-top: 0; color: #667eea;">Top Tags</h3>
"""
    
    # Add top tags
    if top_tags:
        for tag, count in top_tags[:10]:
            html += f"""                    <div class="tag" title="{count} uses">{tag} ({count})</div>
"""
    else:
        html += "                    <p style='color: #999; font-style: italic;'>No tags recorded</p>"
    
    html += """                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>📈 Memory Timeline (Last 7 Days)</h2>
            <div class="chart-container">
                <table class="table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Memories Created</th>
                            <th>Activity</th>
                        </tr>
                    </thead>
                    <tbody>
"""
    
    # Add timeline
    if timeline:
        for entry in timeline[-7:]:
            date = entry.get('date', 'Unknown')
            count = entry.get('memories_created', 0)
            activity_bar = "█" * min(count, 20) if count > 0 else "—"
            html += f"""                        <tr>
                            <td>{date}</td>
                            <td><strong>{count}</strong></td>
                            <td>{activity_bar}</td>
                        </tr>
"""
    else:
        html += """                        <tr>
                            <td colspan="3" style="text-align: center; color: #999;">No data available</td>
                        </tr>
"""
    
    html += """                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="section">
            <div class="chart-container">
                <h3 style="margin-top: 0; color: #667eea;">💡 Key Insights</h3>
                <div class="metric-row">
                    <div class="metric-label">Primary Learning Mode</div>
                    <div class="metric-value">""" + metrics.get('most_common_type', 'Unknown').replace('_', ' ').title() + """</div>
                </div>
                <div class="metric-row">
                    <div class="metric-label">Memory Retention</div>
                    <div class="metric-value">""" + f"{metrics.get('avg_relevance', 0) * 100:.0f}%" + """</div>
                </div>
                <div class="metric-row">
                    <div class="metric-label">24h Growth</div>
                    <div class="metric-value">""" + str(metrics.get('memory_growth_24h', 0)) + """ memories</div>
                </div>
                <div class="metric-row">
                    <div class="metric-label">Last Activity</div>
                    <div class="metric-value">""" + metrics.get('last_activity', 'Never').split('T')[0] if metrics.get('last_activity') != 'Never' else "Never" + """</div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""
    
    return html
