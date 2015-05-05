import sys
import copy
import hashlib

import ply.lex as lex
import ply.yacc as yacc

import fte.bit_ops

sys.path.append('.')

import marionette.PA

# TODO: fix it s.t. "server" in var name doesn't cause problem

tokens = (
    'BOOLEAN',
    'CONNECTION_KWD',
    'KEY',
    'FLOAT',
    'INTEGER',
    'LPAREN',
    'RPAREN',
    'STRING',
    'COMMA',
    'COLON',
    'TRANSPORT_KWD',
    'CLIENT_KWD',
    'SERVER_KWD',
    'START_KWD',
    'END_KWD',
    'REGEX_MATCH_INCOMING_KWD',
    'IF_KWD',
    'NULL_KWD',
    'MODULE_KWD',
    'ACTION_KWD',
    'DOT',
    'EQUALS',
    'NEWLINE',
)

# Regular expression rules for simple tokens
t_COMMA = r','
t_COLON = r':'
t_DOT = r'\.'
t_LPAREN = r'\('
t_RPAREN = r'\)'

t_ignore_COMMENT = r'\#.*'  # comments
t_EQUALS = r'='


def t_CONNECTION_KWD(t):
    r'connection'
    return t


def t_CLIENT_KWD(t):
    r'client'
    return t


def t_SERVER_KWD(t):
    r'server'
    return t


def t_START_KWD(t):
    r'start'
    return t


def t_END_KWD(t):
    r'end'
    return t


def t_ACTION_KWD(t):
    r'action'
    return t


def t_NULL_KWD(t):
    r'NULL'
    return t


def t_TRANSPORT_KWD(t):
    r'(tcp|udp)'
    return t

def t_REGEX_MATCH_INCOMING_KWD(t):
    r"regex_match_incoming"
    return t

def t_IF_KWD(t):
    r"if"
    return t

def t_STRING(t):
    r'("[^"]*")|(\'[^\']*\')'
    return t


def t_BOOLEN(t):
    r'true | false'
    t.value = (t.value == "true")
    return t


def t_FLOAT(t):
    r'([-]?(\d+)(\.\d+)(e(\+|-)?(\d+))? | (\d+)e(\+|-)?(\d+))([lL]|[fF])?'
    t.value = float(t.value)
    return t


def t_INTEGER(t):
    r'[-]?\d+([uU]|[lL]|[uU][lL]|[lL][uU])?'
    t.value = int(t.value)
    return t


def t_KEY(t):
    r'[a-zA-Z_][a-zA-Z0-9_#\?]*'
    return t

# Define a rule so we can track line numbers


def t_NEWLINE(t):
    r'\n+'
    return t


def t_carriagereturn(t):
    r'\r+'
    t.lexer.lineno += len(t.value)

# A string containing ignored characters (spaces and tabs)
t_ignore = ' \t\n'

# Error handling rule


def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

lex.lex()

###################


def p_start(p):
    """start : model action_blocks"""
    p[0] = p[1] + [p[2]]


def p_model(p):
    """model : connection_banner transition_list"""
    p[0] = p[1] + [p[2]]


def p_connection_banner(p):
    """connection_banner : CONNECTION_KWD LPAREN TRANSPORT_KWD COMMA INTEGER RPAREN COLON"""
    p[0] = [p[3], p[5]]


def p_transition_list(p):
    """
    transition_list : transition_list transition
    """
    p[0] = p[1] + [p[2]]


def p_transitions(p):
    """
    transition_list : transition
    """
    p[0] = [p[1]]


def p_transition(p):
    """
    transition : START_KWD KEY NULL_KWD FLOAT
    transition : KEY KEY NULL_KWD FLOAT
    transition : KEY END_KWD NULL_KWD FLOAT
    transition : START_KWD KEY KEY FLOAT
    transition : KEY KEY KEY FLOAT
    transition : KEY END_KWD KEY FLOAT
    transition : START_KWD KEY NULL_KWD INTEGER
    transition : KEY KEY NULL_KWD INTEGER
    transition : KEY END_KWD NULL_KWD INTEGER
    transition : START_KWD KEY KEY INTEGER
    transition : KEY KEY KEY INTEGER
    transition : KEY END_KWD KEY INTEGER
    transition : START_KWD KEY NULL_KWD KEY
    transition : KEY KEY NULL_KWD KEY
    transition : KEY END_KWD NULL_KWD KEY
    transition : START_KWD KEY KEY KEY
    transition : KEY KEY KEY KEY
    transition : KEY END_KWD KEY KEY
    """
    p[3] = None if p[3] == 'NULL' else p[3]
    if p[4] == 'error':
        p[0] = MarionetteTransition(p[1], p[2], p[3], 0, True)
    else:
        p[0] = MarionetteTransition(p[1], p[2], p[3], p[4], False)


def p_action_blocks(p):
    """
    action_blocks : action_blocks action_block
    """
    if isinstance(p[1], list):
        if isinstance(p[1][0], list):
            p[0] = p[1][0] + [p[2]]
        else:
            p[0] = p[1] + p[2]
    else:
        p[0] = [p[1], p[2]]


def p_action_blocks2(p):
    """
    action_blocks : action_block
    """
    p[0] = p[1]


