# marionette

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/marionette-tg.svg)](https://pypi.org/project/marionette-tg/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/marionette-tg/marionette/actions/workflows/ci.yml/badge.svg)](https://github.com/marionette-tg/marionette/actions/workflows/ci.yml)

## Overview

Marionette is a programmable client-server proxy that enables the user to control network traffic features with a lightweight domain-specific language.

### References

1. [Protocol Misidentification Made Easy with Format-Transforming Encryption](https://kpdyer.com/publications/ccs2013-fte.pdf)
2. [Marionette: A Programmable Network Traffic Obfuscation System](https://kpdyer.com/publications/usenix2015-marionette.pdf)

## Installation

### From PyPI

```bash
pip install marionette-tg
```

### From Source

```bash
git clone https://github.com/marionette-tg/marionette.git
cd marionette
pip install -r requirements.txt
pip install -e .
```

### Verify Installation

```bash
python -m pytest marionette/ -v
```

## Quick Start

Start the backend SOCKS server, marionette server, and marionette client:

```bash
./examples/socksserver --local_port 8081 &
./bin/marionette_server --server_ip 127.0.0.1 --proxy_ip 127.0.0.1 --proxy_port 8081 --format dummy &
./bin/marionette_client --server_ip 127.0.0.1 --client_ip 127.0.0.1 --client_port 8079 --format dummy &
```

Test the connection:

```bash
curl --socks4a 127.0.0.1:8079 example.com
```

Use `--help` for a complete list of options.

## Configuration

The `marionette.conf` file supports the following options:

| Option | Type | Description |
|--------|------|-------------|
| `general.debug` | boolean | Print debug information to the console |
| `general.autoupdate` | boolean | Enable automatic checks for new marionette formats |
| `general.update_server` | string | Remote address of the update server |
| `client.client_ip` | string | Interface to listen on (client) |
| `client.client_port` | int | Port to listen on (client) |
| `server.server_ip` | string | Interface to listen on (server) |
| `server.proxy_ip` | string | Interface to forward connections to |
| `server.proxy_port` | int | Port to forward connections to |

## Marionette DSL

Marionette uses a domain-specific language to define traffic patterns:

```
connection([connection_type], [port]):
  start [dst] [block_name] [prob | error]
  [src] [dst] [block_name] [prob | error]
  ...
  [src] end [block_name] [prob | error]

action [block_name]:
  [client | server] [module].[func](arg1, arg2, ...)
  [client | server] [module].[func](arg1, arg2, ...) [if regex_match_incoming(regex)]
```

- **connection_type**: Currently only `tcp` is supported
- **port**: The port the server listens on and client connects to
- **block_name**: Named action executed when transitioning from src to dst
- **error**: Special transition executed when all other transitions fail

## Plugins

| Plugin | Description |
|--------|-------------|
| `fte.send(regex, msg_len)` | Send FTE-encrypted string matching `regex` |
| `fte.send_async(regex, msg_len)` | Non-blocking FTE send |
| `tg.send(grammar_name)` | Send using template grammar |
| `io.puts(str)` | Send raw string on the channel |
| `model.sleep(n)` | Sleep for `n` seconds |
| `model.spawn(format_name, n)` | Spawn `n` instances of format, blocks until completion |

> **Note:** Specifying a send or puts implicitly invokes a recv or gets on the receiver side.

## Example Formats

### Simple HTTP

A basic HTTP format with one request-response cycle:

```
connection(tcp, 80):
  start  client NULL     1.0
  client server http_get 1.0
  server end    http_ok  1.0

action http_get:
  client fte.send("^GET\ \/([a-zA-Z0-9\.\/]*) HTTP/1\.1\r\n\r\n$", 128)

action http_ok:
  server fte.send("^HTTP/1\.1\ 200 OK\r\nContent-Type:\ ([a-zA-Z0-9]+)\r\n\r\n\C*$", 128)
```

### HTTP with Error Handling

Using error transitions and conditionals to handle non-marionette connections:

```
connection(tcp, 8080):
  start          upstream       NULL        1.0
  upstream       downstream     http_get    1.0
  upstream       downstream_err NULL        error
  downstream_err end            http_ok_err 1.0
  downstream     end            http_ok     1.0

action http_get:
  client fte.send("^GET\ \/([a-zA-Z0-9\.\/]*) HTTP/1\.1\r\n\r\n$", 128)

action http_ok:
  server fte.send("^HTTP/1\.1\ 200 OK\r\nContent-Type:\ ([a-zA-Z0-9]+)\r\n\r\n\C*$", 128)

action http_ok_err:
  server io.puts("HTTP/1.1 200 OK\r\n\r\nHello, World!") if regex_match_incoming("^GET /(index\.html)? HTTP/1\.(0|1).*")
  server io.puts("HTTP/1.1 404 File Not Found\r\n\r\nFile not found!") if regex_match_incoming("^GET /.* HTTP/1\.(0|1).*")
  server io.puts("HTTP/1.1 400 Bad Request\r\n\r\nBad request!") if regex_match_incoming("^.+")
```

## License

MIT License - see [LICENSE](LICENSE) for details.
