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

import marionette.conf



class Channel(object):

    def __init__(self, protocol, transport_protocol):
        self.transport_protocol_ = transport_protocol
        self.protocol_ = protocol
        self.closed_ = False
        self.is_alive_ = True
        self.channel_id_ = os.urandom(4)
        self.buffer_lock_ = threading.RLock()
        self.buffer_ = ''
        self.last_buffer_ = ''
        self.model_ = None
        self.remote_host = None
        self.remote_port = None
        self.party = None #client/server

    def appendToBuffer(self, chunk):
        with self.buffer_lock_:
            # Convert bytes to string using latin-1 encoding (preserves byte values 0-255)
            if isinstance(chunk, bytes):
                chunk = chunk.decode('latin-1')
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
        # Convert string to bytes using latin-1 encoding (preserves byte values 0-255)
        if isinstance(data, str):
            data = data.encode('latin-1')
        if self.transport_protocol_ == 'tcp':
            self.protocol_.transport.write(data)
        else: #udp
            self.protocol_.transport.write(data, (self.remote_host, self.remote_port))
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
        if self.is_closed():
            return
        self.closed_ = True
        self.is_alive_ = False
        if not (self.transport_protocol_ == 'udp' and self.party == 'server'):
            self.protocol_.transport.loseConnection()


### Client async. classes
class MyClient(protocol.Protocol):
    def __init__(self, callback=None, transport_protocol='tcp', host=None, port=None):
        self.transport_protocol = transport_protocol
        if self.transport_protocol == 'udp':
            self.host = host
            self.port = port
            self.callback_ = callback
            self.startProtocol()

    def startProtocol(self):
        if self.transport_protocol == 'udp':
            self.channel = Channel(self, "udp")
            self.channel.remote_host = self.host
            self.channel.remote_port = self.port
            self.channel.party = 'client'
            self.callback_(self.channel)
            log.msg("channel.Client: UDP Connection established %s:%d" 
                % (self.host, self.port))

    def datagramReceived(self, chunk, addr):
        host, port = addr
        log.msg("channel.Client: %d bytes received" % len(chunk))
        self.channel.appendToBuffer(chunk)

    def doStop(self):
        if self.transport_protocol == 'udp':
            log.msg("channel.Client.doStop: Stopping UDP connection")

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
        channel = Channel(proto, "tcp")
        channel.party = "client"
        proto.channel = channel
        self.callback_(channel)
        return proto


def open_new_channel(transport_protocol, port, callback):
    reactor.callFromThread(start_connection, transport_protocol, port, callback)

    return True

def start_connection(transport_protocol, port, callback):
    if transport_protocol == 'tcp':
        factory = MyClientFactory(callback)
        factory.protocol = MyClient
        reactor.connectTCP(marionette.conf.get("server.server_ip"),
                int(port), factory)
    else: #udp
        reactor.listenUDP(0, MyClient(callback, 'udp', marionette.conf.get("server.server_ip"),
            int(port)), maxPacketSize=65535)
        #reactor.listenUDP(0, MyUdpClient(marionette.conf.get("server.server_ip"),
        #    int(port), callback), maxPacketSize=65535)


    return True


#### Server async. classes

incoming = {}
incoming_lock = threading.RLock()
listening_sockets_ = {}

class MyServer(protocol.Protocol):

    def __init__(self, transport_protocol='tcp'):
        self.transport_protocol = transport_protocol
        log.msg("channel.Server transport_protocol: %s" % self.transport_protocol)

    def connectionMade(self):
        log.msg("channel.Server.connectionMade")
        port = int(self.transport.getHost().port)
        with incoming_lock:
            if not incoming.get(port):
                incoming[port] = []
            incoming[port].append(self)
        self.channel = Channel(self, self.transport_protocol)
        self.channel.party = "server"

    def dataReceived(self, chunk):
        self.channel.appendToBuffer(chunk)
        log.msg("channel.Server[%s]: %d bytes received" % (self.channel, len(chunk)))

    def datagramReceived(self, chunk, addr):
        host, port = addr
        log.msg("channel.Server[%s]: %d bytes received" % (self.channel, len(chunk)))
        if self.channel.is_closed():
            self.connectionMade()
        self.channel.remote_host = host
        self.channel.remote_port = port
        self.channel.appendToBuffer(chunk)

    def doStop(self):
        log.msg("channel.Server.doStop: Stopping UDP connection")

def bind(port=0):
    with incoming_lock:
        #TODO: handle UDP
        retval = start_listener('tcp', port)

    return retval

def accept_new_channel(transport_protocol, port):
    channel = None
    with incoming_lock:
        start_listener(transport_protocol, port)
        if incoming.get(port) and len(incoming.get(port))>0:
            myprotocol = incoming[port].pop(0)
            channel = myprotocol.channel

    return channel

def start_listener(transport_protocol, port):
    retval = port

    if not port or not listening_sockets_.get(port):
        try:
            if transport_protocol == 'tcp':
                factory = protocol.Factory()
                factory.protocol = MyServer
                connector = reactor.listenTCP(int(port), factory,
                        interface=marionette.conf.get("server.server_ip"))
            else: #udp
                connector = reactor.listenUDP(int(port), MyServer('udp'),
                        interface=marionette.conf.get("server.server_ip"), maxPacketSize=65535)
            port = connector.getHost().port
            listening_sockets_[port] = connector
            retval = port
        except twisted.internet.error.CannotListenError as e:
            retval = False

    return retval


def stop_accepting_new_channels(transport_protocol, port):
    with incoming_lock:
        if listening_sockets_.get(port):
            listening_sockets_[port].stopListening()
            del listening_sockets_[port]
        if incoming.get(port):
            for channel in incoming[port]:
                channel.close()
            del incoming[port]
