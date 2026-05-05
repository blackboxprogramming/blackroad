"""
API Explorer - Interactive GraphQL explorer with documentation
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging


class APIExplorer:
    """Interactive API explorer for GraphQL."""
    
    def __init__(self, base_url: str = "https://api.platform.com"):
        self.base_url = base_url
        self.schema = {}
        self.queries_history: List[Dict] = []
        self.favorites: Dict[str, str] = {}
        self.logger = logging.getLogger(__name__)
    
    def load_schema(self, schema: Dict) -> None:
        """Load GraphQL schema."""
        self.schema = schema
        self.logger.info("Schema loaded")
    
    def save_query(self, name: str, query: str, description: str = "") -> None:
        """Save query to favorites."""
        self.favorites[name] = {
            'query': query,
            'description': description,
            'created_at': datetime.utcnow().isoformat()
        }
        self.logger.info(f"Query saved: {name}")
    
    def get_saved_queries(self) -> Dict[str, Dict]:
        """Get saved queries."""
        return self.favorites
    
    def delete_saved_query(self, name: str) -> bool:
        """Delete saved query."""
        if name in self.favorites:
            del self.favorites[name]
            return True
        return False
    
    def get_query_history(self, limit: int = 50) -> List[Dict]:
        """Get recent query history."""
        return self.queries_history[-limit:]
    
    def clear_history(self) -> None:
        """Clear query history."""
        self.queries_history = []
    
    def add_to_history(self, query: str, variables: Dict = None,
                      result: Dict = None, execution_time: float = 0) -> None:
        """Add query to history."""
        self.queries_history.append({
            'query': query,
            'variables': variables or {},
            'result': result or {},
            'execution_time_ms': execution_time,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def generate_html_explorer(self) -> str:
        """Generate HTML explorer UI."""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Explorer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
        }
        
        .container {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            height: 100vh;
            gap: 1px;
            background: #161b22;
        }
        
        .panel {
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .panel-header {
            padding: 16px;
            border-bottom: 1px solid #30363d;
            background: #161b22;
            font-weight: 600;
        }
        
        .panel-content {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
        }
        
        .query-editor {
            font-family: 'Monaco', 'Menlo', monospace;
            background: #0d1117;
            color: #79c0ff;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 12px;
            font-size: 12px;
            resize: none;
            width: 100%;
            height: 200px;
        }
        
        .button {
            background: #238636;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 6px;
            cursor: pointer;
            margin-top: 8px;
            font-size: 12px;
        }
        
        .button:hover {
            background: #2ea043;
        }
        
        .button.secondary {
            background: #30363d;
            color: #c9d1d9;
        }
        
        .button.secondary:hover {
            background: #484f58;
        }
        
        .doc-section {
            margin-bottom: 24px;
        }
        
        .doc-title {
            font-weight: 600;
            margin-bottom: 8px;
            color: #79c0ff;
        }
        
        .doc-description {
            font-size: 12px;
            color: #8b949e;
            margin-bottom: 8px;
        }
        
        .type-badge {
            display: inline-block;
            background: #1f6feb;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
            margin-right: 4px;
        }
        
        .response {
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 12px;
            font-family: 'Monaco', monospace;
            font-size: 12px;
            max-height: 400px;
            overflow-y: auto;
            word-break: break-all;
        }
        
        .error {
            color: #f85149;
        }
        
        .success {
            color: #3fb950;
        }
        
        .history-item {
            padding: 8px;
            margin-bottom: 8px;
            background: #161b22;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }
        
        .history-item:hover {
            background: #21262d;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Schema Panel -->
        <div class="panel">
            <div class="panel-header">📚 Schema Documentation</div>
            <div class="panel-content">
                <div class="doc-section">
                    <div class="doc-title">Queries</div>
                    <div class="doc-description">
                        <span class="type-badge">Query</span>
                        customers - List all customers
                    </div>
                    <div class="doc-description">
                        <span class="type-badge">Query</span>
                        customer - Get single customer
                    </div>
                </div>
                
                <div class="doc-section">
                    <div class="doc-title">Mutations</div>
                    <div class="doc-description">
                        <span class="type-badge">Mutation</span>
                        createCustomer - Create new customer
                    </div>
                    <div class="doc-description">
                        <span class="type-badge">Mutation</span>
                        updateCustomer - Update customer
                    </div>
                </div>
                
                <div class="doc-section">
                    <div class="doc-title">Subscriptions</div>
                    <div class="doc-description">
                        <span class="type-badge">Subscription</span>
                        customerUpdated - Real-time updates
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Query Editor Panel -->
        <div class="panel">
            <div class="panel-header">✏️ Query Editor</div>
            <div class="panel-content">
                <textarea class="query-editor" placeholder="Enter GraphQL query..." id="queryInput"></textarea>
                <button class="button" onclick="executeQuery()">Execute</button>
                <button class="button secondary" onclick="clearQuery()">Clear</button>
                
                <div style="margin-top: 24px;">
                    <div class="doc-title">Templates</div>
                    <button class="button secondary" onclick="loadTemplate('listCustomers')" style="width: 100%;">
                        List Customers
                    </button>
                    <button class="button secondary" onclick="loadTemplate('getCustomer')" style="width: 100%;">
                        Get Customer
                    </button>
                </div>
            </div>
        </div>
        
        <!-- Response Panel -->
        <div class="panel">
            <div class="panel-header">📋 Response</div>
            <div class="panel-content">
                <div class="response" id="responseOutput">
                    <span class="success">Ready for queries...</span>
                </div>
                <button class="button secondary" onclick="downloadResponse()" style="width: 100%;">
                    Download Response
                </button>
            </div>
        </div>
    </div>
    
    <script>
        const templates = {
            listCustomers: `query ListCustomers {
  customers(limit: 10) {
    edges {
      node {
        id
        name
        email
        status
      }
    }
    pageInfo {
      hasNextPage
    }
  }
}`,
            getCustomer: `query GetCustomer($id: String!) {
  customer(id: $id) {
    id
    name
    email
    subscriptions {
      id
      status
    }
  }
}`
        };
        
        function loadTemplate(name) {
            document.getElementById('queryInput').value = templates[name];
        }
        
        function clearQuery() {
            document.getElementById('queryInput').value = '';
        }
        
        function executeQuery() {
            const query = document.getElementById('queryInput').value;
            const output = document.getElementById('responseOutput');
            
            if (!query.trim()) {
                output.innerHTML = '<span class="error">Query is empty</span>';
                return;
            }
            
            output.innerHTML = '<span class="success">Executing...</span>';
            
            // Mock response for demo
            setTimeout(() => {
                output.innerHTML = `<span class="success">{
  "data": {
    "customers": {
      "edges": [
        {
          "node": {
            "id": "customer_1",
            "name": "Acme Corp",
            "email": "contact@acme.com",
            "status": "active"
          }
        }
      ],
      "pageInfo": {
        "hasNextPage": false
      }
    }
  }
}</span>`;
            }, 500);
        }
        
        function downloadResponse() {
            const response = document.getElementById('responseOutput').innerText;
            const blob = new Blob([response], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'response.json';
            a.click();
        }
    </script>
</body>
</html>
'''


class APIReferenceGenerator:
    """Generate API reference documentation."""
    
    def __init__(self, schema: Dict = None):
        self.schema = schema or {}
        self.logger = logging.getLogger(__name__)
    
    def generate_markdown(self) -> str:
        """Generate Markdown reference."""
        return '''# API Reference

## Authentication

All API requests must include an `Authorization` header with a Bearer token:

```
Authorization: Bearer sk_your_api_key
```

## Endpoints

### GraphQL

**Endpoint**: `POST /graphql`

**Example**:
```bash
curl -X POST https://api.platform.com/graphql \\
  -H "Authorization: Bearer sk_your_api_key" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "{ customers { edges { node { id name } } } }"
  }'
```

## Queries

### GetCustomer

Retrieve a single customer.

**Query**:
```graphql
query GetCustomer($id: String!) {
  customer(id: $id) {
    id
    name
    email
    status
    createdAt
  }
}
```

**Variables**:
- `id` (String!, required): Customer ID

**Response**:
```json
{
  "data": {
    "customer": {
      "id": "customer_123",
      "name": "Acme Corp",
      "email": "contact@acme.com",
      "status": "active",
      "createdAt": "2025-05-04T12:00:00Z"
    }
  }
}
```

### ListCustomers

List all customers with pagination.

**Query**:
```graphql
query ListCustomers($limit: Int!, $offset: Int!) {
  customers(limit: $limit, offset: $offset) {
    edges {
      node {
        id
        name
        email
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

**Variables**:
- `limit` (Int!, required): Number of results per page
- `offset` (Int!, required): Offset for pagination

## Mutations

### CreateCustomer

Create a new customer.

**Mutation**:
```graphql
mutation CreateCustomer($name: String!, $email: String!) {
  createCustomer(input: {name: $name, email: $email}) {
    id
    name
    email
    createdAt
  }
}
```

**Variables**:
- `name` (String!, required): Customer name
- `email` (String!, required): Customer email

### UpdateCustomer

Update an existing customer.

**Mutation**:
```graphql
mutation UpdateCustomer($id: String!, $name: String!) {
  updateCustomer(input: {id: $id, name: $name}) {
    id
    name
    email
  }
}
```

## Subscriptions

### CustomerUpdated

Subscribe to real-time customer updates.

**Subscription**:
```graphql
subscription CustomerUpdated($id: String!) {
  customerUpdated(id: $id) {
    id
    name
    status
    updatedAt
  }
}
```

## Error Handling

All errors are returned in standard format:

```json
{
  "errors": [
    {
      "message": "Authentication required",
      "extensions": {
        "code": "UNAUTHENTICATED"
      }
    }
  ]
}
```

### Error Codes

- `UNAUTHENTICATED` - Missing or invalid API key
- `FORBIDDEN` - Insufficient permissions
- `NOT_FOUND` - Resource not found
- `VALIDATION_ERROR` - Input validation failed
- `RATE_LIMITED` - Rate limit exceeded
- `INTERNAL_ERROR` - Server error

## Rate Limiting

API requests are rate limited to **1,000 requests per minute** per API key.

Rate limit information is included in response headers:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1620000000
```

## Pagination

List endpoints support cursor-based pagination:

```graphql
query {
  customers(limit: 10, after: "cursor_123") {
    edges {
      node { id }
      cursor
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

## Webhooks

### Webhook Events

Your app can subscribe to the following events:

- `customer.created`
- `customer.updated`
- `subscription.created`
- `subscription.cancelled`
- `invoice.paid`

### Event Structure

```json
{
  "id": "evt_123",
  "event": "customer.created",
  "data": {
    "id": "customer_123",
    "name": "Acme Corp"
  },
  "timestamp": "2025-05-04T12:00:00Z"
}
```

Webhooks are signed with HMAC-SHA256. Verify signature in header `X-Webhook-Signature`.

## SDKs

Official SDKs are available in:
- Python: `pip install platform-sdk`
- JavaScript: `npm install @platform/sdk`
- Go: `go get github.com/platform/sdk-go`

## Support

- Documentation: https://docs.platform.com
- Status: https://status.platform.com
- Email: support@platform.com
- Slack: https://platform.slack.com/support
'''
    
    def generate_html_reference(self) -> str:
        """Generate HTML reference documentation."""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Reference</title>
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
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 250px 1fr;
            gap: 24px;
            padding: 24px;
        }
        
        .sidebar {
            position: sticky;
            top: 24px;
            height: fit-content;
        }
        
        .sidebar-section {
            margin-bottom: 24px;
        }
        
        .sidebar-title {
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            color: #6a737d;
            margin-bottom: 8px;
        }
        
        .sidebar-link {
            display: block;
            padding: 8px 12px;
            font-size: 14px;
            color: #0366d6;
            text-decoration: none;
            border-radius: 4px;
            margin-bottom: 4px;
        }
        
        .sidebar-link:hover {
            background: #f6f8fa;
        }
        
        .content {
            background: white;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            padding: 32px;
        }
        
        h1 {
            font-size: 32px;
            margin-bottom: 16px;
        }
        
        h2 {
            font-size: 24px;
            margin-top: 32px;
            margin-bottom: 16px;
            border-bottom: 1px solid #e1e4e8;
            padding-bottom: 8px;
        }
        
        h3 {
            font-size: 18px;
            margin-top: 24px;
            margin-bottom: 12px;
        }
        
        code {
            background: #f6f8fa;
            border: 1px solid #e1e4e8;
            border-radius: 3px;
            padding: 2px 4px;
            font-family: monospace;
            font-size: 14px;
        }
        
        pre {
            background: #f6f8fa;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            padding: 16px;
            margin: 16px 0;
            overflow-x: auto;
        }
        
        pre code {
            background: none;
            border: none;
            padding: 0;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
        }
        
        th, td {
            border: 1px solid #e1e4e8;
            padding: 12px;
            text-align: left;
        }
        
        th {
            background: #f6f8fa;
            font-weight: 600;
        }
        
        .param-required {
            color: #d73a49;
        }
        
        .param-type {
            color: #6f42c1;
        }
    </style>
</head>
<body>
    <header>
        <h1>Platform API Reference</h1>
        <p>Complete documentation for the Platform API</p>
    </header>
    
    <div class="container">
        <aside class="sidebar">
            <div class="sidebar-section">
                <div class="sidebar-title">Getting Started</div>
                <a href="#auth" class="sidebar-link">Authentication</a>
                <a href="#errors" class="sidebar-link">Error Handling</a>
                <a href="#rate-limit" class="sidebar-link">Rate Limiting</a>
            </div>
            
            <div class="sidebar-section">
                <div class="sidebar-title">Queries</div>
                <a href="#query-get-customer" class="sidebar-link">GetCustomer</a>
                <a href="#query-list-customers" class="sidebar-link">ListCustomers</a>
            </div>
            
            <div class="sidebar-section">
                <div class="sidebar-title">Mutations</div>
                <a href="#mutation-create-customer" class="sidebar-link">CreateCustomer</a>
                <a href="#mutation-update-customer" class="sidebar-link">UpdateCustomer</a>
            </div>
            
            <div class="sidebar-section">
                <div class="sidebar-title">Resources</div>
                <a href="#types" class="sidebar-link">Types</a>
                <a href="#webhooks" class="sidebar-link">Webhooks</a>
                <a href="#sdks" class="sidebar-link">SDKs</a>
            </div>
        </aside>
        
        <main class="content">
            <section id="auth">
                <h2>Authentication</h2>
                <p>All API requests must include an Authorization header with a Bearer token:</p>
                <pre><code>Authorization: Bearer sk_your_api_key</code></pre>
            </section>
            
            <section id="query-get-customer">
                <h2>GetCustomer</h2>
                <p>Retrieve a single customer by ID.</p>
                
                <h3>Query</h3>
                <pre><code>query GetCustomer($id: String!) {
  customer(id: $id) {
    id
    name
    email
    status
    createdAt
  }
}</code></pre>
                
                <h3>Parameters</h3>
                <table>
                    <tr>
                        <th>Name</th>
                        <th>Type</th>
                        <th>Description</th>
                    </tr>
                    <tr>
                        <td>id</td>
                        <td><span class="param-required">String!</span></td>
                        <td>Customer ID</td>
                    </tr>
                </table>
            </section>
            
            <section id="types">
                <h2>Types</h2>
                
                <h3>Customer</h3>
                <table>
                    <tr>
                        <th>Field</th>
                        <th>Type</th>
                        <th>Description</th>
                    </tr>
                    <tr>
                        <td>id</td>
                        <td><span class="param-required">String!</span></td>
                        <td>Unique identifier</td>
                    </tr>
                    <tr>
                        <td>name</td>
                        <td><span class="param-required">String!</span></td>
                        <td>Customer name</td>
                    </tr>
                    <tr>
                        <td>email</td>
                        <td><span class="param-required">String!</span></td>
                        <td>Email address</td>
                    </tr>
                    <tr>
                        <td>status</td>
                        <td><span class="param-type">String</span></td>
                        <td>active, inactive, archived</td>
                    </tr>
                </table>
            </section>
            
            <section id="sdks">
                <h2>SDKs</h2>
                <p>Official SDKs available in multiple languages:</p>
                <ul>
                    <li><strong>Python</strong>: <code>pip install platform-sdk</code></li>
                    <li><strong>JavaScript</strong>: <code>npm install @platform/sdk</code></li>
                    <li><strong>Go</strong>: <code>go get github.com/platform/sdk-go</code></li>
                </ul>
            </section>
        </main>
    </div>
</body>
</html>
'''
