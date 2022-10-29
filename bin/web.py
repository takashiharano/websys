#==============================================================================
# Web System Basic Functions
# Copyright (c) 2020 Takashi Harano
#==============================================================================
import os
import sys

import config
sys.path.append(config.UTIL_PATH)
import util
import bsb64

import userman
import sessionman
import authman

root_path = ''
query = None

encryption = True
LOCK_FILE_PATH = config.LOCK_FILE_PATH

#----------------------------------------------------------
# set root path
#----------------------------------------------------------
def set_root_path(path):
    global root_path
    root_path = path

#----------------------------------------------------------
# on access
#----------------------------------------------------------
def on_access():
    sid = util.get_cookie_val('sid')
    sessionman.set_current_session_id(sid)

    session_info = None
    user_info = None

    sessions = sessionman.get_all_sessions_info()
    if sessions is not None:
        if synchronize_start():
            sessions = sessionman.clear_expired_sessions(sessions)
            sessionman.update_last_accessed_info(sessions)
            synchronize_end()
            if sid in sessions:
                session_info = sessions[sid]

    if session_info is not None:
        uid = session_info['uid']
        user_info = userman.get_user_info(uid)

    is_admin = False
    if user_info is not None and 'is_admin' in user_info:
        is_admin = user_info['is_admin']

    context = {
        'session_info': session_info,
        'user_info': user_info, # see userman.create_user() for object fields
        'is_admin': is_admin,
        'authorized': False
    }

    return context

def get_request_param(key=None, default=None):
    q = util.get_query()

    if q is not None:
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
            q = util.get_query(key, q)

    if q is None:
        q = default
    else:
        q = util.decode_uri(q)

    return q

def get_raw_request_param(key=None, default=None):
    q = util.get_query()

    if key is not None:
      if q == '':
          q = None
      else:
          q = util.get_query(key, q)

    if q is None:
        q = default
    else:
        q = util.decode_uri(q)

    return q

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
# users
#   "uid": "root",
#   "name": "root",
#   "is_admin": true,
#   "permissions": ["DOMAIN.PERMISSIONNAME"],
#   "disabled": false
# }
# users_guest
#   "uid": "123456",
#   "name": "GUEST",
#   "permissions": [],
#   "is_guest": true,
#   "path": null | '/path/',
#   "disabled": false,
#   "expire": 1571476916.59936
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
# has_permission
# permission_name: case-insensitive
#----------------------------------------------------------
def has_permission(context, permission_name):
    if is_admin(context):
        return True
    if 'user_info' in context:
        user_info = context['user_info']
        if user_info is not None:
            return permission_name in user_info['permissions']
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
    cookies = []
    cookie1 = util.build_cookie_clear('sid', path='/', http_only=True)
    cookie2 = util.build_cookie_clear('guest', path='/', http_only=True)
    cookies.append({'Set-Cookie': cookie1})
    cookies.append({'Set-Cookie': cookie2})
    return cookies

#----------------------------------------------------------
# build session cookie
#----------------------------------------------------------
def build_session_cookie(session_info):
    cookies = []
    if session_info is None:
        cookies = build_logout_cookies()
    else:
        sid = session_info['sid']
        uid = session_info['uid']
        session_timeout = sessionman.get_session_timeout_value()
        cookie1 = util.build_cookie('sid', sid, max_age=str(session_timeout), path='/', http_only=True)
        cookies.append({'Set-Cookie': cookie1})

    return cookies

#----------------------------------------------------------
# send response
#----------------------------------------------------------
def send_response(type, result, encoding=None, do_not_set_cookie=False):
    headers = None

    if not do_not_set_cookie:
        session_info = sessionman.get_current_session_info()
        cookies = build_session_cookie(session_info)
        headers = cookies

    _send_response(type, result, headers, encoding)

def _send_response(type, result, headers=None, encoding=None):
    if type == 'json' and util.typename(result) != 'str':
        result = util.to_json(result)

    if type == 'html':
        content = result
    else:
        if encryption:
            content = bsb64.encode_string(result, 7)
            type = 'text'
        else:
            content = result

    util.send_response(type, content, headers=headers)

def send_result_json(status, body=None, headers=None, do_not_set_cookie=False):
    result = util.build_result_object(status, body, headers)
    content = util.to_json(result)
    send_response('json', content, do_not_set_cookie=do_not_set_cookie)

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
    send_response('html', html)

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
    send_response('html', html)

#----------------------------------------------------------
def auth(default=False, allow_guest=True):
    ret = False
    if synchronize_start():
        ret = authman.auth(default, allow_guest)
        synchronize_end()
    return ret

#----------------------------------------------------------
def synchronize_start():
    if util.file_lock(LOCK_FILE_PATH, 50, 0.2):
        return True
    return False

def synchronize_end():
    util.file_unlock(LOCK_FILE_PATH)
