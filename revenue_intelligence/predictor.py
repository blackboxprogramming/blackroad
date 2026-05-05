"""
Advanced Revenue Intelligence System
Customer lifetime value prediction and monetization optimization
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json


class CustomerSegment(Enum):
    """Customer segmentation."""
    ENTERPRISE = "enterprise"          # $100K+/year ARR
    MID_MARKET = "mid_market"          # $10K-$100K/year ARR
    SMB = "smb"                        # $1K-$10K/year ARR
    STARTUP = "startup"                # < $1K/year ARR
    FREEMIUM = "freemium"              # Free users


class ChurnRiskLevel(Enum):
    """Churn risk classification."""
    LOW = "low"                        # < 5% risk
    MEDIUM = "medium"                  # 5-20% risk
    HIGH = "high"                      # 20-50% risk
    CRITICAL = "critical"              # > 50% risk


class ExpansionOpportunity(Enum):
    """Types of expansion opportunities."""
    UPGRADE = "upgrade"                # Upgrade to higher tier
    ADD_ON = "add_on"                  # Add feature/product
    CROSS_SELL = "cross_sell"          # Different product
    UPSELL = "upsell"                  # More seats/usage
    RETENTION = "retention"            # At-risk, needs love


class Customer:
    """Track customer metrics for LTV prediction."""
    
    def __init__(self, customer_id: str, company_name: str,
                 acquisition_date: datetime):
        self.customer_id = customer_id
        self.company_name = company_name
        self.acquisition_date = acquisition_date.isoformat()
        
        self.metrics = {
            'mrr': 0,                       # Monthly Recurring Revenue
            'arr': 0,                       # Annual Recurring Revenue
            'usage_score': 0.0,             # 0-100 engagement
            'support_tickets': 0,
            'nps': 0,                       # Net Promoter Score
            'feature_adoption': 0.0,        # % features used
            'api_calls_daily': 0,
            'seats': 1,
            'months_active': 0,
        }
        
        self.segment = CustomerSegment.STARTUP
        self.churn_risk = ChurnRiskLevel.LOW
        self.ltv = 0.0
        self.expansion_opportunities: List[str] = []
    
    def update_metrics(self, metrics: Dict) -> None:
        """Update customer metrics."""
        self.metrics.update(metrics)
        
        # Update segment based on ARR
        arr = metrics.get('arr', 0)
        if arr >= 100000:
            self.segment = CustomerSegment.ENTERPRISE
        elif arr >= 10000:
            self.segment = CustomerSegment.MID_MARKET
        elif arr >= 1000:
            self.segment = CustomerSegment.SMB
        elif arr > 0:
            self.segment = CustomerSegment.STARTUP
        else:
            self.segment = CustomerSegment.FREEMIUM
    
    def to_dict(self) -> Dict:
        """Export customer."""
        return {
            'customer_id': self.customer_id,
            'company_name': self.company_name,
            'segment': self.segment.value,
            'metrics': self.metrics,
            'churn_risk': self.churn_risk.value,
            'ltv': self.ltv,
            'opportunities': self.expansion_opportunities,
        }


class LTVPredictor:
    """Predict Customer Lifetime Value."""
    
    def __init__(self):
        self.customers: Dict[str, Customer] = {}
        self.historical_churn: List[Dict] = []
    
    def add_customer(self, customer: Customer) -> str:
        """Add customer for LTV calculation."""
        self.customers[customer.customer_id] = customer
        return customer.customer_id
    
    def calculate_ltv(self, customer_id: str) -> float:
        """Calculate LTV using cohort analysis."""
        customer = self.customers.get(customer_id)
        if not customer:
            return 0.0
        
        mrr = customer.metrics.get('mrr', 0)
        margin = 0.70  # 70% gross margin assumption
        
        # Calculate retention based on segment
        retention_rates = {
            CustomerSegment.ENTERPRISE: 0.98,
            CustomerSegment.MID_MARKET: 0.95,
            CustomerSegment.SMB: 0.92,
            CustomerSegment.STARTUP: 0.85,
            CustomerSegment.FREEMIUM: 0.60,
        }
        
        monthly_retention = retention_rates.get(customer.segment, 0.85)
        
        # Calculate churn rate (1 - retention)
        monthly_churn = 1 - monthly_retention
        
        # LTV = (MRR * Margin) / Monthly Churn
        if monthly_churn > 0:
            ltv = (mrr * margin) / monthly_churn
        else:
            ltv = mrr * margin * 120  # 10 year assumption
        
        customer.ltv = ltv
        return ltv
    
    def predict_churn_risk(self, customer_id: str) -> Tuple[ChurnRiskLevel, float]:
        """Predict churn risk (0-100%)."""
        customer = self.customers.get(customer_id)
        if not customer:
            return ChurnRiskLevel.LOW, 0.0
        
        risk_score = 0.0
        
        # Low usage = high risk
        usage = customer.metrics.get('usage_score', 0)
        if usage < 30:
            risk_score += 40
        elif usage < 60:
            risk_score += 20
        
        # Few feature adoption = high risk
        adoption = customer.metrics.get('feature_adoption', 0)
        if adoption < 20:
            risk_score += 30
        elif adoption < 50:
            risk_score += 15
        
        # Support tickets = engagement
        tickets = customer.metrics.get('support_tickets', 0)
        if tickets == 0:
            risk_score += 25
        elif tickets < 2:
            risk_score += 10
        
        # NPS < 0 = high risk
        nps = customer.metrics.get('nps', 0)
        if nps < 0:
            risk_score += 30
        elif nps < 30:
            risk_score += 15
        
        # Tenure: Newer customers = higher risk
        months = customer.metrics.get('months_active', 0)
        if months < 3:
            risk_score += 20
        elif months < 12:
            risk_score += 10
        
        # Cap at 100
        risk_score = min(100, risk_score)
        
        # Classify risk level
        if risk_score < 5:
            risk_level = ChurnRiskLevel.LOW
        elif risk_score < 20:
            risk_level = ChurnRiskLevel.MEDIUM
        elif risk_score < 50:
            risk_level = ChurnRiskLevel.HIGH
        else:
            risk_level = ChurnRiskLevel.CRITICAL
        
        customer.churn_risk = risk_level
        return risk_level, risk_score
    
    def get_ltv_distribution(self) -> Dict:
        """Get LTV statistics across portfolio."""
        if not self.customers:
            return {}
        
        ltvs = [self.calculate_ltv(cid) for cid in self.customers.keys()]
        
        return {
            'total_customers': len(self.customers),
            'total_ltv': sum(ltvs),
            'average_ltv': sum(ltvs) / len(ltvs) if ltvs else 0,
            'median_ltv': sorted(ltvs)[len(ltvs) // 2] if ltvs else 0,
            'max_ltv': max(ltvs) if ltvs else 0,
            'min_ltv': min(ltvs) if ltvs else 0,
        }


class ExpansionEngine:
    """Identify expansion opportunities."""
    
    def __init__(self):
        self.opportunities: List[Dict] = []
    
    def identify_opportunities(self, customer_id: str,
                              customer: Customer) -> List[Dict]:
        """Identify expansion opportunities for customer."""
        opportunities = []
        metrics = customer.metrics
        
        # Upgrade opportunity: High usage but low tier
        if (customer.segment == CustomerSegment.STARTUP and 
            metrics.get('usage_score', 0) > 70):
            opportunities.append({
                'type': ExpansionOpportunity.UPGRADE.value,
                'recommendation': 'Upgrade to SMB plan',
                'potential_mrr_increase': 1000,
                'confidence': 0.85,
                'reason': 'High usage on free plan indicates readiness',
            })
        
        # Add-on: Power users could benefit
        if (metrics.get('feature_adoption', 0) > 70 and 
            metrics.get('api_calls_daily', 0) > 100):
            opportunities.append({
                'type': ExpansionOpportunity.ADD_ON.value,
                'recommendation': 'Add API Enterprise tier',
                'potential_mrr_increase': 500,
                'confidence': 0.78,
                'reason': 'High API usage - candidate for premium tier',
            })
        
        # Upsell seats: Many API calls suggest multi-user
        if metrics.get('api_calls_daily', 0) > 1000:
            opportunities.append({
                'type': ExpansionOpportunity.UPSELL.value,
                'recommendation': f"Expand from {metrics.get('seats', 1)} to {metrics.get('seats', 1) + 5} seats",
                'potential_mrr_increase': 750,
                'confidence': 0.72,
                'reason': 'API volume suggests team growth',
            })
        
        # Retention: At-risk customers need engagement
        risk_level, risk_score = self.predict_churn_risk(customer_id, customer)
        if risk_level in [ChurnRiskLevel.HIGH, ChurnRiskLevel.CRITICAL]:
            opportunities.append({
                'type': ExpansionOpportunity.RETENTION.value,
                'recommendation': 'Proactive outreach + feature enablement',
                'potential_mrr_increase': 0,  # Defensive
                'confidence': 0.90,
                'reason': f'Churn risk {risk_score:.0f}% - requires attention',
            })
        
        self.opportunities.extend(opportunities)
        return opportunities
    
    def predict_churn_risk(self, customer_id: str, customer: Customer) -> Tuple:
        """Predict churn risk."""
        predictor = LTVPredictor()
        return predictor.predict_churn_risk(customer_id)


class DynamicPricingEngine:
    """Optimize pricing per customer segment."""
    
    def __init__(self):
        self.pricing_tiers = {
            CustomerSegment.ENTERPRISE: {
                'base': 5000,
                'unit': 50,
                'min': 5000,
                'max': 50000,
            },
            CustomerSegment.MID_MARKET: {
                'base': 1000,
                'unit': 10,
                'min': 500,
                'max': 10000,
            },
            CustomerSegment.SMB: {
                'base': 100,
                'unit': 1,
                'min': 50,
                'max': 1000,
            },
            CustomerSegment.STARTUP: {
                'base': 0,
                'unit': 0.1,
                'min': 0,
                'max': 500,
            },
            CustomerSegment.FREEMIUM: {
                'base': 0,
                'unit': 0,
                'min': 0,
                'max': 0,
            },
        }
    
    def calculate_optimal_price(self, customer: Customer,
                               feature_usage: Dict) -> Dict:
        """Calculate optimal price for customer."""
        tier = self.pricing_tiers.get(customer.segment)
        
        if not tier:
            return {'error': 'Unknown segment'}
        
        # Base price for segment
        base_price = tier['base']
        
        # Add usage-based component
        api_calls = feature_usage.get('api_calls', 0)
        seats = feature_usage.get('seats', 1)
        
        # Calculate usage price
        usage_price = (api_calls / 1000) * tier['unit'] * 30  # Normalize to monthly
        
        # Calculate seats premium
        seats_premium = (seats - 1) * (base_price * 0.20)  # 20% per additional seat
        
        # Total price
        total_price = base_price + usage_price + seats_premium
        
        # Apply elasticity: Price sensitive = lower bound, not = higher bound
        elasticity = feature_usage.get('price_elasticity', 1.0)  # 0.5-1.5 range
        total_price *= elasticity
        
        # Constrain to tier limits
        final_price = max(tier['min'], min(tier['max'], total_price))
        
        return {
            'customer_id': customer.customer_id,
            'segment': customer.segment.value,
            'base_price': base_price,
            'usage_component': usage_price,
            'seats_component': seats_premium,
            'elasticity_factor': elasticity,
            'recommended_price': final_price,
            'price_range': (tier['min'], tier['max']),
        }
    
    def get_segment_pricing(self) -> Dict:
        """Get pricing strategy per segment."""
        return {
            segment.value: self.pricing_tiers[segment]
            for segment in CustomerSegment
        }


class RevenueForecast:
    """Forecast revenue growth."""
    
    def __init__(self, customers: Dict[str, Customer]):
        self.customers = customers
    
    def forecast_mrr(self, months_ahead: int = 12) -> List[Dict]:
        """Forecast MRR growth."""
        forecasts = []
        
        # Current MRR
        current_mrr = sum(c.metrics.get('mrr', 0) for c in self.customers.values())
        
        # Growth factors
        new_customer_mrr = 150  # Average MRR of new customer
        new_customers_per_month = 3
        churn_rate = 0.08  # 8% monthly churn
        expansion_rate = 0.15  # 15% expansion from existing
        
        mrr = current_mrr
        
        for month in range(1, months_ahead + 1):
            # Add new customer revenue
            mrr += new_customers_per_month * new_customer_mrr
            
            # Apply churn
            mrr *= (1 - churn_rate)
            
            # Apply expansion
            mrr *= (1 + expansion_rate)
            
            forecasts.append({
                'month': month,
                'forecasted_mrr': mrr,
                'timestamp': (datetime.utcnow() + timedelta(days=30*month)).isoformat(),
            })
        
        return forecasts
    
    def forecast_arr(self, months_ahead: int = 12) -> Dict:
        """Forecast ARR."""
        mrr_forecast = self.forecast_mrr(months_ahead)
        
        if mrr_forecast:
            final_mrr = mrr_forecast[-1]['forecasted_mrr']
            final_arr = final_mrr * 12
        else:
            final_arr = 0
        
        current_arr = sum(c.metrics.get('arr', 0) for c in self.customers.values())
        growth_rate = 0
        if current_arr > 0:
            growth_rate = (final_arr / current_arr - 1) * 100
        
        return {
            'current_arr': current_arr,
            'forecasted_arr_12m': final_arr,
            'growth_rate': growth_rate,
            'monthly_forecasts': mrr_forecast,
        }
    
    def forecast_ltv_pool(self, months_ahead: int = 12) -> Dict:
        """Forecast total LTV pool."""
        predictor = LTVPredictor()
        predictor.customers = self.customers
        
        current_ltv_pool = sum(predictor.calculate_ltv(cid) for cid in self.customers.keys())
        
        # LTV grows with CAC improvement and churn reduction
        ltv_growth_per_month = 0.02  # 2% monthly growth
        
        forecast_ltv = current_ltv_pool
        for _ in range(months_ahead):
            forecast_ltv *= (1 + ltv_growth_per_month)
        
        return {
            'current_ltv_pool': current_ltv_pool,
            'forecasted_ltv_pool_12m': forecast_ltv,
            'monthly_growth_rate': ltv_growth_per_month,
        }
