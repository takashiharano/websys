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
import userman
import sessionman
import web

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
    send_result_json('FORBIDDEN')

#------------------------------------------------------------------------------
def proc_get_user_list(context):
    if not context.has_permission('sysmanage'):
        web.send_result_json('FORBIDDEN', body=None)
        return

    user_dict = userman.get_all_user_info()
    guest_user_dict = userman.get_all_guest_user_info()
    if guest_user_dict is not None:
        user_dict.update(guest_user_dict)

    web.send_result_json('OK', body=user_dict)

#------------------------------------------------------------------------------
def proc_get_session_list(context):
    if not context.has_permission('sysmanage'):
        web.send_result_json('FORBIDDEN', body=None)
        return

    sessions = get_user_sessions()
    web.send_result_json('OK', body=sessions)

# uid: {
#   [
#     {
#      "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef": {
#       "sid": "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
#       "uid": "root",
#       "time": 1234567890.123456,
#       "tz": "+0900",
#       "addr": "::1",
#       "host": "hostname",
#       "ua": "Mozilla/5.0",
#       "is_guest": False,
#       "last_accessed": {
#        "time": 1234567890.123456,
#        "tz": "+0900",
#        "addr": "::1",
#        "host": "hostname",
#        "ua": "Mozilla/5.0"
#       }
#      }
#     }
#   ]
# }
def get_user_sessions():
    users = userman.get_all_user_info()
    sessions = sessionman.get_all_sessions_info()
    user_sessions = {}
    last_accessed_times = {}
    for sid in sessions:
        session = sessions[sid]
        uid = session['uid']
        if uid not in user_sessions:
            user_sessions[uid] = []
            last_accessed_times[uid] = []
        user_sessions[uid].append(session)
        last_accessed_times[uid].append(session['last_accessed']['time'])

    # sort by last_accessed time
    for uid in user_sessions:
        user_name = ''
        if uid in users:
            user = users[uid]
            user_name = user['name']
        sessions = user_sessions[uid]
        last_accessed_time_list = last_accessed_times[uid]
        last_accessed_time_list.sort(reverse=True)
        new_list = []
        for i in range(len(last_accessed_time_list)):
            time = last_accessed_time_list[i]
            for j in range(len(last_accessed_time_list)):
                session = sessions[j]
                if session['last_accessed']['time'] == time:

                    session['user_name'] = user_name
                    new_list.append(session)
        user_sessions[uid] = new_list

    return user_sessions

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
    if context.is_authorized():
        if context.has_permission('sysmanage'):
            proc_api(context, act)
            return
    proc_on_forbidden()
