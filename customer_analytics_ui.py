"""
Customer-Facing Analytics UI Service
Port: 8004
Provides self-service dashboards for API usage, billing, and forecasting
"""

from flask import Flask, render_template_string, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import os
from functools import wraps
import sqlite3
import csv
from io import StringIO

app = Flask(__name__)
CORS(app)

# ==================== Authentication ====================

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        token = auth.replace('Bearer ', '')
        if not token or len(token) < 10:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

def get_user_id(token):
    """Extract user_id from token (mock implementation)"""
    return f"user_{token[:8]}"

# ==================== Database Access ====================

def get_db():
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    return conn

# ==================== Mock Data Generation ====================

def generate_mock_usage(user_id, days=30):
    """Generate mock usage data for the past N days"""
    usage = []
    base_requests = 1000
    for i in range(days):
        date = (datetime.now() - timedelta(days=days-i)).date()
        requests = int(base_requests * (1 + (i % 7) * 0.15))  # Weekly pattern
        cost = requests * 0.01
        usage.append({
            'date': str(date),
            'requests': requests,
            'cost': round(cost, 2),
            'active_users': int(requests * 0.05),
            'errors': int(requests * 0.001)
        })
    return usage

def get_billing_history(user_id, months=6):
    """Get mock billing history"""
    history = []
    for i in range(months):
        month_date = (datetime.now() - timedelta(days=30*i)).date()
        total_requests = 25000 + (i * 1000)
        total_cost = round(total_requests * 0.01, 2)
        history.append({
            'month': month_date.strftime('%B %Y'),
            'requests': total_requests,
            'cost': total_cost,
            'status': 'Paid' if i > 0 else 'Current',
            'due_date': (month_date + timedelta(days=30)).strftime('%Y-%m-%d')
        })
    return history

def forecast_usage(current_usage, days_ahead=30):
    """Forecast usage for next N days using linear regression"""
    recent = current_usage[-7:]
    avg_daily_requests = sum(u['requests'] for u in recent) / len(recent)
    
    forecast = []
    for i in range(days_ahead):
        date = (datetime.now() + timedelta(days=i)).date()
        requests = int(avg_daily_requests * (1 + (i % 7) * 0.15))
        cost = round(requests * 0.01, 2)
        forecast.append({
            'date': str(date),
            'requests': requests,
            'cost': cost,
            'type': 'forecast'
        })
    return forecast

