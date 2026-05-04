"""
Recommendation Engine & ML Pipeline
Smart recommendations and model management
"""

import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import logging


class RecommendationType(Enum):
    """Types of recommendations."""
    FEATURE = "feature"
    PLAN_UPGRADE = "plan_upgrade"
    PRICING_OPTIMIZATION = "pricing_optimization"
    RESOURCE_OPTIMIZATION = "resource_optimization"
    RETENTION = "retention"


class Recommendation:
    """ML-generated recommendation."""
    
    def __init__(self, rec_type: RecommendationType, title: str,
                 description: str, customer_id: str, confidence: float):
        self.id = f"rec_{int(datetime.utcnow().timestamp() * 1000)}"
        self.rec_type = rec_type
        self.title = title
        self.description = description
        self.customer_id = customer_id
        self.confidence = confidence  # 0-1
        self.created_at = datetime.utcnow()
        self.priority = self._calculate_priority()
        self.action_url = ""
        self.estimated_value = 0.0
    
    def _calculate_priority(self) -> int:
        """Calculate priority (1-5, 5 highest)."""
        if self.confidence >= 0.9:
            return 5
        elif self.confidence >= 0.75:
            return 4
        elif self.confidence >= 0.60:
            return 3
        elif self.confidence >= 0.40:
            return 2
        else:
            return 1


class RecommendationEngine:
    """Generate personalized recommendations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.feature_database = {
            'webhooks': {'popularity': 0.8, 'api_coverage': 0.9},
            'rate_limiting': {'popularity': 0.7, 'api_coverage': 0.95},
            'caching': {'popularity': 0.75, 'api_coverage': 0.85},
            'batch_operations': {'popularity': 0.6, 'api_coverage': 0.7},
            'graphql': {'popularity': 0.85, 'api_coverage': 0.9},
            'websockets': {'popularity': 0.7, 'api_coverage': 0.8},
        }
        self.recommendations: Dict[str, List[Recommendation]] = {}
    
    def recommend_features(self, customer_id: str, 
                          current_features: List[str],
                          usage_pattern: Dict) -> List[Recommendation]:
        """Recommend features based on usage."""
        recommendations = []
        
        for feature, metadata in self.feature_database.items():
            if feature in current_features:
                continue
            
            # Calculate likelihood customer would use this feature
            usage_match_score = self._calculate_usage_match(feature, usage_pattern)
            adoption_likelihood = metadata['popularity'] * usage_match_score
            
            if adoption_likelihood > 0.6:
                rec = Recommendation(
                    RecommendationType.FEATURE,
                    f"Enable {feature.replace('_', ' ').title()}",
                    f"Based on your usage patterns, you would benefit from {feature}",
                    customer_id,
                    adoption_likelihood
                )
                rec.estimated_value = adoption_likelihood * 1000  # Estimated additional revenue
                recommendations.append(rec)
        
        return sorted(recommendations, key=lambda r: r.confidence, reverse=True)
    
    def recommend_plan_upgrade(self, customer_id: str, current_plan: str,
                              current_usage: int, usage_limit: int) -> Optional[Recommendation]:
        """Recommend plan upgrade."""
        utilization = current_usage / usage_limit if usage_limit > 0 else 0
        
        if utilization > 0.8:
            plans = {
                'starter': 'pro',
                'pro': 'enterprise',
            }
            
            if current_plan in plans:
                next_plan = plans[current_plan]
                confidence = min(0.95, utilization)
                
                rec = Recommendation(
                    RecommendationType.PLAN_UPGRADE,
                    f"Upgrade to {next_plan.title()} Plan",
                    f"Your {current_plan} plan is {utilization*100:.0f}% utilized",
                    customer_id,
                    confidence
                )
                rec.estimated_value = 100  # Monthly uplift
                return rec
        
        return None
    
    def recommend_pricing_optimization(self, customer_id: str,
                                       current_pricing: Dict) -> Optional[Recommendation]:
        """Recommend pricing optimization."""
        # Check for volume-based discounts
        total_usage = sum(current_pricing.get(key, 0) 
                         for key in ['api_calls', 'storage', 'compute'])
        
        if total_usage > 10000:
            discount_available = self._calculate_volume_discount(total_usage)
            
            if discount_available > 0.05:  # 5% or more
                rec = Recommendation(
                    RecommendationType.PRICING_OPTIMIZATION,
                    f"Negotiate Volume Discount",
                    f"You qualify for {discount_available*100:.0f}% discount based on usage",
                    customer_id,
                    0.75
                )
                rec.estimated_value = discount_available * sum(current_pricing.values())
                return rec
        
        return None
    
    def recommend_resource_optimization(self, customer_id: str,
                                       resource_metrics: Dict) -> List[Recommendation]:
        """Recommend resource optimization."""
        recommendations = []
        
        # Over-provisioned resources
        if resource_metrics.get('peak_cpu_usage', 0) < 20:
            rec = Recommendation(
                RecommendationType.RESOURCE_OPTIMIZATION,
                "Reduce Compute Allocation",
                "Your peak CPU usage is consistently low, consider downsizing",
                customer_id,
                0.8
            )
            rec.estimated_value = 50  # Monthly savings
            recommendations.append(rec)
        
        # Under-provisioned storage
        if resource_metrics.get('storage_utilization', 0) > 0.9:
            rec = Recommendation(
                RecommendationType.RESOURCE_OPTIMIZATION,
                "Archive Old Data",
                "Your storage is >90% full, consider archiving old data",
                customer_id,
                0.85
            )
            rec.estimated_value = 30  # Monthly savings
            recommendations.append(rec)
        
        return recommendations
    
    def _calculate_usage_match(self, feature: str, usage_pattern: Dict) -> float:
        """Calculate how well feature matches usage pattern."""
        matches = {
            'webhooks': usage_pattern.get('event_driven_usage', 0),
            'rate_limiting': usage_pattern.get('high_volume', 0),
            'caching': usage_pattern.get('repeated_queries', 0),
            'batch_operations': usage_pattern.get('bulk_operations', 0),
            'graphql': usage_pattern.get('complex_queries', 0),
            'websockets': usage_pattern.get('real_time_updates', 0),
        }
        
        return matches.get(feature, 0.3)
    
    def _calculate_volume_discount(self, total_usage: int) -> float:
        """Calculate volume discount."""
        if total_usage > 1000000:
            return 0.20  # 20% discount
        elif total_usage > 100000:
            return 0.10  # 10% discount
        elif total_usage > 50000:
            return 0.05  # 5% discount
        else:
            return 0.0


class ModelVersion:
    """ML model version."""
    
    def __init__(self, name: str, version: str, model_type: str):
        self.name = name
        self.version = version
        self.model_type = model_type
        self.created_at = datetime.utcnow()
        self.accuracy = 0.0
        self.status = 'training'  # training, ready, deprecated
        self.metrics: Dict = {}
    
    def mark_ready(self, accuracy: float) -> None:
        """Mark model as ready."""
        self.status = 'ready'
        self.accuracy = accuracy


class MLPipeline:
    """ML model training and deployment pipeline."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.models: Dict[str, ModelVersion] = {}
        self.active_models: Dict[str, str] = {}  # model_type -> version
        self.training_jobs: List[Dict] = []
        self.evaluation_metrics: Dict = {}
    
    def register_model(self, name: str, version: str, model_type: str) -> ModelVersion:
        """Register new model version."""
        model = ModelVersion(name, version, model_type)
        model_key = f"{model_type}:{version}"
        self.models[model_key] = model
        self.logger.info(f"Model registered: {model_key}")
        return model
    
    def promote_model(self, model_type: str, version: str) -> bool:
        """Promote model to production."""
        model_key = f"{model_type}:{version}"
        
        if model_key not in self.models:
            return False
        
        model = self.models[model_key]
        if model.status != 'ready':
            return False
        
        self.active_models[model_type] = version
        self.logger.info(f"Model promoted: {model_key}")
        return True
    
    def get_active_model(self, model_type: str) -> Optional[ModelVersion]:
        """Get active model version."""
        version = self.active_models.get(model_type)
        if version:
            model_key = f"{model_type}:{version}"
            return self.models.get(model_key)
        return None
    
    def start_training_job(self, model_type: str, training_data_size: int) -> Dict:
        """Start model training job."""
        job = {
            'id': f"job_{int(datetime.utcnow().timestamp())}",
            'model_type': model_type,
            'started_at': datetime.utcnow().isoformat(),
            'status': 'running',
            'progress': 0.0,
            'training_data_size': training_data_size,
        }
        
        self.training_jobs.append(job)
        self.logger.info(f"Training job started: {job['id']}")
        
        return job
    
    def get_model_performance(self, model_type: str) -> Dict:
        """Get model performance metrics."""
        model = self.get_active_model(model_type)
        
        if not model:
            return {}
        
        return {
            'model_type': model_type,
            'version': model.version,
            'accuracy': model.accuracy,
            'status': model.status,
            'metrics': model.metrics,
        }
    
    def get_pipeline_status(self) -> Dict:
        """Get pipeline status."""
        return {
            'active_models': len(self.active_models),
            'total_models': len(self.models),
            'training_jobs': len([j for j in self.training_jobs if j['status'] == 'running']),
            'models': {
                model_type: self.get_model_performance(model_type)
                for model_type in self.active_models.keys()
            }
        }


