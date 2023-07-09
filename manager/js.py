import os
import sys

ROOT_PATH = '../../'

sys.path.append(os.path.join(os.path.dirname(__file__), ROOT_PATH + 'libs'))
import util

util.append_system_path(__file__, ROOT_PATH)
util.append_system_path(__file__, ROOT_PATH + 'websys/bin')
import web

#------------------------------------------------------------------------------
def build_js(context):
    js = 'var sysman = sysman || {};'
    js += 'websys.init(\'' + ROOT_PATH + '\', sysman.onSysReady);'
    return js

#------------------------------------------------------------------------------
def main():
    context = web.on_access()
    js = build_js(context)
    util.send_response(js, 'text/javascript')
