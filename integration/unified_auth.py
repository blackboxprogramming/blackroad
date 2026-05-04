"""
Unified Authentication Layer
Single auth system for all 7 enterprise systems
"""

import jwt
import hashlib
import secrets
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json


class AuthLevel(Enum):
    """Authentication levels across systems."""
    PUBLIC = "public"
    USER = "user"
    SERVICE = "service"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class TokenType(Enum):
    """Token types for different workflows."""
    ACCESS = "access"           # Short-lived (15m)
    REFRESH = "refresh"         # Long-lived (30d)
    SERVICE = "service"         # Service-to-service
    API_KEY = "api_key"         # Permanent API keys
    SESSION = "session"         # Browser sessions


class SystemScope(Enum):
    """Scope permissions for each system."""
    SECURITY = "security"                    # Security Hardening
    DEPLOYMENT = "deployment"                # Global Deployment
    API = "api"                             # Advanced API Features
    DEVELOPER = "developer"                  # Developer Portal
    MONITORING = "monitoring"               # Advanced Monitoring
    ML = "ml"                               # Machine Learning
    COMPLIANCE = "compliance"               # Compliance & Audit


class UnifiedAuthProvider:
    """Unified authentication for all systems."""
    
    def __init__(self, secret_key: str, issuer: str = "blackroad"):
        self.secret_key = secret_key
        self.issuer = issuer
        self.users: Dict[str, Dict] = {}
        self.tokens: Dict[str, Dict] = {}
        self.services: Dict[str, Dict] = {}
        self.scopes: Dict[str, List[str]] = {}
    
    def register_user(self, user_id: str, email: str, password: str,
                     auth_level: AuthLevel = AuthLevel.USER,
                     systems: Optional[List[SystemScope]] = None) -> Dict:
        """Register user across all systems."""
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            secrets.token_bytes(32),
            100000
        ).hex()
        
        user = {
            'user_id': user_id,
            'email': email,
            'password_hash': password_hash,
            'auth_level': auth_level.value,
            'systems': [s.value for s in systems] if systems else [],
            'created_at': datetime.utcnow().isoformat(),
            'active': True,
            'mfa_enabled': False,
        }
        
        self.users[user_id] = user
        self.scopes[user_id] = [s.value for s in systems] if systems else []
        
        return user
    
    def authenticate(self, email: str, password: str) -> Tuple[bool, Optional[str]]:
        """Authenticate user."""
        for user_id, user in self.users.items():
            if user['email'] == email and user['active']:
                # In production, use bcrypt or argon2
                password_hash = hashlib.pbkdf2_hmac(
                    'sha256',
                    password.encode(),
                    user['password_hash'][:64].encode(),
                    100000
                ).hex()
                
                if password_hash == user['password_hash']:
                    return True, user_id
        
        return False, None
    
    def generate_access_token(self, user_id: str, systems: Optional[List[str]] = None,
                             ttl_minutes: int = 15) -> str:
        """Generate short-lived access token."""
        payload = {
            'user_id': user_id,
            'token_type': TokenType.ACCESS.value,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(minutes=ttl_minutes),
            'iss': self.issuer,
            'systems': systems or self.scopes.get(user_id, []),
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        
        self.tokens[token] = {
            'user_id': user_id,
            'type': TokenType.ACCESS.value,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(minutes=ttl_minutes)).isoformat(),
        }
        
        return token
    
    def generate_refresh_token(self, user_id: str, ttl_days: int = 30) -> str:
        """Generate long-lived refresh token."""
        payload = {
            'user_id': user_id,
            'token_type': TokenType.REFRESH.value,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(days=ttl_days),
            'iss': self.issuer,
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        
        self.tokens[token] = {
            'user_id': user_id,
            'type': TokenType.REFRESH.value,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(days=ttl_days)).isoformat(),
        }
        
        return token
    
    def generate_service_token(self, service_id: str, target_systems: List[str],
                              ttl_hours: int = 1) -> str:
        """Generate service-to-service token."""
        payload = {
            'service_id': service_id,
            'token_type': TokenType.SERVICE.value,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=ttl_hours),
            'iss': self.issuer,
            'target_systems': target_systems,
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        
        self.tokens[token] = {
            'service_id': service_id,
            'type': TokenType.SERVICE.value,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(hours=ttl_hours)).isoformat(),
        }
        
        return token
    
    def verify_token(self, token: str) -> Tuple[bool, Optional[Dict]]:
        """Verify token across all systems."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return True, payload
        except jwt.ExpiredSignatureError:
            return False, {'error': 'Token expired'}
        except jwt.InvalidTokenError:
            return False, {'error': 'Invalid token'}
    
    def verify_access(self, token: str, required_system: str) -> Tuple[bool, str]:
        """Verify user has access to system."""
        valid, payload = self.verify_token(token)
        if not valid:
            return False, "Invalid or expired token"
        
        systems = payload.get('systems', [])
        if required_system not in systems and required_system != '*':
            return False, f"Access denied to {required_system}"
        
        return True, payload.get('user_id')
    
    def revoke_token(self, token: str) -> bool:
        """Revoke token (logout)."""
        if token in self.tokens:
            self.tokens[token]['revoked'] = True
            self.tokens[token]['revoked_at'] = datetime.utcnow().isoformat()
            return True
        return False
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile with all system access."""
        user = self.users.get(user_id)
        if not user:
            return None
        
        return {
            'user_id': user['user_id'],
            'email': user['email'],
            'auth_level': user['auth_level'],
            'systems_access': user['systems'],
            'mfa_enabled': user['mfa_enabled'],
            'created_at': user['created_at'],
            'active': user['active'],
        }
    
    def update_system_access(self, user_id: str, systems: List[str]) -> bool:
        """Update user's system access (admin only)."""
        if user_id not in self.users:
            return False
        
        self.users[user_id]['systems'] = systems
        self.scopes[user_id] = systems
        return True
    
    def disable_user(self, user_id: str) -> bool:
        """Disable user across all systems."""
        if user_id not in self.users:
            return False
        
        self.users[user_id]['active'] = False
        
        # Revoke all active tokens
        for token, token_data in self.tokens.items():
            if token_data.get('user_id') == user_id and 'revoked' not in token_data:
                token_data['revoked'] = True
        
        return True


