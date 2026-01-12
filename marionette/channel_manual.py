import sys
import time
import threading

from twisted.internet import reactor

sys.path.append('.')

import marionette.channel as channel


class ServerThread(threading.Thread):
    def run(self):
        print('Starting server...')
        self.channel_ = None
        while True:
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
        print('Starting client...')
        self.channel_ = None
        channel.open_new_channel(
            'udp', 8080, self.set_channel)

    def send(self, data):
        return self.channel_.send(data)

    def set_channel(self, ch):
        self.channel_ = ch


finished = False
already_sent = False
def test_udp_send(msg_lens):
    global already_sent

    expected_msg = 'X'*(msg_lens[0]-28) # Subtract 28 for IP (20) and UDP (8) headers

    if client.channel_ and server.channel_:
        if not already_sent:
            try:
                print("Test: sending message %d bytes" % msg_lens[0])
                client.send(expected_msg)
                already_sent = True
            except:
                print("FAILURE: Error sending message")
                reactor.stop()
                return

        recvd = server.recv()
        if len(recvd) != 0:
            assert len(recvd) == len(expected_msg)
            print('SUCCESS')
            already_sent = False
            if len(msg_lens) > 1:
                reactor.callFromThread(test_udp_send, msg_lens[1:])
            else:
                reactor.stop()
            return
        else:
            reactor.callFromThread(test_udp_send, msg_lens)
    else:
        reactor.callFromThread(test_udp_send, msg_lens)

def timeout_failure():
    print("FAILURE: time out")
    reactor.stop()

if __name__ == '__main__':
    server = ServerThread()
    client = ClientThread()
    reactor.callFromThread(server.start)
    reactor.callFromThread(client.start)
    msg_lens = [512, 1024, 2048, 4096, 8192, 16384, 32768, 65535]
    reactor.callInThread(test_udp_send, msg_lens)
    
    reactor.callLater(30, timeout_failure)
    reactor.run()
