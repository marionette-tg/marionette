

import math
import socket
import random

import regex2dfa
import fte.encoder
import fte.bit_ops

import marionette.record_layer


def send(channel, global_args, local_args, input_args):
    grammar = input_args[0]

    ctxt = generate_template(grammar)

    for handler_key in conf[grammar]["handler_order"]:
        ctxt = execute_handler_sender(global_args, local_args, grammar,
                                      handler_key, ctxt,
                                      global_args["multiplexer_outgoing"])

    ctxt_len = len(ctxt)
    while len(ctxt) > 0:
        try:
            bytes_sent = channel.send(ctxt)
            ctxt = ctxt[bytes_sent:]
        except socket.timeout:
            continue
    retval = (ctxt_len == bytes_sent)

    return retval


def recv(channel, global_args, local_args, input_args):
    retval = False
    grammar = input_args[0]

    try:
        ctxt = channel.recv()

        if parser(grammar, ctxt):
            cell_str = ''
            for handler_key in conf[grammar]["handler_order"]:
                tmp_str = execute_handler_receiver(global_args, local_args,
                                                   grammar, handler_key, ctxt)
                if tmp_str:
                    cell_str += tmp_str

            ##
            cell_obj = marionette.record_layer.unserialize(cell_str)
            assert cell_obj.get_model_uuid() == local_args["model_uuid"]

            #if cell_obj.get_seq_id() == 1:
            local_args["model_instance_id"] = cell_obj.get_model_instance_id()
            ##

            if local_args.get("model_instance_id"):
                #local_args["sequence_id"] = int(cell_obj.get_seq_id()) + 1
                global_args["multiplexer_incoming"].push(cell_str)
                retval = True
    except socket.timeout as e:
        pass
    except socket.error as e:
        pass
    except marionette.record_layer.UnserializeException as e:
        pass

    if not retval:
        channel.rollback()

    return retval

######### handler + (un)embed functions


def do_embed(grammar, template, handler_key, value):
    if template.count("%%" + handler_key + "%%") == 0:
        # handler not in template, no need to execute
        pass
    elif template.count("%%" + handler_key + "%%") == 1:
        template = template.replace("%%" + handler_key + "%%", value)
    else:
        # don't know how to handle >1 handlers, yet
        assert False

    return template


def do_unembed(grammar, ctxt, handler_key):
    parse_tree = parser(grammar, ctxt)
    return parse_tree[handler_key]


def execute_handler_sender(global_args, local_args, grammar, handler_key,
                           template, multiplexer):
    to_execute = conf[grammar]["handlers"][handler_key]

    cell_len_in_bits = to_execute.capacity()
    to_embed = ''
    if cell_len_in_bits > 0:
        cell = multiplexer.pop(local_args["model_uuid"],
                               local_args["model_instance_id"],
                               cell_len_in_bits)
        to_embed = cell.to_string()
    value_to_embed = to_execute.encode(template, to_embed)
    template = do_embed(grammar, template, handler_key, value_to_embed)

    return template


def execute_handler_receiver(global_args, local_args, grammar, handler_key,
                             ctxt):
    ptxt = ''

    to_execute = conf[grammar]["handlers"][handler_key]

    handler_key_value = do_unembed(grammar, ctxt, handler_key)
    if handler_key_value:
        ptxt = to_execute.decode(handler_key_value)

    return ptxt

########### handlers

regex_cache_ = {}
fte_cache_ = {}


class RankerHandler(object):
    def __init__(self, regex, msg_len):
        self.regex_ = regex

        regex_key = regex + str(msg_len)
        if not regex_cache_.get(regex_key):
            dfa = regex2dfa.regex2dfa(regex)
            cDFA = fte.cDFA.DFA(dfa, msg_len)
            encoder = fte.dfa.DFA(cDFA, msg_len)
            regex_cache_[regex_key] = (dfa, encoder)
        (self.dfa_, self.encoder_) = regex_cache_[regex_key]

    def capacity(self):
        cell_len_in_bytes = int(math.floor(self.encoder_.getCapacity() / 8.0))
        cell_len_in_bits = cell_len_in_bytes * 8
        return cell_len_in_bits

    def encode(self, template, to_embed):
        to_embed_as_int = fte.bit_ops.bytes_to_long(to_embed)
        ctxt = self.encoder_.unrank(to_embed_as_int)
        return ctxt

    def decode(self, ctxt):
        try:
            ptxt = self.encoder_.rank(ctxt)
            ptxt = fte.bit_ops.long_to_bytes(ptxt, self.capacity() / 8)
        except Exception as e:
            pass

        return ptxt


