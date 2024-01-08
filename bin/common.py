#==============================================================================
# Common logic
# Copyright (c) 2024 Takashi Harano
#==============================================================================
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import websysconf

sys.path.append(websysconf.UTIL_PATH)
import util

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