class CrossSystemAuthContext:
    """Auth context for cross-system requests."""
    
    def __init__(self, user_id: str, systems: List[str], auth_level: str):
        self.user_id = user_id
        self.systems = systems
        self.auth_level = auth_level
        self.created_at = datetime.utcnow()
        self.request_id = secrets.token_hex(16)
    
    def has_access_to(self, system: str) -> bool:
        """Check if user can access system."""
        return system in self.systems or '*' in self.systems
    
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.auth_level in ['admin', 'super_admin']
    
    def can_modify(self, resource_type: str) -> bool:
        """Check if user can modify resource."""
        if self.is_admin():
            return True
        
        read_only_types = ['audit_logs', 'compliance_reports']
        return resource_type not in read_only_types
    
    def to_dict(self) -> Dict:
        """Export context for logging."""
        return {
            'user_id': self.user_id,
            'systems': self.systems,
            'auth_level': self.auth_level,
            'request_id': self.request_id,
            'created_at': self.created_at.isoformat(),
        }


class SessionManager:
    """Manage authenticated sessions."""
    
    def __init__(self, auth_provider: UnifiedAuthProvider):
        self.auth_provider = auth_provider
        self.sessions: Dict[str, Dict] = {}
    
    def create_session(self, user_id: str, systems: List[str],
                      duration_hours: int = 24) -> str:
        """Create authenticated session."""
        session_id = secrets.token_hex(16)
        
        self.sessions[session_id] = {
            'user_id': user_id,
            'systems': systems,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(hours=duration_hours)).isoformat(),
            'active': True,
        }
        
        return session_id
    
    def validate_session(self, session_id: str) -> Tuple[bool, Optional[Dict]]:
        """Validate session."""
        session = self.sessions.get(session_id)
        
        if not session or not session['active']:
            return False, None
        
        expires_at = datetime.fromisoformat(session['expires_at'])
        if datetime.utcnow() > expires_at:
            session['active'] = False
            return False, None
        
        return True, session
    
    def end_session(self, session_id: str) -> bool:
        """End session (logout)."""
        if session_id in self.sessions:
            self.sessions[session_id]['active'] = False
            self.sessions[session_id]['ended_at'] = datetime.utcnow().isoformat()
            return True
        return False
    
    def get_active_sessions(self, user_id: str) -> List[Dict]:
        """Get user's active sessions."""
        active = []
        for session_id, session in self.sessions.items():
            if session['user_id'] == user_id and session['active']:
                expires_at = datetime.fromisoformat(session['expires_at'])
                if datetime.utcnow() <= expires_at:
                    active.append({
                        'session_id': session_id,
                        'created_at': session['created_at'],
                        'expires_at': session['expires_at'],
                    })
        
        return active
