"""
Intelligent API Gateway
Request routing, rate limiting, circuit breaking for all systems
"""

from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import time


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


class RouteType(Enum):
    """Route types for different systems."""
    SECURITY = "/api/v1/security"
    DEPLOYMENT = "/api/v1/deployment"
    API_CORE = "/api/v1/core"
    DEVELOPER = "/api/v1/developer"
    MONITORING = "/api/v1/monitoring"
    ML = "/api/v1/ml"
    COMPLIANCE = "/api/v1/compliance"


class APIRequest:
    """Unified API request object."""
    
    def __init__(self, method: str, path: str, headers: Dict, body: Optional[Dict] = None):
        self.id = f"req_{int(time.time() * 1000)}"
        self.method = method
        self.path = path
        self.headers = headers
        self.body = body or {}
        self.timestamp = datetime.utcnow().isoformat()
        self.user_id = headers.get('X-User-ID')
        self.correlation_id = headers.get('X-Correlation-ID', self.id)


class APIResponse:
    """Unified API response object."""
    
    def __init__(self, status_code: int, data: Dict, headers: Optional[Dict] = None):
        self.status_code = status_code
        self.data = data
        self.headers = headers or {}
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict:
        """Export response."""
        return {
            'status_code': self.status_code,
            'data': self.data,
            'timestamp': self.timestamp,
        }


class RateLimiter:
    """Rate limiting with token bucket algorithm."""
    
    def __init__(self, requests_per_second: float = 100):
        self.requests_per_second = requests_per_second
        self.buckets: Dict[str, Dict] = {}
    
    def is_allowed(self, user_id: str) -> bool:
        """Check if request is allowed."""
        now = time.time()
        
        if user_id not in self.buckets:
            self.buckets[user_id] = {
                'tokens': self.requests_per_second,
                'last_refill': now,
            }
        
        bucket = self.buckets[user_id]
        
        # Refill tokens
        time_elapsed = now - bucket['last_refill']
        tokens_to_add = time_elapsed * self.requests_per_second
        bucket['tokens'] = min(self.requests_per_second, bucket['tokens'] + tokens_to_add)
        bucket['last_refill'] = now
        
        if bucket['tokens'] >= 1:
            bucket['tokens'] -= 1
            return True
        
        return False
    
    def get_status(self, user_id: str) -> Dict:
        """Get rate limit status."""
        bucket = self.buckets.get(user_id, {})
        return {
            'tokens_remaining': bucket.get('tokens', 0),
            'requests_per_second': self.requests_per_second,
        }


