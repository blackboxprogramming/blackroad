# 📚 API DOCUMENTATION GENERATOR

## Quick Start

```bash
# Generate OpenAPI spec
python3 api_docs/generator.py

# Access interactive documentation
open http://localhost:8000/api/docs/swagger

# Or with ReDoc
open http://localhost:8000/api/docs/redoc
```

## Generated Files

- `openapi.json` - Full OpenAPI 3.0 specification
- `swagger-ui.html` - Interactive API explorer
- `redoc.html` - Alternative documentation view

## Endpoints Documented

- Customers (CRUD)
- Subscriptions (manage plans)
- Payments (process transactions)
- Analytics (track events)
- Health checks

All endpoints fully documented with:
- Request/response schemas
- Authentication requirements
- Example usage
- Error codes
- Parameter descriptions

✅ Status: Production Ready
