"""Secure credential management for integrations."""

from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import hashlib
import secrets
from cryptography.fernet import Fernet
import base64


@dataclass
class CredentialVault:
    """Encrypted credential storage."""
    vault_id: str
    integration_id: str
    credential_type: str  # oauth2, api_key, bearer, etc.
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    encrypted_data: str = ""
    checksum: str = ""


class CredentialManager:
    """Manages secure credential storage and rotation."""
    
    def __init__(self, master_key: str):
        """
        Initialize credential manager.
        
        Args:
            master_key: Base key for credential encryption (will be key-derived)
        """
        # Derive encryption key from master key
        key_material = hashlib.sha256(master_key.encode()).digest()
        self.cipher_key = base64.urlsafe_b64encode(key_material[:32])
        self.fernet = Fernet(self.cipher_key)
        self.vaults: Dict[str, CredentialVault] = {}
        self.rotation_policies: Dict[str, Dict[str, Any]] = {}
    
    def store_credentials(
        self,
        integration_id: str,
        credential_type: str,
        credentials: Dict[str, str],
        rotation_days: int = 90
    ) -> CredentialVault:
        """
        Store encrypted credentials.
        
        Args:
            integration_id: ID of integration
            credential_type: Type (oauth2, api_key, bearer, etc.)
            credentials: Credential data to encrypt
            rotation_days: Days before rotation recommended
        
        Returns:
            CredentialVault with encrypted data
        """
        # Serialize and encrypt
        json_data = json.dumps(credentials)
        encrypted = self.fernet.encrypt(json_data.encode())
        
        # Calculate checksum
        checksum = hashlib.sha256(json_data.encode()).hexdigest()
        
        vault_id = f"cv_{secrets.token_hex(8)}"
        vault = CredentialVault(
            vault_id=vault_id,
            integration_id=integration_id,
            credential_type=credential_type,
            encrypted_data=encrypted.decode(),
            checksum=checksum
        )
        
        self.vaults[vault_id] = vault
        
        # Set rotation policy
        self.rotation_policies[vault_id] = {
            'rotation_days': rotation_days,
            'next_rotation': (datetime.utcnow() + timedelta(days=rotation_days)).isoformat(),
            'rotation_required': False,
        }
        
        return vault
    
    def retrieve_credentials(self, vault_id: str) -> Optional[Dict[str, str]]:
        """
        Retrieve and decrypt credentials.
        
        Args:
            vault_id: ID of credential vault
        
        Returns:
            Decrypted credential dictionary or None if not found
        """
        vault = self.vaults.get(vault_id)
        if not vault:
            return None
        
        try:
            decrypted = self.fernet.decrypt(vault.encrypted_data.encode())
            credentials = json.loads(decrypted.decode())
            
            # Verify checksum
            checksum = hashlib.sha256(decrypted).hexdigest()
            if checksum != vault.checksum:
                return None  # Data may be corrupted
            
            # Update last used
            vault.last_used = datetime.utcnow()
            
            return credentials
        except:
            return None
    
    def rotate_credentials(
        self,
        vault_id: str,
        new_credentials: Dict[str, str]
    ) -> Optional[CredentialVault]:
        """
        Rotate credentials to new values.
        
        Args:
            vault_id: ID of vault to rotate
            new_credentials: New credential values
        
        Returns:
            Updated CredentialVault or None
        """
        vault = self.vaults.get(vault_id)
        if not vault:
            return None
        
        # Store new credentials (creates new vault entry)
        policy = self.rotation_policies.get(vault_id, {})
        rotation_days = policy.get('rotation_days', 90)
        
        new_vault = self.store_credentials(
            vault.integration_id,
            vault.credential_type,
            new_credentials,
            rotation_days
        )
        
        # Mark old vault as rotated
        vault.updated_at = datetime.utcnow()
        
        # Update rotation policy
        if vault_id in self.rotation_policies:
            policy['rotation_required'] = False
            policy['last_rotation'] = datetime.utcnow().isoformat()
            policy['next_rotation'] = (datetime.utcnow() + timedelta(days=rotation_days)).isoformat()
        
        return new_vault
    
    def check_rotation_needed(self, vault_id: str) -> bool:
        """Check if credentials need rotation."""
        policy = self.rotation_policies.get(vault_id)
        if not policy:
            return False
        
        next_rotation = datetime.fromisoformat(policy['next_rotation'])
        return datetime.utcnow() >= next_rotation
    
    def mark_rotation_required(self, vault_id: str) -> bool:
        """Mark credentials as needing rotation (e.g., due to breach)."""
        policy = self.rotation_policies.get(vault_id)
        if not policy:
            return False
        
        policy['rotation_required'] = True
        return True
    
    def get_vault(self, vault_id: str) -> Optional[CredentialVault]:
        """Get vault metadata (without decrypted data)."""
        return self.vaults.get(vault_id)
    
    def list_vaults(
        self,
        integration_id: Optional[str] = None,
        credential_type: Optional[str] = None
    ) -> list:
        """List all credential vaults (metadata only)."""
        vaults = list(self.vaults.values())
        
        if integration_id:
            vaults = [v for v in vaults if v.integration_id == integration_id]
        
        if credential_type:
            vaults = [v for v in vaults if v.credential_type == credential_type]
        
        # Return metadata only (no encrypted data)
        return [
            {
                'vault_id': v.vault_id,
                'integration_id': v.integration_id,
                'credential_type': v.credential_type,
                'created_at': v.created_at.isoformat(),
                'updated_at': v.updated_at.isoformat(),
                'last_used': v.last_used.isoformat() if v.last_used else None,
                'rotation_required': self.rotation_policies.get(v.vault_id, {}).get('rotation_required', False),
            }
            for v in vaults
        ]
    
    def delete_vault(self, vault_id: str) -> bool:
        """Delete a credential vault."""
        if vault_id in self.vaults:
            del self.vaults[vault_id]
            if vault_id in self.rotation_policies:
                del self.rotation_policies[vault_id]
            return True
        return False
    
    def generate_oauth_challenge(self) -> Dict[str, str]:
        """Generate PKCE challenge for OAuth2 authorization flow."""
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip('=')
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode().rstrip('=')
        
        return {
            'code_verifier': code_verifier,
            'code_challenge': code_challenge,
            'challenge_method': 'S256'
        }
    
    def store_oauth_code(
        self,
        integration_id: str,
        code: str,
        state: str,
        expires_in_seconds: int = 600
    ) -> Dict[str, Any]:
        """
        Store OAuth authorization code temporarily.
        
        Args:
            integration_id: Integration ID
            code: Authorization code from OAuth provider
            state: State parameter for CSRF protection
            expires_in_seconds: Code expiration time
        
        Returns:
            Authorization code metadata
        """
        auth_code_id = f"ac_{secrets.token_hex(8)}"
        expiration = datetime.utcnow() + timedelta(seconds=expires_in_seconds)
        
        # Store temporarily (would be in Redis in production)
        auth_data = {
            'id': auth_code_id,
            'integration_id': integration_id,
            'code': code,
            'state': state,
            'expires_at': expiration.isoformat(),
            'used': False,
        }
        
        return auth_data
    
    def exchange_oauth_code(
        self,
        auth_code_id: str,
        code: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_in_seconds: int = 3600
    ) -> Optional[CredentialVault]:
        """
        Exchange OAuth code for tokens.
        
        Args:
            auth_code_id: Authorization code ID
            code: Authorization code to verify
            access_token: Access token from OAuth provider
            refresh_token: Optional refresh token
            expires_in_seconds: Token expiration time
        
        Returns:
            CredentialVault with stored tokens
        """
        # Verify code hasn't expired or been used
        # (in production, would check Redis/temp store)
        
        credentials = {
            'access_token': access_token,
            'token_type': 'Bearer',
        }
        
        if refresh_token:
            credentials['refresh_token'] = refresh_token
        
        credentials['expires_at'] = (
            datetime.utcnow() + timedelta(seconds=expires_in_seconds)
        ).isoformat()
        
        vault = self.store_credentials(
            integration_id='oauth_' + auth_code_id,
            credential_type='oauth2',
            credentials=credentials,
            rotation_days=30  # Rotate OAuth tokens more frequently
        )
        
        return vault
    
    def get_vault_rotation_status(self, vault_id: str) -> Dict[str, Any]:
        """Get rotation status for a vault."""
        vault = self.get_vault(vault_id)
        policy = self.rotation_policies.get(vault_id)
        
        if not vault or not policy:
            return {}
        
        rotation_required = self.check_rotation_needed(vault_id)
        
        return {
            'vault_id': vault_id,
            'last_rotated': vault.updated_at.isoformat(),
            'next_rotation': policy.get('next_rotation'),
            'rotation_due': rotation_required,
            'rotation_required': policy.get('rotation_required', False),
            'rotation_days_interval': policy.get('rotation_days'),
            'days_until_rotation': max(
                0,
                (datetime.fromisoformat(policy['next_rotation']) - datetime.utcnow()).days
            ) if policy.get('next_rotation') else 0,
        }
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """Get credential manager statistics."""
        rotation_needed = sum(
            1 for p in self.rotation_policies.values()
            if p.get('rotation_required', False)
        )
        
        overdue = sum(
            1 for vault_id in self.vaults.keys()
            if self.check_rotation_needed(vault_id)
        )
        
        return {
            'total_vaults': len(self.vaults),
            'rotation_required': rotation_needed,
            'rotation_overdue': overdue,
            'credential_types': list(set(v.credential_type for v in self.vaults.values())),
            'integrations_protected': len(set(v.integration_id for v in self.vaults.values())),
        }
