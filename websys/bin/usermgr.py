#==============================================================================
# User Manager
# Copyright (c) 2020 Takashi Harano
#==============================================================================
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import websysconf

sys.path.append(websysconf.UTIL_PATH)
import util

import logger
import common
import sessionmgr

USER_LIST_FILE_PATH = websysconf.DATA_DIR + '/users.txt'
GUEST_USER_LIST_FILE_PATH = websysconf.DATA_DIR + '/users_guest.txt'
GROUPS_FILE_PATH = websysconf.GROUPS_FILE_PATH
PASSWORD_LIST_FILE_PATH = websysconf.PASSWORD_LIST_FILE_PATH
USER_ROOT_PATH = websysconf.USER_ROOT_PATH
PW_RESET_LOGIN_EXPIRE_SEC = websysconf.PW_RESET_LOGIN_EXPIRE_SEC

U_FLG_NEED_PW_CHANGE = 1
U_FLG_DISABLED = 1 << 2
U_FLG_INVALID_DATA = 1 << 7

USER_DATA_STRUCT = [
    {'name': 'uid'},
    {'name': 'fullname'},
    {'name': 'localfullname'},
    {'name': 'kananame'},
    {'name': 'a_name'},
    {'name': 'email'},
    {'name': 'is_admin', 'type': 'bool'},
    {'name': 'groups'},
    {'name': 'privs'},
    {'name': 'info1'},
    {'name': 'info2'},
    {'name': 'info3'},
    {'name': 'flags', 'type': 'int'},
    {'name': 'created_at', 'type': 'float'},
    {'name': 'updated_at', 'type': 'float'}
]

USER_DATA_STRUCT_FOR_GUEST = [
    {'name': 'is_guest', 'type': 'bool'},
    {'name': 'expires_at', 'type': 'float'}
]

GUEST_DATA_STRUCT = USER_DATA_STRUCT + USER_DATA_STRUCT_FOR_GUEST

USER_STATUS_DATA_STRUCT = [
    {'name': 'last_access', 'type': 'float', 'default': 0},
    {'name': 'last_login', 'type': 'float', 'default': 0},
    {'name': 'last_logout', 'type': 'float', 'default': 0},
    {'name': 'pw_changed_at', 'type': 'float', 'default': 0},
    {'name': 'login_failed_count', 'type': 'int', 'default': 0},
    {'name': 'login_failed_time', 'type': 'float', 'default': 0}
]

# User data format
# #uid	fullname	localfullname	kananame	a_name	is_admin	groups	privs	info1	info2	info3	flags	created_at	updated_at
# admin	Admin	ADMIN		Administrator	1	g1	p1	Info1	Info2	Info3	0	1721446496.789123	1721446496.789123

# Object structure
# users
# {
#   "root": {
#     "uid": "root",
#     "fullname": "root",
#     "localfullname": "root_L",
#     "kananame": "",
#     "a_name": "root_A",
#     "email": "user@host",
#     "is_admin": true,
#     "groups": "GROUP1 GROUP2",
#     "privs": "PRIVILEGE1 PRIVILEGE2",
#     "info1": "Info1",
#     "info2": "Info2",
#     "info3": "Info3",
#     "flags": 0,
#     "created_at": 1667047612.967891,
#     "updated_at": 1667047612.967891,
#     "memo": "TEXT"
#   },
#   ...
# }
#
# users_guest
# {
#   "123456": {
#     "uid": "123456",
#     "fullname": "GUEST",
#     "localfullname": "GUEST_L",
#     "kananame": "",
#     "a_name": "GUEST_A",
#     "email": "",
#     "is_admin": true,
#     "groups": "GROUP1",
#     "privs": "",
#     "info1": "",
#     "info2": "",
#     "info3": "",
#     "flags": 0,
#     "created_at": 1706947022.714497
#     "updated_at": 1706947022.714497
#     "is_guest": true
#     "expires_at": 1706948822.714497
#   },
#   ...
# }

# get user info
# return None is not exist
def get_user_info(uid, guest=True, w_memo=False):
    user = None

    users = get_all_user_info()
    if users is not None and uid in users:
        user = users[uid]
        if w_memo:
            memo_text = get_user_memo_text(uid)
            user['memo'] = memo_text

    if user is None and guest:
        users = get_all_guest_user_info()
        if users is not None and uid in users:
            user = users[uid]

    return user

# get all user info
def get_all_user_info(extra_info=False):
    users = load_all_users()
    if not extra_info:
        return users

    for uid in users:
        status_info = load_user_status_info(uid)
        users[uid]['status_info'] = status_info

    user_sessions = count_sessions_per_user()
    for uid in users:
        if uid in user_sessions:
            users[uid]['status_info']['sessions'] = user_sessions[uid]
        else:
            users[uid]['status_info']['sessions'] = 0

    return users

