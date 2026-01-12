#!/usr/bin/env python3
"""
Example 3: Creating Custom Formats

This example demonstrates how to create and test custom marionette format files.
Shows the DSL syntax and how formats are parsed.

Usage:
    python examples/03_custom_format.py           # Show example format
    python examples/03_custom_format.py --parse   # Parse and validate example
"""

import sys
import argparse
import tempfile
import os

sys.path.insert(0, '.')

# Example custom format - a simple echo protocol
EXAMPLE_FORMAT = '''
# Simple Echo Format
# This format implements a basic echo protocol over TCP port 9000

connection(tcp, 9000):
  start      client   NULL        1.0
  client     server   send_msg    1.0
  server     end      recv_msg    1.0

action send_msg:
  client fte.send("^[a-zA-Z0-9]{1,128}$", 128)

action recv_msg:
  server fte.send("^[a-zA-Z0-9]{1,128}$", 128)
'''

# More complex format with probabilistic transitions
PROBABILISTIC_FORMAT = '''
# Probabilistic HTTP Format
# Randomly chooses between different response types

connection(tcp, 8080):
  start      request    NULL         1.0
  request    response   http_get     1.0
  response   end        http_ok      0.7
  response   end        http_error   0.3

action http_get:
  client fte.send("^GET /[a-zA-Z0-9/]* HTTP/1\\.1\\r\\n\\r\\n$", 256)

action http_ok:
  server fte.send("^HTTP/1\\.1 200 OK\\r\\n\\r\\n[a-zA-Z0-9]*$", 512)

action http_error:
  server fte.send("^HTTP/1\\.1 404 Not Found\\r\\n\\r\\n$", 64)
'''

# Format with error handling
ERROR_HANDLING_FORMAT = '''
# HTTP with Active Probing Resistance
# Uses error transitions to handle non-marionette connections

connection(tcp, 8080):
  start       upstream       NULL          1.0
  upstream    downstream     http_request  1.0
  upstream    downstream_err NULL          error
  downstream  end            http_response 1.0
  downstream_err end         http_decoy    1.0

action http_request:
  client fte.send("^GET /[a-zA-Z0-9]* HTTP/1\\.1\\r\\n\\r\\n$", 256)

action http_response:
  server fte.send("^HTTP/1\\.1 200 OK\\r\\n\\r\\n[a-zA-Z0-9]*$", 512)

action http_decoy:
  server io.puts("HTTP/1.1 200 OK\\r\\n\\r\\nHello World!") if regex_match_incoming("^GET / HTTP/1\\.(0|1).*")
  server io.puts("HTTP/1.1 404 Not Found\\r\\n\\r\\n") if regex_match_incoming("^.*")
'''


def show_formats():
    """Display example format templates."""
    print("=" * 60)
    print("MARIONETTE FORMAT EXAMPLES")
    print("=" * 60)
    
    print("\n1. SIMPLE ECHO FORMAT")
    print("-" * 40)
    print(EXAMPLE_FORMAT)
    
    print("\n2. PROBABILISTIC FORMAT")
    print("-" * 40)
    print(PROBABILISTIC_FORMAT)
    
    print("\n3. ERROR HANDLING FORMAT")
    print("-" * 40)
    print(ERROR_HANDLING_FORMAT)
    
    print("\n" + "=" * 60)
    print("FORMAT SYNTAX GUIDE")
    print("=" * 60)
    print("""
connection(protocol, port):
  - Defines the transport protocol (tcp/udp) and port
  - All state transitions are defined within

State Transitions:
  src dst action_name probability
  - src: source state ('start' is initial)
  - dst: destination state ('end' is terminal)
  - action_name: name of action block to execute
  - probability: 0.0-1.0 or 'error' for error transitions

Actions:
  action action_name:
    party plugin.method(args...)
    
  - party: 'client' or 'server'
  - plugins: fte, tg, io, model

Available Plugins:
  - fte.send(regex, max_len): FTE-encrypted send
  - fte.send_async(regex, max_len): Non-blocking FTE send
  - tg.send(grammar): Template grammar send
  - io.puts(string): Raw string output
  - io.gets(): Raw string input
  - model.sleep(seconds): Pause execution
  - model.spawn(format, count): Spawn sub-connections
""")


def parse_format(format_string, name="custom"):
    """Parse a format string and validate it."""
    import marionette.dsl
    
    # Write format to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mar', delete=False) as f:
        f.write(format_string)
        temp_path = f.name
    
    try:
        print(f"Parsing format: {name}")
        print("-" * 40)
        
        # Parse the format
        result = marionette.dsl.parse(temp_path)
        
        if result:
            print("✓ Format parsed successfully!")
            print(f"  States: {list(result.states_.keys())}")
            print(f"  Actions: {len(result.actions_)}")
            return True
        else:
            print("✗ Format parsing failed")
            return False
            
    except Exception as e:
        print(f"✗ Parse error: {e}")
        return False
    finally:
        os.unlink(temp_path)


def main():
    parser = argparse.ArgumentParser(
        description='Custom Format Examples',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--parse', '-p', action='store_true',
                        help='Parse and validate example formats')
    args = parser.parse_args()
    
    if args.parse:
        print("Validating Example Formats")
        print("=" * 60)
        
        formats = [
            (EXAMPLE_FORMAT, "Simple Echo"),
            (PROBABILISTIC_FORMAT, "Probabilistic HTTP"),
            (ERROR_HANDLING_FORMAT, "Error Handling"),
        ]
        
        passed = 0
        for fmt, name in formats:
            print()
            if parse_format(fmt, name):
                passed += 1
        
        print(f"\n{'=' * 60}")
        print(f"Results: {passed}/{len(formats)} formats valid")
        sys.exit(0 if passed == len(formats) else 1)
    else:
        show_formats()


if __name__ == '__main__':
    main()