class FteHandler(object):
    def __init__(self, regex, msg_len):
        self.regex_ = regex

        fte_key = regex + str(msg_len)
        if not fte_cache_.get(fte_key):
            dfa = regex2dfa.regex2dfa(regex)
            encrypter = fte.encoder.DfaEncoder(dfa, msg_len)
            fte_cache_[fte_key] = (dfa, encrypter)
        (self.dfa_, self.fte_encrypter_) = fte_cache_[fte_key]

    def capacity(self):
        if self.regex_.endswith(".+"):
            retval = (2 ** 16) * 8
        else:
            cell_len_in_bytes = int(math.floor(self.fte_encrypter_.getCapacity() / 8.0)) \
                                   - fte.encoder.DfaEncoderObject._COVERTEXT_HEADER_LEN_CIPHERTTEXT \
                                   - fte.encrypter.Encrypter._CTXT_EXPANSION
            cell_len_in_bits = cell_len_in_bytes * 8
            retval = cell_len_in_bits

        return retval

    def encode(self, template, to_embed):
        ctxt = self.fte_encrypter_.encode(to_embed)
        return ctxt

    def decode(self, ctxt):
        try:
            retval = self.fte_encrypter_.decode(ctxt)
            ptxt = retval[0]
        except Exception as e:
            pass

        return ptxt


class FteMsgLensHandler(FteHandler):
    def capacity(self):
        cell_len_in_bytes = int(math.floor(self.fte_encrypter_.getCapacity() / 8.0)) \
                               - fte.encoder.DfaEncoderObject._COVERTEXT_HEADER_LEN_CIPHERTTEXT \
                               - fte.encrypter.Encrypter._CTXT_EXPANSION
        cell_len_in_bits = cell_len_in_bytes * 8
        return cell_len_in_bits


class HttpContentLengthHandler(object):
    def capacity(self):
        return 0

    def encode(self, template, to_embed):
        http_body_length = str(len(template.split("\r\n\r\n")[1]))
        return http_body_length

    def decode(self, ctxt):
        return None


class Pop3ContentLengthHandler(object):
    def capacity(self):
        return 0

    def encode(self, template, to_embed):
        pop3_body_length = str(len('\n'.join(template.split("\n")[1:])))
        return pop3_body_length

    def decode(self, ctxt):
        return None


class AmazonMsgLensHandler(FteHandler):
    def capacity(self):
        amazon_msg_lens = {
            2049: 1,
            2052: 2,
            2054: 2,
            2057: 3,
            2058: 2,
            2059: 1,
            2065: 1,
            17429: 1,
            3098: 1,
            687: 3,
            2084: 1,
            42: 58,
            43: 107,
            9260: 1,
            11309: 1,
            11829: 1,
            9271: 1,
            6154: 1,
            64: 15,
            1094: 1,
            12376: 1,
            89: 1,
            10848: 1,
            5223: 1,
            69231: 1,
            7795: 1,
            2678: 1,
            8830: 1,
            29826: 1,
            16006: 10,
            8938: 1,
            17055: 2,
            87712: 1,
            23202: 1,
            7441: 1,
            17681: 1,
            12456: 1,
            41132: 1,
            25263: 6,
            689: 1,
            9916: 1,
            10101: 2,
            1730: 1,
            10948: 1,
            26826: 1,
            6357: 1,
            13021: 2,
            1246: 4,
            19683: 1,
            1765: 1,
            1767: 1,
            1768: 1,
            1769: 4,
            1770: 6,
            1771: 3,
            1772: 2,
            1773: 4,
            1774: 4,
            1775: 1,
            1776: 1,
            1779: 1,
            40696: 1,
            767: 1,
            17665: 1,
            27909: 1,
            12550: 1,
            5385: 1,
            16651: 1,
            5392: 1,
            26385: 1,
            12056: 1,
            41245: 2,
            13097: 1,
            15152: 1,
            310: 1,
            40759: 1,
            9528: 1,
            8000: 7,
            471: 1,
            15180: 1,
            14158: 3,
            37719: 2,
            1895: 1,
            31082: 1,
            19824: 1,
            30956: 1,
            18807: 1,
            11095: 1,
            37756: 2,
            746: 1,
            10475: 1,
            4332: 1,
            35730: 1,
            11667: 1,
            16788: 1,
            12182: 4,
            39663: 1,
            9126: 1,
            35760: 1,
            12735: 1,
            6594: 1,
            451: 15,
            19402: 1,
            463: 3,
            10193: 1,
            16853: 6,
            982: 1,
            15865: 1,
            2008: 2,
            476: 1,
            13655: 1,
            10213: 1,
            10737: 1,
            15858: 1,
            2035: 6,
            2039: 1,
            2041: 2
        }

        lens = []
        for key in amazon_msg_lens:
            lens += [key] * amazon_msg_lens[key]

        target_len_in_bytes = random.choice(lens)

        target_len_in_bits = target_len_in_bytes * 8.0
        target_len_in_bits = int(target_len_in_bits)

        return target_len_in_bits

