import http from 'k6/http';
import { check, sleep } from 'k6';

// Test system behavior under sudden traffic spikes
export const options = {
  stages: [
    { duration: '1m', target: 100 },          // Baseline
    { duration: '30s', target: 100000 },      // SPIKE!
    { duration: '30s', target: 100000 },      // Hold spike
    { duration: '2m', target: 0 },            // Recovery
  ],
  thresholds: {
    'http_req_duration': ['p(95)<1000'],
    'http_req_failed': ['rate<0.1'],
  },
};

export default function() {
  let response = http.get('http://localhost:8000/api/customers');
  
  check(response, {
    'spike handled - status 200': (r) => r.status === 200,
    'spike handled - response time': (r) => r.timings.duration < 2000,
  });
  
  sleep(0.5);
}
