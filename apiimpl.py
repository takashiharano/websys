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
import usermgr
import groupmgr
import sessionmgr
import authmgr

import websys

#----------------------------------------------------------
# syslog
#----------------------------------------------------------
def cmd_syslog(context):
    status = 'OK'
    if context.is_admin():
        p_n = websys.get_request_param('n')
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

    websys.send_result_json(status, body=log_list)

#----------------------------------------------------------
# login
# ?id=ID&pw=HASH(SHA-256(pw + uid))
#----------------------------------------------------------
def cmd_login(context):
    id = websys.get_request_param('id')
    pw = websys.get_request_param('pw')
    p_ext_auth = websys.get_request_param('ext_auth')
    ext_auth = True if p_ext_auth == 'true' else False
    result = websys.login(context, id, pw, ext_auth)

    cookies = []
    cookie = websys.build_cookie_for_clear('ts')
    cookies.append({'Set-Cookie': cookie})

    websys.send_result_json(result['status'], body=result['body'], http_headers=cookies)

#----------------------------------------------------------
# logout
# ?sid=SID (prior)
# ?uid=UID
#----------------------------------------------------------
def cmd_logout(context):
    p_sid = websys.get_request_param('sid')
    if p_sid is None:
        p_uid = websys.get_request_param('uid')
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
        if websys.get_request_param('all') == 'true':
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
        headers = websys.build_logout_cookies()

    cb_url = websys.get_request_param('url')
    res_body = {
        'url': cb_url
    }
    websys.send_result_json(status, body=res_body, http_headers=headers)

# Logout by SID
def logout_by_sid(context, current_sid, sid):
    self_logout = False
    if not context.has_permission('sysadmin'):
        current_uid = context.get_user_id()
        target_session_info = sessionmgr.get_session_info(sid)
        if target_session_info is None:
            return False
        elif target_session_info['uid'] != current_uid:
            raise Exception('FORBIDDEN')

    cleared_session = authmgr.logout(sid)
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
        if not context.has_permission('sysadmin'):
            raise Exception('FORBIDDEN')

    i = sessionmgr.clear_user_sessions(uid)
    if i == 0:
        raise Exception('NOT_LOGGED_IN')

    return self_logout

# ALL Logout
def all_logout(context, current_sid, self_logout=False):
    if not context.has_permission('sysadmin'):
        raise Exception('FORBIDDEN')

    sessions = sessionmgr.get_all_sessions_info()
    for sid in sessions:
        if self_logout or sid != current_sid:
            logout_by_sid(context, current_sid, sid)

    return self_logout

#----------------------------------------------------------
# auth
#----------------------------------------------------------
def cmd_auth(context):
    status = 'FORBIDDEN'
    if authmgr.auth():
        status = 'OK'
    websys.send_result_json(status, body=None)

#----------------------------------------------------------
# session
#----------------------------------------------------------
def cmd_session(context):
    status = 'OK'
    session_info = context.get_session_info()
    p_userinfo = websys.get_request_param('userinfo')

    if session_info is not None and p_userinfo == 'true':
        user_info = context.get_user_info()
        session_info['userinfo'] = user_info

    websys.send_result_json(status, body=session_info)

#----------------------------------------------------------
# sessions
#----------------------------------------------------------
def cmd_sessions(context):
    status = 'OK'
    all = websys.get_request_param('all')
    if all is None:
        session_list = get_session_list_from_session(context)
    else:
        if context.has_permission('sysadmin'):
            session_list = []
            sessions = sessionmgr.get_all_sessions_info()
            for sid in sessions:
                session_list.append(sessions[sid])
        else:
            session_list = get_session_list_from_session(context)
    websys.send_result_json(status, body=session_list)

#----------------------------------------------------------
# user
# uid=UID
#----------------------------------------------------------
def cmd_user(context):
    status = 'OK'
    user_info = None
    uid = websys.get_request_param('uid')
    w_memo = websys.get_request_param('w_memo', '0')

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
              user_info = usermgr.get_user_info(uid, w_memo=w_memo)
          else:
              if context.has_permission('sysadmin'):
                  user_info = usermgr.get_user_info(uid, w_memo=w_memo)
                  if user_info is None:
                      status = 'NG'
              else:
                  status = 'FORBIDDEN'

    websys.send_result_json(status, body=user_info)

#----------------------------------------------------------
# users
#----------------------------------------------------------
def cmd_users(context):
    if not authmgr.auth():
        on_auth_error()
        return

    if context.has_permission('sysadmin'):
        status = 'OK'
        user_list = usermgr.get_all_user_info()
        guest_user_list = usermgr.get_all_guest_user_info()
        if guest_user_list is not None:
            user_list.update(guest_user_list)
    else:
        status = 'FORBIDDEN'
        user_list = None

    websys.send_result_json(status, body=user_list)

