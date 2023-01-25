#==============================================================================
# DIR List
# Copyright (c) 2020 Takashi Harano
#==============================================================================
import util
import authman
import web

ALLOW_GUESTS = True

# dir list
def dir_list(root_path, self_path, auth_required=False, upload=False, info=''):
    web.on_access()
    if auth_required and not authman.auth(allow_guest=ALLOW_GUESTS):
        web.redirect_auth_screen()
        return

    dir_info = util.get_dir_info('.', recursive=1)
    dir_list = dir_info['children']

    dirs = []
    files = []
    for key in dir_list:
        item = dir_list[key]
        if item['isdir']:
            dirs.append(key)
        else:
            files.append(key)

    dirs.sort()
    files.sort()

    html = '''<!DOCTYPE html>
<html>
<head>
<meta http-equiv="X-UA-Compatible" content="IE=Edge">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>File List</title>
<style>
body {
  background: #000;
  color: #ddd;
  font-size: 18px;
  font-family: Consolas, Monaco, Menlo, monospace, sans-serif;
  line-height: 1.2em;
}

a {
  color: #fff;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

.dir {
  color: #0ff;
}

.hidden-file {
  color: #00f;
}

.src {
  margin-left: 4px;
  font-size: 12px;
}

.frame {
  width: calc(100vw - 34px);
  height: calc(100vh - 34px);
  min-width: 960px;
  min-height: 800px;
  margin: 4px;
  padding: 6px;
  border: 1px solid #0ff;
  border-radius: 4px;
}

.pseudo-button:hover {
  cursor: pointer;
  text-decoration: underline;
}

.reload-button {
  margin: 0 16px;
  color: #0ff;
}

.delete-button {
  margin-left: 16px;
  color: #f88;
}

#clock {
  color: #0f0;
}
</style>
<script>
var fm = {};
fm.WDAYS = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
fm.onReady = function() {
  fm.clock = document.getElementById('clock');
  fm.updateClock();
};
fm.updateClock = function() {
  var dt = new Date();
  var year = dt.getFullYear();
  var month = dt.getMonth() + 1;
  var day = dt.getDate();
  var hours = dt.getHours();
  var minutes = dt.getMinutes();
  var seconds = dt.getSeconds();
  var milliseconds = dt.getMilliseconds();

  var yyyy = year + '';
  var mm = ('0' + month).slice(-2);
  var dd = ('0' + day).slice(-2);
  var hh = ('0' + hours).slice(-2);
  var mi = ('0' + minutes).slice(-2);
  var ss = ('0' + seconds).slice(-2);
  var sss = ('00' + milliseconds).slice(-3);
  var wday = dt.getDay();
  var w = fm.WDAYS[wday];

  var clock = yyyy + '-' + mm + '-' + dd + ' ' + w + ' ' + hh + ':' + mi + ':' + ss;
  fm.clock.innerText = clock;
  setTimeout(fm.updateClock, 500);
};
fm.delete = function(file) {
  var f = confirm('Delete?');
  if (f) {
    var p = {mode: 'delete', file: file};
    util.postSubmit('./', p);
  }
};
window.addEventListener('DOMContentLoaded', fm.onReady, true);
var util = {};
util.submit = function(url, method, params, uriEnc) {
  var form = document.createElement('form');
  form.action = url;
  form.method = method;
  for (var key in params) {
    var input = document.createElement('input');
    var val = params[key];
    if (uriEnc) val = encodeURIComponent(val);
    input.type = 'hidden';
    input.name = key;
    input.value = val;
    form.appendChild(input);
  }
  document.body.appendChild(form);
  form.submit();
};

util.postSubmit = function(url, params, uriEnc) {
  util.submit(url, 'POST', params, uriEnc);
};
</script>
</head>
<body>
<div class="frame">
<div>
  <span id="clock">---------- --- --:--:--</span>
  <span class="reload-button pseudo-button" onclick="location.href='./'">RELOAD</span>
'''
    if upload:
        html += '''
  <div style="display:inline-block;">
    <form action="./" method="POST" enctype="multipart/form-data">
      <input type="hidden" name="mode" value="upload">
      <input type="file" name="file"><input type="submit" value="Upload">
    </form>
  </div>
'''
    html += '  <div style="display:inline-block;">'
    html += '<span>' + info + '</span>'
    html += '''
  </div>
</div>
<a href="../" class="dir">..</a><br>
'''
    html += '<table>'
    for i in range(len(dirs)):
        key = dirs[i]
        item = dir_list[key]
        html += dir_item(item)

    for i in range(len(files)):
        key = files[i]
        item = dir_list[key]
        filename = item['filename']
        if filename == util.get_filename(self_path):
            continue
        else:
            html += dir_item(item, upload)

    html += '</table>'
    html += '''
</div>
</body>
</html>'''

    web.send_response('html', html)

# is hidden file name
def is_hidden(name):
    return util.match(name, r'^\.') or util.match(name, r'^__.*__$')

# dir item
def dir_item(info, delete_enable):
    name = info['filename']
    ext = util.get_file_ext(name)

    class_name = ''
    if is_hidden(name):
        class_name = 'hidden-file'
    if info['isdir']:
        class_name += ' dir'

    html = ''
    html += '<tr'
    if class_name != '':
        html += ' class="' + class_name + '"'
    html += '>'
    html += '<td>'

    filename = ''
    with_a_tag = False
    if not is_hidden(name):
        if info['isdir']:
            with_a_tag = True
            filename += '<a href="' + name + '"'
        elif ext == 'html':
            with_a_tag = True
            filename += '<a href="' + name + '"'
        else:
            with_a_tag = True
            filename += '<a href="./?file=' + name + '"'

        if class_name != '':
            filename += ' class="' + class_name + '"'

        filename += '>'

    filename += name

    if with_a_tag:
        filename += '</a>'

    src_link = ''
    if ext == 'html' or ext == 'py':
        src_link += '<a href="./?file=' + name + '" class="src">[SRC]</a>'

    html += filename
    html += src_link
    html += '</td>'

    html += '<td align="right" style="padding-left:10px;">'
    if info['isdir']:
        html += '&lt;DIR&gt;'
    else:
        html += '{:,d}'.format(info['size'])

        if delete_enable:
            html += '<span class="delete-button pseudo-button" onclick="fm.delete(\'' + name + '\');">X</span>'

    html += '</td>'
    html += '<td style="padding-left:10px;">' + util.get_datetime_str(info['mtime'], fmt='%Y-%m-%d %H:%M:%S') + '</td>'
    html += '</tr>'
    return html
