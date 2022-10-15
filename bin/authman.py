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
LOCK_FILE_PATH = config.LOCK_FILE_PATH

#----------------------------------------------------------
# login
#  uid
#  pw: SHA-256(pw + uid)
#----------------------------------------------------------
def login(uid, pw, ext_auth=False):
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

    if user_info['disabled']:
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

    if 'expire' in user_info:
        now = util.get_timestamp()
        if user_info['expire'] < now:
            raise Exception('EXPIRED')

    new_session_info = sessionman.create_and_register_session_info(uid, is_guest=True, ext_auth=ext_auth)
    sid = new_session_info['sid']
    sessionman.set_current_session_id(sid)

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
    return sessionman.clear_session(sid)

#----------------------------------------------------------
# auth
#----------------------------------------------------------
def auth(default=False, roles=None, allow_guest=False):
    for i in range(3):
        if util.file_lock(LOCK_FILE_PATH):
            status = _auth(default=default, roles=roles, allow_guest=allow_guest)
            util.file_unlock(LOCK_FILE_PATH)
            if status == 'OK':
                return True
            return False
        else:
            time.sleep(1)

def _auth(default=False, roles=None, allow_guest=False):
    session_info = sessionman.get_current_session_info()
    if session_info is None:
        if default:
            _on_auth_error()
        return 'SESSION_INFO_NOT_FOUND'

    if 'ext_user' in session_info and session_info['ext_user']:
        return 'OK'

    sid = session_info['sid']
    user_info = sessionman.get_user_info_from_sid(sid)
    if user_info is None:
        if default:
            _on_auth_error()
        return 'USER_INFO_NOT_FOUND'

    if user_info['disabled']:
        if default:
            _on_auth_error()
        return 'USER_IS_DISABLED'

    if 'expire' in user_info:
        now = util.get_timestamp()
        if user_info['expire'] < now:
            if default:
                _on_auth_error()
            return 'USER_IS_EXPIRED'

    if not allow_guest and 'guest' in user_info['attr']:
        if default:
            _on_auth_error()
        return 'GUEST_USER_NOT_ALLOWED'

    if 'path' in user_info and user_info['path'] is not None:
        req_uri = util.get_request_uri()
        pattern = '^' + user_info['path']
        pattern = util.replace(pattern, '\.', '\\.')
        pattern = util.replace(pattern, '\?', '\\?')
        if not util.match(req_uri, pattern):
            if default:
                _on_auth_error()
            return 'FORBIDDEN_PATH'

    if roles is not None:
        if userman.has_attr(user_info, 'system'):
            # OK
            return 'OK'

        for role_name in roles:
            if userman.has_role(user_info, role_name):
                # OK
                return 'OK'

        # No role
        return 'NO_ROLE'

    # OK
    return 'OK'

def _on_auth_error():
    cookie = util.build_cookie_clear('sid', '/')
    headers = [
        {'Set-Cookie': cookie}
    ]
    result = {'status': 'AUTH_ERROR'}
    web._send_response('json', result, headers=headers);

#----------------------------------------------------------
# is logged in
#----------------------------------------------------------
def is_logged_in():
    return sessionman.get_current_session_id() is not None

#----------------------------------------------------------
# has role
# uid is None = current user
#----------------------------------------------------------
def has_role(role_name, uid=None):
    if uid is None:
        uid = sessionman.get_current_user_id()

    user_info = userman.get_user_info(uid)
    if user_info is not None:
        if 'system' in user_info['attr']:
            return True
        role_list = user_info['roles']
        return _has_role(role_list, role_name)
    return False

def _has_role(role_list, role_name):
    for item in role_list:
        if item == role_name:
            return True
    return False