#----------------------------------------------------------
# add a user
#----------------------------------------------------------
def cmd_useradd(context):
    if not authmgr.auth():
        on_auth_error()
        return

    status = 'ERROR'
    if not context.has_permission('sysadmin'):
        websys.send_result_json('FORBIDDEN', body=None)
        return

    uid = websys.get_request_param('uid')
    fullname = websys.get_request_param('fullname')
    localfullname = websys.get_request_param('localfullname')
    a_name = websys.get_request_param('a_name')
    email = websys.get_request_param('email')
    pw = websys.get_request_param('pw')
    p_admin = websys.get_request_param('is_admin')
    p_groups = websys.get_request_param('groups', '')
    p_privs = websys.get_request_param('privs')
    info1 = websys.get_request_param('info1', '')
    info2 = websys.get_request_param('info2', '')
    info3 = websys.get_request_param('info3', '')
    p_flags = websys.get_request_param('flags')
    memo = websys.get_request_param('memo', '')

    if uid is None:
        websys.send_result_json('ERR_UID', body=None)
        return

    if pw is None:
        websys.send_result_json('ERR_PW', body=None)
        return
    pw_hash = util.hash(pw, websysconf.ALGOTRITHM)

    if fullname is None:
        fullname = uid

    if localfullname is None:
        localfullname = fullname

    is_admin = False
    if p_admin is not None:
        is_admin = p_admin == 'true'

    groups = ''
    if p_groups is not None:
        groups = p_groups
        groups = util.replace(groups, r'\s{2,}', ' ')
        groups = groups.strip()

    privs = ''
    if p_privs is not None:
        privs = p_privs
        privs = util.replace(privs, r'\s{2,}', ' ')
        privs = privs.strip()

    if p_flags == '':
        p_flags = None

    try:
        usermgr.add_user(uid, pw_hash, fullname=fullname, localfullname=localfullname, a_name=a_name, email=email, is_admin=is_admin, groups=groups, privs=privs, info1=info1, info2=info2, info3=info3, flags=p_flags, memo=memo)
        logger.write_event_log(context, 'ADD_USER', 'OK', 'target=' + uid)
        status = 'OK'
    except Exception as e:
        status = 'ERR:' + str(e)

    websys.send_result_json(status, body=None)

#----------------------------------------------------------
# mod a user
#----------------------------------------------------------
def cmd_usermod(context):
    if not authmgr.auth():
        on_auth_error()
        return

    uid = websys.get_request_param('uid')

    if not context.has_permission('sysadmin'):
        user_info = context.get_user_info()
        if uid != user_info['uid']:
            websys.send_result_json('FORBIDDEN', body=None)
            return

    if uid is None:
        websys.send_result_json('ERR_UID', body=None)
        return

    fullname = websys.get_request_param('fullname')
    localfullname = websys.get_request_param('localfullname')
    a_name = websys.get_request_param('a_name')
    email = websys.get_request_param('email')

    pw = websys.get_request_param('pw')
    pw_hash = None
    if pw is not None:
        pw_hash = util.hash(pw, websysconf.ALGOTRITHM)

    is_admin = None
    groups = None
    agroup = None
    rgroup = None
    privs = None
    aprivs = None
    rprivs = None
    info1 = None
    info2 = None
    info3 = None
    u_flags = None
    memo = None

    if context.has_permission('sysadmin'):
        p_admin = websys.get_request_param('is_admin')
        if p_admin is not None:
            is_admin = p_admin == 'true'

        p_groups = websys.get_request_param('groups')
        if p_groups is not None:
            groups = p_groups
            groups = util.replace(groups, r'\s{2,}', ' ')
            groups = groups.strip()

        agroup = _get_optional_param_by_list('agroup')
        rgroup = _get_optional_param_by_list('rgroup')

        p_privs = websys.get_request_param('privs')
        if p_privs is not None:
            privs = p_privs
            privs = util.replace(privs, r'\s{2,}', ' ')
            privs = privs.strip()

        aprivs = _get_optional_param_by_list('aprivs')
        rprivs = _get_optional_param_by_list('rprivs')
        info1 = websys.get_request_param('info1', '')
        info2 = websys.get_request_param('info2', '')
        info3 = websys.get_request_param('info3', '')
        memo = websys.get_request_param('memo', '')

        p_flags = websys.get_request_param('flags')
        if p_flags is not None:
            u_flags = p_flags

    try:
        usermgr.modify_user(uid, pw_hash, fullname=fullname, localfullname=localfullname, a_name=a_name, email=email, is_admin=is_admin, groups=groups, agroup=agroup, rgroup=rgroup, privs=privs, aprivs=aprivs, rprivs=rprivs, info1=info1, info2=info2, info3=info3, flags=u_flags, memo=memo)
        logger.write_event_log(context, 'MOD_USER', 'OK', 'target=' + uid)
        status = 'OK'
    except Exception as e:
        status = 'ERR:' + str(e)

    websys.send_result_json(status, body=None)

