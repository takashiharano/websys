import os
import sys

UTIL_PATH = os.path.join(os.path.dirname(__file__), '../libs')
sys.path.append(UTIL_PATH)
import util

SESSION_TIMEOUT_SEC = 7 * util.DAY
DATA_DIR = util.get_relative_path(__file__, '../../private/websys')
LOCK_FILE_PATH = DATA_DIR + '/lock'
USER_ROOT_PATH = DATA_DIR + '/users'
USER_LIST_FILE_PATH = DATA_DIR + '/users.json'
GUEST_USER_LIST_FILE_PATH = DATA_DIR + '/users_guest.json'
PASSWORD_LIST_FILE_PATH = DATA_DIR + '/userspw.txt'
GROUPS_FILE_PATH = DATA_DIR + '/groups.json'
LOG_FILE_PATH = DATA_DIR + '/logs/websys.log'

ALGOTRITHM = 'SHA-256'
USE_HOSTNAME = True
