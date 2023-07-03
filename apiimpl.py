#==============================================================================
# Web System API Implementations
# Copyright (c) 2020 Takashi Harano
#==============================================================================
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../libs'))
import util

util.append_system_path(__file__, './bin')
import websysconf
import userman
import sessionman
import authman
import web

#----------------------------------------------------------
# login
# ?id=ID&pw=HASH(SHA-256(pw + uid))
#----------------------------------------------------------
def cmd_login(context):
    id = web.get_request_param('id')
    pw = web.get_request_param('pw')
    p_ext_auth = web.get_request_param('ext_auth')
    ext_auth = True if p_ext_auth == 'true' else False

    userman.delete_expired_guest()

    if not ext_auth:
        current_sid = web.get_session_id(context)
        if current_sid is not None:
            authman.logout(current_sid)

    try:
        login_info = authman.login(id, pw, ext_auth)
        session_info = login_info['session_info']
        user_info = login_info['user_info']
        sid = session_info['sid']
        status = 'OK'
        body = {
            'sid': sid
        }
        for key in user_info:
            body[key] = user_info[key]

    except Exception as e:
        status = str(e)
        body = None
        util.sleep(0.5)

    web.send_result_json(status, body=body)

#----------------------------------------------------------
# loginlog
#----------------------------------------------------------
def cmd_loginlog(context):
    status = 'OK'
    if web.is_admin(context):
        p_n = web.get_request_param('n')
        n = 30
        if p_n is not None:
            try:
                n = int(p_n)
            except:
                pass
        n = n * (-1)
        login_log = authman.get_login_log()[n:]
    else:
        status = 'NO_PRIVILEGE'
        login_log = None

    web.send_result_json(status, body=login_log)

#----------------------------------------------------------
# logout
# ?sid=SID (prior)
# ?uid=UID
#----------------------------------------------------------
def cmd_logout(context):
    p_sid = web.get_request_param('sid')
    if p_sid is None:
        p_uid = web.get_request_param('uid')
    else:
        p_uid = None

    status = 'OK'
    current_sid = web.get_session_id(context)

    target_sid = None
    if p_sid is None and p_uid is None:
        target_sid = current_sid
    elif p_sid is not None:
        target_sid = p_sid

    self_logout = False
    try:
        if web.get_request_param('all') == 'true':
            self_logout = all_logout(context, current_sid)
        elif target_sid is not None:
            # current session or specified sid
            self_logout = logout_by_sid(context, current_sid, target_sid)
        elif p_uid is not None:
            # all sessions of the user
            self_logout = logout_by_uid(context, p_uid)
    except Exception as e:
        status = str(e)

    if p_sid is None and p_uid is None:
        self_logout = True

    headers = None
    if self_logout:
        headers = web.build_logout_cookies()

    web.send_result_json(status, body=None, http_headers=headers)

# Logout by SID
def logout_by_sid(context, current_sid, sid):
    self_logout = False
    if not web.is_admin(context):
        current_uid = web.get_user_id(context)
        target_session_info = sessionman.get_session_info(sid)
        if target_session_info is None:
            return False
        elif target_session_info['uid'] != current_uid:
            raise Exception('FORBIDDEN')

    cleared_session = authman.logout(sid)
    if cleared_session is None:
        raise Exception('SESSION_NOT_FOUND')

    if sid == current_sid:
        self_logout = True
    return self_logout

# Logout by UID
def logout_by_uid(context, uid):
    self_logout = False
    current_uid = web.get_user_id(context)
    if uid == current_uid:
        self_logout = True
    else:
        if not web.is_admin(context):
            raise Exception('FORBIDDEN')

    i = sessionman.clear_user_sessions(uid)
    if i == 0:
        raise Exception('NOT_LOGGED_IN')

    return self_logout

# ALL Logout
def all_logout(context, current_sid, self_logout=False):
    if not web.is_admin(context):
        raise Exception('FORBIDDEN')

    sessions = sessionman.get_all_sessions_info()
    for sid in sessions:
        if self_logout or sid != current_sid:
            logout_by_sid(context, current_sid, sid)

    return self_logout

#----------------------------------------------------------
# auth
#----------------------------------------------------------
def cmd_auth(context):
    status = 'FORBIDDEN'
    if authman.auth():
        status = 'OK'
    web.send_result_json(status, body=None)

#----------------------------------------------------------
# session
#----------------------------------------------------------
def cmd_session(context):
    status = 'OK'
    session_info = web.get_session_info(context)
    p_userinfo = web.get_request_param('userinfo')

    if session_info is not None and p_userinfo == 'true':
        user_info = web.get_user_info(context)
        session_info['userinfo'] = user_info

    web.send_result_json(status, body=session_info)

