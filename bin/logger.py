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

ALGOTRITHM = websysconf.ALGOTRITHM
LOG_FILE_PATH = websysconf.LOG_FILE_PATH

# Write Log
def write_log(data):
    util.append_line_to_text_file(LOG_FILE_PATH, data, max=1000)

#----------------------------------------------------------
# Read log
#---------------------------------------------------------
def get_login_log():
    return util.read_text_file_as_list(LOG_FILE_PATH)

