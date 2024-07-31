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

import usermgr
import groupmgr
import sessionmgr
import authmgr

LOCK_FILE_PATH = websysconf.LOCK_FILE_PATH
root_path = ''
query = None
sendrecv_encryption = True
recv_encryption_key = 1
send_encryption_key = 7

#----------------------------------------------------------
# set root path
#----------------------------------------------------------
def set_root_path(path):
    global root_path
    root_path = path

#-----------------
# WebContext Class
#-----------------
class WebContext:
    def __init__(self):
        self.status = ''
        self.session_info = None
        self.user_info = None
        self.authorized = False

    def get_status(self):
        return self.status

    def set_status(self, status):
        self.status = status

    def is_authorized(self):
        return self.authorized

    def set_authorized(self, authorized):
        self.authorized = authorized

    def get_session_info(self):
        return self.session_info

    def set_session_info(self, session_info):
        self.session_info = session_info

    #------------------------------------------------------
    # get_user_info
    #
    # Returns:
    # user: {
    #   "uid": "root", # guest: "123456"
    #   "fullname": "root", # guest: "GUEST"
    #   "local_name": "root_L", # guest: "GUEST_L"
    #   "c_name": "root_C", # guest: "GUEST_C"
    #   "is_admin": true,
    #   "groups": "GROUP1 GROUP2",
    #   "privs": "PRIVILEGE1 PRIVILEGE2",
    #   "desc": "Description",
    #   "status": 0,
    #   "created_at": 1667047612.967891,
    #   "updated_at": 1667047612.967891,
    #   "pw_changed_at": 1667047612.967891,
    #   "is_guest": true, # for guest only
    #   "expires_at": 1571476916.59936 # for guest only
    # }
    #
    # or None
    #------------------------------------------------------
    def get_user_info(self):
        return self.user_info

    def set_user_info(self, user_info):
        self.user_info = user_info

    def get_session_id(self):
        session_info = self.session_info
        if session_info is not None and 'sid' in session_info:
            return session_info['sid']
        return None

    def get_user_id(self):
        user_info = self.user_info
        if user_info is not None and 'uid' in user_info:
            return user_info['uid']
        return None

    def get_user_fullname(self):
        user_info = self.user_info
        if user_info is not None and 'fullname' in user_info:
            return user_info['fullname']
        return ''

    def get_user_local_name(self):
        user_info = self.user_info
        if user_info is not None and 'local_name' in user_info:
            return user_info['local_name']
        return ''

    def get_user_c_name(self):
        user_info = self.user_info
        if user_info is not None and 'c_name' in user_info:
            return user_info['c_name']
        return ''

    def is_admin(self):
        user_info = self.user_info
        if user_info is not None:
            if 'is_admin' in user_info and user_info['is_admin']:
                return True
        return False

    # group_name: case-insensitive
    def is_member_of(self, group_name):
        user_info = self.user_info
        if user_info is None:
            return False
        return usermgr.is_member_of(user_info, group_name)

    def get_groups(self):
        user_info = self.user_info
        if user_info is None:
            return []

        if 'groups' not in user_info:
            return []

        groups = user_info['groups']
        group_list = groups.split(' ')
        return group_list

    # priv_name: case-insensitive
    def has_privilege(self, priv_name):
        user_info = self.user_info
        if user_info is None:
            return False
        return usermgr.has_privilege(user_info, priv_name)

    # Returns if the user has privilege in privileges or groups
    # priv_name: case-insensitive
    def has_permission(self, priv_name):
        if self.has_privilege(priv_name):
            return True

        groups = self.get_groups()
        for i in range(len(groups)):
            gid = groups[i]
            if groupmgr.has_privilege_in_group(gid, priv_name):
                return True

        return False

    def get_user_description(self):
        user_info = self.user_info
        if user_info is not None and 'desc' in user_info:
            return user_info['desc']
        return ''

    def is_guest(self):
        session_info = self.session_info
        if session_info is not None:
            if 'is_guest' in session_info and session_info['is_guest']:
                return True
        return False