class ModelEvaluator:
    """Evaluate model performance."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def evaluate_classification_model(self, predictions: List[int],
                                    actuals: List[int]) -> Dict:
        """Evaluate classification model."""
        tp = sum(1 for p, a in zip(predictions, actuals) if p == 1 and a == 1)
        tn = sum(1 for p, a in zip(predictions, actuals) if p == 0 and a == 0)
        fp = sum(1 for p, a in zip(predictions, actuals) if p == 1 and a == 0)
        fn = sum(1 for p, a in zip(predictions, actuals) if p == 0 and a == 1)
        
        accuracy = (tp + tn) / len(predictions) if predictions else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'tp': tp,
            'tn': tn,
            'fp': fp,
            'fn': fn,
        }
    
    def evaluate_regression_model(self, predictions: List[float],
                                 actuals: List[float]) -> Dict:
        """Evaluate regression model."""
        mse = sum((p - a) ** 2 for p, a in zip(predictions, actuals)) / len(predictions)
        rmse = mse ** 0.5
        mae = sum(abs(p - a) for p, a in zip(predictions, actuals)) / len(predictions)
        
        mean_actual = sum(actuals) / len(actuals) if actuals else 0
        ss_tot = sum((a - mean_actual) ** 2 for a in actuals)
        ss_res = sum((p - a) ** 2 for p, a in zip(predictions, actuals))
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        return {
            'mse': mse,
            'rmse': rmse,
            'mae': mae,
            'r2_score': r2,
        }
