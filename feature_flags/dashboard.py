"""Feature flags dashboard HTML."""

def generate_feature_flags_dashboard(metrics: dict) -> str:
    """Generate feature flags dashboard."""
    enabled_rate = metrics.get('enabled_rate', 0)
    html = f"""<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Feature Flags</title><style>
    body {{ font-family: system-ui; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #e2e8f0; padding: 40px; }}
    .container {{ max-width: 1400px; margin: 0 auto; }}
    h1 {{ background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 30px; }}
    .card {{ background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(6, 182, 212, 0.3); border-radius: 12px; padding: 20px; }}
    .value {{ font-size: 28px; font-weight: bold; color: #06b6d4; margin: 10px 0; }}
    .label {{ color: #94a3b8; font-size: 12px; text-transform: uppercase; }}
    </style></head><body><div class='container'>
    <h1>🚩 Feature Flags Control</h1>
    <div class='grid'>
        <div class='card'><div class='label'>Total Flags</div><div class='value'>{metrics.get('total_flags', 0):,}</div></div>
        <div class='card'><div class='label'>Enabled</div><div class='value'>{metrics.get('enabled_flags', 0):,}</div></div>
        <div class='card'><div class='label'>Enable Rate</div><div class='value'>{enabled_rate:.1f}%</div></div>
        <div class='card'><div class='label'>Evaluations</div><div class='value'>{metrics.get('total_evaluations', 0):,}</div></div>
        <div class='card'><div class='label'>Active Segments</div><div class='value'>{metrics.get('segments', 0):,}</div></div>
        <div class='card'><div class='label'>Rules Configured</div><div class='value'>{metrics.get('rules', 0):,}</div></div>
    </div>
    </div></body></html>"""
    return html