def load_all_users():
    users = _load_all_users(USER_LIST_FILE_PATH, USER_DATA_STRUCT)
    return users

def load_all_guest_users():
    users = _load_all_users(GUEST_USER_LIST_FILE_PATH, GUEST_DATA_STRUCT)
    return users

#----
def _load_all_users(path, data_fields_def):
    tsv_text_list = util.read_text_file_as_list(path)
    obj = {}
    for i in range(len(tsv_text_list)):
        text_line = tsv_text_list[i]
        if not util.is_comment(text_line, '#'):
            result = common.parse_tsv_field_values(text_line, data_fields_def, path)

            data = result['values']
            if result['status'] == 'OK':
                data['flags'] &= ~U_FLG_INVALID_DATA
            else:
                data['flags'] |= U_FLG_INVALID_DATA

            uid = data['uid']
            obj[uid] = data
    return obj

#------------------------------------------------------------------------------
def count_sessions_per_user():
    user_sessions = {}
    sessions = sessionmgr.get_all_sessions_info()
    for sid in sessions:
        session = sessions[sid]
        uid = session['uid']
        if uid in user_sessions:
            user_sessions[uid] += 1
        else:
            user_sessions[uid] = 1
    return user_sessions

# Create a user
# pw: SHA-256(SHA-256(pw + uid))
def add_user(uid, pw, fullname=None, localfullname=None, kananame=None, a_name=None, email=None, is_admin=False, groups='', privs='', info1='', info2='', info3='', flags=None, memo=None):
    now = util.get_timestamp()
    users = get_all_user_info()

    if users is None:
        users = {}
    elif uid in users:
        raise Exception('ALREADY_EXISTS')

    user = create_new_user(now, uid, fullname, localfullname, kananame, a_name, email, is_admin, groups, privs, info1, info2, info3, flags)

    users[uid] = user
    save_users(users)
    save_user_password(uid, pw)
    create_user_status_info(uid)

    if memo is not None:
        save_user_memo(uid, memo)

    return user

def create_new_user(timestamp, uid, fullname=None, localfullname=None, kananame=None, a_name=None, email='', is_admin=False, groups='', privs='', info1='', info2='', info3='', flags=None):
    if flags is None:
        u_flags = U_FLG_NEED_PW_CHANGE
    else:
        u_flags = parse_int(flags)

    user = {
        'uid': uid,
        'fullname': fullname,
        'localfullname': localfullname,
        'kananame': kananame,
        'a_name': a_name,
        'email': email,
        'is_admin': is_admin,
        'groups': groups,
        'privs': privs,
        'info1': info1,
        'info2': info2,
        'info3': info3,
        'flags': u_flags,
        'created_at': timestamp,
        'updated_at': timestamp
    }

    return user

# Modify a user
def modify_user(uid, pw=None, fullname=None, localfullname=None, kananame=None, a_name=None, email=None, is_admin=None, groups=None, agroup=None, rgroup=None, privs=None, aprivs=None, rprivs=None, info1=None, info2=None, info3=None, flags=None, memo=None, chg_pw=False):
    now = util.get_timestamp()
    is_guest = False

    users = get_all_user_info()
    if users is None:
        users = {}

    if uid not in users:
        users = get_all_guest_user_info()
        if users is None or uid not in users:
            raise Exception('NOT_EXISTS')
        else:
            is_guest = True

    user = users[uid]

    updated = False
    if fullname is not None:
        user['fullname'] = fullname
        updated = True

    if localfullname is not None:
        user['localfullname'] = localfullname
        updated = True

    if kananame is not None:
        user['kananame'] = kananame
        updated = True

    if a_name is not None:
        user['a_name'] = a_name
        updated = True

    if email is not None:
        user['email'] = email
        updated = True

    if is_admin is not None:
        user['is_admin'] = is_admin
        updated = True

    if groups is not None:
        user['groups'] = groups
        updated = True

    if agroup is not None:
        user['groups'] = common.add_item_value(user['groups'], agroup)
        updated = True

    if rgroup is not None:
        user['groups'] = common.remove_item_value(user['groups'], rgroup)
        updated = True

    if privs is not None:
        user['privs'] = privs
        updated = True

    if aprivs is not None:
        user['privs'] = common.add_item_value(user['privs'], aprivs)
        updated = True

    if rprivs is not None:
        user['privs'] = common.remove_item_value(user['privs'], rprivs)
        updated = True

    if info1 is not None:
        user['info1'] = info1
        updated = True

    if info2 is not None:
        user['info2'] = info2
        updated = True

    if info3 is not None:
        user['info3'] = info3
        updated = True

    if flags is not None:
        try:
            u_flags = int(flags)
            user['flags'] = u_flags
            updated = True
        except:
            pass

    if memo is not None:
        save_user_memo(uid, memo)
        updated = True

    if pw is not None:
        save_user_password(uid, pw)
        if chg_pw:
            user['flags'] = unset_user_flag(user['flags'], U_FLG_NEED_PW_CHANGE)
        update_user_status_info(uid, 'pw_changed_at', now)

    if updated:
        user['updated_at'] = now

    users[uid] = user

    if is_guest:
        save_guest_users(users)
    else:
        save_users(users)

    return user

