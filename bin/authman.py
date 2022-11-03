#==============================================================================
# Auth Manager
# Copyright (c) 2020 Takashi Harano
#==============================================================================
import os
import sys
import time

import config
sys.path.append(config.UTIL_PATH)
import util

import sessionman
import userman
import web

ALGOTRITHM = config.ALGOTRITHM
LOGIN_LOG_PATH = config.LOGIN_LOG_PATH

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
        if status == 'NO_SUCH_USER':
            write_log(status, '')
            status = 'NG'
        else:
            write_log(status, uid)
        raise Exception(status)

    session_info = login_info['session_info']
    sessionman.set_current_session_info(session_info)

    sid = login_info['session_info']['sid']
    write_log('OK', uid, sid)
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

    user_pw = userman.get_user_password(uid)
    pw2 = util.hash(pw, ALGOTRITHM)
    if pw2 != user_pw:
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
        raise Exception('NO_SUCH_USER')

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

# Write Log
def write_log(status, id, sid=''):
    now = util.get_timestamp()
    date_time = util.get_datetime_str(now, fmt='%Y-%m-%dT%H:%M:%S.%f')
    addr = util.get_ip_addr()
    host = util.get_host_name()
    ua = util.get_user_agent()

    data = date_time
    data += '\t'
    data += str(now)
    data += '\t'
    data += status
    data += '\t'
    data += id
    data += '\t'
    data += addr
    data += '\t'
    data += host
    data += '\t'
    data += ua
    data += '\t'
    data += sid

    util.append_line_to_text_file(LOGIN_LOG_PATH, data, max=1000)

#----------------------------------------------------------
# Read login log
#---------------------------------------------------------
def get_login_log():
    return util.read_text_file_as_list(LOGIN_LOG_PATH)

#----------------------------------------------------------
# logout
# return cleared session info
#----------------------------------------------------------
def logout(sid=None):
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
    session_info = sessionman.get_current_session_info()
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
        pattern = util.replace(pattern, '\.', '\\.')
        pattern = util.replace(pattern, '\?', '\\?')
        if not util.match(req_uri, pattern):
            return 'FORBIDDEN_PATH'

    # OK
    return 'OK'
