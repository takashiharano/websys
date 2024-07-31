#==============================================================================
# Logger
# Copyright (c) 2023 Takashi Harano
#==============================================================================
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import websysconf

sys.path.append(websysconf.UTIL_PATH)
import util
import web

LOG_FILE_PATH = websysconf.LOG_FILE_PATH

#----------------------------------------------------------
# Read log
def get_system_log():
    return util.read_text_file_as_list(LOG_FILE_PATH)

#----------------------------------------------------------
# Write Log
def write_log(data):
    util.append_line_to_text_file(LOG_FILE_PATH, data, max=1000)

#----------------------------------------------------------
def write_status_log(op_type, status, uid, addr, host, ua, sid, info=''):
    now = util.get_timestamp()
    date_time = util.get_datetime_str(now, fmt='%Y-%m-%dT%H:%M:%S.%f')
    data = date_time
    data += '\t'
    data += str(now)
    data += '\t'
    data += op_type
    data += '\t'
    data += status
    data += '\t'
    data += uid
    data += '\t'
    data += addr
    data += '\t'
    data += host
    data += '\t'
    data += ua
    data += '\t'
    data += sid
    data += '\t'
    data += info
    write_log(data)

#----------------------------------------------------------
def write_event_log(context, op_type, status, info):
    user_info = context.get_user_info()
    uid = user_info['uid']
    addr = web.get_ip_addr()
    host = web.get_host_name()
    ua = web.get_user_agent()
    sid = context.get_session_id()
    write_status_log(op_type, status, uid, addr, host, ua, sid, info)

#----------------------------------------------------------
def write_system_log(status, uid, info):
    info = util.replace(info, '\t', '  ');
    write_status_log('SYSTEM', status, uid, addr='-', host='-', ua='-', sid='-', info=info)