# Delete a user
def delete_user(uid):
    users = get_all_user_info()
    if users is None or uid not in users or uid == 'root':
        return False
    sessionmgr.clear_user_sessions(uid)
    users.pop(uid)
    save_users(users)
    delete_user_password(uid)
    delete_user_dir(uid)
    return True

# Save Users
def save_users(users):
    common.save_to_tsv_file(USER_LIST_FILE_PATH, users, USER_DATA_STRUCT)

def delete_user_dir(uid):
    path = USER_ROOT_PATH + '/' + uid
    util.rmdir(path, True)

#------------------------------------------------------------------------------
# Guest user
#------------------------------------------------------------------------------
# Get all guest user
def get_all_guest_user_info(extra_info=False):
    users = load_all_guest_users()
    if not extra_info:
        return users

    for uid in users:
        status_info = load_user_status_info(uid)
        users[uid]['status_info'] = status_info

    user_sessions = count_sessions_per_user()
    for uid in users:
        if uid in user_sessions:
            users[uid]['status_info']['sessions'] = user_sessions[uid]
        else:
            users[uid]['status_info']['sessions'] = 0

    return users

# get guest user info
# return None is not exist
def get_guest_user_info(uid):
    user = None
    users = get_all_guest_user_info()
    if users is not None and uid in users:
        user = users[uid]
    return user

# Create a guest user
def add_guest(uid=None, uid_len=6, valid_min=30, groups='', privs=''):
    now = util.get_timestamp()
    users = get_all_user_info()

    guest_users = get_all_guest_user_info()
    if guest_users is None:
        guest_users = {}

    if uid is None:
        new_uid = _generate_code(uid_len)
    else:
        new_uid = uid

    if new_uid in users or new_uid in guest_users:
        if uid is None:
            for i in range(10):
                new_uid = _generate_code(uid_len)
                if new_uid not in users and new_uid not in guest_users:
                    break
        else:
            raise Exception('ALREADY_EXISTS')

    gid = len(guest_users) + 1
    fullname = 'GUEST' + str(gid)
    localfullname = fullname
    kanname = ''
    a_name = ''

    user = create_new_user(now, new_uid, fullname, localfullname, kanname, a_name, is_admin=False, groups=groups, privs=privs, flags=0)
    user['is_guest'] = True
    user['expires_at'] = now + valid_min * 60

    guest_users[new_uid] = user
    save_guest_users(guest_users)
    create_user_status_info(new_uid)

    return new_uid

def _generate_code(code_len):
    cd = util.random_string(min=code_len, max=code_len, tbl='0123456789')
    return cd

# Delete expired guest
def delete_expired_guest():
    users = get_all_guest_user_info()
    if users is None:
        return

    now = util.get_timestamp()
    new_users = {}
    for uid in users:
        user = users[uid]
        if user['expires_at'] >= now:
            new_users[uid] = user
        else:
            delete_user_dir(uid)

    save_guest_users(new_users)

# Delete a guest user
def delete_guest_user(uid):
    users = get_all_guest_user_info()
    if users is None or uid not in users:
        return False
    sessionmgr.clear_user_sessions(uid)
    users.pop(uid)
    save_guest_users(users)
    delete_user_dir(uid)
    return True

# Save Guest Users
def save_guest_users(users):
    if len(users) == 0:
        util.delete_file(GUEST_USER_LIST_FILE_PATH)
    else:
        common.save_to_tsv_file(GUEST_USER_LIST_FILE_PATH, users, GUEST_DATA_STRUCT)

#----------------------------------------------------------
def is_admin(user_info):
    if 'is_admin' in user_info and user_info['is_admin']:
        return True
    return False

#----------------------------------------------------------
# is_member_of
# group_name: case-insensitive
#----------------------------------------------------------
def is_member_of(user_info, group_name):
    if user_info is None:
        return False

    if is_admin(user_info):
        return True

    return common.has_item(user_info, 'groups', group_name)

#----------------------------------------------------------
# has_privilege
# priv_name: case-insensitive
#----------------------------------------------------------
def has_privilege(user_info, priv_name):
    if user_info is None:
        return False

    if is_admin(user_info):
        return True

    return common.has_item(user_info, 'privs', priv_name)

#------------------------------------------------------------------------------
# Password
#------------------------------------------------------------------------------
def get_password_list():
    path = PASSWORD_LIST_FILE_PATH
    pw_list = util.read_text_file_as_list(path)
    return pw_list

