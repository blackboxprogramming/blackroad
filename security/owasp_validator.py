"""
OWASP Top 10 Vulnerability Prevention & Detection
"""

import re
import hashlib
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import json


class SQLInjectionPreventionValidator:
    """Detect and prevent SQL injection attacks."""
    
    def __init__(self):
        # SQL injection patterns
        self.sql_patterns = [
            r"(\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE)\b)",
            r"(--|#|\/\*)",  # SQL comments
            r"('|\")\s*(OR|AND)\s*('|\")\s*=\s*('|\")",  # ' OR '='
            r"(;)\s*(DROP|DELETE|UPDATE)",  # Stacked queries
            r"(\bEXEC\(|\bEXECUTE\()",  # Stored procedure execution
        ]
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.sql_patterns]
    
    def validate(self, input_str: str) -> Tuple[bool, Optional[str]]:
        """
        Check if input contains SQL injection patterns.
        
        Returns:
            (is_safe: bool, detected_pattern: str or None)
        """
        if not input_str:
            return True, None
        
        for pattern in self.compiled_patterns:
            if pattern.search(input_str):
                matched = pattern.pattern
                return False, matched
        
        return True, None


class XSSPreventionValidator:
    """Detect and prevent Cross-Site Scripting attacks."""
    
    def __init__(self):
        self.dangerous_html_tags = [
            'script', 'iframe', 'object', 'embed', 'applet',
            'meta', 'link', 'style'
        ]
        self.dangerous_attributes = [
            'onclick', 'onload', 'onerror', 'onmouseover',
            'onkeydown', 'onkeyup', 'onchange', 'onsubmit',
            'ondblclick', 'onfocus', 'onblur'
        ]
        self.html_pattern = re.compile(
            r'<\s*(?:' + '|'.join(self.dangerous_html_tags) + r')\s*[>\/]',
            re.IGNORECASE
        )
        self.event_handler_pattern = re.compile(
            r'\b(?:' + '|'.join(self.dangerous_attributes) + r')\s*=',
            re.IGNORECASE
        )
    
    def sanitize(self, input_str: str) -> str:
        """Remove XSS payload from input."""
        # Remove dangerous tags
        sanitized = self.html_pattern.sub('', input_str)
        # Remove event handlers
        sanitized = self.event_handler_pattern.sub('', sanitized)
        return sanitized
    
    def validate(self, input_str: str) -> Tuple[bool, List[str]]:
        """
        Check if input contains XSS patterns.
        
        Returns:
            (is_safe: bool, detected_patterns: list)
        """
        issues = []
        
        if self.html_pattern.search(input_str):
            issues.append('Dangerous HTML tags detected')
        
        if self.event_handler_pattern.search(input_str):
            issues.append('Event handlers detected')
        
        if re.search(r'javascript:', input_str, re.IGNORECASE):
            issues.append('JavaScript protocol detected')
        
        if re.search(r'data:text/html', input_str, re.IGNORECASE):
            issues.append('Data URI with HTML detected')
        
        return len(issues) == 0, issues


class CSRFPreventionValidator:
    """Prevent Cross-Site Request Forgery."""
    
    def __init__(self):
        self.token_length = 32
    
    def generate_token(self, session_id: str) -> str:
        """Generate CSRF token for session."""
        data = f"{session_id}:{datetime.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def validate_token(self, token: str, session_id: str) -> bool:
        """Validate CSRF token (simplified - real implementation uses session storage)."""
        return len(token) == self.token_length * 2  # hex string is 2x length
    
    def get_headers_for_form(self, csrf_token: str) -> Dict:
        """Get headers needed for CSRF protection."""
        return {
            'X-CSRF-Token': csrf_token,
            'Content-Type': 'application/x-www-form-urlencoded'
        }


class InsecureDeserializationValidator:
    """Prevent insecure deserialization attacks."""
    
    def __init__(self):
        self.dangerous_modules = {
            'pickle', 'cPickle', 'dill', 'cloudpickle',
            'marshal', '__import__', 'eval', 'exec'
        }
    
    def validate_json(self, data: str) -> Tuple[bool, Optional[str]]:
        """Safely validate JSON data."""
        try:
            parsed = json.loads(data)
            # Additional validation could go here
            return True, None
        except json.JSONDecodeError as e:
            return False, str(e)
    
    def detect_dangerous_content(self, data: Dict) -> Tuple[bool, List[str]]:
        """Detect dangerous content in deserialized data."""
        issues = []
        
        def check_recursive(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    for dangerous in self.dangerous_modules:
                        if dangerous in str(key).lower():
                            issues.append(f"Dangerous key at {path}.{key}")
                    check_recursive(value, f"{path}.{key}")
            elif isinstance(obj, str):
                for dangerous in self.dangerous_modules:
                    if dangerous in obj.lower():
                        issues.append(f"Dangerous string at {path}")
        
        check_recursive(data)
        return len(issues) == 0, issues


class AuthenticationValidator:
    """Validate authentication security."""
    
    def __init__(self):
        self.min_password_length = 12
    
    def validate_password(self, password: str) -> Tuple[bool, List[str]]:
        """
        Validate password strength.
        
        Returns:
            (is_valid: bool, issues: list)
        """
        issues = []
        
        if len(password) < self.min_password_length:
            issues.append(f'Password too short (min: {self.min_password_length})')
        
        if not re.search(r'[A-Z]', password):
            issues.append('Missing uppercase letters')
        
        if not re.search(r'[a-z]', password):
            issues.append('Missing lowercase letters')
        
        if not re.search(r'[0-9]', password):
            issues.append('Missing numbers')
        
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:,.<>?]', password):
            issues.append('Missing special characters')
        
        return len(issues) == 0, issues


class OWASPValidator:
    """Combined validator for OWASP Top 10."""
    
    def __init__(self):
        self.sql_validator = SQLInjectionPreventionValidator()
        self.xss_validator = XSSPreventionValidator()
        self.csrf_validator = CSRFPreventionValidator()
        self.deserialization_validator = InsecureDeserializationValidator()
        self.auth_validator = AuthenticationValidator()
    
    def validate_request(self, data: Dict) -> Dict:
        """
        Comprehensive request validation.
        
        Returns:
            {
                'valid': bool,
                'vulnerabilities': list,
                'details': {
                    'sql_injection': ...,
                    'xss': ...,
                    'issues': [...]
                }
            }
        """
        vulnerabilities = []
        details = {}
        
        # Check each field for SQL injection
        for key, value in data.items():
            if isinstance(value, str):
                safe, pattern = self.sql_validator.validate(value)
                if not safe:
                    vulnerabilities.append(f'SQL Injection in {key}')
                    details.setdefault('sql_injection', []).append({
                        'field': key,
                        'pattern': pattern
                    })
                
                # Check for XSS
                safe, xss_issues = self.xss_validator.validate(value)
                if not safe:
                    vulnerabilities.append(f'XSS in {key}')
                    details.setdefault('xss', []).append({
                        'field': key,
                        'issues': xss_issues
                    })
        
        return {
            'valid': len(vulnerabilities) == 0,
            'vulnerabilities': vulnerabilities,
            'details': details,
            'checked_fields': len(data)
        }
