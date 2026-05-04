import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Counter } from 'k6/metrics';

export const latency = new Trend('latency');
export const throughput = new Counter('requests');

// Gradual load increase to find breaking point
export const options = {
  stages: [
    // Phase 1: Baseline (100 users)
    { duration: '5m', target: 100 },
    { duration: '5m', target: 100 },
    
    // Phase 2: Normal load (1K users)
    { duration: '5m', target: 1000 },
    { duration: '5m', target: 1000 },
    
    // Phase 3: Elevated (10K users)
    { duration: '5m', target: 10000 },
    { duration: '5m', target: 10000 },
    
    // Phase 4: High load (50K users)
    { duration: '5m', target: 50000 },
    { duration: '5m', target: 50000 },
    
    // Phase 5: Peak (100K users)
    { duration: '5m', target: 100000 },
    { duration: '5m', target: 100000 },
    
    // Phase 6: Extreme (1M users - representing 1B scale)
    { duration: '10m', target: 1000000 },
    { duration: '5m', target: 1000000 },
    
    // Ramp down
    { duration: '5m', target: 0 },
  ],
  thresholds: {
    'http_req_duration': ['p(95)<1000', 'p(99)<2000'],
    'http_req_failed': ['rate<0.05'],
  },
};

export default function() {
  let response = http.get('http://localhost:8000/api/customers');
  
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 1000ms': (r) => r.timings.duration < 1000,
  });
  
  latency.add(response.timings.duration);
  throughput.add(1);
  
  sleep(0.1);
}