def get_password_list_as_dict():
    pw_list = get_password_list()
    pws = {}
    for i in range(len(pw_list)):
        line = pw_list[i]
        a = line.split('\t')
        uid =  a[0]
        pw = a[1]
        ts = float(a[2])
        pws[uid] = {
            'pw': pw,
            'updated_at': ts
        }
    return pws

def save_password_list(pw_list):
    path = PASSWORD_LIST_FILE_PATH
    util.write_text_file_from_list(path, pw_list)

def get_user_password(uid):
    pw_list = get_password_list()
    for i in range(len(pw_list)):
        data = pw_list[i]
        a = data.split('\t')
        if a[0] == uid:
            return a[1]
    return None

def save_user_password(uid, pw):
    new_data = uid + '\t' + pw
    pw_list = get_password_list()
    for i in range(len(pw_list)):
        data = pw_list[i]
        a = data.split('\t')
        if a[0] == uid:
            pw_list[i] = new_data
            save_password_list(pw_list)
            return

    pw_list.append(new_data)
    save_password_list(pw_list)

def delete_user_password(uid):
    pw_list = get_password_list()
    idx = -1
    for i in range(len(pw_list)):
        data = pw_list[i]
        a = data.split('\t')
        if a[0] == uid:
            idx = i
            break

    if idx >= 0:
        pw_list.pop(idx)
        save_password_list(pw_list)

#------------------------------------------------------------------------------
# User memo text
#------------------------------------------------------------------------------
def get_user_memo_file_path(uid):
    return  USER_ROOT_PATH + '/' + uid + '/memo.txt'

def get_user_memo_text(uid):
    path = get_user_memo_file_path(uid)
    text = util.read_text_file(path, '')
    return text

def save_user_memo(uid, memo):
    path = get_user_memo_file_path(uid)
    if memo == '':
        util.delete_file(path)
    else:
        util.write_text_file(path, memo)

#------------------------------------------------------------------------------
# User Flags
#------------------------------------------------------------------------------
def is_disabled(user_info):
    return has_user_flag(user_info, U_FLG_DISABLED)

def is_expired(user_info, now):
    if has_user_flag(user_info, U_FLG_NEED_PW_CHANGE):
        updated_at = user_info['updated_at']
        if round(now - updated_at) > PW_RESET_LOGIN_EXPIRE_SEC:
            return True
    return False

def has_user_flag(user_info, flg):
    flags =  0
    if 'flags' in user_info:
        flags =  user_info['flags']
        if util.typename(flags) == 'str':
            flags = parse_int(flags)
    if flags & flg:
        return True
    return False

def set_user_flag(flags, flg):
    if util.typename(flags) == 'str':
        flags = parse_int(flags)
    flags |= flg
    return flags

def unset_user_flag(flags, flg):
    if util.typename(flags) == 'str':
        flags = parse_int(flags)
    flags &= ~flg
    return flags

def parse_int(s):
    v = 0
    try:
        v = int(s)
    except:
        pass
    return v

#------------------------------------------------------------------------------
# User status
#------------------------------------------------------------------------------
def get_user_status_file_path(uid):
    return  USER_ROOT_PATH + '/' + uid + '/status.txt'

def get_default_status_info():
    data_struct = USER_STATUS_DATA_STRUCT
    info = {}
    for i in range(len(data_struct)):
        field = data_struct[i]
        name = field['name']
        default = field['default']
        info[name] = default
    return info

def create_user_status_info(uid):
    info = get_default_status_info()
    write_user_status_info(uid, info)

def load_user_status_info(uid):
    info = get_default_status_info()
    path = get_user_status_file_path(uid)

    data = util.load_properties(path, USER_STATUS_DATA_STRUCT, info)
    info = data['props']
    if data['error'] is not None:
        logger.write_system_log('ERROR', uid, 'usermgr.load_user_status_info(): ' + data['error'])

    return info

def write_user_status_info(uid, info):
    path = get_user_status_file_path(uid)
    util.save_properties(path, info)

# Clear login failure counter and time
def clear_login_failed(uid):
    info = load_user_status_info(uid)
    info['login_failed_count'] = 0
    info['login_failed_time'] = 0
    write_user_status_info(uid, info)
    return info

def update_user_status_info(uid, key, v):
    user_status_info = load_user_status_info(uid)
    user_status_info[key] = v
    write_user_status_info(uid, user_status_info)

#------------------------------------------------------------------------------
# Groups
#------------------------------------------------------------------------------
def get_groups_for_user(uid):
    user_info = get_user_info(uid)
    if user_info is None:
        return None
    if groups is not None:
        return None
    groups = user_info['groups']
    group_list = groups.split(' ')
    return group_list
