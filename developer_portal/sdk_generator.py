"""
SDK Generator - Auto-generate SDKs for Python, JavaScript, and Go
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging


class SDKLanguage:
    """Base SDK language template."""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.logger = logging.getLogger(__name__)
    
    def generate_client_class(self, schema: Dict) -> str:
        """Generate main client class."""
        raise NotImplementedError
    
    def generate_types(self, schema: Dict) -> str:
        """Generate type definitions."""
        raise NotImplementedError
    
    def generate_auth(self) -> str:
        """Generate authentication handler."""
        raise NotImplementedError


class PythonSDK(SDKLanguage):
    """Python SDK generator."""
    
    def generate_client_class(self, schema: Dict) -> str:
        """Generate Python client."""
        return '''"""Auto-generated SDK for Platform API."""

import httpx
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import asyncio


class APIClient:
    """Main API client."""
    
    def __init__(self, api_key: str, base_url: str = "https://api.platform.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.Client(timeout=30.0)
        self.async_client = httpx.AsyncClient(timeout=30.0)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "SDK/1.0.0",
        }
    
    def query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Execute GraphQL query."""
        headers = self._get_headers()
        headers["X-Client-Version"] = "python-1.0.0"
        
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        response = self.client.post(
            f"{self.base_url}/graphql",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    
    async def query_async(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Execute GraphQL query asynchronously."""
        headers = self._get_headers()
        headers["X-Client-Version"] = "python-1.0.0"
        
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        response = await self.async_client.post(
            f"{self.base_url}/graphql",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    
    def rest_get(self, path: str, params: Optional[Dict] = None) -> Dict:
        """Execute GET request."""
        response = self.client.get(
            f"{self.base_url}{path}",
            params=params,
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    def rest_post(self, path: str, data: Dict) -> Dict:
        """Execute POST request."""
        response = self.client.post(
            f"{self.base_url}{path}",
            json=data,
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    def close(self):
        """Close client."""
        self.client.close()


class Customers:
    """Customer operations."""
    
    def __init__(self, client: APIClient):
        self.client = client
    
    def get(self, customer_id: str) -> Dict:
        """Get customer by ID."""
        query = """
        query GetCustomer($id: String!) {
            customer(id: $id) {
                id
                name
                email
                status
                createdAt
            }
        }
        """
        result = self.client.query(query, {"id": customer_id})
        return result.get("data", {}).get("customer")
    
    def list(self, limit: int = 10, offset: int = 0) -> List[Dict]:
        """List customers."""
        query = """
        query ListCustomers($limit: Int!, $offset: Int!) {
            customers(limit: $limit, offset: $offset) {
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
                    endCursor
                }
            }
        }
        """
        result = self.client.query(query, {"limit": limit, "offset": offset})
        return result.get("data", {}).get("customers", {}).get("edges", [])
    
    def create(self, name: str, email: str) -> Dict:
        """Create customer."""
        query = """
        mutation CreateCustomer($name: String!, $email: String!) {
            createCustomer(input: {name: $name, email: $email}) {
                id
                name
                email
                createdAt
            }
        }
        """
        result = self.client.query(query, {"name": name, "email": email})
        return result.get("data", {}).get("createCustomer")


class Subscriptions:
    """Subscription operations."""
    
    def __init__(self, client: APIClient):
        self.client = client
    
    def create(self, customer_id: str, plan_id: str) -> Dict:
        """Create subscription."""
        query = """
        mutation CreateSubscription($customerId: String!, $planId: String!) {
            createSubscription(input: {customerId: $customerId, planId: $planId}) {
                id
                customerId
                planId
                status
                startDate
                renewalDate
            }
        }
        """
        result = self.client.query(query, {"customerId": customer_id, "planId": plan_id})
        return result.get("data", {}).get("createSubscription")
    
    def cancel(self, subscription_id: str, reason: str = None) -> Dict:
        """Cancel subscription."""
        query = """
        mutation CancelSubscription($id: String!, $reason: String) {
            cancelSubscription(input: {id: $id, reason: $reason}) {
                id
                status
                cancelledAt
            }
        }
        """
        result = self.client.query(query, {"id": subscription_id, "reason": reason})
        return result.get("data", {}).get("cancelSubscription")


class Platform:
    """Main Platform SDK."""
    
    def __init__(self, api_key: str, base_url: str = "https://api.platform.com"):
        self.client = APIClient(api_key, base_url)
        self.customers = Customers(self.client)
        self.subscriptions = Subscriptions(self.client)
    
    def close(self):
        """Close SDK."""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
'''
    
    def generate_types(self, schema: Dict) -> str:
        """Generate Python types."""
        return '''"""Type definitions for Platform API."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class Customer:
    """Customer type."""
    id: str
    name: str
    email: str
    status: str
    createdAt: datetime
    updatedAt: Optional[datetime] = None
    deletedAt: Optional[datetime] = None


@dataclass
class Subscription:
    """Subscription type."""
    id: str
    customerId: str
    planId: str
    status: str
    amount: float
    currency: str
    startDate: datetime
    renewalDate: datetime
    cancelledAt: Optional[datetime] = None


@dataclass
class Invoice:
    """Invoice type."""
    id: str
    customerId: str
    amount: float
    currency: str
    status: str
    issuedAt: datetime
    dueAt: datetime
    paidAt: Optional[datetime] = None


@dataclass
class PageInfo:
    """Pagination info."""
    hasNextPage: bool
    endCursor: Optional[str]
    startCursor: Optional[str]
    hasPreviousPage: bool
'''
    
    def generate_auth(self) -> str:
        """Generate Python auth."""
        return '''"""Authentication helpers."""

import jwt
from datetime import datetime, timedelta


class TokenManager:
    """Manage API tokens."""
    
    def __init__(self, api_key: str, secret: str):
        self.api_key = api_key
        self.secret = secret
    
    def generate_token(self, user_id: str, expires_in: int = 3600) -> str:
        """Generate JWT token."""
        payload = {
            "user_id": user_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(seconds=expires_in)
        }
        return jwt.encode(payload, self.secret, algorithm="HS256")
    
    def verify_token(self, token: str) -> dict:
        """Verify JWT token."""
        return jwt.decode(token, self.secret, algorithms=["HS256"])
'''


class JavaScriptSDK(SDKLanguage):
    """JavaScript SDK generator."""
    
    def generate_client_class(self, schema: Dict) -> str:
        """Generate JavaScript client."""
        return '''/**
 * Auto-generated SDK for Platform API
 */

class APIClient {
    constructor(apiKey, baseUrl = "https://api.platform.com") {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
        this.timeout = 30000;
    }
    
    getHeaders() {
        return {
            "Authorization": `Bearer ${this.apiKey}`,
            "Content-Type": "application/json",
            "User-Agent": "SDK/1.0.0",
            "X-Client-Version": "js-1.0.0"
        };
    }
    
    async query(query, variables = {}) {
        const response = await fetch(`${this.baseUrl}/graphql`, {
            method: "POST",
            headers: this.getHeaders(),
            body: JSON.stringify({ query, variables }),
            timeout: this.timeout
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return response.json();
    }
    
    async rest(method, path, data = null) {
        const options = {
            method,
            headers: this.getHeaders(),
            timeout: this.timeout
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(`${this.baseUrl}${path}`, options);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return response.json();
    }
}

class Customers {
    constructor(client) {
        this.client = client;
    }
    
    async get(customerId) {
        const query = `
            query GetCustomer($id: String!) {
                customer(id: $id) {
                    id
                    name
                    email
                    status
                    createdAt
                }
            }
        `;
        
        const result = await this.client.query(query, { id: customerId });
        return result.data?.customer;
    }
    
    async list(limit = 10, offset = 0) {
        const query = `
            query ListCustomers($limit: Int!, $offset: Int!) {
                customers(limit: $limit, offset: $offset) {
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
                        endCursor
                    }
                }
            }
        `;
        
        const result = await this.client.query(query, { limit, offset });
        return result.data?.customers?.edges || [];
    }
    
    async create(name, email) {
        const query = `
            mutation CreateCustomer($name: String!, $email: String!) {
                createCustomer(input: {name: $name, email: $email}) {
                    id
                    name
                    email
                    createdAt
                }
            }
        `;
        
        const result = await this.client.query(query, { name, email });
        return result.data?.createCustomer;
    }
}

class Platform {
    constructor(apiKey, baseUrl = "https://api.platform.com") {
        this.client = new APIClient(apiKey, baseUrl);
        this.customers = new Customers(this.client);
    }
}

module.exports = { Platform, APIClient, Customers };
'''
    
    def generate_types(self, schema: Dict) -> str:
        """Generate TypeScript types."""
        return '''/**
 * TypeScript type definitions
 */

export interface Customer {
    id: string;
    name: string;
    email: string;
    status: string;
    createdAt: Date;
    updatedAt?: Date;
    deletedAt?: Date;
}

export interface Subscription {
    id: string;
    customerId: string;
    planId: string;
    status: string;
    amount: number;
    currency: string;
    startDate: Date;
    renewalDate: Date;
    cancelledAt?: Date;
}

export interface Invoice {
    id: string;
    customerId: string;
    amount: number;
    currency: string;
    status: string;
    issuedAt: Date;
    dueAt: Date;
    paidAt?: Date;
}

export interface PageInfo {
    hasNextPage: boolean;
    endCursor?: string;
    startCursor?: string;
    hasPreviousPage: boolean;
}
'''


class GoSDK(SDKLanguage):
    """Go SDK generator."""
    
    def generate_client_class(self, schema: Dict) -> str:
        """Generate Go client."""
        return '''package sdk

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type APIClient struct {
	APIKey  string
	BaseURL string
	Client  *http.Client
}

type GraphQLRequest struct {
	Query     string                 `json:"query"`
	Variables map[string]interface{} `json:"variables"`
}

type GraphQLResponse struct {
	Data   map[string]interface{} `json:"data"`
	Errors []map[string]interface{} `json:"errors"`
}

func NewAPIClient(apiKey, baseURL string) *APIClient {
	return &APIClient{
		APIKey:  apiKey,
		BaseURL: baseURL,
		Client: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

func (c *APIClient) getHeaders() map[string]string {
	return map[string]string{
		"Authorization":     fmt.Sprintf("Bearer %s", c.APIKey),
		"Content-Type":      "application/json",
		"User-Agent":        "SDK/1.0.0",
		"X-Client-Version":  "go-1.0.0",
	}
}

func (c *APIClient) Query(query string, variables map[string]interface{}) (*GraphQLResponse, error) {
	req := GraphQLRequest{
		Query:     query,
		Variables: variables,
	}
	
	body, err := json.Marshal(req)
	if err != nil {
		return nil, err
	}
	
	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/graphql", c.BaseURL), bytes.NewBuffer(body))
	if err != nil {
		return nil, err
	}
	
	for k, v := range c.getHeaders() {
		httpReq.Header.Set(k, v)
	}
	
	resp, err := c.Client.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("HTTP %d", resp.StatusCode)
	}
	
	var gqlResp GraphQLResponse
	if err := json.NewDecoder(resp.Body).Decode(&gqlResp); err != nil {
		return nil, err
	}
	
	return &gqlResp, nil
}

type CustomersAPI struct {
	client *APIClient
}

func (c *APIClient) Customers() *CustomersAPI {
	return &CustomersAPI{client: c}
}

func (ca *CustomersAPI) Get(customerID string) (map[string]interface{}, error) {
	query := `
		query GetCustomer($id: String!) {
			customer(id: $id) {
				id
				name
				email
				status
				createdAt
			}
		}
	`
	
	result, err := ca.client.Query(query, map[string]interface{}{"id": customerID})
	if err != nil {
		return nil, err
	}
	
	if data, ok := result.Data["customer"].(map[string]interface{}); ok {
		return data, nil
	}
	
	return nil, fmt.Errorf("customer not found")
}
'''
    
    def generate_types(self, schema: Dict) -> str:
        """Generate Go types."""
        return '''package sdk

import "time"

type Customer struct {
	ID        string     `json:"id"`
	Name      string     `json:"name"`
	Email     string     `json:"email"`
	Status    string     `json:"status"`
	CreatedAt time.Time  `json:"createdAt"`
	UpdatedAt *time.Time `json:"updatedAt,omitempty"`
	DeletedAt *time.Time `json:"deletedAt,omitempty"`
}

type Subscription struct {
	ID          string     `json:"id"`
	CustomerID  string     `json:"customerId"`
	PlanID      string     `json:"planId"`
	Status      string     `json:"status"`
	Amount      float64    `json:"amount"`
	Currency    string     `json:"currency"`
	StartDate   time.Time  `json:"startDate"`
	RenewalDate time.Time  `json:"renewalDate"`
	CancelledAt *time.Time `json:"cancelledAt,omitempty"`
}

type Invoice struct {
	ID         string     `json:"id"`
	CustomerID string     `json:"customerId"`
	Amount     float64    `json:"amount"`
	Currency   string     `json:"currency"`
	Status     string     `json:"status"`
	IssuedAt   time.Time  `json:"issuedAt"`
	DueAt      time.Time  `json:"dueAt"`
	PaidAt     *time.Time `json:"paidAt,omitempty"`
}

type PageInfo struct {
	HasNextPage   bool   `json:"hasNextPage"`
	EndCursor     string `json:"endCursor,omitempty"`
	StartCursor   string `json:"startCursor,omitempty"`
	HasPreviousPage bool `json:"hasPreviousPage"`
}
'''


class SDKGenerator:
    """Main SDK generator."""
    
    def __init__(self):
        self.languages = {
            'python': PythonSDK('python'),
            'javascript': JavaScriptSDK('javascript'),
            'go': GoSDK('go'),
        }
        self.logger = logging.getLogger(__name__)
    
    def generate(self, language: str, output_dir: str, 
                schema: Dict = None) -> Dict:
        """Generate SDK for language."""
        if language not in self.languages:
            raise ValueError(f"Unsupported language: {language}")
        
        sdk = self.languages[language]
        
        # Generate components
        client_code = sdk.generate_client_class(schema or {})
        types_code = sdk.generate_types(schema or {})
        auth_code = sdk.generate_auth()
        
        result = {
            'language': language,
            'files': {
                'client': client_code,
                'types': types_code,
                'auth': auth_code,
            },
            'generated_at': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        }
        
        self.logger.info(f"Generated {language} SDK")
        return result
    
    def generate_all(self, output_dir: str, 
                    schema: Dict = None) -> Dict:
        """Generate SDKs for all languages."""
        results = {}
        for language in self.languages.keys():
            results[language] = self.generate(language, output_dir, schema)
        
        return results
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return list(self.languages.keys())
    
    def generate_requirements(self, language: str) -> str:
        """Generate requirements for SDK."""
        requirements = {
            'python': '''httpx==0.24.0
pydantic==2.0.0
pyjwt==2.8.0
python-dateutil==2.8.2
''',
            'javascript': '''graphql-request@^5.0.0
graphql@^16.0.0
axios@^1.4.0
jose@^4.0.0
''',
            'go': '''github.com/google/uuid v1.3.0
github.com/golang-jwt/jwt/v5 v5.0.0
''',
        }
        
        return requirements.get(language, '')
    
    def generate_examples(self, language: str) -> str:
        """Generate usage examples."""
        if language == 'python':
            return '''
# Python SDK Example
from platform_sdk import Platform

# Initialize SDK
platform = Platform(api_key="sk_your_api_key")

# Get customer
customer = platform.customers.get("customer_123")
print(f"Customer: {customer.name}")

# List customers
customers = platform.customers.list(limit=10)
for c in customers:
    print(c)

# Create subscription
sub = platform.subscriptions.create(
    customer_id="customer_123",
    plan_id="plan_pro"
)
print(f"Subscription: {sub.id}")

# Cancel subscription
cancelled = platform.subscriptions.cancel("subscription_456")
'''
        elif language == 'javascript':
            return '''
// JavaScript SDK Example
const { Platform } = require('platform-sdk');

// Initialize SDK
const platform = new Platform("sk_your_api_key");

// Get customer
const customer = await platform.customers.get("customer_123");
console.log(`Customer: ${customer.name}`);

// List customers
const customers = await platform.customers.list(10, 0);
customers.forEach(c => console.log(c));

// Create subscription
const sub = await platform.subscriptions.create(
    "customer_123",
    "plan_pro"
);
console.log(`Subscription: ${sub.id}`);
'''
        elif language == 'go':
            return '''
// Go SDK Example
package main

import (
    "fmt"
    "github.com/platform/sdk-go"
)

func main() {
    // Initialize SDK
    client := sdk.NewAPIClient("sk_your_api_key", "https://api.platform.com")
    
    // Get customer
    customer, err := client.Customers().Get("customer_123")
    if err != nil {
        panic(err)
    }
    fmt.Printf("Customer: %v\\n", customer)
}
'''
        
        return ''
