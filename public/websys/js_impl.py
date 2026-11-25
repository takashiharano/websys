#==============================================================================
# Web System - JavaScript Generator
# Copyright 2026 Takashi Harano
# Released under the MIT License
#==============================================================================
import os
import websysconf
import util

def main():
    js_path = os.path.join(os.path.dirname(__file__), 'websys.js')
    js = util.read_text_file(js_path)

    default_http_scramble = 'true' if websysconf.DEFAULT_HTTP_SCRAMBLE else 'false'
    js += 'websys.defaultHttpScramble = ' + default_http_scramble + ';\n'
    js += 'websys.requestScrambleKey = \'' + websysconf.SCRAMBLE_KEY_1 + '\';\n'
    js += 'websys.responseScrambleKey = \'' + websysconf.SCRAMBLE_KEY_2 + '\';\n'

    util.send_response(js, 'text/javascript')
