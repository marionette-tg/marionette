import marionette

# channel.bind("my_var") sets local variable my_var to a port number
#   it bound to
def bind(channel, marionette_state, input_args):
    local_var = input_args[0]

    if marionette_state.get_local(local_var):
        port = marionette_state.get_local(local_var)
    else:
        port = marionette.channel.bind()
        if port:
            marionette_state.set_local(local_var, port)

    success = (port > 0)

    return success