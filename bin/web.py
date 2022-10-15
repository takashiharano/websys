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

import sessionman
import authman

root_path = ''
query = None

encryption = True

#----------------------------------------------------------
# set root path
#----------------------------------------------------------
def set_root_path(path):
    global root_path
    root_path = path

#----------------------------------------------------------
# on access
#----------------------------------------------------------
def on_access(from_ext=False):
    sid = util.get_cookie_val('sid')
    sessionman.set_current_session_id(sid)
    sessions = sessionman.get_all_sessions_info()
    if sessions is None:
        return
    sessions = sessionman.clear_expired_sessions(sessions)
    sessionman.update_last_accessed_info(sessions)
    return sessions

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
# get_current_session_id
# session id or None
#----------------------------------------------------------
def get_current_session_id():
    return sessionman.get_current_session_id()

#----------------------------------------------------------
# get_current_session_info
# session info or None
#----------------------------------------------------------
def get_current_session_info():
    return sessionman.get_current_session_info()

#----------------------------------------------------------
# get_current_user_id
# user id or None
#----------------------------------------------------------
def get_current_user_id():
    return sessionman.get_current_user_id()

#----------------------------------------------------------
# get_current_user_name
# user name or None
#----------------------------------------------------------
def get_current_user_name():
    name = None
    userinfo = sessionman.get_current_user_info()
    if userinfo is not None:
        name = userinfo['name']
    return name

#----------------------------------------------------------
# get_current_user_info
#----------------------------------------------------------
# users
#   "uid": "root",
#   "attr": ["system"],
#   "role": ["admin"],
#   "disabled": false
# }
# users_guest
#   "uid": "123456",
#   "name": "GUEST",
#   "attr": [
#     "guest"
#   ],
#   "role": [],
#   "path": null | '/path/',
#   "disabled": false,
#   "expire": 1571476916.59936
# }
#
# or None
def get_current_user_info():
    return sessionman.get_current_user_info()

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
        is_guest = session_info['is_guest']
        session_timeout = sessionman.get_session_timeout_value()
        cookie1 = util.build_cookie('sid', sid, max_age=str(session_timeout), path='/', http_only=True)
        cookies.append({'Set-Cookie': cookie1})

        if is_guest:
            cookie2 = util.build_cookie('guest', 'true', max_age=str(session_timeout), path='/', http_only=True)
            cookies.append({'Set-Cookie': cookie2})

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
def auth(default=False, roles=None, allow_guest=False):
    return authman.auth(default, roles, allow_guest)
