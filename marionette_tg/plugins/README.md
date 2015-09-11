marionette plugins
------------------

If you wish to create a new marionette plugin called ```my_plugin.my_func``` you must do the following:
Create the following file:

```
marionette_tg/plugins/_my_plugin.py
```

with a function that implementats the following interface

```python
def my_func(channel, marionette_state, input_args, blocking):
    # channel is where we do our send/recv
    # marionette_state is an instance of MarionetteSystemState, with our global/local variables
    # input_args is a list of the inputs to our plugin
    # if blocking is True the plugin can block as long as it wants, if blocking is False it must return in a timely manner
```

The plugin, ```my_func``` must abide by the following rules:

* If the plugin does not complete successfully, but could be successful in future, it must return ```False```.
* If the plugin does not complete successfully, and can determine that it will never succeed. (e.g., MAC failure) it must throw an exception.

What's more, plugins cannot assume that they have been given the "right" channel and must verify that the incoming data is actually destined for the model that invoked the plugin.
