#==============================================================================
# User Manager
# Copyright (c) 2020 Takashi Harano
#==============================================================================
import os
import sys

import config
sys.path.append(config.UTIL_PATH)
import util

import sessionman

USER_LIST_FILE_PATH = config.USER_LIST_FILE_PATH
GUEST_USER_LIST_FILE_PATH = config.GUEST_USER_LIST_FILE_PATH

# users.json
# {
#   "root": {
#     "uid": "root",
#     "attr": ["system"],
#     "roles": ["admin"],
#     "disabled": false
#   },
#   ...
# }

# users_guest.json
# {
#   "123456": {
#     "uid": "123456",
#     "name": "GUEST",
#     "attr": [
#       "guest"
#     ],
#     "roles": [],
#     "path": null | '/path/',
#     "disabled": false,
#     "expire": 1571476916.59936
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
def create_user(uid, pw, name=None, attr=[], roles=[], disabled=False):
    users = get_all_user_info()
    if users is None:
        users = {}
    elif uid in users:
        raise Exception('ALREADY_EXISTS')

    user = {
        'uid': uid,
        'name': name,
        'attr': attr,
        'roles': roles,
        'disabled': disabled
    }

    users[uid] = user
    save_users(users)
    save_user_password(uid, pw)
    return user

# Modify a user
def modify_user(uid, pw=None, name=None, attr=None, roles=None, disabled=None):
    users = get_all_user_info()
    if users is None:
        users = {}
    elif uid not in users:
        raise Exception('NOT_EXISTS')

    user = users[uid]

    if name is not None:
        user['name'] = name

    if attr is not None:
        user['attr'] = attr

    if roles is not None:
        user['roles'] = roles

    if disabled is not None:
        user['disabled'] = disabled

    users[uid] = user
    save_users(users)

    if pw is not None:
        save_user_password(uid, pw)

    return user

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
def create_guest(uid=None, uid_len=6, valid_min=30, path=None):
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

    now = util.get_timestamp()
    expire = now + valid_min * 60
    user = {
        'uid': new_uid,
        'name': 'GUEST',
        'attr': ['guest'],
        'roles': [],
        'path': path,
        'disabled': False,
        'created': now,
        'expire': expire
    }

    guest_users[new_uid] = user
    save_guest_users(guest_users)

    return new_uid

def _generate_code(code_len):
    cd = util.random_str(min=code_len, max=code_len, tbl='0123456789')
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
        if user['expire'] >= now:
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

# Has attr
def has_attr(user_info, attr):
    return attr in user_info['attr']

# Has role
def has_role(user_info, role_name):
    return role_name in user_info['roles']

#------------------------------------------------------------------------------
# Password
#------------------------------------------------------------------------------
def get_password_list():
    path = config.PASSWORD_LIST_FILE_PATH
    pw_list = util.read_text_file_as_list(path)
    return pw_list

def save_password_list(pw_list):
    path = config.PASSWORD_LIST_FILE_PATH
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
