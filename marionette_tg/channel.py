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

class Channel(object):

    def __init__(self, protocol, port):
        self.port_ = port
        self.protocol_ = protocol
        self.closed_ = False
        self.is_alive_ = True
        self.channel_id_ = os.urandom(4)
        self.buffer_lock_ = threading.RLock()
        self.buffer_ = ''
        self.last_buffer_ = ''
        self.model_ = None

    def appendToBuffer(self, chunk):
        with self.buffer_lock_:
            self.buffer_ += chunk

    def recv(self):
        with self.buffer_lock_:
            retval = self.buffer_
            self.last_buffer_ = self.buffer_
            self.buffer_ = ''
        return retval

    def peek(self):
        with self.buffer_lock_:
            return self.buffer_

    def send(self, data):
        self.protocol_.transport.write(data)
        return len(data)

    def sendall(self, data):
        return self.send(data)

    def rollback(self, n=0):
        with self.buffer_lock_:
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


### Client async. classes

class MyClient(protocol.Protocol):
    def connectionMade(self):
        log.msg("channel.Client.connectionMade")

    def dataReceived(self, chunk):
        log.msg("channel.Client: %d bytes received" % len(chunk))
        self.channel.appendToBuffer(chunk)


class MyClientFactory(protocol.ClientFactory):

    def __init__(self, callback):
        self.callback_ = callback

    def buildProtocol(self, address):
        proto = protocol.ClientFactory.buildProtocol(self, address)
        channel = Channel(proto, None)
        proto.channel = channel
        self.callback_(channel)
        return proto


def open_new_channel(port, callback):
    reactor.callFromThread(start_connection, port, callback)

    return True

def start_connection(port, callback):
    factory = MyClientFactory(callback)
    factory.protocol = MyClient
    reactor.connectTCP(marionette_tg.conf.get("server.server_ip"),
        int(port), factory)

    return True


#### Server async. classes

incoming = {}
incoming_lock = threading.RLock()
listening_sockets_ = {}

class MyServer(protocol.Protocol):
    def connectionMade(self):
        log.msg("channel.Server.connectionMade")
        port = int(self.transport.getHost().port)
        with incoming_lock:
            if not incoming.get(port):
                incoming[port] = []
            incoming[port].append(self)
        self.channel = Channel(self, self.transport.getHost().port)

    def dataReceived(self, chunk):
        self.channel.appendToBuffer(chunk)

        log.msg("channel.Server[%s]: %d bytes received" % (self.channel, len(chunk)))

def bind(port=0):
    with incoming_lock:
        retval = start_listener(port)

    return retval

def accept_new_channel(port):
    channel = None
    with incoming_lock:
        start_listener(port)
        if incoming.get(port) and len(incoming.get(port))>0:
            myprotocol = incoming[port].pop(0)
            channel = myprotocol.channel

    return channel

def start_listener(port):
    retval = port

    if not port or not listening_sockets_.get(port):
        try:
            factory = protocol.Factory()
            factory.protocol = MyServer
            connector = reactor.listenTCP(int(port), factory,
                interface=marionette_tg.conf.get("server.server_ip"))
            port = connector.getHost().port
            listening_sockets_[port] = connector
            retval = port
        except twisted.internet.error.CannotListenError as e:
            retval = False

    return retval


def stop_accepting_new_channels(port):
    with incoming_lock:
        if listening_sockets_.get(port):
            listening_sockets_[port].stopListening()
            del listening_sockets_[port]
        if incoming.get(port):
            for channel in incoming[port]:
                channel.close()
            del incoming[port]
