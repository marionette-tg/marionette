# marionette

[![Build Status](https://travis-ci.org/kpdyer/marionette.svg?branch=master)](https://travis-ci.org/kpdyer/marionette)

Marionette is a programmable client-server proxy that enables the user to control network traffic features with a lightweight programming language.

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

### Testing

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
$ ./bin/socksserver 18081 &
$ ./bin/marionette_server 127.0.0.1 18081 &
$ ./bin/marionette_client 127.0.0.1 18079 &
$ curl --socks4a 127.0.0.1:18079 example.com
```

Example Formats
---------------

### Synchronous HTTP

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

### Asynchronous HTTP

```
connection(tcp, 80):
  start      handshake  NULL              1.0
  handshake  upstream   http_get_blocking 1.0
  upstream   downstream http_get          1.0
  downstream upstream   http_ok           1.0

action http_get_blocking:
  client fte.send("^GET\ \/([a-zA-Z0-9\.\/]*) HTTP/1\.1\r\n\r\n$", 128)

action http_get:
  client fte.send_async("^GET\ \/([a-zA-Z0-9\.\/]*) HTTP/1\.1\r\n\r\n$", 128)

action http_ok:
  server fte.send_async("^HTTP/1\.1\ 200 OK\r\nContent-Type:\ ([a-zA-Z0-9]+)\r\n\r\n\C*$", 128)
```

### Nondeterministic HTTP

```
connection(tcp, 80):
  start http_get http_get 0.5
  start http_post http_post 0.5
  http_get http10_ok http10_ok 0.5
  http_get http11_ok http11_ok 0.5
  http_post http10_ok http10_ok 0.5
  http_post http11_ok http11_ok 0.5
  http10_ok http_get NULL 0.33
  http10_ok http_post NULL 0.33
  http10_ok end NULL 0.33
  http11_ok http_get NULL 0.33
  http11_ok http_post NULL 0.33
  http11_ok end NULL 0.33

action http_get:
  client fte.send("GET\s/.*", 128)

action http10_ok:
  server fte.send("HTTP/1\.0.*", 128)

action http_post:
  client fte.send("POST\s/.*", 128)

action http11_ok:
  server fte.send("HTTP/1\.1.*", 128)
```