def _get_optional_param_by_list(key):
    p_value = websys.get_request_param(key)
    param_list = None
    if p_value is not None:
        p_value = p_value.strip()
        p_value = util.replace(p_value, r'\s{2,}', ' ')
        param_list = p_value.split(' ')
        if len(param_list) == 1 and param_list[0] == '':
            param_list = None
    return param_list

#----------------------------------------------------------
# Change password
#----------------------------------------------------------
def cmd_passwd(context):
    if not authmgr.auth():
        on_auth_error()
        return

    uid = websys.get_request_param('uid')

    if not context.has_permission('sysadmin'):
        user_info = context.get_user_info()
        if uid != user_info['uid']:
            websys.send_result_json('FORBIDDEN', body=None)
            return

    if uid is None:
        websys.send_result_json('ERR_UID', body=None)
        return

    pw = websys.get_request_param('pw')
    pw_hash = None
    if pw is not None:
        pw_hash = util.hash(pw, websysconf.ALGOTRITHM)

    try:
        usermgr.modify_user(uid, pw_hash, chg_pw=True)
        status = 'OK'
        logger.write_event_log(context, 'CHG_PW', 'OK', 'target=' + uid)
    except Exception as e:
        status = 'ERR_' + str(e)

    websys.send_result_json(status, body=None)

#----------------------------------------------------------
# gencode
# ?validsec=1800
#----------------------------------------------------------
def cmd_gencode(context):
    if not authmgr.auth():
        on_auth_error()
        return

    uid = None
    if not context.has_permission('sysadmin'):
        websys.send_result_json('FORBIDDEN', body=None)
        return

    status = 'OK'
    valid_min = 30
    p_valid_time = websys.get_request_param('validtime')
    if p_valid_time is not None:
        try:
            valid_min = int(p_valid_time)
        except:
            pass

    id = None
    p_id = websys.get_request_param('id')
    if p_id is not None:
        id = p_id

    p_groups = websys.get_request_param('groups')
    groups = ''
    if p_groups is not None:
        groups = p_groups
        groups = util.replace(groups, r'\s{2,}', ' ')
        groups = groups.strip()

    p_privs = websys.get_request_param('privs')
    privs = ''
    if p_privs is not None:
        privs = p_privs
        privs = util.replace(privs, r'\s{2,}', ' ')
        privs = privs.strip()

    try:
        uid = usermgr.add_guest(uid=id, valid_min=valid_min, groups=groups, privs=privs)
    except Exception as e:
        status = str(e)

    websys.send_result_json(status, body=uid)

#----------------------------------------------------------
# userdel
# ?uid=UID
#----------------------------------------------------------
def cmd_userdel(context):
    if not authmgr.auth():
        on_auth_error()
        return

    status = 'ERROR'
    if context.has_permission('sysadmin'):
        uid = websys.get_request_param('uid')
        if uid is None:
            status = 'ERR_NO_UID'
        else:
            if _is_prohibited_uid(uid):
                status = 'ERR_PROHIBITED_UID'
            else:
                status = 'ERR_NO_SUCH_UID'
                deleted = usermgr.delete_guest_user(uid)
                if deleted:
                    status = 'OK'
                else:
                    deleted = usermgr.delete_user(uid)
                    if deleted:
                        logger.write_event_log(context, 'DEL_USER', 'OK', 'target=' + uid)
                        status = 'OK'

    else:
        status = 'FORBIDDEN'

    websys.send_result_json(status, body=None)

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
    if not authmgr.auth():
        on_auth_error()
        return

    status = 'ERROR'
    if context.has_permission('sysadmin'):
        uid = websys.get_request_param('uid')
        if uid is None:
            status = 'ERR_NO_UID'
        else:
            usermgr.clear_login_failed(uid)
            logger.write_event_log(context, 'UNLOCK_USER', 'OK', 'target=' + uid)
            status = 'OK'
    else:
        status = 'FORBIDDEN'

    websys.send_result_json(status, body=None)

#----------------------------------------------------------
# guests
#----------------------------------------------------------
def cmd_guests(context):
    usermgr.delete_expired_guest()

    if not authmgr.auth():
        on_auth_error()
        return

    if context.has_permission('sysadmin'):
        status = 'OK'
        guest_user_list = usermgr.get_all_guest_user_info()

    else:
        status = 'FORBIDDEN'
        guest_user_list = None

    websys.send_result_json(status, body=guest_user_list)