#----------------------------------------------------------
# sessions
#----------------------------------------------------------
def cmd_sessions(context):
    status = 'OK'
    all = web.get_request_param('all')
    if all is None:
        session_list = get_session_list_from_session(context)
    else:
        if web.is_admin(context):
            session_list = []
            sessions = sessionman.get_all_sessions_info()
            for sid in sessions:
                session_list.append(sessions[sid])
        else:
            session_list = get_session_list_from_session(context)
    web.send_result_json(status, body=session_list)

#----------------------------------------------------------
# user
# uid=UID
#----------------------------------------------------------
def cmd_user(context):
    status = 'OK'
    user_info = None
    uid = web.get_request_param('uid')

    if uid is None:
        sid = web.get_session_id(context)
        if sid is None:
            status = 'NOT_LOGGED_IN'
        else:
            user_info = web.get_user_info(context)
    else:
      current_uid = web.get_user_id(context)
      if current_uid is None:
          status = 'FORBIDDEN'
      else:
          if uid == current_uid:
              user_info = userman.get_user_info(uid)
          else:
              if web.is_admin(context):
                  user_info = userman.get_user_info(uid)
                  if user_info is None:
                      status = 'NG'
              else:
                  status = 'FORBIDDEN'

    web.send_result_json(status, body=user_info)

#----------------------------------------------------------
# users
#----------------------------------------------------------
def cmd_users(context):
    if not authman.auth():
        on_auth_error()
        return

    if web.is_admin(context):
        status = 'OK'
        user_list = userman.get_all_user_info()
        guest_user_list = userman.get_all_guest_user_info()
        if guest_user_list is not None:
            user_list.update(guest_user_list)
    else:
        status = 'FORBIDDEN'
        user_list = None

    web.send_result_json(status, body=user_list)

#----------------------------------------------------------
# add a user
#----------------------------------------------------------
def cmd_useradd(context):
    if not authman.auth():
        on_auth_error()
        return

    status = 'ERROR'
    if not web.is_admin(context):
        web.send_result_json('FORBIDDEN', body=None)
        return

    uid = web.get_request_param('uid')
    name = web.get_request_param('name')
    name_l = web.get_request_param('name_l')
    pw = web.get_request_param('pw')
    p_st = web.get_request_param('st')

    if uid is None:
        web.send_result_json('ERR_UID', body=None)
        return

    if pw is None:
        web.send_result_json('ERR_PW', body=None)
        return

    if name is None:
        name = uid

    if name_l is None:
        name_l = name

    p_group = web.get_request_param('group', '')
    group = ''
    if p_group is not None:
        group = p_group
        group = util.replace(group, '\s{2,}', ' ')
        group = group.strip()

    p_privs = web.get_request_param('privs')
    privs = ''
    if p_privs is not None:
        privs = p_privs
        privs = util.replace(privs, '\s{2,}', ' ')
        privs = privs.strip()

    p_admin = web.get_request_param('admin')
    is_admin = False
    if p_admin is not None:
        is_admin = p_admin == 'true'

    if p_st is None:
        p_st = '0'

    pw_hash = util.hash(pw, websysconf.ALGOTRITHM)
    u_status = p_st

    try:
        userman.create_user(uid, pw_hash, name=name, name_l=name_l, is_admin=is_admin, group=group, privs=privs, status=u_status)
        status = 'OK'
    except Exception as e:
        status = 'ERR_' + str(e)

    web.send_result_json(status, body=None)

#----------------------------------------------------------
# mod a user
#----------------------------------------------------------
def cmd_usermod(context):
    if not authman.auth():
        on_auth_error()
        return

    uid = web.get_request_param('uid')

    if not web.is_admin(context):
        user_info = web.get_user_info(context)
        if uid != user_info['uid']:
            web.send_result_json('FORBIDDEN', body=None)
            return

    if uid is None:
        web.send_result_json('ERR_UID', body=None)
        return

    name = web.get_request_param('name')
    name_l = web.get_request_param('name_l')

    pw = web.get_request_param('pw')
    pw_hash = None
    if pw is not None:
        pw_hash = util.hash(pw, websysconf.ALGOTRITHM)

    group = None
    agroup = None
    rgroup = None
    privs = None
    aprivs = None
    rprivs = None
    is_admin = None
    u_status = None

    if web.is_admin(context):
        p_group = web.get_request_param('group')
        if p_group is not None:
            group = p_group.strip()
            group = util.replace(group, '\s{2,}', ' ')
            group = p_group.split(' ')
            if len(group) == 1 and group[0] == '':
                group = []

        agroup = _get_optional_param_by_list('agroup')
        rgroup = _get_optional_param_by_list('rgroup')

        p_privs = web.get_request_param('privs')
        if p_privs is not None:
            privs = p_privs
            privs = util.replace(privs, '\s{2,}', ' ')
            privs = privs.strip()

        aprivs = _get_optional_param_by_list('aprivs')
        rprivs = _get_optional_param_by_list('rprivs')

        p_admin = web.get_request_param('admin')
        if p_admin is not None:
            is_admin = p_admin == 'true'

        p_st = web.get_request_param('st')
        if p_st is not None:
            u_status = p_st

    try:
        userman.modify_user(uid, pw_hash, name=name, name_l=name_l, is_admin=is_admin, group=group, agroup=agroup, rgroup=rgroup, privs=privs, aprivs=aprivs, rprivs=rprivs, status=u_status)
        status = 'OK'
    except Exception as e:
        status = 'ERR_' + str(e)

    web.send_result_json(status, body=None)

