#!/usr/bin/env python3
"""
Example 6: Active Probing Resistance

This example demonstrates how marionette formats can resist active probing
by using error transitions to handle non-marionette connections gracefully.

Active probing resistance is important for:
- Avoiding detection by network analysis tools
- Handling legitimate traffic that isn't from marionette clients
- Maintaining plausible deniability

Usage:
    python examples/06_active_probing_resistance.py --format http_active_probing
"""

import sys
import argparse

sys.path.insert(0, '.')

import marionette.dsl


def analyze_probing_resistance(format_name):
    """Analyze a format's active probing resistance features."""
    print(f"Analyzing Active Probing Resistance")
    print("=" * 60)
    print(f"Format: {format_name}")
    print("=" * 60)
    
    try:
        # Load client format
        client_exec = marionette.dsl.load('client', format_name)
        
        # Check for error transitions
        error_transitions = []
        for state_name, state in client_exec.states_.items():
            error_state = state.get_error_transition()
            if error_state:
                error_transitions.append((state_name, error_state))
        
        print(f"\nError Transitions Found: {len(error_transitions)}")
        if error_transitions:
            print("  These states can handle non-marionette connections:")
            for src, dst in error_transitions:
                print(f"    {src} -> {dst} (error)")
        else:
            print("  ⚠ No error transitions found - format may not resist active probing")
        
        # Check for conditional actions (regex matching)
        conditional_actions = []
        for action in client_exec.actions_:
            if action.get_regex_match_incoming():
                conditional_actions.append(action)
        
        print(f"\nConditional Actions: {len(conditional_actions)}")
        if conditional_actions:
            print("  Actions with regex matching (can respond to probes):")
            for action in conditional_actions:
                print(f"    {action.get_module()}.{action.get_method()}")
                print(f"      Regex: {action.get_regex_match_incoming()}")
        
        # Load server format
        server_exec = marionette.dsl.load('server', format_name)
        
        # Check server-side error handling
        server_error_transitions = []
        for state_name, state in server_exec.states_.items():
            error_state = state.get_error_transition()
            if error_state:
                server_error_transitions.append((state_name, error_state))
        
        print(f"\nServer Error Transitions: {len(server_error_transitions)}")
        if server_error_transitions:
            print("  Server can handle unexpected connections:")
            for src, dst in server_error_transitions:
                print(f"    {src} -> {dst} (error)")
        
        # Summary
        print("\n" + "=" * 60)
        print("RESISTANCE ASSESSMENT")
        print("=" * 60)
        
        has_resistance = (len(error_transitions) > 0 or 
                         len(server_error_transitions) > 0 or
                         len(conditional_actions) > 0)
        
        if has_resistance:
            print("✓ Format has active probing resistance features")
            print("\nFeatures:")
            if error_transitions:
                print("  ✓ Error transitions for unexpected connections")
            if conditional_actions:
                print("  ✓ Conditional actions for probe detection")
            if server_error_transitions:
                print("  ✓ Server-side error handling")
        else:
            print("⚠ Format may be vulnerable to active probing")
            print("\nRecommendations:")
            print("  - Add error transitions to handle non-marionette connections")
            print("  - Use conditional actions with regex matching")
            print("  - Implement server-side decoy responses")
        
        return has_resistance
        
    except Exception as e:
        print(f"Error analyzing format: {e}")
        return False


def list_probing_formats():
    """List formats that have active probing resistance."""
    print("Formats with Active Probing Resistance")
    print("=" * 60)
    
    all_formats = set()
    for fmt in marionette.dsl.list_mar_files('client'):
        name = fmt.rsplit(':', 1)[0] if ':' in fmt else fmt
        all_formats.add(name)
    
    probing_formats = [f for f in all_formats if 'probing' in f.lower() or 'active' in f.lower()]
    
    if probing_formats:
        for fmt in sorted(probing_formats):
            print(f"  - {fmt}")
    else:
        print("  No formats with 'probing' in name found")
        print("\n  Checking all formats for resistance features...")
        
        resistant_formats = []
        for fmt in sorted(all_formats):
            try:
                if analyze_probing_resistance(fmt):
                    resistant_formats.append(fmt)
            except:
                pass
        
        if resistant_formats:
            print(f"\n  Formats with resistance features: {', '.join(resistant_formats)}")
        else:
            print("  No formats with resistance features found")


def main():
    parser = argparse.ArgumentParser(
        description='Active Probing Resistance Analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--format', '-f', help='Format to analyze')
    parser.add_argument('--list', '-l', action='store_true',
                        help='List formats with probing resistance')
    args = parser.parse_args()
    
    if args.list:
        list_probing_formats()
    elif args.format:
        success = analyze_probing_resistance(args.format)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python examples/06_active_probing_resistance.py --list")
        print("  python examples/06_active_probing_resistance.py --format http_active_probing")


if __name__ == '__main__':
    main()
