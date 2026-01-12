#!/usr/bin/env python3
"""
Example 1: Basic HTTP Tunnel

This example demonstrates how to create a basic HTTP tunnel using marionette.
The tunnel disguises traffic as HTTP requests/responses.

Usage:
    # Start the tunnel (run each in a separate terminal):
    python examples/01_http_tunnel.py server
    python examples/01_http_tunnel.py client
    
    # Test with curl:
    curl --socks4a 127.0.0.1:8079 http://example.com
"""

import sys
import argparse

# Add parent directory to path for imports
sys.path.insert(0, '.')

from twisted.internet import defer, protocol, reactor
from twisted.protocols import socks
from twisted.python import log

import marionette_tg
import marionette_tg.conf


# Configuration
FORMAT = 'http_simple_blocking'
CLIENT_IP = '127.0.0.1'
CLIENT_PORT = 8079
SERVER_IP = '127.0.0.1'
PROXY_IP = '127.0.0.1'
PROXY_PORT = 8081


class ProxyClient(protocol.Protocol):
    """Client-side protocol that bridges SOCKS connections to marionette."""
    
    def connectionMade(self):
        log.msg("ProxyClient: Connection established")
        self.srv_queue = defer.DeferredQueue()
        self.srv_queue.get().addCallback(self.clientDataReceived)
        self.client_stream_ = self.factory.marionette_client.start_new_stream(self.srv_queue)

    def clientDataReceived(self, chunk):
        log.msg(f"ProxyClient: Received {len(chunk)} bytes from server")
        self.transport.write(chunk)
        self.srv_queue.get().addCallback(self.clientDataReceived)

    def dataReceived(self, chunk):
        log.msg(f"ProxyClient: Sending {len(chunk)} bytes to server")
        self.client_stream_.push(chunk)

    def connectionLost(self, why):
        log.msg(f"ProxyClient: Connection lost - {why}")
        self.client_stream_.terminate()


class ProxyServerProtocol(protocol.Protocol):
    """Server-side protocol that forwards to the actual destination."""
    
    def connectionMade(self):
        log.msg("ProxyServerProtocol: Connected to destination")
        self.cli_queue = self.factory.cli_queue
        self.cli_queue.get().addCallback(self.serverDataReceived)

    def serverDataReceived(self, chunk):
        if chunk is False:
            self.cli_queue = None
            self.factory.continueTrying = False
            self.transport.loseConnection()
        elif self.cli_queue:
            log.msg(f"ProxyServerProtocol: Forwarding {len(chunk)} bytes to destination")
            self.transport.write(chunk)
            self.cli_queue.get().addCallback(self.serverDataReceived)

    def dataReceived(self, chunk):
        log.msg(f"ProxyServerProtocol: Received {len(chunk)} bytes from destination")
        self.factory.srv_queue.put(chunk)

    def connectionLost(self, why):
        log.msg(f"ProxyServerProtocol: Connection lost - {why}")
        if self.cli_queue:
            self.cli_queue = None


class ProxyServerFactory(protocol.ClientFactory):
    protocol = ProxyServerProtocol

    def __init__(self, srv_queue, cli_queue):
        self.srv_queue = srv_queue
        self.cli_queue = cli_queue


class ProxyServer:
    """Server-side handler for marionette streams."""
    
    def __init__(self):
        self.connector = None

    def connectionMade(self, marionette_stream):
        log.msg("ProxyServer: New marionette stream")
        self.cli_queue = defer.DeferredQueue()
        self.srv_queue = defer.DeferredQueue()
        self.marionette_stream = marionette_stream
        self.srv_queue.get().addCallback(self.clientDataReceived)

        self.factory = ProxyServerFactory(self.srv_queue, self.cli_queue)
        self.connector = reactor.connectTCP(PROXY_IP, PROXY_PORT, self.factory)

    def clientDataReceived(self, chunk):
        log.msg(f"ProxyServer: Sending {len(chunk)} bytes back through marionette")
        self.marionette_stream.push(chunk)
        self.srv_queue.get().addCallback(self.clientDataReceived)

    def dataReceived(self, chunk):
        log.msg(f"ProxyServer: Received {len(chunk)} bytes from marionette")
        self.cli_queue.put(chunk)

    def connectionLost(self):
        log.msg("ProxyServer: Connection lost")
        self.cli_queue.put(False)
        if self.connector:
            self.connector.disconnect()


def run_client(debug=False):
    """Run the marionette client."""
    if debug:
        log.startLogging(sys.stdout)
    
    print(f"Starting marionette client...")
    print(f"  Format: {FORMAT}")
    print(f"  Listen: {CLIENT_IP}:{CLIENT_PORT}")
    print(f"  Server: {SERVER_IP}")
    print(f"\nTest with: curl --socks4a {CLIENT_IP}:{CLIENT_PORT} http://example.com")
    
    marionette_tg.conf.set('server.server_ip', SERVER_IP)
    marionette_tg.conf.set('client.client_ip', CLIENT_IP)
    marionette_tg.conf.set('client.client_port', CLIENT_PORT)
    
    client = marionette_tg.Client(FORMAT, None)
    
    factory = protocol.Factory()
    factory.protocol = ProxyClient
    factory.marionette_client = client
    
    reactor.listenTCP(CLIENT_PORT, factory, interface=CLIENT_IP)
    reactor.callFromThread(client.execute, reactor)
    reactor.run()


def run_server(debug=False):
    """Run the marionette server."""
    if debug:
        log.startLogging(sys.stdout)
    
    print(f"Starting marionette server...")
    print(f"  Format: {FORMAT}")
    print(f"  Listen: {SERVER_IP}")
    print(f"  Proxy to: {PROXY_IP}:{PROXY_PORT}")
    print(f"\nMake sure a SOCKS server is running on {PROXY_IP}:{PROXY_PORT}")
    
    marionette_tg.conf.set('server.server_ip', SERVER_IP)
    marionette_tg.conf.set('server.proxy_ip', PROXY_IP)
    marionette_tg.conf.set('server.proxy_port', PROXY_PORT)
    
    server = marionette_tg.Server(FORMAT)
    server.factory = ProxyServer
    
    reactor.callFromThread(server.execute, reactor)
    reactor.run()


def run_socks_backend(debug=False):
    """Run a simple SOCKS4 server as the backend."""
    if debug:
        log.startLogging(sys.stdout)
    
    print(f"Starting SOCKS4 backend server on {PROXY_IP}:{PROXY_PORT}...")
    
    reactor.listenTCP(PROXY_PORT, socks.SOCKSv4Factory(None), interface=PROXY_IP)
    reactor.run()


def main():
    parser = argparse.ArgumentParser(description='HTTP Tunnel Example')
    parser.add_argument('mode', choices=['client', 'server', 'backend'],
                        help='Run as client, server, or backend SOCKS server')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Enable debug output')
    args = parser.parse_args()
    
    if args.mode == 'client':
        run_client(args.debug)
    elif args.mode == 'server':
        run_server(args.debug)
    elif args.mode == 'backend':
        run_socks_backend(args.debug)


if __name__ == '__main__':
    main()
