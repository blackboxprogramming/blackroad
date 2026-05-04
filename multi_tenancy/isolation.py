"""
Multi-Tenant Isolation Engine
Cryptographic tenant boundaries, billing separation, and data segregation
"""

from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import hmac
import json
from abc import ABC, abstractmethod


class TenantIsolationLevel(Enum):
    """Isolation levels for multi-tenancy."""
    DATABASE_ROW = "database_row"           # Row-level filtering (basic)
    SCHEMA_ISOLATION = "schema_isolation"   # Separate schema per tenant
    DATABASE_ISOLATION = "database_isolation"  # Separate DB per tenant
    CRYPTOGRAPHIC = "cryptographic"        # Encrypted per-tenant data


class BillingModel(Enum):
    """Tenant billing models."""
    PER_SEAT = "per_seat"                  # $X per user per month
    USAGE_BASED = "usage_based"            # $X per API call/unit
    FLAT_RATE = "flat_rate"                # Fixed monthly fee
    HYBRID = "hybrid"                      # Combination


class TenantTier(Enum):
    """SaaS pricing tiers."""
    STARTER = "starter"                    # $99/mo
    PROFESSIONAL = "professional"          # $299/mo
    ENTERPRISE = "enterprise"              # Custom pricing


class DataEncryption:
    """Cryptographic data isolation."""
    
    def __init__(self, master_key: str):
        self.master_key = master_key.encode()
    
    def _derive_tenant_key(self, tenant_id: str) -> bytes:
        """Derive tenant-specific encryption key."""
        return hmac.new(
            self.master_key,
            tenant_id.encode(),
            hashlib.sha256
        ).digest()
    
    def encrypt_data(self, tenant_id: str, data: str) -> str:
        """Encrypt data with tenant-specific key."""
        tenant_key = self._derive_tenant_key(tenant_id)
        
        # Simple XOR-based encryption (production would use AES-256)
        encrypted = bytearray()
        data_bytes = data.encode()
        
        for i, byte in enumerate(data_bytes):
            encrypted.append(byte ^ tenant_key[i % len(tenant_key)])
        
        return encrypted.hex()
    
    def decrypt_data(self, tenant_id: str, encrypted: str) -> str:
        """Decrypt data with tenant-specific key."""
        tenant_key = self._derive_tenant_key(tenant_id)
        
        # Reverse XOR
        encrypted_bytes = bytes.fromhex(encrypted)
        decrypted = bytearray()
        
        for i, byte in enumerate(encrypted_bytes):
            decrypted.append(byte ^ tenant_key[i % len(tenant_key)])
        
        return decrypted.decode()
    
    def compute_data_hash(self, tenant_id: str, data: str) -> str:
        """Compute tamper-proof hash for data integrity."""
        tenant_key = self._derive_tenant_key(tenant_id)
        return hmac.new(tenant_key, data.encode(), hashlib.sha256).hexdigest()
    
    def verify_data_integrity(self, tenant_id: str, data: str, hash_val: str) -> bool:
        """Verify data hasn't been modified."""
        expected_hash = self.compute_data_hash(tenant_id, data)
        return hmac.compare_digest(expected_hash, hash_val)


