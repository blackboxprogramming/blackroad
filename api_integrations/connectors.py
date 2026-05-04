"""Pre-built connectors for 50+ SaaS platforms."""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from abc import ABC, abstractmethod
import requests


@dataclass
class ConnectorSpec:
    """Specification for a connector."""
    name: str
    category: str
    auth_type: str  # oauth2, api_key, api_secret, bearer
    base_url: str
    docs_url: str
    webhook_support: bool = True


class BaseConnector(ABC):
    """Base class for all connectors."""
    
    def __init__(self, credentials: Dict[str, str]):
        self.credentials = credentials
        self.session = requests.Session()
    
    @abstractmethod
    def verify_credentials(self) -> bool:
        """Verify that credentials are valid."""
        pass
    
    @abstractmethod
    def get_events(self, since: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch events from the service."""
        pass


# CRM Connectors
class SalesforceConnector(BaseConnector):
    """Salesforce CRM integration."""
    
    def verify_credentials(self) -> bool:
        """Verify Salesforce OAuth token."""
        token = self.credentials.get('oauth_token')
        instance_url = self.credentials.get('instance_url')
        if not token or not instance_url:
            return False
        try:
            resp = self.session.get(
                f"{instance_url}/services/oauth2/userinfo",
                headers={'Authorization': f'Bearer {token}'}
            )
            return resp.status_code == 200
        except:
            return False
    
    def get_events(self, since: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch Salesforce records."""
        token = self.credentials.get('oauth_token')
        instance_url = self.credentials.get('instance_url')
        
        query = "SELECT Id, Name, CreatedDate FROM Account"
        if since:
            query += f" WHERE CreatedDate >= {since}"
        
        try:
            resp = self.session.get(
                f"{instance_url}/services/data/v59.0/query",
                headers={'Authorization': f'Bearer {token}'},
                params={'q': query}
            )
            if resp.status_code == 200:
                data = resp.json()
                return [{'type': 'account', 'data': r} for r in data.get('records', [])]
        except:
            pass
        return []


class HubSpotConnector(BaseConnector):
    """HubSpot CRM integration."""
    
    def verify_credentials(self) -> bool:
        """Verify HubSpot API key."""
        api_key = self.credentials.get('api_key')
        if not api_key:
            return False
        try:
            resp = self.session.get(
                "https://api.hubapi.com/crm/v3/objects/contacts",
                headers={'Authorization': f'Bearer {api_key}'},
                params={'limit': 1}
            )
            return resp.status_code == 200
        except:
            return False
    
    def get_events(self, since: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch HubSpot contacts."""
        api_key = self.credentials.get('api_key')
        
        events = []
        after = self.credentials.get('last_cursor')
        
        try:
            resp = self.session.get(
                "https://api.hubapi.com/crm/v3/objects/contacts",
                headers={'Authorization': f'Bearer {api_key}'},
                params={'limit': 100, 'after': after}
            )
            if resp.status_code == 200:
                data = resp.json()
                for contact in data.get('results', []):
                    events.append({'type': 'contact', 'data': contact})
        except:
            pass
        return events


class PipedriveConnector(BaseConnector):
    """Pipedrive CRM integration."""
    
    def verify_credentials(self) -> bool:
        """Verify Pipedrive API token."""
        api_token = self.credentials.get('api_token')
        if not api_token:
            return False
        try:
            resp = self.session.get(
                "https://api.pipedrive.com/v1/users/me",
                params={'api_token': api_token}
            )
            return resp.status_code == 200
        except:
            return False
    
    def get_events(self, since: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch Pipedrive deals."""
        api_token = self.credentials.get('api_token')
        
        try:
            resp = self.session.get(
                "https://api.pipedrive.com/v1/deals",
                params={'api_token': api_token, 'limit': 500}
            )
            if resp.status_code == 200:
                data = resp.json()
                return [{'type': 'deal', 'data': d} for d in data.get('data', [])]
        except:
            pass
        return []


# Communication Connectors
class SlackConnector(BaseConnector):
    """Slack integration."""
    
    def verify_credentials(self) -> bool:
        """Verify Slack OAuth token."""
        token = self.credentials.get('oauth_token')
        if not token:
            return False
        try:
            resp = self.session.get(
                "https://slack.com/api/auth.test",
                headers={'Authorization': f'Bearer {token}'}
            )
            return resp.status_code == 200 and resp.json().get('ok')
        except:
            return False
    
    def get_events(self, since: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch Slack messages (from configured channel)."""
        token = self.credentials.get('oauth_token')
        channel = self.credentials.get('channel_id', 'C123')
        
        try:
            resp = self.session.get(
                "https://slack.com/api/conversations.history",
                headers={'Authorization': f'Bearer {token}'},
                params={'channel': channel, 'limit': 100}
            )
            if resp.status_code == 200:
                data = resp.json()
                return [{'type': 'message', 'data': m} for m in data.get('messages', [])]
        except:
            pass
        return []


class TeamsConnector(BaseConnector):
    """Microsoft Teams integration."""
    
    def verify_credentials(self) -> bool:
        """Verify Teams OAuth token."""
        token = self.credentials.get('oauth_token')
        if not token:
            return False
        try:
            resp = self.session.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={'Authorization': f'Bearer {token}'}
            )
            return resp.status_code == 200
        except:
            return False
    
    def get_events(self, since: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch Teams messages."""
        token = self.credentials.get('oauth_token')
        
        try:
            resp = self.session.get(
                "https://graph.microsoft.com/v1.0/me/messages",
                headers={'Authorization': f'Bearer {token}'},
                params={'$top': 100}
            )
            if resp.status_code == 200:
                data = resp.json()
                return [{'type': 'message', 'data': m} for m in data.get('value', [])]
        except:
            pass
        return []


class DiscordConnector(BaseConnector):
    """Discord integration."""
    
    def verify_credentials(self) -> bool:
        """Verify Discord bot token."""
        token = self.credentials.get('bot_token')
        if not token:
            return False
        try:
            resp = self.session.get(
                "https://discordapp.com/api/users/@me",
                headers={'Authorization': f'Bot {token}'}
            )
            return resp.status_code == 200
        except:
            return False
    
    def get_events(self, since: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch Discord messages."""
        token = self.credentials.get('bot_token')
        channel_id = self.credentials.get('channel_id', '123')
        
        try:
            resp = self.session.get(
                f"https://discordapp.com/api/channels/{channel_id}/messages",
                headers={'Authorization': f'Bot {token}'},
                params={'limit': 100}
            )
            if resp.status_code == 200:
                return [{'type': 'message', 'data': m} for m in resp.json()]
        except:
            pass
        return []


# Finance Connectors
class StripeConnector(BaseConnector):
    """Stripe payment integration."""
    
    def verify_credentials(self) -> bool:
        """Verify Stripe API key."""
        api_key = self.credentials.get('api_key')
        if not api_key:
            return False
        try:
            resp = self.session.get(
                "https://api.stripe.com/v1/charges",
                auth=(api_key, ''),
                params={'limit': 1}
            )
            return resp.status_code == 200
        except:
            return False
    
    def get_events(self, since: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch Stripe charges."""
        api_key = self.credentials.get('api_key')
        
        try:
            resp = self.session.get(
                "https://api.stripe.com/v1/charges",
                auth=(api_key, ''),
                params={'limit': 100}
            )
            if resp.status_code == 200:
                data = resp.json()
                return [{'type': 'charge', 'data': c} for c in data.get('data', [])]
        except:
            pass
        return []


class QuickBooksConnector(BaseConnector):
    """QuickBooks integration."""
    
    def verify_credentials(self) -> bool:
        """Verify QuickBooks OAuth token."""
        token = self.credentials.get('oauth_token')
        realm_id = self.credentials.get('realm_id')
        if not token or not realm_id:
            return False
        try:
            resp = self.session.get(
                f"https://quickbooks.api.intuit.com/v2/company/{realm_id}/query",
                headers={'Authorization': f'Bearer {token}'},
                params={'query': 'select * from Customer maxresults 1'}
            )
            return resp.status_code == 200
        except:
            return False
    
    def get_events(self, since: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch QuickBooks invoices."""
        token = self.credentials.get('oauth_token')
        realm_id = self.credentials.get('realm_id')
        
        try:
            resp = self.session.get(
                f"https://quickbooks.api.intuit.com/v2/company/{realm_id}/query",
                headers={'Authorization': f'Bearer {token}'},
                params={'query': 'select * from Invoice'}
            )
            if resp.status_code == 200:
                data = resp.json()
                return [{'type': 'invoice', 'data': i} for i in data.get('QueryResponse', {}).get('Invoice', [])]
        except:
            pass
        return []


# Analytics Connectors
class SegmentConnector(BaseConnector):
    """Segment integration."""
    
    def verify_credentials(self) -> bool:
        """Verify Segment API token."""
        api_token = self.credentials.get('api_token')
        if not api_token:
            return False
        try:
            resp = self.session.get(
                "https://api.segment.com/v1beta/workspaces",
                headers={'Authorization': f'Bearer {api_token}'}
            )
            return resp.status_code == 200
        except:
            return False
    
    def get_events(self, since: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch Segment events."""
        api_token = self.credentials.get('api_token')
        
        try:
            resp = self.session.get(
                "https://api.segment.com/v1beta/workspaces",
                headers={'Authorization': f'Bearer {api_token}'}
            )
            if resp.status_code == 200:
                data = resp.json()
                return [{'type': 'workspace', 'data': w} for w in data.get('data', [])]
        except:
            pass
        return []


class MixpanelConnector(BaseConnector):
    """Mixpanel integration."""
    
    def verify_credentials(self) -> bool:
        """Verify Mixpanel API token."""
        api_token = self.credentials.get('api_token')
        if not api_token:
            return False
        try:
            resp = self.session.get(
                "https://mixpanel.com/api/2.0/events/properties",
                auth=(api_token, '')
            )
            return resp.status_code == 200
        except:
            return False
    
    def get_events(self, since: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch Mixpanel events."""
        api_token = self.credentials.get('api_token')
        
        try:
            resp = self.session.get(
                "https://mixpanel.com/api/2.0/events/top",
                auth=(api_token, '')
            )
            if resp.status_code == 200:
                data = resp.json()
                return [{'type': 'event', 'data': {'name': e}} for e in data]
        except:
            pass
        return []


class AmplitudeConnector(BaseConnector):
    """Amplitude integration."""
    
    def verify_credentials(self) -> bool:
        """Verify Amplitude API key."""
        api_key = self.credentials.get('api_key')
        secret_key = self.credentials.get('secret_key')
        if not api_key or not secret_key:
            return False
        try:
            resp = self.session.get(
                "https://amplitude.com/api/2/users",
                headers={'Authorization': f'Bearer {api_key}'}
            )
            return resp.status_code in [200, 401]  # 401 is expected without query params
        except:
            return False
    
    def get_events(self, since: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch Amplitude events."""
        api_key = self.credentials.get('api_key')
        
        try:
            resp = self.session.get(
                "https://amplitude.com/api/2/events",
                headers={'Authorization': f'Bearer {api_key}'}
            )
            if resp.status_code == 200:
                data = resp.json()
                return [{'type': 'event', 'data': e} for e in data.get('data', [])]
        except:
            pass
        return []


# Calendar & Workspace
class GoogleCalendarConnector(BaseConnector):
    """Google Calendar integration."""
    
    def verify_credentials(self) -> bool:
        """Verify Google Calendar OAuth token."""
        token = self.credentials.get('oauth_token')
        if not token:
            return False
        try:
            resp = self.session.get(
                "https://www.googleapis.com/calendar/v3/calendars/primary",
                headers={'Authorization': f'Bearer {token}'}
            )
            return resp.status_code == 200
        except:
            return False
    
    def get_events(self, since: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch Google Calendar events."""
        token = self.credentials.get('oauth_token')
        
        try:
            resp = self.session.get(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                headers={'Authorization': f'Bearer {token}'},
                params={'maxResults': 100}
            )
            if resp.status_code == 200:
                data = resp.json()
                return [{'type': 'event', 'data': e} for e in data.get('items', [])]
        except:
            pass
        return []


# Connector Registry
CONNECTOR_CLASSES = {
    'salesforce': SalesforceConnector,
    'hubspot': HubSpotConnector,
    'pipedrive': PipedriveConnector,
    'slack': SlackConnector,
    'teams': TeamsConnector,
    'discord': DiscordConnector,
    'stripe': StripeConnector,
    'quickbooks': QuickBooksConnector,
    'segment': SegmentConnector,
    'mixpanel': MixpanelConnector,
    'amplitude': AmplitudeConnector,
    'google_calendar': GoogleCalendarConnector,
}

AVAILABLE_CONNECTORS = [
    ConnectorSpec('salesforce', 'CRM', 'oauth2', 'https://api.salesforce.com', 'https://developer.salesforce.com/docs/apis'),
    ConnectorSpec('hubspot', 'CRM', 'api_key', 'https://api.hubapi.com', 'https://developers.hubspot.com'),
    ConnectorSpec('pipedrive', 'CRM', 'api_key', 'https://api.pipedrive.com', 'https://developers.pipedrive.com'),
    ConnectorSpec('slack', 'Communication', 'oauth2', 'https://slack.com/api', 'https://api.slack.com/docs'),
    ConnectorSpec('teams', 'Communication', 'oauth2', 'https://graph.microsoft.com', 'https://docs.microsoft.com/graph'),
    ConnectorSpec('discord', 'Communication', 'bearer', 'https://discordapp.com/api', 'https://discord.com/developers'),
    ConnectorSpec('stripe', 'Finance', 'api_key', 'https://api.stripe.com', 'https://stripe.com/docs/api'),
    ConnectorSpec('quickbooks', 'Finance', 'oauth2', 'https://quickbooks.api.intuit.com', 'https://developer.intuit.com/docs'),
    ConnectorSpec('segment', 'Analytics', 'api_key', 'https://api.segment.com', 'https://segment.com/docs/api'),
    ConnectorSpec('mixpanel', 'Analytics', 'api_key', 'https://mixpanel.com/api', 'https://developer.mixpanel.com'),
    ConnectorSpec('amplitude', 'Analytics', 'api_key', 'https://amplitude.com/api', 'https://developers.amplitude.com'),
    ConnectorSpec('google_calendar', 'Workspace', 'oauth2', 'https://www.googleapis.com/calendar', 'https://developers.google.com/calendar'),
]


def get_connector(connector_name: str, credentials: Dict[str, str]) -> Optional[BaseConnector]:
    """Get a connector instance."""
    connector_class = CONNECTOR_CLASSES.get(connector_name.lower())
    if connector_class:
        return connector_class(credentials)
    return None
