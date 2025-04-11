# Authentication Screen
# Copyright (c) 2023 Takashi Harano

import os
import sys

ROOT_DIR = '../'

sys.path.append(os.path.join(os.path.dirname(__file__), ROOT_DIR + 'libs'))
import util

SCREEN_TYPE = 1

def build_html():
    html = '''
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="no-referrer">
<meta name="referrer" content="never">
<script src="../libs/sha.js"></script>
<script src="../libs/util.js"></script>
<script src="../websys/websys.js"></script>
<title>Login</title>
<style>
body {
  width: calc(100% - 17px);
  height: calc(100vh - 17px);
}
body, textarea {
  background: #000;
  color: #fff;
  font-size: 12px;
  font-family: Consolas, Monaco, Menlo, monospace, sans-serif;
}
a {
  color: #08e;
}
input {
  font-size: 12px;
  border: none;
  border-bottom: solid 1px #888;
  padding: 2px;
  color: #fff;
  background: transparent;
  font-family: Consolas, Monaco, Menlo, monospace, sans-serif;
  outline: none;
}
button, input[type="button"], input[type="submit"] {
  width: 100%;
  border: none;
  border-radius: 1px;
  outline: none;
  color: #fff;
  background: #06c;
  font-size: 12px;
  transition: all 0.2s ease;
}
button:hover, input[type="button"]:hover, input[type="submit"]:hover {
  cursor: pointer;
  background: #08e;
  color: #fff;
  transition: all 0.2s ease;
}
button:disabled, input[type="button"]:disabled, input[type="submit"]:disabled {
  opacity: 0.5;
}

input {
  width: 100%;
  border: none;
  border-bottom: 1px solid #333;
  outline: none;
  font-size: 12px;
  font-family: Consolas, Monaco, Menlo, monospace, sans-serif;
}

input:-webkit-autofill {
  -webkit-transition: all 86400s;
  transition: all 86400s;
}

#wrapper {
  position: relative;
  height: calc(100vh - 17px);
}

#login {
  position: absolute;
  display: inline-block;
  width: 320px;
  height: 180px;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  margin: auto;
  text-align: center;
}
</style>
<script>
var auth = {};
auth.originUrl = '${%srcurl%}';
auth.extAuth = ${%ext_auth%};
auth.led = null;
auth.elCode = null;
auth.retryNum = 0;
auth.locking = false;
auth.uid = null;
auth.sid = null;
auth.mode = 'login';
auth.onEnterButton = function() {
  if (auth.mode == 'pwchg') {
    auth.changePw();
  } else {
    auth.login();
  }
};
auth.login = function() {
  if (auth.locking) return;
'''
    if SCREEN_TYPE == 0:
        html += '''
  var code = $el('#id').value;
  var p = code.indexOf(' ');
  var id = ((p >= 0) ? code.substring(0, p) : '');
  var pw = ((p >= 0) ? code.substring(p + 1) : '');
'''
    else:
        html += '''
  var id = $el('#id').value;
  var pw = $el('#pw').value;
'''
    html += '''
  auth.doLogin(id, pw);
  auth.showInfo('<span style="color:#888;">Please wait...</span>', 100);
};
auth.doLogin = function(id, pw) {
  auth.retryNum++;
  var hash = websys.getHash('SHA-256', pw, id);
  var param = {
    cmd: 'login',
    id: id,
    pw: hash
  };
  if (auth.extAuth) {
    param.ext_auth = 'true';
  }
  var req = {
    url: '../websys/api.cgi',
    method: 'POST',
    data: param,
    cb: auth.loginCb
  };
  websys.http(req);
};
auth.loginCb = function(xhr, res) {
  var statusMsg = xhr.status + ' ' + xhr.statusText;
  if (xhr.status == 200) {
    res = util.fromJSON(res);
    var status = res.status;
    var data = res.body;
    if (status == 'OK') {
      var sid = data.sid;
      auth.onLoginOK(sid);
    } else if (status == 'NEED_PWD_CHG') {
      sid = data.sid;
      var uid = data.uid;
      auth.changeToPwChangeScreen(uid, sid);
    } else {
      auth.onLoginNG(status);
    }
  } else {
    auth.showInfo('ERROR: ' + xhr.status);
    setTimeout(auth.clearInfo, 1500);
  }
};
auth.sid = null;
auth.onLoginOK = function(sid) {
  auth.sid = sid;
  auth.led.on('#0f0');
  auth.lock();
  var m = '<span style="color:#09f;">OK</span>';
  auth.textseq($el('#message'), m, 2, auth.onLoginOkTextSeqComplete);
};
auth.onLoginOkTextSeqComplete = function() {
  setTimeout(auth.redirect, 1000, auth.sid);
};
auth.onLoginNG = function(status) {
  auth.led.on('#f88');
  var msg = '<span style="color:#f66;">' + status + '</span>';
  auth.textseq($el('#message'), msg, 2, auth.onLoginErr);

  if (auth.retryNum >= 10) {
    auth.goodBye();
  } else if (auth.retryNum % 3 == 0) {
    auth.lockTemporary(3000);
  }
};

auth.textseq = function(el, msg, cursor, oncomplete) {
  var opt = {
    cursor: cursor,
    oncomplete: oncomplete
  };
  $el('#message').textseq(msg, opt);
};

auth.showInfo = function(m, s) {
  util.writeHTML('#message', m, s);
};
auth.clearInfo = function() {
  util.clearHTML('#message');
};

auth.onLoginErr = function() {
  setTimeout(auth._onLoginErr, 1500);
};
auth._onLoginErr = function() {
  auth.led.off();
  $el('#message').html('', 250);
};

auth.lockTemporary = function(ms) {
  auth.lock();
  setTimeout(auth.unlock, ms);
};
auth.lock = function() {
  auth.locking = true;
  auth.disableOpenBtn();
};
auth.unlock = function() {
  auth.locking = false;
  auth.onInput();
};
auth.enableOpenBtn = function() {
  if (!auth.locking) {
    $el('#enter-button').disabled = false;
  }
};
auth.disableOpenBtn = function() {
  $el('#enter-button').disabled = true;
};
auth.redirect = function(sid) {
  var url = auth.originUrl;
  if (!url) return;
  if (auth.extAuth) {
    if (url.match(/\?.+/)) {
      url += '&sid=' + sid;
    } else if (uri.match(/\?$/)) {
      url += 'sid=' + sid;
    } else {
      url += '?sid=' + sid;
    }
  }
  location.href = url;
};
auth.goodBye = function() {
  auth.lock();
  $el('#id').disabled = true;
  $el('#pw').disabled = true;
  setTimeout(auth._goodBye, 3000);
};
auth._goodBye = function() {
  auth.textseq($el('#message'), 'Bye!');
  setTimeout(auth.__goodBye, 3000);
};
auth.__goodBye = function() {
  document.body.innerHTML = '';
};

auth.changeToPwChangeScreen = function(uid, sid) {
  auth.mode = 'pwchg';
  auth.uid = uid;
  auth.sid = sid;
  $el('#info1').style.display = 'none';
  $el('#info2').style.display = '';
  var m = 'Enter your new password';
  auth.textseq($el('#message'), m, 2, auth.onTextSeqCompleted);
  auth.led.on('#ff0');
  $el('#top-message').innerHTML = 'Change password&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
  $el('#enter-button').innerText = 'SUBMIT'
  auth.disableOpenBtn();
  $el('#pw1').focus();
};

auth.changePw = function() {
  var id = auth.uid;
  var pw1 = $el('#pw1').value;
  var pw2 = $el('#pw2').value;
  if (pw1 != pw2) {
    var m = 'Password mismatched';
    auth.textseq($el('#message'), m, 2, auth.onTextSeqCompleted);
    return;
  }

  var hash = websys.getHash('SHA-256', pw1, id);
  var param = {
    cmd: 'passwd',
    uid: id,
    pw: hash
  };

  var req = {
    url: '../websys/api.cgi',
    method: 'POST',
    data: param,
    cb: auth.changePwCb
  };
  websys.http(req);
};

auth.changePwCb = function(xhr, res) {
  var statusMsg = xhr.status + ' ' + xhr.statusText;
  if (xhr.status == 200) {
    res = util.fromJSON(res);
    var status = res.status;
    if (status == 'OK') {
      var sid = auth.sid;
      auth.onLoginOK(sid);
    } else {
      auth.onLoginNG(status);
    }
  } else {
    auth.showInfo('ERROR: ' + xhr.status);
    setTimeout(auth.clearInfo, 1500);
  }
};

auth.onTextSeqCompleted = function() {
  setTimeout(auth._onTextSeqCompleted, 3000);
};
auth._onTextSeqCompleted = function() {
  $el('#message').html('', 250);
};

auth.onInput = function() {
  var f = 0;
  if (auth.mode == 'login') {
    if ($el('#id').value || $el('#pw').value) {
      f = 1;
    }
  } else {
    if ($el('#pw1').value && $el('#pw2').value) {
      f = 1;
    }
  }
  if (f) {
    auth.enableOpenBtn();
  } else {
    auth.disableOpenBtn();
  }
};
auth.onEnterKey = function(e) {
  if ($el('#id').hasFocus() || $el('#pw').hasFocus()) {
    if ($el('#id').value || $el('#pw').value) {
      auth.login();
    }
  } else if ($el('#pw1').hasFocus() || $el('#pw2').hasFocus()) {
    auth.changePw();
  }
};

auth.regieterInputEventHandler = function(el) {
  el.addEventListener('keydown', auth.onInput);
  el.addEventListener('keyup', auth.onInput);
  el.addEventListener('input', auth.onInput);
  el.addEventListener('change', auth.onInput);
};

onLoad = function() {
  util.addKeyHandler(13, 'down', auth.onEnterKey);

  var opt = {
   speed: 125
  };
  auth.led = new util.Led('#led', opt);

  auth.regieterInputEventHandler($el('#id'));
  auth.regieterInputEventHandler($el('#pw'));
  auth.regieterInputEventHandler($el('#pw1'));
  auth.regieterInputEventHandler($el('#pw2'));

  $el('#id').focus();
  $el('#enter-button').disabled = true;
};
window.addEventListener('load', onLoad, true);
</script>
</head>
<body>
<div id="wrapper">
  <div id="login">
    <div>
      <span id="led"></span><span style="margin-left:8px;" id="top-message">Enter your credential</span>
    </div>
    <div id="info1">
'''
    if SCREEN_TYPE == 0:
        html += '''
    <div style="margin-top:20px;">
      <input type="password" id="id">
      <span id="pw"></span>
    </div>
'''
    else:
        html += '''
    <div style="margin-top:20px;">
      <input type="text" id="id" placeholder="ID" spellcheck="false">
    </div>
    <div style="margin-top:10px;">
      <input type="password" id="pw" placeholder="Password"><br>
    </div>
'''

    html += '''
    </div>

    <div id="info2" style="display:none;">
      <div style="margin-top:20px;">
        <input type="password" id="pw1" placeholder="New password">
      </div>
      <div style="margin-top:10px;">
        <input type="password" id="pw2" placeholder="Re-type"><br>
      </div>
    </div>

    <div style="margin-top:10px;text-align:left;">
      <span id="message"></span><br>
    </div>
    <div style="margin-top:16px;">
      <button id="enter-button" onclick="auth.onEnterButton();" disabled>LOGIN</button>
    </div>
  </div>
</div>
</html>
'''
    return html

def print_screen():
    srcurl = util.get_request_param('srcurl', '')
    p_ext_auth = util.get_request_param('ext_auth', '')
    ext_auth = 'true' if p_ext_auth == 'true' else 'false'
    html = build_html()
    html = util.replace(html, '\${%srcurl%}', srcurl);
    html = util.replace(html, '\${%ext_auth%}', ext_auth);
    util.send_response(html, 'text/html')
