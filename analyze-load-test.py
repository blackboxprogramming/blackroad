#!/usr/bin/env python3
"""
BlackRoad Load Test Results Analyzer
Parses k6 JSON output and generates performance reports
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from statistics import mean, stdev, quantiles
import argparse

class LoadTestAnalyzer:
    def __init__(self, json_file):
        self.json_file = Path(json_file)
        self.data = self._load_json()
        self.metrics = self._parse_metrics()

    def _load_json(self):
        """Load k6 JSON output file"""
        with open(self.json_file, 'r') as f:
            return json.load(f)

    def _parse_metrics(self):
        """Extract relevant metrics from k6 output"""
        metrics = {}
        
        for metric_name, metric_data in self.data.get('metrics', {}).items():
            samples = metric_data.get('values', [])
            if samples:
                metrics[metric_name] = samples
        
        return metrics

    def generate_report(self):
        """Generate comprehensive performance report"""
        report = []
        report.append("=" * 70)
        report.append("BlackRoad Load Test Performance Report")
        report.append("=" * 70)
        report.append(f"Test File: {self.json_file}")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Summary
        report.append("SUMMARY METRICS")
        report.append("-" * 70)
        
        # Extract key metrics
        if 'http_req_duration' in self.metrics:
            durations = self.metrics['http_req_duration']
            report.append(f"Request Duration Statistics:")
            report.append(f"  Min:    {min(durations):.2f}ms")
            report.append(f"  Max:    {max(durations):.2f}ms")
            report.append(f"  Mean:   {mean(durations):.2f}ms")
            if len(durations) > 1:
                report.append(f"  StdDev: {stdev(durations):.2f}ms")
            
            # Percentiles
            if len(durations) >= 4:
                p50, p95, p99 = quantiles(sorted(durations), n=100)
                report.append(f"  p50:    {p50:.2f}ms")
                report.append(f"  p95:    {p95:.2f}ms")
                report.append(f"  p99:    {p99:.2f}ms")

        report.append("")

        # Throughput
        if 'http_reqs' in self.metrics:
            reqs = len(self.metrics['http_reqs'])
            report.append(f"Throughput: {reqs} requests")

        # Error rate
        if 'http_req_failed' in self.metrics:
            failed = self.metrics['http_req_failed']
            error_rate = (sum(failed) / len(failed) * 100) if failed else 0
            report.append(f"Error Rate: {error_rate:.2f}%")

        report.append("")

        # Endpoint-specific metrics
        report.append("ENDPOINT PERFORMANCE")
        report.append("-" * 70)
        
        for metric in ['charge_latency', 'usage_latency', 'billing_latency']:
            if metric in self.metrics:
                latencies = self.metrics[metric]
                endpoint = metric.split('_')[0].upper()
                report.append(f"{endpoint} Endpoint:")
                report.append(f"  Samples: {len(latencies)}")
                if latencies:
                    report.append(f"  Mean:    {mean(latencies):.2f}ms")
                    if len(latencies) >= 4:
                        p95 = quantiles(sorted(latencies), n=100)[1]
                        report.append(f"  p95:     {p95:.2f}ms")
                report.append("")

        # Performance verdict
        report.append("PERFORMANCE VERDICT")
        report.append("-" * 70)
        
        verdict = self._generate_verdict()
        for line in verdict:
            report.append(line)

        return "\n".join(report)

    def _generate_verdict(self):
        """Generate performance verdict based on thresholds"""
        verdict = []
        
        if 'http_req_duration' in self.metrics:
            durations = self.metrics['http_req_duration']
            if len(durations) >= 4:
                p95 = quantiles(sorted(durations), n=100)[1]
                p99 = quantiles(sorted(durations), n=100)[2]
                
                if p95 < 500:
                    verdict.append("✅ p95 PASS: {:.0f}ms < 500ms threshold".format(p95))
                else:
                    verdict.append("⚠️  p95 SLOW: {:.0f}ms > 500ms threshold".format(p95))
                
                if p99 < 1000:
                    verdict.append("✅ p99 PASS: {:.0f}ms < 1000ms threshold".format(p99))
                else:
                    verdict.append("⚠️  p99 SLOW: {:.0f}ms > 1000ms threshold".format(p99))

        if 'http_req_failed' in self.metrics:
            failed = self.metrics['http_req_failed']
            error_rate = (sum(failed) / len(failed) * 100) if failed else 0
            
            if error_rate < 1.0:
                verdict.append("✅ ERRORS PASS: {:.2f}% < 1% threshold".format(error_rate))
            else:
                verdict.append("❌ ERRORS FAIL: {:.2f}% > 1% threshold".format(error_rate))

        return verdict

    def save_report(self, output_file=None):
        """Save report to file"""
        report = self.generate_report()
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
            print(f"Report saved to: {output_file}")
        else:
            print(report)

def main():
    parser = argparse.ArgumentParser(description='Analyze k6 load test results')
    parser.add_argument('json_file', help='Path to k6 JSON output file')
    parser.add_argument('-o', '--output', help='Save report to file', default=None)
    
    args = parser.parse_args()
    
    analyzer = LoadTestAnalyzer(args.json_file)
    analyzer.save_report(args.output)

if __name__ == '__main__':
    main()
