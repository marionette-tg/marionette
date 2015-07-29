import sys
import time
import threading

from twisted.internet import reactor

sys.path.append('.')

import marionette_tg.channel as channel


class ServerThread(threading.Thread):
    def run(self):
        print 'Starting server...'
        self.channel_ = None
        while True:
            time.sleep(0.1)
            ch = channel.accept_new_channel(
                'udp', 8080)
            if ch:
                self.channel_ = ch
                break

    def recv(self):
        return self.channel_.recv()


class ClientThread(threading.Thread):
    channel_ = None

    def run(self):
        time.sleep(1)
        print 'Starting client...'
        self.channel_ = None
        channel.open_new_channel(
            'udp', 8080, self.set_channel)

    def send(self, data):
        return self.channel_.send(data)

    def set_channel(self, ch):
        self.channel_ = ch

finished = False
already_sent = False
def test_udp_send(msg_len):
    global already_sent

    expected_msg = 'X'*msg_len

    if client.channel_ and server.channel_:
        if not already_sent:
            try:
                print "Test: sending message %d bytes" % msg_len
                client.send(expected_msg)
                already_sent = True
            except:
                print "FAILURE: Error sending message"
                reactor.stop()
                return

        recvd = server.recv()
        if len(recvd) != 0:
            assert len(recvd) == len(expected_msg)
            print 'SUCCESS'
            reactor.stop()
            return
        else:
            reactor.callFromThread(test_udp_send, msg_len)
    else:
        reactor.callFromThread(test_udp_send, msg_len)

if __name__ == '__main__':
    server = ServerThread()
    client = ClientThread()
    reactor.callFromThread(server.start)
    reactor.callFromThread(client.start)
    reactor.callFromThread(test_udp_send, 65507)
    reactor.run()
