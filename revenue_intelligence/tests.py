"""
Revenue Intelligence - Comprehensive Test Suite
Tests LTV prediction, expansion detection, and forecasting
"""

from datetime import datetime, timedelta
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from predictor import (
    LTVPredictor, Customer, ExpansionEngine,
    DynamicPricingEngine, RevenueForecast,
    CustomerSegment, ChurnRiskLevel, ExpansionOpportunity
)
from dashboard import RevenueIntelligenceDashboard


def test_ltv_calculation():
    """Test LTV calculation accuracy."""
    print("Testing LTV Calculation...")
    
    predictor = LTVPredictor()
    
    # Create test customer - ENTERPRISE
    c1 = Customer("cust_001", "TechCorp", datetime.now() - timedelta(days=365))
    c1.update_metrics({
        'mrr': 10000,
        'arr': 120000,  # $120K = ENTERPRISE tier
        'usage_score': 85,
        'support_tickets': 15,
        'nps': 65,
        'feature_adoption': 90,
        'api_calls_daily': 500,
        'seats': 10,
        'months_active': 12,
    })
    
    predictor.add_customer(c1)
    
    ltv = predictor.calculate_ltv("cust_001")
    
    # Enterprise segment (98% retention) should have high LTV
    # LTV = (MRR * Margin) / Monthly Churn
    # = (10000 * 0.7) / 0.02 = 350,000
    expected_ltv = (10000 * 0.70) / 0.02
    
    assert c1.segment == CustomerSegment.ENTERPRISE, f"Expected ENTERPRISE, got {c1.segment}"
    assert ltv > 340000, f"LTV too low: {ltv}"
    print(f"✓ Enterprise LTV: ${ltv:,.0f} (expected ~${expected_ltv:,.0f})")
    
    # Test MID_MARKET customer
    c2 = Customer("cust_002", "MidSize", datetime.now() - timedelta(days=180))
    c2.update_metrics({
        'mrr': 1000,
        'arr': 12000,  # $12K = MID_MARKET tier
        'usage_score': 60,
        'support_tickets': 3,
        'nps': 45,
        'feature_adoption': 50,
        'api_calls_daily': 50,
        'seats': 2,
        'months_active': 6,
    })
    
    predictor.add_customer(c2)
    ltv2 = predictor.calculate_ltv("cust_002")
    
    assert c2.segment == CustomerSegment.MID_MARKET, f"Expected MID_MARKET, got {c2.segment}"
    assert ltv2 < ltv, "Mid-Market LTV should be lower than Enterprise"
    print(f"✓ Mid-Market LTV: ${ltv2:,.0f} (lower than Enterprise, as expected)")
    
    # Test distribution
    dist = predictor.get_ltv_distribution()
    assert dist['total_customers'] == 2
    total = ltv + ltv2
    assert abs(dist['total_ltv'] - total) / total < 0.01, "LTV distribution mismatch"
    print(f"✓ LTV Pool: ${dist['total_ltv']:,.0f} from {dist['total_customers']} customers")


def test_churn_risk_prediction():
    """Test churn risk prediction."""
    print("\nTesting Churn Risk Prediction...")
    
    predictor = LTVPredictor()
    
    # High risk customer: Low usage, low engagement
    c_high_risk = Customer("cust_high", "AtRisk Corp", 
                          datetime.now() - timedelta(days=30))
    c_high_risk.update_metrics({
        'mrr': 100,
        'arr': 1200,
        'usage_score': 15,  # Low
        'support_tickets': 0,  # No engagement
        'nps': -10,  # Very unhappy
        'feature_adoption': 5,  # Barely using
        'api_calls_daily': 10,
        'seats': 1,
        'months_active': 1,  # New customer (higher risk)
    })
    
    predictor.add_customer(c_high_risk)
    risk_level, risk_score = predictor.predict_churn_risk("cust_high")
    
    assert risk_level in [ChurnRiskLevel.HIGH, ChurnRiskLevel.CRITICAL]
    assert risk_score > 50
    print(f"✓ High-risk customer detected: {risk_level.value} (score: {risk_score:.0f}%)")
    
    # Low risk customer: High engagement
    c_low_risk = Customer("cust_low", "Engaged Inc",
                         datetime.now() - timedelta(days=365))
    c_low_risk.update_metrics({
        'mrr': 5000,
        'arr': 60000,
        'usage_score': 95,  # Very high
        'support_tickets': 10,  # Active support
        'nps': 80,  # Very happy
        'feature_adoption': 85,  # Using most features
        'api_calls_daily': 1000,
        'seats': 20,
        'months_active': 12,
    })
    
    predictor.add_customer(c_low_risk)
    risk_level2, risk_score2 = predictor.predict_churn_risk("cust_low")
    
    assert risk_level2 == ChurnRiskLevel.LOW
    assert risk_score2 < 10
    print(f"✓ Low-risk customer: {risk_level2.value} (score: {risk_score2:.0f}%)")


