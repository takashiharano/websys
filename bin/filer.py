import os
import sys

import websysconf
sys.path.append(websysconf.UTIL_PATH)
import util
import dirlist
import file
import web

#----------------------------------------------------------
# main
#----------------------------------------------------------
def main(root_path, target_path, auth_required, upload):
    web.set_root_path(root_path)

    form = None
    content_type = os.environ.get('CONTENT_TYPE', '')
    if content_type.startswith('multipart/form-data'):
        form = util.get_field_storage()

    if form is None:
        file_path = util.get_request_param('file')
        if file_path is None:
            dirlist.dir_list(root_path, target_path, auth_required=auth_required, upload=upload, info='')
        else:
            file.main(root_path, file_path, auth_required=auth_required)
    else:
        save_dir = './'
        result = save_file(form, save_dir)
        dirlist.dir_list(root_path, target_path, auth_required=auth_required, upload=upload, info=result)

def save_file(form, save_dir):
    if 'file' in form:
        item = form['file']
        content = item.file
        filename = item.filename
        if content and filename:
            filepath = save_dir + filename
            try:
                util.write_file(filepath, content)
                result = 'OK'
            except Exception as e:
                result = str(e)
        else:
            result = 'NO_FILE_CONTENT'
    else:
        result = 'NO_FILE_FIELD'

    return result
