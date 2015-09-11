marionette modules
------------------

### marionette.executable

The ```marionette.executable``` class is a meta-class that creates one or more instances of ```marionette.executables.pioa```. In inital tests we use this to instantiate multiple versions of the same format. (e.g., small changes to it's structure or regexes used)

The ```marionette.executable``` runs multiple ```marionette.executables.pioa``` classes in parallel on the same channel. It's the responsiblility of each ```marionette.executables.pioa``` to act on a channel iff it's supposed to, as determined by the ```model_uuid``` field in the first incoming ```Cell```.

If no PIOA is able to act on a channel, then it should be the most recent version is executed with any potential error transtions.

### marionette.updater

The ```marionette.updater``` is responsible for checking a remote server for new marionette format updates. It makes the following assumptions:

* Expects a ```manifest.txt``` in the root of the remote server. The manifest file must have one entry per line and each entry must be a name of a tar file that contains marionette mar files.
* The marionette client or server will check if doesn't have any of the listed packages, if it doesn't it will attempt to download each of them.
* For each format_version it doesn't have it will attempt to download ```update_server/format_name.tar.gz``` and will extract the file into it's local directory.

*note*: The iniital implementation does not use TLS.

### miscellaneous notes

* ```marionette_tg``` holds the ```Server``` and ```Client``` classes, which are the main entry points into marionette.
* ```marionette_tg.action``` contains the ```MarionetteAction``` class, which describes marionette actions that occur in state transitions.
* ```marionette_tg.channel``` is responsible for creating/destroying and managing the state of TCP/UDP/etc. connections.
* ```marionette_tg.conf``` enables read-only access to marionette.conf.
* ```marionette_tg.driver``` is the core of marionette and is responsible to creating/destroying/running models.
* ```marionette_tg.dsl``` is our parser for our DSL and converts input formats into ```marionette_tg.executables.pioa```.
* ```marionette_tg.executable``` is a meta-class that enables us to have multiple, simultaneous instances of ```marionette_tg.executables.pioa``` and use non-determinism to run them in parallel on a single ```marionette_tg.channel```.
* ```marionette_tg.multiplexer``` converts arbitrary datastreams in ```marionette_tg.record_layer.Cell```, and also performs the reverse functionality.
* ```marionette_tg.record_layer``` contains the ```Cell``` class, which is the core of data transport in marionette.
* ```marionette_tg.updater``` is responsible for finding and unpacking marionette format packages.
