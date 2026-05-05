"""Content optimization and A/B testing framework."""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import random
import math


class ABTestStatus(Enum):
    """Status of A/B test."""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass
class Variant:
    """A/B test variant."""
    variant_id: str
    name: str
    treatment: Dict[str, Any]
    impressions: int = 0
    conversions: int = 0
    revenue: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ABTest:
    """A/B test configuration and results."""
    test_id: str
    name: str
    description: str
    status: ABTestStatus
    control_variant: Variant
    treatment_variants: List[Variant]
    allocation_percentages: Dict[str, float]
    metric_to_optimize: str  # conversions, revenue, engagement, etc.
    start_date: datetime
    end_date: Optional[datetime]
    created_at: datetime = field(default_factory=datetime.utcnow)
    min_sample_size: int = 100


class ContentOptimizer:
    """Content optimization and A/B testing engine."""
    
    def __init__(self):
        """Initialize content optimizer."""
        self.active_tests: Dict[str, ABTest] = {}
        self.archived_tests: Dict[str, ABTest] = {}
        self.user_assignments: Dict[str, Dict[str, str]] = {}  # user_id -> test_id -> variant
    
    def create_test(
        self,
        name: str,
        description: str,
        control_treatment: Dict[str, Any],
        treatment_options: List[Dict[str, Any]],
        metric_to_optimize: str = "conversions",
        duration_days: int = 14,
        min_sample_size: int = 100
    ) -> ABTest:
        """Create new A/B test."""
        test_id = f"test_{datetime.utcnow().timestamp()}"
        
        control = Variant(
            variant_id="control",
            name="Control",
            treatment=control_treatment
        )
        
        treatments = []
        for i, option in enumerate(treatment_options):
            treatments.append(Variant(
                variant_id=f"treatment_{i+1}",
                name=f"Treatment {i+1}",
                treatment=option
            ))
        
        # Equal allocation
        total_variants = 1 + len(treatments)
        allocation = 100.0 / total_variants
        
        allocation_percentages = {
            "control": allocation,
            **{t.variant_id: allocation for t in treatments}
        }
        
        test = ABTest(
            test_id=test_id,
            name=name,
            description=description,
            status=ABTestStatus.DRAFT,
            control_variant=control,
            treatment_variants=treatments,
            allocation_percentages=allocation_percentages,
            metric_to_optimize=metric_to_optimize,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=duration_days),
            min_sample_size=min_sample_size
        )
        
        return test
    
    def start_test(self, test_id: str, test: ABTest) -> bool:
        """Start an A/B test."""
        test.status = ABTestStatus.RUNNING
        self.active_tests[test_id] = test
        return True
    
    def pause_test(self, test_id: str) -> bool:
        """Pause a running test."""
        if test_id not in self.active_tests:
            return False
        self.active_tests[test_id].status = ABTestStatus.PAUSED
        return True
    
    def resume_test(self, test_id: str) -> bool:
        """Resume a paused test."""
        if test_id not in self.active_tests:
            return False
        self.active_tests[test_id].status = ABTestStatus.RUNNING
        return True
    
    def end_test(self, test_id: str) -> bool:
        """End a test and archive it."""
        if test_id not in self.active_tests:
            return False
        
        test = self.active_tests[test_id]
        test.status = ABTestStatus.COMPLETED
        test.end_date = datetime.utcnow()
        
        self.archived_tests[test_id] = test
        del self.active_tests[test_id]
        
        return True
    
    def assign_variant(self, user_id: str, test_id: str) -> Optional[str]:
        """Assign user to variant (Thompson sampling)."""
        if test_id not in self.active_tests:
            return None
        
        test = self.active_tests[test_id]
        
        if test.status != ABTestStatus.RUNNING:
            return None
        
        # Check if already assigned
        if user_id in self.user_assignments and test_id in self.user_assignments[user_id]:
            return self.user_assignments[user_id][test_id]
        
        # Thompson sampling for variant selection
        variant_id = self._thompson_sampling(test)
        
        if user_id not in self.user_assignments:
            self.user_assignments[user_id] = {}
        
        self.user_assignments[user_id][test_id] = variant_id
        return variant_id
    
    def record_impression(
        self,
        user_id: str,
        test_id: str,
        variant_id: str
    ) -> bool:
        """Record that user saw a variant."""
        if test_id not in self.active_tests:
            return False
        
        test = self.active_tests[test_id]
        
        if variant_id == "control":
            test.control_variant.impressions += 1
        else:
            for variant in test.treatment_variants:
                if variant.variant_id == variant_id:
                    variant.impressions += 1
                    break
        
        return True
    
    def record_conversion(
        self,
        user_id: str,
        test_id: str,
        variant_id: str,
        revenue: float = 0.0
    ) -> bool:
        """Record conversion for variant."""
        if test_id not in self.active_tests:
            return False
        
        test = self.active_tests[test_id]
        
        if variant_id == "control":
            test.control_variant.conversions += 1
            test.control_variant.revenue += revenue
        else:
            for variant in test.treatment_variants:
                if variant.variant_id == variant_id:
                    variant.conversions += 1
                    variant.revenue += revenue
                    break
        
        return True
    
    def _thompson_sampling(self, test: ABTest) -> str:
        """Thompson sampling for multi-armed bandit."""
        variants = [test.control_variant] + test.treatment_variants
        
        # Beta-Bernoulli model
        samples = []
        for variant in variants:
            if variant.impressions == 0:
                # Uninformed prior - explore
                sample = random.random()
            else:
                # Sample from Beta distribution
                alpha = variant.conversions + 1
                beta = variant.impressions - variant.conversions + 1
                sample = random.betavariate(alpha, beta)
            samples.append(sample)
        
        # Select variant with highest sample
        best_idx = samples.index(max(samples))
        return variants[best_idx].variant_id
    
    def get_test_results(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get A/B test results and statistical significance."""
        test = None
        if test_id in self.active_tests:
            test = self.active_tests[test_id]
        elif test_id in self.archived_tests:
            test = self.archived_tests[test_id]
        
        if not test:
            return None
        
        results = {
            'test_id': test_id,
            'name': test.name,
            'status': test.status.value,
            'start_date': test.start_date.isoformat(),
            'end_date': test.end_date.isoformat() if test.end_date else None,
            'variants': []
        }
        
        all_variants = [test.control_variant] + test.treatment_variants
        
        for variant in all_variants:
            if variant.impressions == 0:
                conversion_rate = 0.0
                avg_revenue = 0.0
            else:
                conversion_rate = (variant.conversions / variant.impressions) * 100
                avg_revenue = variant.revenue / variant.conversions if variant.conversions > 0 else 0
            
            results['variants'].append({
                'variant_id': variant.variant_id,
                'name': variant.name,
                'impressions': variant.impressions,
                'conversions': variant.conversions,
                'conversion_rate': f"{conversion_rate:.2f}%",
                'revenue': f"${variant.revenue:.2f}",
                'avg_revenue_per_conversion': f"${avg_revenue:.2f}",
                'is_winner': False  # Will be set by statistical test
            })
        
        # Simple statistical significance test
        if len(all_variants) >= 2:
            winner_idx = self._find_significant_winner(all_variants, test.min_sample_size)
            if winner_idx is not None:
                results['variants'][winner_idx]['is_winner'] = True
                results['winner'] = results['variants'][winner_idx]['variant_id']
        
        return results
    
    def _find_significant_winner(
        self,
        variants: List[Variant],
        min_sample_size: int
    ) -> Optional[int]:
        """Find statistically significant winner using Chi-square test."""
        control = variants[0]
        
        if control.impressions < min_sample_size:
            return None
        
        best_idx = 0
        best_lift = 0.0
        
        for i, variant in enumerate(variants[1:], 1):
            if variant.impressions < min_sample_size:
                continue
            
            control_rate = control.conversions / control.impressions
            variant_rate = variant.conversions / variant.impressions
            
            lift = ((variant_rate - control_rate) / control_rate) * 100
            
            # Chi-square test for significance
            chi_square = self._chi_square_test(
                control.conversions,
                control.impressions,
                variant.conversions,
                variant.impressions
            )
            
            # p < 0.05 threshold
            if chi_square > 3.841 and lift > best_lift:
                best_idx = i
                best_lift = lift
        
        return best_idx if best_lift > 0 else None
    
    def _chi_square_test(
        self,
        conv1: int,
        imp1: int,
        conv2: int,
        imp2: int
    ) -> float:
        """Chi-square test for two proportions."""
        non_conv1 = imp1 - conv1
        non_conv2 = imp2 - conv2
        
        n = imp1 + imp2
        exp_conv = ((conv1 + conv2) / n) * (imp1 + imp2)
        exp_non_conv = ((non_conv1 + non_conv2) / n) * (imp1 + imp2)
        
        chi_sq = 0.0
        chi_sq += ((conv1 - exp_conv) ** 2) / exp_conv
        chi_sq += ((non_conv1 - exp_non_conv) ** 2) / exp_non_conv
        chi_sq += ((conv2 - exp_conv) ** 2) / exp_conv
        chi_sq += ((non_conv2 - exp_non_conv) ** 2) / exp_non_conv
        
        return chi_sq
    
    def recommend_personalization(
        self,
        user_profile,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recommend personalization based on profile and context."""
        recommendation = {
            'personalization': {},
            'reason': []
        }
        
        # Price sensitivity
        if user_profile.price_sensitivity > 0.7:
            recommendation['personalization']['show_discount'] = True
            recommendation['reason'].append("User price-sensitive")
        
        # Content type preferences
        if user_profile.content_type_preferences:
            top_type = max(
                user_profile.content_type_preferences.items(),
                key=lambda x: x[1]
            )[0]
            recommendation['personalization']['content_type'] = top_type
            recommendation['reason'].append(f"Prefers {top_type}")
        
        # Engagement-based
        if user_profile.engagement_score > 80:
            recommendation['personalization']['show_premium'] = True
            recommendation['reason'].append("High-value VIP customer")
        
        # Category affinity
        if user_profile.category_affinities:
            top_category = max(
                user_profile.category_affinities.items(),
                key=lambda x: x[1]
            )[0]
            recommendation['personalization']['featured_category'] = top_category
        
        return recommendation
    
    def get_engine_metrics(self) -> Dict[str, Any]:
        """Get content optimizer metrics."""
        return {
            'active_tests': len(self.active_tests),
            'completed_tests': len(self.archived_tests),
            'total_variants_active': sum(
                1 + len(t.treatment_variants)
                for t in self.active_tests.values()
            ),
            'total_users_in_tests': len(self.user_assignments),
            'total_test_impressions': sum(
                test.control_variant.impressions +
                sum(v.impressions for v in test.treatment_variants)
                for test in self.active_tests.values()
            ),
        }
