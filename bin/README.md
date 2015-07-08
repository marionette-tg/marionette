Marionette Command-line Tools
-----------------------------

### marionette_server

Spins up a marionette server with ```marionette_format``` and forward all requests to ```listen_iface:port```.
If multiple versions of the same format exist, then the server will listen with all of them simultaneously.

```
./bin/marionette_server [listen_iface] [port] [marionette_format]
```

### marionette_client

Spins up a marionette client with ```marionette_format``` and accepts incoming requests on ```listen_iface:port```.
The version of the format can be specified with the version parameter.

```
./bin/marionette_server [listen_iface] [port] [[marionette_format]:version]
```

### benchmark

Spawns ```marionette_server``` and ```marionette_client``` using ```marionette_format```, and also starts up ```httpserver```.
It then performs a GET request to the httpserver via marionette and reports statistics on the throughput.

```
./bin/benchmark [marionette_format]
```

### socksproxy

Creates a SOCKS4 proxy that listens on ```port```.

```
./bin/socksproxy [port]
```

### httpserver

Creates an HTTP server that listens on ```port```. By default returns 2^{18} Xs on any GET request. This can be modified by changing the implementation of ```GetResource.render_GET```. The ```benchmark``` script assume that it's connecting to this httpserver for its performance tests.

```
./bin/httpserver [port]
```
