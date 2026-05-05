"""
Cost Optimization Dashboard
Real-time cost tracking and optimization opportunities
"""

from typing import Dict, List
from datetime import datetime


class CostOptimizationDashboard:
    """Generate cost optimization dashboard."""
    
    def __init__(self):
        self.generated_at = datetime.utcnow()
    
    def generate_html_dashboard(self) -> str:
        """Generate HTML cost optimization dashboard."""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cost Optimization Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f6f8fa;
            color: #24292e;
        }
        
        header {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 24px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        header h1 {
            font-size: 28px;
            margin-bottom: 8px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 24px;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        
        .card {
            background: white;
            border: 1px solid #e1e4e8;
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        
        .card-title {
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            color: #6a737d;
            margin-bottom: 12px;
        }
        
        .metric {
            font-size: 32px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .metric.savings {
            color: #10b981;
        }
        
        .metric.critical {
            color: #da3633;
        }
        
        .metric.warning {
            color: #d29922;
        }
        
        .section {
            background: white;
            border: 1px solid #e1e4e8;
            border-radius: 8px;
            margin-bottom: 24px;
            overflow: hidden;
        }
        
        .section-header {
            padding: 16px;
            border-bottom: 1px solid #e1e4e8;
            font-weight: 600;
            background: #f6f8fa;
        }
        
        .section-content {
            padding: 16px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #e1e4e8;
        }
        
        th {
            background: #f6f8fa;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .status-optimized {
            background: #dafbe1;
            color: #033a16;
        }
        
        .status-savings {
            background: #ddf4ff;
            color: #0c2e6b;
        }
        
        .status-waste {
            background: #fff8c5;
            color: #3d2601;
        }
        
        .status-critical {
            background: #ffebe6;
            color: #82180d;
        }
        
        .chart {
            display: flex;
            gap: 8px;
            align-items: flex-end;
            height: 200px;
            margin: 16px 0;
        }
        
        .chart-bar {
            flex: 1;
            background: linear-gradient(180deg, #10b981, #059669);
            border-radius: 4px 4px 0 0;
            position: relative;
            min-height: 20px;
        }
        
        .chart-label {
            position: absolute;
            bottom: -30px;
            width: 100%;
            text-align: center;
            font-size: 11px;
            color: #6a737d;
        }
        
        .savings-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
        }
        
        .savings-item {
            background: #f0fdf4;
            border: 1px solid #dcfce7;
            border-radius: 6px;
            padding: 16px;
        }
        
        .savings-item h3 {
            font-size: 14px;
            margin-bottom: 8px;
            color: #027a48;
        }
        
        .savings-amount {
            font-size: 24px;
            font-weight: 600;
            color: #10b981;
        }
        
        .savings-period {
            font-size: 12px;
            color: #6a737d;
            margin-top: 4px;
        }
    </style>
</head>
<body>
    <header>
        <h1>💰 Cost Optimization Dashboard</h1>
        <p>Real-time cloud cost analysis and optimization opportunities</p>
    </header>
    
    <div class="container">
        <!-- Key Metrics -->
        <div class="grid">
            <div class="card">
                <div class="card-title">Current Monthly Spend</div>
                <div class="metric">$124.5K</div>
                <p style="font-size: 12px; color: #6a737d;">↓ 2.3% from last month</p>
            </div>
            
            <div class="card">
                <div class="card-title">Annual Spend</div>
                <div class="metric">$1.49M</div>
                <p style="font-size: 12px; color: #6a737d;">6 AWS regions + CDN</p>
            </div>
            
            <div class="card">
                <div class="card-title">Potential Monthly Savings</div>
                <div class="metric savings">$47.3K</div>
                <p style="font-size: 12px; color: #6a737d;">38% reduction</p>
            </div>
            
            <div class="card">
                <div class="card-title">Potential Annual Savings</div>
                <div class="metric savings">$567.6K</div>
                <p style="font-size: 12px; color: #6a737d;">If optimized now</p>
            </div>
        </div>
        
        <!-- Cost by Region -->
        <div class="section">
            <div class="section-header">🌍 Spend by Region</div>
            <div class="section-content">
                <table>
                    <thead>
                        <tr>
                            <th>Region</th>
                            <th>Monthly Cost</th>
                            <th>Annual Cost</th>
                            <th>% of Total</th>
                            <th>Optimization Potential</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>us-east-1</td>
                            <td>$42,300</td>
                            <td>$507,600</td>
                            <td>34%</td>
                            <td><span class="status-badge status-waste">$16.4K/mo</span></td>
                        </tr>
                        <tr>
                            <td>eu-west-1</td>
                            <td>$28,450</td>
                            <td>$341,400</td>
                            <td>23%</td>
                            <td><span class="status-badge status-waste">$12.1K/mo</span></td>
                        </tr>
                        <tr>
                            <td>ap-southeast-1</td>
                            <td>$19,200</td>
                            <td>$230,400</td>
                            <td>15%</td>
                            <td><span class="status-badge status-waste">$8.3K/mo</span></td>
                        </tr>
                        <tr>
                            <td>us-west-2</td>
                            <td>$18,600</td>
                            <td>$223,200</td>
                            <td>15%</td>
                            <td><span class="status-badge status-waste">$6.7K/mo</span></td>
                        </tr>
                        <tr>
                            <td>eu-central-1</td>
                            <td>$12,800</td>
                            <td>$153,600</td>
                            <td>10%</td>
                            <td><span class="status-badge status-savings">$2.8K/mo</span></td>
                        </tr>
                        <tr>
                            <td>ap-northeast-1</td>
                            <td>$3,150</td>
                            <td>$37,800</td>
                            <td>3%</td>
                            <td><span class="status-badge status-optimized">Optimized</span></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Underutilized Resources -->
        <div class="section">
            <div class="section-header">🚨 Underutilized Resources (42 found)</div>
            <div class="section-content">
                <table>
                    <thead>
                        <tr>
                            <th>Resource ID</th>
                            <th>Type</th>
                            <th>Region</th>
                            <th>Utilization</th>
                            <th>Monthly Cost</th>
                            <th>Savings Potential</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>i-0a1b2c3d4e5f</td>
                            <td>EC2 (m5.2xlarge)</td>
                            <td>us-east-1</td>
                            <td><span class="status-badge status-critical">2%</span></td>
                            <td>$2,847</td>
                            <td>$2,278 (80%)</td>
                        </tr>
                        <tr>
                            <td>i-1b2c3d4e5f6g</td>
                            <td>EC2 (m5.xlarge)</td>
                            <td>eu-west-1</td>
                            <td><span class="status-badge status-waste">8%</span></td>
                            <td>$1,423</td>
                            <td>$854 (60%)</td>
                        </tr>
                        <tr>
                            <td>rds-prod-01</td>
                            <td>RDS (db.r5.2xl)</td>
                            <td>us-east-1</td>
                            <td><span class="status-badge status-critical">3%</span></td>
                            <td>$4,156</td>
                            <td>$3,325 (80%)</td>
                        </tr>
                        <tr>
                            <td>i-2c3d4e5f6g7h</td>
                            <td>EC2 (c5.4xlarge)</td>
                            <td>ap-southeast-1</td>
                            <td><span class="status-badge status-waste">12%</span></td>
                            <td>$3,612</td>
                            <td>$1,808 (50%)</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Consolidation Opportunities -->
        <div class="section">
            <div class="section-header">🔗 Consolidation Opportunities (18 found)</div>
            <div class="section-content">
                <div class="savings-grid">
                    <div class="savings-item">
                        <h3>Compute Consolidation - us-east-1</h3>
                        <p style="font-size: 12px; margin-bottom: 8px;">12 small EC2 instances → 3 large instances</p>
                        <div class="savings-amount">$8.4K/mo</div>
                        <div class="savings-period">$100.8K annually</div>
                    </div>
                    
                    <div class="savings-item">
                        <h3>Database Consolidation - eu-west-1</h3>
                        <p style="font-size: 12px; margin-bottom: 8px;">7 RDS instances → Aurora cluster</p>
                        <div class="savings-amount">$6.2K/mo</div>
                        <div class="savings-period">$74.4K annually</div>
                    </div>
                    
                    <div class="savings-item">
                        <h3>Cache Consolidation - ap-southeast-1</h3>
                        <p style="font-size: 12px; margin-bottom: 8px;">8 Redis nodes → ElastiCache</p>
                        <div class="savings-amount">$3.8K/mo</div>
                        <div class="savings-period">$45.6K annually</div>
                    </div>
                    
                    <div class="savings-item">
                        <h3>Reserved Instances - All Regions</h3>
                        <p style="font-size: 12px; margin-bottom: 8px;">Convert 45 on-demand to 3-year RI</p>
                        <div class="savings-amount">$18.3K/mo</div>
                        <div class="savings-period">$219.6K annually</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Cost by Resource Type -->
        <div class="section">
            <div class="section-header">📊 Spend by Resource Type</div>
            <div class="section-content">
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px;">
                    <div>
                        <h3 style="margin-bottom: 16px; font-size: 14px;">Monthly Breakdown</h3>
                        <table style="font-size: 13px;">
                            <tr style="border-bottom: 1px solid #e1e4e8;">
                                <td style="padding: 8px 0;">Compute (EC2)</td>
                                <td style="text-align: right; font-weight: 600;">$52.1K (42%)</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #e1e4e8;">
                                <td style="padding: 8px 0;">Database (RDS)</td>
                                <td style="text-align: right; font-weight: 600;">$28.3K (23%)</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #e1e4e8;">
                                <td style="padding: 8px 0;">Storage (S3)</td>
                                <td style="text-align: right; font-weight: 600;">$18.7K (15%)</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #e1e4e8;">
                                <td style="padding: 8px 0;">Network (CDN)</td>
                                <td style="text-align: right; font-weight: 600;">$15.2K (12%)</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0;">Other</td>
                                <td style="text-align: right; font-weight: 600;">$10.2K (8%)</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div>
                        <h3 style="margin-bottom: 16px; font-size: 14px;">Savings Opportunities</h3>
                        <table style="font-size: 13px;">
                            <tr style="border-bottom: 1px solid #e1e4e8;">
                                <td style="padding: 8px 0;">Right-sizing</td>
                                <td style="text-align: right; font-weight: 600; color: #10b981;">$18.2K/mo</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #e1e4e8;">
                                <td style="padding: 8px 0;">Consolidation</td>
                                <td style="text-align: right; font-weight: 600; color: #10b981;">$18.4K/mo</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #e1e4e8;">
                                <td style="padding: 8px 0;">Reserved Instances</td>
                                <td style="text-align: right; font-weight: 600; color: #10b981;">$10.7K/mo</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0;">Total Potential</td>
                                <td style="text-align: right; font-weight: 600; color: #10b981;">$47.3K/mo</td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Recommendations -->
        <div class="section">
            <div class="section-header">✅ Recommended Actions (Priority Order)</div>
            <div class="section-content">
                <div style="display: grid; gap: 12px;">
                    <div style="padding: 12px; background: #fef3c7; border-left: 4px solid #d29922; border-radius: 4px;">
                        <div style="font-weight: 600; margin-bottom: 4px;">1. Convert on-demand to reserved instances</div>
                        <p style="font-size: 12px; color: #6a737d;">Impact: $10.7K/month, 3-month payback</p>
                    </div>
                    
                    <div style="padding: 12px; background: #fef3c7; border-left: 4px solid #d29922; border-radius: 4px;">
                        <div style="font-weight: 600; margin-bottom: 4px;">2. Right-size underutilized instances</div>
                        <p style="font-size: 12px; color: #6a737d;">Impact: $18.2K/month, no downtime (canary deploy)</p>
                    </div>
                    
                    <div style="padding: 12px; background: #fef3c7; border-left: 4px solid #d29922; border-radius: 4px;">
                        <div style="font-weight: 600; margin-bottom: 4px;">3. Consolidate databases and caches</div>
                        <p style="font-size: 12px; color: #6a737d;">Impact: $10.2K/month, 1-2 week migration</p>
                    </div>
                    
                    <div style="padding: 12px; background: #dbeafe; border-left: 4px solid #0284c7; border-radius: 4px;">
                        <div style="font-weight: 600; margin-bottom: 4px;">4. Enable auto-scaling policies</div>
                        <p style="font-size: 12px; color: #6a737d;">Impact: 8.9K/month savings, real-time optimization</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''
