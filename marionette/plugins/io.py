

import socket


def puts(channel, global_args, local_args, input_args, blocking=True):
    if (not channel):
        return False

    msg = input_args[0]
    msg_len = len(msg)

    while len(msg) > 0:
        try:
            bytes_sent = channel.send(msg)
            msg = msg[bytes_sent:]
        except socket.timeout:
            continue
    retval = (msg_len == bytes_sent)

    return retval


def gets(channel, global_args, local_args, input_args, blocking=True):
    if (not channel):
        return False

    msg = input_args[0]
    remainder = ''

    try:
        incoming = channel.recv()

        if len(incoming) > len(msg):
            remainder = incoming[len(msg):]
            incoming = incoming[:len(msg)]

        retval = (incoming == msg)
    except Exception as e:
        retval = False

    if retval:
        if remainder:
            channel.rollback(len(remainder))
    else:
        channel.rollback()

    return retval
