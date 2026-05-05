"""
Developer Portal Dashboard - API keys, usage stats, SDKs, docs
"""

import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import hashlib
import secrets
import logging


class APIKey:
    """Represents an API key."""
    
    def __init__(self, name: str, environment: str = "development"):
        self.id = f"sk_{secrets.token_hex(16)}"
        self.name = name
        self.environment = environment
        self.prefix = self.id[:10] + "..."
        self.secret = secrets.token_urlsafe(32)
        self.is_active = True
        self.created_at = datetime.utcnow()
        self.last_used = None
        self.ip_allowlist: List[str] = []
        self.permissions: List[str] = ["read", "write"]
        self.rate_limit = 1000
        self.requests_this_month = 0


class DeveloperPortalDashboard:
    """Main developer portal dashboard."""
    
    def __init__(self):
        self.api_keys: Dict[str, APIKey] = {}
        self.usage_stats = {
            'requests_today': 0,
            'requests_this_month': 0,
            'errors_today': 0,
            'avg_latency_ms': 0,
        }
        self.logger = logging.getLogger(__name__)
    
    def create_api_key(self, name: str, environment: str = "development") -> APIKey:
        """Create new API key."""
        key = APIKey(name, environment)
        self.api_keys[key.id] = key
        self.logger.info(f"API key created: {key.id}")
        return key
    
    def get_api_keys(self) -> List[APIKey]:
        """Get all API keys."""
        return list(self.api_keys.values())
    
    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke API key."""
        if key_id in self.api_keys:
            self.api_keys[key_id].is_active = False
            self.logger.info(f"API key revoked: {key_id}")
            return True
        return False
    
    def rotate_api_key(self, key_id: str) -> Optional[APIKey]:
        """Rotate API key."""
        if key_id not in self.api_keys:
            return None
        
        old_key = self.api_keys[key_id]
        new_key = APIKey(old_key.name, old_key.environment)
        self.api_keys[new_key.id] = new_key
        del self.api_keys[key_id]
        
        self.logger.info(f"API key rotated: {key_id} -> {new_key.id}")
        return new_key
    
    def set_ip_allowlist(self, key_id: str, ips: List[str]) -> bool:
        """Set IP allowlist for API key."""
        if key_id in self.api_keys:
            self.api_keys[key_id].ip_allowlist = ips
            return True
        return False
    
    def get_usage_stats(self) -> Dict:
        """Get usage statistics."""
        return self.usage_stats
    
    def get_api_usage_over_time(self, days: int = 30) -> List[Dict]:
        """Get API usage over time."""
        usage = []
        for i in range(days):
            date = (datetime.utcnow() - timedelta(days=i)).date()
            usage.append({
                'date': str(date),
                'requests': 1000 + (i * 50),  # Mock data
                'errors': 5 + (i // 5),
                'avg_latency': 150 - (i // 10),
            })
        return list(reversed(usage))
    
    def get_error_stats(self) -> Dict:
        """Get error statistics."""
        return {
            '404': 25,
            '401': 10,
            '429': 5,
            '500': 2,
        }
    
    def generate_html_dashboard(self) -> str:
        """Generate HTML dashboard."""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Developer Portal</title>
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
            background: white;
            border-bottom: 1px solid #e1e4e8;
            padding: 16px;
        }
        
        .header-content {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        h1 {
            font-size: 24px;
        }
        
        .nav {
            display: flex;
            gap: 24px;
            margin-left: auto;
        }
        
        .nav a {
            color: #586069;
            text-decoration: none;
            font-size: 14px;
        }
        
        .nav a:hover {
            color: #24292e;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 24px;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 16px;
            margin-bottom: 32px;
        }
        
        .card {
            background: white;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            padding: 16px;
        }
        
        .card-title {
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            color: #6a737d;
            margin-bottom: 8px;
        }
        
        .card-value {
            font-size: 32px;
            font-weight: 600;
            color: #0366d6;
        }
        
        .card-subtitle {
            font-size: 12px;
            color: #6a737d;
            margin-top: 8px;
        }
        
        .section {
            background: white;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            margin-bottom: 24px;
            overflow: hidden;
        }
        
        .section-header {
            padding: 16px;
            border-bottom: 1px solid #e1e4e8;
            font-weight: 600;
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
            font-size: 14px;
        }
        
        th {
            background: #f6f8fa;
            font-weight: 600;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .badge-active {
            background: #34d399;
            color: white;
        }
        
        .badge-inactive {
            background: #f3f4f6;
            color: #6b7280;
        }
        
        .badge-dev {
            background: #dbeafe;
            color: #1e40af;
        }
        
        .badge-prod {
            background: #fee2e2;
            color: #991b1b;
        }
        
        .button {
            background: #0366d6;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
        }
        
        .button:hover {
            background: #0256c7;
        }
        
        .button-secondary {
            background: #f6f8fa;
            color: #24292e;
            border: 1px solid #e1e4e8;
        }
        
        .button-secondary:hover {
            background: #e1e4e8;
        }
        
        .copy-button {
            font-family: monospace;
            font-size: 12px;
            background: #f6f8fa;
            border: 1px solid #e1e4e8;
            padding: 4px 8px;
            border-radius: 3px;
            cursor: pointer;
        }
        
        .copy-button:hover {
            background: #e1e4e8;
        }
        
        .code-block {
            background: #f6f8fa;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            padding: 12px;
            font-family: monospace;
            font-size: 12px;
            overflow-x: auto;
            margin: 12px 0;
        }
        
        .tabs {
            display: flex;
            border-bottom: 1px solid #e1e4e8;
            margin-bottom: 16px;
        }
        
        .tab {
            padding: 12px 16px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            font-size: 14px;
        }
        
        .tab.active {
            border-bottom-color: #0366d6;
            color: #0366d6;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
    </style>
</head>
<body>
    <header>
        <div class="header-content">
            <h1>🚀 Developer Portal</h1>
            <nav class="nav">
                <a href="#overview">Overview</a>
                <a href="#api-keys">API Keys</a>
                <a href="#usage">Usage</a>
                <a href="#docs">Documentation</a>
                <a href="#sdks">SDKs</a>
            </nav>
        </div>
    </header>
    
    <div class="container">
        <!-- Stats Grid -->
        <div class="grid">
            <div class="card">
                <div class="card-title">Requests Today</div>
                <div class="card-value">1,234</div>
                <div class="card-subtitle">↑ 12% from yesterday</div>
            </div>
            
            <div class="card">
                <div class="card-title">This Month</div>
                <div class="card-value">45,678</div>
                <div class="card-subtitle">15.2% of monthly quota</div>
            </div>
            
            <div class="card">
                <div class="card-title">Avg Latency</div>
                <div class="card-value">145ms</div>
                <div class="card-subtitle">↓ 5ms from yesterday</div>
            </div>
            
            <div class="card">
                <div class="card-title">Error Rate</div>
                <div class="card-value">0.2%</div>
                <div class="card-subtitle">Excellent health</div>
            </div>
        </div>
        
        <!-- API Keys Section -->
        <div class="section">
            <div class="section-header">
                API Keys
                <button class="button" style="float: right;">+ Create Key</button>
            </div>
            <div class="section-content">
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Key</th>
                            <th>Environment</th>
                            <th>Status</th>
                            <th>Created</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Production API</td>
                            <td>
                                <code>sk_prod_xxx...</code>
                                <button class="copy-button">Copy</button>
                            </td>
                            <td><span class="badge badge-prod">Production</span></td>
                            <td><span class="badge badge-active">Active</span></td>
                            <td>May 1, 2025</td>
                            <td>
                                <button class="button-secondary">Rotate</button>
                                <button class="button-secondary">Revoke</button>
                            </td>
                        </tr>
                        <tr>
                            <td>Development API</td>
                            <td>
                                <code>sk_dev_xxx...</code>
                                <button class="copy-button">Copy</button>
                            </td>
                            <td><span class="badge badge-dev">Development</span></td>
                            <td><span class="badge badge-active">Active</span></td>
                            <td>Apr 15, 2025</td>
                            <td>
                                <button class="button-secondary">Rotate</button>
                                <button class="button-secondary">Revoke</button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Usage Section -->
        <div class="section">
            <div class="section-header">API Usage</div>
            <div class="section-content">
                <div class="tabs">
                    <div class="tab active">Graph</div>
                    <div class="tab">Details</div>
                </div>
                
                <div class="tab-content active">
                    <div style="height: 200px; background: #f6f8fa; border-radius: 6px; display: flex; align-items: center; justify-content: center;">
                        📈 Usage Chart (Requests over last 30 days)
                    </div>
                </div>
                
                <div class="tab-content">
                    <table>
                        <tr>
                            <th>Endpoint</th>
                            <th>Requests</th>
                            <th>Avg Response</th>
                            <th>Errors</th>
                        </tr>
                        <tr>
                            <td>/graphql</td>
                            <td>28,400</td>
                            <td>142ms</td>
                            <td>45 (0.16%)</td>
                        </tr>
                        <tr>
                            <td>/webhook</td>
                            <td>12,300</td>
                            <td>89ms</td>
                            <td>8 (0.06%)</td>
                        </tr>
                        <tr>
                            <td>/rest/v3</td>
                            <td>4,978</td>
                            <td>156ms</td>
                            <td>2 (0.04%)</td>
                        </tr>
                    </table>
                </div>
            </div>
        </div>
        
        <!-- SDKs Section -->
        <div class="section">
            <div class="section-header">SDKs</div>
            <div class="section-content">
                <h3 style="margin-bottom: 16px;">Official SDKs</h3>
                
                <div style="margin-bottom: 24px;">
                    <strong>Python</strong>
                    <div class="code-block">pip install platform-sdk</div>
                    <a href="#" style="color: #0366d6;">View on PyPI</a> • 
                    <a href="#" style="color: #0366d6;">Documentation</a> • 
                    <a href="#" style="color: #0366d6;">GitHub</a>
                </div>
                
                <div style="margin-bottom: 24px;">
                    <strong>JavaScript/TypeScript</strong>
                    <div class="code-block">npm install @platform/sdk</div>
                    <a href="#" style="color: #0366d6;">View on npm</a> • 
                    <a href="#" style="color: #0366d6;">Documentation</a> • 
                    <a href="#" style="color: #0366d6;">GitHub</a>
                </div>
                
                <div style="margin-bottom: 24px;">
                    <strong>Go</strong>
                    <div class="code-block">go get github.com/platform/sdk-go</div>
                    <a href="#" style="color: #0366d6;">View on pkg.go.dev</a> • 
                    <a href="#" style="color: #0366d6;">Documentation</a> • 
                    <a href="#" style="color: #0366d6;">GitHub</a>
                </div>
            </div>
        </div>
        
        <!-- Resources Section -->
        <div class="section">
            <div class="section-header">Resources</div>
            <div class="section-content">
                <ul style="list-style: none;">
                    <li style="padding: 8px 0; border-bottom: 1px solid #e1e4e8;">
                        <strong>API Reference</strong> - Complete endpoint documentation
                        <a href="#" style="color: #0366d6; margin-left: 8px;">View →</a>
                    </li>
                    <li style="padding: 8px 0; border-bottom: 1px solid #e1e4e8;">
                        <strong>GraphQL Explorer</strong> - Interactive query builder
                        <a href="#" style="color: #0366d6; margin-left: 8px;">Open →</a>
                    </li>
                    <li style="padding: 8px 0; border-bottom: 1px solid #e1e4e8;">
                        <strong>Code Examples</strong> - Real-world integration examples
                        <a href="#" style="color: #0366d6; margin-left: 8px;">Browse →</a>
                    </li>
                    <li style="padding: 8px 0;">
                        <strong>Support</strong> - Get help from our team
                        <a href="#" style="color: #0366d6; margin-left: 8px;">Contact →</a>
                    </li>
                </ul>
            </div>
        </div>
    </div>
</body>
</html>
'''


class CodeSampleGenerator:
    """Generate code samples for common tasks."""
    
    @staticmethod
    def get_sample_python() -> str:
        return '''# Get Customer Example
from platform_sdk import Platform

# Initialize
sdk = Platform(api_key="sk_your_api_key")

# Get customer
customer = sdk.customers.get("customer_123")
print(f"Customer: {customer.name}, Status: {customer.status}")

# List customers
customers = sdk.customers.list(limit=10)
for c in customers:
    print(f"  - {c.name} ({c.email})")

# Create subscription
sub = sdk.subscriptions.create(
    customer_id="customer_123",
    plan_id="plan_pro"
)
print(f"Created subscription: {sub.id}")
'''
    
    @staticmethod
    def get_sample_javascript() -> str:
        return '''// Get Customer Example
const { Platform } = require('@platform/sdk');

// Initialize
const platform = new Platform("sk_your_api_key");

// Get customer
const customer = await platform.customers.get("customer_123");
console.log(`Customer: ${customer.name}, Status: ${customer.status}`);

// List customers
const customers = await platform.customers.list(10);
customers.forEach(c => {
    console.log(`  - ${c.name} (${c.email})`);
});

// Create subscription
const sub = await platform.subscriptions.create(
    "customer_123",
    "plan_pro"
);
console.log(`Created subscription: ${sub.id}`);
'''
    
    @staticmethod
    def get_sample_go() -> str:
        return '''// Get Customer Example
package main

import (
    "fmt"
    "github.com/platform/sdk-go"
)

func main() {
    // Initialize
    client := sdk.NewAPIClient("sk_your_api_key", "https://api.platform.com")
    
    // Get customer
    customer, err := client.Customers().Get("customer_123")
    if err != nil {
        panic(err)
    }
    fmt.Printf("Customer: %s\\n", customer["name"])
    
    // List customers
    customers, err := client.Customers().List(10)
    if err != nil {
        panic(err)
    }
    for _, c := range customers {
        fmt.Printf("  - %s\\n", c["name"])
    }
}
'''
