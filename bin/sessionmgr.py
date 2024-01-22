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
import usermgr
import web

USER_ROOT_PATH = websysconf.USER_ROOT_PATH
SESSION_TIMEOUT_SEC = websysconf.SESSION_TIMEOUT_SEC
MAX_SESSIONS_PER_USER = websysconf.MAX_SESSIONS_PER_USER
ALGOTRITHM = websysconf.ALGOTRITHM

current_session_info = None

#----------------------------------------------------------
# Get all sessions info
#----------------------------------------------------------
def get_all_sessions_info():
    return load_all_session_info_from_file()

def get_user_sessions(uid):
    session_file_path = USER_ROOT_PATH + '/' + uid + '/sessions.json'
    try:
        session_list = util.load_dict(session_file_path)
    except Exception as e:
        logger.write_system_log('ERROR', uid, 'sessionmgr.get_user_sessions(): ' + str(e))
        session_list = None

    return session_list

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
#   "is_guest": False,
#   "last_accessed": {
#    "time": 1234567890.123456,
#    "tz": "+0900",
#    "addr": "::1",
#    "host": "hostname",
#    "ua": "Mozilla/5.0"
#   }
#  }
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

#----------------------------------------------------------
# Create and register new session info
#----------------------------------------------------------
def create_and_register_session_info(uid, is_guest=False, ext_auth=False):
    new_session_info = create_session_info(uid, is_guest)
    if ext_auth:
        new_session_info['ext_auth'] = True
    append_session_info_to_session_file(uid, new_session_info)
    return new_session_info

#----------------------------------------------------------
# Create session info
#----------------------------------------------------------
def create_session_info(uid, is_guest=False):
    now = util.get_timestamp()
    addr = web.get_ip_addr()
    host = web.get_host_name()
    useragent = web.get_user_agent()
    tz = web.get_request_param('_tz')

    sid = generate_session_id(uid)
    new_session = {
        'sid': sid,
        'uid': uid,
        'created_time': now,
        'tz': tz,
        'addr': addr,
        'host': host,
        'ua': useragent,
        'is_guest': is_guest,
        'last_accessed': {
            'time': now,
            'tz': tz,
            'addr': addr,
            'host': host
        }
    }

    return new_session

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
    save_user_sessions_to_file(uid, sessions)

def _trim_sessions(sessions, num_of_sessions):
    time_list = []
    for sid in sessions:
        session = sessions[sid]
        t = session['last_accessed']['time']
        time_list.append(t)

    time_list.sort(reverse=True)

    trimmed_sessions = {}
    for sid in sessions:
        session = sessions[sid]
        t = session['last_accessed']['time']
        if _in_top_n(time_list, num_of_sessions, t):
            trimmed_sessions[sid] = session
        else:
            write_logout_log(session, 'EXCEEDED')

    return trimmed_sessions

def _in_top_n(v_list, n, v):
    if n > len(v_list):
        n = len(v_list)
    for i in range(n):
        if v == v_list[i]:
            return True
    False

#----------------------------------------------------------
# Generate session id
#----------------------------------------------------------
def generate_session_id(uid):
    input = util.get_datetime_str() + uid
    sid = util.hash(input, ALGOTRITHM)
    return sid

#----------------------------------------------------------
# Update last accessed info
#----------------------------------------------------------
def update_last_accessed_info(uid, sid):
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
    last_accessed = session['last_accessed']

    prev_time = last_accessed['time']

    last_accessed['time'] = time
    if tz is not None:
        last_accessed['tz'] = tz
    if addr is not None:
        last_accessed['addr'] = addr
    if host is not None:
        last_accessed['host'] = host
    if ua is not None:
        last_accessed['ua'] = ua

    elapsed = time - prev_time
    if elapsed > 0.5:
        save_user_sessions_to_file(uid, sessions)

        user_status_info = usermgr.load_user_status_info(uid)
        user_status_info['last_accessed'] = time
        usermgr.write_user_status_info(uid, user_status_info)

    return session

#----------------------------------------------------------
# Clear session
#----------------------------------------------------------
def clear_session(sid):
    session = get_session_info(sid)
    if session is None:
        return None

    uid = session['uid']

    user_sessions = get_user_sessions(uid)

    if user_sessions is not None:
        session = user_sessions.pop(sid, None)
        write_logout_log(session)
        save_user_sessions_to_file(uid, user_sessions)

    if get_current_session_id() == sid:
        set_current_session_info_to_global(None)

    return session

#----------------------------------------------------------
def write_logout_log(session, status='OK'):
    uid = session['uid']
    la_info = session['last_accessed']
    addr = '-'
    host = '-'
    ua = la_info['ua']
    sid = session['sid']

    if status == 'OK':
        addr = la_info['addr']
        host = la_info['host']

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
            last_access_time = session['last_accessed']['time']
            if round(now - last_access_time) <= SESSION_TIMEOUT_SEC:
                new_sessions[sid] = session
            else:
                cleared = True
                write_logout_log(session, 'EXPIRED')
        except:
            pass

    if cleared:
        save_user_sessions_to_file(uid, new_sessions)

#----------------------------------------------------------
# Clear user sessions
#----------------------------------------------------------
def clear_user_sessions(uid):
    user_sessions = get_user_sessions(uid)
    if user_sessions is None:
        return 0

    i = 0
    for sid in user_sessions:
        i = i + 1

    save_user_sessions_to_file(uid, {})
    return i

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
def save_user_sessions_to_file(uid, sessions):
    path = USER_ROOT_PATH + '/' + uid + '/sessions.json'
    if len(sessions) == 0:
        util.delete_file(path)
    else:
        util.save_dict(path, sessions)
