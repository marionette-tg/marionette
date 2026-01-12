#!/usr/bin/env python
# coding: utf-8

import math
import socket
import random
import string

from twisted.python import log

import fte
import fte.encoder
import fte.bit_ops
import re

import marionette.record_layer

def send(channel, marionette_state, input_args):
    grammar = input_args[0]

    ctxt = generate_template(grammar)

    for handler_key in conf[grammar]["handler_order"]:
        ctxt = execute_handler_sender(
            marionette_state,
            grammar,
            handler_key,
            ctxt,
            marionette_state.get_global("multiplexer_outgoing"))

    ctxt_len = len(ctxt)
    while len(ctxt) > 0:
        try:
            bytes_sent = channel.send(ctxt)
            ctxt = ctxt[bytes_sent:]
        except socket.timeout:
            continue
    retval = (ctxt_len == bytes_sent)

    return retval


def recv(channel, marionette_state, input_args):
    retval = False
    grammar = input_args[0]

    try:
        ctxt = channel.recv()

        if parser(grammar, ctxt):
            cell_str = ''
            for handler_key in conf[grammar]["handler_order"]:
                tmp_str = execute_handler_receiver(marionette_state,
                                                   grammar, handler_key, ctxt)
                if tmp_str:
                    cell_str += tmp_str

            if not cell_str:
                retval = True
            else:
                ##
                cell_obj = marionette.record_layer.unserialize(cell_str)
                assert cell_obj.get_model_uuid() == marionette_state.get_local(
                    "model_uuid")

                marionette_state.set_local(
                    "model_instance_id", cell_obj.get_model_instance_id())
                ##

                if marionette_state.get_local("model_instance_id"):
                    marionette_state.get_global(
                        "multiplexer_incoming").push(cell_str)
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

def get_grammar_capacity(grammar):
    retval = 0
    for handler_key in conf[grammar]["handler_order"]:
        retval += conf[grammar]['handlers'][handler_key].capacity()
    retval /= 8.0
    return retval

# handler + (un)embed functions


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


def execute_handler_sender(marionette_state, grammar, handler_key,
                           template, multiplexer):
    to_execute = conf[grammar]["handlers"][handler_key]

    cell_len_in_bits = to_execute.capacity()
    to_embed = ''
    if cell_len_in_bits > 0:
        cell = multiplexer.pop(marionette_state.get_local("model_uuid"),
                               marionette_state.get_local("model_instance_id"),
                               cell_len_in_bits)
        to_embed = cell.to_string()
    value_to_embed = to_execute.encode(marionette_state, template, to_embed)
    template = do_embed(grammar, template, handler_key, value_to_embed)

    return template


def execute_handler_receiver(marionette_state, grammar, handler_key,
                             ctxt):
    ptxt = ''

    to_execute = conf[grammar]["handlers"][handler_key]

    handler_key_value = do_unembed(grammar, ctxt, handler_key)
    ptxt = to_execute.decode(marionette_state, handler_key_value)

    return ptxt

# handlers

regex_cache_ = {}
fte_cache_ = {}


