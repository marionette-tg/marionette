#!/usr/bin/env python
# coding: utf-8

import os
import sys
import threading

import twisted.internet.error
from twisted.internet import protocol
from twisted.internet import reactor
from twisted.python import log

sys.path.append('.')

import marionette_tg.conf

SERVER_IFACE = marionette_tg.conf.get("server.listen_iface")


class Channel(object):

    def __init__(self, protocol, port):
        self.port_ = port
        self.protocol_ = protocol
        self.closed_ = False
        self.is_alive_ = True
        self.channel_id_ = os.urandom(4)
        self.buffer_ = ''
        self.last_buffer_ = ''
        self.model_ = None

    def update_buffer(self):
        with self.protocol_.buffer_lock_:
            tmpbuf = self.protocol_.buffer_
            self.protocol_.buffer_ = ''
            self.buffer_ += tmpbuf

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
        self.protocol_.transport.getHandle().sendall(data)
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
        self.protocol_.transport.loseConnection()


###

class MyClient(protocol.Protocol):
    def connectionMade(self):
        log.msg("channel.Client.connectionMade")
        self.buffer_lock_ = threading.RLock()
        with self.buffer_lock_:
            self.buffer_ = ''
        self.transport.setTcpNoDelay(True)

    def dataReceived(self, chunk):
        log.msg("channel.Client: %d bytes received" % len(chunk))
        with self.buffer_lock_:
            self.buffer_ += chunk


class MyClientFactory(protocol.ClientFactory):

    def __init__(self, callback):
        self.callback_ = callback

    def buildProtocol(self, address):
        proto = protocol.ClientFactory.buildProtocol(self, address)
        channel = Channel(proto, address)
        self.callback_(channel)
        return proto


def open_new_channel(port, callback):
    reactor.callFromThread(start_connection, port, callback)

    return True

def start_connection(port, callback):
    factory = MyClientFactory(callback)
    factory.protocol = MyClient
    connector = reactor.connectTCP(SERVER_IFACE, int(port), factory)

    return True


####
incoming = {}

class MyServer(protocol.Protocol):
    def connectionMade(self):
        log.msg("channel.Server.connectionMade")
        port = int(self.transport.getHost().port)
        if not incoming.get(port):
            incoming[port] = []
        incoming[port].append(self)
        self.buffer_lock_ = threading.RLock()
        with self.buffer_lock_:
            self.buffer_ = ''
        self.transport.setTcpNoDelay(True)

    def dataReceived(self, chunk):
        log.msg("channel.Server: %d bytes received" % len(chunk))
        with self.buffer_lock_:
            self.buffer_ += chunk


def accept_new_channel(listening_sockets, port):
    reactor.callFromThread(start_listener, listening_sockets, port)

    channel = None
    if incoming.get(port) and len(incoming.get(port))>0:
        myprotocol = incoming[port].pop(0)
        channel = Channel(myprotocol, port)

    return channel

def start_listener(listening_sockets, port):
    retval = True

    if not listening_sockets.get(port):
        try:
            factory = protocol.Factory()
            factory.protocol = MyServer
            reactor.listenTCP(int(port), factory, interface=SERVER_IFACE)
            listening_sockets[port] = True
        except twisted.internet.error.CannotListenError as e:
            retval = False

    return retval
