"""
Usage Forecasting & Anomaly Detection
Time-series forecasting and real-time anomaly detection
"""

import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from statistics import mean, stdev
import logging


class UsageDataPoint:
    """Usage data point."""
    
    def __init__(self, timestamp: datetime, api_calls: int, 
                 compute_hours: int, storage_gb: int):
        self.timestamp = timestamp
        self.api_calls = api_calls
        self.compute_hours = compute_hours
        self.storage_gb = storage_gb


class UsageForecaster:
    """Time-series forecasting for usage."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.historical_data: List[UsageDataPoint] = []
        self.forecast_horizon = 30  # days
        self.model_version = "1.0.0"
    
    def add_data_point(self, data_point: UsageDataPoint) -> None:
        """Add data point."""
        self.historical_data.append(data_point)
    
    def get_trend(self, metric_key: str, days: int = 30) -> float:
        """Get trend for metric (growth rate)."""
        if len(self.historical_data) < 2:
            return 1.0
        
        recent_data = self.historical_data[-days:]
        if not recent_data:
            return 1.0
        
        values = [getattr(dp, metric_key) for dp in recent_data if hasattr(dp, metric_key)]
        if len(values) < 2:
            return 1.0
        
        # Simple linear trend
        first_half_avg = mean(values[:len(values)//2])
        second_half_avg = mean(values[len(values)//2:])
        
        if first_half_avg == 0:
            return 1.0
        
        return second_half_avg / first_half_avg
    
    def forecast_metric(self, metric_key: str, days_ahead: int = 30) -> List[Dict]:
        """Forecast metric N days ahead."""
        if len(self.historical_data) < 7:
            return []
        
        recent_data = self.historical_data[-30:]
        values = [getattr(dp, metric_key) for dp in recent_data if hasattr(dp, metric_key)]
        
        if not values:
            return []
        
        # Calculate statistics
        current_avg = mean(values[-7:]) if len(values) >= 7 else mean(values)
        trend = self.get_trend(metric_key, 30)
        
        # Add some noise/variation
        seasonal_factor = 1.1  # 10% higher on weekends
        
        forecasts = []
        for day in range(days_ahead):
            # Apply trend
            forecast_value = current_avg * (trend ** (day / 30.0))
            
            # Add seasonal variation
            day_of_week = (datetime.utcnow() + timedelta(days=day)).weekday()
            if day_of_week >= 5:  # Weekend
                forecast_value *= seasonal_factor
            
            forecasts.append({
                'date': (datetime.utcnow() + timedelta(days=day)).date().isoformat(),
                'forecast': forecast_value,
                'confidence': 0.85 - (day * 0.01),  # Confidence decreases over time
            })
        
        return forecasts
    
    def forecast_revenue(self, customer_mrr: float, days_ahead: int = 90) -> List[Dict]:
        """Forecast revenue based on usage trends."""
        api_forecasts = self.forecast_metric('api_calls', days_ahead)
        
        forecasts = []
        for i, forecast in enumerate(api_forecasts):
            # Assume revenue scales with API usage
            usage_factor = forecast['forecast'] / 100000.0  # Normalize
            revenue = customer_mrr * (0.8 + usage_factor * 0.4)  # Revenue varies ±20%
            
            forecasts.append({
                'date': forecast['date'],
                'forecast_mrr': revenue,
                'confidence': forecast['confidence'],
            })
        
        return forecasts
    
    def get_forecast_stats(self, forecasts: List[Dict]) -> Dict:
        """Get forecast statistics."""
        if not forecasts:
            return {}
        
        values = [f['forecast'] for f in forecasts]
        
        return {
            'avg_forecast': mean(values),
            'trend': 'up' if values[-1] > values[0] else 'down',
            'trend_magnitude': (values[-1] - values[0]) / values[0] * 100 if values[0] != 0 else 0,
            'min': min(values),
            'max': max(values),
        }


class AnomalyDetector:
    """Real-time anomaly detection."""
    
    def __init__(self, sensitivity: float = 2.0):
        self.logger = logging.getLogger(__name__)
        self.historical_data: List[float] = []
        self.sensitivity = sensitivity  # Standard deviations
        self.anomalies: List[Dict] = []
        self.baseline_window = 30  # days
    
    def add_observation(self, value: float, timestamp: datetime = None) -> None:
        """Add observation."""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        self.historical_data.append(value)
    
    def detect_anomaly(self, value: float) -> Tuple[bool, Optional[str], float]:
        """Detect if value is anomalous."""
        if len(self.historical_data) < 10:
            return False, None, 0.0
        
        # Calculate baseline statistics
        baseline = self.historical_data[-self.baseline_window:]
        mean_val = mean(baseline)
        
        if len(baseline) < 2:
            return False, None, 0.0
        
        stdev_val = stdev(baseline)
        
        if stdev_val == 0:
            return False, None, 0.0
        
        # Z-score
        z_score = abs((value - mean_val) / stdev_val)
        
        is_anomalous = z_score > self.sensitivity
        
        # Classify anomaly type
        anomaly_type = None
        if is_anomalous:
            if value > mean_val:
                anomaly_type = 'spike'
            else:
                anomaly_type = 'drop'
        
        return is_anomalous, anomaly_type, z_score
    
    def detect_trend_change(self, window_size: int = 7) -> Tuple[bool, str]:
        """Detect significant trend changes."""
        if len(self.historical_data) < window_size * 2:
            return False, 'insufficient_data'
        
        recent = self.historical_data[-window_size:]
        previous = self.historical_data[-(window_size*2):-window_size]
        
        recent_avg = mean(recent)
        previous_avg = mean(previous)
        
        if previous_avg == 0:
            return False, 'no_change'
        
        change_pct = (recent_avg - previous_avg) / previous_avg * 100
        
        if abs(change_pct) > 25:  # >25% change
            direction = 'increasing' if change_pct > 0 else 'decreasing'
            return True, direction
        
        return False, 'no_significant_change'
    
    def detect_pattern(self) -> Optional[str]:
        """Detect patterns in data."""
        if len(self.historical_data) < 14:
            return None
        
        # Check for cycles/seasonality
        last_week = self.historical_data[-7:]
        prev_week = self.historical_data[-14:-7]
        
        last_week_avg = mean(last_week)
        prev_week_avg = mean(prev_week)
        
        if last_week_avg == 0:
            return None
        
        correlation = 1.0 - abs(last_week_avg - prev_week_avg) / max(last_week_avg, prev_week_avg)
        
        if correlation > 0.8:
            return 'weekly_cycle'
        
        return None
    
    def get_anomaly_report(self) -> Dict:
        """Get anomaly report."""
        return {
            'total_anomalies': len(self.anomalies),
            'recent_anomalies': self.anomalies[-10:],
            'anomaly_rate': len(self.anomalies) / len(self.historical_data) if self.historical_data else 0,
        }


class BehaviorAnomalyDetector:
    """Detect anomalies in user behavior."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.user_baselines: Dict[str, Dict] = {}
    
    def add_user_activity(self, user_id: str, api_calls: int,
                         unique_endpoints: int, error_rate: float) -> None:
        """Add user activity."""
        if user_id not in self.user_baselines:
            self.user_baselines[user_id] = {
                'api_calls': [],
                'unique_endpoints': [],
                'error_rate': [],
            }
        
        baseline = self.user_baselines[user_id]
        baseline['api_calls'].append(api_calls)
        baseline['unique_endpoints'].append(unique_endpoints)
        baseline['error_rate'].append(error_rate)
    
    def detect_user_anomaly(self, user_id: str, current_api_calls: int,
                           current_endpoints: int, current_error_rate: float) -> List[str]:
        """Detect behavior anomalies."""
        if user_id not in self.user_baselines:
            return []
        
        baseline = self.user_baselines[user_id]
        anomalies = []
        
        # Check API calls
        if baseline['api_calls']:
            calls_baseline = mean(baseline['api_calls'][-30:])
            if current_api_calls > calls_baseline * 3:
                anomalies.append(f'Unusually high API calls ({current_api_calls} vs {calls_baseline})')
        
        # Check endpoints
        if baseline['unique_endpoints']:
            endpoints_baseline = mean(baseline['unique_endpoints'][-30:])
            if current_endpoints < endpoints_baseline * 0.5:
                anomalies.append(f'Reduced endpoint diversity')
        
        # Check error rate
        if baseline['error_rate']:
            error_baseline = mean(baseline['error_rate'][-30:])
            if current_error_rate > error_baseline * 2:
                anomalies.append(f'Elevated error rate ({current_error_rate} vs {error_baseline})')
        
        return anomalies
    
    def detect_coordinated_attack(self, user_behaviors: Dict) -> bool:
        """Detect potential coordinated attack."""
        high_api_call_users = sum(1 for v in user_behaviors.values() 
                                 if v.get('api_calls', 0) > 100000)
        
        # If >50% of users have abnormally high activity, might be attack
        if len(user_behaviors) > 0:
            ratio = high_api_call_users / len(user_behaviors)
            return ratio > 0.5
        
        return False
