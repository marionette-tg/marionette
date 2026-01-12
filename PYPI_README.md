# marionette

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/marionette-tg/marionette/actions/workflows/ci.yml/badge.svg)](https://github.com/marionette-tg/marionette/actions/workflows/ci.yml)

**Marionette** is a programmable client-server proxy that enables the user to control network traffic features with a lightweight domain-specific language.

> ⚠️ **Pre-alpha software** - Not suitable for real-world deployment.

## Installation

```bash
pip install marionette-tg
```

## Quick Start

```bash
# Start the SOCKS backend
./examples/socksserver --local_port 8081 &

# Start the marionette server
./bin/marionette_server --server_ip 127.0.0.1 --proxy_ip 127.0.0.1 --proxy_port 8081 --format dummy &

# Start the marionette client
./bin/marionette_client --server_ip 127.0.0.1 --client_ip 127.0.0.1 --client_port 8079 --format dummy &

# Test the connection
curl --socks4a 127.0.0.1:8079 example.com
```

## Features

- **Programmable traffic shaping** using a domain-specific language
- **Format-Transforming Encryption (FTE)** for protocol obfuscation
- **Template grammars** for generating realistic traffic patterns
- **Pluggable architecture** for custom protocol handlers

## Documentation

Full documentation, DSL reference, and example formats are available on [GitHub](https://github.com/marionette-tg/marionette).

## References

1. [Protocol Misidentification Made Easy with Format-Transforming Encryption](https://kpdyer.com/publications/ccs2013-fte.pdf) (CCS 2013)
2. [Marionette: A Programmable Network Traffic Obfuscation System](https://kpdyer.com/publications/usenix2015-marionette.pdf) (USENIX Security 2015)

## License

MIT License - see [LICENSE](https://github.com/marionette-tg/marionette/blob/master/LICENSE) for details.
