"""
Advanced Threat Detection System
AI-powered anomaly detection, insider threat detection, DDoS protection
"""

from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import statistics


class ThreatLevel(Enum):
    """Threat severity levels."""
    LOW = "low"                        # < 5% risk
    MEDIUM = "medium"                  # 5-25% risk
    HIGH = "high"                      # 25-50% risk
    CRITICAL = "critical"              # > 50% risk


class AnomalyType(Enum):
    """Types of detected anomalies."""
    UNUSUAL_VOLUME = "unusual_volume"  # API call volume spike
    UNUSUAL_PATTERN = "unusual_pattern"  # Non-standard usage pattern
    FAILED_AUTH = "failed_auth"        # Multiple failed logins
    PRIVILEGE_ESCALATION = "privilege_escalation"  # Unauthorized access attempt
    DATA_EXFILTRATION = "data_exfiltration"  # Large data access
    TIME_ANOMALY = "time_anomaly"      # Access outside normal hours
    GEOGRAPHIC_ANOMALY = "geographic_anomaly"  # Access from new location


class InsiderThreatIndicator(Enum):
    """Insider threat signals."""
    EXCESSIVE_DOWNLOADS = "excessive_downloads"  # Downloading unusual amounts
    PRIVILEGE_ABUSE = "privilege_abuse"  # Using admin access for personal data
    OFF_HOURS_ACCESS = "off_hours_access"  # Access outside work hours
    TERMINATED_EMPLOYEE = "terminated_employee"  # Post-termination activity
    MASS_EXPORT = "mass_export"        # Exporting customer/proprietary data
    FAILED_LOGIN_ATTEMPTS = "failed_login"  # Brute force attempts


class DDoSAttackType(Enum):
    """Types of DDoS attacks."""
    VOLUMETRIC = "volumetric"          # High bandwidth consumption
    PROTOCOL = "protocol"              # Protocol exploitation (SYN flood)
    APPLICATION = "application"        # Application-layer attacks (HTTP floods)
    SLOWLORIS = "slowloris"            # Slow connection attacks


class SecurityEvent:
    """Individual security event."""
    
    def __init__(self, event_id: str, timestamp: datetime, 
                 user_id: str, event_type: str):
        self.event_id = event_id
        self.timestamp = timestamp
        self.user_id = user_id
        self.event_type = event_type
        self.metadata: Dict = {}
        self.severity = ThreatLevel.LOW
    
    def to_dict(self) -> Dict:
        return {
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'event_type': self.event_type,
            'severity': self.severity.value,
            'metadata': self.metadata,
        }


class AnomalyDetector:
    """AI-powered anomaly detection using statistical analysis."""
    
    def __init__(self, baseline_window_days: int = 30):
        self.baseline_window_days = baseline_window_days
        self.user_baselines: Dict[str, Dict] = {}
        self.events: List[SecurityEvent] = []
    
    def record_event(self, event: SecurityEvent) -> None:
        """Record security event for analysis."""
        self.events.append(event)
    
    def build_baseline(self, user_id: str) -> Dict:
        """Build baseline behavior profile for user."""
        cutoff = datetime.utcnow() - timedelta(days=self.baseline_window_days)
        
        user_events = [e for e in self.events 
                      if e.user_id == user_id and e.timestamp >= cutoff]
        
        if not user_events:
            return {}
        
        api_calls = [e.metadata.get('api_calls', 0) for e in user_events]
        response_times = [e.metadata.get('response_time_ms', 0) for e in user_events]
        
        baseline = {
            'user_id': user_id,
            'avg_api_calls': statistics.mean(api_calls) if api_calls else 0,
            'std_api_calls': statistics.stdev(api_calls) if len(api_calls) > 1 else 0,
            'avg_response_time': statistics.mean(response_times) if response_times else 0,
            'events_per_day': len(user_events) / max(1, self.baseline_window_days),
            'common_hours': self._get_common_hours(user_events),
            'common_locations': self._get_common_locations(user_events),
        }
        
        self.user_baselines[user_id] = baseline
        return baseline
    
    def _get_common_hours(self, events: List[SecurityEvent]) -> List[int]:
        """Get typical access hours."""
        hours = defaultdict(int)
        for event in events:
            hour = event.timestamp.hour
            hours[hour] += 1
        
        return sorted(hours.items(), key=lambda x: x[1], reverse=True)[:3]
    
    def _get_common_locations(self, events: List[SecurityEvent]) -> Set[str]:
        """Get typical access locations."""
        locations = set()
        for event in events:
            if 'location' in event.metadata:
                locations.add(event.metadata['location'])
        return locations
    
    def detect_anomalies(self, user_id: str) -> List[Tuple[AnomalyType, float]]:
        """Detect anomalies for user (0-100 risk score)."""
        anomalies = []
        
        if user_id not in self.user_baselines:
            self.build_baseline(user_id)
        
        baseline = self.user_baselines.get(user_id, {})
        
        cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_events = [e for e in self.events 
                        if e.user_id == user_id and e.timestamp >= cutoff]
        
        if not recent_events:
            return anomalies
        
        recent_api_calls = sum(e.metadata.get('api_calls', 0) for e in recent_events)
        if baseline.get('std_api_calls', 0) > 0:
            z_score = abs((recent_api_calls - baseline['avg_api_calls']) / baseline['std_api_calls'])
            if z_score > 3:
                risk = min(100, z_score * 20)
                anomalies.append((AnomalyType.UNUSUAL_VOLUME, risk))
        
        for event in recent_events:
            hour = event.timestamp.hour
            common_hours = [h for h, _ in baseline.get('common_hours', [])]
            if hour not in common_hours:
                anomalies.append((AnomalyType.TIME_ANOMALY, 35.0))
                break
        
        current_locations = set(e.metadata.get('location', '') for e in recent_events)
        common_locations = baseline.get('common_locations', set())
        if current_locations and common_locations:
            if not current_locations.intersection(common_locations):
                anomalies.append((AnomalyType.GEOGRAPHIC_ANOMALY, 40.0))
        
        failed_auths = sum(1 for e in recent_events if 'failed_auth' in e.event_type)
        if failed_auths > 5:
            anomalies.append((AnomalyType.FAILED_AUTH, min(100, failed_auths * 10)))
        
        return anomalies


