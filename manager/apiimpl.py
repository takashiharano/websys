#==============================================================================
# Web System Management Screen
# Copyright (c) 2023 Takashi Harano
#==============================================================================
import os
import sys

ROOT_PATH = '../../'

sys.path.append(os.path.join(os.path.dirname(__file__), ROOT_PATH + 'libs'))
import util

util.append_system_path(__file__, ROOT_PATH)
util.append_system_path(__file__, '../')
util.append_system_path(__file__, ROOT_PATH + 'websys/bin')
import websysconf
import web
import sysmanage

DATA_DIR = util.get_relative_path(__file__, '../../../private/websys/')
GROUPS_DATA_FILE_PATH = DATA_DIR + 'groups.json'

#------------------------------------------------------------------------------
# Returns None if the value not found
def get_request_param(key, default=None):
    return web.get_request_param(key, default=default)

def send_result_json(status, body=None):
    web.send_result_json(status, body)

def send_error_text(msg):
    b = msg.encode()
    util.send_binary(b, filename='error.txt')

def proc_on_forbidden():
    send_error_text('ERROR')

#------------------------------------------------------------------------------
def proc_get_groups(context):
    empty_def = '{\n  "g1": {\n    "privs": ""\n  }\n}\n'
    text = util.read_text_file(GROUPS_DATA_FILE_PATH, default=empty_def)
    b64text = util.encode_base64(text)

    result = {
        'text': b64text
    }

    web.send_result_json('OK', result)

#------------------------------------------------------------------------------
def proc_save_groups(context):
    b64text = get_request_param('text')
    text = util.decode_base64(b64text)
    util.write_text_file(GROUPS_DATA_FILE_PATH, text)
    web.send_result_json('OK', None)

#------------------------------------------------------------------------------
def proc_api(context, act):
    status = 'OK'
    result = None
    func_name = 'proc_' + act
    g = globals()
    if func_name in g:
        g[func_name](context)
    else:
        web.send_result_json('PROC_NOT_FOUND:' + act, None)

#------------------------------------------------------------------------------
def main():
    context = web.on_access()
    act = get_request_param('act')
    if sysmanage.is_authorized(context):
        if sysmanage.has_permission(context, 'sysmanage'):
            proc_api(context, act)
            return
    proc_on_forbidden()
