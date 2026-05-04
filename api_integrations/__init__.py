"""Third-Party API Integration Hub - Pre-built connectors for 50+ SaaS platforms."""

__version__ = "1.0.0"

from .integrations import IntegrationHub, IntegrationConfig, IntegrationStatus
from .connectors import get_connector, AVAILABLE_CONNECTORS
from .webhook_manager import WebhookManager
from .credentials import CredentialManager

__all__ = [
    'IntegrationHub',
    'IntegrationConfig',
    'IntegrationStatus',
    'get_connector',
    'AVAILABLE_CONNECTORS',
    'WebhookManager',
    'CredentialManager',
]
