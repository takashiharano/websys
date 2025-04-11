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

sys.path.append(os.path.join(os.path.dirname(__file__), 'bin'))
import usermgr
import groupmgr
import sessionmgr
import authmgr

LOCK_FILE_PATH = websysconf.LOCK_FILE_PATH
g_root_path = ''
query = None
sendrecv_encryption = True
recv_encryption_key = 1
send_encryption_key = 7

current_context = None

def init(http_encryption):
    global sendrecv_encryption
    sendrecv_encryption = http_encryption

#----------------------------------------------------------
# set root path
#----------------------------------------------------------
def set_root_path(path):
    global g_root_path
    g_root_path = path

#-----------------
# WebContext Class
#-----------------
class WebContext:
    def __init__(self):
        self.status = ''
        self.session_info = None
        self.user_info = None
        self.authorized = False
        self.timestamp = None

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
    #   "localfullname": "root_L", # guest: "GUEST_L"
    #   "kananame": "", # guest: ""
    #   "a_name": "root_A", # guest: "GUEST_A"
    #   "is_admin": true,
    #   "groups": "GROUP1 GROUP2",
    #   "privs": "PRIVILEGE1 PRIVILEGE2",
    #   "flags": 0,
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

    def get_user_local_fullname(self):
        user_info = self.user_info
        if user_info is not None and 'localfullname' in user_info:
            return user_info['localfullname']
        return ''

    def get_user_kananame(self):
        user_info = self.user_info
        if user_info is not None and 'kananame' in user_info:
            return user_info['kananame']
        return ''

    def get_user_a_name(self):
        user_info = self.user_info
        if user_info is not None and 'a_name' in user_info:
            return user_info['a_name']
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

    def is_guest(self):
        session_info = self.session_info
        if session_info is not None:
            if 'is_guest' in session_info and session_info['is_guest']:
                return True
        return False

    def get_timestamp(self):
        return self.timestamp

    def set_timestamp(self, ts):
        self.timestamp = ts

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

    set_context_to_global(context)

    return context

def _on_access(context, allow_guest):
    now = util.get_timestamp()
    now_ms = int(now * 1000)
    sessionmgr.clear_all_expired_sessions()

    sid = util.get_cookie_val('sid')
    sessions = sessionmgr.get_all_sessions_info()
    is_managed = False

    if sid in sessions:
        session_info = sessions[sid]
        uid = session_info['uid']
        user_info = usermgr.get_user_info(uid)
        is_managed = True
    else:
        # Anonymous
        anonymous_session_sec = sessionmgr.get_anonymous_session_period_sec()
        if anonymous_session_sec <= 0:
            return context

        ts = util.get_cookie_val('ts')
        if ts is None:
            ts = now_ms
        ts = util.to_int(ts)

        uid = None
        if sid is None:
            # New session
            session_info = sessionmgr.create_new_session_info(uid, now)
            ts = now_ms
        else:
            # Sesion already exists
            session_info = sessionmgr.build_session_info(sid, uid, now)

        context.set_timestamp(ts)

    sessionmgr.set_current_session_info_to_global(session_info)
    context.set_session_info(session_info)

    if is_managed:
        session_info = sessionmgr.update_last_access_info(uid, sid)
        authorized = authmgr.auth(allow_guest)
        context.set_user_info(user_info) # see usermgr.create_user() for object fields

        flags = user_info['flags']
        if flags & usermgr.U_FLG_NEED_PW_CHANGE:
            authorized = False

        context.set_authorized(authorized)

    return context

def get_current_context_from_global():
    global current_context
    return current_context

def set_context_to_global(context):
    global current_context
    current_context = context

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
# login
#----------------------------------------------------------
def login(context, id, pw, ext_auth):
    usermgr.delete_expired_guest()

    if not ext_auth:
        invalidate_existing_session(context)

    try:
        login_info = authmgr.login(id, pw, ext_auth)
        session_info = login_info['session_info']
        user_info = login_info['user_info']

        context.set_session_info(session_info)
        context.set_user_info(user_info)

        sid = session_info['sid']
        status = 'OK'

        flags = user_info['flags']
        if flags & usermgr.U_FLG_NEED_PW_CHANGE:
            status = 'PWD_CHG'

        body = {
            'sid': sid
        }
        for key in user_info:
            body[key] = user_info[key]

    except Exception as e:
        status = str(e)
        body = None
        util.sleep(0.5)

    return {'status': status, 'body': body}

