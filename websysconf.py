import os
import sys

UTIL_PATH = os.path.join(os.path.dirname(__file__), '../libs')
sys.path.append(UTIL_PATH)
import util

SESSION_TIMEOUT_SEC = 7 * util.DAY
DATA_DIR = util.get_relative_path(__file__, '../../private/websys/')
LOCK_FILE_PATH = DATA_DIR + 'lock'
USER_LIST_FILE_PATH = DATA_DIR + 'users.json'
GUEST_USER_LIST_FILE_PATH = DATA_DIR + 'users_guest.json'
PASSWORD_LIST_FILE_PATH = DATA_DIR + 'userspw.txt'
SESSION_LIST_FILE_PATH = DATA_DIR + 'sessions.json'
ALGOTRITHM = 'SHA-256'
LOGIN_LOG_PATH = DATA_DIR + 'logs/login.log'

USE_HOSTNAME = True
