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
import usermgr
import groupmgr
import sessionmgr
import web

DATA_DIR = util.get_relative_path(__file__, '../../../private/websys/')
GROUPS_DATA_FILE_PATH = DATA_DIR + 'groups.json'

#------------------------------------------------------------------------------
# Returns None if the value not found
def get_request_param(key, default=None):
    return web.get_request_param(key, default=default)

def get_request_param_as_int(key):
    return web.get_request_param_as_int(key)

def send_result_json(status, body=None):
    web.send_result_json(status, body)

def send_error_text(msg):
    b = msg.encode()
    util.send_binary(b, filename='error.txt')

def proc_on_forbidden():
    send_result_json('FORBIDDEN')

#------------------------------------------------------------------------------
def proc_get_user_list(context):
    if not context.has_permission('sysadmin'):
        web.send_result_json('FORBIDDEN', body=None)
        return

    user_dict = usermgr.get_all_user_info(True)
    guest_user_dict = usermgr.get_all_guest_user_info(True)
    if guest_user_dict is not None:
        user_dict.update(guest_user_dict)

    web.send_result_json('OK', body=user_dict)

#------------------------------------------------------------------------------
def proc_get_session_list(context):
    if not context.has_permission('sysadmin'):
        web.send_result_json('FORBIDDEN', body=None)
        return

    sessions = get_sorted_session_list()

    p_logs = get_request_param('logs')
    if p_logs == '1':
        p_offset = get_request_param_as_int('offset')
        timeline_logs = ger_timeline_logs_by_session(sessions, p_offset)

        for i in range(len(sessions)):
            session = sessions[i]
            sid = session['sid']

            if sid in timeline_logs:
                logs = timeline_logs[sid]
            else:
                logs = []

            session['timeline_log'] = logs

    web.send_result_json('OK', body=sessions)

def ger_timeline_logs_by_session(sessions, target_offset):
    now = util.now()

    tm = now - util.DAY * target_offset
    mn_timestamp = util.get_midnight_timestamp(tm)
    target_from = mn_timestamp
    target_to = mn_timestamp + util.DAY

    users = {}
    for i in range(len(sessions)):
        session = sessions[i]
        uid = session['uid']
        users[uid] = 1

    # {
    #   sid: [
    #     time,
    #     time
    #     ...
    #   ].
    #   ...
    # }
    timeline_logs_by_session = {}
    for uid in users:
        logs = sessionmgr.get_user_timeline_log(uid)
        for i in range(len(logs)):
            line = logs[i]
            values = sessionmgr.get_timeline_log_field_values(line)
            sid = values['sid']
            if sid not in timeline_logs_by_session:
                timeline_logs_by_session[sid] = []
            time = values['time']

            if target_from <= time and time < target_to:
                timeline_logs_by_session[sid].append(time)

    return timeline_logs_by_session

# [
#  {
#   "sid": "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
#   "uid": "root",
#   "time": 1234567890.123456,
#   "tz": "+0900",
#   "addr": "::1",
#   "host": "hostname",
#   "ua": "Mozilla/5.0",
#   "user_fullname": "John Doe"
#   "c_time": 1234567890.123456,
#   "c_tz": "+0900",
#   "c_addr": "::1",
#   "c_host": "hostname",
#   "c_ua": "Mozilla/5.0",
#   "is_guest": False
#  },
#  ...
# ]
def get_sorted_session_list():
    sessions = sessionmgr.get_all_sessions_info()
    users = usermgr.get_all_user_info()

    last_access_time_list = []
    for sid in sessions:
        session = sessions[sid]
        last_access_time_list.append(session['time'])

    last_access_time_list.sort(reverse=True)
    new_list = []
    for i in range(len(last_access_time_list)):
        time = last_access_time_list[i]
        for sid in sessions:
            session = sessions[sid]
            if session['time'] == time:
                uid = session['uid']
                user_fullname = _get_user_fullname(users, uid)
                session['user_fullname'] = user_fullname
                new_list.append(session)

    return new_list

def _get_user_fullname(users, uid):
    if uid in users:
        user = users[uid]
        return user['name']
    return ''

#------------------------------------------------------------------------------
def proc_get_group_list(context):
    group_list = groupmgr.get_group_list()
    result = {
        'group_list': group_list
    }
    web.send_result_json('OK', result)

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
        if context.has_permission('sysadmin'):
            proc_api(context, act)
            return
    proc_on_forbidden()
