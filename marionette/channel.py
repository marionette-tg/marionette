#!/usr/bin/env python
# coding: utf-8

import os
import sys
import struct
import time
import select
import socket

sys.path.append('.')

import marionette.conf

SERVER_IFACE = marionette.conf.get("server.listen_iface")
SERVER_TIMEOUT = 0.001


class Channel(object):
    def __init__(self, conn):
        self.conn_ = conn
        self.closed_ = False
        self.is_alive_ = True
        self.channel_id_ = os.urandom(4)
        self.buffer_ = ''
        self.last_buffer_ = ''
        self.model_ = None

    def __del__(self):
        self.close()

    def recv(self):
        self.buffer_ += self.do_recv()

        retval = self.buffer_
        self.last_buffer_ = self.buffer_
        self.buffer_ = ''
        return retval

    def do_recv(self, bufsize=2 ** 16, select_timeout=0.001):
        retval = ''

        try:
            ready = select.select([self.conn_], [], [self.conn_],
                                  select_timeout)
            if ready[0]:
                _data = self.conn_.recv(bufsize)
                if _data:
                    retval += _data
                    self.is_alive_ = True
                else:
                    self.is_alive_ = False
            else:
                self.is_alive_ = True
        except socket.timeout as e:
            self.is_alive_ = True
        except socket.error as e:
            self.is_alive_ = (len(retval) > 0)
        except select.error as e:
            self.is_alive_ = (len(retval) > 0)
        finally:
            if retval:
                self.is_alive_ = True

        return retval

    def send(self, data):
        retval = self.conn_.send(data)

        return retval

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
        return self.conn_.close()

def open_new_channel(port):
    for i in range(10):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((SERVER_IFACE, int(port)))
            channel = marionette.channel.new(s)
        except Exception as e:
            channel = None
        finally:
            if channel: break
            else: time.sleep(i*0.1)

    return channel

def accept_new_channel(listening_sockets, port):
    if not listening_sockets.get(port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER,
                     struct.pack('ii', 0, 0))
        s.bind((SERVER_IFACE, int(port)))
        s.listen(10)
        s.settimeout(SERVER_TIMEOUT)
        listening_sockets[port] = s

    try:
        conn, addr = listening_sockets[port].accept()
        channel = marionette.channel.new(conn)
    except socket.timeout:
        channel = None

    return channel


def new(connection):
    return Channel(connection)
