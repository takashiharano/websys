#==============================================================================
# Web System API Implementations
# Copyright (c) 2020 Takashi Harano
#==============================================================================
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../libs'))
import util

util.append_system_path(__file__, './bin')
import logger
import websysconf
import userman
import groupman
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
        current_sid = context.get_session_id()
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
# syslog
#----------------------------------------------------------
def cmd_syslog(context):
    status = 'OK'
    if context.is_admin():
        p_n = web.get_request_param('n')
        n = 30
        if p_n is not None:
            try:
                n = int(p_n)
            except:
                pass
        n = n * (-1)
        log_list = logger.get_system_log()[n:]
    else:
        status = 'NO_PRIVILEGE'
        log_list = None

    web.send_result_json(status, body=log_list)

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
    current_sid = context.get_session_id()

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

    cb_url = web.get_request_param('url')
    res_body = {
        'url': cb_url
    }
    web.send_result_json(status, body=res_body, http_headers=headers)

# Logout by SID
def logout_by_sid(context, current_sid, sid):
    self_logout = False
    if not context.is_admin():
        current_uid = context.get_user_id()
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
    current_uid = context.get_user_id()
    if uid == current_uid:
        self_logout = True
    else:
        if not context.is_admin():
            raise Exception('FORBIDDEN')

    i = sessionman.clear_user_sessions(uid)
    if i == 0:
        raise Exception('NOT_LOGGED_IN')

    return self_logout

# ALL Logout
def all_logout(context, current_sid, self_logout=False):
    if not context.is_admin():
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
    session_info = context.get_session_info()
    p_userinfo = web.get_request_param('userinfo')

    if session_info is not None and p_userinfo == 'true':
        user_info = context.get_user_info()
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
        if context.is_admin():
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
        sid = context.get_session_id()
        if sid is None:
            status = 'NOT_LOGGED_IN'
        else:
            user_info = context.get_user_info()
    else:
      current_uid = context.get_user_id()
      if current_uid is None:
          status = 'FORBIDDEN'
      else:
          if uid == current_uid:
              user_info = userman.get_user_info(uid)
          else:
              if context.is_admin():
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

    if context.is_admin():
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
    if not context.is_admin():
        web.send_result_json('FORBIDDEN', body=None)
        return

    uid = web.get_request_param('uid')
    name = web.get_request_param('name')
    local_name = web.get_request_param('local_name')
    pw = web.get_request_param('pw')
    p_admin = web.get_request_param('admin')
    p_group = web.get_request_param('group', '')
    p_privs = web.get_request_param('privs')
    desc = web.get_request_param('desc', '')
    p_st = web.get_request_param('st')

    if uid is None:
        web.send_result_json('ERR_UID', body=None)
        return

    if pw is None:
        web.send_result_json('ERR_PW', body=None)
        return
    pw_hash = util.hash(pw, websysconf.ALGOTRITHM)

    if name is None:
        name = uid

    if local_name is None:
        local_name = name

    is_admin = False
    if p_admin is not None:
        is_admin = p_admin == 'true'

    group = ''
    if p_group is not None:
        group = p_group
        group = util.replace(group, '\s{2,}', ' ')
        group = group.strip()

    privs = ''
    if p_privs is not None:
        privs = p_privs
        privs = util.replace(privs, '\s{2,}', ' ')
        privs = privs.strip()

    if p_st == '':
        p_st = None

    try:
        userman.create_user(uid, pw_hash, name=name, local_name=local_name, is_admin=is_admin, group=group, privs=privs, desc=desc, status=p_st)
        logger.write_event_log(context, 'ADD_USER', 'OK', 'target=' + uid)
        status = 'OK'
    except Exception as e:
        status = 'ERR:' + str(e)

    web.send_result_json(status, body=None)

