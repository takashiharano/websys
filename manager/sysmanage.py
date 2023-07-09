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

#------------------------------------------------------------------------------
def is_authorized(context):
    if context['authorized']:
        return True
    return False

def has_permission(context, target_priv):
    return web.has_permission(context, target_priv)