#---
def invalidate_existing_session(context):
    current_sid = context.get_session_id()
    if current_sid is not None:
        authmgr.logout(current_sid, renew=True)

#----------------------------------------------------------
# logout
#----------------------------------------------------------
def logout(sid, renew=False):
    return authmgr.logout(sid)

def build_logout_cookies():
    names = ['sid', 'ts']
    cookies = []
    for i in range(len(names)):
        name = names[i]
        cookie = build_cookie_for_clear(name)
        cookies.append({'Set-Cookie': cookie})
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
# build session cookie
#----------------------------------------------------------
def get_response_cookies(context):
    if context is None:
        return None

    for_anonymous = True

    cookies = None
    session_info = context.get_session_info()
    if session_info is not None:
        sid = session_info['sid']
        uid = session_info['uid']

        if uid is not None:
            for_anonymous = False

        cookies = append_cookie(cookies, 'sid', sid, for_anonymous)

    if for_anonymous:
        ts = context.get_timestamp()
        if ts is not None:
            sts = str(ts)
            cookies = append_cookie(cookies, 'ts', sts, for_anonymous)

    return cookies

def append_cookie(cookies, name, value, for_anonymous):
    if cookies is None:
        cookies = []
    cookie = build_cookie_header_field(name, value, for_anonymous)
    cookies.append(cookie)
    return cookies

def build_cookie_header_field(name, value, for_anonymous):
    if for_anonymous:
        max_age = sessionmgr.get_anonymous_session_period_sec()
        if max_age <= 0:
            return cookies
    else:
        max_age = sessionmgr.get_session_timeout_value()

    cookie = util.build_cookie(name, value, max_age=str(max_age), path='/', http_only=True)
    return {'Set-Cookie': cookie}

def build_cookie_for_clear(name):
    cookie = util.build_cookie_for_clear(name, path='/', http_only=True)
    return cookie

#----------------------------------------------------------
# send response
#----------------------------------------------------------
def send_response(result, type, headers=None, encoding=None, encryption=None):
    if encryption is None:
        encryption = sendrecv_encryption

    context = get_current_context_from_global()
    cookies = get_response_cookies(context)

    if cookies is not None:
        if headers is None:
            headers = []
        headers += cookies

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
def send_result_json(status, body=None, headers=None, http_headers=None, encryption=None):
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
#
#    if context.is_authorized() or context.has_permission('privilege_name'):
#        websys.redirect_auth_screen('../')
#        return
#
def redirect_auth_screen(root_path=None):
    if root_path is None:
        global g_root_path
        root_path = g_root_path

    html = build_auth_redirection_screen(root_path)
    send_response(html, 'text/html')

#------------------------------------------------------------------------------
def build_auth_redirection_screen(root_path):
    html = '<!DOCTYPE html>'
    html += '<html>'
    html += '<head>'
    html += '<meta charset="utf-8">'
    html += '<script src="' + root_path + 'libs/util.js"></script>'
    html += '<script src="' + root_path + 'websys/websys.js"></script>'
    html += '<script>'
    html += 'websys.init(\'' + root_path + '\');'
    html += '$onLoad = function() {websys.authRedirection(location.href);};'
    html += '</script>'
    html += '</head>'
    html += '<body></body>'
    html += '</html>'
    return html

#----------------------------------------------------------
def get_user_fullname(uid, default=None):
    user_fullname = default
    if default is None:
        user_fullname = uid
    user_info = usermgr.get_user_info(uid)
    if user_info is not None and 'fullname' in user_info:
        user_fullname = user_info['fullname']
    return user_fullname

def get_user_local_fullname(uid, default=None):
    user_local_fullname = default
    if default is None:
        user_local_fullname = uid
    user_info = usermgr.get_user_info(uid)
    if user_info is not None and 'localfullname' in user_info:
        user_local_fullname = user_info['localfullname']
    return user_local_fullname

def get_user_kananame(uid, default=None):
    user_kananame = default
    if user_info is not None and 'kananame' in user_info:
        user_kananame = user_info['kananame']
    if default is None:
        user_kananame = ''
    return user_kananame

def get_user_a_name(uid, default=None):
    user_a_name = default
    if user_info is not None and 'a_name' in user_info:
        user_a_name = user_info['a_name']
    if default is None:
        user_a_name = get_user_local_fullname(uid)
    return user_a_name

#----------------------------------------------------------
def synchronize_start():
    return util.file_lock(LOCK_FILE_PATH, 15, 0.2)

def synchronize_end():
    util.file_unlock(LOCK_FILE_PATH)
