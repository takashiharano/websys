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

def write_error_file(s):
    path = websysconf.DATA_DIR + '/error.txt'
    t = util.get_datetime_str()
    s = '---\n[' + t + ']\n' + s
    util.append_text_file(path, s)

#------------------------------------------------------------------------------
def parse_tsv_field_values(tsv_text, data_fields_def, path):
    text_values = tsv_text.split('\t')

    status = 'OK'
    values = {}
    for i in range(len(data_fields_def)):
        field = data_fields_def[i]
        key = field['name']
        data_type = 'str'
        as_true = '1'

        if 'type' in field:
            data_type = field['type']
            if 'data_type' == 'bool':
                if 'as_true' in field:
                    as_true = field['as_true']

        try:
            if len(text_values) > i:
                value = text_values[i]
            else:
                value = ''
            values[key] = util.from_text_value(value, data_type, as_true)
        except Exception as e:
            logger.write_system_log('ERROR', '-', 'common.parse_tsv_field_values() : path=' + path + ' : col=' + str(i + 1) + ' : ' + str(e) + ' : text=' + tsv_text)
            status = 'ERROR'
            values[key] = util.get_value_for_default(data_type)

    result = {
        'values': values,
        'status': status
    }

    if status != 'OK':
        write_error_file(tsv_text)

    return result

#------------------------------------------------------------------------------
def save_to_tsv_file(path, data_dict, fields):
    header = _build_data_header(fields)
    s = header + '\n'
    for data_key in data_dict:
        data = data_dict[data_key]
        for i in range(len(fields)):
            field = fields[i]
            key = field['name']
            data_type = 'str'
            if 'type' in field:
                data_type = field['type']
            if i > 0:
                s += '\t'
            if key not in data:
                value_text = ''
            else:
                value = data[key]
                value_text = util.to_value_text(value, data_type)
            s += value_text
        s += '\n'
    util.write_text_file(path, s)

def _build_data_header(fields):
    s = '#'
    for i in range(len(fields)):
        field = fields[i]
        key = field['name']
        if i > 0:
            s += '\t'
        s += key
    return s
