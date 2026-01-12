#!/usr/bin/env python3
"""
Example 10: Custom Protocol Implementation

This example shows how to implement a complete custom protocol using marionette,
from format definition to client/server implementation.

Usage:
    python examples/10_custom_protocol.py --create-format
    python examples/10_custom_protocol.py --test-format my_protocol
"""

import sys
import argparse
import os
import tempfile

sys.path.insert(0, '.')

import marionette.dsl


# Example: Simple Chat Protocol
CHAT_PROTOCOL_FORMAT = '''
# Simple Chat Protocol
# Implements a basic chat protocol over TCP port 9999

connection(tcp, 9999):
  start      client   NULL          1.0
  client     server   send_message  1.0
  server     client   recv_message  1.0
  client     end      disconnect    1.0

action send_message:
  client fte.send("^MSG:[a-zA-Z0-9 ]{1,256}$", 256)

action recv_message:
  server fte.send("^ACK:[a-zA-Z0-9 ]{1,256}$", 256)

action disconnect:
  client io.puts("BYE")
'''

# Example: File Transfer Protocol
FILE_TRANSFER_FORMAT = '''
# File Transfer Protocol
# Transfers files in chunks with checksums

connection(tcp, 8888):
  start      client   NULL           1.0
  client     server   send_chunk      1.0
  server     client   send_checksum   1.0
  client     server   send_chunk      0.8
  client     end      transfer_done   0.2

action send_chunk:
  client fte.send("^CHUNK:[0-9]+:[a-zA-Z0-9+/=]{1,1024}$", 1024)

action send_checksum:
  server fte.send("^CHECKSUM:[a-f0-9]{32}$", 32)

action transfer_done:
  client io.puts("DONE")
'''


def create_format_file(format_name, format_content, output_dir='.'):
    """Create a .mar format file."""
    format_path = os.path.join(output_dir, f"{format_name}.mar")
    
    with open(format_path, 'w') as f:
        f.write(format_content)
    
    print(f"Created format file: {format_path}")
    return format_path


def test_format(format_path):
    """Test a format file by parsing it."""
    print(f"\nTesting format: {format_path}")
    print("-" * 60)
    
    try:
        executable = marionette.dsl.load('client', format_path)
        
        print("✓ Format parsed successfully!")
        print(f"  States: {list(executable.states_.keys())}")
        print(f"  Actions: {len(executable.actions_)}")
        
        return True
    except Exception as e:
        print(f"✗ Format parsing failed: {e}")
        return False


def show_protocol_templates():
    """Show example protocol templates."""
    print("Custom Protocol Templates")
    print("=" * 60)
    
    print("\n1. CHAT PROTOCOL")
    print("-" * 40)
    print("Features:")
    print("  - Bidirectional messaging")
    print("  - Message acknowledgment")
    print("  - Graceful disconnect")
    print("\nFormat:")
    print(CHAT_PROTOCOL_FORMAT)
    
    print("\n2. FILE TRANSFER PROTOCOL")
    print("-" * 40)
    print("Features:")
    print("  - Chunked file transfer")
    print("  - Checksum verification")
    print("  - Probabilistic completion")
    print("\nFormat:")
    print(FILE_TRANSFER_FORMAT)
    
    print("\n" + "=" * 60)
    print("IMPLEMENTATION STEPS")
    print("=" * 60)
    print("""
1. Define your protocol format in a .mar file
   - Specify connection type (tcp/udp) and port
   - Define state transitions
   - Create action blocks

2. Test your format:
   python examples/10_custom_protocol.py --test-format my_protocol.mar

3. Use the format in your client/server:
   client = marionette.Client('my_protocol', None)
   server = marionette.Server('my_protocol')

4. Integrate with your application logic
""")


def main():
    parser = argparse.ArgumentParser(
        description='Custom Protocol Implementation Guide',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--create-format', '-c', 
                        choices=['chat', 'file-transfer'],
                        help='Create example format file')
    parser.add_argument('--test-format', '-t',
                        help='Test a format file')
    parser.add_argument('--output-dir', '-o', default='.',
                        help='Output directory for format files')
    args = parser.parse_args()
    
    if args.create_format:
        if args.create_format == 'chat':
            create_format_file('chat_protocol', CHAT_PROTOCOL_FORMAT, args.output_dir)
        elif args.create_format == 'file-transfer':
            create_format_file('file_transfer', FILE_TRANSFER_FORMAT, args.output_dir)
    elif args.test_format:
        if os.path.exists(args.test_format):
            test_format(args.test_format)
        else:
            # Try to find it in formats directory
            format_path = marionette.dsl.find_format_file('client', args.test_format)
            if format_path:
                test_format(format_path)
            else:
                print(f"Error: Format file not found: {args.test_format}")
                sys.exit(1)
    else:
        show_protocol_templates()


if __name__ == '__main__':
    main()
