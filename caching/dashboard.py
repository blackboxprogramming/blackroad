"""Caching dashboard HTML."""

def generate_caching_dashboard(metrics: dict) -> str:
    """Generate caching dashboard."""
    hit_rate = metrics.get('hit_rate', 0)
    html = f"""<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Caching</title><style>
    body {{ font-family: system-ui; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #e2e8f0; padding: 40px; }}
    .container {{ max-width: 1400px; margin: 0 auto; }}
    h1 {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 30px; }}
    .card {{ background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 12px; padding: 20px; }}
    .value {{ font-size: 28px; font-weight: bold; color: #10b981; margin: 10px 0; }}
    .label {{ color: #94a3b8; font-size: 12px; text-transform: uppercase; }}
    .bar {{ background: linear-gradient(90deg, #10b981 0%, #059669 100%); height: 8px; border-radius: 4px; margin-top: 10px; }}
    </style></head><body><div class='container'>
    <h1>⚡ Caching Performance Dashboard</h1>
    <div class='grid'>
        <div class='card'>
            <div class='label'>Hit Rate</div>
            <div class='value'>{hit_rate:.1f}%</div>
            <div class='bar' style='width: {hit_rate}%'></div>
        </div>
        <div class='card'>
            <div class='label'>Total Hits</div>
            <div class='value'>{metrics.get('total_hits', 0):,}</div>
        </div>
        <div class='card'>
            <div class='label'>Total Misses</div>
            <div class='value'>{metrics.get('total_misses', 0):,}</div>
        </div>
        <div class='card'>
            <div class='label'>Evictions</div>
            <div class='value'>{metrics.get('total_evictions', 0):,}</div>
        </div>
        <div class='card'>
            <div class='label'>Invalidations</div>
            <div class='value'>{metrics.get('total_invalidations', 0):,}</div>
        </div>
        <div class='card'>
            <div class='label'>Cache Size</div>
            <div class='value'>{metrics.get('cache_size', 0):,}</div>
        </div>
    </div>
    </div></body></html>"""
    return html
