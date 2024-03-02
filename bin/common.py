#==============================================================================
# Common logic
# Copyright (c) 2024 Takashi Harano
#==============================================================================
import os
import sys
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import websysconf

sys.path.append(websysconf.UTIL_PATH)
import util

import logger

def has_item(obj, key, value):
    if obj is None:
        return False

    if key not in obj:
        return False

    items = obj[key]
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

def add_item_value(items, aitems):
    for item in aitems:
        items = util.add_item_value(items, item, separator=' ')
    return items

def remove_item_value(items, ritems):
    for item in ritems:
        items = util.remove_item_value(items, item, separator=' ')
    return items

def load_dict(path, default=None):
    if not util.path_exists(path):
        return get_default_dict_value(default)

    s = util.read_text_file(path).strip()
    if s == '':
        return get_default_dict_value(default)

    try:
        o = json.loads(s)
    except Exception as e:
        logger.write_system_log('ERROR', '-', 'common.load_dict(): path=' + path + ' : ' + str(e))
        write_error_file(s)
        if s.endswith('}}'):
            s = s[:-1]
            o = json.loads(s)
        else:
            raise e

    return o

def get_default_dict_value(default):
    ret = default
    if util.typename(default) == 'dict' or util.typename(default) == 'list':
        ret = default.copy()
    return ret

def write_error_file(s):
    path = websysconf.DATA_DIR + '/error.txt'
    t = util.get_datetime_str()
    s = '---\n[' + t + ']\n' + s
    util.append_text_file(path, s)