def test_expansion_opportunities():
    """Test expansion opportunity detection."""
    print("\nTesting Expansion Opportunities...")
    
    engine = ExpansionEngine()
    
    # SMB customer with high usage = potential for upsell/upgrade
    c_upgrade = Customer("cust_upgrade", "FastGrowing", 
                        datetime.now() - timedelta(days=60))
    c_upgrade.update_metrics({
        'mrr': 100,
        'arr': 800,  # Below $1K = STARTUP segment
        'usage_score': 85,  # High usage
        'support_tickets': 5,
        'nps': 70,
        'feature_adoption': 80,
        'api_calls_daily': 500,  # High API usage
        'seats': 3,
        'months_active': 2,
    })
    
    opps = engine.identify_opportunities("cust_upgrade", c_upgrade)
    
    # Should detect upgrade opportunity (STARTUP + high usage)
    upgrade_opps = [o for o in opps if o['type'] == ExpansionOpportunity.UPGRADE.value]
    assert len(upgrade_opps) > 0, f"Should detect upgrade opportunity, got: {opps}"
    print(f"✓ Upgrade opportunity detected: {upgrade_opps[0]['recommendation']}")
    
    # Enterprise customer with massive API calls = upsell opportunity
    c_upsell = Customer("cust_upsell", "DataHeavy",
                       datetime.now() - timedelta(days=365))
    c_upsell.update_metrics({
        'mrr': 3000,
        'arr': 36000,  # MID_MARKET
        'usage_score': 90,
        'support_tickets': 8,
        'nps': 60,
        'feature_adoption': 75,
        'api_calls_daily': 2000,  # Very high - triggers upsell
        'seats': 5,  # Currently 5 seats
        'months_active': 12,
    })
    
    opps2 = engine.identify_opportunities("cust_upsell", c_upsell)
    
    # Should detect upsell opportunity
    upsell_opps = [o for o in opps2 if o['type'] == ExpansionOpportunity.UPSELL.value]
    assert len(upsell_opps) > 0, f"Should detect upsell opportunity, got: {opps2}"
    print(f"✓ Upsell opportunity detected: {upsell_opps[0]['recommendation']}")


def test_dynamic_pricing():
    """Test dynamic pricing calculation."""
    print("\nTesting Dynamic Pricing Engine...")
    
    pricing_engine = DynamicPricingEngine()
    
    # Mid-Market customer - should get mid-range price
    c_mid = Customer("cust_mid", "MidCorp",
                           datetime.now() - timedelta(days=365))
    c_mid.update_metrics({'arr': 36000})  # Mid-Market tier
    
    price_mid = pricing_engine.calculate_optimal_price(c_mid, {
        'api_calls': 5000,  # Lower API calls to not hit cap
        'seats': 2,
        'price_elasticity': 1.0,
    })
    
    assert 500 <= price_mid['recommended_price'] <= 10000, f"Mid pricing out of range: {price_mid['recommended_price']}"
    print(f"✓ Mid-Market pricing: ${price_mid['recommended_price']:,.0f}/month")
    
    # Startup customer - free or low cost
    c_startup = Customer("cust_startup", "NewCo",
                        datetime.now() - timedelta(days=30))
    c_startup.update_metrics({'arr': 0})
    
    price_startup = pricing_engine.calculate_optimal_price(c_startup, {
        'api_calls': 1000,
        'seats': 1,
        'price_elasticity': 1.0,
    })
    
    assert price_startup['recommended_price'] <= 500, "Startup max should be $500"
    print(f"✓ Startup pricing: ${price_startup['recommended_price']:,.0f}/month")
    
    # Price sensitivity adjustment - lower elasticity = lower price
    price_sensitive = pricing_engine.calculate_optimal_price(c_mid, {
        'api_calls': 5000,  # Same as price_mid
        'seats': 2,
        'price_elasticity': 0.7,  # Price sensitive
    })
    
    assert price_sensitive['recommended_price'] < price_mid['recommended_price'], \
        f"Price sensitive ${price_sensitive['recommended_price']} should be < base ${price_mid['recommended_price']}"
    print(f"✓ Price-sensitive adjustment: ${price_sensitive['recommended_price']:,.0f}/month")


