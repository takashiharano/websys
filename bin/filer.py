#==============================================================================
# Filer
# Copyright (c) 2023 Takashi Harano
#==============================================================================
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import websysconf
import websys

sys.path.append(websysconf.UTIL_PATH)
import util
import dirlist
import file

#----------------------------------------------------------
# main
#----------------------------------------------------------
def main(root_path, target_path, auth_required, upload=False):
    websys.set_root_path(root_path)

    context = websys.on_access()

    content_type = os.environ.get('CONTENT_TYPE', '')

    if not context.is_authorized():
        upload = False

    if content_type.startswith('multipart/form-data'):
        save_dir = './'
        result = save_file(save_dir)
        dirlist.dir_list(root_path, target_path, auth_required=auth_required, upload=upload, info=result)
    else:
        file_path = util.get_request_param('file')
        if file_path is None:
            dirlist.dir_list(root_path, target_path, auth_required=auth_required, upload=upload, info='')
        else:
            mode = util.get_request_param('mode')
            if mode == 'delete':
                util.delete(file_path)
                dirlist.dir_list(root_path, target_path, auth_required=auth_required, upload=upload, info='Deleted')
            else:
                file.main(root_path, file_path, auth_required=auth_required)

def save_file(save_dir):
    multi_prt_data = util.get_multipart_data()
    if 'file' in multi_prt_data:
        item = multi_prt_data['file']
        content = item['body']
        disposition = item['disposition']
        filename = disposition['filename']
        if content and filename:
            if filename.endswith('.cgi'):
                filename += '.txt'
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