def p_action_block(p):
    """
    action_block : ACTION_KWD KEY COLON actions
    """
    p[0] = []
    for i in range(len(p[4])):
        p[0] += [marionette.action.MarionetteAction(p[2], p[4][i][0], p[4][i][1], p[4][i][2], p[4][i][3], p[4][i][4])]


def p_actions(p):
    """
    actions : actions action
    """
    p[0] = p[1] + [p[2]]


def p_actions2(p):
    """
    actions : action
    """
    p[0] = [p[1]]


def p_action(p):
    """
    action : CLIENT_KWD KEY DOT KEY LPAREN args RPAREN
    action : SERVER_KWD KEY DOT KEY LPAREN args RPAREN
    action : CLIENT_KWD KEY DOT KEY LPAREN args RPAREN IF_KWD REGEX_MATCH_INCOMING_KWD LPAREN p_string_arg RPAREN
    action : SERVER_KWD KEY DOT KEY LPAREN args RPAREN IF_KWD REGEX_MATCH_INCOMING_KWD LPAREN p_string_arg RPAREN
    """
    if len(p)==8:
        p[0] = [p[1], p[2], p[4], p[6], None]
    elif len(p)==13:
        p[0] = [p[1], p[2], p[4], p[6], p[11]]


def p_args(p):
    """
    args : args COMMA arg
    args : arg
    """
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]


def p_arg(p):
    """
    arg : p_string_arg
    arg : p_integer_arg
    arg : p_float_arg
    """
    p[0] = p[1]


def p_string_arg(p):
    """
    p_string_arg : STRING
    """
    p[0] = str(p[1][1:-1])


def p_integer_arg(p):
    """
    p_integer_arg : INTEGER
    """
    p[0] = int(p[1])


def p_float_arg(p):
    """
    p_float_arg : FLOAT
    """
    p[0] = float(p[1])


def p_error(p):
    print "Syntax error at '%s' on line %s" % (str([p.value]), p.lineno)
    # yacc.errok()

yacc.yacc()

###################


class MarionetteTransition(object):

    def __init__(self, src, dst, action_block, probability, is_error_transition=False):
        self.src_ = src
        self.dst_ = dst
        self.action_block_ = action_block
        self.probability_ = probability
        self.is_error_transition_ = is_error_transition

    def get_src(self):
        return self.src_

    def get_dst(self):
        return self.dst_

    def get_action_block(self):
        return self.action_block_

    def get_probability(self):
        return self.probability_

    def is_error_transition(self):
        return self.is_error_transition_

class MarionetteFormat(object):

    def set_transport(self, transport):
        self.transport_ = transport

    def get_transport(self):
        return self.transport_

    def set_port(self, port):
        self.port_ = port

    def get_port(self):
        return self.port_

    def set_transitions(self, transitions):
        self.transitions_ = transitions

    def get_transitions(self):
        return self.transitions_

    def set_action_blocks(self, action_blocks):
        self.action_blocks_ = action_blocks

    def get_action_blocks(self):
        return self.action_blocks_


def parse(s):
    s = s.strip()

    retval = MarionetteFormat()

    parsed_format = yacc.parse(s)

    retval.set_transport(parsed_format[0])
    retval.set_port(parsed_format[1])
    retval.set_transitions(parsed_format[2])
    retval.set_action_blocks(parsed_format[3])

    return retval


def load(party, format_name):
    with open("marionette/formats/" + format_name + ".mar") as f:
        mar_str = f.read()

    parsed_format = parse(mar_str)

    first_sender = 'client'
    if format_name in ["ftp_pasv_transfer"]:
        first_sender = "server"

    executable = marionette.PA.PA(party, first_sender)
    executable.set_port(parsed_format.get_port())
    executable.marionette_state_.set_local(
        "model_uuid", get_model_uuid(mar_str))

    for transition in parsed_format.get_transitions():
        executable.add_state(transition.get_src())
        executable.add_state(transition.get_dst())
        executable.states_[
            transition.get_src()].add_transition(
            transition.get_dst(),
            transition.get_action_block(),
            transition.get_probability())

    actions = []
    for action in parsed_format.get_action_blocks():
        actions.append(action)
        complementary_action = copy.deepcopy(action)
        if action.get_module() in ['fte', 'tg']:
            if action.get_method() == 'send':
                complementary_method = 'recv'
            elif action.get_method() == 'send_async':
                complementary_method = 'recv_async'
            complementary_party = 'client' if action.get_party(
            ) == 'server' else 'server'

            complementary_action.set_method(complementary_method)
            complementary_action.set_party(complementary_party)

            actions.append(complementary_action)
        elif action.get_module() in ['io']:
            complementary_method = 'gets' if action.get_method(
            ) == 'puts' else 'puts'
            complementary_party = 'client' if action.get_party(
            ) == 'server' else 'server'

            complementary_action.set_method(complementary_method)
            complementary_action.set_party(complementary_party)

            actions.append(complementary_action)

    executable.actions_ = actions

    if executable.states_.get("end"):
        executable.add_state("dead")
        executable.states_["end"].add_transition("dead", None, 1)
        executable.states_["dead"].add_transition("dead", None, 1)

    return executable


def get_model_uuid(format_str):
    m = hashlib.md5()
    m.update(format_str)
    bytes = m.digest()
    return fte.bit_ops.bytes_to_long(bytes[:4])