#----------------------------------------------------------
# mod a user
#----------------------------------------------------------
def cmd_usermod(context):
    if not authman.auth():
        on_auth_error()
        return

    uid = web.get_request_param('uid')

    if not context.is_admin():
        user_info = context.get_user_info()
        if uid != user_info['uid']:
            web.send_result_json('FORBIDDEN', body=None)
            return

    if uid is None:
        web.send_result_json('ERR_UID', body=None)
        return

    name = web.get_request_param('name')
    local_name = web.get_request_param('local_name')

    pw = web.get_request_param('pw')
    pw_hash = None
    if pw is not None:
        pw_hash = util.hash(pw, websysconf.ALGOTRITHM)

    is_admin = None
    group = None
    agroup = None
    rgroup = None
    privs = None
    aprivs = None
    rprivs = None
    desc = None
    u_status = None

    if context.is_admin():
        p_admin = web.get_request_param('admin')
        if p_admin is not None:
            is_admin = p_admin == 'true'

        p_group = web.get_request_param('group')
        if p_group is not None:
            group = p_group
            group = util.replace(group, '\s{2,}', ' ')
            group = group.strip()

        agroup = _get_optional_param_by_list('agroup')
        rgroup = _get_optional_param_by_list('rgroup')

        p_privs = web.get_request_param('privs')
        if p_privs is not None:
            privs = p_privs
            privs = util.replace(privs, '\s{2,}', ' ')
            privs = privs.strip()

        aprivs = _get_optional_param_by_list('aprivs')
        rprivs = _get_optional_param_by_list('rprivs')

        desc = web.get_request_param('desc', '')

        p_st = web.get_request_param('st')
        if p_st is not None:
            u_status = p_st

    try:
        userman.modify_user(uid, pw_hash, name=name, local_name=local_name, is_admin=is_admin, group=group, agroup=agroup, rgroup=rgroup, privs=privs, aprivs=aprivs, rprivs=rprivs, desc=desc, status=u_status)
        logger.write_event_log(context, 'MOD_USER', 'OK', 'target=' + uid)
        status = 'OK'
    except Exception as e:
        status = 'ERR:' + str(e)

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
# Change password
#----------------------------------------------------------
def cmd_passwd(context):
    if not authman.auth():
        on_auth_error()
        return

    uid = web.get_request_param('uid')

    if not context.is_admin():
        user_info = context.get_user_info()
        if uid != user_info['uid']:
            web.send_result_json('FORBIDDEN', body=None)
            return

    if uid is None:
        web.send_result_json('ERR_UID', body=None)
        return

    pw = web.get_request_param('pw')
    pw_hash = None
    if pw is not None:
        pw_hash = util.hash(pw, websysconf.ALGOTRITHM)

    try:
        userman.modify_user(uid, pw_hash)
        status = 'OK'
        logger.write_event_log(context, 'CHG_PW', 'OK', 'target=' + uid)
    except Exception as e:
        status = 'ERR_' + str(e)

    web.send_result_json(status, body=None)

#----------------------------------------------------------
# gencode
# ?validsec=1800
#----------------------------------------------------------
def cmd_gencode(context):
    if not authman.auth():
        on_auth_error()
        return

    uid = None
    if not context.is_admin():
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
    if context.is_admin():
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
                        logger.write_event_log(context, 'DEL_USER', 'OK', 'target=' + uid)
                        status = 'OK'

    else:
        status = 'FORBIDDEN'

    web.send_result_json(status, body=None)

def _is_prohibited_uid(uid):
    PROHIBITED_UIDS = ['root']
    for puid in PROHIBITED_UIDS:
        if uid == puid:
            return True
    return False

#----------------------------------------------------------
# unlockuser
#----------------------------------------------------------
# ?uid=UID
#----------------------------------------------------------
def cmd_unlockuser(context):
    if not authman.auth():
        on_auth_error()
        return

    status = 'ERROR'
    if context.is_admin():
        uid = web.get_request_param('uid')
        if uid is None:
            status = 'ERR_NO_UID'
        else:
            userman.clear_login_failed(uid)
            logger.write_event_log(context, 'UNLOCK_USER', 'OK', 'target=' + uid)
            status = 'OK'
    else:
        status = 'FORBIDDEN'

    web.send_result_json(status, body=None)