########### formats

conf = {}

conf["http_request_keep_alive"] = {
    "grammar": "http_request_keep_alive",
    "handler_order": ["URL"],
    "handlers": {"URL": RankerHandler("[a-zA-Z0-9\?\-\.\&]+", 2048), }
}

conf["http_response_keep_alive"] = {
    "grammar": "http_response_keep_alive",
    "handler_order": [  #"COOKIE",
        "HTTP-RESPONSE-BODY", "CONTENT-LENGTH"
    ],
    "handlers": {
        "CONTENT-LENGTH": HttpContentLengthHandler(),
        "COOKIE": RankerHandler("([a-zA-Z0-9]+=[a-zA-Z0-9]+;)+", 128),
        "HTTP-RESPONSE-BODY": FteHandler(".+", 128),
    }
}

conf["http_request_close"] = {
    "grammar": "http_request_close",
    "handler_order": ["URL"],
    "handlers": {"URL": RankerHandler("[a-zA-Z0-9\?\-\.\&]+", 2048), }
}

conf["http_response_close"] = {
    "grammar": "http_response_close",
    "handler_order": [  #"COOKIE",
        "HTTP-RESPONSE-BODY", "CONTENT-LENGTH"
    ],
    "handlers": {
        "CONTENT-LENGTH": HttpContentLengthHandler(),
        "COOKIE": RankerHandler("([a-zA-Z0-9]+=[a-zA-Z0-9]+;)+", 128),
        "HTTP-RESPONSE-BODY": FteHandler(".+", 128),
    }
}

conf["pop3_message_response"] = {
    "grammar": "pop3_message_response",
    "handler_order": ["POP3-RESPONSE-BODY", "CONTENT-LENGTH"],
    "handlers": {
        "CONTENT-LENGTH": Pop3ContentLengthHandler(),
        "POP3-RESPONSE-BODY": RankerHandler("[a-zA-Z0-9]+", 2048),
    }
}

conf["pop3_password"] = {
    "grammar": "pop3_password",
    "handler_order": ["PASSWORD"],
    "handlers": {"PASSWORD": RankerHandler("[a-zA-Z0-9]+", 256), }
}

conf["http_request_keep_alive_with_msg_lens"] = {
    "grammar": "http_request_keep_alive",
    "handler_order": ["URL"],
    "handlers": {"URL": FteMsgLensHandler("[a-zA-Z0-9\?\-\.\&]+", 2048), }
}

conf["http_response_keep_alive_with_msg_lens"] = {
    "grammar": "http_response_keep_alive",
    "handler_order": ["HTTP-RESPONSE-BODY", "CONTENT-LENGTH"],
    "handlers": {
        "CONTENT-LENGTH": HttpContentLengthHandler(),
        "HTTP-RESPONSE-BODY": FteMsgLensHandler(".+", 2048),
    }
}

conf["http_amazon_request"] = {
    "grammar": "http_request_keep_alive",
    "handler_order": ["URL"],
    "handlers": {"URL": RankerHandler("[a-zA-Z0-9\?\-\.\&]+", 2048), }
}

conf["http_amazon_response"] = {
    "grammar": "http_response_keep_alive",
    "handler_order": ["HTTP-RESPONSE-BODY", "CONTENT-LENGTH"],
    "handlers": {
        "CONTENT-LENGTH": HttpContentLengthHandler(),
        "HTTP-RESPONSE-BODY": AmazonMsgLensHandler(".+", 128),
    }
}

############# grammars


def parser(grammar, msg):
    if grammar.startswith("http_response") or grammar == "http_amazon_response":
        return http_response_parser(msg)
    elif grammar.startswith("http_request") or grammar == "http_amazon_request":
        return http_request_parser(msg)
    elif grammar.startswith("pop3_message_response"):
        return pop3_parser(msg)
    elif grammar.startswith("pop3_password"):
        return pop3_password_parser(msg)


