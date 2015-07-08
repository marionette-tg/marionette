marionette formats
------------------

Marionette formats are specified in ```mar``` files.
See the top-level README for examples of how to use the DSL and specify formats.
We add formats using the following convention.

```
marionette_tg/formats/[fromat_version]/[format_name].mar
```

One can specify the format name and version on the CLI.

```
./bin/marionette_server [ip] [port] [format_name]
./bin/marionette_client [ip] [port] [format_name[:format_version]]
```

If the format version is not supplied, the most recent one will be used client-side.
On the server, all versions of ```format_name``` are loaded and supported.