#----------------------------------------------------------
# on access
#----------------------------------------------------------
def on_access(allow_guest=True):
    #context = {
    #    'status': '',
    #    'session_info': None,
    #    'user_info': None,
    #    'authorized': False
    #}

    context = WebContext()

    if synchronize_start():
        context = _on_access(context, allow_guest)
        context.set_status('OK')
        synchronize_end()
    else:
        context.set_status('SYSTEM_BUSY')

    return context

def _on_access(context, allow_guest):
    sessionmgr.clear_all_expired_sessions()

    sid = util.get_cookie_val('sid')
    sessions = sessionmgr.get_all_sessions_info()
    session_info = None
    if sid in sessions:
        session_info = sessions[sid]

    if session_info is None:
        return context

    uid = session_info['uid']
    user_info = usermgr.get_user_info(uid)

    session_info = sessionmgr.update_last_access_info(uid, sid)
    sessionmgr.set_current_session_info_to_global(session_info)
    authorized = authmgr.auth(allow_guest)

    context.set_session_info(session_info)
    context.set_user_info(user_info) # see usermgr.create_user() for object fields
    context.set_authorized(authorized)

    return context

#----------------------------------------------------------
# Get Request Param
#----------------------------------------------------------
def get_request_param(key=None, default=None):
    content_type = os.environ.get('CONTENT_TYPE', '')
    if content_type.startswith('multipart/form-data'):
        return default

    q = util.get_query()
    if q is None or util.typename(q) == 'FieldStorage':
        return default

    if sendrecv_encryption:
        q = util.replace(q, '&?_trcid=.+', '')
        try:
            q = bsb64.decode_string(q, recv_encryption_key)
        except:
            pass

    if key is not None:
        if q == '':
            q = None
        else:
            q = util.get_request_param(key, q=q)

    if q is None:
        q = default
    else:
        q = util.decode_uri(q)

    return q

def get_request_param_as_int(key=None, default=0):
    p = get_request_param(key)
    try:
        v = int(p)
    except:
        v = default
    return v

def get_request_param_as_bool(key=None, as_true='true'):
    p = get_request_param(key)
    return p == as_true

def get_raw_request_param(key=None, default=None):
    return get_request_param(key, default)

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
        session_timeout = sessionmgr.get_session_timeout_value()
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
# get user agent
#----------------------------------------------------------
def get_user_agent():
    return util.get_user_agent()

#----------------------------------------------------------
# send response
#----------------------------------------------------------
def send_response(result, type, headers=None, encoding=None, encryption=sendrecv_encryption):
    if headers is None:
        session_info = sessionmgr.get_current_session_info_from_global()
        cookies = build_session_cookie(session_info)
        headers = cookies
    _send_response(result, type, headers, encoding, encryption)

def _send_response(result, type, headers=None, encoding=None, encryption=False):
    if type == 'application/json' and util.typename(result) != 'str':
        result = util.to_json(result)

    if type == 'text/html':
        content = result
    else:
        if encryption:
            content = bsb64.encode_string(result, send_encryption_key)
            type = 'text/plain'
        else:
            content = result

    util.send_response(content, type, headers=headers)

#----------------------------------------------------------
def send_result_json(status, body=None, headers=None, http_headers=None, encryption=sendrecv_encryption):
    result = util.build_result_object(status, body, headers)
    content = util.to_json(result)
    send_response(content, 'application/json', headers=http_headers, encryption=encryption)

#----------------------------------------------------------
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

#----------------------------------------------------------
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
def get_user_fullname(uid, default=None):
    user_fullname = default
    if default is None:
        user_fullname = uid
    user_info = usermgr.get_user_info(uid)
    if user_info is not None and 'fullname' in user_info:
        user_fullname = user_info['fullname']
    return user_fullname

def get_user_local_name(uid, default=None):
    user_local_name = default
    if default is None:
        user_local_name = uid
    user_info = usermgr.get_user_info(uid)
    if user_info is not None and 'local_name' in user_info:
        user_local_name = user_info['local_name']
    return user_local_name

def get_user_c_name(uid, default=None):
    if user_info is not None and 'c_name' in user_info:
        user_c_name = user_info['c_name']
    if default is None:
        user_c_name = get_user_local_name(uid)
    return user_c_name

#----------------------------------------------------------
def synchronize_start():
    return util.file_lock(LOCK_FILE_PATH, 15, 0.2)

def synchronize_end():
    util.file_unlock(LOCK_FILE_PATH)
