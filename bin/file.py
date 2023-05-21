#==============================================================================
# File Viewer
# Copyright (c) 2020 Takashi Harano
#==============================================================================
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import websysconf

sys.path.append(websysconf.UTIL_PATH)
import util
import bsb64

import authman
import web

TXT_EXT = ['bas', 'bat', 'c', 'css', 'html', 'java', 'js', 'log', 'ps1', 'sh', 'txt', 'xml']

# is text file
def is_text_file(filename):
    ext = util.get_file_ext(filename)
    for i in range(len(TXT_EXT)):
        if TXT_EXT[i] == ext:
            return True
    return False

def output_text_file(root_path, path):
    n = 7
    content = util.read_file(path, 't')
    enc_content = bsb64.encode_string(content, n)
    html = '<html><head><meta charset="utf-8">'
    html += '<script src="' + root_path + 'libs/util.js"></script>'
    html += '<style>body,pre{font-size:13px;font-family:Consolas,Monaco,Menlo,monospace,sans-serif;}</style>'
    html += '<script>'
    html += 'var c=\'' + enc_content + '\';'
    html += 'onReady=function(){'
    html += 'var d=util.decodeBSB64;'
    html += 'var a=d(c,' + str(n) + ');'
    html += 'a=util.escHtml(a);'
    html += 'document.getElementById(\'t\').innerHTML=a;'
    html += '};window.addEventListener(\'DOMContentLoaded\',onReady,true);'
    html += '</script></head><body><pre id="t"></pre></body></html>'
    web.send_response(html, 'text/html')

def main(root_path, path, allow_guest=False, auth_required=True):
    web.on_access()
    if auth_required and  not authman.auth(allow_guest=allow_guest):
        util.send_response('FORBIDDEN')
    else:
        if is_text_file(path):
            output_text_file(root_path, path)
        else:
            headers = [
                {'Location': path}
            ]
            util.send_response('FILE', status=302, headers=headers)
