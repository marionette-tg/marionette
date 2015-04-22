#!/usr/bin/env python
# coding: utf-8

import os
import select
import socket


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


def new(connection):
    return Channel(connection)
