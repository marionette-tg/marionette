#!/usr/bin/env python3
"""
Example 9: Format Comparison and Benchmarking

This example compares different formats side-by-side, showing their
characteristics, performance estimates, and use cases.

Usage:
    python examples/09_format_comparison.py
    python examples/09_format_comparison.py --format http_simple_blocking
"""

import sys
import argparse

sys.path.insert(0, '.')

import marionette.dsl
import marionette.plugins._tg


def get_format_info(format_name):
    """Get detailed information about a format."""
    info = {
        'name': format_name,
        'client_version': None,
        'server_version': None,
        'states': [],
        'actions': [],
        'has_error_handling': False,
        'has_async': False,
    }
    
    try:
        # Client info
        client_version = marionette.dsl.get_latest_version('client', format_name)
        info['client_version'] = client_version
        client_exec = marionette.dsl.load('client', format_name, client_version)
        info['states'] = list(client_exec.states_.keys())
        info['actions'] = len(client_exec.actions_)
        
        # Check for error handling
        for state_name, state in client_exec.states_.items():
            if state.get_error_transition():
                info['has_error_handling'] = True
                break
        
        # Check for async operations
        for action in client_exec.actions_:
            if 'async' in action.get_method():
                info['has_async'] = True
                break
        
        # Server info
        try:
            server_version = marionette.dsl.get_latest_version('server', format_name)
            info['server_version'] = server_version
        except:
            pass
        
    except Exception as e:
        info['error'] = str(e)
    
    return info


def compare_all_formats():
    """Compare all available formats."""
    print("Format Comparison Report")
    print("=" * 80)
    
    all_formats = set()
    for fmt in marionette.dsl.list_mar_files('client'):
        name = fmt.rsplit(':', 1)[0] if ':' in fmt else fmt
        all_formats.add(name)
    
    formats_info = []
    for fmt in sorted(all_formats):
        info = get_format_info(fmt)
        formats_info.append(info)
    
    # Print comparison table
    print(f"\n{'Format':<35} {'Version':<12} {'States':<8} {'Actions':<8} {'Features':<20}")
    print("-" * 80)
    
    for info in formats_info:
        if 'error' in info:
            continue
        
        features = []
        if info['has_error_handling']:
            features.append('error-handling')
        if info['has_async']:
            features.append('async')
        
        version = info['client_version'] or 'N/A'
        features_str = ', '.join(features) if features else 'none'
        
        print(f"{info['name']:<35} {version:<12} {len(info['states']):<8} {info['actions']:<8} {features_str:<20}")
    
    print("\n" + "=" * 80)
    print(f"Total formats: {len([f for f in formats_info if 'error' not in f])}")


def show_format_details(format_name):
    """Show detailed information about a specific format."""
    info = get_format_info(format_name)
    
    if 'error' in info:
        print(f"Error: {info['error']}")
        return
    
    print(f"\nFormat Details: {info['name']}")
    print("=" * 60)
    
    print(f"\nVersions:")
    print(f"  Client: {info['client_version'] or 'N/A'}")
    print(f"  Server: {info['server_version'] or 'N/A'}")
    
    print(f"\nStructure:")
    print(f"  States: {len(info['states'])}")
    for state in info['states']:
        print(f"    - {state}")
    print(f"  Actions: {info['actions']}")
    
    print(f"\nFeatures:")
    print(f"  Error Handling: {'Yes' if info['has_error_handling'] else 'No'}")
    print(f"  Async Operations: {'Yes' if info['has_async'] else 'No'}")
    
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Format Comparison Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--format', '-f', help='Show details for specific format')
    args = parser.parse_args()
    
    if args.format:
        show_format_details(args.format)
    else:
        compare_all_formats()


if __name__ == '__main__':
    main()
