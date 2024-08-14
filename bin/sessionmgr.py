#==============================================================================
# Session Manager
# Copyright (c) 2020 Takashi Harano
#==============================================================================
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import websysconf

sys.path.append(websysconf.UTIL_PATH)
import util

import logger
import common
import usermgr
import web

USER_ROOT_PATH = websysconf.USER_ROOT_PATH
ANONYMOUS_SESSION_SEC = websysconf.ANONYMOUS_SESSION_SEC
SESSION_TIMEOUT_SEC = websysconf.SESSION_TIMEOUT_SEC
MAX_SESSIONS_PER_USER = websysconf.MAX_SESSIONS_PER_USER
ALGOTRITHM = websysconf.ALGOTRITHM
MIN_FILE_UPDATE_INTERVAL_SEC = 0.25

SESSION_DATA_STRUCT = [
   {'name': 'sid'},
   {'name': 'uid'},
   {'name': 'time', 'type': 'float'},
   {'name': 'tz'},
   {'name': 'addr'},
   {'name': 'host'},
   {'name': 'ua'},
   {'name': 'c_time', 'type': 'float'},
   {'name': 'c_tz'},
   {'name': 'c_addr'},
   {'name': 'c_host'},
   {'name': 'c_ua'},
   {'name': 'is_guest', 'type': 'bool'}
]

current_session_info = None

#----------------------------------------------------------
# Get sessions file path
#----------------------------------------------------------
def get_sessions_file_path(uid):
    path = USER_ROOT_PATH + '/' + uid + '/sessions.txt'
    return path

#----------------------------------------------------------
# Get all sessions info
#----------------------------------------------------------
def get_all_sessions_info():
    return load_all_session_info_from_file()

def get_user_sessions(uid):
    path = get_sessions_file_path(uid)
    tsv_text_list = util.read_text_file_as_list(path)
    try:
        sessions = {}
        for i in range(len(tsv_text_list)):
            line = tsv_text_list[i]
            if line != '' and not util.is_comment(line, '#'):
                result = common.parse_tsv_field_values(line, SESSION_DATA_STRUCT, path)
                data = result['values']
                sid = data['sid']
                sessions[sid] = data
    except Exception as e:
        logger.write_system_log('ERROR', uid, 'sessionmgr.get_user_sessions(): ' + str(e))
        sessions = None

    return sessions

#----------------------------------------------------------
# Get session info
#----------------------------------------------------------
# {
#  "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef": {
#   "sid": "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
#   "uid": "root",
#   "time": 1234567890.123456,
#   "tz": "+0900",
#   "addr": "::1",
#   "host": "hostname",
#   "ua": "Mozilla/5.0",
#   "c_time": 1234567890.123456,
#   "c_tz": "+0900",
#   "c_addr": "::1",
#   "c_host": "hostname",
#   "c_ua": "Mozilla/5.0",
#   "is_guest": False
# }
#
# Returns None id the session does not exist.
def get_session_info(sid):
    session = None
    user_dirs = util.list_dirs(USER_ROOT_PATH)
    for i in range(len(user_dirs)):
        uid = user_dirs[i]
        user_sessions = get_user_sessions(uid)
        if user_sessions is not None:
            if sid in user_sessions:
                session = user_sessions[sid]
                break
    return session

#----------------------------------------------------------
# Get current session info
#----------------------------------------------------------
def get_current_session_info_from_global():
    global current_session_info
    return current_session_info

#----------------------------------------------------------
# Set current session info
#----------------------------------------------------------
def set_current_session_info_to_global(info):
    global current_session_info
    current_session_info = info

#----------------------------------------------------------
# Get current session id
# Returns id or None
#----------------------------------------------------------
def get_current_session_id():
    session_id = None
    session_info = get_current_session_info_from_global()
    if session_info is not None:
        session_id = session_info['sid']
    return session_id

#----------------------------------------------------------
# Get user info from session id
#----------------------------------------------------------
def get_user_info_from_sid(sid):
    session_info = get_session_info(sid)
    if session_info is None:
        return None

    uid = session_info['uid']
    user_info = usermgr.get_user_info(uid, guest=True)

    return user_info

#----------------------------------------------------------
# Get session timeout value
#----------------------------------------------------------
def get_session_timeout_value():
    return SESSION_TIMEOUT_SEC

def get_anonymous_session_sec():
    return ANONYMOUS_SESSION_SEC

