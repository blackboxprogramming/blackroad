#!/usr/bin/env python3
"""
BlackRoad API Documentation Generator
Auto-generates OpenAPI/Swagger specs from Python API code
"""

import json
import inspect
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

@dataclass
class Parameter:
    """API Parameter definition"""
    name: str
    param_type: str
    required: bool = True
    description: str = ""
    example: Any = None

@dataclass
class Response:
    """API Response definition"""
    status_code: int
    description: str
    schema: Dict = None
    example: Any = None

@dataclass
class Endpoint:
    """API Endpoint definition"""
    path: str
    method: str
    summary: str
    description: str = ""
    tags: List[str] = None
    parameters: List[Parameter] = None
    request_body: Dict = None
    responses: List[Response] = None
    auth_required: bool = False

class APIDocGenerator:
    """Generates OpenAPI/Swagger documentation"""
    
    def __init__(self, title: str, version: str, base_url: str):
        self.title = title
        self.version = version
        self.base_url = base_url
        self.endpoints: List[Endpoint] = []
        self.schemas: Dict[str, Dict] = {}
    
    def add_endpoint(self, endpoint: Endpoint):
        """Add endpoint to documentation"""
        self.endpoints.append(endpoint)
    
    def add_schema(self, name: str, schema: Dict):
        """Add reusable schema"""
        self.schemas[name] = schema
    
    def generate_openapi(self) -> Dict:
        """Generate OpenAPI 3.0 specification"""
        
        paths = {}
        for endpoint in self.endpoints:
            path = endpoint.path
            if path not in paths:
                paths[path] = {}
            
            operation = {
                "summary": endpoint.summary,
                "description": endpoint.description,
                "tags": endpoint.tags or ["General"],
                "operationId": f"{endpoint.method.lower()}_{endpoint.path.replace('/', '_')}",
            }
            
            # Parameters
            if endpoint.parameters:
                operation["parameters"] = []
                for param in endpoint.parameters:
                    operation["parameters"].append({
                        "name": param.name,
                        "in": "query",
                        "required": param.required,
                        "description": param.description,
                        "schema": {"type": param.param_type},
                        "example": param.example,
                    })
            
            # Request body
            if endpoint.request_body:
                operation["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": endpoint.request_body,
                            "example": {"example": "data"},
                        }
                    }
                }
            
            # Responses
            if endpoint.responses:
                operation["responses"] = {}
                for response in endpoint.responses:
                    operation["responses"][str(response.status_code)] = {
                        "description": response.description,
                        "content": {
                            "application/json": {
                                "schema": response.schema or {"type": "object"},
                                "example": response.example,
                            }
                        }
                    }
            
            # Auth
            if endpoint.auth_required:
                operation["security"] = [{"bearerAuth": []}]
            
            paths[path][endpoint.method.lower()] = operation
        
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": self.title,
                "version": self.version,
                "description": f"API documentation for {self.title}",
                "contact": {
                    "name": "BlackRoad API Support",
                    "email": "api-support@blackroad.io",
                    "url": "https://blackroad.io",
                },
                "license": {
                    "name": "MIT",
                    "url": "https://opensource.org/licenses/MIT",
                },
            },
            "servers": [
                {
                    "url": self.base_url,
                    "description": "Production API Server",
                }
            ],
            "paths": paths,
            "components": {
                "schemas": self.schemas,
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT",
                    }
                },
            },
            "tags": self._generate_tags(),
        }
        
        return spec
    
    def _generate_tags(self) -> List[Dict]:
        """Generate tag descriptions"""
        tags = set()
        for endpoint in self.endpoints:
            if endpoint.tags:
                tags.update(endpoint.tags)
        
        return [{"name": tag, "description": f"{tag} operations"} for tag in sorted(tags)]
    
    def generate_swagger_ui_html(self) -> str:
        """Generate Swagger UI HTML"""
        return '''<!DOCTYPE html>
<html>
<head>
    <title>BlackRoad API Documentation</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/4.15.5/swagger-ui.min.css">
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: sans-serif;
        }
        .topbar {
            background: linear-gradient(to right, #2196F3, #1976D2);
            padding: 20px;
            color: white;
        }
        .topbar h1 {
            margin: 0;
            font-size: 24px;
        }
        .topbar p {
            margin: 5px 0 0 0;
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <div class="topbar">
        <h1>🚀 BlackRoad API Documentation</h1>
        <p>Complete API reference for the BlackRoad platform</p>
    </div>
    <div id="swagger-ui"></div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/4.15.5/swagger-ui.min.js"></script>
    <script>
        SwaggerUIBundle({
            url: '/api/docs/openapi.json',
            dom_id: '#swagger-ui',
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIBundle.SwaggerUIStandalonePreset
            ],
            layout: "BaseLayout",
            deepLinking: true,
            onComplete: function() {
                console.log("Swagger UI loaded successfully");
            }
        });
    </script>
</body>
</html>
'''
    
    def generate_redoc_html(self) -> str:
        """Generate ReDoc HTML (alternative documentation)"""
        return '''<!DOCTYPE html>
<html>
<head>
    <title>BlackRoad API - ReDoc</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
    <style>
        body {
            margin: 0;
            padding: 0;
        }
    </style>
</head>
<body>
    <redoc spec-url='/api/docs/openapi.json'></redoc>
    <script src="https://cdn.jsdelivr.net/npm/redoc@latest/bundles/redoc.standalone.js"></script>
</body>
</html>
'''


