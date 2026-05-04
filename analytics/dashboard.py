"""Analytics dashboard HTML."""

def generate_analytics_dashboard(metrics: dict) -> str:
    """Generate analytics dashboard."""
    html = f"""<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Analytics</title><style>
    body {{ font-family: system-ui; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #e2e8f0; padding: 40px; }}
    .container {{ max-width: 1400px; margin: 0 auto; }}
    h1 {{ background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 30px; }}
    .card {{ background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 12px; padding: 20px; }}
    .value {{ font-size: 28px; font-weight: bold; color: #3b82f6; margin: 10px 0; }}
    .label {{ color: #94a3b8; font-size: 12px; text-transform: uppercase; }}
    </style></head><body><div class='container'>
    <h1>📊 Analytics Dashboard</h1>
    <div class='grid'>
        <div class='card'><div class='label'>Total Events</div><div class='value'>{metrics.get('total_events', 0):,}</div></div>
        <div class='card'><div class='label'>Unique Users</div><div class='value'>{metrics.get('unique_users', 0):,}</div></div>
        <div class='card'><div class='label'>Total Revenue</div><div class='value'>${metrics.get('total_revenue', 0):,.2f}</div></div>
        <div class='card'><div class='label'>Fact Tables</div><div class='value'>{metrics.get('fact_tables', 0)}</div></div>
        <div class='card'><div class='label'>Dimension Tables</div><div class='value'>{metrics.get('dimension_tables', 0)}</div></div>
        <div class='card'><div class='label'>Warehouse Rows</div><div class='value'>{metrics.get('total_rows', 0):,}</div></div>
    </div>
    </div></body></html>"""
    return html
