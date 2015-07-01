import sys
import time
import threading

from twisted.internet import reactor

sys.path.append('.')

import marionette_tg.channel as channel


class ServerThread(threading.Thread):
    def run(self):
        print 'server started'
        self.channel_ = None
        while True:
            time.sleep(0.1)
            ch = channel.accept_new_channel(
                'udp', 8080)
            if ch:
                self.channel_ = ch
                break
        print 'server done'

    def recv(self):
        return self.channel_.recv()


class ClientThread(threading.Thread):
    channel_ = None

    def run(self):
        time.sleep(1)
        print 'client started'
        self.channel_ = None
        channel.open_new_channel(
            'udp', 8080, self.set_channel)
        print 'client done'

    def send(self, data):
        return self.channel_.send(data)

    def set_channel(self, ch):
        self.channel_ = ch


already_sent = False
def test_udp_send():
    global already_sent

    expected_msg = 'X'*100

    if client.channel_ and server.channel_:
        if not already_sent:
            client.send(expected_msg)
            already_sent = True

        recvd = server.recv()
        if recvd  == expected_msg:
            print 'success'
            reactor.stop()
        else:
            reactor.callFromThread(test_udp_send)
    else:
        reactor.callFromThread(test_udp_send)


if __name__ == '__main__':
    server = ServerThread()
    client = ClientThread()
    reactor.callFromThread(server.start)
    reactor.callFromThread(client.start)
    reactor.callFromThread(test_udp_send)
    reactor.run()
