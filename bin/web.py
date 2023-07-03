#==============================================================================
# Web System Basic Functions
# Copyright (c) 2020 Takashi Harano
#==============================================================================
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import websysconf

sys.path.append(websysconf.UTIL_PATH)
import util
import bsb64

import userman
import sessionman
import authman

root_path = ''
query = None

encryption = True
LOCK_FILE_PATH = websysconf.LOCK_FILE_PATH

#----------------------------------------------------------
# set root path
#----------------------------------------------------------
def set_root_path(path):
    global root_path
    root_path = path

#----------------------------------------------------------
# on access
#----------------------------------------------------------
def on_access(allow_guest=True):
    context = {
        'status': '',
        'session_info': None,
        'user_info': None,
        'authorized': False
    }

    if synchronize_start():
        context = _on_access(context, allow_guest)
        context['status'] = 'OK'
        synchronize_end()
    else:
        context['status'] = 'SYSTEM_BUSY'

    return context

def _on_access(context, allow_guest):
    sid = util.get_cookie_val('sid')
    session_info = None
    user_info = None

    sessions = sessionman.get_all_sessions_info()
    if sessions is None:
        return context

    sessions = sessionman.clear_expired_sessions(sessions)
    sessionman.update_last_accessed_info(sessions, sid)

    if sid in sessions:
        session_info = sessions[sid]

    if session_info is None:
        return context

    uid = session_info['uid']
    user_info = userman.get_user_info(uid)

    sessionman.set_current_session_info(session_info)
    context['session_info'] = session_info
    context['user_info'] = user_info # see userman.create_user() for object fields
    context['authorized'] = authman.auth(allow_guest)

    return context

#----------------------------------------------------------
# Get Request Param
#----------------------------------------------------------
def get_request_param(key=None, default=None):
    q = util.get_query()
    if q is None:
        return default

    if encryption:
        q = util.replace(q, '&?_trcid=.+', '')
        try:
            q = bsb64.decode_string(q, 1)
        except:
            pass

    if key is not None:
        if q == '':
            q = None
        else:
            q = util.get_query_value(q, key)

    if q is None:
        q = default
    else:
        q = util.decode_uri(q)

    return q

def get_raw_request_param(key=None, default=None):
    return get_request_param(key, default)

#----------------------------------------------------------
# get_session_info
# Returns: session_info or None
#----------------------------------------------------------
def get_session_info(context):
    session_info = None
    if 'session_info' in context:
        session_info = context['session_info']
    return session_info

#----------------------------------------------------------
# get_session_id
# Returns: session id or None
#----------------------------------------------------------
def get_session_id(context):
    if 'session_info' in context:
        session_info = context['session_info']
        if session_info is not None and 'sid' in session_info:
            return session_info['sid']
    return None

#----------------------------------------------------------
# get_user_info
#
# Returns:
# user: {
#   "uid": "root",
#   "name": "root",
#   "name_l": "root_L",
#   "is_admin": true,
#   "group": "GROUP1 GROUP2",
#   "privs": "PRIVILEGE1 PRIVILEGE2"
#   "created_at": 1667047612.967891,
#   "updated_at": 1667047612.967891,
#   "status": 0
# }
#
# users_guest: {
#   "uid": "123456",
#   "name": "GUEST",
#   "name_l": "GUEST_L",
#   "group": "GROUP1",
#   "privs": "",
#   "is_guest": true,
#   "created_at": 1667047612.967891,
#   "updated_at": 1667047612.967891,
#   "expires_at": 1571476916.59936
#   "status": 0
# }
#
# or None
#----------------------------------------------------------
def get_user_info(context):
    user_info = None
    if 'user_info' in context:
        user_info = context['user_info']
    return user_info

#----------------------------------------------------------
# get_user_id
# Returns: user id or None
#----------------------------------------------------------
def get_user_id(context):
    if 'user_info' in context:
        user_info = context['user_info']
        if user_info is not None and 'uid' in user_info:
            return user_info['uid']
    return None

#----------------------------------------------------------
# get_user_name
# Returns: user name or ''
#----------------------------------------------------------
def get_user_name(context):
    if 'user_info' in context:
        user_info = context['user_info']
        if user_info is not None and 'name' in user_info:
            return user_info['name']
    return ''

#----------------------------------------------------------
# get_user_name_l
# Returns: user local name or ''
#----------------------------------------------------------
def get_user_name_l(context):
    if 'user_info' in context:
        user_info = context['user_info']
        if user_info is not None and 'name_l' in user_info:
            return user_info['name_l']
    return ''

