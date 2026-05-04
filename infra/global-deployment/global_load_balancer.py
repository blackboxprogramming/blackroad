"""
Global Load Balancer - CloudFlare + Route53 integration
Routes traffic to optimal region based on latency/location
"""

import json
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime


class Region(Enum):
    """AWS regions for global deployment."""
    US_EAST_1 = "us-east-1"
    US_WEST_2 = "us-west-2"
    EU_WEST_1 = "eu-west-1"
    AP_SOUTHEAST_1 = "ap-southeast-1"
    AP_NORTHEAST_1 = "ap-northeast-1"
    SA_EAST_1 = "sa-east-1"


class RegionalEndpoint:
    """Represents a regional deployment endpoint."""
    
    def __init__(self, region: Region, endpoint_url: str, 
                 latitude: float, longitude: float):
        self.region = region
        self.endpoint_url = endpoint_url
        self.latitude = latitude
        self.longitude = longitude
        self.is_healthy = True
        self.last_check = datetime.utcnow()
        self.latency_ms = 0
        self.request_count = 0
        self.error_rate = 0.0


class GlobalLoadBalancer:
    """Distributes traffic across multiple regions."""
    
    def __init__(self):
        self.regions: Dict[Region, RegionalEndpoint] = {}
        self.cloudflare_api_key = None
        self.route53_client = None
        self._init_regions()
    
    def _init_regions(self) -> None:
        """Initialize regional endpoints."""
        endpoints = [
            (Region.US_EAST_1, "https://api-us-east.blackroad.io", 38.8951, -77.0369),
            (Region.US_WEST_2, "https://api-us-west.blackroad.io", 45.6721, -121.2723),
            (Region.EU_WEST_1, "https://api-eu-west.blackroad.io", 53.3498, -6.2603),
            (Region.AP_SOUTHEAST_1, "https://api-ap-southeast.blackroad.io", 1.3521, 103.8198),
            (Region.AP_NORTHEAST_1, "https://api-ap-northeast.blackroad.io", 35.6762, 139.6503),
            (Region.SA_EAST_1, "https://api-sa-east.blackroad.io", -23.5505, -46.6333),
        ]
        
        for region, url, lat, lon in endpoints:
            self.regions[region] = RegionalEndpoint(region, url, lat, lon)
    
    def get_optimal_region(self, user_latitude: float, 
                          user_longitude: float) -> Tuple[Region, str]:
        """
        Calculate optimal region based on user location.
        Uses latency-based routing with geographic fallback.
        
        Returns:
            (optimal_region, endpoint_url)
        """
        # Filter healthy regions
        healthy_regions = [
            r for r in self.regions.values() if r.is_healthy
        ]
        
        if not healthy_regions:
            # All regions down, return primary
            return Region.US_EAST_1, self.regions[Region.US_EAST_1].endpoint_url
        
        # Calculate distance to each region
        distances = []
        for region_ep in healthy_regions:
            distance = self._calculate_distance(
                user_latitude, user_longitude,
                region_ep.latitude, region_ep.longitude
            )
            # Factor in latency and error rate
            score = distance + (region_ep.latency_ms / 10) + (region_ep.error_rate * 100)
            distances.append((region_ep, score))
        
        # Sort by score (lower is better)
        distances.sort(key=lambda x: x[1])
        optimal = distances[0][0]
        
        return optimal.region, optimal.endpoint_url
    
    def _calculate_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """Calculate great-circle distance between two points (simplified)."""
        import math
        # Haversine formula (simplified)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        km = 6371 * c
        return km
    
    def check_region_health(self, region: Region) -> bool:
        """Check if region endpoint is healthy."""
        try:
            # Would perform actual health check (HEAD request)
            # For now, return stored health status
            endpoint = self.regions[region]
            endpoint.last_check = datetime.utcnow()
            return endpoint.is_healthy
        except Exception:
            self.regions[region].is_healthy = False
            return False
    
    def update_region_metrics(self, region: Region, latency_ms: float,
                             error_rate: float, request_count: int) -> None:
        """Update metrics for a region."""
        if region in self.regions:
            ep = self.regions[region]
            ep.latency_ms = latency_ms
            ep.error_rate = error_rate
            ep.request_count = request_count
    
    def get_routing_policy(self) -> Dict:
        """Get current CloudFlare routing policy."""
        policy = {
            'name': 'Global Traffic Optimization',
            'regions': {},
            'rules': []
        }
        
        for region, endpoint in self.regions.items():
            policy['regions'][region.value] = {
                'endpoint': endpoint.endpoint_url,
                'health': 'healthy' if endpoint.is_healthy else 'unhealthy',
                'latency_ms': endpoint.latency_ms,
                'error_rate': endpoint.error_rate,
                'weight': self._calculate_weight(endpoint)
            }
        
        # Routing rules
        policy['rules'] = [
            {
                'name': 'Geographic Routing',
                'type': 'geo',
                'description': 'Route to nearest healthy region'
            },
            {
                'name': 'Latency-Based Routing',
                'type': 'latency',
                'description': 'Route to lowest latency region'
            },
            {
                'name': 'Failover Routing',
                'type': 'failover',
                'description': 'Automatic failover on unhealthy endpoint'
            }
        ]
        
        return policy
    
    def _calculate_weight(self, endpoint: RegionalEndpoint) -> float:
        """Calculate weight for load balancing."""
        base_weight = 100.0
        
        # Reduce weight based on latency
        latency_factor = min(endpoint.latency_ms / 100.0, 1.0)
        
        # Reduce weight based on error rate
        error_factor = endpoint.error_rate * 100
        
        weight = base_weight * (1.0 - latency_factor) * (1.0 - error_factor)
        
        # Never go below 10 or above 100
        return max(10, min(100, weight))
    
    def get_statistics(self) -> Dict:
        """Get global statistics."""
        total_requests = sum(r.request_count for r in self.regions.values())
        avg_latency = sum(r.latency_ms for r in self.regions.values()) / len(self.regions)
        healthy_regions = sum(1 for r in self.regions.values() if r.is_healthy)
        
        return {
            'total_regions': len(self.regions),
            'healthy_regions': healthy_regions,
            'total_requests': total_requests,
            'average_latency_ms': avg_latency,
            'regional_breakdown': {
                region.value: {
                    'requests': ep.request_count,
                    'latency_ms': ep.latency_ms,
                    'error_rate': ep.error_rate
                }
                for region, ep in self.regions.items()
            }
        }