#----------------------------------------------------------
# Create and register new session info
#----------------------------------------------------------
def create_and_register_session_info(uid, is_guest=False, ext_auth=False):
    new_session_info = create_new_session_info(uid, is_guest)
    if ext_auth:
        new_session_info['ext_auth'] = True
    append_session_info_to_session_file(uid, new_session_info)
    return new_session_info

#----------------------------------------------------------
# Create session info
#----------------------------------------------------------
def create_new_session_info(uid, is_guest=False):
    now = util.get_timestamp()
    sid = generate_session_id(uid)
    new_session = create_session_info(sid, uid, now, is_guest=is_guest)
    return new_session

def create_session_info(sid, uid, now, is_guest=False):
    addr = web.get_ip_addr()
    host = web.get_host_name()
    useragent = web.get_user_agent()
    tz = web.get_request_param('_tz')

    session_info = {
        'sid': sid,
        'uid': uid,
        'time': now,
        'tz': tz,
        'addr': addr,
        'host': host,
        'ua': useragent,
        'c_time': now,
        'c_tz': tz,
        'c_addr': addr,
        'c_host': host,
        'c_ua': useragent,
        'is_guest': is_guest
    }

    return session_info

#----------------------------------------------------------
# Append session info to session file
#----------------------------------------------------------
def append_session_info_to_session_file(uid, session_info):
    sessions = get_user_sessions(uid)

    if sessions is None:
        sessions = {}

    if len(sessions) >= MAX_SESSIONS_PER_USER:
        sessions = _trim_sessions(sessions, MAX_SESSIONS_PER_USER - 1)

    sid = session_info['sid']
    sessions[sid] = session_info
    save_user_sessions(uid, sessions)

def _trim_sessions(sessions, num_of_sessions):
    time_list = []
    for sid in sessions:
        session = sessions[sid]
        t = session['time']
        time_list.append(t)

    time_list.sort(reverse=True)

    trimmed_sessions = {}
    for sid in sessions:
        session = sessions[sid]
        t = session['time']
        if _in_top_n(time_list, num_of_sessions, t):
            trimmed_sessions[sid] = session
        else:
            write_logout_log(session, 'EXCEED_MAX')

    return trimmed_sessions

def _in_top_n(v_list, n, v):
    if n > len(v_list):
        n = len(v_list)
    for i in range(n):
        if v == v_list[i]:
            return True
    return False

#----------------------------------------------------------
# Generate session id
#----------------------------------------------------------
def generate_session_id(uid):
    if uid is None:
        uid = util.random_string()
    now = util.get_timestamp()
    input = str(now) + uid
    sid = util.hash(input, ALGOTRITHM)
    return sid

#----------------------------------------------------------
# Update last access info
#----------------------------------------------------------
def update_last_access_info(uid, sid):
    now = util.get_timestamp()
    addr = web.get_ip_addr()
    host = web.get_host_name()
    useragent = web.get_user_agent()
    tz = web.get_request_param('_tz')
    session = update_session_info_in_session_file(uid, sid, now, addr, host, useragent, tz)
    return session

#----------------------------------------------------------
# Update session info
#----------------------------------------------------------
def update_session_info_in_session_file(uid, sid, time, addr=None, host=None, ua=None, tz=None):
    sessions = get_user_sessions(uid)

    if sessions is None:
        return None

    if not sid in sessions:
        return None

    session = sessions[sid]
    uid = session['uid']

    prev_time = session['time']
    session['time'] = time

    if tz is not None:
        session['tz'] = tz

    if addr is not None:
        session['addr'] = addr

    if host is not None:
        session['host'] = host

    if ua is not None:
        session['ua'] = ua

    elapsed = time - prev_time
    if elapsed > MIN_FILE_UPDATE_INTERVAL_SEC:
        save_user_sessions(uid, sessions)
        usermgr.update_user_status_info(uid, 'last_access', time)
        write_user_timeline_log(uid, sid, time)

    return session

#------------------------------------------------------------------------------
def get_user_timeline_log_file_path(uid):
    return  USER_ROOT_PATH + '/' + uid + '/timeline.log'

def get_user_timeline_log(uid):
    logs = load_user_timeline_log(uid)
    return logs

def load_user_timeline_log(uid):
    path = get_user_timeline_log_file_path(uid)
    logs = util.read_text_file_as_list(path)
    return logs

