import sys
import time
import threading

from twisted.internet import reactor

sys.path.append('.')

import marionette_tg.channel as channel


class ServerThread(threading.Thread):
    def run(self):
        print 'server started'
        self.channel = None
        while True:
            time.sleep(0.1)
            ch = channel.accept_new_channel(
                'tcp', 8080)
            if ch:
                self.channel = ch
                break
        print 'server done'

    def recv(self):
        return self.channel.recv()


class ClientThread(threading.Thread):
    def run(self):
        self.channel = None
        time.sleep(1)
        print 'client started'
        self.channel = None
        channel.open_new_channel(
            'tcp', 8080, self.set_channel)
        print 'client done'

    def send(self, data):
        return self.channel.send(data)

    def set_channel(self, ch):
        self.channel = ch


already_sent = False
def test_tcp_send():
    global already_sent

    expected_msg = 'X'*100

    if client.channel and server.channel:
        if not already_sent:
            client.send(expected_msg)
            already_sent = True

        recvd = server.recv()
        if recvd  == expected_msg:
            print 'success'
            reactor.stop()
        else:
            reactor.callFromThread(test_tcp_send)
    else:
        reactor.callFromThread(test_tcp_send)


if __name__ == '__main__':
    server = ServerThread()
    client = ClientThread()
    reactor.callFromThread(server.start)
    reactor.callFromThread(client.start)
    reactor.callFromThread(test_tcp_send)
    reactor.run()
