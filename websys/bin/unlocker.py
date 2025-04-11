#==============================================================================
# Force Unlocker
# Copyright (c) 2024 Takashi Harano
#==============================================================================
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import websysconf

sys.path.append(websysconf.UTIL_PATH)
import util

def force_unlock():
    path = websysconf.LOCK_FILE_PATH

    deleted = False
    if os.path.exists(path):
        deleted = util.file_unlock(path)
        if deleted:
            status = 'OK'
        else:
            status = 'NG'
    else:
        status = 'NO_LOCK_FILE'

    util.send_response(status)
