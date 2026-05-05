"""
Security Headers Middleware - Implements OWASP security headers
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json


class SecurityHeadersMiddleware:
    """
    Implements comprehensive security headers for protecting against
    common web vulnerabilities (OWASP Top 10).
    """
    
    def __init__(self, environment: str = 'production'):
        self.environment = environment
        self.headers = self._build_headers()
    
    def _build_headers(self) -> Dict[str, str]:
        """Build security headers based on environment."""
        headers = {
            # HSTS - Force HTTPS for 2 years
            'Strict-Transport-Security': 'max-age=63072000; includeSubDomains; preload',
            
            # Content Security Policy - Prevent XSS, inline scripts
            'Content-Security-Policy': (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "img-src 'self' data: https:; "
                "font-src 'self' https://fonts.gstatic.com; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            ),
            
            # Prevent clickjacking
            'X-Frame-Options': 'DENY',
            
            # Prevent MIME type sniffing
            'X-Content-Type-Options': 'nosniff',
            
            # Enable XSS filter in older browsers
            'X-XSS-Protection': '1; mode=block',
            
            # Referrer Policy - Control referrer information
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            
            # Feature Policy - Disable unused browser features
            'Permissions-Policy': (
                'accelerometer=(), camera=(), geolocation=(), '
                'gyroscope=(), magnetometer=(), microphone=(), '
                'payment=(), usb=()'
            ),
            
            # Prevent caching of sensitive data
            'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
            
            # Remove server identification
            'Server': 'Blackroad/1.0',
            
            # CORS headers (can be overridden per route)
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-API-Key',
        }
        
        if self.environment == 'production':
            # Stricter CSP in production
            headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' https://cdn.jsdelivr.net; "
                "style-src 'self' https://fonts.googleapis.com; "
                "img-src 'self' data: https:; "
                "font-src 'self' https://fonts.gstatic.com; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "upgrade-insecure-requests"
            )
        
        return headers
    
    def get_headers(self, endpoint: str = None, 
                   cors_origin: str = None) -> Dict[str, str]:
        """
        Get security headers, optionally customized for endpoint.
        
        Args:
            endpoint: API endpoint (for custom CSP)
            cors_origin: Allowed CORS origin
        
        Returns:
            Dictionary of security headers
        """
        headers = self.headers.copy()
        
        # Customize CORS
        if cors_origin:
            headers['Access-Control-Allow-Origin'] = cors_origin
        else:
            headers.pop('Access-Control-Allow-Origin', None)
        
        # Endpoint-specific CSP customization
        if endpoint and endpoint.startswith('/api/'):
            # API endpoints get stricter CSP
            headers['Content-Security-Policy'] = (
                "default-src 'none'; "
                "script-src 'self'; "
                "connect-src 'self'"
            )
        
        return headers
    
    def apply_headers(self, response_headers: Dict) -> Dict:
        """Apply security headers to response."""
        response_headers.update(self.get_headers())
        return response_headers


class CSPBuilder:
    """Build custom Content Security Policy headers."""
    
    def __init__(self):
        self.directives = {}
    
    def allow_domain(self, directive: str, domain: str) -> 'CSPBuilder':
        """Allow content from specific domain for directive."""
        if directive not in self.directives:
            self.directives[directive] = []
        self.directives[directive].append(domain)
        return self
    
    def disallow_unsafe_inline(self) -> 'CSPBuilder':
        """Disable unsafe-inline for all directives."""
        for key in self.directives:
            if 'unsafe-inline' in self.directives[key]:
                self.directives[key].remove('unsafe-inline')
        return self
    
    def build(self) -> str:
        """Build CSP header string."""
        csp_parts = []
        for directive, sources in self.directives.items():
            csp_parts.append(f"{directive} {' '.join(sources)}")
        return '; '.join(csp_parts)


class SecurityHeaderValidator:
    """Validate responses have proper security headers."""
    
    def __init__(self):
        self.required_headers = {
            'Strict-Transport-Security',
            'X-Frame-Options',
            'X-Content-Type-Options',
            'Content-Security-Policy',
        }
    
    def validate(self, response_headers: Dict) -> Dict:
        """
        Validate response headers.
        
        Returns:
            {
                'valid': bool,
                'missing_headers': list,
                'warnings': list,
                'issues': list
            }
        """
        missing = []
        warnings = []
        issues = []
        
        # Check for required headers
        for header in self.required_headers:
            if header not in response_headers:
                missing.append(header)
        
        # Validate header values
        hsts = response_headers.get('Strict-Transport-Security', '')
        if hsts and 'max-age' in hsts:
            max_age = int(hsts.split('max-age=')[1].split(';')[0])
            if max_age < 31536000:  # 1 year
                warnings.append(f'HSTS max-age is low: {max_age}s (recommended: 63072000s)')
        
        csp = response_headers.get('Content-Security-Policy', '')
        if 'unsafe-inline' in csp:
            issues.append('CSP contains unsafe-inline (XSS vulnerability)')
        
        if "default-src 'none'" not in csp and "default-src 'self'" not in csp:
            warnings.append('CSP default-src not restrictive enough')
        
        # Check for server info leakage
        server = response_headers.get('Server', '')
        if 'Apache' in server or 'nginx' in server:
            issues.append(f'Server header leaks version info: {server}')
        
        return {
            'valid': len(missing) == 0 and len(issues) == 0,
            'missing_headers': missing,
            'warnings': warnings,
            'issues': issues,
            'headers_checked': len(response_headers)
        }
