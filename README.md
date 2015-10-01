# marionette

[![Build Status](https://travis-ci.org/kpdyer/marionette.svg?branch=master)](https://travis-ci.org/kpdyer/marionette)

**This code is still pre-alpha and is NOT suitable for any real-world deployment.**

Overview
--------

Marionette is a programmable client-server proxy that enables the user to control network traffic features with a lightweight domain-specific language. The marionette system is described in [2] and builds on ideas from other papers, such as Format-Transforming Encryption [1].

1. Protocol Misidentification Made Easy with Format-Transforming Encryption
   url: https://kpdyer.com/publications/ccs2013-fte.pdf
2. Marionette: A Programmable Network Traffic Obfuscation System
   url: https://kpdyer.com/publications/usenix2015-marionette.pdf

Installation
------------

### Ubuntu

```console
$ sudo apt-get update && sudo apt-get upgrade
$ sudo apt-get install git libgmp-dev python-pip python-dev curl
$ git clone https://github.com/kpdyer/marionette.git
$ cd marionette
$ sudo pip install -r requirements.txt
$ python setup.py build
$ sudo python setup.py install
```

### RedHat/Fedora/CentOS

```console
$ sudo yum update
$ yum install epel-release  # EPEL may be required for some distros
$ sudo yum groupinstall "Development Tools"
$ sudo yum install git gmp-devel python-pip python-devel curl
$ git clone https://github.com/kpdyer/marionette.git
$ cd marionette
$ sudo pip install -r requirements.txt
$ python setup.py build
$ sudo python setup.py install
```


###  OSX

Requires homebrew.

```console
$ brew install python gmp curl
$ git clone https://github.com/kpdyer/marionette.git
$ cd marionette
$ python setup.py install
```

### Sanity check

```console
$ python setup.py test
...
----------------------------------------------------------------------
Ran 13 tests in Xs

OK
```

### Running

And then testing with the servers...

```console
$ ./bin/socksserver --local_port 8081 &
$ ./bin/marionette_server --server_ip 127.0.0.1 --proxy_ip 127.0.0.1 --proxy_port 8081 --format dummy&
$ ./bin/marionette_client --server_ip 127.0.0.1 --client_ip 127.0.0.1 --client_port 8079 --format dummy&
$ curl --socks4a 127.0.0.1:8079 example.com
```

A complete list of options is available with the `--help` parameter.


marionette.conf
---------------

* ```general.debug``` - [boolean] print useful debug information to the console
* ```general.autoupdate``` - [boolean] enable automatic checks for new marionette formats
* ```general.update_server``` - [string] the remote address of the server we should use for marionette updates
* ```client.client_ip``` - [string] the iface we should listen on if it isn't
specified on the CLI
* ```client.client_port``` - [int] the port we should listen on if it isn't
specified on the CLI
* ```server.server_ip``` - [string] the iface we should listen on if it isn't
specified on the CLI
* ```server.proxy_ip``` - [string] the iface we should forward connects to if it
isn't specified on the CLI
* ```server.proxy_port``` - [int] the port we should forward connects to if it isn't specified on the CLI


Marionette DSL
--------------

Marionette's DSL is

```
connection([connection_type], [port]):
  start [dst] [block_name] [prob | error]
  [src] [dst] [block_name] [prob | error]
  ...
  [src] end [block_name] [prob | error]

action [block_name]:
  [client | server] [module].[func](arg1, arg2, ...)
  [client | server] [module].[func](arg1, arg2, ...) [if regex_match_incoming(regex)]
...
```

The only ```connection_type``` currently supported is tcp. The port specifies the port that the server listens on and client connects to. The ```block_name``` specifies the named action that should be exected when transitioning from src to dst. A single error transition can be specified for each src and will be executed if all other potential transitions from src are impossible.

Action blocks specify actions by either a client or server. For brevity we allow specification of an action, such as ```fte.send```

Marionette Plugins
------------------

* ```fte.send(regex, msg_len)``` - sends a string on the channel that's encrypted with fte under ```regex```.
* ```fte.send_async(regex, msg_len)``` - sends a string on the channel that's encrypted with fte under ```regex```, does not block receiver-side when waiting for the incoming message.
* ```tg.send(grammar_name)``` - send a message using template grammar ```grammar_name```
* ```io.puts(str)``` - send string ```str``` on the channel.
* ```model.sleep(n)``` - sleep for ```n``` seconds.
* ```model.spawn(format_name, n)``` - spawn ```n``` instances of model ```format_name```, blocks until completion.

*note*: by specifying a send or a puts, that implicitly invokes a recv or a gets on the receiver side.

Example Formats
---------------

### Simple HTTP

The following format generates a TCP connection sends one upstream GET and is followed by a downstream OK.

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

### HTTP with error transitions and conditionals

We use error transitions in the following format to deal with incoming connections that aren't from a marionette client. The conditionals are used to match a regex aginst the incoming request.

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
