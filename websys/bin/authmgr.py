#==============================================================================
# Auth Manager
# Copyright (c) 2020 Takashi Harano
#==============================================================================
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import websysconf
import websys

sys.path.append(websysconf.UTIL_PATH)
import util

import logger
import sessionmgr
import usermgr

ALGOTRITHM = websysconf.ALGOTRITHM

#----------------------------------------------------------
# login
#  uid
#  pw: SHA-256(pw + uid)
#----------------------------------------------------------
def login(uid, pw, ext_auth=False):
    if websys.synchronize_start():
        try:
            ret = do_login(uid, pw, ext_auth=ext_auth)
            websys.synchronize_end()
        except Exception as e:
            websys.synchronize_end()
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
    sessionmgr.set_current_session_info_to_global(session_info)

    status = 'OK'
    user_info = login_info['user_info']
    flags = user_info['flags']
    if flags & usermgr.U_FLG_NEED_PW_CHANGE:
        status = 'NEED_PWD_CHG'

    login_info['status'] = status

    write_login_log(status, uid, session_info)
    return login_info

def _login(uid, pw, ext_auth=False):
    user_info = usermgr.get_user_info(uid, guest=False)
    if user_info is None:
        try:
            return _guest_login(uid, ext_auth)
        except Exception as e:
            raise e

    if usermgr.is_disabled(user_info):
        raise Exception('DISABLED')

    LOGIN_FAILURE_MAX = websysconf.LOGIN_FAILURE_MAX
    LOGIN_LOCK_PERIOD_SEC = websysconf.LOGIN_LOCK_PERIOD_SEC
    now = util.get_timestamp()
    user_status_info = usermgr.load_user_status_info(uid)

    if LOGIN_FAILURE_MAX > 0 and user_status_info['login_failed_count'] >= LOGIN_FAILURE_MAX:
        diff_t = now - user_status_info['login_failed_time']
        if LOGIN_LOCK_PERIOD_SEC == 0 or diff_t <= LOGIN_LOCK_PERIOD_SEC:
            raise Exception('LOCKED')
        else:
            user_status_info['login_failed_count'] = 0
            user_status_info['login_failed_time'] = 0

    if usermgr.is_expired(user_info, now):
        raise Exception('EXPIRED')

    user_pw = usermgr.get_user_password(uid)
    pw2 = util.hash(pw, ALGOTRITHM)
    if pw2 != user_pw:
        user_status_info['login_failed_count'] += 1
        user_status_info['login_failed_time'] = now
        usermgr.write_user_status_info(uid, user_status_info)
        raise Exception('NG')

    new_session_info = sessionmgr.create_and_register_session_info(uid, is_guest=False, ext_auth=ext_auth)
    loggedin_user_info = user_info
    login_info = {
        'session_info': new_session_info,
        'user_info': loggedin_user_info
    }

    user_status_info['last_access'] = now
    user_status_info['last_login'] = now
    user_status_info['login_failed_count'] = 0
    user_status_info['login_failed_time'] = 0
    usermgr.write_user_status_info(uid, user_status_info)

    sid = new_session_info['sid']
    sessionmgr.write_user_timeline_log(uid, sid, now, 'LOGIN')

    return login_info

# guest login
def _guest_login(uid, ext_auth=False):
    user_info = usermgr.get_guest_user_info(uid)
    if user_info is None:
        raise Exception('USER_NOT_FOUND')

    if 'expires_at' in user_info:
        now = util.get_timestamp()
        if user_info['expires_at'] < now:
            raise Exception('EXPIRED')

    new_session_info = sessionmgr.create_and_register_session_info(uid, is_guest=True, ext_auth=ext_auth)
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
def logout(sid, renew=False):
    session = None
    if websys.synchronize_start():
        session = sessionmgr.clear_session(sid, renew)
        websys.synchronize_end()
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
    session_info = sessionmgr.get_current_session_info_from_global()
    if session_info is None:
        return 'SESSION_INFO_NOT_FOUND'

    if 'ext_user' in session_info and session_info['ext_user']:
        return 'OK'

    sid = session_info['sid']
    user_info = sessionmgr.get_user_info_from_sid(sid)
    if user_info is None:
        return 'USER_INFO_NOT_FOUND'

    if usermgr.is_disabled(user_info):
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

    addr = websys.get_ip_addr()
    host = websys.get_host_name()
    ua = websys.get_user_agent()

    logger.write_status_log('LOGIN', status, uid, addr, host, ua, sid)
