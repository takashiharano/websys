#==============================================================================
# Auth Manager
# Copyright 2020 Takashi Harano
# Released under the MIT License
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
def login(uid, pw):
    if websys.synchronize_start():
        try:
            ret = do_login(uid, pw)
            websys.synchronize_end()
        except Exception as e:
            websys.synchronize_end()
            raise Exception(e)
        return ret
    raise Exception('ERROR')

def do_login(uid, pw):
    try:
        login_info = _login(uid, pw)
    except Exception as e:
        status = str(e)
        if status == 'USER_NOT_FOUND':
            write_login_log(status, '')
            status = 'FAILED'
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

def _login(uid, pw):
    user_info = usermgr.get_user_info(uid)
    if user_info is None:
        raise Exception('USER_NOT_FOUND')

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
        raise Exception('FAILED')

    new_session_info = sessionmgr.create_and_register_session_info(uid)
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
def auth():
    status = _auth()
    if status == 'OK':
        return True
    return False

def _auth():
    session_info = sessionmgr.get_current_session_info_from_global()
    if session_info is None:
        return 'SESSION_INFO_NOT_FOUND'

    sid = session_info['sid']
    user_info = sessionmgr.get_user_info_from_sid(sid)
    if user_info is None:
        return 'USER_INFO_NOT_FOUND'

    if usermgr.is_disabled(user_info):
        return 'USER_IS_DISABLED'

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