class RankerHandler(object):

    def __init__(self, regex, msg_len):
        self.regex_ = regex

        regex_key = regex + str(msg_len)
        if not regex_cache_.get(regex_key):
            dfa = fte.regex2dfa.regex2dfa(regex)
            cDFA = fte.cDFA_py.DFA(dfa, msg_len)
            encoder = fte.dfa.DFA(cDFA, msg_len)
            regex_cache_[regex_key] = (dfa, encoder)
        (self.dfa_, self.encoder_) = regex_cache_[regex_key]

    def capacity(self):
        cell_len_in_bytes = int(math.floor(self.encoder_.getCapacity() / 8.0))
        cell_len_in_bits = cell_len_in_bytes * 8
        return cell_len_in_bits

    def encode(self, marionette_state, template, to_embed):
        to_embed_as_int = fte.bit_ops.bytes_to_long(to_embed)
        ctxt = self.encoder_.unrank(to_embed_as_int)
        return ctxt

    def decode(self, marionette_state, ctxt):
        try:
            ptxt = self.encoder_.rank(ctxt)
            ptxt = fte.bit_ops.long_to_bytes(ptxt, self.capacity() // 8)
        except Exception as e:
            pass

        return ptxt


class FteHandler(object):

    def __init__(self, regex, msg_len):
        self.regex_ = regex

        fte_key = regex + str(msg_len)
        if not fte_cache_.get(fte_key):
            dfa = fte.regex2dfa.regex2dfa(regex)
            encrypter = fte.encoder.DfaEncoder(dfa, msg_len)
            fte_cache_[fte_key] = (dfa, encrypter)
        (self.dfa_, self.fte_encrypter_) = fte_cache_[fte_key]

    def capacity(self):
        if self.regex_.endswith(".+"):
            retval = (2 ** 18) * 8
        else:
            cell_len_in_bytes = int(math.floor(self.fte_encrypter_.getCapacity(
            ) / 8.0)) - fte.encoder.DfaEncoderObject._COVERTEXT_HEADER_LEN_CIPHERTEXT - fte.encrypter.Encrypter._CTXT_EXPANSION
            cell_len_in_bits = cell_len_in_bytes * 8
            retval = cell_len_in_bits

        return retval

    def encode(self, marionette_state, template, to_embed):
        ctxt = self.fte_encrypter_.encode(to_embed)
        return ctxt

    def decode(self, marionette_state, ctxt):
        try:
            retval = self.fte_encrypter_.decode(ctxt)
            ptxt = retval[0]
        except Exception as e:
            pass

        return ptxt


class FteMsgLensHandler(FteHandler):

    def capacity(self):
        cell_len_in_bytes = int(math.floor(self.fte_encrypter_.getCapacity(
        ) / 8.0)) - fte.encoder.DfaEncoderObject._COVERTEXT_HEADER_LEN_CIPHERTEXT - fte.encrypter.Encrypter._CTXT_EXPANSION
        cell_len_in_bits = cell_len_in_bytes * 8
        return cell_len_in_bits


class HttpContentLengthHandler(object):

    def capacity(self):
        return 0

    def encode(self, marionette_state, template, to_embed):
        http_body_length = str(len(template.split("\r\n\r\n")[1]))
        return http_body_length

    def decode(self, marionette_state, ctxt):
        return None


class Pop3ContentLengthHandler(object):

    def capacity(self):
        return 0

    def encode(self, marionette_state, template, to_embed):
        pop3_body_length = str(len('\n'.join(template.split("\n")[1:])))
        return pop3_body_length

    def decode(self, marionette_state, ctxt):
        return None


class SetFTPPasvX(object):

    def capacity(self):
        return 0

    def encode(self, marionette_state, template, to_embed):
        ftp_pasv_port = marionette_state.get_local("ftp_pasv_port")
        ftp_pasv_port_x = int(math.floor(ftp_pasv_port / 256.0))
        return str(ftp_pasv_port_x)

    def decode(self, marionette_state, ctxt):
        marionette_state.set_local("ftp_pasv_port_x", int(ctxt))
        return None


class SetFTPPasvY(object):

    def capacity(self):
        return 0

    def encode(self, marionette_state, template, to_embed):
        ftp_pasv_port = marionette_state.get_local("ftp_pasv_port")
        ftp_pasv_port_y = ftp_pasv_port % 256
        return str(ftp_pasv_port_y)

    def decode(self, marionette_state, ctxt):
        ftp_pasv_port_x = marionette_state.get_local("ftp_pasv_port_x")
        ftp_pasv_port_y = int(ctxt)
        ftp_pasv_port = ftp_pasv_port_x * 256 + ftp_pasv_port_y
        marionette_state.set_local("ftp_pasv_port", ftp_pasv_port)
        return None

class SetDnsTransactionId(object):
    def capacity(self):
        return 0

    def encode(self, marionette_state, template, to_embed):
        dns_transaction_id = None
        if marionette_state.get_local("dns_transaction_id"):
            dns_transaction_id =  marionette_state.get_local("dns_transaction_id")
        else:
            dns_transaction_id = chr(random.randint(1,254))+chr(random.randint(1,254))
            marionette_state.set_local("dns_transaction_id", dns_transaction_id)
        return str(dns_transaction_id)

    def decode(self, marionette_state, ctxt):
        marionette_state.set_local("dns_transaction_id", ctxt)
        return None
  
class SetDnsDomain(object):
    def capacity(self):
        return 0

    def encode(self, marionette_state, template, to_embed):
        dns_domain = None
        if marionette_state.get_local("dns_domain"):
            dns_domain =  marionette_state.get_local("dns_domain")
        else:
            dns_domain_len = random.randint(3,63)
            dns_domain = chr(dns_domain_len) + ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(dns_domain_len)) + "\x03" + random.choice(['com', 'net', 'org'])
            marionette_state.set_local("dns_domain", dns_domain)
        return str(dns_domain)

    def decode(self, marionette_state, ctxt):
        marionette_state.set_local("dns_domain", ctxt)
        return None

