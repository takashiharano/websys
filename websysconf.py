import os
import sys

UTIL_PATH = os.path.join(os.path.dirname(__file__), '../libs')
sys.path.append(UTIL_PATH)
import util

ANONYMOUS_SESSION_PERIOD_SEC = 31536000
SESSION_TIMEOUT_SEC = 7 * util.DAY
MAX_SESSIONS_PER_USER = 10
LOGIN_FAILURE_MAX = 10
LOGIN_LOCK_PERIOD_SEC = 180
PW_RESET_LOGIN_EXPIRE_SEC = 7 * util.DAY
DATA_DIR = util.get_relative_path(__file__, '../../private/websys')
LOCK_FILE_PATH = DATA_DIR + '/lock'
USER_ROOT_PATH = DATA_DIR + '/users'
PASSWORD_LIST_FILE_PATH = DATA_DIR + '/userspw.txt'
GROUPS_FILE_PATH = DATA_DIR + '/groups.txt'
LOG_FILE_PATH = DATA_DIR + '/logs/websys.log'

ALGOTRITHM = 'SHA-256'
USE_HOSTNAME = True
