marionette modules
------------------

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
