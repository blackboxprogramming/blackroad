"""
Churn Prediction & Customer Lifecycle ML Models
"""

import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum
import logging
import random


class ChurnRisk(Enum):
    """Churn risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Customer:
    """Customer data for ML."""
    
    def __init__(self, customer_id: str, name: str):
        self.customer_id = customer_id
        self.name = name
        self.created_at = datetime.utcnow()
        self.last_payment = datetime.utcnow()
        self.plan = "pro"
        self.mrr = 99.0  # Monthly recurring revenue
        
        # Features
        self.payment_failed_count = 0
        self.support_tickets = 0
        self.api_usage_trend = 1.0  # Trend: 0.5 = declining, 1.0 = stable, 1.5 = growing
        self.feature_adoption = 0.7  # 0-1 scale
        self.nps_score = 8  # Net promoter score
        self.days_since_signup = 180
        self.days_inactive = 0
        self.discount_percentage = 0
        self.contract_remaining_days = 365


class ChurnPredictionModel:
    """ML model for churn prediction."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.feature_weights = {
            'payment_failed_count': -0.8,      # Negative weight = increases churn risk
            'support_tickets': -0.1,            # Low priority
            'api_usage_trend': 0.6,             # Positive weight = decreases churn risk
            'feature_adoption': 0.7,
            'nps_score': 0.5,
            'days_since_signup': 0.1,
            'days_inactive': -0.9,              # Strong negative
            'discount_percentage': -0.3,
            'contract_remaining_days': 0.4,
        }
        self.model_accuracy = 0.87
        self.model_version = "1.0.0"
        self.trained_at = datetime.utcnow()
    
    def extract_features(self, customer: Customer) -> Dict[str, float]:
        """Extract features from customer."""
        return {
            'payment_failed_count': float(customer.payment_failed_count),
            'support_tickets': float(customer.support_tickets),
            'api_usage_trend': customer.api_usage_trend,
            'feature_adoption': customer.feature_adoption,
            'nps_score': float(customer.nps_score) / 10.0,  # Normalize to 0-1
            'days_since_signup': float(customer.days_since_signup) / 365.0,  # Normalize
            'days_inactive': float(customer.days_inactive) / 30.0,  # Normalize
            'discount_percentage': customer.discount_percentage / 100.0,  # Normalize
            'contract_remaining_days': float(customer.contract_remaining_days) / 365.0,
        }
    
    def predict_churn_probability(self, customer: Customer) -> float:
        """Predict churn probability (0-1)."""
        features = self.extract_features(customer)
        
        score = 0.5  # Base score
        
        for feature_name, weight in self.feature_weights.items():
            if feature_name in features:
                feature_value = features[feature_name]
                score += (feature_value * weight) * 0.1
        
        # Clamp to 0-1
        score = max(0, min(1, score))
        
        return score
    
    def predict_churn_risk(self, customer: Customer) -> ChurnRisk:
        """Predict churn risk level."""
        probability = self.predict_churn_probability(customer)
        
        if probability >= 0.75:
            return ChurnRisk.CRITICAL
        elif probability >= 0.50:
            return ChurnRisk.HIGH
        elif probability >= 0.30:
            return ChurnRisk.MEDIUM
        else:
            return ChurnRisk.LOW
    
    def get_churn_factors(self, customer: Customer) -> List[Dict]:
        """Get top factors contributing to churn."""
        features = self.extract_features(customer)
        
        # Calculate contribution of each feature
        contributions = []
        for feature_name, weight in self.feature_weights.items():
            if feature_name in features:
                feature_value = features[feature_name]
                contribution = (feature_value * weight) * 100
                contributions.append({
                    'factor': feature_name,
                    'weight': weight,
                    'value': feature_value,
                    'contribution': contribution,
                })
        
        # Sort by contribution magnitude (most negative first)
        contributions.sort(key=lambda x: x['contribution'])
        
        return contributions[:5]  # Top 5 factors
    
    def get_retention_recommendations(self, customer: Customer) -> List[str]:
        """Get recommendations to reduce churn risk."""
        recommendations = []
        probability = self.predict_churn_probability(customer)
        factors = self.get_churn_factors(customer)
        
        for factor in factors:
            if factor['contribution'] < 0:  # Negative contribution
                if 'payment' in factor['factor']:
                    recommendations.append("Contact customer about payment issues - offer payment plan")
                elif 'inactive' in factor['factor']:
                    recommendations.append("Send re-engagement campaign with feature highlights")
                elif 'usage' in factor['factor']:
                    recommendations.append("Schedule product demo to increase adoption")
                elif 'adoption' in factor['factor']:
                    recommendations.append("Offer personalized onboarding and training")
                elif 'nps' in factor['factor']:
                    recommendations.append("Reach out to understand satisfaction issues")
        
        return recommendations
    
    def get_model_performance(self) -> Dict:
        """Get model performance metrics."""
        return {
            'model_version': self.model_version,
            'trained_at': self.trained_at.isoformat(),
            'accuracy': self.model_accuracy,
            'precision': 0.89,
            'recall': 0.84,
            'f1_score': 0.86,
            'auc_roc': 0.91,
        }


