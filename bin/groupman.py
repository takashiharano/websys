#==============================================================================
# Group Manager
# Copyright (c) 2024 Takashi Harano
#==============================================================================
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import websysconf

sys.path.append(websysconf.UTIL_PATH)
import util

import common

GROUPS_FILE_PATH = websysconf.GROUPS_FILE_PATH

# group.json
# {
#   "g1": {
#     "privs": "kb.write"
#   },
#   "g2": {
#     "privs": "kb.read kb.export"
#   }
# }

# get group info
# return None is not exist
def get_group_info(gid):
    groups = get_all_group_info()
    group = None
    if groups is not None:
        if gid in groups:
            group = groups[gid]
    return group

# get all group info
def get_all_group_info():
    groups = util.load_dict(GROUPS_FILE_PATH)
    return groups

# get all group info list
def get_group_list():
    group_list = []
    groups = get_all_group_info()
    if groups is None:
        return group_list

    for gid in groups:
        group = groups[gid]
        group_list.append(group)

    group_list = util.sort_object_list(group_list, 'gid')
    return group_list

# Add a group
def add_group(gid, privs='', desc='', status=None):
    groups = get_all_group_info()
    if groups is None:
        groups = {}
    elif gid in groups:
        raise Exception('ALREADY_EXISTS')

    now = util.get_timestamp()
    desc = util.replace(desc, '\t|\r\n|\n', ' ')

    group = {
        'gid': gid,
        'privs': privs,
        'desc': desc,
        'created_at': now,
        'updated_at': now
    }

    groups[gid] = group
    save_groups(groups)
    return group

# Modify a group
def modify_group(gid, privs=None, aprivs=None, rprivs=None, desc=None):
    now = util.get_timestamp()

    groups = get_all_group_info()
    if groups is None:
        groups = {}
    elif gid not in groups:
        raise Exception('NOT_EXISTS')

    group = groups[gid]

    updated = False
    if privs is not None:
        group['privs'] = privs
        updated = True

    if aprivs is not None:
        group['privs'] = common.add_item_value(group['privs'], aprivs)
        updated = True

    if rprivs is not None:
        group['privs'] = common.remove_item_value(group['privs'], rprivs)
        updated = True

    if desc is not None:
        desc = util.replace(desc, '\t|\r\n|\n', ' ')
        group['desc'] = desc
        updated = True

    if updated:
        group['updated_at'] = now

    groups[gid] = group
    save_groups(groups)

    return group

# Delete a group
def delete_group(gid):
    groups = get_all_group_info()
    if groups is None or gid not in groups:
        return False
    groups.pop(gid)
    save_groups(groups)
    return True

# Save Groups
def save_groups(groups):
    util.save_dict(GROUPS_FILE_PATH, groups, indent=2)

def get_group_privileges(gid):
    privs = None
    group = get_group_info(gid)
    if group is not None:
        if 'privs' in group:
            privs = group['privs']
    return privs

def has_privilege_in_group(gid, priv_name):
    group = get_group_info(gid)
    return common.has_item(group, 'privs', priv_name)
