import os
import sys

LIBS_DIR = 'libs'
LIBS_PATH = os.path.join(os.path.dirname(__file__), '..', LIBS_DIR)
LIBS_URL_PATH = LIBS_DIR + '/'
sys.path.append(LIBS_PATH)
import util

CSRF_ALLOWED_ORIGIN = 'http://localhost'

SESSION_COOKIE_NAME = 'sid'
ANONYMOUS_SESSION_PERIOD_SEC = 31536000
SESSION_TIMEOUT_SEC = 7 * util.DAY
MAX_SESSIONS_PER_USER = 10
LOGIN_FAILURE_MAX = 10
LOGIN_LOCK_PERIOD_SEC = 180
PW_RESET_LOGIN_EXPIRE_SEC = 7 * util.DAY
DATA_DIR = util.get_relative_path(__file__, '../../private/websys')
LOCK_FILE_PATH = DATA_DIR + '/lock'
USER_ROOT_PATH = DATA_DIR + '/users'
LOG_DIR_PATH = DATA_DIR + '/logs'
LOG_FILE_PATH = LOG_DIR_PATH + '/websys.log'
USE_HOSTNAME = True
ALGOTRITHM = 'SHA-256'

PASSWORD_BLACKLIST = (
    'pass1234',
    'password',
    'password123',
    'password1234',
    '12345678',
    'qwerty123'
)
