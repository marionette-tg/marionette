#!/usr/bin/env python3
"""
Example 8: Traffic Shaping

This example demonstrates how to shape traffic patterns to match specific
characteristics, such as timing, packet sizes, and burst patterns.

Usage:
    python examples/08_traffic_shaping.py --format http_simple_blocking --analyze
"""

import sys
import argparse
import time
import statistics

sys.path.insert(0, '.')

import marionette_tg.dsl


class TrafficAnalyzer:
    """Analyzes traffic patterns from format definitions."""
    
    def __init__(self, format_name):
        self.format_name = format_name
        self.actions = []
        self.states = []
        
    def analyze(self):
        """Analyze the format's traffic characteristics."""
        try:
            executable = marionette_tg.dsl.load('client', self.format_name)
            
            # Extract state information
            self.states = list(executable.states_.keys())
            
            # Extract action information
            for action in executable.actions_:
                action_info = {
                    'module': action.get_module(),
                    'method': action.get_method(),
                    'args': action.get_args(),
                }
                self.actions.append(action_info)
            
            return True
        except Exception as e:
            print(f"Error analyzing format: {e}")
            return False
    
    def get_timing_characteristics(self):
        """Estimate timing characteristics."""
        # Count blocking vs non-blocking operations
        blocking = sum(1 for a in self.actions 
                      if a['method'] in ['send', 'recv'] and 'async' not in a['method'])
        non_blocking = sum(1 for a in self.actions 
                          if 'async' in a['method'])
        
        return {
            'blocking_ops': blocking,
            'non_blocking_ops': non_blocking,
            'total_ops': len(self.actions),
        }
    
    def get_capacity_characteristics(self):
        """Estimate capacity characteristics."""
        capacities = []
        
        for action in self.actions:
            if action['module'] == 'fte' and action['args']:
                # FTE capacity is typically in the args
                if len(action['args']) >= 2:
                    capacities.append(action['args'][1])  # msg_len parameter
        
        if capacities:
            return {
                'min_capacity': min(capacities),
                'max_capacity': max(capacities),
                'avg_capacity': statistics.mean(capacities),
            }
        return None
    
    def print_report(self):
        """Print analysis report."""
        print(f"\nTraffic Analysis: {self.format_name}")
        print("=" * 60)
        
        print(f"\nStates: {len(self.states)}")
        for state in self.states:
            print(f"  - {state}")
        
        print(f"\nActions: {len(self.actions)}")
        for action in self.actions:
            print(f"  - {action['module']}.{action['method']}({', '.join(map(str, action['args']))})")
        
        timing = self.get_timing_characteristics()
        print(f"\nTiming Characteristics:")
        print(f"  Blocking operations: {timing['blocking_ops']}")
        print(f"  Non-blocking operations: {timing['non_blocking_ops']}")
        print(f"  Total operations: {timing['total_ops']}")
        
        capacity = self.get_capacity_characteristics()
        if capacity:
            print(f"\nCapacity Characteristics:")
            print(f"  Min: {capacity['min_capacity']} bytes")
            print(f"  Max: {capacity['max_capacity']} bytes")
            print(f"  Average: {capacity['avg_capacity']:.0f} bytes")
        
        print("=" * 60)


def compare_formats(format_names):
    """Compare multiple formats."""
    print("Format Comparison")
    print("=" * 60)
    
    results = {}
    for fmt in format_names:
        analyzer = TrafficAnalyzer(fmt)
        if analyzer.analyze():
            results[fmt] = {
                'timing': analyzer.get_timing_characteristics(),
                'capacity': analyzer.get_capacity_characteristics(),
                'states': len(analyzer.states),
                'actions': len(analyzer.actions),
            }
    
    # Print comparison table
    print(f"\n{'Format':<30} {'States':<10} {'Actions':<10} {'Blocking':<10} {'Capacity':<15}")
    print("-" * 75)
    
    for fmt, data in results.items():
        capacity_str = f"{data['capacity']['avg_capacity']:.0f}" if data['capacity'] else "N/A"
        print(f"{fmt:<30} {data['states']:<10} {data['actions']:<10} {data['timing']['blocking_ops']:<10} {capacity_str:<15}")


def main():
    parser = argparse.ArgumentParser(
        description='Traffic Shaping Analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--format', '-f', help='Format to analyze')
    parser.add_argument('--compare', '-c', help='Comma-separated formats to compare')
    parser.add_argument('--analyze', '-a', action='store_true',
                        help='Show detailed analysis')
    args = parser.parse_args()
    
    if args.compare:
        formats = [f.strip() for f in args.compare.split(',')]
        compare_formats(formats)
    elif args.format:
        analyzer = TrafficAnalyzer(args.format)
        if analyzer.analyze():
            analyzer.print_report()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