class InsiderThreatDetector:
    """Detect insider threat indicators."""
    
    def __init__(self):
        self.user_indicators: Dict[str, List[InsiderThreatIndicator]] = defaultdict(list)
        self.alert_history: List[Dict] = []
    
    def analyze_user(self, user_id: str, activity: Dict) -> List[InsiderThreatIndicator]:
        """Analyze user activity for insider threat signals."""
        indicators = []
        
        if activity.get('downloads_gb', 0) > 50:
            indicators.append(InsiderThreatIndicator.EXCESSIVE_DOWNLOADS)
        
        if activity.get('admin_actions', 0) > 100 and activity.get('user_type') == 'regular_user':
            indicators.append(InsiderThreatIndicator.PRIVILEGE_ABUSE)
        
        if activity.get('off_hours_access_pct', 0) > 60:
            indicators.append(InsiderThreatIndicator.OFF_HOURS_ACCESS)
        
        if activity.get('exports_count', 0) > 20 or activity.get('export_size_gb', 0) > 10:
            indicators.append(InsiderThreatIndicator.MASS_EXPORT)
        
        if activity.get('failed_logins', 0) > 10:
            indicators.append(InsiderThreatIndicator.FAILED_LOGIN_ATTEMPTS)
        
        if activity.get('is_terminated', False) and activity.get('post_termination_access', False):
            indicators.append(InsiderThreatIndicator.TERMINATED_EMPLOYEE)
        
        self.user_indicators[user_id] = indicators
        return indicators
    
    def calculate_insider_threat_score(self, user_id: str) -> float:
        """Calculate insider threat risk (0-100)."""
        indicators = self.user_indicators.get(user_id, [])
        
        if not indicators:
            return 0.0
        
        weights = {
            InsiderThreatIndicator.EXCESSIVE_DOWNLOADS: 20,
            InsiderThreatIndicator.PRIVILEGE_ABUSE: 25,
            InsiderThreatIndicator.OFF_HOURS_ACCESS: 15,
            InsiderThreatIndicator.MASS_EXPORT: 30,
            InsiderThreatIndicator.FAILED_LOGIN_ATTEMPTS: 20,
            InsiderThreatIndicator.TERMINATED_EMPLOYEE: 100,
        }
        
        score = sum(weights.get(ind, 0) for ind in indicators)
        return min(100, score)
    
    def get_risk_profile(self, user_id: str) -> Dict:
        """Get complete insider threat risk profile."""
        indicators = self.user_indicators.get(user_id, [])
        score = self.calculate_insider_threat_score(user_id)
        
        return {
            'user_id': user_id,
            'risk_score': score,
            'risk_level': (
                ThreatLevel.CRITICAL if score > 50 else
                ThreatLevel.HIGH if score > 25 else
                ThreatLevel.MEDIUM if score > 10 else
                ThreatLevel.LOW
            ).value,
            'indicators': [ind.value for ind in indicators],
            'indicator_count': len(indicators),
        }


