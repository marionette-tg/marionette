import os
import sys
import copy
import glob
import hashlib
import fnmatch
import codecs

import ply.lex as lex
import ply.yacc as yacc

import fte.bit_ops

sys.path.append('.')

import marionette.executables.pioa

# TODO: fix it s.t. "server" in var name doesn't cause problem

tokens = (
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
    'ACTION_KWD',
    'DOT',
)

# Regular expression rules for simple tokens
t_COMMA = r','
t_COLON = r':'
t_DOT = r'\.'
t_LPAREN = r'\('
t_RPAREN = r'\)'

t_ignore_COMMENT = r'\#.*'  # comments


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


def t_carriagereturn(t):
    r'\r+'
    t.lexer.lineno += len(t.value)

# A string containing ignored characters (spaces and tabs)
t_ignore = ' \t\n\r'

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
    """connection_banner : CONNECTION_KWD LPAREN TRANSPORT_KWD COMMA port RPAREN COLON"""
    p[0] = [p[3], p[5]]

def p_port(p):
    """
    port : KEY
    port : p_integer_arg
    """
    p[0] = p[1]

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
        p[0] += [marionette.action.MarionetteAction(p[2], p[4][i][0],
                                                          p[4][i][1],
                                                          p[4][i][2],
                                                          p[4][i][3],
                                                          p[4][i][4])]


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
    # Suppress deprecation warning for invalid escape sequences (e.g., \C, \ , \.)
    # These are intentional in format files and codecs.decode handles them correctly
    import warnings
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=DeprecationWarning, message='.*invalid escape.*')
        p[0] = codecs.decode(p[0], 'unicode_escape')

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
    print("Syntax error at '%s' on line %s" % (str([p.value]), p.lineno))
    # yacc.errok()

yacc.yacc(debug=False, write_tables=False)

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

def get_search_dirs():
    dsl_dir = os.path.dirname(os.path.join(__file__))
    dsl_dir = os.path.join(dsl_dir, 'formats')
    dsl_dir = os.path.abspath(dsl_dir)
    cwd_dir = os.path.join(os.getcwd(), 'marionette', 'formats')
    cwd_dir = os.path.abspath(cwd_dir)
    retval = [dsl_dir, # find formats based on location of dsl.py
              cwd_dir, # find formats based on location of marionette_client.exe
              sys.prefix, # find formats based on location of python install
              sys.exec_prefix, # same as above
             ]
    return retval

def get_format_dir():
    retval = None

    search_dirs = get_search_dirs()
    FORMAT_BANNER = '### marionette formats dir ###'
    for cur_dir in search_dirs:
        init_path = os.path.join(cur_dir, '__init__.py')

        # check if __init__ marks our marionette formats dir
        if os.path.exists(init_path):
            with open(init_path) as fh:
                contents = fh.read()
                contents = contents.strip()
                if contents != FORMAT_BANNER:
                    continue
                else:
                    retval = cur_dir
                    break
        else:
            continue

    return retval

def find_mar_files(party, format_name, version=None):
    retval = []

    # get marionette format directory
    format_dir = get_format_dir()

    # check all subdirs unless a version is specified
    if version:
        subdirs = glob.glob(os.path.join(format_dir, version))
    else:
        subdirs = glob.glob(os.path.join(format_dir, '*'))

    # make sure we prefer the most recent format
    subdirs.sort()

    # for each subdir, load our format_name
    formats = {}
    for path in subdirs:
        if os.path.isdir(path):
            conf_path = os.path.join(path, format_name + '.mar')
            if os.path.exists(conf_path):
                if not formats.get(format_name):
                    formats[format_name] = []
                if party == 'client':
                    formats[format_name] = [conf_path]
                elif party == 'server':
                    formats[format_name] += [conf_path]

    for key in formats.keys():
        retval += formats[key]

    return retval

def list_mar_files(party):
    format_dir = get_format_dir()

    subdirs = glob.glob(os.path.join(format_dir,'*'))

    mar_files = []
    for path in subdirs:
        if os.path.isdir(path):
            format_version = os.path.basename(path)

            for root, dirnames, filenames in os.walk(path):
                for filename in fnmatch.filter(filenames, '*.mar'):
                    full_path = os.path.join(root,filename)
                    rel_path = os.path.relpath(full_path, path)
                    format = os.path.splitext(rel_path)[0]
                    mar_file = "%s:%s" % (format,format_version)
                    mar_files.append(mar_file)

    return mar_files

def get_latest_version(party, format_name):
    mar_version = None

    # get marionette format directory
    format_dir = get_format_dir()

    subdirs = glob.glob(os.path.join(format_dir, '*'))

    # make sure we prefer the most recent format
    subdirs.sort()

    # for each subdir, load our format_name
    for path in subdirs:
        if os.path.isdir(path):
            conf_path = os.path.join(path, format_name + '.mar')
            if os.path.exists(conf_path):
                mar_version = path.split('/')[-1]

    return mar_version


def load_all(party, format_name, version=None):
    retval = []

    mar_files = find_mar_files(party, format_name, version)
    if not mar_files:
        raise Exception("Can't find "+format_name)

    for mar_path in mar_files:
        retval.append(load(party, format_name, mar_path))

    return retval


def load(party, format_name, mar_path):

    with open(mar_path) as f:
        mar_str = f.read()

    parsed_format = parse(mar_str)
    
    # Validate format before creating executable
    import marionette.format_validator
    try:
        marionette.format_validator.validate_format(parsed_format)
    except marionette.format_validator.FormatValidationError as e:
        raise Exception(f"Format validation failed for {format_name}: {str(e)}")

    first_sender = 'client'
    if format_name in ["ftp_pasv_transfer"]:
        first_sender = "server"

    executable = marionette.executables.pioa.PIOA(party, first_sender)
    executable.set_transport_protocol(parsed_format.get_transport())
    executable.set_port(parsed_format.get_port())
    executable.set_local(
        "model_uuid", get_model_uuid(mar_str))

    for transition in parsed_format.get_transitions():
        executable.add_state(transition.get_src())
        executable.add_state(transition.get_dst())
        executable.states_[
            transition.get_src()].add_transition(
            transition.get_dst(),
            transition.get_action_block(),
            transition.get_probability())
        if transition.is_error_transition():
            executable.states_[
                transition.get_src()].set_error_transition(transition.get_dst())

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
    executable.do_precomputations()

    # Check if "end" state already has outgoing transitions defined in the format
    end_state = executable.states_.get("end")
    if end_state:
        # Only add automatic "dead" state if "end" has no outgoing transitions
        # This allows formats to explicitly define transitions from "end"
        if not end_state.transitions_:
            executable.add_state("dead")
            executable.states_["end"].add_transition("dead", None, 1)
            executable.states_["dead"].add_transition("dead", None, 1)

    return executable


def get_model_uuid(format_str):
    m = hashlib.md5()
    m.update(format_str.encode('utf-8'))
    bytes_digest = m.digest()
    return fte.bit_ops.bytes_to_long(bytes_digest[:4])
