#==============================================================================
# Web System Management Screen
# Copyright (c) 2023 Takashi Harano
#==============================================================================
import os
import sys

ROOT_PATH = '../../'

sys.path.append(os.path.join(os.path.dirname(__file__), ROOT_PATH + 'libs'))
import util

util.append_system_path(__file__, ROOT_PATH + '/websys')
import websys

import js

#------------------------------------------------------------------------------
def build_main_screen(context):
    html = '''<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="robots" content="none">
<meta name="referrer" content="no-referrer">
<meta name="referrer" content="never">
<meta name="viewport" content="width=device-width,initial-scale=1">
'''
    html += '<title>WebSys</title>'
    html += '<link rel="stylesheet" href="style.css" />'
    html += '<script src="' + ROOT_PATH + 'libs/sha.js"></script>'
    html += '<script src="' + ROOT_PATH + 'libs/debug.js"></script>'
    html += '<script src="' + ROOT_PATH + 'libs/util.js"></script>'
    html += '<script src="' + ROOT_PATH + 'websys/websys.js"></script>'
    html += '<script src="sysmgr.js"></script>'
    html += '''<script src="./?res=js"></script>
</head>
<body>
<div id="body1">

<div style="margin-top:4px;margin-bottom:4px;">
<b>Users</b><br>
<button onclick="sysmgr.newUser();">+</button>
<button onclick="sysmgr.reloadUserInfo();">Reload</button>
<span style="margin-left:16px;">Search: <input type="text" id="search-text" style="width:150px;" oninput="scnjs.onSearchInput(this);"></span><span style="margin-left:8px;"><input type="checkbox" id="search-filter" onchange="scnjs.onFilterChange();" checked><label for="search-filter">Filter</label></span>
<span id="letter-case-button" class="pseudo-link link-button" style="margin-left:16px;" onclick="scnjs.toggleLetterCase();"><span id="uc">A</span><span id="lc">a</span></span>
</div>
<div id="user-list" style="width:100%;max-height:400px;overflow:auto;"></div>

<pre style="margin-top:10px;"><span>Sessions</span><span style="margin-left:24px;"><span id="clock"></span></span>
<div id="session-list" style="width:100%;max-height:250px;overflow:auto;"></div></pre>

<div style="display:inline-block;margin-top:20px;margin-bottom:40px;">
<div style="margin-bottom:4px;">
<b>Groups</b><br>
<button onclick="sysmgr.newGroup();">+</button>
<button onclick="sysmgr.getGroupList();">Reload</button>
<span id="groups-status" style="margin-left:8px;"></span><br>
</div>
<div id="group-list" style="width:100%;max-height:300px;overflow:auto;"></div>
</div>

</div>
</body>
</html>'''
    return html

#------------------------------------------------------------------------------
def build_forbidden_screen(context):
    html = '''<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="robots" content="none">
<meta name="referrer" content="no-referrer">
<meta name="referrer" content="never">
<meta name="viewport" content="width=device-width,initial-scale=1">
'''
    html += '<title>WebSys</title>'
    html += '<link rel="stylesheet" href="style.css" />'
    html += '<script src="' + ROOT_PATH + 'libs/debug.js"></script>'
    html += '<script src="' + ROOT_PATH + 'libs/util.js"></script>'
    html += '<script src="' + ROOT_PATH + 'websys/websys.js"></script>'
    html += '''
</head>
<body>
FORBIDDEN
</body></html>'''
    return html

#------------------------------------------------------------------------------
def build_auth_redirection_screen():
    html = '''<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="robots" content="none">
<meta name="referrer" content="no-referrer">
<meta name="referrer" content="never">
'''
    html += '<script src="' + ROOT_PATH + 'libs/debug.js"></script>'
    html += '<script src="' + ROOT_PATH + 'libs/util.js"></script>'
    html += '<script src="' + ROOT_PATH + 'websys/websys.js"></script>'
    html += '<script src="./?res=js"></script>'
    html += '''
<script>
$onLoad = function() {
  websys.authRedirection(location.href);
};
</script>
</head><body></body></html>'''
    return html

#------------------------------------------------------------------------------
def main():
    context = websys.on_access()
    res = util.get_request_param('res')
    if res == 'js':
        js.main()
        return

    if context.is_authorized():
        if context.has_permission('sysadmin'):
            html = build_main_screen(context)
        else:
            html = build_forbidden_screen(context)

    else:
        html = build_auth_redirection_screen()

    util.send_html(html)
