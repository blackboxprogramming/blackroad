import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter, Gauge } from 'k6/metrics';

// Custom metrics
export const errors = new Counter('errors');
export const createCustomerDuration = new Trend('create_customer_duration');
export const getCustomerDuration = new Trend('get_customer_duration');
export const updateSubscriptionDuration = new Trend('update_subscription_duration');
export const processPaymentDuration = new Trend('process_payment_duration');
export const customersProcessed = new Counter('customers_processed');
export const transactionsProcessed = new Counter('transactions_processed');

// Options for test
export const options = {
  stages: [
    { duration: '1m', target: 50 },       // Ramp up
    { duration: '3m', target: 500 },      // Gradually increase
    { duration: '2m', target: 1000 },     // Peak load
    { duration: '2m', target: 0 },        // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.1'],
  },
};

const BASE_URL = 'http://localhost:8000';
const BILLING_URL = 'http://localhost:8001';
const ANALYTICS_URL = 'http://localhost:8002';

export default function() {
  // User scenario simulating real behavior
  
  group('Customer Management', function() {
    // Create customer
    let createRes = http.post(`${BASE_URL}/api/customers`, JSON.stringify({
      name: `Customer ${__VU}`,
      email: `customer${__VU}@example.com`,
      tier: 'pro',
    }), {
      headers: { 'Content-Type': 'application/json' },
    });
    
    check(createRes, {
      'create customer status is 200': (r) => r.status === 200 || r.status === 201,
      'create customer has id': (r) => r.json('id') !== null,
    }) || errors.add(1);
    
    createCustomerDuration.add(createRes.timings.duration);
    customersProcessed.add(1);
    
    const customerId = createRes.json('id');
    sleep(1);
    
    // Get customer
    let getRes = http.get(`${BASE_URL}/api/customers/${customerId}`);
    check(getRes, {
      'get customer status is 200': (r) => r.status === 200,
      'get customer has email': (r) => r.json('email') !== null,
    }) || errors.add(1);
    
    getCustomerDuration.add(getRes.timings.duration);
    sleep(1);
  });
  
  group('Billing Operations', function() {
    // Create subscription
    let subRes = http.post(`${BILLING_URL}/api/subscriptions`, JSON.stringify({
      customer_id: `cust_${__VU}`,
      plan: 'pro_monthly',
      billing_cycle: 'monthly',
    }), {
      headers: { 'Content-Type': 'application/json' },
    });
    
    check(subRes, {
      'subscription creation status is 201': (r) => r.status === 201,
    }) || errors.add(1);
    
    sleep(1);
    
    // Process payment
    let payRes = http.post(`${BILLING_URL}/api/payments`, JSON.stringify({
      customer_id: `cust_${__VU}`,
      amount: 9900,
      currency: 'USD',
      source: 'card_stripe_test',
    }), {
      headers: { 'Content-Type': 'application/json' },
    });
    
    check(payRes, {
      'payment processing status is 200': (r) => r.status === 200,
      'payment has transaction_id': (r) => r.json('transaction_id') !== null,
    }) || errors.add(1);
    
    processPaymentDuration.add(payRes.timings.duration);
    transactionsProcessed.add(1);
    sleep(1);
  });
  
  group('Analytics', function() {
    // Record events
    let eventRes = http.post(`${ANALYTICS_URL}/api/events`, JSON.stringify({
      user_id: `user_${__VU}`,
      event_type: 'page_view',
      event_data: {
        page: '/dashboard',
        timestamp: new Date().toISOString(),
      },
    }), {
      headers: { 'Content-Type': 'application/json' },
    });
    
    check(eventRes, {
      'event tracking status is 200': (r) => r.status === 200 || r.status === 201,
    }) || errors.add(1);
    
    sleep(2);
  });
  
  group('Health Checks', function() {
    // Check API health
    let healthRes = http.get(`${BASE_URL}/health`);
    check(healthRes, {
      'API health check passed': (r) => r.status === 200,
    }) || errors.add(1);
  });
}

export function handleSummary(data) {
  // Log summary
  console.log('Test Summary:');
  console.log(`  Total Requests: ${data.metrics.http_reqs.value}`);
  console.log(`  Failed Requests: ${data.metrics.http_req_failed.value}`);
  return {
    'stdout': JSON.stringify(data, null, 2),
  };
}