#----------------------------------------------------------
# is_admin
#----------------------------------------------------------
def is_admin(context):
    if 'user_info' in context:
        user_info = context['user_info']
        if user_info is not None:
            if 'is_admin' in user_info and user_info['is_admin']:
                return True
    return False

#----------------------------------------------------------
# is_member_of
# group_name: case-insensitive
#----------------------------------------------------------
def is_member_of(context, group_name):
    if 'user_info' in context:
        user_info = context['user_info']
        return userman.is_member_of(user_info, group_name)

    return False

#----------------------------------------------------------
# has_privilege
# privilege_name: case-insensitive
#----------------------------------------------------------
def has_privilege(context, privilege_name):
    if 'user_info' in context:
        user_info = context['user_info']
        return userman.has_privilege(user_info, privilege_name)

    return False

#----------------------------------------------------------
# is_guest
#----------------------------------------------------------
def is_guest(context):
    if 'session_info' in context:
        session_info = context['session_info']
        if session_info is not None:
            if 'is_guest' in session_info and session_info['is_guest']:
                return True
    return False

#----------------------------------------------------------
# build logout cookies
#----------------------------------------------------------
def build_logout_cookies():
    cookie1 = util.build_cookie_for_clear('sid', path='/', http_only=True)
    cookies = []
    cookies.append({'Set-Cookie': cookie1})
    return cookies

#----------------------------------------------------------
# build session cookie
#----------------------------------------------------------
def build_session_cookie(session_info):
    cookies = None
    if session_info is not None:
        sid = session_info['sid']
        uid = session_info['uid']
        session_timeout = sessionman.get_session_timeout_value()
        cookie1 = util.build_cookie('sid', sid, max_age=str(session_timeout), path='/', http_only=True)
        cookies = []
        cookies.append({'Set-Cookie': cookie1})

    return cookies

#----------------------------------------------------------
# get ip addr
#----------------------------------------------------------
def get_ip_addr():
    addr = util.get_ip_addr()
    return addr

#----------------------------------------------------------
# get host name
#----------------------------------------------------------
def get_host_name():
    if websysconf.USE_HOSTNAME:
        host = util.get_host_name()
    else:
        host = ''
    return host

#----------------------------------------------------------
# send response
#----------------------------------------------------------
def send_response(result, type, headers=None, encoding=None):
    if headers is None:
        session_info = sessionman.get_current_session_info()
        cookies = build_session_cookie(session_info)
        headers = cookies
    _send_response(result, type, headers, encoding)

def _send_response(result, type, headers=None, encoding=None):
    if type == 'application/json' and util.typename(result) != 'str':
        result = util.to_json(result)

    if type == 'text/html':
        content = result
    else:
        if encryption:
            content = bsb64.encode_string(result, 7)
            type = 'text/plain'
        else:
            content = result

    util.send_response(content, type, headers=headers)

def send_result_json(status, body=None, headers=None, http_headers=None):
    result = util.build_result_object(status, body, headers)
    content = util.to_json(result)
    send_response(content, 'application/json', headers=http_headers)

# Blue Screen
def blue_screen(msg=None):
    if msg is None:
        msg = 'FORBIDDEN'
    html = '''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=Edge">
<title>ERROR</title>
<style>
body, pre {
  background: #fff;
  color: #000;
  font-size: 14px;
  font-family: Consolas;
}
</style>
</head>
<body>
<pre>''' +  msg + '''</pre>
</body>
</html>'''
    send_response(html, 'text/html')

# Auth Redirection
def redirect_auth_screen():
    global root_path
    html = '''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=Edge">
'''
    html += '<script src="' + root_path + 'libs/util.js"></script>\n'
    html += '<script src="' + root_path + 'websys/websys.js"></script>\n'
    html += '<script>\n'
    html += 'onLoad = function() {\n'
    html +='  websys.init(\'' + root_path + '\');\n'
    html += 'websys.authRedirection(location.href);';
    html += '};\n'
    html += '''window.addEventListener('load', onLoad, true);
</script>
</head>
<body>
</body>
</html>'''
    send_response(html, 'text/html')

#----------------------------------------------------------
def synchronize_start():
    if util.file_lock(LOCK_FILE_PATH, 25, 0.2):
        return True
    return False

def synchronize_end():
    util.file_unlock(LOCK_FILE_PATH)
