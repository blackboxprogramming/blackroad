"""
Enterprise Cost Optimization System
Cloud resource consolidation, right-sizing, and commitment management
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json


class ResourceType(Enum):
    """Cloud resource types."""
    COMPUTE = "compute"           # EC2, VMs
    STORAGE = "storage"           # S3, disks
    NETWORK = "network"           # Data transfer
    DATABASE = "database"         # RDS, managed DB
    CACHE = "cache"              # ElastiCache, Redis
    LOAD_BALANCER = "lb"         # ALB, NLB


class UtilizationTier(Enum):
    """Resource utilization levels."""
    CRITICAL_WASTE = "critical_waste"    # <5% utilization
    SEVERE_WASTE = "severe_waste"        # 5-15% utilization
    SIGNIFICANT_WASTE = "significant_waste"  # 15-30% utilization
    MODERATE_WASTE = "moderate_waste"    # 30-50% utilization
    OPTIMIZED = "optimized"              # >70% utilization


class CapacityCommitment(Enum):
    """Cloud capacity commitment options."""
    ON_DEMAND = "on_demand"              # Pay-as-you-go
    ONE_YEAR_RESERVED = "1yr_reserved"   # 1-year RI
    THREE_YEAR_RESERVED = "3yr_reserved" # 3-year RI
    SPOT = "spot"                        # Spot instances


class CloudResource:
    """Track individual cloud resource."""
    
    def __init__(self, resource_id: str, resource_type: ResourceType,
                 region: str, hourly_cost: float):
        self.resource_id = resource_id
        self.type = resource_type
        self.region = region
        self.hourly_cost = hourly_cost
        self.daily_cost = hourly_cost * 24
        self.monthly_cost = hourly_cost * 24 * 30
        self.annual_cost = hourly_cost * 24 * 365
        
        self.metrics = {
            'cpu_utilization': 0.0,
            'memory_utilization': 0.0,
            'network_throughput': 0.0,
            'disk_io': 0.0,
            'age_days': 0,
        }
        
        self.commitment = CapacityCommitment.ON_DEMAND
        self.created_at = datetime.utcnow().isoformat()
    
    def update_metrics(self, metrics: Dict[str, float]) -> None:
        """Update resource metrics."""
        self.metrics.update(metrics)
    
    def get_average_utilization(self) -> float:
        """Calculate average utilization percentage."""
        util_metrics = ['cpu_utilization', 'memory_utilization', 'network_throughput']
        values = [self.metrics.get(m, 0) for m in util_metrics]
        return sum(values) / len(values) if values else 0
    
    def get_waste_tier(self) -> UtilizationTier:
        """Determine if resource is being wasted."""
        util = self.get_average_utilization()
        
        if util < 5:
            return UtilizationTier.CRITICAL_WASTE
        elif util < 15:
            return UtilizationTier.SEVERE_WASTE
        elif util < 30:
            return UtilizationTier.SIGNIFICANT_WASTE
        elif util < 50:
            return UtilizationTier.MODERATE_WASTE
        else:
            return UtilizationTier.OPTIMIZED
    
    def to_dict(self) -> Dict:
        """Export resource."""
        return {
            'resource_id': self.resource_id,
            'type': self.type.value,
            'region': self.region,
            'hourly_cost': self.hourly_cost,
            'monthly_cost': self.monthly_cost,
            'annual_cost': self.annual_cost,
            'utilization': self.get_average_utilization(),
            'waste_tier': self.get_waste_tier().value,
            'metrics': self.metrics,
            'commitment': self.commitment.value,
        }


class CostAnalyzer:
    """Analyze cloud costs and identify optimization opportunities."""
    
    def __init__(self):
        self.resources: Dict[str, CloudResource] = {}
        self.historical_costs: List[Dict] = []
    
    def add_resource(self, resource: CloudResource) -> str:
        """Add resource to analyze."""
        self.resources[resource.resource_id] = resource
        return resource.resource_id
    
    def get_total_monthly_cost(self) -> float:
        """Calculate total monthly costs."""
        return sum(r.monthly_cost for r in self.resources.values())
    
    def get_total_annual_cost(self) -> float:
        """Calculate total annual costs."""
        return sum(r.annual_cost for r in self.resources.values())
    
    def get_costs_by_region(self) -> Dict[str, float]:
        """Break down costs by region."""
        by_region = {}
        for resource in self.resources.values():
            by_region[resource.region] = by_region.get(resource.region, 0) + resource.monthly_cost
        return by_region
    
    def get_costs_by_type(self) -> Dict[str, float]:
        """Break down costs by resource type."""
        by_type = {}
        for resource in self.resources.values():
            rtype = resource.type.value
            by_type[rtype] = by_type.get(rtype, 0) + resource.monthly_cost
        return by_type
    
    def find_underutilized_resources(self, threshold: float = 50.0) -> List[Dict]:
        """Find resources below utilization threshold."""
        underutilized = []
        for resource in self.resources.values():
            if resource.get_average_utilization() < threshold:
                underutilized.append({
                    'resource_id': resource.resource_id,
                    'type': resource.type.value,
                    'region': resource.region,
                    'utilization': resource.get_average_utilization(),
                    'monthly_cost': resource.monthly_cost,
                    'annual_cost': resource.annual_cost,
                    'waste_tier': resource.get_waste_tier().value,
                })
        
        return sorted(underutilized, key=lambda x: x['annual_cost'], reverse=True)
    
    def find_consolidation_opportunities(self) -> List[Dict]:
        """Find resources that can be consolidated."""
        opportunities = []
        
        # Group by region and type
        by_region_type = {}
        for resource in self.resources.values():
            key = (resource.region, resource.type.value)
            if key not in by_region_type:
                by_region_type[key] = []
            by_region_type[key].append(resource)
        
        # Find groups with low utilization that could consolidate
        for (region, rtype), resources in by_region_type.items():
            if len(resources) >= 2:
                total_util = sum(r.get_average_utilization() for r in resources) / len(resources)
                total_cost = sum(r.monthly_cost for r in resources)
                
                if total_util < 60:  # Consolidation opportunity
                    # Estimate savings by consolidating to larger instance
                    estimated_savings = total_cost * 0.30  # 30% savings estimate
                    
                    opportunities.append({
                        'region': region,
                        'type': rtype,
                        'resource_count': len(resources),
                        'average_utilization': total_util,
                        'current_monthly_cost': total_cost,
                        'estimated_monthly_cost': total_cost - estimated_savings,
                        'estimated_monthly_savings': estimated_savings,
                        'estimated_annual_savings': estimated_savings * 12,
                        'resources': [r.resource_id for r in resources],
                    })
        
        return sorted(opportunities, key=lambda x: x['estimated_annual_savings'], reverse=True)
    
    def get_cost_optimization_report(self) -> Dict:
        """Generate comprehensive cost optimization report."""
        return {
            'generated_at': datetime.utcnow().isoformat(),
            'total_resources': len(self.resources),
            'current_monthly_cost': self.get_total_monthly_cost(),
            'current_annual_cost': self.get_total_annual_cost(),
            'costs_by_region': self.get_costs_by_region(),
            'costs_by_type': self.get_costs_by_type(),
            'underutilized_resources': self.find_underutilized_resources(),
            'consolidation_opportunities': self.find_consolidation_opportunities(),
            'potential_monthly_savings': self._calculate_potential_savings(),
            'potential_annual_savings': self._calculate_potential_savings() * 12,
        }
    
    def _calculate_potential_savings(self) -> float:
        """Calculate total potential monthly savings."""
        savings = 0.0
        
        # Savings from right-sizing underutilized
        for resource in self.find_underutilized_resources(threshold=30):
            waste_tier = resource['waste_tier']
            if waste_tier == UtilizationTier.CRITICAL_WASTE.value:
                savings += resource['monthly_cost'] * 0.80  # 80% savings
            elif waste_tier == UtilizationTier.SEVERE_WASTE.value:
                savings += resource['monthly_cost'] * 0.60
            elif waste_tier == UtilizationTier.SIGNIFICANT_WASTE.value:
                savings += resource['monthly_cost'] * 0.40
        
        # Savings from consolidation
        for opportunity in self.find_consolidation_opportunities():
            savings += opportunity['estimated_monthly_savings']
        
        return savings


class RightSizingEngine:
    """Recommend optimal resource sizes."""
    
    @staticmethod
    def analyze_growth_pattern(metrics_history: List[Dict]) -> Dict:
        """Analyze resource growth pattern."""
        if not metrics_history:
            return {'trend': 'insufficient_data'}
        
        utilizations = [m.get('utilization', 0) for m in metrics_history]
        
        if not utilizations:
            return {'trend': 'no_metrics'}
        
        avg_util = sum(utilizations) / len(utilizations)
        max_util = max(utilizations)
        
        return {
            'average_utilization': avg_util,
            'peak_utilization': max_util,
            'stability': 'stable' if max_util < avg_util * 1.5 else 'variable',
            'trend': 'growing' if utilizations[-1] > utilizations[0] else 'declining',
        }
    
    @staticmethod
    def recommend_right_size(resource: CloudResource) -> Dict:
        """Recommend right-sized resource."""
        util = resource.get_average_utilization()
        waste_tier = resource.get_waste_tier()
        
        if waste_tier == UtilizationTier.OPTIMIZED:
            return {
                'current_cost': resource.monthly_cost,
                'recommendation': 'No change - optimally sized',
                'estimated_savings': 0,
            }
        
        # Calculate reduction factor based on waste tier
        reduction_factors = {
            UtilizationTier.CRITICAL_WASTE: 0.75,
            UtilizationTier.SEVERE_WASTE: 0.55,
            UtilizationTier.SIGNIFICANT_WASTE: 0.35,
            UtilizationTier.MODERATE_WASTE: 0.15,
        }
        
        reduction = reduction_factors.get(waste_tier, 0)
        recommended_cost = resource.monthly_cost * (1 - reduction)
        monthly_savings = resource.monthly_cost - recommended_cost
        
        return {
            'current_cost': resource.monthly_cost,
            'current_utilization': util,
            'waste_tier': waste_tier.value,
            'recommended_cost': recommended_cost,
            'estimated_monthly_savings': monthly_savings,
            'estimated_annual_savings': monthly_savings * 12,
            'recommendation': f"Reduce to {int((1-reduction)*100)}% of current size",
        }


class CommitmentOptimizer:
    """Optimize reserved capacity commitments."""
    
    def __init__(self, discount_rates: Optional[Dict] = None):
        self.discount_rates = discount_rates or {
            '1yr_reserved': 0.30,   # 30% discount
            '3yr_reserved': 0.60,   # 60% discount
        }
    
    def recommend_commitment(self, resource: CloudResource,
                            usage_prediction: float = 0.95) -> Dict:
        """Recommend commitment level."""
        
        if resource.get_average_utilization() < 20:
            return {
                'resource_id': resource.resource_id,
                'recommendation': 'on_demand',
                'reasoning': 'Low utilization - keep flexible',
                'monthly_cost_on_demand': resource.monthly_cost,
                'monthly_cost_reserved': 'N/A',
            }
        
        # Calculate costs for different commitment levels
        on_demand_monthly = resource.monthly_cost
        reserved_1yr_monthly = on_demand_monthly * (1 - self.discount_rates['1yr_reserved']) / 12
        reserved_3yr_monthly = on_demand_monthly * (1 - self.discount_rates['3yr_reserved']) / 36
        
        if usage_prediction > 0.9:
            recommendation = '3yr_reserved'
            monthly_cost = reserved_3yr_monthly
            discount = self.discount_rates['3yr_reserved']
        elif usage_prediction > 0.7:
            recommendation = '1yr_reserved'
            monthly_cost = reserved_1yr_monthly
            discount = self.discount_rates['1yr_reserved']
        else:
            recommendation = 'spot'
            monthly_cost = on_demand_monthly * 0.70
            discount = 0.30
        
        monthly_savings = on_demand_monthly - monthly_cost
        
        return {
            'resource_id': resource.resource_id,
            'current_commitment': resource.commitment.value,
            'recommended_commitment': recommendation,
            'monthly_cost_on_demand': on_demand_monthly,
            'monthly_cost_recommended': monthly_cost,
            'estimated_monthly_savings': monthly_savings,
            'estimated_annual_savings': monthly_savings * 12,
            'discount_percentage': int(discount * 100),
        }


class CapacityForecaster:
    """Forecast cloud capacity needs."""
    
    def __init__(self):
        self.forecast_data: List[Dict] = []
    
    def forecast_usage(self, historical_metrics: List[Dict],
                      months_ahead: int = 12) -> List[Dict]:
        """Forecast usage for next N months."""
        
        if not historical_metrics or len(historical_metrics) < 3:
            return []
        
        forecasts = []
        
        # Simple linear regression
        x_values = list(range(len(historical_metrics)))
        y_values = [m.get('utilization', 0) for m in historical_metrics]
        
        n = len(x_values)
        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n
        
        numerator = sum((x_values[i] - x_mean) * (y_values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean
        
        for month in range(1, months_ahead + 1):
            projected_util = intercept + slope * (n + month - 1)
            projected_util = max(0, min(100, projected_util))  # Clamp to 0-100
            
            forecasts.append({
                'month': month,
                'projected_utilization': projected_util,
                'projected_cost': 0,  # Will be calculated per resource
                'timestamp': (datetime.utcnow() + timedelta(days=30*month)).isoformat(),
            })
        
        self.forecast_data = forecasts
        return forecasts
    
    def get_capacity_needs(self, forecasts: List[Dict]) -> Dict:
        """Determine capacity needs based on forecasts."""
        if not forecasts:
            return {}
        
        utilizations = [f['projected_utilization'] for f in forecasts]
        max_forecast = max(utilizations)
        avg_forecast = sum(utilizations) / len(utilizations)
        
        return {
            'average_utilization': avg_forecast,
            'peak_utilization': max_forecast,
            'buffer_recommendation': '20%',  # Recommend 20% capacity buffer
            'recommended_peak_capacity': max_forecast * 1.2,
        }
