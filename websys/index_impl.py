#==============================================================================
# websys
# Copyright 2024 Takashi Harano
#==============================================================================
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../libs'))
import util

util.append_system_path(__file__, './bin')
import unlocker

#------------------------------------------------------------------------------
def main():
    p = util.get_request_param('unlock')
    if p == '1':
        unlocker.force_unlock()
    else:
        util.send_response('websys')