class SetDnsIp(object):
    def capacity(self):
        return 0

    def encode(self, marionette_state, template, to_embed):
        dns_ip = None
        if marionette_state.get_local("dns_ip"):
            dns_ip =  marionette_state.get_local("dns_ip")
        else:
            dns_ip = chr(random.randint(1,254))+chr(random.randint(1,254))+chr(random.randint(1,254))+chr(random.randint(1,254))
            marionette_state.set_local("dns_ip", dns_ip)
        return str(dns_ip)

    def decode(self, marionette_state, ctxt):
        marionette_state.set_local("dns_ip", ctxt)
        return None
 

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

MIN_PTXT_LEN = fte.encoder.DfaEncoderObject._COVERTEXT_HEADER_LEN_CIPHERTEXT + \
    fte.encrypter.Encrypter._CTXT_EXPANSION + 32

class AmazonMsgLensHandler(object):
    def __init__(self, regex, min_len = MIN_PTXT_LEN, msg_lens = amazon_msg_lens):
        self.regex_ = regex

        self.msg_lens_ = msg_lens
        self.random_lens_ = []
        for key in self.msg_lens_:
            self.random_lens_ += [key] * self.msg_lens_[key]

        self.min_len_ = min_len

        key = self.regex_ + str(self.min_len_)
        if not fte_cache_.get(key):
            dfa = fte.regex2dfa.regex2dfa(self.regex_)
            encoder = fte.encoder.DfaEncoder(dfa, self.min_len_)
            fte_cache_[key] = (dfa, encoder)

        self.max_len_ = 2**18

        self.target_len_ = 0.0


    def capacity(self):

        self.target_len_ = random.choice(self.random_lens_)

        if self.target_len_ < self.min_len_:
            ptxt_len = 0.0

        elif self.target_len_ > self.max_len_:
            #We do this to prevent unranking really large slices
            # in practice this is probably bad since it unnaturally caps 
            # our message sizes to whatever FTE can support
            ptxt_len = self.max_len_
            self.target_len_ = self.max_len_

        else:
            ptxt_len = self.target_len_ - fte.encoder.DfaEncoderObject._COVERTEXT_HEADER_LEN_CIPHERTEXT 
            ptxt_len -= fte.encrypter.Encrypter._CTXT_EXPANSION
            ptxt_len = int(ptxt_len * 8.0)-1

        return ptxt_len

    def encode(self, marionette_state, template, to_embed):
        ctxt = ''

        if self.target_len_ < self.min_len_ or self.target_len_ > self.max_len_:
            key = self.regex_ + str(self.target_len_)
            if not regex_cache_.get(key):
                dfa = fte.regex2dfa.regex2dfa(self.regex_)
                cdfa_obj = fte.cDFA_py.DFA(dfa, self.target_len_)
                encoder = fte.dfa.DFA(cdfa_obj, self.target_len_)
                regex_cache_[key] = (dfa, encoder)

            (dfa, encoder) = regex_cache_[key]

            to_unrank = random.randint(0, encoder.getNumWordsInSlice(self.target_len_))
            ctxt = encoder.unrank(to_unrank)

        else:
            key = self.regex_ + str(self.min_len_)
            (dfa, encoder) = fte_cache_[key]

            ctxt = encoder.encode(to_embed)

            if len(ctxt) != self.target_len_:
                raise Exception("Could not find ctxt of len %d (%d)" % 
                    (self.target_len_,len(ctxt)))

        return ctxt

    def decode(self, marionette_state, ctxt):
        ptxt = None

        ctxt_len = len(ctxt)

        if ctxt_len >= self.min_len_:
            key = self.regex_ + str(self.min_len_)
            (dfa, encoder) = fte_cache_[key]
            
            try:
                retval = encoder.decode(ctxt)
                ptxt = retval[0]
            except Exception as e:
                pass

        return ptxt

