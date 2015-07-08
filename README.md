# marionette

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
$ sudo apt-get install git libgmp-dev python-pip python-dev
$ git clone https://github.com/kpdyer/marionette.git
$ cd marionette
$ pip install -r requirements.txt
$ python setup.py install
```

###  OSX

Requires homebrew.

```console
$ brew install python gmp
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
$ ./bin/socksserver 8081 &
$ ./bin/marionette_server 127.0.0.1 8081 &
$ ./bin/marionette_client 127.0.0.1 8079 &
$ curl --socks4a 127.0.0.1:8079 example.com
```


Marionette DSL
--------------

Marionette's DSL is 

```
connection([connection_type]):
  start [dst] [block_name] [prob | error]
  [src] [dst] [block_name] [prob | error]
  ...
  [src] end [block_name] [prob | error]

action [block_name]:
  [client | server] plugin(arg1, arg2, ...)
  [client | server] plugin(arg1, arg2, ...) [if regex_match_incoming(regex)]
...
```


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