class CircuitBreaker:
    """Circuit breaker for service health."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.services: Dict[str, Dict] = {}
    
    def record_success(self, service: str) -> None:
        """Record successful request."""
        if service not in self.services:
            self.services[service] = {
                'state': CircuitBreakerState.CLOSED.value,
                'failures': 0,
                'last_failure_time': None,
            }
        
        svc = self.services[service]
        svc['failures'] = 0
        svc['state'] = CircuitBreakerState.CLOSED.value
    
    def record_failure(self, service: str) -> None:
        """Record failed request."""
        if service not in self.services:
            self.services[service] = {
                'state': CircuitBreakerState.CLOSED.value,
                'failures': 0,
                'last_failure_time': None,
            }
        
        svc = self.services[service]
        svc['failures'] += 1
        svc['last_failure_time'] = datetime.utcnow().isoformat()
        
        if svc['failures'] >= self.failure_threshold:
            svc['state'] = CircuitBreakerState.OPEN.value
    
    def can_execute(self, service: str) -> bool:
        """Check if request can be executed."""
        if service not in self.services:
            return True
        
        svc = self.services[service]
        
        if svc['state'] == CircuitBreakerState.CLOSED.value:
            return True
        
        if svc['state'] == CircuitBreakerState.OPEN.value:
            # Check if timeout expired
            last_failure = datetime.fromisoformat(svc['last_failure_time'])
            if (datetime.utcnow() - last_failure).seconds > self.recovery_timeout:
                svc['state'] = CircuitBreakerState.HALF_OPEN.value
                return True
            
            return False
        
        # HALF_OPEN - allow single test request
        return True
    
    def get_status(self, service: str) -> Dict:
        """Get circuit breaker status."""
        svc = self.services.get(service, {
            'state': CircuitBreakerState.CLOSED.value,
            'failures': 0,
        })
        
        return {
            'service': service,
            'state': svc['state'],
            'failures': svc['failures'],
            'last_failure': svc.get('last_failure_time'),
        }


class RequestValidator:
    """Validate cross-system requests."""
    
    @staticmethod
    def validate_headers(headers: Dict) -> tuple[bool, Optional[str]]:
        """Validate required headers."""
        required = ['X-User-ID', 'Authorization']
        
        for header in required:
            if header not in headers:
                return False, f"Missing required header: {header}"
        
        return True, None
    
    @staticmethod
    def validate_body(body: Dict, schema: Dict) -> tuple[bool, Optional[str]]:
        """Validate request body against schema."""
        for field, field_type in schema.items():
            if field not in body:
                return False, f"Missing required field: {field}"
            
            if not isinstance(body[field], field_type):
                return False, f"Invalid type for field {field}"
        
        return True, None


class APIGateway:
    """Central API gateway for all systems."""
    
    def __init__(self, rate_limiter: RateLimiter, circuit_breaker: CircuitBreaker):
        self.rate_limiter = rate_limiter
        self.circuit_breaker = circuit_breaker
        self.routes: Dict[str, Callable] = {}
        self.request_log: List[Dict] = []
        self.middlewares: List[Callable] = []
    
    def register_route(self, path: str, handler: Callable) -> None:
        """Register route handler."""
        self.routes[path] = handler
    
    def add_middleware(self, middleware: Callable) -> None:
        """Add middleware."""
        self.middlewares.append(middleware)
    
    def handle_request(self, request: APIRequest) -> APIResponse:
        """Handle incoming request."""
        
        # Validate headers
        valid, error = RequestValidator.validate_headers(request.headers)
        if not valid:
            return APIResponse(400, {'error': error})
        
        # Check rate limit
        if not self.rate_limiter.is_allowed(request.user_id):
            return APIResponse(429, {
                'error': 'Rate limit exceeded',
                'limit': self.rate_limiter.requests_per_second
            })
        
        # Find route
        handler = None
        for route_path, route_handler in self.routes.items():
            if request.path.startswith(route_path):
                handler = route_handler
                break
        
        if not handler:
            return APIResponse(404, {'error': 'Route not found'})
        
        # Get service name from route
        service = request.path.split('/')[3] if len(request.path.split('/')) > 3 else 'unknown'
        
        # Check circuit breaker
        if not self.circuit_breaker.can_execute(service):
            return APIResponse(503, {
                'error': f'Service {service} is currently unavailable',
                'status': self.circuit_breaker.get_status(service)
            })
        
        try:
            # Apply middlewares
            for middleware in self.middlewares:
                request = middleware(request)
            
            # Execute handler
            result = handler(request)
            
            # Record success
            self.circuit_breaker.record_success(service)
            
            response = APIResponse(200, result)
            
        except Exception as e:
            # Record failure
            self.circuit_breaker.record_failure(service)
            
            response = APIResponse(500, {'error': str(e)})
        
        # Log request
        self.request_log.append({
            'request_id': request.id,
            'path': request.path,
            'method': request.method,
            'status_code': response.status_code,
            'user_id': request.user_id,
            'timestamp': datetime.utcnow().isoformat(),
        })
        
        return response
    
    def get_metrics(self) -> Dict:
        """Get gateway metrics."""
        total_requests = len(self.request_log)
        success_requests = sum(1 for r in self.request_log if r['status_code'] == 200)
        error_requests = sum(1 for r in self.request_log if r['status_code'] >= 400)
        
        return {
            'total_requests': total_requests,
            'successful_requests': success_requests,
            'failed_requests': error_requests,
            'success_rate': (success_requests / total_requests * 100) if total_requests > 0 else 0,
            'circuit_breakers': {
                service: self.circuit_breaker.get_status(service)
                for service in self.circuit_breaker.services.keys()
            }
        }


class GatewayOrchestrator:
    """Orchestrate requests across all systems."""
    
    def __init__(self, gateway: APIGateway):
        self.gateway = gateway
        self.dependencies: Dict[str, List[str]] = {}
    
    def register_dependency(self, service: str, depends_on: List[str]) -> None:
        """Register service dependencies."""
        self.dependencies[service] = depends_on
    
    def can_serve_request(self, service: str) -> bool:
        """Check if service can serve requests."""
        if service not in self.dependencies:
            return True
        
        # Check all dependencies
        for dep_service in self.dependencies[service]:
            if not self.gateway.circuit_breaker.can_execute(dep_service):
                return False
        
        return True
    
    def get_service_dependency_status(self) -> Dict:
        """Get status of all service dependencies."""
        status = {}
        
        for service, deps in self.dependencies.items():
            all_healthy = all(
                self.gateway.circuit_breaker.get_status(dep)['state'] == CircuitBreakerState.CLOSED.value
                for dep in deps
            )
            
            status[service] = {
                'can_serve': all_healthy,
                'dependencies': deps,
                'dependency_health': {
                    dep: self.gateway.circuit_breaker.get_status(dep)
                    for dep in deps
                }
            }
        
        return status