class DDoSDetector:
    """Detect and classify DDoS attacks."""
    
    def __init__(self, request_window_seconds: int = 60):
        self.request_window_seconds = request_window_seconds
        self.request_history: List[Dict] = []
        self.blocked_ips: Set[str] = set()
    
    def record_request(self, ip_address: str, timestamp: datetime, 
                      bytes_received: int, endpoint: str) -> None:
        """Record incoming request."""
        self.request_history.append({
            'ip': ip_address,
            'timestamp': timestamp,
            'bytes': bytes_received,
            'endpoint': endpoint,
        })
    
    def detect_volumetric_attack(self) -> Tuple[bool, float]:
        """Detect volumetric DDoS (high bandwidth)."""
        cutoff = datetime.utcnow() - timedelta(seconds=self.request_window_seconds)
        recent = [r for r in self.request_history if r['timestamp'] >= cutoff]
        
        if not recent:
            return False, 0.0
        
        total_bytes = sum(r['bytes'] for r in recent)
        requests_per_sec = len(recent) / max(1, self.request_window_seconds)
        bytes_per_sec = total_bytes / max(1, self.request_window_seconds)
        
        if bytes_per_sec > 100 * 1024 * 1024 or requests_per_sec > 10000:
            risk = min(100, (bytes_per_sec / (100 * 1024 * 1024)) * 50)
            return True, risk
        
        return False, 0.0
    
    def detect_protocol_attack(self) -> Tuple[bool, float]:
        """Detect protocol-level DDoS (SYN flood, etc)."""
        cutoff = datetime.utcnow() - timedelta(seconds=self.request_window_seconds)
        recent = [r for r in self.request_history if r['timestamp'] >= cutoff]
        
        if not recent:
            return False, 0.0
        
        ip_counts = defaultdict(int)
        for r in recent:
            ip_counts[r['ip']] += 1
        
        max_ip_requests = max(ip_counts.values()) if ip_counts else 0
        
        if max_ip_requests > 1000:
            risk = min(100, (max_ip_requests / 1000) * 80)
            return True, risk
        
        return False, 0.0
    
    def detect_application_attack(self) -> Tuple[bool, float]:
        """Detect application-layer DDoS (HTTP floods)."""
        cutoff = datetime.utcnow() - timedelta(seconds=self.request_window_seconds)
        recent = [r for r in self.request_history if r['timestamp'] >= cutoff]
        
        if not recent:
            return False, 0.0
        
        endpoint_counts = defaultdict(int)
        for r in recent:
            endpoint_counts[r['endpoint']] += 1
        
        max_endpoint_requests = max(endpoint_counts.values()) if endpoint_counts else 0
        
        if max_endpoint_requests > 500:
            risk = min(100, (max_endpoint_requests / 500) * 70)
            return True, risk
        
        return False, 0.0
    
    def should_block_ip(self, ip_address: str) -> bool:
        """Determine if IP should be blocked."""
        cutoff = datetime.utcnow() - timedelta(seconds=self.request_window_seconds)
        ip_requests = [r for r in self.request_history 
                      if r['ip'] == ip_address and r['timestamp'] >= cutoff]
        
        return len(ip_requests) > 500
    
    def get_ddos_status(self) -> Dict:
        """Get current DDoS status."""
        volumetric_attack, vol_risk = self.detect_volumetric_attack()
        protocol_attack, proto_risk = self.detect_protocol_attack()
        app_attack, app_risk = self.detect_application_attack()
        
        max_risk = max(vol_risk, proto_risk, app_risk)
        
        return {
            'under_attack': volumetric_attack or protocol_attack or app_attack,
            'attack_types': {
                'volumetric': volumetric_attack,
                'protocol': protocol_attack,
                'application': app_attack,
            },
            'risk_scores': {
                'volumetric': vol_risk,
                'protocol': proto_risk,
                'application': app_risk,
            },
            'max_risk': max_risk,
            'blocked_ips': list(self.blocked_ips),
            'request_count_1min': len([r for r in self.request_history 
                                      if r['timestamp'] >= datetime.utcnow() - timedelta(minutes=1)]),
        }


class ThreatIntelligence:
    """Aggregate threats and generate actionable intelligence."""
    
    def __init__(self):
        self.anomaly_detector = AnomalyDetector()
        self.insider_detector = InsiderThreatDetector()
        self.ddos_detector = DDoSDetector()
        self.alerts: List[Dict] = []
    
    def scan_user(self, user_id: str, activity: Dict) -> Dict:
        """Comprehensive threat scan for user."""
        
        insider_indicators = self.insider_detector.analyze_user(user_id, activity)
        insider_profile = self.insider_detector.get_risk_profile(user_id)
        
        anomalies = self.anomaly_detector.detect_anomalies(user_id)
        anomaly_risk = max((risk for _, risk in anomalies), default=0)
        
        combined_risk = max(insider_profile['risk_score'], anomaly_risk)
        
        threat_level = (
            ThreatLevel.CRITICAL if combined_risk > 50 else
            ThreatLevel.HIGH if combined_risk > 25 else
            ThreatLevel.MEDIUM if combined_risk > 10 else
            ThreatLevel.LOW
        )
        
        result = {
            'user_id': user_id,
            'threat_level': threat_level.value,
            'combined_risk_score': combined_risk,
            'insider_profile': insider_profile,
            'anomalies': [{'type': a.value, 'risk': r} for a, r in anomalies],
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            self.alerts.append(result)
        
        return result
    
    def get_threat_summary(self) -> Dict:
        """Get overall threat summary."""
        return {
            'total_alerts': len(self.alerts),
            'critical_threats': len([a for a in self.alerts if a['threat_level'] == 'critical']),
            'high_threats': len([a for a in self.alerts if a['threat_level'] == 'high']),
            'recent_alerts': self.alerts[-10:],
        }
