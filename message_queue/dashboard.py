"""HTML dashboard for message queue monitoring."""


def generate_dashboard(
    queue_stats: dict,
    worker_stats: dict,
    scheduler_stats: dict,
    overall_metrics: dict
) -> str:
    """Generate HTML dashboard for message queue system."""

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Message Queue Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #06b6d4, #0891b2); padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .header h1 {{ margin: 0; color: white; }}
            .metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }}
            .metric {{ background: linear-gradient(135deg, #1e3a8a, #1e40af); padding: 15px; border-radius: 8px; border-left: 4px solid #06b6d4; }}
            .metric .label {{ font-size: 12px; color: #94a3b8; margin-bottom: 5px; }}
            .metric .value {{ font-size: 28px; font-weight: bold; color: #06b6d4; }}
            .section {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
            .section h2 {{ margin: 0 0 15px 0; color: #06b6d4; border-bottom: 2px solid #334155; padding-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th {{ background: #0f172a; padding: 10px; text-align: left; font-size: 12px; color: #94a3b8; border-bottom: 2px solid #334155; }}
            td {{ padding: 10px; border-bottom: 1px solid #334155; }}
            tr:hover {{ background: #0f172a; }}
            .status-idle {{ color: #10b981; }}
            .status-processing {{ color: #f59e0b; }}
            .status-error {{ color: #ef4444; }}
            .progress-bar {{ width: 100%; height: 6px; background: #334155; border-radius: 3px; overflow: hidden; }}
            .progress-fill {{ height: 100%; background: linear-gradient(90deg, #06b6d4, #0891b2); }}
            .footer {{ text-align: center; color: #64748b; font-size: 12px; margin-top: 40px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📦 Message Queue System</h1>
        </div>

        <div class="metrics">
            <div class="metric">
                <div class="label">Total Enqueued</div>
                <div class="value">{overall_metrics.get('total_enqueued', 0):,}</div>
            </div>
            <div class="metric">
                <div class="label">Total Processed</div>
                <div class="value">{overall_metrics.get('total_processed', 0):,}</div>
            </div>
            <div class="metric">
                <div class="label">Success Rate</div>
                <div class="value">{overall_metrics.get('success_rate', 0):.1f}%</div>
            </div>
            <div class="metric">
                <div class="label">Active Queues</div>
                <div class="value">{overall_metrics.get('queue_count', 0)}</div>
            </div>
        </div>

        <div class="section">
            <h2>Queue Status</h2>
            <table>
                <tr>
                    <th>Queue Name</th>
                    <th>Type</th>
                    <th>Size</th>
                    <th>Dead Letters</th>
                    <th>Utilization</th>
                </tr>
    """

    if isinstance(queue_stats, list):
        for queue in queue_stats:
            utilization = queue.get('utilization_percent', 0)
            progress_width = min(utilization, 100)
            html += f"""
                <tr>
                    <td>{queue.get('queue_name', 'N/A')}</td>
                    <td>{queue.get('queue_type', 'N/A')}</td>
                    <td>{queue.get('size', 0)}</td>
                    <td>{queue.get('dead_letter_count', 0)}</td>
                    <td>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {progress_width}%"></div>
                        </div>
                        {utilization:.1f}%
                    </td>
                </tr>
            """

    html += """
            </table>
        </div>

        <div class="section">
            <h2>Worker Pool Status</h2>
            <table>
                <tr>
                    <th>Worker</th>
                    <th>Status</th>
                    <th>Messages Processed</th>
                    <th>Failed</th>
                    <th>Avg Time (ms)</th>
                </tr>
    """

    if worker_stats and 'workers' in worker_stats:
        for worker in worker_stats.get('workers', []):
            status = worker.get('status', 'idle')
            status_class = f"status-{status}"
            html += f"""
                <tr>
                    <td>{worker.get('worker_id', 'N/A')}</td>
                    <td><span class="{status_class}">{status.upper()}</span></td>
                    <td>{worker.get('messages_processed', 0)}</td>
                    <td>{worker.get('messages_failed', 0)}</td>
                    <td>{worker.get('average_processing_time_ms', 0):.2f}</td>
                </tr>
            """

    html += """
            </table>
    """

    if worker_stats:
        html += f"""
            <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #334155;">
                <strong>Pool Statistics:</strong><br>
                Total Processed: {worker_stats.get('total_messages_processed', 0):,}<br>
                Success Rate: {worker_stats.get('success_rate', 0):.1f}%<br>
                Utilization: {worker_stats.get('utilization_percent', 0):.1f}%
            </div>
        """

    html += """
        </div>

        <div class="section">
            <h2>Scheduler Status</h2>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
    """

    if scheduler_stats:
        html += f"""
                <tr>
                    <td>Total Scheduled</td>
                    <td>{scheduler_stats.get('total_scheduled', 0)}</td>
                </tr>
                <tr>
                    <td>Total Executed</td>
                    <td>{scheduler_stats.get('total_executed', 0)}</td>
                </tr>
                <tr>
                    <td>Active Tasks</td>
                    <td>{scheduler_stats.get('active_tasks', 0)}</td>
                </tr>
                <tr>
                    <td>At Capacity</td>
                    <td>{scheduler_stats.get('tasks_at_capacity', 0)}</td>
                </tr>
        """

    html += """
            </table>
        </div>

        <div class="footer">
            <p>Message Queue System Dashboard | Last Updated: """ + f"{overall_metrics.get('timestamp', 'N/A')}" + """</p>
        </div>

    </body>
    </html>
    """

    return html
