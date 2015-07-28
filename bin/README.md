Marionette Command-line Tools
-----------------------------

### marionette_server

Spins up a marionette server with ```marionette_format``` and forward all
requests to ```server_ip:port```.
If multiple versions of the same format exist, then the server will listen with all of them simultaneously.
The --version flag lists all available formats.

```
./bin/marionette_server [-h] [--version] [--server_ip SERVER_IP]
                         [--proxy_port PROXY_PORT] [--proxy_ip PROXY_IP]
                         --format format_name
```

### marionette_client

Spins up a marionette client with ```marionette_format``` and accepts incoming
requests on ```client_ip:port```.
The version of the format can be specified with the version parameter.
The --version flag lists all available formats.

```
./bin/marionette_client [-h] [--version] [--client_ip CLIENT_IP]
                         [--client_port CLIENT_PORT] [--server_ip SERVER_IP]
                         --format format_name[:format_version]
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
