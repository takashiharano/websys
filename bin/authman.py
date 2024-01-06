#==============================================================================
# Auth Manager
# Copyright (c) 2020 Takashi Harano
#==============================================================================
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import websysconf

sys.path.append(websysconf.UTIL_PATH)
import util

import logger
import sessionman
import userman
import web

USER_ROOT_PATH = websysconf.USER_ROOT_PATH
ALGOTRITHM = websysconf.ALGOTRITHM

#----------------------------------------------------------
# login
#  uid
#  pw: SHA-256(pw + uid)
#----------------------------------------------------------
def login(uid, pw, ext_auth=False):
    if web.synchronize_start():
        try:
            ret = do_login(uid, pw, ext_auth=ext_auth)
            web.synchronize_end()
        except Exception as e:
            web.synchronize_end()
            raise Exception(e)
        return ret
    raise Exception('ERROR')

def do_login(uid, pw, ext_auth=False):
    try:
        login_info = _login(uid, pw, ext_auth)
    except Exception as e:
        status = str(e)
        if status == 'USER_NOT_FOUND':
            write_login_log(status, '')
            status = 'NG'
        else:
            write_login_log(status, uid)
        raise Exception(status)

    session_info = login_info['session_info']
    sessionman.set_current_session_info_to_global(session_info)

    write_login_log('OK', uid, session_info)
    userman.clear_login_failed(uid)
    return login_info

def _login(uid, pw, ext_auth=False):
    user_info = userman.get_user_info(uid, guest=False)
    if user_info is None:
        try:
            return _guest_login(uid, ext_auth)
        except Exception as e:
            raise e

    if userman.is_disabled(user_info):
        raise Exception('DISABLED')

    LOGIN_FAILURE_MAX = websysconf.LOGIN_FAILURE_MAX
    LOGIN_LOCK_PERIOD_SEC = websysconf.LOGIN_LOCK_PERIOD_SEC
    now = util.get_timestamp()

    login_failed_info = userman.load_login_failed_info(uid)
    if LOGIN_FAILURE_MAX > 0 and login_failed_info['count'] >= LOGIN_FAILURE_MAX:
        diff_t = now - login_failed_info['time']
        if LOGIN_LOCK_PERIOD_SEC == 0 or diff_t <= LOGIN_LOCK_PERIOD_SEC:
            raise Exception('LOCKED')
        else:
            login_failed_info = userman.clear_login_failed(uid)

    user_pw = userman.get_user_password(uid)
    pw2 = util.hash(pw, ALGOTRITHM)
    if pw2 != user_pw:
        login_failed_info['count'] += 1
        login_failed_info['time'] = now
        userman.write_login_failed(uid, login_failed_info)
        raise Exception('NG')

    new_session_info = sessionman.create_and_register_session_info(uid, is_guest=False, ext_auth=ext_auth)
    loggedin_user_info = user_info
    login_info = {
        'session_info': new_session_info,
        'user_info': loggedin_user_info
    }
    return login_info

# guest login
def _guest_login(uid, ext_auth=False):
    user_info = userman.get_guest_user_info(uid)
    if user_info is None:
        raise Exception('USER_NOT_FOUND')

    if 'expires_at' in user_info:
        now = util.get_timestamp()
        if user_info['expires_at'] < now:
            raise Exception('EXPIRED')

    new_session_info = sessionman.create_and_register_session_info(uid, is_guest=True, ext_auth=ext_auth)
    sid = new_session_info['sid']

    login_info = {
        'session_info': new_session_info,
        'user_info': user_info
    }

    return login_info

#----------------------------------------------------------
# logout
# return cleared session info
#----------------------------------------------------------
def logout(sid):
    session = None
    if web.synchronize_start():
        session = sessionman.clear_session(sid)
        web.synchronize_end()
    return session

#----------------------------------------------------------
# auth
#----------------------------------------------------------
def auth(allow_guest=True):
    status = _auth(allow_guest=allow_guest)
    if status == 'OK':
        return True
    return False

def _auth(allow_guest):
    session_info = sessionman.get_current_session_info_from_global()
    if session_info is None:
        return 'SESSION_INFO_NOT_FOUND'

    if 'ext_user' in session_info and session_info['ext_user']:
        return 'OK'

    sid = session_info['sid']
    user_info = sessionman.get_user_info_from_sid(sid)
    if user_info is None:
        return 'USER_INFO_NOT_FOUND'

    if userman.is_disabled(user_info):
        return 'USER_IS_DISABLED'

    if 'expires_at' in user_info:
        now = util.get_timestamp()
        if user_info['expires_at'] < now:
            return 'USER_IS_EXPIRED'

    if not allow_guest and 'guest' in user_info and user_info['is_guest']:
        return 'GUEST_USER_NOT_ALLOWED'

    if 'path' in user_info and user_info['path'] is not None:
        req_uri = util.get_request_uri()
        pattern = '^' + user_info['path']
        pattern = util.replace(pattern, '\\.', '\\\\.')
        pattern = util.replace(pattern, '\\?', '\\\\?')
        if not util.match(req_uri, pattern):
            return 'FORBIDDEN_PATH'

    return 'OK'

#----------------------------------------------------------
# Write Login Log
#----------------------------------------------------------
def write_login_log(status, uid, session_info=None):
    sid = ''
    if session_info is not None:
        sid = session_info['sid']

    addr = web.get_ip_addr()
    host = web.get_host_name()
    ua = web.get_user_agent()

    logger.write_status_log('LOGIN', status, uid, addr, host, ua, sid)
