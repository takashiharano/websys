#==============================================================================
# Web System API Implementations
# Copyright (c) 2020 Takashi Harano
#==============================================================================
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../libs'))
import util

util.append_system_path(__file__, './bin')
import config
import userman
import sessionman
import authman
import web

#----------------------------------------------------------
# main
#----------------------------------------------------------
def main():
  web.on_access()
  cmd = web.get_request_param('cmd')

  if cmd is None:
    web.send_result_json('ERR_NO_CMD_SPECIFIED', body=cmd)
    return

  func_name = 'cmd_' + cmd
  g = globals()
  if func_name in g:
    g[func_name]()
  else:
    web.send_result_json('ERR_CMD_NOT_FOUND', body=cmd)

#----------------------------------------------------------
# login
# ?id=ID&pw=HASH(SHA-256(pw + uid))
#----------------------------------------------------------
def cmd_login():
  id = web.get_request_param('id')
  pw = web.get_request_param('pw')
  p_ext_auth = web.get_request_param('ext_auth')
  ext_auth = True if p_ext_auth == 'true' else False

  userman.delete_expired_guest()

  if not ext_auth:
    web.on_access()
    current_sid = sessionman.get_current_session_id()
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

    if not ext_auth:
      sessionman.set_current_session_id(sid)

  except Exception as e:
    status = str(e)
    body = None
    util.sleep(0.5)

  do_not_set_cookie = True if ext_auth else False

  web.send_result_json(status, body=body, do_not_set_cookie=do_not_set_cookie)

#----------------------------------------------------------
# loginlog
#----------------------------------------------------------
def cmd_loginlog():
  status = 'OK'
  if authman.has_role('admin'):
    p_n = web.get_request_param('n')
    n = 10
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
def cmd_logout():
  web.on_access()

  p_sid = web.get_request_param('sid')
  if p_sid is None:
    p_uid = web.get_request_param('uid')
  else:
    p_uid = None

  status = 'OK'
  current_sid = sessionman.get_current_session_id()

  target_sid = None
  if p_sid is None and p_uid is None:
    target_sid = current_sid
  elif p_sid is not None:
    target_sid = p_sid

  self_logout = False
  try:
    if web.get_request_param('all') == 'true':
      self_logout = all_logout(current_sid)
    elif target_sid is not None:
      # current session or specified sid
      self_logout = logout_by_sid(current_sid, target_sid)
    elif p_uid is not None:
      # all sessions of the user
      self_logout = logout_by_uid(p_uid)
  except Exception as e:
    status = str(e)

  if p_sid is None and p_uid is None:
    self_logout = True

  headers = None
  if self_logout:
    cookie = util.build_cookie_clear('sid', '/')
    headers = [
      ('Set-Cookie', cookie)
    ]

  web.send_result_json(status, body=None)

# Logout by SID
def logout_by_sid(current_sid, sid):
  self_logout = False
  if not authman.has_role('admin'):
    current_uid = sessionman.get_current_user_id()
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
def logout_by_uid(uid):
  self_logout = False
  current_uid = sessionman.get_current_user_id()
  if uid == current_uid:
    self_logout = True
  else:
    if not authman.has_role('admin'):
      raise Exception('FORBIDDEN')

  user_sessions = sessionman.get_session_info_list_from_uid(uid)
  if len(user_sessions) == 0:
    raise Exception('NOT_LOGGED_IN')

  for session in user_sessions:
    sid = session['sid']
    cleared_session = authman.logout(sid)

  return self_logout

# ALL Logout
def all_logout(current_sid, self_logout=False):
  if not authman.has_role('admin'):
    raise Exception('FORBIDDEN')

  sessions = sessionman.get_all_sessions_info()
  for sid in sessions:
    if self_logout or sid != current_sid:
      logout_by_sid(current_sid, sid)

  return self_logout

#----------------------------------------------------------
# auth
#----------------------------------------------------------
def cmd_auth():
  web.on_access()
  status = 'FORBIDDEN'
  if authman.auth(default=False):
    status = 'OK'
  web.send_result_json(status, body=None)

#----------------------------------------------------------
# session
#----------------------------------------------------------
def cmd_session():
  web.on_access()
  status = 'OK'
  session_info = sessionman.get_current_session_info()
  p_userinfo = web.get_request_param('userinfo')

  if session_info is not None and p_userinfo == 'true':
    user_info = sessionman.get_current_user_info()
    session_info['userinfo'] = user_info

  web.send_result_json(status, body=session_info)

#----------------------------------------------------------
# sessions
#----------------------------------------------------------
def cmd_sessions():
  status = 'OK'
  all = web.get_request_param('all')
  if all is None:
    session_list = get_session_list_from_session()
  else:
    if authman.has_role('admin'):
      session_list = sessionman.get_all_sessions_info()
    else:
      session_list = get_session_list_from_session()
  web.send_result_json(status, body=session_list)