# formats

conf = {}

conf["http_request_keep_alive"] = {
    "grammar": "http_request_keep_alive",
    "handler_order": ["URL"],
    "handlers": {"URL": RankerHandler("[a-zA-Z0-9\\?\\-\\.\\&]+", 2048), }
}

conf["http_response_keep_alive"] = {
    "grammar": "http_response_keep_alive",
    "handler_order": [  # "COOKIE",
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
    "handlers": {"URL": RankerHandler("[a-zA-Z0-9\\?\\-\\.\\&]+", 2048), }
}

conf["http_response_close"] = {
    "grammar": "http_response_close",
    "handler_order": [  # "COOKIE",
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
    "handlers": {"URL": FteMsgLensHandler("[a-zA-Z0-9\\?\\-\\.\\&]+", 2048), }
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
    "handlers": {"URL": RankerHandler("[a-zA-Z0-9\\?\\-\\.\\&]+", 2048), }
}

conf["http_amazon_response"] = {
    "grammar": "http_response_keep_alive",
    "handler_order": ["HTTP-RESPONSE-BODY", "CONTENT-LENGTH"],
    "handlers": {
        "CONTENT-LENGTH": HttpContentLengthHandler(),
        "HTTP-RESPONSE-BODY": AmazonMsgLensHandler(".+"),
    }
}

conf["ftp_entering_passive"] = {
    "grammar": "ftp_entering_passive",
    "handler_order": ["FTP_PASV_PORT_X", "FTP_PASV_PORT_Y"],
    "handlers": {
        "FTP_PASV_PORT_X": SetFTPPasvX(),
        "FTP_PASV_PORT_Y": SetFTPPasvY(),
    }
}

conf["dns_request"] = {
    "grammar": "dns_request",
    "handler_order": ["DNS_TRANSACTION_ID", "DNS_DOMAIN"],
    "handlers": {
        "DNS_TRANSACTION_ID": SetDnsTransactionId(),
        "DNS_DOMAIN": SetDnsDomain(),
        }
}

conf["dns_response"] = {
    "grammar": "dns_response",
    "handler_order": ["DNS_TRANSACTION_ID", "DNS_DOMAIN", "DNS_IP"],
    "handlers": {
        "DNS_TRANSACTION_ID": SetDnsTransactionId(),
        "DNS_DOMAIN": SetDnsDomain(),
        "DNS_IP": SetDnsIp(),
        }
}

# grammars


def parser(grammar, msg):
    if grammar.startswith(
            "http_response") or grammar == "http_amazon_response":
        return http_response_parser(msg)
    elif grammar.startswith("http_request") or grammar == "http_amazon_request":
        return http_request_parser(msg)
    elif grammar.startswith("pop3_message_response"):
        return pop3_parser(msg)
    elif grammar.startswith("pop3_password"):
        return pop3_password_parser(msg)
    elif grammar.startswith("ftp_entering_passive"):
        return ftp_entering_passive_parser(msg)
    elif grammar.startswith("dns_request"):
        return dns_request_parser(msg)
    elif grammar.startswith("dns_response"):
        return dns_response_parser(msg)


def generate_template(grammar):
    return random.choice(templates[grammar])

#############

templates = {}

server_listen_ip = marionette.conf.get("server.server_ip")

templates["http_request_keep_alive"] = [
    "GET http://" +
    server_listen_ip +
    ":8080/%%URL%% HTTP/1.1\r\nUser-Agent: marionette 0.1\r\nConnection: keep-alive\r\n\r\n",
]

templates["http_request_close"] = [
    "GET http://" +
    server_listen_ip +
    ":8080/%%URL%% HTTP/1.1\r\nUser-Agent: marionette 0.1\r\nConnection: close\r\n\r\n",
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

templates["http_request_keep_alive_with_msg_lens"] = templates[
    "http_request_keep_alive"]
templates["http_response_keep_alive_with_msg_lens"] = templates[
    "http_response_keep_alive"]
templates["http_amazon_request"] = templates["http_request_keep_alive"]
templates["http_amazon_response"] = templates["http_response_keep_alive"]

templates["ftp_entering_passive"] = [
    "227 Entering Passive Mode (127,0,0,1,%%FTP_PASV_PORT_X%%,%%FTP_PASV_PORT_Y%%).\n",
]

templates["dns_request"] = [
    "%%DNS_TRANSACTION_ID%%\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00%%DNS_DOMAIN%%\x00\x00\x01\x00\x01",
]

templates["dns_response"] = [
   "%%DNS_TRANSACTION_ID%%\x81\x80\x00\x01\x00\x01\x00\x00\x00\x00%%DNS_DOMAIN%%\x00\x01\x00\x01\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x02\x00\x04%%DNS_IP%%",
]

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
    if not msg.startswith("GET"):
        return None

    retval = {}

    if msg.startswith("GET http"):
        retval["URL"] = '/'.join(msg.split('\r\n')[0][:-9].split('/')[3:])
    else:
        retval["URL"] = '/'.join(msg.split('\r\n')[0][:-9].split('/')[1:])

    if not msg.endswith("\r\n\r\n"):
        retval = None

    return retval


def http_response_parser(msg):
    if not msg.startswith("HTTP"):
        return None

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

def ftp_entering_passive_parser(msg):
    retval = {}

    try:
        assert msg.startswith("227 Entering Passive Mode (")
        assert msg.endswith(").\n")
        bits = msg.split(',')
        retval['FTP_PASV_PORT_X'] = int(bits[4])
        retval['FTP_PASV_PORT_Y'] = int(bits[5][:-3])
    except Exception as e:
        retval = {}

    return retval


def validate_dns_domain(msg, dns_response=False):
    if dns_response:
        expected_splits = 3
        split1_msg = '\x81\x80\x00\x01\x00\x01\x00\x00\x00\x00'
    else:
        expected_splits = 2
        split1_msg = '\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00'

    tmp_domain_split1 = msg.split(split1_msg)
    if len(tmp_domain_split1) != 2:
        return None
    tmp_domain_split2 = tmp_domain_split1[1].split('\x00\x01\x00\x01')
    if len(tmp_domain_split2) != expected_splits:
        return None
    tmp_domain = tmp_domain_split2[0]
    # Check for valid prepended length
    # Remove trailing tld prepended length (1), tld (3) and trailing null (1) = 5
    if ord(tmp_domain[0]) != len(tmp_domain[1:-5]): 
        return None
    if ord(tmp_domain[-5]) != 3:
        return None
    # Check for valid TLD
    if not re.search("(com|net|org)\x00$", tmp_domain):
        return None
    # Check for valid domain characters
    if not re.match("^[\\w\\d]+$", tmp_domain[1:-5]):
        return None

    return tmp_domain


def validate_dns_ip(msg):
    tmp_ip_split = msg.split('\x00\x01\x00\x01\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x02\x00\x04')
    if len(tmp_ip_split) != 2:
        return None
    tmp_ip = tmp_ip_split[1]
    if len(tmp_ip) != 4:
        return None

    return tmp_ip


def dns_request_parser(msg):
    retval = {}
    if '\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00' not in msg:
        return retval

    try:
        # Nothing to validate for Transaction ID
        retval["DNS_TRANSACTION_ID"] = msg[:2]

        tmp_domain = validate_dns_domain(msg)
        if not tmp_domain:
            raise Exception("Bad DNS Domain")
        retval["DNS_DOMAIN"] = tmp_domain
        
    except Exception as e:
        retval = {}

    return retval


def dns_response_parser(msg):
    retval = {}
    if '\x81\x80\x00\x01\x00\x01\x00\x00\x00\x00' not in msg:
        return retval

    try:
        # Nothing to validate for Transaction ID
        retval["DNS_TRANSACTION_ID"] = msg[:2]

        tmp_domain = validate_dns_domain(msg, dns_response=True)
        if not tmp_domain:
            raise Exception("Bad DNS Domain")
        retval["DNS_DOMAIN"] = tmp_domain
        
        tmp_ip = validate_dns_ip(msg)
        if not tmp_ip:
            raise Exception("Bad DNS IP")
        retval["DNS_IP"] = tmp_ip

    except Exception as e:
        retval = {}

    return retval