def create_blackroad_api_spec() -> APIDocGenerator:
    """Create complete BlackRoad API specification"""
    
    gen = APIDocGenerator(
        title="BlackRoad API",
        version="1.0.0",
        base_url="http://localhost:8000"
    )
    
    # Add schemas
    gen.add_schema("Customer", {
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "Customer ID"},
            "name": {"type": "string", "description": "Customer name"},
            "email": {"type": "string", "format": "email", "description": "Email address"},
            "tier": {"type": "string", "enum": ["free", "pro", "enterprise"]},
            "created_at": {"type": "string", "format": "date-time"},
            "updated_at": {"type": "string", "format": "date-time"},
        },
        "required": ["id", "name", "email", "tier"],
    })
    
    gen.add_schema("Subscription", {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "customer_id": {"type": "string"},
            "plan": {"type": "string"},
            "status": {"type": "string", "enum": ["active", "paused", "cancelled"]},
            "billing_cycle": {"type": "string", "enum": ["monthly", "annual"]},
            "current_period_start": {"type": "string", "format": "date-time"},
            "current_period_end": {"type": "string", "format": "date-time"},
        },
    })
    
    gen.add_schema("Transaction", {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "customer_id": {"type": "string"},
            "amount": {"type": "number"},
            "currency": {"type": "string"},
            "status": {"type": "string", "enum": ["pending", "completed", "failed"]},
            "created_at": {"type": "string", "format": "date-time"},
        },
    })
    
    gen.add_schema("Error", {
        "type": "object",
        "properties": {
            "error": {"type": "string"},
            "status": {"type": "integer"},
            "message": {"type": "string"},
            "details": {"type": "object"},
        },
    })
    
    # Customer endpoints
    gen.add_endpoint(Endpoint(
        path="/api/customers",
        method="GET",
        summary="List all customers",
        description="Retrieve a paginated list of all customers",
        tags=["Customers"],
        parameters=[
            Parameter("page", "integer", False, "Page number (0-indexed)", 0),
            Parameter("limit", "integer", False, "Items per page (max 100)", 20),
        ],
        responses=[
            Response(200, "Successful response", {
                "type": "object",
                "properties": {
                    "customers": {"type": "array", "items": {"$ref": "#/components/schemas/Customer"}},
                    "total": {"type": "integer"},
                    "page": {"type": "integer"},
                }
            }, {"customers": [], "total": 0, "page": 0}),
            Response(401, "Unauthorized"),
        ],
        auth_required=True,
    ))
    
    gen.add_endpoint(Endpoint(
        path="/api/customers",
        method="POST",
        summary="Create a new customer",
        description="Create a new customer account",
        tags=["Customers"],
        request_body={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string", "format": "email"},
                "tier": {"type": "string", "enum": ["free", "pro", "enterprise"]},
            },
            "required": ["name", "email"],
        },
        responses=[
            Response(201, "Customer created", {"$ref": "#/components/schemas/Customer"}),
            Response(400, "Invalid request"),
            Response(409, "Customer already exists"),
        ],
        auth_required=True,
    ))
    
    gen.add_endpoint(Endpoint(
        path="/api/customers/{customer_id}",
        method="GET",
        summary="Get customer by ID",
        description="Retrieve a specific customer",
        tags=["Customers"],
        parameters=[
            Parameter("customer_id", "string", True, "Customer ID"),
        ],
        responses=[
            Response(200, "Customer retrieved", {"$ref": "#/components/schemas/Customer"}),
            Response(404, "Customer not found"),
        ],
        auth_required=True,
    ))
    
    gen.add_endpoint(Endpoint(
        path="/api/customers/{customer_id}",
        method="PUT",
        summary="Update customer",
        description="Update customer information",
        tags=["Customers"],
        parameters=[
            Parameter("customer_id", "string", True, "Customer ID"),
        ],
        request_body={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "tier": {"type": "string", "enum": ["free", "pro", "enterprise"]},
            },
        },
        responses=[
            Response(200, "Customer updated", {"$ref": "#/components/schemas/Customer"}),
            Response(404, "Customer not found"),
        ],
        auth_required=True,
    ))
    
    gen.add_endpoint(Endpoint(
        path="/api/customers/{customer_id}",
        method="DELETE",
        summary="Delete customer",
        description="Delete a customer account",
        tags=["Customers"],
        parameters=[
            Parameter("customer_id", "string", True, "Customer ID"),
        ],
        responses=[
            Response(204, "Customer deleted"),
            Response(404, "Customer not found"),
        ],
        auth_required=True,
    ))
    
    # Subscription endpoints
    gen.add_endpoint(Endpoint(
        path="/api/subscriptions",
        method="POST",
        summary="Create subscription",
        description="Create a new subscription for a customer",
        tags=["Subscriptions"],
        request_body={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "plan": {"type": "string"},
                "billing_cycle": {"type": "string", "enum": ["monthly", "annual"]},
            },
            "required": ["customer_id", "plan"],
        },
        responses=[
            Response(201, "Subscription created", {"$ref": "#/components/schemas/Subscription"}),
            Response(400, "Invalid request"),
            Response(404, "Customer not found"),
        ],
        auth_required=True,
    ))
    
    gen.add_endpoint(Endpoint(
        path="/api/subscriptions/{subscription_id}",
        method="GET",
        summary="Get subscription",
        description="Retrieve subscription details",
        tags=["Subscriptions"],
        parameters=[
            Parameter("subscription_id", "string", True, "Subscription ID"),
        ],
        responses=[
            Response(200, "Subscription retrieved", {"$ref": "#/components/schemas/Subscription"}),
            Response(404, "Subscription not found"),
        ],
        auth_required=True,
    ))
    
    # Payment endpoints
    gen.add_endpoint(Endpoint(
        path="/api/payments",
        method="POST",
        summary="Process payment",
        description="Process a payment transaction",
        tags=["Payments"],
        request_body={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "amount": {"type": "number"},
                "currency": {"type": "string"},
                "source": {"type": "string"},
            },
            "required": ["customer_id", "amount", "currency"],
        },
        responses=[
            Response(200, "Payment processed", {"$ref": "#/components/schemas/Transaction"}),
            Response(400, "Invalid payment details"),
            Response(402, "Payment failed"),
        ],
        auth_required=True,
    ))
    
    # Analytics endpoints
    gen.add_endpoint(Endpoint(
        path="/api/analytics/events",
        method="POST",
        summary="Track event",
        description="Track a user event for analytics",
        tags=["Analytics"],
        request_body={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "event_type": {"type": "string"},
                "event_data": {"type": "object"},
            },
            "required": ["user_id", "event_type"],
        },
        responses=[
            Response(200, "Event tracked"),
            Response(400, "Invalid event data"),
        ],
        auth_required=False,
    ))
    
    # Health endpoint
    gen.add_endpoint(Endpoint(
        path="/health",
        method="GET",
        summary="Health check",
        description="Check if API is healthy",
        tags=["Health"],
        responses=[
            Response(200, "API is healthy", {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "timestamp": {"type": "string", "format": "date-time"},
                }
            }, {"status": "healthy"}),
        ],
        auth_required=False,
    ))
    
    return gen


if __name__ == "__main__":
    # Generate spec
    gen = create_blackroad_api_spec()
    spec = gen.generate_openapi()
    
    # Save OpenAPI spec
    with open("openapi.json", "w") as f:
        json.dump(spec, f, indent=2)
    
    print("✅ OpenAPI spec generated: openapi.json")
    print(f"📊 Endpoints: {len(gen.endpoints)}")
    print(f"📦 Schemas: {len(gen.schemas)}")
