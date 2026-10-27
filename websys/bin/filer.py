#==============================================================================
# Filer
# Copyright 2023 Takashi Harano
# Released under the MIT License
#==============================================================================
import os
import sys
import re

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import websysconf
import websys

sys.path.append(websysconf.UTIL_PATH)
import util
import dirlist
import file

PROTECT_EXTENSIONS = ('.cgi', '.py', '.pyc', '.so', '.pyd', '.php', '.pl', '.sh')

#------------------------------------------------------------------------------
def convert_to_safe_file_path(filename):
    if not isinstance(filename, str) or not filename or filename.startswith('.'):
        return None

    if any(c in filename for c in '/\\:<>"|?*'):
        return None

    if any(ord(c) < 32 or ord(c) == 127 for c in filename):
        return None

    if filename.endswith(('.', ' ')):
        return None

    name = filename.split('.', 1)[0].rstrip(' ').upper()
    if name in ('CON', 'PRN', 'AUX', 'NUL', 'CONIN$', 'CONOUT$'):
        return None
    if re.fullmatch(r'(COM|LPT)[1-9¹²³]', name):
        return None

    base_dir = os.path.realpath(os.getcwd())
    path = os.path.join(base_dir, filename)

    if os.path.islink(path):
        return None

    if os.path.dirname(os.path.realpath(path)) != base_dir:
        return None

    if os.path.isdir(path):
        return None

    return path

#------------------------------------------------------------------------------
def save_file():
    multi_prt_data = util.get_multipart_data()

    if not multi_prt_data or 'file' not in multi_prt_data:
        return 'NO_FILE_FIELD'

    item = multi_prt_data['file']
    content = item['body']
    filename = item['disposition'].get('filename', '')

    if not content or not filename:
        return 'NO_FILE_CONTENT'

    if filename.lower().endswith(PROTECT_EXTENSIONS):
        filename += '.txt'

    filepath = convert_to_safe_file_path(filename)

    if filepath is None:
        return 'INVALID_FILENAME'

    try:
        util.write_file(filepath, content, make_dir=False)
        status = 'OK'
    except OSError:
        status = 'WRITE_FAILED'

    return status

#------------------------------------------------------------------------------
def handle_multipart_form_data(root_path, target_path, auth_required, can_write):
    if not can_write or not websys.is_valid_api_request():
        util.send_response('FORBIDDEN', status=403)
        return

    result = save_file()
    dirlist.dir_list(root_path, target_path, auth_required=auth_required, upload=can_write, info=result)

#------------------------------------------------------------------------------
# main
#------------------------------------------------------------------------------
def main(root_path, target_path, auth_required, upload=False):
    websys.set_root_path(root_path)
    context = websys.on_access()

    can_write = upload and context.is_authorized() and context.has_permission('sysadmin')
    content_type = os.environ.get('CONTENT_TYPE', '')

    if content_type.startswith('multipart/form-data'):
        handle_multipart_form_data(root_path, target_path, auth_required, can_write)
        return

    file_path = util.get_request_param('file')

    if file_path is None:
        dirlist.dir_list(root_path, target_path, auth_required=auth_required, upload=can_write, info='')
        return

    safe_path = convert_to_safe_file_path(file_path)

    if safe_path is None:
        util.send_response('FORBIDDEN', status=403)
        return

    mode = util.get_request_param('mode')

    if mode == 'delete':
        if not can_write or not websys.is_valid_api_request():
            util.send_response('FORBIDDEN', status=403)
            return

        if not os.path.isfile(safe_path):
            util.send_response('NOT_FOUND', status=404)
            return

        util.delete(safe_path)
        dirlist.dir_list(root_path, target_path, auth_required=auth_required, upload=can_write, info='Deleted')
        return

    if not os.path.isfile(safe_path):
        util.send_response('NOT_FOUND', status=404)
        return

    file.main(root_path, file_path, auth_required=auth_required)
