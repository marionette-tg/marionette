# Marionette Examples

This directory contains example scripts and utilities for working with Marionette.

## Helper Utilities

### socksserver

A simple SOCKS4 proxy server. Used as a backend for the marionette server to forward traffic.

```bash
./examples/socksserver --local_port 8081
```

### httpserver

A simple HTTP server for testing. Returns a large response body for benchmarking.

```bash
./examples/httpserver --local_port 8080
```

## Development Tools

### benchmark

Performance benchmarking tool. Measures throughput by sending requests through marionette.

```bash
./examples/benchmark [format_name]
```

### simulate

Simulates marionette format execution to analyze capacity and timing characteristics.

```bash
./examples/simulate <format_name> <latency_ms>
```

## Quick Start Example

Start a complete marionette tunnel:

```bash
# Terminal 1: Start the backend SOCKS server
./examples/socksserver --local_port 8081

# Terminal 2: Start the marionette server
./bin/marionette_server --server_ip 127.0.0.1 --proxy_ip 127.0.0.1 --proxy_port 8081 --format dummy

# Terminal 3: Start the marionette client  
./bin/marionette_client --server_ip 127.0.0.1 --client_ip 127.0.0.1 --client_port 8079 --format dummy

# Terminal 4: Test the connection
curl --socks4a 127.0.0.1:8079 http://example.com
```

## See Also

- Main entry points: `bin/marionette_client`, `bin/marionette_server`
- Format definitions: `marionette/formats/`
- Full documentation: [README.md](../README.md)
