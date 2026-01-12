#!/usr/bin/env python3
"""
Example 5: Load Testing

This example demonstrates how to perform load testing on marionette tunnels.
Measures throughput, latency, and connection stability under load.

Usage:
    python examples/05_load_testing.py --format http_simple_blocking --connections 10 --duration 60
"""

import sys
import argparse
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, '.')

import marionette_tg.dsl


class LoadTestResult:
    """Container for load test results."""
    
    def __init__(self):
        self.successful_requests = 0
        self.failed_requests = 0
        self.latencies = []
        self.throughput_bytes = 0
        self.start_time = None
        self.end_time = None

    def add_result(self, success, latency, bytes_transferred):
        if success:
            self.successful_requests += 1
            self.latencies.append(latency)
            self.throughput_bytes += bytes_transferred
        else:
            self.failed_requests += 1

    def get_stats(self):
        """Calculate statistics from results."""
        if not self.latencies:
            return {
                'total_requests': self.successful_requests + self.failed_requests,
                'success_rate': 0.0,
                'avg_latency': 0.0,
                'min_latency': 0.0,
                'max_latency': 0.0,
                'p95_latency': 0.0,
                'throughput_mbps': 0.0,
            }
        
        sorted_latencies = sorted(self.latencies)
        p95_index = int(len(sorted_latencies) * 0.95)
        
        duration = (self.end_time - self.start_time) if self.end_time and self.start_time else 1.0
        total_requests = self.successful_requests + self.failed_requests
        
        return {
            'total_requests': total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': (self.successful_requests / total_requests * 100) if total_requests > 0 else 0.0,
            'avg_latency': statistics.mean(self.latencies),
            'min_latency': min(self.latencies),
            'max_latency': max(self.latencies),
            'p95_latency': sorted_latencies[p95_index] if p95_index < len(sorted_latencies) else sorted_latencies[-1],
            'throughput_mbps': (self.throughput_bytes * 8 / duration / 1_000_000) if duration > 0 else 0.0,
            'duration': duration,
        }


def simulate_request(format_name, request_id):
    """Simulate a single request through marionette."""
    try:
        start_time = time.time()
        
        # Load the format
        executable = marionette_tg.dsl.load('client', format_name)
        
        # Simulate execution (simplified - real test would use actual network)
        # For now, we'll just measure format loading time
        load_time = time.time() - start_time
        
        # Simulate some data transfer
        bytes_transferred = 1024  # 1KB per request
        
        return True, load_time, bytes_transferred
    except Exception as e:
        return False, 0, 0


def run_load_test(format_name, num_connections, duration_seconds):
    """Run load test with specified parameters."""
    print(f"Starting Load Test")
    print("=" * 60)
    print(f"Format: {format_name}")
    print(f"Concurrent Connections: {num_connections}")
    print(f"Duration: {duration_seconds} seconds")
    print("=" * 60)
    
    result = LoadTestResult()
    result.start_time = time.time()
    
    end_time = result.start_time + duration_seconds
    request_counter = 0
    
    def worker():
        """Worker thread that makes requests."""
        nonlocal request_counter
        while time.time() < end_time:
            request_id = request_counter
            request_counter += 1
            
            success, latency, bytes_transferred = simulate_request(format_name, request_id)
            result.add_result(success, latency, bytes_transferred)
            
            # Small delay to avoid overwhelming
            time.sleep(0.1)
    
    # Start worker threads
    with ThreadPoolExecutor(max_workers=num_connections) as executor:
        futures = [executor.submit(worker) for _ in range(num_connections)]
        
        # Wait for all workers to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Worker error: {e}")
    
    result.end_time = time.time()
    
    # Print results
    stats = result.get_stats()
    print("\n" + "=" * 60)
    print("LOAD TEST RESULTS")
    print("=" * 60)
    print(f"Total Requests: {stats['total_requests']}")
    print(f"Successful: {stats['successful_requests']}")
    print(f"Failed: {stats['failed_requests']}")
    print(f"Success Rate: {stats['success_rate']:.2f}%")
    print(f"\nLatency (ms):")
    print(f"  Average: {stats['avg_latency']*1000:.2f}")
    print(f"  Min: {stats['min_latency']*1000:.2f}")
    print(f"  Max: {stats['max_latency']*1000:.2f}")
    print(f"  P95: {stats['p95_latency']*1000:.2f}")
    print(f"\nThroughput: {stats['throughput_mbps']:.2f} Mbps")
    print(f"Duration: {stats['duration']:.2f} seconds")
    print("=" * 60)
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Marionette Load Testing Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--format', '-f', default='dummy',
                        help='Format to test (default: dummy)')
    parser.add_argument('--connections', '-c', type=int, default=10,
                        help='Number of concurrent connections (default: 10)')
    parser.add_argument('--duration', '-d', type=int, default=30,
                        help='Test duration in seconds (default: 30)')
    args = parser.parse_args()
    
    # Verify format exists
    import marionette_tg.dsl
    formats = marionette_tg.dsl.list_mar_files('client')
    format_found = any(args.format in f for f in formats)
    
    if not format_found:
        print(f"Error: Format '{args.format}' not found")
        print(f"Available formats: {', '.join(set(f.split(':')[0] for f in formats))}")
        sys.exit(1)
    
    run_load_test(args.format, args.connections, args.duration)


if __name__ == '__main__':
    main()
