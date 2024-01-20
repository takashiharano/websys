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

import common
import sessionmgr

USER_LIST_FILE_PATH = websysconf.USER_LIST_FILE_PATH
GUEST_USER_LIST_FILE_PATH = websysconf.GUEST_USER_LIST_FILE_PATH
GROUPS_FILE_PATH = websysconf.GROUPS_FILE_PATH
USER_ROOT_PATH = websysconf.USER_ROOT_PATH

U_FLG_NEED_PW_CHANGE = 1
U_FLG_DISABLED = 1 << 1

# users.json
# {
#   "root": {
#     "uid": "root",
#     "name": "root",
#     "local_name": "root_L",
#     "is_admin": true,
#     "group": "GROUP1 GROUP2",
#     "privs": "PRIVILEGE1 PRIVILEGE2",
#     "desc": "Description",
#     "flags": 0,
#     "created_at": 1667047612.967891,
#     "updated_at": 1667047612.967891
#   },
#   ...
# }

# users_guest.json
# {
#   "123456": {
#     "uid": "123456",
#     "name": "GUEST",
#     "local_name": "GUEST_L",
#     "group": "GROUP1",
#     "privs": "",
#     "desc": "Description",
#     "is_guest": true,
#     "flags": 0,
#     "created_at": 1667047612.967891,
#     "updated_at": 1667047612.967891,
#     "expires_at": 1571476916.59936
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
    users = util.load_dict(USER_LIST_FILE_PATH)

    if extra_info:
        for uid in users:
            status_info = load_user_status_info(uid)
            users[uid]['status_info'] = status_info

    return users

# Create a user
# pw: SHA-256(SHA-256(pw + uid))
def create_user(uid, pw, name=None, local_name=None, is_admin=False, group='', privs='', desc='', flags=None):
    users = get_all_user_info()
    if users is None:
        users = {}
    elif uid in users:
        raise Exception('ALREADY_EXISTS')

    now = util.get_timestamp()
    if flags is None:
        u_flags = U_FLG_NEED_PW_CHANGE
    else:
        u_flags = parse_int(flags)

    desc = util.replace(desc, '\t|\r\n|\n', ' ')

    user = {
        'uid': uid,
        'name': name,
        'local_name': local_name,
        'is_admin': is_admin,
        'group': group,
        'privs': privs,
        'desc': desc,
        'flags': u_flags,
        'created_at': now,
        'updated_at': now
    }

    users[uid] = user
    save_users(users)
    save_user_password(uid, pw)
    create_user_status_info(uid)

    return user

# Modify a user
def modify_user(uid, pw=None, name=None, local_name=None, is_admin=None, group=None, agroup=None, rgroup=None, privs=None, aprivs=None, rprivs=None, desc=None, flags=None):
    now = util.get_timestamp()

    users = get_all_user_info()
    if users is None:
        users = {}
    elif uid not in users:
        raise Exception('NOT_EXISTS')

    user = users[uid]

    updated = False
    if name is not None:
        user['name'] = name
        updated = True

    if local_name is not None:
        user['local_name'] = local_name
        updated = True

    if is_admin is not None:
        user['is_admin'] = is_admin
        updated = True

    if group is not None:
        user['group'] = group
        updated = True

    if agroup is not None:
        user['group'] = common.add_item_value(user['group'], agroup)
        updated = True

    if rgroup is not None:
        user['group'] = common.remove_item_value(user['group'], rgroup)
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
        user_status_info = load_user_status_info(uid)
        user_status_info['pw_changed_at'] = now
        write_user_status_info(uid, user_status_info)

    if updated:
        user['updated_at'] = now

    users[uid] = user
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
    util.save_dict(USER_LIST_FILE_PATH, users, indent=2)

def delete_user_dir(uid):
    path = USER_ROOT_PATH + '/' + uid
    util.rmdir(path, True)

#------------------------------------------------------------------------------
# Guest user
#------------------------------------------------------------------------------
# Get all guest user
def get_all_guest_user_info():
    users = util.load_dict(GUEST_USER_LIST_FILE_PATH)
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
def add_guest(uid=None, uid_len=6, valid_min=30, group='', privs='', desc=''):
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

    desc = util.replace(desc, '\t|\r\n|\n', ' ')

    now = util.get_timestamp()
    expires_at = now + valid_min * 60
    user = {
        'uid': new_uid,
        'name': name,
        'local_name': local_name,
        'group': group,
        'privs': privs,
        'desc': desc,
        'is_guest': True,
        'flags': 0,
        'created_at': now,
        'updated_at': now,
        'expires_at': expires_at
    }

    guest_users[new_uid] = user
    save_guest_users(guest_users)

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

    save_guest_users(new_users)

# Delete a guest user
def delete_guest_user(uid):
    users = get_all_guest_user_info()
    if users is None or uid not in users:
        return False
    sessionmgr.clear_user_sessions(uid)
    users.pop(uid)
    save_guest_users(users)
    return True

# Save Guest Users
def save_guest_users(users):
    util.save_dict(GUEST_USER_LIST_FILE_PATH, users, indent=2)

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

    return common.has_item(user_info, 'group', group_name)

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
    path = websysconf.PASSWORD_LIST_FILE_PATH
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
    path = websysconf.PASSWORD_LIST_FILE_PATH
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
    'last_accessed': 0,
    'pw_changed_at': 0,
    'login_failed': {'count': 0, 'time': 0}
}

def get_user_status_file_path(uid):
    return  USER_ROOT_PATH + '/' + uid + '/status.json'

def create_user_status_info(uid):
    info = DEFAULT_STATUS_INFO.copy()
    write_user_status_info(uid, info)

def load_user_status_info(uid):
    info = DEFAULT_STATUS_INFO.copy()
    path = get_user_status_file_path(uid)
    data = util.load_dict(path)
    if not data is None:
        info = util.update_dict(info, data)
    return info

def write_user_status_info(uid, info):
    path = get_user_status_file_path(uid)
    util.save_dict(path, info)

# Clear login failure counter and time
def clear_login_failed(uid):
    info = load_user_status_info(uid)
    info['login_failed']['count'] = 0
    info['login_failed']['time'] = 0
    write_user_status_info(uid, info)
    return info

#------------------------------------------------------------------------------
# Groups
#------------------------------------------------------------------------------
def get_groups_for_user(uid):
    user_info = get_user_info(uid)
    if user_info is None:
        return None
    if group is not None:
        return None
    groups = user_info['group']
    group_list = groups.split(' ')
    return group_list