def write_user_timeline_log(uid, sid, time, info=None):
    TIME_SLOT_MIN = 15
    MAX_LOG_LINES = 1000
    logs = load_user_timeline_log(uid)

    rb = util.RingBuffer(MAX_LOG_LINES)
    for i in range(len(logs)):
        rb.add(logs[i])

    time_slot_sec = TIME_SLOT_MIN * 60

    for i in range(rb.size):
        line = rb.get_reversed(i)
        values = get_timeline_log_field_values(line)

        if values['sid'] == sid:
            log_time = values['time']
            log_time_slot_sec = int(log_time / time_slot_sec) * time_slot_sec
            elapsed_from_latest = time - log_time_slot_sec
            if elapsed_from_latest <= time_slot_sec:
                return

    text = str(time) + '\t' + sid
    if info is not None:
        text += '\t' + info
    rb.add(text)

    logs = rb.get_all()
    path = get_user_timeline_log_file_path(uid)
    util.write_text_file_from_list(path, logs)

def get_timeline_log_field_values(line):
    values = {'time': 0, 'sid': '', 'info': None}
    try:
        wk = line.split('\t')
        values['time'] = float(wk[0])
        values['sid'] = wk[1]
        if len(wk) >= 3:
            values['info'] = wk[2]
    except:
        pass
    return values

#----------------------------------------------------------
# Clear session
#----------------------------------------------------------
def clear_session(sid, renew=False):
    session = get_session_info(sid)
    if session is None:
        return None

    uid = session['uid']

    user_sessions = get_user_sessions(uid)

    if user_sessions is not None:
        session = user_sessions.pop(sid, None)
        status = 'RENEW' if renew else 'OK'
        write_logout_log(session, status)
        save_user_sessions(uid, user_sessions)

    if get_current_session_id() == sid:
        set_current_session_info_to_global(None)

    return session

#----------------------------------------------------------
def write_logout_log(session, status='OK'):
    uid = session['uid']
    sid = session['sid']
    addr = '-'
    host = '-'
    ua = ''

    if 'ua' in session:
        ua = session['ua']

    if status == 'OK':
        addr = session['addr']
        host = session['host']

    logger.write_status_log('LOGOUT', status, uid, addr, host, ua, sid)

#----------------------------------------------------------
# Clear expired sessions
#----------------------------------------------------------
def clear_all_expired_sessions():
    now = util.get_timestamp()
    user_dirs = util.list_dirs(USER_ROOT_PATH)
    for i in range(len(user_dirs)):
        uid = user_dirs[i]
        try:
            user_sessions = get_user_sessions(uid)
            clear_expired_sessions(uid, user_sessions, now)
        except:
            pass

def clear_expired_sessions(uid, sessions, now):
    if sessions is None:
        return

    new_sessions = {}
    cleared = False

    for sid in sessions:
        session = sessions[sid]
        try:
            last_access_time = session['time']
            if round(now - last_access_time) <= SESSION_TIMEOUT_SEC:
                new_sessions[sid] = session
            else:
                cleared = True
                write_logout_log(session, 'EXPIRED')
        except:
            pass

    if cleared:
        save_user_sessions(uid, new_sessions)

#----------------------------------------------------------
# Clear user sessions
#----------------------------------------------------------
def clear_user_sessions(uid):
    user_sessions = get_user_sessions(uid)
    if user_sessions is None:
        return 0
    count =  len(user_sessions)
    save_user_sessions(uid, {})
    return count

#----------------------------------------------------------
# Load sessions info
#----------------------------------------------------------
def load_all_session_info_from_file():
    user_dirs = util.list_dirs(USER_ROOT_PATH)
    sessions = {}
    for i in range(len(user_dirs)):
        uid = user_dirs[i]
        try:
            user_sessions = get_user_sessions(uid)
            for sid in user_sessions:
                session = user_sessions[sid]
                sessions[sid] = session
        except:
            pass
    return sessions

#----------------------------------------------------------
# Save sessions info
#----------------------------------------------------------
def save_user_sessions(uid, sessions):
    path = get_sessions_file_path(uid)
    if len(sessions) == 0:
        now = util.get_timestamp()
        util.delete_file(path)
        usermgr.update_user_status_info(uid, 'last_logout', now)
    else:
        common.save_to_tsv_file(path, sessions, SESSION_DATA_STRUCT)