#----------------------------------------------------------
# user
# uid=UID
#----------------------------------------------------------
def cmd_user():
  status = 'OK'
  user_info = None
  uid = web.get_request_param('uid')

  if uid is None:
    sid = sessionman.get_current_session_id()
    if sid is None:
      status = 'NOT_LOGGED_IN'
    else:
      user_info = sessionman.get_current_user_info()
  else:
    current_uid = sessionman.get_current_user_id()
    if current_uid is None:
      status = 'FORBIDDEN'
    else:
      if uid == current_uid:
        user_info = userman.get_user_info(uid)
      else:
        if authman.has_role('admin'):
          user_info = userman.get_user_info(uid)
          if user_info is None:
            status = 'NG'
        else:
          status = 'FORBIDDEN'

  web.send_result_json(status, body=user_info)

#----------------------------------------------------------
# users
#----------------------------------------------------------
def cmd_users():
  if not authman.auth(default=True):
    return

  if authman.has_role('admin'):
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
def cmd_useradd():
  if not authman.auth(default=True):
    return

  status = 'ERROR'
  if not authman.has_role('admin'):
    web.send_result_json('FORBIDDEN', body=None)
    return

  uid = web.get_request_param('uid')
  name = web.get_request_param('name')
  pw = web.get_request_param('pw')
  p_disabled = web.get_request_param('disabled')

  if uid is None:
    web.send_result_json('ERR_UID', body=None)
    return

  if pw is None:
    web.send_result_json('ERR_PW', body=None)
    return

  if name is None:
    name = uid

  if p_disabled is None:
    p_disabled = 'false'

  pw_hash = util.hash(pw, config.ALGOTRITHM)
  disabled = p_disabled == 'true'

  try:
    userman.create_user(uid, pw_hash, name=name, attr=[], roles=[], disabled=disabled)
    status = 'OK'
  except Exception as e:
    status = 'ERR_' + str(e)

  web.send_result_json(status, body=None)

#----------------------------------------------------------
# mod a user
#----------------------------------------------------------
def cmd_usermod():
  if not authman.auth(default=True):
    return

  uid = web.get_request_param('uid')
  name = web.get_request_param('name')
  pw = web.get_request_param('pw')
  p_disabled = web.get_request_param('disabled')

  user_info = web.get_current_user_info()

  status = 'ERROR'
  if not authman.has_role('admin'):
    if uid != user_info['uid']:
      web.send_result_json('FORBIDDEN', body=None)
      return

  if uid is None:
    web.send_result_json('ERR_UID', body=None)
    return

  pw_hash = None
  if pw is not None:
    pw_hash = util.hash(pw, config.ALGOTRITHM)

  disabled = None
  if p_disabled is not None:
    disabled = p_disabled == 'true'

  try:
    userman.modify_user(uid, pw_hash, name=name, disabled=disabled)
    status = 'OK'
  except Exception as e:
    status = 'ERR_' + str(e)

  web.send_result_json(status, body=None)

#----------------------------------------------------------
# gencode
# ?validsec=1800
#----------------------------------------------------------
def cmd_gencode():
  if not authman.auth(default=True):
    return

  uid = None
  if not authman.has_role('admin'):
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

  p_path = web.get_request_param('path')

  id = None
  p_id = web.get_request_param('id')
  if p_id is not None:
    id = p_id

  try:
    uid = userman.create_guest(uid=id, valid_min=valid_min, path=p_path)
  except Exception as e:
    status = str(e)

  web.send_result_json(status, body=uid)

#----------------------------------------------------------
# userdel
# ?uid=UID
#----------------------------------------------------------
def cmd_userdel():
  if not authman.auth(default=True):
    return

  status = 'ERROR'
  if authman.has_role('admin'):
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
def cmd_guests():
  userman.delete_expired_guest()

  if not authman.auth(default=True):
    return

  if authman.has_role('admin'):
    status = 'OK'
    guest_user_list = userman.get_all_guest_user_info()

  else:
    status = 'FORBIDDEN'
    guest_user_list = None

  web.send_result_json(status, body=guest_user_list)

#----------------------------------------------------------
# hello
#----------------------------------------------------------
def cmd_hello():
  status = 'OK'
  msg = None

  q = web.get_request_param('q')
  if q is None:
    msg = 'Hello, World!'
  else:
    if not authman.auth(default=True):
      return

    if authman.has_role('admin'):
      msg= 'Hello, ' + q
    else:
      msg = 'Hi!'

  web.send_result_json(status, body=msg)

#------------------------------------------------------------------------------
#----------------------------------------------------------
# get user info
#----------------------------------------------------------
def get_session_list_from_session():
  uid = sessionman.get_current_user_id()
  session_list = sessionman.get_session_info_list_from_uid(uid)
  return session_list
