#==============================================================================
# Group Manager
# Copyright 2024 Takashi Harano
# Released under the MIT License
#==============================================================================
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import websysconf
import util
import common

GROUPS_FILE_PATH = websysconf.DATA_DIR + '/groups.tsv'

GROUP_DATA_FIELDS = [
    {'name': 'gid'},
    {'name': 'name'},
    {'name': 'privileges'},
    {'name': 'desc'},
    {'name': 'created_at', 'type': 'float'},
    {'name': 'created_by'},
    {'name': 'updated_at', 'type': 'float'},
    {'name': 'updated_by'}
]

def is_valid_gid(gid):
    return util.match(gid, r'\A[a-zA-Z0-9@._-]+\Z') and not gid.endswith('.')

# Object structure
# group
# {
#   "g1": {
#     "gid": "g1",
#     "name": "Group1",
#     "privileges": "p1 p2",
#     "desc": "foo",
#     "created_at": 1784967352.923123,
#     "created_by": "John Doe",
#     "updated_at": 1784967352.923123,
#     "updated_by": "John Doe"
#   },
#   "g2": {
#     "gid": "g2",
#     "name": "Group2",
#     "privileges": "p1",
#     "desc": "bar",
#     "created_at": 1784967352.923123,
#     "created_by": "John Doe",
#     "updated_at": 1784967352.923123,
#     "updated_by": "John Doe"
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
@common.synchronized
def add_group(gid, name='', privileges='', desc='', status=None, operator_full_name=''):
    if not is_valid_gid(gid):
        raise Exception('INVALID_GID')

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
        'privileges': privileges,
        'desc': desc,
        'created_at': now,
        'created_by': operator_full_name,
        'updated_at': now,
        'updated_by': operator_full_name
    }

    groups[gid] = group
    save_groups(groups)
    return group

# Modify a group
@common.synchronized
def modify_group(gid, name=None, privileges=None, a_privileges=None, r_privileges=None, desc=None, operator_full_name=''):
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

    if privileges is not None:
        group['privileges'] = privileges
        updated = True

    if a_privileges is not None:
        group['privileges'] = common.add_item_value(group['privileges'], a_privileges)
        updated = True

    if r_privileges is not None:
        group['privileges'] = common.remove_item_value(group['privileges'], r_privileges)
        updated = True

    if desc is not None:
        desc = util.replace(desc, '\t|\r\n|\n', ' ')
        group['desc'] = desc
        updated = True

    if updated:
        group['updated_at'] = now

    group['updated_by'] = operator_full_name

    groups[gid] = group
    save_groups(groups)

    return group

# Delete a group
@common.synchronized
def delete_group(gid):
    groups = get_all_group_info()
    if groups is None or gid not in groups:
        return False
    groups.pop(gid)
    save_groups(groups)
    return True

def get_group_privileges(gid):
    privileges = None
    group = get_group_info(gid)
    if group is not None:
        if 'privileges' in group:
            privileges = group['privileges']
    return privileges

def has_privilege_in_group(gid, privilege_name):
    group = get_group_info(gid)
    return common.has_item(group, 'privileges', privilege_name)

def has_privilege_in_groups(group_ids, privilege_name, groups=None):
    has_privilege = False

    if groups is None:
        groups = get_all_group_info()

    if groups is not None:
        for gid in group_ids:
            if gid in groups:
                group = groups[gid]
                if common.has_item(group, 'privileges', privilege_name):
                    has_privilege = True
                    break

    return has_privilege

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