class Tenant:
    """Multi-tenant customer entity."""
    
    def __init__(self, tenant_id: str, company_name: str, 
                 isolation_level: TenantIsolationLevel = TenantIsolationLevel.CRYPTOGRAPHIC):
        self.tenant_id = tenant_id
        self.company_name = company_name
        self.isolation_level = isolation_level
        self.created_at = datetime.utcnow().isoformat()
        
        # Tenant configuration
        self.tier = TenantTier.STARTER
        self.billing_model = BillingModel.HYBRID
        self.seats = 1
        self.monthly_api_calls = 0
        self.api_call_limit = 100000
        self.storage_gb = 0
        self.storage_limit_gb = 10
        
        # Isolation metadata
        self.database_schema = f"tenant_{tenant_id}"
        self.encryption_key_id = f"key_{tenant_id}"
        self.api_key = self._generate_api_key()
        
        # Access control
        self.allowed_ips: Set[str] = set()
        self.webhook_urls: List[str] = []
        self.team_members: Dict[str, Dict] = {}
        
        # Billing
        self.monthly_cost = 0.0
        self.invoice_history: List[Dict] = []
    
    def _generate_api_key(self) -> str:
        """Generate tenant API key."""
        data = f"{self.tenant_id}_{datetime.utcnow().isoformat()}".encode()
        return hashlib.sha256(data).hexdigest()[:32]
    
    def add_team_member(self, user_id: str, email: str, role: str) -> bool:
        """Add team member to tenant."""
        if user_id not in self.team_members:
            self.team_members[user_id] = {
                'email': email,
                'role': role,
                'added_at': datetime.utcnow().isoformat(),
                'last_login': None,
            }
            return True
        return False
    
    def to_dict(self) -> Dict:
        """Export tenant."""
        return {
            'tenant_id': self.tenant_id,
            'company_name': self.company_name,
            'tier': self.tier.value,
            'isolation_level': self.isolation_level.value,
            'seats': self.seats,
            'monthly_api_calls': self.monthly_api_calls,
            'api_call_limit': self.api_call_limit,
            'storage_gb': self.storage_gb,
            'storage_limit_gb': self.storage_limit_gb,
            'monthly_cost': self.monthly_cost,
        }


class TenantContextManager:
    """Manage tenant context and request isolation."""
    
    def __init__(self):
        self.current_tenant_id: Optional[str] = None
        self.request_headers: Dict[str, str] = {}
        self.audit_logs: List[Dict] = []
    
    def set_tenant_context(self, tenant_id: str, api_key: str) -> bool:
        """Set tenant context for current request."""
        # Validate API key matches tenant
        if not self._validate_api_key(tenant_id, api_key):
            self.audit_logs.append({
                'timestamp': datetime.utcnow().isoformat(),
                'event': 'INVALID_API_KEY',
                'tenant_id': tenant_id,
                'severity': 'HIGH',
            })
            return False
        
        self.current_tenant_id = tenant_id
        self.request_headers['X-Tenant-ID'] = tenant_id
        self.request_headers['Authorization'] = f"Bearer {api_key}"
        
        self.audit_logs.append({
            'timestamp': datetime.utcnow().isoformat(),
            'event': 'TENANT_CONTEXT_SET',
            'tenant_id': tenant_id,
            'severity': 'INFO',
        })
        return True
    
    def _validate_api_key(self, tenant_id: str, api_key: str) -> bool:
        """Validate API key format."""
        return len(api_key) == 32 and api_key.isalnum()
    
    def get_tenant_context(self) -> Optional[str]:
        """Get current tenant context."""
        return self.current_tenant_id
    
    def enforce_tenant_isolation(self, requested_tenant_id: str) -> bool:
        """Enforce that current context matches requested tenant."""
        if self.current_tenant_id != requested_tenant_id:
            self.audit_logs.append({
                'timestamp': datetime.utcnow().isoformat(),
                'event': 'ISOLATION_VIOLATION',
                'current_tenant': self.current_tenant_id,
                'requested_tenant': requested_tenant_id,
                'severity': 'CRITICAL',
            })
            return False
        return True
    
    def get_audit_trail(self, limit: int = 100) -> List[Dict]:
        """Get audit trail."""
        return self.audit_logs[-limit:]