def generate_template(grammar):
    return random.choice(templates[grammar])

#############

templates = {}

server_listen_iface = marionette.conf.get("server.listen_iface")

templates["http_request_keep_alive"] = [
    "GET http://"+server_listen_iface+":8080/%%URL%% HTTP/1.1\r\nUser-Agent: marionette 0.1\r\nConnection: keep-alive\r\n\r\n",
]

templates["http_request_close"] = [
    "GET http://"+server_listen_iface+":8080/%%URL%% HTTP/1.1\r\nUser-Agent: marionette 0.1\r\nConnection: close\r\n\r\n",
]

templates["http_response_keep_alive"] = [
    "HTTP/1.1 200 OK\r\nContent-Length: %%CONTENT-LENGTH%%\r\nConnection: keep-alive\r\n\r\n%%HTTP-RESPONSE-BODY%%",
    "HTTP/1.1 404 Not Found\r\nContent-Length: %%CONTENT-LENGTH%%\r\nConnection: keep-alive\r\n\r\n%%HTTP-RESPONSE-BODY%%",
]

templates["http_response_close"] = [
    "HTTP/1.1 200 OK\r\nContent-Length: %%CONTENT-LENGTH%%\r\nConnection: close\r\n\r\n%%HTTP-RESPONSE-BODY%%",
    "HTTP/1.1 404 Not Found\r\nContent-Length: %%CONTENT-LENGTH%%\r\nConnection: close\r\n\r\n%%HTTP-RESPONSE-BODY%%",
]

templates["pop3_message_response"] = [
    "+OK %%CONTENT-LENGTH%% octets\nReturn-Path: sender@example.com\nReceived: from client.example.com ([192.0.2.1])\nFrom: sender@example.com\nSubject: Test message\nTo: recipient@example.com\n\n%%POP3-RESPONSE-BODY%%\n.\n",
]

templates["pop3_password"] = ["PASS %%PASSWORD%%\n", ]

templates["http_request_keep_alive_with_msg_lens"] = templates["http_request_keep_alive"]
templates["http_response_keep_alive_with_msg_lens"] = templates["http_response_keep_alive"]
templates["http_amazon_request"] = templates["http_request_keep_alive"]
templates["http_amazon_response"] = templates["http_response_keep_alive"]


def get_http_header(header_name, msg):
    retval = None

    message_lines = msg.split("\r\n")
    for line in message_lines[1:-2]:
        line_compontents = line.partition(": ")
        if line_compontents[0] == header_name:
            retval = line_compontents[-1]
            break

    return retval


def http_request_parser(msg):
    if not msg.startswith("GET"): return None

    retval = {}

    if msg.startswith("GET http"):
        retval["URL"] = '/'.join(msg.split('\r\n')[0][:-9].split('/')[3:])
    else:
        retval["URL"] = '/'.join(msg.split('\r\n')[0][:-9].split('/')[1:])

    if not msg.endswith("\r\n\r\n"):
        retval = None

    return retval


def http_response_parser(msg):
    if not msg.startswith("HTTP"): return None

    retval = {}

    retval["CONTENT-LENGTH"] = int(get_http_header("Content-Length", msg))
    retval["COOKIE"] = get_http_header("Cookie", msg)
    try:
        retval["HTTP-RESPONSE-BODY"] = msg.split("\r\n\r\n")[1]
    except:
        retval["HTTP-RESPONSE-BODY"] = ''

    if retval["CONTENT-LENGTH"] != len(retval["HTTP-RESPONSE-BODY"]):
        retval = None

    return retval


def pop3_parser(msg):
    retval = {}

    try:
        retval["POP3-RESPONSE-BODY"] = msg.split('\n\n')[1]
        assert retval["POP3-RESPONSE-BODY"].endswith('\n.\n')
        retval["POP3-RESPONSE-BODY"] = retval["POP3-RESPONSE-BODY"][:-3]
        retval["CONTENT-LENGTH"] = len(retval["POP3-RESPONSE-BODY"])
    except Exception as e:
        pass
        retval = {}

    return retval


def pop3_password_parser(msg):
    retval = {}

    try:
        assert msg.endswith('\n')
        retval["PASSWORD"] = msg[5:-1]
    except Exception as e:
        retval = {}

    return retval