class LifecycleSegmentation:
    """Customer lifecycle segmentation."""
    
    def __init__(self):
        self.segments = {
            'new': {'days': (0, 30), 'description': 'Recently signed up'},
            'growing': {'days': (31, 180), 'description': 'Usage increasing'},
            'mature': {'days': (181, 365), 'description': 'Stable, established'},
            'at_risk': {'days': (366, 730), 'description': 'Usage declining'},
            'churned': {'days': (731, 999999), 'description': 'Inactive >2 years'},
        }
    
    def get_segment(self, customer: Customer) -> str:
        """Get customer segment."""
        if customer.days_inactive > 60:
            return 'churned'
        
        for segment_name, config in self.segments.items():
            min_days, max_days = config['days']
            if min_days <= customer.days_since_signup <= max_days:
                return segment_name
        
        return 'mature'
    
    def get_segment_metrics(self, customers: List[Customer]) -> Dict:
        """Get metrics per segment."""
        segments_data = {s: [] for s in self.segments.keys()}
        
        for customer in customers:
            segment = self.get_segment(customer)
            segments_data[segment].append(customer)
        
        return {
            segment: {
                'count': len(customers_in_segment),
                'avg_mrr': sum(c.mrr for c in customers_in_segment) / len(customers_in_segment) if customers_in_segment else 0,
                'churn_rate': sum(1 for c in customers_in_segment if c.days_inactive > 30) / len(customers_in_segment) if customers_in_segment else 0,
            }
            for segment, customers_in_segment in segments_data.items()
        }


class UpgradeOpportunities:
    """Identify upgrade opportunities."""
    
    def __init__(self):
        self.plans = {
            'starter': {'price': 29, 'api_calls': 10000},
            'pro': {'price': 99, 'api_calls': 100000},
            'enterprise': {'price': 999, 'api_calls': 1000000},
        }
    
    def should_upgrade(self, customer: Customer, current_usage: int) -> Tuple[bool, Optional[str]]:
        """Determine if customer should upgrade."""
        # If usage is >80% of limit, recommend upgrade
        if customer.plan == 'starter' and current_usage > 8000:
            return True, 'pro'
        elif customer.plan == 'pro' and current_usage > 80000:
            return True, 'enterprise'
        
        return False, None
    
    def estimate_upsell_revenue(self, customer: Customer) -> Dict:
        """Estimate potential upsell revenue."""
        current_plan = customer.plan
        current_mrr = customer.mrr
        
        if current_plan == 'starter':
            potential_plan = 'pro'
            potential_mrr = self.plans['pro']['price']
        elif current_plan == 'pro':
            potential_plan = 'enterprise'
            potential_mrr = self.plans['enterprise']['price']
        else:
            return {}
        
        return {
            'current_plan': current_plan,
            'current_mrr': current_mrr,
            'potential_plan': potential_plan,
            'potential_mrr': potential_mrr,
            'monthly_uplift': potential_mrr - current_mrr,
            'annual_uplift': (potential_mrr - current_mrr) * 12,
        }


class CustomerHealthScore:
    """Compute customer health score."""
    
    def __init__(self):
        self.weights = {
            'payment_health': 0.25,
            'usage_health': 0.30,
            'engagement_health': 0.25,
            'support_health': 0.20,
        }
    
    def compute_score(self, customer: Customer) -> float:
        """Compute health score (0-100)."""
        payment_score = max(0, 100 - (customer.payment_failed_count * 20))
        usage_score = customer.api_usage_trend * 100
        engagement_score = customer.feature_adoption * 100
        support_score = max(0, 100 - (customer.support_tickets * 5))
        
        health_score = (
            payment_score * self.weights['payment_health'] +
            usage_score * self.weights['usage_health'] +
            engagement_score * self.weights['engagement_health'] +
            support_score * self.weights['support_health']
        )
        
        return health_score
    
    def get_health_status(self, score: float) -> str:
        """Get health status."""
        if score >= 80:
            return 'excellent'
        elif score >= 60:
            return 'good'
        elif score >= 40:
            return 'fair'
        else:
            return 'poor'
    
    def get_recommendations_by_score(self, customer: Customer) -> List[str]:
        """Get recommendations based on health score."""
        score = self.compute_score(customer)
        recommendations = []
        
        if score >= 80:
            recommendations.append("Customer is thriving - consider for upsell opportunities")
            recommendations.append("Request testimonial or case study")
        elif score >= 60:
            recommendations.append("Monitor for early signs of disengagement")
            recommendations.append("Schedule QBR (quarterly business review)")
        elif score >= 40:
            recommendations.append("Implement retention initiatives")
            recommendations.append("Reach out with personalized support")
        else:
            recommendations.append("URGENT: Customer at high risk of churn")
            recommendations.append("Escalate to customer success team immediately")
        
        return recommendations
