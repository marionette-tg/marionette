marionette
----------

[![Build Status](https://travis-ci.org/kpdyer/marionette.svg?branch=master)](https://travis-ci.org/kpdyer/marionette)


### Ubuntu Quickstart

```console
$ sudo apt-get update && sudo apt-get upgrade
$ sudo apt-get install git libgmp-dev python-pip python-dev
$ git clone https://github.com/kpdyer/marionette.git
$ cd marionette
$ pip install -r requirements.txt
$ python setup.py test
...
----------------------------------------------------------------------
Ran 13 tests in Xs

OK
```

And then testing with the servers...

```console
$ ./bin/socksserver 8081 &
$ ./bin/marionette_server 8080 127.0.0.1 8081 &
$ ./bin/marionette_client 8079 127.0.0.1 8080 &
$ curl --socks4a 127.0.0.1:8079 example.com
```