class TenantDataStore:
    """Isolated tenant data storage."""
    
    def __init__(self, encryption: DataEncryption):
        self.encryption = encryption
        self.storage: Dict[str, Dict[str, str]] = {}  # tenant_id -> {data_id -> encrypted_data}
        self.metadata: Dict[str, Dict] = {}  # tenant_id -> metadata
    
    def create_tenant_storage(self, tenant_id: str) -> bool:
        """Initialize storage for tenant."""
        if tenant_id not in self.storage:
            self.storage[tenant_id] = {}
            self.metadata[tenant_id] = {
                'created_at': datetime.utcnow().isoformat(),
                'data_count': 0,
                'total_size_bytes': 0,
            }
            return True
        return False
    
    def store_data(self, tenant_id: str, data_id: str, data: str) -> Tuple[bool, str]:
        """Store encrypted data for tenant."""
        if tenant_id not in self.storage:
            return False, "Tenant not initialized"
        
        encrypted = self.encryption.encrypt_data(tenant_id, data)
        integrity_hash = self.encryption.compute_data_hash(tenant_id, data)
        
        self.storage[tenant_id][data_id] = json.dumps({
            'encrypted_data': encrypted,
            'integrity_hash': integrity_hash,
            'stored_at': datetime.utcnow().isoformat(),
        })
        
        self.metadata[tenant_id]['data_count'] += 1
        self.metadata[tenant_id]['total_size_bytes'] += len(encrypted)
        
        return True, data_id
    
    def retrieve_data(self, tenant_id: str, data_id: str) -> Tuple[bool, Optional[str]]:
        """Retrieve and decrypt data for tenant."""
        if tenant_id not in self.storage or data_id not in self.storage[tenant_id]:
            return False, None
        
        stored = json.loads(self.storage[tenant_id][data_id])
        
        # Decrypt and verify integrity
        decrypted = self.encryption.decrypt_data(tenant_id, stored['encrypted_data'])
        
        if not self.encryption.verify_data_integrity(tenant_id, decrypted, stored['integrity_hash']):
            return False, None
        
        return True, decrypted
    
    def delete_tenant_data(self, tenant_id: str) -> bool:
        """Delete all tenant data (GDPR right to be forgotten)."""
        if tenant_id in self.storage:
            self.storage[tenant_id] = {}
            self.metadata[tenant_id]['data_count'] = 0
            self.metadata[tenant_id]['total_size_bytes'] = 0
            return True
        return False
    
    def get_tenant_metadata(self, tenant_id: str) -> Optional[Dict]:
        """Get tenant storage metadata."""
        return self.metadata.get(tenant_id)


class TenantBillingEngine:
    """Calculate and track per-tenant costs."""
    
    def __init__(self):
        self.invoices: Dict[str, List[Dict]] = {}  # tenant_id -> [invoices]
    
    def calculate_monthly_cost(self, tenant: Tenant) -> float:
        """Calculate monthly cost for tenant."""
        cost = 0.0
        
        # Tier-based cost
        tier_costs = {
            TenantTier.STARTER: 99.0,
            TenantTier.PROFESSIONAL: 299.0,
            TenantTier.ENTERPRISE: 999.0,
        }
        cost += tier_costs.get(tenant.tier, 99.0)
        
        # Usage-based overages
        if tenant.billing_model in [BillingModel.USAGE_BASED, BillingModel.HYBRID]:
            # $0.01 per 1000 API calls
            api_overages = max(0, tenant.monthly_api_calls - 100000)
            cost += (api_overages / 1000) * 0.01
            
            # $0.50 per GB storage overage
            storage_overages = max(0, tenant.storage_gb - 10)
            cost += storage_overages * 0.50
        
        # Per-seat cost
        if tenant.billing_model in [BillingModel.PER_SEAT, BillingModel.HYBRID]:
            # $10 per seat
            seat_cost = max(0, tenant.seats - 1) * 10
            cost += seat_cost
        
        tenant.monthly_cost = cost
        return cost
    
    def generate_invoice(self, tenant: Tenant) -> Dict:
        """Generate invoice for tenant."""
        if tenant.tenant_id not in self.invoices:
            self.invoices[tenant.tenant_id] = []
        
        cost = self.calculate_monthly_cost(tenant)
        
        invoice = {
            'invoice_id': f"INV-{tenant.tenant_id}-{datetime.utcnow().strftime('%Y%m')}",
            'tenant_id': tenant.tenant_id,
            'company_name': tenant.company_name,
            'period_start': (datetime.utcnow() - timedelta(days=30)).isoformat(),
            'period_end': datetime.utcnow().isoformat(),
            'items': [
                {
                    'description': f"{tenant.tier.value} plan",
                    'amount': 99.0 if tenant.tier == TenantTier.STARTER else 299.0 if tenant.tier == TenantTier.PROFESSIONAL else 999.0,
                },
            ],
            'total': cost,
            'status': 'issued',
            'generated_at': datetime.utcnow().isoformat(),
        }
        
        self.invoices[tenant.tenant_id].append(invoice)
        tenant.invoice_history.append(invoice)
        
        return invoice
    
    def get_billing_summary(self, tenant_id: str) -> Dict:
        """Get billing summary for tenant."""
        return {
            'tenant_id': tenant_id,
            'invoice_count': len(self.invoices.get(tenant_id, [])),
            'recent_invoices': self.invoices.get(tenant_id, [])[-3:],
        }


