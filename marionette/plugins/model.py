import time
import random

import marionette.driver

def sleep(channel, global_args, local_args, input_args, blocking=True):
    sleep_dist = input_args[0]
    sleep_dist = sleep_dist[1:-1]
    sleep_dist = sleep_dist.split(',')

    dist = {}
    for item in sleep_dist:
        val = float(item.split(':')[0][1:-1])
        prob = float(item.split(':')[1])
        if val>0:
            dist[val] = prob

    coin = random.random()
    total_sum = 0
    for to_sleep in dist.keys():
        total_sum += dist[to_sleep]
        if total_sum >= coin:
            break

    time.sleep(to_sleep)

    return True

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