def test_revenue_forecasting():
    """Test revenue forecasting accuracy."""
    print("\nTesting Revenue Forecasting...")
    
    customers = {}
    for i in range(10):
        c = Customer(f"cust_{i}", f"Company {i}",
                    datetime.now() - timedelta(days=365*i//10))
        c.update_metrics({
            'mrr': 1000 + (i * 500),
            'arr': 12000 + (i * 6000),
            'usage_score': 70 + (i * 2),
            'months_active': 12 - (i * 1),
        })
        customers[f"cust_{i}"] = c
    
    forecast = RevenueForecast(customers)
    
    # ARR forecast
    arr_forecast = forecast.forecast_arr(12)
    assert arr_forecast['current_arr'] > 0
    assert arr_forecast['forecasted_arr_12m'] > arr_forecast['current_arr']
    assert arr_forecast['growth_rate'] > 0
    print(f"✓ ARR Forecast: ${arr_forecast['current_arr']:,.0f} → " +
          f"${arr_forecast['forecasted_arr_12m']:,.0f} ({arr_forecast['growth_rate']:.1f}% growth)")
    
    # MRR forecast
    mrr_forecast = forecast.forecast_mrr(12)
    assert len(mrr_forecast) == 12
    first_mrr = mrr_forecast[0]['forecasted_mrr']
    last_mrr = mrr_forecast[-1]['forecasted_mrr']
    assert last_mrr > first_mrr  # Should grow
    print(f"✓ MRR Forecast: Month 1: ${first_mrr:,.0f} → Month 12: ${last_mrr:,.0f}")
    
    # LTV forecast
    ltv_forecast = forecast.forecast_ltv_pool(12)
    assert ltv_forecast['forecasted_ltv_pool_12m'] > ltv_forecast['current_ltv_pool']
    print(f"✓ LTV Pool Forecast: ${ltv_forecast['current_ltv_pool']:,.0f} → " +
          f"${ltv_forecast['forecasted_ltv_pool_12m']:,.0f}")


def test_dashboard_generation():
    """Test dashboard HTML generation."""
    print("\nTesting Dashboard Generation...")
    
    predictor = LTVPredictor()
    engine = ExpansionEngine()
    pricing_engine = DynamicPricingEngine()
    
    # Create test customers
    for i in range(5):
        c = Customer(f"cust_{i}", f"TestCo {i}",
                    datetime.now() - timedelta(days=365*i//5))
        c.update_metrics({
            'mrr': 1000 + (i * 500),
            'arr': 12000 + (i * 6000),
            'usage_score': 60 + (i * 8),
            'support_tickets': 2 + i,
            'nps': 40 + (i * 10),
            'feature_adoption': 50 + (i * 8),
            'api_calls_daily': 100 * (i + 1),
            'seats': 1 + i,
            'months_active': 12 - (i * 2),
        })
        predictor.add_customer(c)
        engine.identify_opportunities(f"cust_{i}", c)
    
    forecast = RevenueForecast(predictor.customers)
    dashboard = RevenueIntelligenceDashboard()
    
    html = dashboard.generate_html(predictor, engine, pricing_engine, forecast)
    
    assert '<html>' in html.lower()
    assert 'revenue intelligence' in html.lower()
    assert 'ltv pool' in html.lower()
    assert 'forecast' in html.lower()
    assert len(html) > 5000  # Substantial HTML
    
    print(f"✓ Dashboard generated ({len(html)} bytes)")


def pytest_approx(value, rel=0.01):
    """Helper for approximate equality."""
    class Approx:
        def __init__(self, v, r):
            self.v = v
            self.r = r
        def __eq__(self, other):
            if self.v == 0:
                return other == 0
            return abs(other - self.v) / abs(self.v) <= self.r
    return Approx(value, rel)


if __name__ == '__main__':
    print("=" * 60)
    print("Revenue Intelligence - Test Suite")
    print("=" * 60)
    
    test_ltv_calculation()
    test_churn_risk_prediction()
    test_expansion_opportunities()
    test_dynamic_pricing()
    test_revenue_forecasting()
    test_dashboard_generation()
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