def _get_optional_param_by_list(key):
    p_value = web.get_request_param(key)
    param_list = None
    if p_value is not None:
        p_value = p_value.strip()
        p_value = util.replace(p_value, '\s{2,}', ' ')
        param_list = p_value.split(' ')
        if len(param_list) == 1 and param_list[0] == '':
            param_list = None
    return param_list

#----------------------------------------------------------
# gencode
# ?validsec=1800
#----------------------------------------------------------
def cmd_gencode(context):
    if not authman.auth():
        on_auth_error()
        return

    uid = None
    if not web.is_admin(context):
        web.send_result_json('FORBIDDEN', body=None)
        return

    status = 'OK'
    valid_min = 30
    p_valid_time = web.get_request_param('validtime')
    if p_valid_time is not None:
        try:
            valid_min = int(p_valid_time)
        except:
            pass

    id = None
    p_id = web.get_request_param('id')
    if p_id is not None:
        id = p_id

    p_group = web.get_request_param('group')
    group = ''
    if p_group is not None:
        group = p_group
        group = util.replace(group, '\s{2,}', ' ')
        group = group.strip()

    p_privs = web.get_request_param('privs')
    privs = ''
    if p_privs is not None:
        privs = p_privs
        privs = util.replace(privs, '\s{2,}', ' ')
        privs = privs.strip()

    try:
        uid = userman.create_guest(uid=id, valid_min=valid_min, group=group, privs=privs)
    except Exception as e:
        status = str(e)

    web.send_result_json(status, body=uid)

#----------------------------------------------------------
# userdel
# ?uid=UID
#----------------------------------------------------------
def cmd_userdel(context):
    if not authman.auth():
        on_auth_error()
        return

    status = 'ERROR'
    if web.is_admin(context):
        uid = web.get_request_param('uid')
        if uid is None:
            status = 'ERR_NO_UID'
        else:
            if _is_prohibited_uid(uid):
                status = 'ERR_PROHIBITED_UID'
            else:
                status = 'ERR_NO_SUCH_UID'
                deleted = userman.delete_guest_user(uid)
                if deleted:
                    status = 'OK'
                else:
                    deleted = userman.delete_user(uid)
                    if deleted:
                        status = 'OK'

    else:
        status = 'FORBIDDEN'

    web.send_result_json(status, body=None)

def _is_prohibited_uid(uid):
    PROHIBITED_UIDs = ['root']
    for puid in PROHIBITED_UIDs:
        if uid == puid:
            return True
    return False

#----------------------------------------------------------
# guests
#----------------------------------------------------------
def cmd_guests(context):
    userman.delete_expired_guest()

    if not authman.auth():
        on_auth_error()
        return

    if web.is_admin(context):
        status = 'OK'
        guest_user_list = userman.get_all_guest_user_info()

    else:
        status = 'FORBIDDEN'
        guest_user_list = None

    web.send_result_json(status, body=guest_user_list)

#----------------------------------------------------------
# hello
#----------------------------------------------------------
def cmd_hello(context):
    status = 'OK'
    msg = None

    q = web.get_request_param('q')
    if q is None:
        msg = 'Hello, World!'
    else:
        if not authman.auth():
            on_auth_error()
            return

        if web.is_admin(context):
            msg= 'Hello, ' + q
        else:
            msg = 'Hi!'

    web.send_result_json(status, body=msg)

#------------------------------------------------------------------------------
#----------------------------------------------------------
# On auth error
#----------------------------------------------------------
def on_auth_error():
    obj = {'status': 'AUTH_ERROR'}
    web.send_response(obj, 'application/json')

#----------------------------------------------------------
# get user info
#----------------------------------------------------------
def get_session_list_from_session(context):
    uid = web.get_user_id(context)
    session_list = sessionman.get_session_info_list_from_uid(uid)
    return session_list

#----------------------------------------------------------
# main
#----------------------------------------------------------
def main():
    context = web.on_access()
    cmd = web.get_request_param('cmd')

    if cmd is None:
        web.send_result_json('ERR_NO_CMD_SPECIFIED', body=cmd)
        return

    func_name = 'cmd_' + cmd
    g = globals()
    if func_name in g:
        g[func_name](context)
    else:
        web.send_result_json('ERR_CMD_NOT_FOUND', body=cmd)