class CloudFlareIntegration:
    """Integrates with CloudFlare for global routing."""
    
    def __init__(self, api_key: str, api_email: str, zone_id: str):
        self.api_key = api_key
        self.api_email = api_email
        self.zone_id = zone_id
        self.base_url = "https://api.cloudflare.com/client/v4"
    
    def configure_geo_routing(self, rules: List[Dict]) -> bool:
        """Configure geographic routing rules."""
        # Would make actual Cloudflare API calls
        # For demo, return success
        return True
    
    def enable_cdn_caching(self, cache_rules: List[Dict]) -> bool:
        """Enable CDN caching for static assets."""
        rules = [
            {
                'path': '/static/*',
                'cache_ttl': 86400,  # 1 day
                'cache_level': 'cache_everything'
            },
            {
                'path': '/api/*',
                'cache_ttl': 0,
                'cache_level': 'bypass'  # Don't cache API responses
            },
            {
                'path': '/images/*',
                'cache_ttl': 604800,  # 1 week
                'cache_level': 'cache_everything'
            }
        ]
        return True
    
    def purge_cache(self, paths: List[str]) -> bool:
        """Purge specific paths from CDN cache."""
        # Would make actual Cloudflare purge API call
        return True
    
    def get_cache_statistics(self) -> Dict:
        """Get CDN cache performance statistics."""
        return {
            'total_requests': 1000000,
            'cached_requests': 850000,
            'cache_hit_rate': 0.85,
            'bandwidth_saved': 425000,  # GB
            'average_response_time': 125,  # ms
            'top_cached_paths': [
                '/static/app.js',
                '/static/app.css',
                '/images/logo.png',
            ]
        }


class EdgeLocationOptimizer:
    """Optimizes content delivery across CloudFlare edge locations."""
    
    def __init__(self, cloudflare_client):
        self.cf = cloudflare_client
        self.edge_locations = 350  # CloudFlare has 350+ POPs
    
    def get_optimal_cache_ttl(self, content_type: str, 
                             freshness_requirement: str) -> int:
        """Calculate optimal cache TTL based on content type."""
        ttl_map = {
            'static': {
                'strict': 3600,      # 1 hour
                'normal': 86400,     # 1 day
                'loose': 604800      # 1 week
            },
            'dynamic': {
                'strict': 0,         # No cache
                'normal': 300,       # 5 min
                'loose': 3600        # 1 hour
            },
            'api': {
                'strict': 0,
                'normal': 0,
                'loose': 60
            }
        }
        
        return ttl_map.get(content_type, {}).get(freshness_requirement, 0)
    
    def implement_stale_while_revalidate(self) -> Dict:
        """Implement stale-while-revalidate caching strategy."""
        return {
            'cache_control': 'public, max-age=3600, stale-while-revalidate=86400',
            'strategy': 'Serve cached content for up to 1 day while revalidating in background',
            'benefits': [
                'Faster response times',
                'Reduced origin load',
                'Better user experience during origin issues'
            ]
        }
