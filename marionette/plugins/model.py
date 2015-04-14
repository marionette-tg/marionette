import marionette.driver


def spawn(channel, global_args, local_args, input_args, blocking=True):
    format_name_ = input_args[0]
    num_models = int(input_args[1])

    driver = marionette.driver.Driver(local_args["party"])
    driver.set_multiplexer_incoming(global_args["multiplexer_incoming"])
    driver.set_multiplexer_outgoing(global_args["multiplexer_outgoing"])
    driver.setFormat(format_name_)

    driver.one_execution_cycle(num_models)
    driver.stop()

    return True
