"""
Revenue Intelligence Dashboard
Real-time LTV, expansion, and revenue forecasting
"""

from datetime import datetime
from predictor import (
    LTVPredictor, Customer, ExpansionEngine, 
    DynamicPricingEngine, RevenueForecast,
    CustomerSegment, ChurnRiskLevel
)


class RevenueIntelligenceDashboard:
    """Generate HTML dashboard for revenue metrics."""
    
    def __init__(self):
        self.generated_at = datetime.utcnow().isoformat()
    
    def generate_html(self, predictor: LTVPredictor, 
                     engine: ExpansionEngine,
                     pricing_engine: DynamicPricingEngine,
                     forecast: RevenueForecast) -> str:
        """Generate comprehensive dashboard HTML."""
        
        ltv_dist = predictor.get_ltv_distribution()
        segment_pricing = pricing_engine.get_segment_pricing()
        arr_forecast = forecast.forecast_arr(12)
        ltv_forecast = forecast.forecast_ltv_pool(12)
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Revenue Intelligence Dashboard</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                margin: 0; padding: 20px; background: #f5f7fa; }}
        .dashboard {{ max-width: 1400px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                  color: white; padding: 30px; border-radius: 8px; margin-bottom: 30px; }}
        .header h1 {{ margin: 0; font-size: 32px; }}
        .header p {{ margin: 5px 0 0 0; opacity: 0.9; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
                gap: 20px; margin-bottom: 30px; }}
        .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .card h3 {{ margin: 0 0 10px 0; color: #333; font-size: 14px; text-transform: uppercase; 
                   letter-spacing: 1px; opacity: 0.7; }}
        .metric {{ font-size: 32px; font-weight: bold; color: #667eea; margin: 10px 0; }}
        .metric-small {{ font-size: 14px; color: #666; margin-top: 10px; }}
        .segment {{ padding: 15px; background: #f8f9fa; border-left: 4px solid #667eea; 
                   margin-bottom: 10px; border-radius: 4px; }}
        .segment-name {{ font-weight: 600; color: #333; margin-bottom: 8px; }}
        .segment-metrics {{ font-size: 13px; color: #666; }}
        .chart {{ background: #f8f9fa; padding: 20px; border-radius: 8px; 
                 font-family: 'Courier New', monospace; overflow-x: auto; }}
        .warning {{ color: #e74c3c; }}
        .success {{ color: #27ae60; }}
        .info {{ color: #3498db; }}
        .table {{ width: 100%; border-collapse: collapse; }}
        .table th {{ background: #f8f9fa; padding: 12px; text-align: left; 
                    font-weight: 600; border-bottom: 1px solid #ddd; font-size: 13px; }}
        .table td {{ padding: 12px; border-bottom: 1px solid #eee; font-size: 13px; }}
        .table tr:hover {{ background: #f8f9fa; }}
        .risk-critical {{ color: #e74c3c; font-weight: 600; }}
        .risk-high {{ color: #f39c12; font-weight: 600; }}
        .risk-medium {{ color: #f1c40f; font-weight: 600; }}
        .risk-low {{ color: #27ae60; font-weight: 600; }}
        .opportunity {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                       color: white; padding: 12px; border-radius: 4px; margin: 8px 0; }}
        .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 40px; 
                  padding-top: 20px; border-top: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>💰 Revenue Intelligence Dashboard</h1>
            <p>LTV Prediction, Expansion Opportunities & Revenue Forecasting</p>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>Total LTV Pool</h3>
                <div class="metric">${ltv_dist.get('total_ltv', 0):,.0f}</div>
                <div class="metric-small">
                    {len(predictor.customers)} customers<br>
                    Avg LTV: ${ltv_dist.get('average_ltv', 0):,.0f}
                </div>
            </div>
            
            <div class="card">
                <h3>Projected 12M ARR</h3>
                <div class="metric">${arr_forecast.get('forecasted_arr_12m', 0):,.0f}</div>
                <div class="metric-small">
                    Current: ${arr_forecast.get('current_arr', 0):,.0f}<br>
                    Growth: <span class="success">{arr_forecast.get('growth_rate', 0):.1f}%</span>
                </div>
            </div>
            
            <div class="card">
                <h3>Forecasted LTV Pool</h3>
                <div class="metric">${ltv_forecast.get('forecasted_ltv_pool_12m', 0):,.0f}</div>
                <div class="metric-small">
                    Current: ${ltv_forecast.get('current_ltv_pool', 0):,.0f}<br>
                    Growth/Month: {ltv_forecast.get('monthly_growth_rate', 0)*100:.1f}%
                </div>
            </div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>Customer Segments</h3>
                <div class="segment">
                    <div class="segment-name">Enterprise ($100K+ ARR)</div>
                    <div class="segment-metrics">
                        Base: ${segment_pricing['enterprise']['base']:,}/mo<br>
                        Unit: ${segment_pricing['enterprise']['unit']}/1K calls<br>
                        Max: ${segment_pricing['enterprise']['max']:,}/mo
                    </div>
                </div>
                <div class="segment">
                    <div class="segment-name">Mid-Market ($10-100K ARR)</div>
                    <div class="segment-metrics">
                        Base: ${segment_pricing['mid_market']['base']:,}/mo<br>
                        Unit: ${segment_pricing['mid_market']['unit']}/1K calls<br>
                        Max: ${segment_pricing['mid_market']['max']:,}/mo
                    </div>
                </div>
                <div class="segment">
                    <div class="segment-name">SMB ($1-10K ARR)</div>
                    <div class="segment-metrics">
                        Base: ${segment_pricing['smb']['base']}/mo<br>
                        Unit: ${segment_pricing['smb']['unit']}/1K calls<br>
                        Max: ${segment_pricing['smb']['max']:,}/mo
                    </div>
                </div>
                <div class="segment">
                    <div class="segment-name">Startup (<$1K ARR)</div>
                    <div class="segment-metrics">
                        Base: Free<br>
                        Unit: ${segment_pricing['startup']['unit']}/1K calls<br>
                        Max: ${segment_pricing['startup']['max']}/mo
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>LTV Distribution</h3>
                <table class="table">
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>Average</td>
                        <td><strong>${ltv_dist.get('average_ltv', 0):,.0f}</strong></td>
                    </tr>
                    <tr>
                        <td>Median</td>
                        <td><strong>${ltv_dist.get('median_ltv', 0):,.0f}</strong></td>
                    </tr>
                    <tr>
                        <td>Max</td>
                        <td><strong class="success">${ltv_dist.get('max_ltv', 0):,.0f}</strong></td>
                    </tr>
                    <tr>
                        <td>Min</td>
                        <td><strong>${ltv_dist.get('min_ltv', 0):,.0f}</strong></td>
                    </tr>
                </table>
            </div>
        </div>
        
        <div class="card">
            <h3>12-Month Revenue Forecast</h3>
            <div class="chart">
                MRR Projection (12 months):<br>
"""
        
        # Add MRR forecast chart
        mrr_forecast = forecast.forecast_mrr(12)
        if mrr_forecast:
            max_mrr = max(f['forecasted_mrr'] for f in mrr_forecast)
            for f in mrr_forecast:
                bar_width = int((f['forecasted_mrr'] / max_mrr) * 50) if max_mrr > 0 else 0
                bar = "█" * bar_width
                html += f"Month {f['month']:2d}: {bar} ${f['forecasted_mrr']:>10,.0f}<br>"
        
        html += f"""
            </div>
        </div>
        
        <div class="card">
            <h3>Risk Analysis</h3>
            <table class="table">
                <tr>
                    <th>Risk Level</th>
                    <th>Count</th>
                    <th>Action Required</th>
                </tr>
"""
        
        # Count by risk level
        risk_counts = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
        }
        
        for customer in predictor.customers.values():
            risk_counts[customer.churn_risk.value] += 1
        
        for level, count in risk_counts.items():
            if count > 0:
                class_name = f'risk-{level}'
                action = 'URGENT: Immediate outreach' if level == 'critical' else \
                        'Priority: Engagement plan' if level == 'high' else \
                        'Monitor: Quarterly check-in' if level == 'medium' else \
                        'Monitor: Standard support'
                html += f'<tr><td class="{class_name}">{level.upper()}</td><td>{count}</td><td>{action}</td></tr>'
        
        html += """
            </table>
        </div>
        
        <div class="card">
            <h3>Expansion Opportunities</h3>
"""
        
        # Add opportunities
        opportunity_types = {}
        total_potential = 0
        for opp in engine.opportunities:
            opp_type = opp['type']
            if opp_type not in opportunity_types:
                opportunity_types[opp_type] = []
            opportunity_types[opp_type].append(opp)
            total_potential += opp.get('potential_mrr_increase', 0)
        
        html += f"""
            <div class="metric-small">
                <strong>{len(engine.opportunities)} opportunities identified</strong><br>
                Potential MRR increase: <span class="success">${total_potential:,.0f}</span>
            </div>
"""
        
        for opp_type, opps in opportunity_types.items():
            html += f'<div class="opportunity"><strong>{opp_type.upper()}</strong> ({len(opps)} customers)<br>'
            for opp in opps[:3]:  # Show top 3
                html += f"  • {opp['recommendation']} (${opp['potential_mrr_increase']:,}/mo, "
                html += f"{opp['confidence']*100:.0f}% confidence)<br>"
            html += '</div>'
        
        html += f"""
        </div>
        
        <div class="footer">
            Generated {self.generated_at} UTC<br>
            Advanced Revenue Intelligence System v1.0 | Phase 11
        </div>
    </div>
</body>
</html>
"""
        return html
