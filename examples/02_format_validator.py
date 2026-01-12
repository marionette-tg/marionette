#!/usr/bin/env python3
"""
Example 2: Format Validator

This example demonstrates how to validate and inspect marionette format files (.mar).
Useful for testing custom formats before deployment.

Usage:
    python examples/02_format_validator.py                    # List all formats
    python examples/02_format_validator.py http_simple_blocking  # Validate specific format
    python examples/02_format_validator.py --all              # Validate all formats
"""

import sys
import argparse

sys.path.insert(0, '.')

import marionette_tg.dsl


def list_formats():
    """List all available formats."""
    print("Available Marionette Formats")
    print("=" * 50)
    
    client_formats = marionette_tg.dsl.list_mar_files('client')
    server_formats = marionette_tg.dsl.list_mar_files('server')
    
    all_formats = set(client_formats) | set(server_formats)
    
    for fmt in sorted(all_formats):
        name, version = fmt.rsplit(':', 1) if ':' in fmt else (fmt, 'unknown')
        client_ok = fmt in client_formats
        server_ok = fmt in server_formats
        
        status = []
        if client_ok:
            status.append('client')
        if server_ok:
            status.append('server')
        
        print(f"  {name:<40} v{version:<10} [{', '.join(status)}]")
    
    print(f"\nTotal: {len(all_formats)} formats")


def validate_format(format_name, verbose=False):
    """Validate a specific format."""
    print(f"\nValidating format: {format_name}")
    print("-" * 50)
    
    errors = []
    warnings = []
    
    # Check if format exists for client
    try:
        client_version = marionette_tg.dsl.get_latest_version('client', format_name)
        print(f"✓ Client format found (version: {client_version})")
        
        # Try to load and parse
        client_exec = marionette_tg.dsl.load('client', format_name, client_version)
        if client_exec:
            print(f"✓ Client format parses successfully")
            if verbose:
                print(f"  States: {list(client_exec.states_.keys())}")
        else:
            errors.append("Client format failed to load")
    except Exception as e:
        errors.append(f"Client format error: {e}")
    
    # Check if format exists for server
    try:
        server_version = marionette_tg.dsl.get_latest_version('server', format_name)
        print(f"✓ Server format found (version: {server_version})")
        
        server_exec = marionette_tg.dsl.load('server', format_name, server_version)
        if server_exec:
            print(f"✓ Server format parses successfully")
            if verbose:
                print(f"  States: {list(server_exec.states_.keys())}")
        else:
            errors.append("Server format failed to load")
    except Exception as e:
        errors.append(f"Server format error: {e}")
    
    # Summary
    print()
    if errors:
        print("ERRORS:")
        for err in errors:
            print(f"  ✗ {err}")
        return False
    else:
        print("✓ Format validation passed!")
        return True


def validate_all_formats():
    """Validate all available formats."""
    print("Validating All Formats")
    print("=" * 50)
    
    all_formats = set()
    for fmt in marionette_tg.dsl.list_mar_files('client'):
        name = fmt.rsplit(':', 1)[0] if ':' in fmt else fmt
        all_formats.add(name)
    for fmt in marionette_tg.dsl.list_mar_files('server'):
        name = fmt.rsplit(':', 1)[0] if ':' in fmt else fmt
        all_formats.add(name)
    
    passed = 0
    failed = 0
    
    for fmt in sorted(all_formats):
        try:
            if validate_format(fmt):
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ✗ {fmt}: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0


def main():
    parser = argparse.ArgumentParser(
        description='Validate Marionette format files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                     List all available formats
  %(prog)s http_simple_blocking   Validate a specific format
  %(prog)s --all               Validate all formats
  %(prog)s -v dummy            Validate with verbose output
        """)
    parser.add_argument('format', nargs='?', help='Format name to validate')
    parser.add_argument('--all', '-a', action='store_true',
                        help='Validate all formats')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show verbose output')
    args = parser.parse_args()
    
    if args.all:
        success = validate_all_formats()
        sys.exit(0 if success else 1)
    elif args.format:
        success = validate_format(args.format, args.verbose)
        sys.exit(0 if success else 1)
    else:
        list_formats()


if __name__ == '__main__':
    main()
