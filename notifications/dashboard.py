"""Notification dashboard HTML."""

def generate_notification_dashboard(metrics: dict) -> str:
    """Generate notification dashboard."""
    success_rate = metrics.get('success_rate', 0)
    html = f"""<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Notifications</title><style>
    body {{ font-family: system-ui; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #e2e8f0; padding: 40px; }}
    .container {{ max-width: 1400px; margin: 0 auto; }}
    h1 {{ background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 30px; }}
    .card {{ background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 12px; padding: 20px; }}
    .value {{ font-size: 28px; font-weight: bold; color: #f59e0b; margin: 10px 0; }}
    .label {{ color: #94a3b8; font-size: 12px; text-transform: uppercase; }}
    </style></head><body><div class='container'>
    <h1>📬 Notification System</h1>
    <div class='grid'>
        <div class='card'><div class='label'>Total Sent</div><div class='value'>{metrics.get('total', 0):,}</div></div>
        <div class='card'><div class='label'>Delivered</div><div class='value'>{metrics.get('delivered', 0):,}</div></div>
        <div class='card'><div class='label'>Failed</div><div class='value'>{metrics.get('failed', 0):,}</div></div>
        <div class='card'><div class='label'>Success Rate</div><div class='value'>{success_rate:.1f}%</div></div>
        <div class='card'><div class='label'>Queue Size</div><div class='value'>{metrics.get('queue_size', 0):,}</div></div>
        <div class='card'><div class='label'>Active Rules</div><div class='value'>{metrics.get('enabled_rules', 0):,}</div></div>
    </div>
    </div></body></html>"""
    return html