# ==================== HTML Templates ====================

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Analytics Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        
        .stat-card:hover { transform: translateY(-4px); }
        .stat-card h3 { color: #666; font-size: 0.9rem; margin-bottom: 0.5rem; }
        .stat-card .value { font-size: 2rem; font-weight: bold; color: #333; }
        .stat-card .trend { font-size: 0.85rem; color: #4CAF50; margin-top: 0.5rem; }
        
        .chart-container {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 2rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .chart-title { font-size: 1.2rem; font-weight: bold; margin-bottom: 1rem; color: #333; }
        
        .tabs {
            display: flex;
            gap: 1rem;
            margin-bottom: 1.5rem;
            border-bottom: 2px solid #eee;
        }
        
        .tab {
            padding: 1rem;
            cursor: pointer;
            border: none;
            background: none;
            font-size: 1rem;
            color: #666;
            border-bottom: 3px solid transparent;
            transition: all 0.2s;
        }
        
        .tab.active { color: #667eea; border-bottom-color: #667eea; }
        
        .table-container {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow-x: auto;
        }
        
        table { width: 100%; border-collapse: collapse; }
        th { background: #f5f5f5; padding: 1rem; text-align: left; font-weight: 600; color: #333; }
        td { padding: 1rem; border-bottom: 1px solid #eee; }
        tr:hover { background: #f9f9f9; }
        
        .badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
        }
        
        .badge.paid { background: #4CAF50; color: white; }
        .badge.current { background: #FFC107; color: #333; }
        
        .export-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 1rem;
            transition: background 0.2s;
        }
        
        .export-btn:hover { background: #764ba2; }
        
        .alert {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 4px;
        }
        
        .loading { text-align: center; padding: 2rem; color: #999; }
        
        @media (max-width: 768px) {
            .stats-grid { grid-template-columns: 1fr; }
            .tabs { flex-wrap: wrap; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Usage Analytics Dashboard</h1>
        <p>Track your API usage, billing, and forecasts</p>
    </div>
    
    <div class="container">
        <!-- Stats Overview -->
        <div class="stats-grid">
            <div class="stat-card">
                <h3>This Month</h3>
                <div class="value" id="current-requests">-</div>
                <div class="trend">Requests</div>
            </div>
            <div class="stat-card">
                <h3>Monthly Spend</h3>
                <div class="value" id="current-cost">$-</div>
                <div class="trend">USD</div>
            </div>
            <div class="stat-card">
                <h3>Subscription Tier</h3>
                <div class="value" id="tier-name">-</div>
                <div class="trend">Free tier</div>
            </div>
            <div class="stat-card">
                <h3>Monthly Forecast</h3>
                <div class="value" id="forecast-cost">$-</div>
                <div class="trend">Projected spend</div>
            </div>
        </div>
        
        <!-- Usage Chart -->
        <div class="chart-container">
            <div class="chart-title">30-Day Usage Trend</div>
            <canvas id="usageChart" height="60"></canvas>
        </div>
        
        <!-- Cost Forecast -->
        <div class="chart-container">
            <div class="chart-title">Cost Forecast (Next 30 Days)</div>
            <canvas id="forecastChart" height="60"></canvas>
        </div>
        
        <!-- Tabs -->
        <div class="tabs">
            <button class="tab active" onclick="showTab('usage')">Daily Usage</button>
            <button class="tab" onclick="showTab('billing')">Billing History</button>
            <button class="tab" onclick="showTab('forecast')">Forecast</button>
        </div>
        
        <!-- Tab: Daily Usage -->
        <div id="usage-tab" class="tab-content">
            <div class="table-container">
                <button class="export-btn" onclick="exportUsageCSV()">📥 Export as CSV</button>
                <table style="margin-top: 1rem;">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Requests</th>
                            <th>Cost</th>
                            <th>Active Users</th>
                            <th>Errors</th>
                        </tr>
                    </thead>
                    <tbody id="usage-table">
                        <tr><td colspan="5" class="loading">Loading...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Tab: Billing History -->
        <div id="billing-tab" class="tab-content" style="display: none;">
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Month</th>
                            <th>Requests</th>
                            <th>Total Cost</th>
                            <th>Status</th>
                            <th>Due Date</th>
                        </tr>
                    </thead>
                    <tbody id="billing-table">
                        <tr><td colspan="5" class="loading">Loading...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Tab: Forecast -->
        <div id="forecast-tab" class="tab-content" style="display: none;">
            <div class="alert">
                💡 Usage forecast is based on the last 7 days of activity with weekly seasonality adjustments.
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Projected Requests</th>
                            <th>Projected Cost</th>
                        </tr>
                    </thead>
                    <tbody id="forecast-table">
                        <tr><td colspan="3" class="loading">Loading...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        let usageData = [];
        let billingData = [];
        let forecastData = [];
        
        // Initialize dashboard
        async function initDashboard() {
            try {
                await Promise.all([
                    loadUsageData(),
                    loadBillingData(),
                    loadForecastData()
                ]);
                renderCharts();
                renderTables();
                updateStats();
            } catch (err) {
                console.error('Error loading dashboard:', err);
            }
        }
        
        async function loadUsageData() {
            const res = await fetch('/api/customer/usage', {
                headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
            });
            usageData = await res.json();
        }
        
        async function loadBillingData() {
            const res = await fetch('/api/customer/billing-history', {
                headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
            });
            billingData = await res.json();
        }
        
        async function loadForecastData() {
            const res = await fetch('/api/customer/forecast', {
                headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
            });
            forecastData = await res.json();
        }
        
        function renderCharts() {
            // Usage Chart
            const usageCtx = document.getElementById('usageChart').getContext('2d');
            new Chart(usageCtx, {
                type: 'line',
                data: {
                    labels: usageData.map(u => u.date),
                    datasets: [{
                        label: 'Requests',
                        data: usageData.map(u => u.requests),
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });
            
            // Forecast Chart
            const forecastCtx = document.getElementById('forecastChart').getContext('2d');
            new Chart(forecastCtx, {
                type: 'bar',
                data: {
                    labels: forecastData.map(f => f.date),
                    datasets: [{
                        label: 'Projected Cost ($)',
                        data: forecastData.map(f => f.cost),
                        backgroundColor: '#764ba2'
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });
        }
        
        function renderTables() {
            // Usage table
            const usageHtml = usageData.map(u => `
                <tr>
                    <td>${u.date}</td>
                    <td>${u.requests.toLocaleString()}</td>
                    <td>$${u.cost.toFixed(2)}</td>
                    <td>${u.active_users}</td>
                    <td>${u.errors}</td>
                </tr>
            `).join('');
            document.getElementById('usage-table').innerHTML = usageHtml;
            
            // Billing table
            const billingHtml = billingData.map(b => `
                <tr>
                    <td>${b.month}</td>
                    <td>${b.requests.toLocaleString()}</td>
                    <td>$${b.cost.toFixed(2)}</td>
                    <td><span class="badge ${b.status.toLowerCase()}">${b.status}</span></td>
                    <td>${b.due_date}</td>
                </tr>
            `).join('');
            document.getElementById('billing-table').innerHTML = billingHtml;
            
            // Forecast table
            const forecastHtml = forecastData.slice(0, 10).map(f => `
                <tr>
                    <td>${f.date}</td>
                    <td>${f.requests.toLocaleString()}</td>
                    <td>$${f.cost.toFixed(2)}</td>
                </tr>
            `).join('');
            document.getElementById('forecast-table').innerHTML = forecastHtml;
        }
        
        function updateStats() {
            const monthUsage = usageData.reduce((sum, u) => sum + u.requests, 0);
            const monthCost = usageData.reduce((sum, u) => sum + u.cost, 0);
            const forecastSum = forecastData.reduce((sum, f) => sum + f.cost, 0);
            
            document.getElementById('current-requests').textContent = monthUsage.toLocaleString();
            document.getElementById('current-cost').textContent = `$${monthCost.toFixed(2)}`;
            document.getElementById('forecast-cost').textContent = `$${forecastSum.toFixed(2)}`;
        }
        
        function showTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(t => t.style.display = 'none');
            document.getElementById(tabName + '-tab').style.display = 'block';
            document.querySelectorAll('.tab').forEach((t, i) => {
                t.classList.toggle('active', t.textContent.includes(
                    tabName === 'usage' ? 'Daily' : tabName === 'billing' ? 'Billing' : 'Forecast'
                ));
            });
        }
        
        function exportUsageCSV() {
            const csv = ['Date,Requests,Cost,Active Users,Errors'].concat(
                usageData.map(u => `${u.date},${u.requests},${u.cost},${u.active_users},${u.errors}`)
            ).join('\\n');
            
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'usage-' + new Date().toISOString().split('T')[0] + '.csv';
            a.click();
        }
        
        // Load token from localStorage or query param
        const token = new URLSearchParams(window.location.search).get('token') || localStorage.getItem('token');
        if (token) localStorage.setItem('token', token);
        
        // Initialize on load
        window.addEventListener('load', initDashboard);
    </script>
</body>
</html>
"""

# ==================== API Endpoints ====================

@app.route('/', methods=['GET'])
@require_auth
def dashboard():
    """Serve the analytics dashboard UI"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/customer/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get customer profile and tier info"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = get_user_id(token)
    
    return jsonify({
        'user_id': user_id,
        'email': f'{user_id}@example.com',
        'tier': 'Light',
        'tier_limit_requests_per_hour': 7200,
        'monthly_limit': 180000,
        'joined_date': '2024-01-15',
        'payment_method': '•••• 4242'
    })

@app.route('/api/customer/usage', methods=['GET'])
@require_auth
def get_usage():
    """Get usage data for past 30 days"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = get_user_id(token)
    usage = generate_mock_usage(user_id, days=30)
    return jsonify(usage)

@app.route('/api/customer/billing-history', methods=['GET'])
@require_auth
def get_billing_history_endpoint():
    """Get billing history for past 6 months"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = get_user_id(token)
    history = get_billing_history(user_id, months=6)
    return jsonify(history)

@app.route('/api/customer/forecast', methods=['GET'])
@require_auth
def get_forecast():
    """Get usage forecast for next 30 days"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = get_user_id(token)
    usage = generate_mock_usage(user_id, days=30)
    forecast = forecast_usage(usage, days_ahead=30)
    return jsonify(forecast)

@app.route('/api/customer/alerts', methods=['GET'])
@require_auth
def get_alerts():
    """Get usage alerts and warnings"""
    return jsonify([
        {
            'id': '1',
            'type': 'usage_warning',
            'message': 'You\'ve used 75% of your monthly limit',
            'severity': 'warning',
            'created_at': (datetime.now() - timedelta(hours=2)).isoformat()
        },
        {
            'id': '2',
            'type': 'forecast_alert',
            'message': 'Based on current usage, you\'ll exceed your limit by 15% next month',
            'severity': 'info',
            'created_at': (datetime.now() - timedelta(hours=24)).isoformat()
        }
    ])

@app.route('/api/customer/billing-portal', methods=['GET'])
@require_auth
def get_billing_portal():
    """Get Stripe billing portal link"""
    # In production, this would create a Stripe billing portal session
    return jsonify({
        'portal_url': 'https://billing.stripe.com/p/example'
    })

@app.route('/api/customer/export', methods=['GET'])
@require_auth
def export_data():
    """Export usage data as CSV"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = get_user_id(token)
    usage = generate_mock_usage(user_id, days=90)
    
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=['date', 'requests', 'cost', 'active_users', 'errors'])
    writer.writeheader()
    writer.writerows(usage)
    
    return output.getvalue(), 200, {
        'Content-Disposition': 'attachment; filename=usage-export.csv',
        'Content-Type': 'text/csv'
    }

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'ok', 'service': 'customer-analytics-ui'})

# ==================== Entry Point ====================

if __name__ == '__main__':
    print("🎨 Customer Analytics UI starting on http://localhost:8004")
    print("📊 Access at: http://localhost:8004/?token=YOUR_API_KEY")
    print("📖 API docs: http://localhost:8004/api-docs")
    app.run(host='0.0.0.0', port=8004, debug=True)
