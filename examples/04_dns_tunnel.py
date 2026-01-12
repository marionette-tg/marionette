#!/usr/bin/env python3
"""
Example 4: DNS Tunnel

This example demonstrates how to create a DNS tunnel using marionette.
DNS tunneling is useful for bypassing network restrictions that only allow DNS traffic.

Usage:
    # Start the tunnel (run each in a separate terminal):
    python examples/04_dns_tunnel.py server
    python examples/04_dns_tunnel.py client
    
    # Test with dig:
    dig @127.0.0.1 -p 53535 example.com
"""

import sys
import argparse
import socket

sys.path.insert(0, '.')

from twisted.internet import defer, protocol, reactor
from twisted.internet.protocol import DatagramProtocol
from twisted.python import log

import marionette_tg
import marionette_tg.conf


# Configuration
FORMAT = 'dns_request'
CLIENT_IP = '127.0.0.1'
CLIENT_PORT = 53535
SERVER_IP = '127.0.0.1'
SERVER_PORT = 53536
PROXY_IP = '127.0.0.1'
PROXY_PORT = 53  # Standard DNS port


class DNSClientProtocol(DatagramProtocol):
    """UDP client protocol for DNS tunneling."""
    
    def __init__(self, marionette_client):
        self.marionette_client = marionette_client
        self.streams = {}
        self.stream_counter = 0

    def datagramReceived(self, data, addr):
        """Handle incoming DNS query."""
        log.msg(f"DNSClient: Received {len(data)} bytes from {addr}")
        
        # Create a new stream for this DNS query
        stream = self.marionette_client.start_new_stream()
        self.streams[self.stream_counter] = (stream, addr)
        
        # Push the DNS query through marionette
        stream.push(data)
        
        # Set up callback to receive response
        def handle_response(response_data):
            if response_data:
                log.msg(f"DNSClient: Sending {len(response_data)} bytes to {addr}")
                self.transport.write(response_data, addr)
        
        # This is simplified - in practice you'd need proper stream management
        self.stream_counter += 1

    def sendQuery(self, query, addr):
        """Send a DNS query through marionette."""
        log.msg(f"DNSClient: Sending query to {addr}")
        self.datagramReceived(query, addr)


class DNSServerProtocol(DatagramProtocol):
    """UDP server protocol that forwards to real DNS server."""
    
    def __init__(self, marionette_server):
        self.marionette_server = marionette_server
        self.streams = {}

    def datagramReceived(self, data, addr):
        """Handle incoming marionette-encrypted DNS query."""
        log.msg(f"DNSServer: Received {len(data)} bytes from {addr}")
        
        # Forward to real DNS server
        d = reactor.resolve(addr[0])
        d.addCallback(self._forwardToDNS, data, addr)
        d.addErrback(self._handleError, addr)

    def _forwardToDNS(self, ip, data, client_addr):
        """Forward query to real DNS server."""
        log.msg(f"DNSServer: Forwarding to DNS server {PROXY_IP}:{PROXY_PORT}")
        
        # Create UDP connection to real DNS server
        transport = reactor.listenUDP(0, self)
        
        def sendQuery():
            transport.write(data, (PROXY_IP, PROXY_PORT))
        
        reactor.callLater(0, sendQuery)

    def _handleError(self, failure, addr):
        """Handle DNS resolution errors."""
        log.msg(f"DNSServer: Error - {failure}")


def run_client(debug=False):
    """Run the marionette DNS client."""
    if debug:
        log.startLogging(sys.stdout)
    
    print(f"Starting marionette DNS client...")
    print(f"  Format: {FORMAT}")
    print(f"  Listen: {CLIENT_IP}:{CLIENT_PORT} (UDP)")
    print(f"  Server: {SERVER_IP}:{SERVER_PORT}")
    print(f"\nTest with: dig @{CLIENT_IP} -p {CLIENT_PORT} example.com")
    
    marionette_tg.conf.set('server.server_ip', SERVER_IP)
    marionette_tg.conf.set('client.client_ip', CLIENT_IP)
    marionette_tg.conf.set('client.client_port', CLIENT_PORT)
    
    client = marionette_tg.Client(FORMAT, None)
    
    protocol = DNSClientProtocol(client)
    reactor.listenUDP(CLIENT_PORT, protocol, interface=CLIENT_IP)
    reactor.callFromThread(client.execute, reactor)
    reactor.run()


def run_server(debug=False):
    """Run the marionette DNS server."""
    if debug:
        log.startLogging(sys.stdout)
    
    print(f"Starting marionette DNS server...")
    print(f"  Format: {FORMAT}")
    print(f"  Listen: {SERVER_IP}:{SERVER_PORT} (UDP)")
    print(f"  Forward to: {PROXY_IP}:{PROXY_PORT} (real DNS)")
    
    marionette_tg.conf.set('server.server_ip', SERVER_IP)
    marionette_tg.conf.set('server.proxy_ip', PROXY_IP)
    marionette_tg.conf.set('server.proxy_port', PROXY_PORT)
    
    server = marionette_tg.Server(FORMAT)
    
    protocol = DNSServerProtocol(server)
    reactor.listenUDP(SERVER_PORT, protocol, interface=SERVER_IP)
    reactor.callFromThread(server.execute, reactor)
    reactor.run()


def main():
    parser = argparse.ArgumentParser(description='DNS Tunnel Example')
    parser.add_argument('mode', choices=['client', 'server'],
                        help='Run as client or server')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Enable debug output')
    args = parser.parse_args()
    
    if args.mode == 'client':
        run_client(args.debug)
    elif args.mode == 'server':
        run_server(args.debug)


if __name__ == '__main__':
    main()
