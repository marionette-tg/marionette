#!/usr/bin/env python
# coding: utf-8

import os
import sys
import time
import threading

from twisted.internet import protocol
from twisted.internet import reactor
from twisted.python import log
from twisted.internet.defer import Deferred

sys.path.append('.')

import marionette_tg.conf

SERVER_IFACE = marionette_tg.conf.get("server.listen_iface")


class Channel(object):

    def __init__(self, protocol):
        self.protocol_ = protocol
        self.closed_ = False
        self.is_alive_ = True
        self.channel_id_ = os.urandom(4)
        self.buffer_ = ''
        self.last_buffer_ = ''
        self.model_ = None

    def update_buffer(self):
        incoming = self.protocol_.buffer_
        self.protocol_.buffer_ = ''
        self.buffer_ += incoming

    def recv(self):
        self.update_buffer()

        retval = self.buffer_
        self.last_buffer_ = self.buffer_
        self.buffer_ = ''

        return retval

    def peek(self):
        self.update_buffer()

        return self.buffer_

    def send(self, data):
        self.protocol_.transport.write(data)
        self.protocol_.transport.doWrite()
        return len(data)

    def rollback(self, n=0):
        if n > 0:
            self.buffer_ = self.last_buffer_[-n:] + self.buffer_
        else:
            self.buffer_ = self.last_buffer_ + self.buffer_

    def is_alive(self):
        return self.is_alive_

    def is_closed(self):
        return self.closed_

    def get_channel_id(self):
        return self.channel_id_

    def close(self):
        self.closed_ = True
        self.is_alive_ = False
        self.protocol_.transport.disconnect()


###

class MyClient(protocol.Protocol):
    def connectionMade(self):
        log.msg("channel.Client.connectionMade")
        self.buffer_ = ''

    def dataReceived(self, chunk):
        log.msg("channel.Client: %d bytes received" % len(chunk))
        self.buffer_ += chunk


class MyClientFactory(protocol.ClientFactory):

    def __init__(self, callback):
        self.callback_ = callback
        self.done = Deferred()

    def buildProtocol(self, address):
        proto = protocol.ClientFactory.buildProtocol(self, address)
        self.connectedProtocol = proto
        channel = Channel(self.connectedProtocol)
        self.callback_(channel)
        return proto

    def clientConnectionFailed(self, connector, reason):
        log.msg('channel.ClientFactory: connection failed:', reason.getErrorMessage())
        self.done.errback(reason)

    def clientConnectionLost(self, connector, reason):
        log.msg('channel.ClientFactory: connection lost:', reason.getErrorMessage())
        self.done.callback(None)


def open_new_channel(port, callback):
    reactor.callFromThread(start_connection, port, callback)

    return True

def start_connection(port, callback):
    factory = MyClientFactory(callback)
    factory.protocol = MyClient
    reactor.connectTCP(SERVER_IFACE, int(port), factory)

    return True


####
incoming = []

class MyServer(protocol.Protocol):
    def connectionMade(self):
        log.msg("channel.Server.connectionMade")
        incoming.append(self)
        self.buffer_ = ''

    def dataReceived(self, chunk):
        log.msg("channel.Server: %d bytes received" % len(chunk))
        self.buffer_ += chunk


def accept_new_channel(listening_sockets, port):
    reactor.callFromThread(start_listener, listening_sockets, port)

    # have data store with incoming connections? peel one off?
    channel = None
    if len(incoming)>0:
        myprotocol = incoming.pop(0)
        channel = Channel(myprotocol)

    return channel

def start_listener(listening_sockets, port):
    if not listening_sockets.get(port):
        factory = protocol.Factory()
        factory.protocol = MyServer
        reactor.listenTCP(int(port), factory, interface=SERVER_IFACE)
        listening_sockets[port] = True

    return True
