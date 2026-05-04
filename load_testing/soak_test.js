import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Trend } from 'k6/metrics';

export const successCount = new Counter('successful_requests');
export const errorCount = new Counter('failed_requests');
export const duration = new Trend('request_duration');

// Long-running test to detect memory leaks and stability issues
export const options = {
  stages: [
    { duration: '5m', target: 50000 },    // Ramp up
    { duration: '60m', target: 50000 },   // Soak for 1 hour
    { duration: '5m', target: 0 },        // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p(99)<1000'],
    'http_req_failed': ['rate<0.01'],
  },
};

export default function() {
  let response = http.get('http://localhost:8000/api/customers');
  
  if (response.status === 200) {
    successCount.add(1);
  } else {
    errorCount.add(1);
  }
  
  duration.add(response.timings.duration);
  
  check(response, {
    'soak test - status OK': (r) => r.status === 200,
    'soak test - no timeout': (r) => r.timings.duration < 5000,
  });
  
  sleep(0.2);
}
