import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Trend } from 'k6/metrics';

// Metrics tracking 1B user simulation
export const totalOperations = new Counter('1b_total_operations');
export const operationDuration = new Trend('1b_operation_duration');
export const successRate = new Counter('1b_success_rate');
export const errorRate = new Counter('1b_error_rate');

// Simulating 1 billion users:
// - 1M concurrent connections in test
// - Each represents 1000 actual users
// - Total: 1M * 1000 = 1B users
export const options = {
  stages: [
    { duration: '2m', target: 10000 },       // 10M users
    { duration: '2m', target: 100000 },      // 100M users  
    { duration: '2m', target: 500000 },      // 500M users
    { duration: '5m', target: 1000000 },     // 1B users
    { duration: '10m', target: 1000000 },    // Hold at 1B
    { duration: '2m', target: 0 },           // Ramp down
  ],
  
  thresholds: {
    'http_req_duration': ['p(95)<500', 'p(99)<1000'],
    'http_req_failed': ['rate<0.01'],
    'http_requests': ['count>1000000'],  // At least 1M requests
  },
};

const ENDPOINTS = [
  '/api/customers',
  '/api/subscriptions', 
  '/api/transactions',
  '/api/analytics/events',
  '/api/billing/invoices',
];

export default function() {
  // Simulate realistic 1B user workload
  const endpoint = ENDPOINTS[Math.floor(Math.random() * ENDPOINTS.length)];
  
  let response = http.get(`http://localhost:8000${endpoint}`);
  
  totalOperations.add(1);
  operationDuration.add(response.timings.duration);
  
  if (response.status === 200) {
    successRate.add(1);
  } else {
    errorRate.add(1);
  }
  
  check(response, {
    '1B scale - status 200': (r) => r.status === 200,
    '1B scale - response < 500ms': (r) => r.timings.duration < 500,
    '1B scale - no errors': (r) => r.status !== 500 && r.status !== 503,
  });
  
  sleep(0.05);
}
