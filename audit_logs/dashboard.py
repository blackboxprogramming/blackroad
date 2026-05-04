"""HTML dashboard for audit logging monitoring."""


def generate_dashboard(
    stats: dict,
    recent_entries: list,
    failed_actions: list,
    action_breakdown: dict,
    resource_breakdown: dict
) -> str:
    """Generate HTML dashboard for audit logging."""

    recent_html = ""
    for entry in recent_entries[:20]:
        timestamp = entry.get('timestamp', 'N/A')
        user = entry.get('user_id', 'N/A')
        action = entry.get('action', 'N/A')
        resource = entry.get('resource_id', 'N/A')
        status = entry.get('status', 'N/A')
        status_color = '#10b981' if status == 'success' else '#ef4444'
        
        recent_html += f"""
        <tr>
            <td>{timestamp}</td>
            <td>{user}</td>
            <td>{action}</td>
            <td>{resource}</td>
            <td><span style="color: {status_color}">{status.upper()}</span></td>
        </tr>
        """

    failed_html = ""
    for entry in failed_actions[:10]:
        user = entry.get('user_id', 'N/A')
        action = entry.get('action', 'N/A')
        resource = entry.get('resource_id', 'N/A')
        details = entry.get('details', {})
        
        failed_html += f"""
        <tr>
            <td>{user}</td>
            <td>{action}</td>
            <td>{resource}</td>
            <td>{str(details)[:50]}</td>
        </tr>
        """

    action_breakdown_html = ""
    for action, count in sorted(action_breakdown.items(), key=lambda x: x[1], reverse=True)[:10]:
        action_breakdown_html += f"<tr><td>{action}</td><td>{count:,}</td></tr>"

    resource_breakdown_html = ""
    for resource, count in sorted(resource_breakdown.items(), key=lambda x: x[1], reverse=True)[:10]:
        resource_breakdown_html += f"<tr><td>{resource}</td><td>{count:,}</td></tr>"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Audit Logging Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #06b6d4, #0891b2); padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .header h1 {{ margin: 0; color: white; }}
            .metrics {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 15px; margin-bottom: 20px; }}
            .metric {{ background: linear-gradient(135deg, #1e3a8a, #1e40af); padding: 15px; border-radius: 8px; border-left: 4px solid #06b6d4; }}
            .metric .label {{ font-size: 12px; color: #94a3b8; margin-bottom: 5px; }}
            .metric .value {{ font-size: 24px; font-weight: bold; color: #06b6d4; }}
            .section {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
            .section h2 {{ margin: 0 0 15px 0; color: #06b6d4; border-bottom: 2px solid #334155; padding-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th {{ background: #0f172a; padding: 10px; text-align: left; font-size: 12px; color: #94a3b8; border-bottom: 2px solid #334155; }}
            td {{ padding: 10px; border-bottom: 1px solid #334155; font-size: 12px; }}
            tr:hover {{ background: #0f172a; }}
            .success {{ color: #10b981; }}
            .failure {{ color: #ef4444; }}
            .footer {{ text-align: center; color: #64748b; font-size: 12px; margin-top: 40px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔐 Audit Logging Dashboard</h1>
        </div>

        <div class="metrics">
            <div class="metric">
                <div class="label">Total Entries</div>
                <div class="value">{stats.get('total_entries', 0):,}</div>
            </div>
            <div class="metric">
                <div class="label">Successful Actions</div>
                <div class="value">{stats.get('successful_actions', 0):,}</div>
            </div>
            <div class="metric">
                <div class="label">Failed Actions</div>
                <div class="value">{stats.get('failed_actions', 0)}</div>
            </div>
            <div class="metric">
                <div class="label">Success Rate</div>
                <div class="value">{stats.get('success_rate', 0):.1f}%</div>
            </div>
            <div class="metric">
                <div class="label">Unique Users</div>
                <div class="value">{stats.get('unique_users', 0)}</div>
            </div>
        </div>

        <div class="section">
            <h2>Compliance Summary</h2>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Total Entries</td>
                    <td>{stats.get('total_entries', 0):,}</td>
                </tr>
                <tr>
                    <td>Successful Actions</td>
                    <td class="success">{stats.get('successful_actions', 0):,}</td>
                </tr>
                <tr>
                    <td>Failed Actions</td>
                    <td class="failure">{stats.get('failed_actions', 0):,}</td>
                </tr>
                <tr>
                    <td>Success Rate</td>
                    <td>{stats.get('success_rate', 0):.1f}%</td>
                </tr>
                <tr>
                    <td>Unique Users</td>
                    <td>{stats.get('unique_users', 0)}</td>
                </tr>
                <tr>
                    <td>Unique Resources</td>
                    <td>{stats.get('unique_resources', 0)}</td>
                </tr>
                <tr>
                    <td>Capacity Used</td>
                    <td>{stats.get('capacity_percent', 0):.1f}%</td>
                </tr>
            </table>
        </div>

        <div class="section">
            <h2>Recent Entries</h2>
            <table>
                <tr>
                    <th>Timestamp</th>
                    <th>User</th>
                    <th>Action</th>
                    <th>Resource</th>
                    <th>Status</th>
                </tr>
                {recent_html}
            </table>
        </div>

        <div class="section">
            <h2>Failed Actions</h2>
            <table>
                <tr>
                    <th>User</th>
                    <th>Action</th>
                    <th>Resource</th>
                    <th>Details</th>
                </tr>
                {failed_html}
            </table>
        </div>

        <div class="section">
            <h2>Action Breakdown</h2>
            <table>
                <tr>
                    <th>Action Type</th>
                    <th>Count</th>
                </tr>
                {action_breakdown_html}
            </table>
        </div>

        <div class="section">
            <h2>Resource Breakdown</h2>
            <table>
                <tr>
                    <th>Resource Type</th>
                    <th>Count</th>
                </tr>
                {resource_breakdown_html}
            </table>
        </div>

        <div class="footer">
            <p>Audit Logging Dashboard | Real-Time Monitoring</p>
        </div>

    </body>
    </html>
    """

    return html
