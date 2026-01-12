#!/usr/bin/env python3
"""
Example 7: Multi-Format Switching

This example demonstrates how to dynamically switch between multiple formats
during a session. Useful for evading detection by rotating traffic patterns.

Usage:
    python examples/07_multi_format_switching.py --formats http_simple_blocking,https_simple_blocking --switch-interval 30
"""

import sys
import argparse
import time
import threading

sys.path.insert(0, '.')

import marionette_tg
import marionette_tg.conf


class FormatSwitcher:
    """Manages switching between multiple formats."""
    
    def __init__(self, formats, switch_interval=30):
        self.formats = formats
        self.switch_interval = switch_interval
        self.current_index = 0
        self.switch_count = 0
        self.running = False
        
    def get_current_format(self):
        """Get the currently active format."""
        return self.formats[self.current_index]
    
    def switch_format(self):
        """Switch to the next format in rotation."""
        if len(self.formats) <= 1:
            return False
        
        self.current_index = (self.current_index + 1) % len(self.formats)
        self.switch_count += 1
        return True
    
    def start_switching(self, client):
        """Start automatic format switching."""
        self.running = True
        
        def switch_loop():
            while self.running:
                time.sleep(self.switch_interval)
                if self.running:
                    old_format = self.get_current_format()
                    self.switch_format()
                    new_format = self.get_current_format()
                    
                    print(f"[Format Switch #{self.switch_count}] {old_format} -> {new_format}")
                    
                    # Reload the driver with new format
                    client.reload_driver()
        
        thread = threading.Thread(target=switch_loop, daemon=True)
        thread.start()
        return thread
    
    def stop_switching(self):
        """Stop automatic format switching."""
        self.running = False


def run_client(formats, switch_interval, debug=False):
    """Run client with format switching."""
    if len(formats) == 0:
        print("Error: At least one format required")
        return
    
    print("Multi-Format Switching Client")
    print("=" * 60)
    print(f"Formats: {', '.join(formats)}")
    print(f"Switch Interval: {switch_interval} seconds")
    print("=" * 60)
    
    marionette_tg.conf.set('client.client_ip', '127.0.0.1')
    marionette_tg.conf.set('client.client_port', 8079)
    marionette_tg.conf.set('server.server_ip', '127.0.0.1')
    
    if debug:
        from twisted.python import log
        log.startLogging(sys.stdout)
    
    # Start with first format
    switcher = FormatSwitcher(formats, switch_interval)
    client = marionette_tg.Client(switcher.get_current_format(), None)
    
    # Start format switching
    switcher.start_switching(client)
    
    print(f"\nStarting client with format: {switcher.get_current_format()}")
    print("Format will switch automatically every {} seconds".format(switch_interval))
    print("Press Ctrl+C to stop\n")
    
    try:
        from twisted.internet import reactor
        reactor.callFromThread(client.execute, reactor)
        reactor.run()
    except KeyboardInterrupt:
        print("\nStopping format switching...")
        switcher.stop_switching()
        print(f"Total format switches: {switcher.switch_count}")


def main():
    parser = argparse.ArgumentParser(
        description='Multi-Format Switching Example',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--formats', '-f', required=True,
                        help='Comma-separated list of formats (e.g., http_simple_blocking,https_simple_blocking)')
    parser.add_argument('--switch-interval', '-i', type=int, default=30,
                        help='Seconds between format switches (default: 30)')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Enable debug output')
    args = parser.parse_args()
    
    formats = [f.strip() for f in args.formats.split(',')]
    
    # Verify formats exist
    import marionette_tg.dsl
    available = marionette_tg.dsl.list_mar_files('client')
    available_names = {f.split(':')[0] for f in available}
    
    invalid = [f for f in formats if f not in available_names]
    if invalid:
        print(f"Error: Invalid formats: {', '.join(invalid)}")
        print(f"Available formats: {', '.join(sorted(available_names))}")
        sys.exit(1)
    
    run_client(formats, args.switch_interval, args.debug)


if __name__ == '__main__':
    main()
