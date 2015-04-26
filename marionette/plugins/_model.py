#!/usr/bin/env python
# coding: utf-8

import time
import random

from twisted.internet import reactor

import marionette
import marionette.driver


def sleep(channel, marionette_state, input_args, blocking=True):
    sleep_dist = input_args[0]
    sleep_dist = sleep_dist[1:-1]
    while ' ' in sleep_dist:
        sleep_dist = sleep_dist.replace(' ', '')
    while '\n' in sleep_dist:
        sleep_dist = sleep_dist.replace('\n', '')
    while '\t' in sleep_dist:
        sleep_dist = sleep_dist.replace('\t', '')
    while '\r' in sleep_dist:
        sleep_dist = sleep_dist.replace('\r', '')
    sleep_dist = sleep_dist.split(',')

    dist = {}
    for item in sleep_dist:
        val = float(item.split(':')[0][1:-1])
        prob = float(item.split(':')[1])
        if val > 0:
            dist[val] = prob

    coin = random.random()
    total_sum = 0
    for to_sleep in dist.keys():
        total_sum += dist[to_sleep]
        if total_sum >= coin:
            break

    time.sleep(to_sleep)

    return True


def spawn(channel, marionette_state, input_args, blocking=True):
    format_name_ = input_args[0]
    num_models = int(input_args[1])

    if marionette_state.get_local("party") == 'server':
        driver = marionette.driver.ServerDriver(
            marionette_state.get_local("party"))
    elif marionette_state.get_local("party") == 'client':
        driver = marionette.driver.ClientDriver(
            marionette_state.get_local("party"))

    driver.set_multiplexer_incoming(
        marionette_state.get_global("multiplexer_incoming"))
    driver.set_multiplexer_outgoing(
        marionette_state.get_global("multiplexer_outgoing"))
    driver.setFormat(format_name_)

    if marionette_state.get_local("party") == 'server':
        while driver.num_executables_completed_ < num_models:
            driver.execute(reactor)
    elif marionette_state.get_local("party") == 'client':
        driver.reset(num_models)
        while driver.isRunning():
            driver.execute(reactor)

    return True
