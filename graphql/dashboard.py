"""GraphQL dashboard HTML."""

def generate_graphql_dashboard(metrics: dict) -> str:
    """Generate GraphQL dashboard."""
    request_rate = (metrics.get('total_requests', 0) - metrics.get('total_errors', 0)) / max(metrics.get('total_requests', 1), 1) * 100
    html = f"""<!DOCTYPE html><html><head><meta charset='UTF-8'><title>GraphQL</title><style>
    body {{ font-family: system-ui; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #e2e8f0; padding: 40px; }}
    .container {{ max-width: 1400px; margin: 0 auto; }}
    h1 {{ background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 30px; }}
    .card {{ background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 12px; padding: 20px; }}
    .value {{ font-size: 28px; font-weight: bold; color: #8b5cf6; margin: 10px 0; }}
    .label {{ color: #94a3b8; font-size: 12px; text-transform: uppercase; }}
    </style></head><body><div class='container'>
    <h1>🚀 GraphQL API Gateway</h1>
    <div class='grid'>
        <div class='card'><div class='label'>Total Requests</div><div class='value'>{metrics.get('total_requests', 0):,}</div></div>
        <div class='card'><div class='label'>Success Rate</div><div class='value'>{request_rate:.1f}%</div></div>
        <div class='card'><div class='label'>Errors</div><div class='value'>{metrics.get('total_errors', 0):,}</div></div>
        <div class='card'><div class='label'>Avg Query Depth</div><div class='value'>{metrics.get('avg_depth', 0):.1f}</div></div>
        <div class='card'><div class='label'>Request Log Size</div><div class='value'>{metrics.get('request_log_size', 0):,}</div></div>
        <div class='card'><div class='label'>Subscribers</div><div class='value'>{metrics.get('subscribers', 0):,}</div></div>
    </div>
    </div></body></html>"""
    return html
