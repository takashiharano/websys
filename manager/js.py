import os
import sys

ROOT_PATH = '../..'

sys.path.append(os.path.join(os.path.dirname(__file__), ROOT_PATH + '/libs'))
import util

util.append_system_path(__file__, ROOT_PATH + '/websys')
import websysconf
import websys

#------------------------------------------------------------------------------
def build_js(context):
    js = 'var sysmgr = sysmgr || {};'
    js += 'sysmgr.websysconf = {'
    js += 'LOGIN_FAILURE_MAX: ' + str(websysconf.LOGIN_FAILURE_MAX)
    js += '};'
    js += 'websys.init(\'' + ROOT_PATH + '/\', sysmgr.onSysReady);'
    return js

#------------------------------------------------------------------------------
def main():
    context = websys.on_access()
    js = build_js(context)
    util.send_response(js, 'text/javascript')
