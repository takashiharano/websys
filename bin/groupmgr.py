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

GROUP_DATA_FIELDS = [
    {'name': 'gid'},
    {'name': 'name'},
    {'name': 'privs'},
    {'name': 'desc'},
    {'name': 'created_at', 'type': 'float'},
    {'name': 'updated_at', 'type': 'float'}
]

# Object structure
# group
# {
#   "g1": {
#     "gid": "g1",
#     "name": "Group1",
#     "privs": "p1 p2",
#     "desc": "foo"
#   },
#   "g2": {
#     "gid": "g2",
#     "name": "Group2",
#     "privs": "p1",
#     "desc": "bar"
#   },
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
    groups = load_all_groups(GROUPS_FILE_PATH, GROUP_DATA_FIELDS)
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
def add_group(gid, name='', privs='', desc='', status=None):
    groups = get_all_group_info()
    if groups is None:
        groups = {}
    elif gid in groups:
        raise Exception('ALREADY_EXISTS')

    now = util.get_timestamp()
    desc = util.replace(desc, '\t|\r\n|\n', ' ')

    group = {
        'gid': gid,
        'name': name,
        'privs': privs,
        'desc': desc,
        'created_at': now,
        'updated_at': now
    }

    groups[gid] = group
    save_groups(groups)
    return group

# Modify a group
def modify_group(gid, name=None, privs=None, aprivs=None, rprivs=None, desc=None):
    now = util.get_timestamp()

    groups = get_all_group_info()
    if groups is None:
        groups = {}
    elif gid not in groups:
        raise Exception('NOT_EXISTS')

    group = groups[gid]

    updated = False
    if name is not None:
        group['name'] = name
        updated = True

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

#------------------------------------------------------------------------------
# Load Groups
def load_all_groups(path, data_fields_def):
    tsv_text_list = util.read_text_file_as_list(path)
    obj = {}
    for i in range(len(tsv_text_list)):
        text_line = tsv_text_list[i]
        if not util.is_comment(text_line, '#'):
            result = common.parse_tsv_field_values(text_line, data_fields_def, path)
            data = result['values']
            gid = data['gid']
            obj[gid] = data
    return obj

# Save Groups
def save_groups(groups):
    common.save_to_tsv_file(GROUPS_FILE_PATH, groups, GROUP_DATA_FIELDS)
