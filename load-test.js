import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter, Gauge } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const chargeLatency = new Trend('charge_latency');
const usageLatency = new Trend('usage_latency');
const billingLatency = new Trend('billing_latency');
const successfulCharges = new Counter('successful_charges');
const failedCharges = new Counter('failed_charges');
const requestThroughput = new Gauge('request_throughput');

// Configuration
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const CLERK_TOKEN = __ENV.CLERK_TOKEN || 'test-clerk-token-' + Math.random().toString(36).substr(2, 9);
const STRIPE_KEY = __ENV.STRIPE_KEY || 'sk_test_' + Math.random().toString(36).substr(2, 20);

// Load test options
export const options = {
  // Scenario 1: Baseline (ramping to 1K users)
  stages: [
    { duration: '2m', target: 100, name: 'ramp-up-100' },
    { duration: '3m', target: 500, name: 'ramp-up-500' },
    { duration: '5m', target: 1000, name: 'baseline' },
    { duration: '2m', target: 2000, name: 'ramp-up-2k' },
    { duration: '5m', target: 5000, name: 'sustained-5k' },
    { duration: '2m', target: 10000, name: 'spike-10k' },
    { duration: '5m', target: 10000, name: 'sustained-spike' },
    { duration: '3m', target: 0, name: 'ramp-down' },
  ],
  
  // Performance thresholds
  thresholds: {
    'http_req_duration': ['p(95)<500', 'p(99)<1000'],  // 95% under 500ms, 99% under 1s
    'http_req_failed': ['rate<0.01'],                   // Less than 1% error rate
    'errors': ['rate<0.01'],                            // Less than 1% custom errors
    'charge_latency': ['p(95)<300', 'p(99)<500'],       // Charge endpoint targets
    'successful_charges': ['rate>=100'],                // At least 100 charges/sec at peak
  },
  
  // Settings
  ext: {
    loadimpact: {
      projectID: 3356396,
      name: 'BlackRoad API Load Test'
    }
  }
};

// Helper: Generate unique customer ID
function getCustomerId(vu) {
  return `cus_${String(vu.idInScenarioInstance).padStart(6, '0')}`;
}

// Test function
export default function (data) {
  const customerId = getCustomerId(__VU);
  const headers = {
    'Authorization': `Bearer ${CLERK_TOKEN}`,
    'Content-Type': 'application/json',
  };

  group('Charge Endpoint', function () {
    const chargePayload = {
      customer_id: customerId,
      amount: Math.floor(Math.random() * 10000) + 100, // $1-$100
      description: `Load test charge for ${customerId}`,
    };

    const startTime = new Date();
    const res = http.post(
      `${BASE_URL}/api/metering/charge/hourly`,
      JSON.stringify(chargePayload),
      { headers }
    );
    const duration = new Date() - startTime;

    chargeLatency.add(duration);
    requestThroughput.add(1);

    const success = check(res, {
      'charge status is 200 or 202': (r) => r.status === 200 || r.status === 202,
      'charge has transaction_id': (r) => r.json('transaction_id') !== undefined,
      'charge has amount': (r) => r.json('amount') !== undefined,
    });

    if (success) {
      successfulCharges.add(1);
    } else {
      failedCharges.add(1);
      errorRate.add(1);
    }
  });

  // Small delay between requests
  sleep(Math.random() * 2 + 1);

  group('Usage Endpoint', function () {
    const startTime = new Date();
    const res = http.get(
      `${BASE_URL}/api/metering/usage?customer_id=${customerId}`,
      { headers }
    );
    const duration = new Date() - startTime;

    usageLatency.add(duration);

    const success = check(res, {
      'usage status is 200': (r) => r.status === 200,
      'usage has total_calls': (r) => r.json('total_calls') !== undefined,
      'usage has remaining_free_hours': (r) => r.json('remaining_free_hours') !== undefined,
    });

    if (!success) {
      errorRate.add(1);
    }
  });

  sleep(Math.random() * 1 + 0.5);

  group('Billing Portal', function () {
    const startTime = new Date();
    const res = http.get(
      `${BASE_URL}/api/metering/billing-portal/${customerId}`,
      { headers }
    );
    const duration = new Date() - startTime;

    billingLatency.add(duration);

    const success = check(res, {
      'billing portal status is 200': (r) => r.status === 200,
      'billing portal has invoices': (r) => Array.isArray(r.json('invoices')),
    });

    if (!success) {
      errorRate.add(1);
    }
  });

  sleep(Math.random() * 2 + 1);
}

// Teardown: Summary stats
export function teardown(data) {
  console.log('='.repeat(60));
  console.log('Load Test Complete');
  console.log('='.repeat(60));
}
