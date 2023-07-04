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

import sessionman

USER_LIST_FILE_PATH = websysconf.USER_LIST_FILE_PATH
GUEST_USER_LIST_FILE_PATH = websysconf.GUEST_USER_LIST_FILE_PATH

U_ST_DISABLED = 1
U_ST_RESTRICTED = 1 << 1

# users.json
# {
#   "root": {
#     "uid": "root",
#     "name": "root",
#     "local_name": "root_L",
#     "is_admin": true,
#     "group": "GROUP1 GROUP2",
#     "privs": "PRIVILEGE1 PRIVILEGE2"
#     "created_at": 1667047612.967891,
#     "updated_at": 1667047612.967891,
#     "status": 0
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
#     "is_guest": true,
#     "created_at": 1667047612.967891,
#     "updated_at": 1667047612.967891,
#     "expires_at": 1571476916.59936
#     "status": 0,
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
def get_all_user_info():
    users = util.load_dict(USER_LIST_FILE_PATH)
    return users

# Create a user
# pw: SHA-256(SHA-256(pw + uid))
def create_user(uid, pw, name=None, local_name=None, is_admin=False, group='', privs='', status='0'):
    users = get_all_user_info()
    if users is None:
        users = {}
    elif uid in users:
        raise Exception('ALREADY_EXISTS')

    now = util.get_timestamp()
    u_status = parse_int(status)

    user = {
        'uid': uid,
        'name': name,
        'local_name': local_name,
        'is_admin': is_admin,
        'group': group,
        'privs': privs,
        'created_at': now,
        'updated_at': now,
        'status': u_status
    }

    users[uid] = user
    save_users(users)
    save_user_password(uid, pw)
    return user

# Modify a user
def modify_user(uid, pw=None, name=None, local_name=None, is_admin=None, group=None, agroup=None, rgroup=None, privs=None, aprivs=None, rprivs=None, status=None):
    users = get_all_user_info()
    if users is None:
        users = {}
    elif uid not in users:
        raise Exception('NOT_EXISTS')

    user = users[uid]

    if name is not None:
        user['name'] = name

    if local_name is not None:
        user['local_name'] = local_name

    if group is not None:
        user['group'] = group

    if agroup is not None:
        user['group'] = _add_item_value(user['group'], agroup)

    if rgroup is not None:
        user['group'] = _remove_item_value(user['group'], rgroup)

    if privs is not None:
        user['privs'] = privs

    if aprivs is not None:
        user['privs'] = _add_item_value(user['privs'], aprivs)

    if rprivs is not None:
        user['privs'] = _remove_item_value(user['privs'], rprivs)

    if is_admin is not None:
        user['is_admin'] = is_admin

    if status is not None:
        try:
            u_status = int(status)
            user['status'] = u_status
        except:
            pass

    now = util.get_timestamp()
    user['updated_at'] = now

    users[uid] = user
    save_users(users)

    if pw is not None:
        save_user_password(uid, pw)

    return user

def _add_item_value(items, aitems):
    for item in aitems:
        items = util.add_item_value(items, item, separator=' ')
    return items

def _remove_item_value(items, ritems):
    for item in ritems:
        items = util.remove_item_value(items, item, separator=' ')
    return items

# Delete a user
def delete_user(uid):
    users = get_all_user_info()
    if users is None or uid not in users or uid == 'root':
        return False
    sessionman.clear_user_sessions(uid)
    users.pop(uid)
    save_users(users)
    delete_user_password(uid)
    return True

# Save Users
def save_users(users):
    util.save_dict(USER_LIST_FILE_PATH, users, indent=2)

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
def create_guest(uid=None, uid_len=6, valid_min=30, group=[], privs=''):
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

    now = util.get_timestamp()
    expires_at = now + valid_min * 60
    user = {
        'uid': new_uid,
        'name': name,
        'local_name': local_name,
        'group': group,
        'privs': privs,
        'is_guest': True,
        'created_at': now,
        'updated_at': now,
        'expires_at': expires_at,
        'status': 0
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
    sessionman.clear_user_sessions(uid)
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
    return _has_item(user_info, 'group', group_name)

#----------------------------------------------------------
# has_privilege
# priv_name: case-insensitive
#----------------------------------------------------------
def has_privilege(user_info, priv_name):
    return _has_item(user_info, 'privs', priv_name)

#----------------------------------------------------------
def _has_item(user_info, key, value):
    if user_info is None:
        return False

    if is_admin(user_info):
        return True

    items = user_info[key]
    items = items.split(' ')
    if value in items:
        return True

    last_index = value.rfind('.')
    if last_index == -1:
        if _has_any_item_for_domain(items, value):
            return True
    else:
        if _has_item_by_domain(items, value):
            return True

    return False

def _has_any_item_for_domain(item_list, domain_name):
    for value in item_list:
        if value == domain_name:
            return True
        last_index = value.rfind('.')
        if last_index != -1:
            domain = value[:last_index]
            if domain == domain_name:
                return True
    return False

def _has_item_by_domain(item_list, value):
    for item in item_list:
        if item == value:
            return True

        last_index = value.rfind('.')
        if last_index != -1:
            domain = value[:last_index]
            if item == domain:
                return True

    return False

#------------------------------------------------------------------------------
# Password
#------------------------------------------------------------------------------
def get_password_list():
    path = websysconf.PASSWORD_LIST_FILE_PATH
    pw_list = util.read_text_file_as_list(path)
    return pw_list

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
# User Status
#------------------------------------------------------------------------------
def is_disabled(user_info):
    return check_user_status(user_info, U_ST_DISABLED)

def check_user_status(user_info, st):
    u_status =  '0'
    if 'status' in user_info:
        u_status =  user_info['status']
    i_status = parse_int(u_status)
    if i_status & st:
        return True
    return False

def parse_int(s):
    v = 0
    try:
        v = int(s)
    except:
        pass
    return v
