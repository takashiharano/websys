#==============================================================================
# Web System Management Screen
# Copyright (c) 2023 Takashi Harano
#==============================================================================
import os
import sys

ROOT_PATH = '../../'

sys.path.append(os.path.join(os.path.dirname(__file__), ROOT_PATH + 'libs'))
import util

util.append_system_path(__file__, ROOT_PATH)
util.append_system_path(__file__, '../bin')
import web
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
    html += '<script src="sysman.js"></script>'
    html += '''<script src="./?res=js"></script>
</head>
<body>
<div id="body1">

<div style="margin-bottom:4px;">
<button onclick="sysman.newUser();">+</button>
<button onclick="sysman.reload();">RELOAD</button>
</div>
<div id="user-list"></div>

<pre style="margin-top:20px;">Sessions
<div id="session-list"></div></pre>

<div style="margin-top:40px;">
Groups<button style="margin-left:8px;" onclick="sysman.confirmSaveGroups();">SAVE</button><span id="groups-status" style="margin-left:8px;"></span><br>
<textarea id="groups-text"></textarea>
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
    context = web.on_access()
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
