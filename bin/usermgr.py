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

U_FLG_NEED_PW_CHANGE = 1
U_FLG_DISABLED = 1 << 1
U_FLG_INVALID_DATA = 1 << 7

USER_DATA_FIELDS = [
    {'key': 'uid'},
    {'key': 'name'},
    {'key': 'local_name'},
    {'key': 'email'},
    {'key': 'is_admin', 'data_type': 'bool'},
    {'key': 'groups'},
    {'key': 'privs'},
    {'key': 'info1'},
    {'key': 'info2'},
    {'key': 'desc'},
    {'key': 'flags', 'data_type': 'int'},
    {'key': 'created_at', 'data_type': 'float'},
    {'key': 'updated_at', 'data_type': 'float'}
]

USER_DATA_FIELDS_FOR_GUEST = [
    {'key': 'is_guest', 'data_type': 'bool'},
    {'key': 'expires_at', 'data_type': 'float'}
]

GUEST_DATA_FIELDS = USER_DATA_FIELDS + USER_DATA_FIELDS_FOR_GUEST

# User data format
# #uid	name	local_name	is_admin	groups	privs	info1	info2	desc	flags	created_at	updated_at
# admin	Admin	ADMIN	1	g1	p1	Info1	Info2	Description	0	1721446496.789123	1721446496.789123

# Object structure
# users
# {
#   "root": {
#     "uid": "root",
#     "name": "root",
#     "local_name": "root_L",
#     "email": "user@host",
#     "is_admin": true,
#     "groups": "GROUP1 GROUP2",
#     "privs": "PRIVILEGE1 PRIVILEGE2",
#     "info1": "Info1",
#     "info2": "Info2",
#     "desc": "Description",
#     "flags": 0,
#     "created_at": 1667047612.967891,
#     "updated_at": 1667047612.967891
#   },
#   ...
# }
#
# users_guest
# {
#   "123456": {
#     "uid": "123456",
#     "name": "GUEST",
#     "local_name": "GUEST_L",
#     "email": "",
#     "is_admin": true,
#     "groups": "GROUP1",
#     "privs": "",
#     "info1": "",
#     "info2": "",
#     "desc": "Description",
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
def get_user_info(uid, guest=True):
    user = None

    users = get_all_user_info()
    if users is not None and uid in users:
        user = users[uid]

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
    users = _load_all_users(USER_LIST_FILE_PATH, USER_DATA_FIELDS)
    return users

def load_all_guest_users():
    users = _load_all_users(GUEST_USER_LIST_FILE_PATH, GUEST_DATA_FIELDS)
    return users

#----
def _load_all_users(path, data_fields_def):
    tsv_text_list = util.read_text_file_as_list(path)
    obj = {}
    for i in range(len(tsv_text_list)):
        text_line = tsv_text_list[i]
        if not util.is_comment(text_line, '#'):
            result = common.parse_tsv_field_values(text_line, data_fields_def)

            data = result['values']
            if result['has_error']:
                data['flags'] |= U_FLG_INVALID_DATA
            else:
                data['flags'] &= ~U_FLG_INVALID_DATA

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
def add_user(uid, pw, name=None, local_name=None, email=None, is_admin=False, groups='', privs='', info1='', info2='', desc='', flags=None):
    now = util.get_timestamp()
    users = get_all_user_info()

    if users is None:
        users = {}
    elif uid in users:
        raise Exception('ALREADY_EXISTS')

    user = create_new_user(now, uid, name, local_name, email, is_admin, groups, privs, info1, info2, desc, flags)

    users[uid] = user
    save_users(users)
    save_user_password(uid, pw)
    create_user_status_info(uid)

    return user

def create_new_user(timestamp, uid, name=None, local_name=None, email='', is_admin=False, groups='', privs='', info1='', info2='', desc='', flags=None):
    if flags is None:
        u_flags = U_FLG_NEED_PW_CHANGE
    else:
        u_flags = parse_int(flags)

    desc = util.replace(desc, '\t|\r\n|\n', ' ')

    user = {
        'uid': uid,
        'name': name,
        'local_name': local_name,
        'email': email,
        'is_admin': is_admin,
        'groups': groups,
        'privs': privs,
        'info1': info1,
        'info2': info2,
        'desc': desc,
        'flags': u_flags,
        'created_at': timestamp,
        'updated_at': timestamp
    }

    return user

# Modify a user
def modify_user(uid, pw=None, name=None, local_name=None, email=None, is_admin=None, groups=None, agroup=None, rgroup=None, privs=None, aprivs=None, rprivs=None, info1=None, info2=None, desc=None, flags=None):
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
    if name is not None:
        user['name'] = name
        updated = True

    if local_name is not None:
        user['local_name'] = local_name
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

    if desc is not None:
        desc = util.replace(desc, '\t|\r\n|\n', ' ')
        user['desc'] = desc
        updated = True

    if flags is not None:
        try:
            u_flags = int(flags)
            user['flags'] = u_flags
            updated = True
        except:
            pass

    if pw is not None:
        save_user_password(uid, pw)
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
    common.save_to_tsv_file(USER_LIST_FILE_PATH, users, USER_DATA_FIELDS)

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
def add_guest(uid=None, uid_len=6, valid_min=30, groups='', privs='', desc=''):
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
    name = 'GUEST' + str(gid)
    local_name = name

    user = create_new_user(now, new_uid, name, local_name, is_admin=False, groups=groups, privs=privs, desc=desc, flags=0)
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
    common.save_to_tsv_file(GUEST_USER_LIST_FILE_PATH, users, GUEST_DATA_FIELDS)

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
# User Flags
#------------------------------------------------------------------------------
def is_disabled(user_info):
    return has_user_flag(user_info, U_FLG_DISABLED)

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
DEFAULT_STATUS_INFO = {
    'last_access': 0,
    'last_login': 0,
    'last_logout': 0,
    'pw_changed_at': 0,
    'login_failed_count': 0,
    'login_failed_time': 0
}

def get_user_status_file_path(uid):
    return  USER_ROOT_PATH + '/' + uid + '/status.json'

def create_user_status_info(uid):
    info = DEFAULT_STATUS_INFO.copy()
    write_user_status_info(uid, info)

def load_user_status_info(uid):
    info = DEFAULT_STATUS_INFO.copy()
    path = get_user_status_file_path(uid)

    try:
        data = common.load_dict(path)
        if not data is None:
            info = util.update_dict(info, data)
    except Exception as e:
        logger.write_system_log('ERROR', uid, 'usermgr.load_user_status_info(): ' + str(e))

    return info

def write_user_status_info(uid, info):
    path = get_user_status_file_path(uid)
    util.save_dict(path, info)

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