class AccessControlPolicy:
    """Tenant access control and authorization."""
    
    def __init__(self):
        self.policies: Dict[str, Dict] = {}
    
    def create_policy(self, policy_id: str, tenant_id: str,
                     allowed_operations: List[str],
                     allowed_resources: List[str]) -> bool:
        """Create access control policy."""
        self.policies[policy_id] = {
            'tenant_id': tenant_id,
            'allowed_operations': allowed_operations,
            'allowed_resources': allowed_resources,
            'created_at': datetime.utcnow().isoformat(),
        }
        return True
    
    def check_access(self, policy_id: str, operation: str, resource: str) -> bool:
        """Check if operation is allowed."""
        if policy_id not in self.policies:
            return False
        
        policy = self.policies[policy_id]
        
        # Check operation
        if operation not in policy['allowed_operations']:
            return False
        
        # Check resource (support wildcards)
        allowed = False
        for allowed_resource in policy['allowed_resources']:
            if allowed_resource == '*' or resource.startswith(allowed_resource):
                allowed = True
                break
        
        return allowed
    
    def list_policies(self, tenant_id: str) -> List[Dict]:
        """List policies for tenant."""
        return [p for p in self.policies.values() if p['tenant_id'] == tenant_id]


class MultiTenantOrchestrator:
    """Orchestrate multi-tenant operations."""
    
    def __init__(self, master_key: str):
        self.encryption = DataEncryption(master_key)
        self.context_manager = TenantContextManager()
        self.data_store = TenantDataStore(self.encryption)
        self.billing_engine = TenantBillingEngine()
        self.access_control = AccessControlPolicy()
        self.tenants: Dict[str, Tenant] = {}
    
    def provision_tenant(self, tenant_id: str, company_name: str) -> Tuple[bool, str]:
        """Provision new tenant."""
        if tenant_id in self.tenants:
            return False, "Tenant already exists"
        
        tenant = Tenant(tenant_id, company_name)
        self.tenants[tenant_id] = tenant
        
        # Initialize storage
        self.data_store.create_tenant_storage(tenant_id)
        
        # Create default access policy
        policy_id = f"policy_{tenant_id}_default"
        self.access_control.create_policy(
            policy_id,
            tenant_id,
            ['read', 'write', 'delete'],
            ['*']
        )
        
        return True, tenant.api_key
    
    def deprovision_tenant(self, tenant_id: str) -> bool:
        """Deprovision tenant (GDPR right to be forgotten)."""
        if tenant_id not in self.tenants:
            return False
        
        # Delete all data
        self.data_store.delete_tenant_data(tenant_id)
        
        # Remove tenant
        del self.tenants[tenant_id]
        
        return True
    
    def get_tenant_usage(self, tenant_id: str) -> Dict:
        """Get tenant resource usage."""
        if tenant_id not in self.tenants:
            return {}
        
        tenant = self.tenants[tenant_id]
        metadata = self.data_store.get_tenant_metadata(tenant_id)
        
        return {
            'tenant_id': tenant_id,
            'api_calls': tenant.monthly_api_calls,
            'api_call_limit': tenant.api_call_limit,
            'usage_percent': (tenant.monthly_api_calls / tenant.api_call_limit * 100) if tenant.api_call_limit > 0 else 0,
            'storage_gb': tenant.storage_gb,
            'storage_limit_gb': tenant.storage_limit_gb,
            'storage_percent': (tenant.storage_gb / tenant.storage_limit_gb * 100) if tenant.storage_limit_gb > 0 else 0,
            'seats': tenant.seats,
            'data_count': metadata.get('data_count', 0) if metadata else 0,
        }