#----------------------------------------------------------
# group
# gid=GID
#----------------------------------------------------------
def cmd_group(context):
    status = 'OK'
    group_info = None
    gid = websys.get_request_param('gid')
    if gid is None:
        status = 'NO_GID'
    else:
        if context.has_permission('sysadmin'):
            group_info = groupmgr.get_group_info(gid)
            if group_info is None:
                status = 'NG'
        else:
            status = 'FORBIDDEN'

    websys.send_result_json(status, body=group_info)

#----------------------------------------------------------
# add a group
#----------------------------------------------------------
def cmd_addgroup(context):
    if not authmgr.auth():
        on_auth_error()
        return

    status = 'ERROR'
    if not context.has_permission('sysadmin'):
        websys.send_result_json('FORBIDDEN', body=None)
        return

    gid = websys.get_request_param('gid')
    name = websys.get_request_param('name', '')
    p_privs = websys.get_request_param('privs')
    desc = websys.get_request_param('desc', '')

    if gid is None:
        websys.send_result_json('ERR_GID', body=None)
        return

    privs = ''
    if p_privs is not None:
        privs = p_privs
        privs = util.replace(privs, r'\s{2,}', ' ')
        privs = privs.strip()

    try:
        groupmgr.add_group(gid, name=name, privs=privs, desc=desc)
        logger.write_event_log(context, 'ADD_GROUP', 'OK', 'gid=' + gid)
        status = 'OK'
    except Exception as e:
        status = 'ERR:' + str(e)

    websys.send_result_json(status, body=None)

#----------------------------------------------------------
# mod a group
#----------------------------------------------------------
def cmd_modgroup(context):
    if not authmgr.auth():
        on_auth_error()
        return

    gid = websys.get_request_param('gid')

    if not context.has_permission('sysadmin'):
        websys.send_result_json('FORBIDDEN', body=None)
        return

    if gid is None:
        websys.send_result_json('ERR_NO_GID', body=None)
        return

    privs = None
    aprivs = None
    rprivs = None
    desc = None

    name = websys.get_request_param('name')
    p_privs = websys.get_request_param('privs')
    if p_privs is not None:
        privs = p_privs
        privs = util.replace(privs, r'\s{2,}', ' ')
        privs = privs.strip()

    aprivs = _get_optional_param_by_list('aprivs')
    rprivs = _get_optional_param_by_list('rprivs')

    desc = websys.get_request_param('desc', '')

    try:
        groupmgr.modify_group(gid, name=name, privs=privs, aprivs=aprivs, rprivs=rprivs, desc=desc)
        logger.write_event_log(context, 'MOD_GROUP', 'OK', 'gid=' + gid)
        status = 'OK'
    except Exception as e:
        status = 'ERR:' + str(e)

    websys.send_result_json(status, body=None)

#----------------------------------------------------------
# delgroup
# ?gid=GID
#----------------------------------------------------------
def cmd_delgroup(context):
    if not authmgr.auth():
        on_auth_error()
        return

    status = 'ERROR'
    if context.has_permission('sysadmin'):
        gid = websys.get_request_param('gid')
        if gid is None:
            status = 'ERR_NO_GID'
        else:
            status = 'ERR_NO_SUCH_GID'
            deleted = groupmgr.delete_group(gid)
            if deleted:
                logger.write_event_log(context, 'DEL_GROUP', 'OK', 'gid=' + gid)
                status = 'OK'
    else:
        status = 'FORBIDDEN'

    websys.send_result_json(status, body=None)

#----------------------------------------------------------
# hello
#----------------------------------------------------------
def cmd_hello(context):
    status = 'OK'
    msg = None

    q = websys.get_request_param('q')
    if q is None:
        msg = 'Hello, World!'
    else:
        if not authmgr.auth():
            on_auth_error()
            return

        if context.has_permission('sysadmin'):
            msg= 'Hello, ' + q
        else:
            msg = 'Hi!'

    websys.send_result_json(status, body=msg)

#------------------------------------------------------------------------------
#----------------------------------------------------------
# On auth error
#----------------------------------------------------------
def on_auth_error():
    obj = {'status': 'AUTH_ERROR'}
    websys.send_response(obj, 'application/json')

#----------------------------------------------------------
# get user info
#----------------------------------------------------------
def get_session_list_from_session(context):
    uid = context.get_user_id()
    session_list = sessionmgr.get_user_sessions(uid)
    return session_list

#----------------------------------------------------------
# main
#----------------------------------------------------------
def main():
    context = websys.on_access()
    cmd = websys.get_request_param('cmd')

    if cmd is None:
        websys.send_result_json('ERR_NO_CMD_SPECIFIED', body=cmd)
        return

    func_name = 'cmd_' + cmd
    g = globals()
    if func_name in g:
        g[func_name](context)
    else:
        websys.send_result_json('ERR_CMD_NOT_FOUND', body=cmd)