#----------------------------------------------------------
# guests
#----------------------------------------------------------
def cmd_guests(context):
    userman.delete_expired_guest()

    if not authman.auth():
        on_auth_error()
        return

    if context.is_admin():
        status = 'OK'
        guest_user_list = userman.get_all_guest_user_info()

    else:
        status = 'FORBIDDEN'
        guest_user_list = None

    web.send_result_json(status, body=guest_user_list)

#----------------------------------------------------------
# group
# gid=GID
#----------------------------------------------------------
def cmd_group(context):
    status = 'OK'
    group_info = None
    gid = web.get_request_param('gid')
    if gid is None:
        status = 'NO_GID'
    else:
        if context.is_admin():
            group_info = groupman.get_group_info(gid)
            if group_info is None:
                status = 'NG'
        else:
            status = 'FORBIDDEN'

    web.send_result_json(status, body=group_info)

#----------------------------------------------------------
# add a group
#----------------------------------------------------------
def cmd_addgroup(context):
    if not authman.auth():
        on_auth_error()
        return

    status = 'ERROR'
    if not context.is_admin():
        web.send_result_json('FORBIDDEN', body=None)
        return

    gid = web.get_request_param('gid')
    p_privs = web.get_request_param('privs')
    desc = web.get_request_param('desc', '')

    if gid is None:
        web.send_result_json('ERR_GID', body=None)
        return

    privs = ''
    if p_privs is not None:
        privs = p_privs
        privs = util.replace(privs, '\s{2,}', ' ')
        privs = privs.strip()

    try:
        groupman.add_group(gid, privs=privs, desc=desc)
        logger.write_event_log(context, 'ADD_GROUP', 'OK', 'gid=' + gid)
        status = 'OK'
    except Exception as e:
        status = 'ERR:' + str(e)

    web.send_result_json(status, body=None)

#----------------------------------------------------------
# mod a group
#----------------------------------------------------------
def cmd_modgroup(context):
    if not authman.auth():
        on_auth_error()
        return

    gid = web.get_request_param('gid')

    if not context.is_admin():
        web.send_result_json('FORBIDDEN', body=None)
        return

    if gid is None:
        web.send_result_json('ERR_NO_GID', body=None)
        return

    privs = None
    aprivs = None
    rprivs = None
    desc = None

    p_privs = web.get_request_param('privs')
    if p_privs is not None:
        privs = p_privs
        privs = util.replace(privs, '\s{2,}', ' ')
        privs = privs.strip()

    aprivs = _get_optional_param_by_list('aprivs')
    rprivs = _get_optional_param_by_list('rprivs')

    desc = web.get_request_param('desc', '')

    try:
        groupman.modify_group(gid, privs=privs, aprivs=aprivs, rprivs=rprivs, desc=desc)
        logger.write_event_log(context, 'MOD_GROUP', 'OK', 'gid=' + gid)
        status = 'OK'
    except Exception as e:
        status = 'ERR:' + str(e)

    web.send_result_json(status, body=None)

#----------------------------------------------------------
# delgroup
# ?gid=GID
#----------------------------------------------------------
def cmd_delgroup(context):
    if not authman.auth():
        on_auth_error()
        return

    status = 'ERROR'
    if context.is_admin():
        gid = web.get_request_param('gid')
        if gid is None:
            status = 'ERR_NO_GID'
        else:
            status = 'ERR_NO_SUCH_GID'
            deleted = groupman.delete_group(gid)
            if deleted:
                logger.write_event_log(context, 'DEL_GROUP', 'OK', 'gid=' + gid)
                status = 'OK'
    else:
        status = 'FORBIDDEN'

    web.send_result_json(status, body=None)

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

        if context.is_admin():
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
    uid = context.get_user_id()
    session_list = sessionman.get_user_sessions(uid)
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
