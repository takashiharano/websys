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
import userman
import web

SESSION_LIST_FILE_PATH = websysconf.SESSION_LIST_FILE_PATH
SESSION_TIMEOUT_SEC = websysconf.SESSION_TIMEOUT_SEC
ALGOTRITHM = websysconf.ALGOTRITHM

current_session_info = None

#----------------------------------------------------------
# Get all sessions info
#----------------------------------------------------------
def get_all_sessions_info():
    return load_sessions_info_from_file()

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
    sessions = get_all_sessions_info()
    if sessions is not None:
        if sid in sessions:
            session = sessions[sid]
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
    user_info = userman.get_user_info(uid, guest=True)

    return user_info

#----------------------------------------------------------
# Get session info list for the user
#----------------------------------------------------------
def get_session_info_list_for_uid(uid):
    session_list = []
    sessions = get_all_sessions_info()
    if sessions is not None:
        for sid in sessions:
            session = sessions[sid]
            if session['uid'] == uid:
                session_list.append(session)
    return session_list

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
    sid = new_session_info['sid']
    append_session_info_to_session_file(sid, new_session_info)
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
def append_session_info_to_session_file(sid, session_info):
    sessions = get_all_sessions_info()

    if sessions is None:
        sessions = {}

    sessions[sid] = session_info
    save_sessions_info_to_file(sessions)

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
def update_last_accessed_info(sessions, sid):
    now = util.get_timestamp()
    addr = web.get_ip_addr()
    host = web.get_host_name()
    useragent = web.get_user_agent()
    tz = web.get_request_param('_tz')
    update_session_info_in_session_file(sessions, sid, now, addr, host, useragent, tz)

#----------------------------------------------------------
# Update session info
#----------------------------------------------------------
def update_session_info_in_session_file(sessions, sid, time=None, addr=None, host=None, ua=None, tz=None):
    if sessions is None:
        return

    if not sid in sessions:
        return

    session = sessions[sid]
    last_accessed = session['last_accessed']
    if time is not None:
        last_accessed['time'] = time
    if tz is not None:
        last_accessed['tz'] = tz
    if addr is not None:
        last_accessed['addr'] = addr
    if host is not None:
        last_accessed['host'] = host
    if ua is not None:
        last_accessed['ua'] = ua

    save_sessions_info_to_file(sessions)

#----------------------------------------------------------
# Clear session
#----------------------------------------------------------
def clear_session(sid):
    if sid is None:
        return None

    session = None
    sessions = get_all_sessions_info()

    if sessions is not None:
        session = sessions.pop(sid, None)
        write_logout_log(session)
        save_sessions_info_to_file(sessions)

    if get_current_session_id() == sid:
        set_current_session_info_to_global(None)

    return session

#----------------------------------------------------------
def write_logout_log(session, expire=False):
    status = 'OK'
    uid = session['uid']
    if expire:
        status = 'EXPIRED'
    la_info = session['last_accessed']
    addr = la_info['addr']
    host = la_info['host']
    ua = la_info['ua']
    sid = session['sid']
    logger.write_status_log('LOGOUT', status, uid, addr, host, ua, sid)

#----------------------------------------------------------
# Clear expired sessions
#----------------------------------------------------------
def clear_expired_sessions(sessions, save=False):
  now = util.get_timestamp()
  new_sessions = {}
  try:
      for sid in sessions:
          session = sessions[sid]
          last_access_time = session['last_accessed']['time']
          if round(now - last_access_time) <= SESSION_TIMEOUT_SEC:
              new_sessions[sid] = session
          else:
              write_logout_log(session, True)
  except:
      pass

  if save:
      save_sessions_info_to_file(new_sessions)

  return new_sessions

#----------------------------------------------------------
# Clear user sessions
#----------------------------------------------------------
def clear_user_sessions(uid):
    user_sessions = get_session_info_list_for_uid(uid)
    i = 0
    for session in user_sessions:
        sid = session['sid']
        clear_session(sid)
        i = i + 1
    return i

#----------------------------------------------------------
# Load sessions info
#----------------------------------------------------------
def load_sessions_info_from_file():
    try:
        info = util.load_dict(SESSION_LIST_FILE_PATH)
    except:
        info = None
    return info

#----------------------------------------------------------
# Save sessions info
#----------------------------------------------------------
def save_sessions_info_to_file(sessions):
    util.save_dict(SESSION_LIST_FILE_PATH, sessions)
