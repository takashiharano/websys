/*!
 * Copyright (c) 2020 Takashi Harano
 */
var websys = {};

websys.ST_LOGIN_ID = 1;
websys.ST_LOGIN_PW = 2;
websys.ST_CHANGE_PW = 3;

websys.USER_FLAGS = [
  'U_FLG_NEED_PW_CHANGE',
  '',
  'U_FLG_DISABLED',
  '',
  '',
  '',
  '',
  'U_FLG_INVALID_DATA'
];

websys.setupUserFlags = function() {
  for (var i = 0; i < websys.USER_FLAGS.length; i++) {
    var name = websys.USER_FLAGS[i];
    websys[name] = Math.pow(2, i);
  }
}();

websys.sendEncKey = 1;
websys.recvEncKey = 7;
websys.initStatus = 0;
websys.status = 0;
websys.isDbgAvailable = false;
websys.basePath = '';
websys.sessionInfo = null;

//-----------------------------------------------------------------------------
websys.logout = function(cb) {
  websys.logout.usrCb = cb;
  websys.callLogoutApi(null, websys.logout.cb);
};
websys.logout.usrCb = null;
websys.logout.cb = function(xhr, res) {
  if (xhr.status != 200) {
    log.e('ERROR: ' + xhr.status);
    return;
  }
  var res = util.fromJSON(res);
  var f = websys.logout.usrCb;
  websys.logout.usrCb = null;
  if (f) f(res.status);
};

//-----------------------------------------------------------------------------
websys.openChangePwDialog = function() {
  var html = '<div style="margin:10px;">';
  html += '<table>';
  html += '<tr>';
  html += '<td>New Password:</td>';
  html += '<td><input type="password" id="websys-pw1" class="websys-dialog"></td>';
  html += '</tr>';
  html += '<tr>';
  html += '<td style="text-align:right;">Re-type:</td>';
  html += '<td><input type="password" id="websys-pw2" class="websys-dialog"></td>';
  html += '</tr>';
  html += '</tr>';
  html += '</table>\n';
  html += '<div style="margin-top:8px;">';
  html += '<button onclick="websys.changePw();" style="min-width:64px;">OK</button>';
  html += '<button onclick="websys.closeDialog();" style="margin-left:8px;min-width:64px;">Cancel</button>';
  html += '</div>';
  html += '</div>';
  var opt = {
    closeAnywhere: false
  };
  util.dialog.open(html, opt);
  $el('#websys-pw1').focus();
};

websys.changePw = function() {
  var uid = websys.getUserId();
  var pw1 = $el('#websys-pw1').value;
  var pw2 = $el('#websys-pw2').value;
  var m;
  if (!pw1) {
    m = 'Password is required';
  } else if (pw1 != pw2) {
    m = 'Password mismatch';
  } else if (!uid) {
    m = 'Not logged in'
  }
  if (m) {
    websys.showInfotip(m);
    return;
  }
  websys.closeDialog();
  websys._changePw(uid, pw1);
};

websys._changePw = function(uid, p) {
  var pw = websys.getUserPwHash(uid, p);
  var param = {
    cmd: 'passwd',
    uid: uid,
    pw: pw
  };
  var req = {
    url: websys.basePath + 'websys/api.cgi',
    method: 'POST',
    data: param,
    cb: websys.changePwCb
  };
  websys.http(req);
};
websys.changePwCb = function(xhr, res) {
  var res = util.fromJSON(res);
  if (res.status != 'OK') {
    websys.showInfotip(res.status);
    return;
  }
  util.confirm('Success!\n\nLogout?\n', websys.logoutAfterCngPw);
};
websys.logoutAfterCngPw = function() {
  websys.logout(websys.logoutCb);
};
websys.logoutCb = function() {
  location.href = location.href;
};

//-----------------------------------------------------------------------------
websys.closeDialog = function() {
  util.dialog.close();
};

websys.showInfotip = function(m, a2, a3) {
  util.infotip.show(m, a2, a3)
};

//-----------------------------------------------------------------------------
// commands
//-----------------------------------------------------------------------------
/**
 * gencode
 */
websys.gencode = function(arg, tbl, echo) {
  var param = {
    cmd: 'gencode'
  };

  var code = dbg.getNonOptVals(arg)[0];
  if (code) {
    if (code.match(/^[A-Za-z\d_\-.]+$/)) {
      param['id'] = code;
    } else {
      dbg.printUsage(tbl.help);
      return;
    }
  }

  var valid = dbg.getOptVal(arg, 'valid');
  if (valid != null) {
    param['validtime'] = valid;
  }

  var groups = dbg.getOptVal(arg, 'g');
  if (groups) {
    try {
      groups = eval(groups);
    } catch (e) {
      log.e(e);
      return;
    }
    param.groups = groups;
  }

  var privs = dbg.getOptVal(arg, 'privs');
  if (privs) {
    try {
      privs = eval(privs);
    } catch (e) {
      log.e(e);
      return;
    }
    param.privs = privs;
  }

  var req = {
    url: websys.basePath + 'websys/api.cgi',
    method: 'POST',
    data: param,
    cb: websys.gencode.cb
  };
  websys.http(req);
};
websys.gencode.cb = function(xhr, res) {
  if (xhr.status == 200) {
    res = util.fromJSON(res);
    var status = res.status;
    if (status == 'OK') {
      var code = res.body;
      log.res(status);
      log(code);
    } else {
      log.res.err(status);
    }
  } else {
    log.e('ERROR: ' + xhr.status);
  }
};

/**
 * guests
 */
websys.guests = function(arg, tbl, echo) {
  var param = {
    cmd: 'guests'
  };
  var req = {
    url: websys.basePath + 'websys/api.cgi',
    method: 'POST',
    data: param,
    cb: websys.guests.cb
  };
  websys.http(req);
};
websys.guests.cb = function(xhr, res) {
  websys.onResponseReceived(xhr, res, true);
};

/**
 * hello
 */
websys.hello = function(arg, tbl, echo) {
  var param = {
    cmd: 'hello',
  };
  if (arg) {
    param.q = arg;
  }
  var req = {
    url: websys.basePath + 'websys/api.cgi',
    method: 'POST',
    data: param,
    cb: websys.hello.cb
  };
  websys.http(req);
};
websys.hello.cb = function(xhr, res) {
  var statusMsg = xhr.status + ' ' + xhr.statusText;
  if (xhr.status == 200) {
    res = util.fromJSON(res);
    if (res.status == 'OK') {
      log.res(res.body);
    } else {
      log.res.err(res.status);
    }
  } else {
    log.e('ERROR: ' + xhr.status);
  }
};

/**
 * login
 */
websys.login = function(arg, tbl, echo) {
  var uid = dbg.getOptVal(arg, '')[0];
  var pw = dbg.getOptVal(arg, 'p');
  websys.status = websys.ST_LOGIN_ID;
  dbg.cmd.saveHistory(false);
  if (uid) {
    if (pw) {
      websys.login.doLogin(uid, pw);
    } else {
      websys.login.inputId(uid);
    }
  } else {
    log('ID ?');
  }
};
websys.login.data = {
  id: ''
};
websys.login.inputId = function(id) {
  websys.login.data.id = id;
  websys.status = websys.ST_LOGIN_PW;
  dbg.cmd.setMode('password');
  log('PW ?');
};
websys.login.inputPw = function(pw) {
  websys.login.data.pw = pw;
  websys.status = 0;
  dbg.cmd.saveHistory(true);
  var id = websys.login.data.id;
  websys.login.data.id = '';
  websys.login.doLogin(id, pw);
  dbg.cmd.setMode('text');
};
websys.login.cancel = function() {
  dbg.cmd.setMode('text');
};
websys.login.doLogin = function(id, pw) {
  id = id.trim();
  pw = pw.trim();
  var param = {
    cmd: 'login',
    id: id
  };
  var hash = websys.getHash('SHA-256', pw, id);
  param.pw = hash;
  var req = {
    url: websys.basePath + 'websys/api.cgi',
    method: 'POST',
    data: param,
    cb: websys.login.cb
  };
  websys.http(req);
};
websys.login.cb = function(xhr, res) {
  var statusMsg = xhr.status + ' ' + xhr.statusText;
  if (xhr.status == 200) {
    res = util.fromJSON(res);
    var status = res.status;
    if (status == 'OK') {
      log.res(status);
    } else {
      log.res.err(status);
    }
  } else {
    log.e('ERROR: ' + xhr.status);
  }
  websys.updateUserInfo();
};

/**
 * logout
 */
websys.cmdLogout = function(arg, tbl, echo) {
  arg = arg.trim();

  var param = {};
  var sid = dbg.getOptVal(arg, 'sid');
  if (sid != null) {
    param.sid = sid;
  }

  var uid = dbg.getOptVal(arg, 'u');
  if (uid != null) {
    param.uid = uid;
  }

  var isAll = dbg.hasOpt(arg, 'a');
  if (isAll) {
    param.all = 'true';
  }

  if (!sid && !uid && !isAll && arg) {
    dbg.printUsage(tbl.help);
    return;
  }

  websys.callLogoutApi(param, websys.logoutCmdCb);
};
websys.callLogoutApi = function(param, cb) {
  if (!param) param = {};
  param.cmd = 'logout';
  var req = {
    url: websys.basePath + 'websys/api.cgi',
    method: 'POST',
    data: param,
    cb: cb
  };
  websys.http(req);
};
websys.logoutCmdCb = function(xhr, res) {
  if (xhr.status == 200) {
    res = util.fromJSON(res);
    if (res.status == 'OK') {
      log.res(res.status);
    } else {
      log.res.err(res.status);
    }
  } else {
    log.e('ERROR: ' + xhr.status);
  }
  websys.updateUserInfo();
};

websys.syslog = function(arg) {
  var n = arg.trim();
  var param = {
    cmd: 'syslog',
    n: n
  };
  var req = {
    url: websys.basePath + 'websys/api.cgi',
    method: 'POST',
    data: param,
    cb: websys.syslog.cb
  };
  websys.http(req);
};
websys.syslog.cb = function(xhr, res) {
  var statusMsg = xhr.status + ' ' + xhr.statusText;
  if (xhr.status == 200) {
    res = util.fromJSON(res);
    var status = res.status;
    if (status == 'OK') {
      log.res(status);
    } else {
      log.res.err(status);
    }
  } else {
    log.e('ERROR: ' + xhr.status);
  }
  if (res.status != 'OK') return;
  var logs = res.body;
  var s = '';
  for (var i = 0; i < logs.length; i++) {
    var v = logs[i];
    var a = v.split('\t');
    var time = a[0];
    var type = a[2];
    var st = a[3];
    var nm = a[4];
    var addr = a[5];
    var host = a[6];
    var ua = a[7];
    var sid = a[8];
    var info = a[9];
    if (!info) info = '';
    var brws = util.getBrowserInfo(ua);
    ua = brws.name + ' ' + brws.version;
    time = time.replace(/T/, ' ');
    sid = util.snip(sid, 7, 3);
    s += time + '\t' + type + '\t' + st + '\t' + nm + '\t' + addr + '\t' + host + '\t' + ua + '\t' + sid + '\t' + info + '\n';
  }
  var r = util.alignFields(s, '\t', 2);
  log.mlt(r);
};

/**
 * passwd
 */
websys.passwdUid = null;
websys.passwdNewPw = null;
websys.cmdPasswd = function(arg, tbl, echo) {
  if (!websys.sessionInfo) {
    log.res.err('NOT_LOGGED_IN');
    return;
  }
  var uid = dbg.getOptVal(arg, 'u');
  var p = dbg.getOptVal(arg, 'p');
  if (!uid) {
    uid = websys.sessionInfo.uid;
  }
  if (p) {
    websys._cmdPasswd(uid, p);
  } else {
    websys.status = websys.ST_CHANGE_PW;
    dbg.cmd.setMode('password');
    log('New PW ?');
    websys.passwdUid = uid;
    websys.passwdNewPw = null;
  }
};
websys.cmdPasswd.inputPw = function(pw) {
  if (websys.passwdNewPw == null) {
    log('Retype ?');
    websys.passwdNewPw = pw;
  } else {
    if (pw == websys.passwdNewPw) {
      websys._cmdPasswd(websys.passwdUid, pw);
    } else {
      log.res.err('Unmatched');
    }
    websys.cmdPasswd.cancel();
  }
};
websys.cmdPasswd.cancel = function() {
  dbg.cmd.setMode('text');
  websys.passwdUid = null;
  websys.passwdNewPw = null;
  websys.status = 0;
};
websys._cmdPasswd = function(uid, p) {
  var pw = websys.getUserPwHash(uid, p);
  var param = {
    cmd: 'passwd',
    uid: uid,
    pw: pw
  };
  var req = {
    url: websys.basePath + 'websys/api.cgi',
    method: 'POST',
    data: param,
    cb: websys.cmdPasswd.cb
  };
  websys.http(req);
};
websys.cmdPasswd.cb = function(xhr, res) {
  websys.onResponseReceived(xhr, res);
};

/**
 * session
 */
websys.cmdSession = function(arg, tbl, echo) {
  var param = {
    cmd: 'session'
  };
  if (dbg.hasOpt(arg, 'u')) {
    param.userinfo = 'true'
  }
  var req = {
    url: websys.basePath + 'websys/api.cgi',
    method: 'POST',
    data: param,
    cb: websys.cmdSession.cb
  };
  websys.http(req);
};
websys.cmdSession.cb = function(xhr, res) {
  var status = websys.onResponseReceived(xhr, res);
  if (status != 'OK') return;
  res = util.fromJSON(res);
  var info = res.body;
  if (info) {
    var s = '\n' + websys.buildSessinInfo(info, true) + '\n';
    log(s);
  }
};

/**
 * sessions
 */
websys.cmdSessions = function(arg, tbl, echo) {
  var param = {
    cmd: 'sessions'
  };
  if (dbg.hasOpt(arg, 'a')) {
    param.all = 'a'
  }
  if (dbg.hasOpt(arg, 'A')) {
    param.all = 'A'
  }
  var req = {
    url: websys.basePath + 'websys/api.cgi',
    method: 'POST',
    data: param,
    cb: websys.cmdSessions.cb
  };
  websys.http(req);
};
websys.cmdSessions.cb = function(xhr, res, req) {
  var status = websys.onResponseReceived(xhr, res);
  if (status != 'OK') return;
  res = util.fromJSON(res);
  var list = res.body;
  var flgA = (req.data.all == 'A');
  var s = '\n';
  if (list instanceof Array) {
    list = util.sortObjectList(list, 'uid');
    for (var i = 0; i < list.length; i++) {
      info = list[i];
      s+= '----------------------------------------------------------------------------\n';
      s += websys.buildSessinInfo(info, flgA) + '\n';
    }
  } else {
    i = 0;
    for (var sid  in list) {
      info = list[sid];
      s+= '----------------------------------------------------------------------------\n';
      s += websys.buildSessinInfo(info, flgA) + '\n';
      i++;
    }
  }
  log(s);
};

websys.buildSessinInfo = function(info, flgA) {
  var brwC = util.getBrowserInfo(info['c_ua']);
  var brwL = util.getBrowserInfo(info['ua']);

  var s = '';
  s += 'uid     : ' + info['uid'] + (info.is_guest ? ' (GUEST)' : '') + '\n';
  s += 'sid     : ' + info['sid'] + '\n';
  s += 'time    : ' + util.getDateTimeString(info['time']) + ' <span style="color:#ccc;">' + info['tz'] + '\n';
  s += 'host    : ' + info['addr'] + '  ' + info['host'] + '\n';
  s += 'ua      : ' + brwL.name + ' ' + brwL.version + '\n';
  s += '</span>';
  if (flgA) {
    s += '<span style="color:#aaa;">';
    s += ' created:\n';
    s += '    time: ' + util.getDateTimeString(info['c_time']) + ' ' + info['c_tz'] + '\n';
    s += '    host: ' + info['c_addr'] + '  ' + info['c_host'] + '\n';
    s += '    ua  : ' + brwC.name + ' ' + brwC.version + '\n';
    s += '</span>';
  }
  return s;
};

/**
 * hash
 */
websys.getHash = function(algorithm, src, salt) {
  var shaObj = new jsSHA(algorithm, 'TEXT');
  shaObj.update(src);
  if (salt != undefined) {
    shaObj.update(salt);
  }
  var hash = shaObj.getHash('HEX');
  return hash;
};

/**
 * user password hash
 */
websys.getUserPwHash = function(uid, pw) {
  return websys.getHash('SHA-256', pw, uid);
};

/**
 * user
 */
websys.cmdUser = function(arg, tbl, echo) {
  var uid = dbg.splitCmdLine(arg)[0];
  var q = (uid ? 'uid=' + uid : null);
  var param = {
    cmd: 'user'
  };
  if (uid) {
    param.uid = uid
  }
  var req = {
    url: websys.basePath + 'websys/api.cgi',
    method: 'POST',
    data: param,
    cb: websys.cmdUser.cb
  };
  websys.http(req);
};
websys.cmdUser.cb = function(xhr, res) {
  var statusMsg = xhr.status + ' ' + xhr.statusText;
  if (xhr.status == 200) {
    var json = res;
    res = util.fromJSON(json);
    if (res.status == 'OK') {
      res = util.fromJSON(json);
      log.res('OK');
      if (res.body) {
        log.p(res.body);
      } else {
        log('no info');
      }
    } else {
      log.res.err(res.status);
    }
  } else if (xhr.status == 0) {
    websys.log.e('NETWORK_CONNECTION_ERROR');
  } else {
    websys.log.e('ERROR: ' + xhr.status);
  }
};

/**
 * useradd
 */
websys.cmdUserAdd = function(arg, tbl, echo) {
  var uid = dbg.getOptVal(arg, 'u');
  if (!uid) {
    dbg.printUsage(tbl.help);
    return;
  }
  var p = dbg.getOptVal(arg, 'p');
  var fullname = dbg.getOptVal(arg, 'n');
  var nameL = dbg.getOptVal(arg, 'lname');
  var nameA = dbg.getOptVal(arg, 'aname');
  var email = dbg.getOptVal(arg, 'email');
  var admin = dbg.getOptVal(arg, 'admin');
  var groups = dbg.getOptVal(arg, 'g');
  var privs = dbg.getOptVal(arg, 'privs');
  var info1 = dbg.getOptVal(arg, 'info1');
  var info2 = dbg.getOptVal(arg, 'info2');
  var desc = dbg.getOptVal(arg, 'desc');
  var flags = dbg.getOptVal(arg, 'flags');
  if (!p) p = '';
  var pw = websys.getUserPwHash(uid, p);
  var param = {
    cmd: 'useradd',
    uid: uid,
    pw: pw
  };
  if (fullname) {
    try {
      fullname = eval(fullname);
    } catch (e) {
      log.e(e);
      return;
    }
    param.fullname = fullname;
  }
  if (nameL) {
    try {
      nameL = eval(nameL);
    } catch (e) {
      log.e(e);
      return;
    }
    param.localfullname = nameL;
  }
  if (nameA) {
    try {
      nameA = eval(nameA);
    } catch (e) {
      log.e(e);
      return;
    }
    param.a_name = nameA;
  }
  if (email) {
    try {
      email = eval(email);
    } catch (e) {
      log.e(e);
      return;
    }
    param.email = email;
  }
  if (admin) {
    param.admin = (admin == 'true' ? 'true' : 'false');
  }
  if (groups) {
    try {
      groups = eval(groups);
    } catch (e) {
      log.e(e);
      return;
    }
    param.groups = groups;
  }
  if (privs) {
    try {
      privs = eval(privs);
    } catch (e) {
      log.e(e);
      return;
    }
    param.privs = privs;
  }
  if (info1) {
    try {
      info1 = eval(info1);
    } catch (e) {
      log.e(e);
      return;
    }
    param.info1 = info1;
  }
  if (info2) {
    try {
      info2 = eval(info2);
    } catch (e) {
      log.e(e);
      return;
    }
    param.info2 = info2;
  }
  if (desc) {
    try {
      desc = eval(desc);
    } catch (e) {
      log.e(e);
      return;
    }
    param.desc = desc;
  }
  if (flags) {
    if (util.isInteger(flags)) {
      param.flags = flags;
    } else {
      log.e('ERROR: flags should be an integer value');
      return;
    }
  }
  var req = {
    url: websys.basePath + 'websys/api.cgi',
    method: 'POST',
    data: param,
    cb: websys.cmdUserAdd.cb
  };
  websys.http(req);
};
websys.cmdUserAdd.cb = function(xhr, res) {
  websys.onResponseReceived(xhr, res);
};

/**
 * usermod
 */
websys.cmdUserMod = function(arg, tbl, echo) {
  var uid = dbg.getOptVal(arg, 'u');
  var p = dbg.getOptVal(arg, 'p');
  var fullname = dbg.getOptVal(arg, 'n');
  var nameL = dbg.getOptVal(arg, 'lname');
  var nameA = dbg.getOptVal(arg, 'aname');
  var email = dbg.getOptVal(arg, 'email');
  var admin = dbg.getOptVal(arg, 'admin');
  var groups = dbg.getOptVal(arg, 'g');
  var agroup = dbg.getOptVal(arg, 'aG');
  var rgroup = dbg.getOptVal(arg, 'rG');
  var privs = dbg.getOptVal(arg, 'privs');
  var aprivs = dbg.getOptVal(arg, 'aPriv');
  var rprivs = dbg.getOptVal(arg, 'rPriv');
  var info1 = dbg.getOptVal(arg, 'info1');
  var info2 = dbg.getOptVal(arg, 'info2');
  var desc = dbg.getOptVal(arg, 'desc');

  if (!uid || (admin && (admin != 'true') && (admin != 'false'))) {
    dbg.printUsage(tbl.help);
    return;
  }

  var param = {
    cmd: 'usermod',
    uid: uid
  };
  if (fullname) {
    try {
      fullname = eval(fullname);
    } catch (e) {
      log.e(e);
      return;
    }
    param.fullname = fullname;
  }
  if (nameL) {
    try {
      nameL = eval(nameL);
    } catch (e) {
      log.e(e);
      return;
    }
    param.localfullname = nameL;
  }
  if (nameA) {
    try {
      nameA = eval(nameA);
    } catch (e) {
      log.e(e);
      return;
    }
    param.a_name = nameA;
  }
  if (email) {
    try {
      email = eval(email);
    } catch (e) {
      log.e(e);
      return;
    }
    param.email = email;
  }
  if (p) {
    var pw = websys.getUserPwHash(uid, p);
    param.pw = pw;
  }
  if (admin) {
    param.admin = (admin == 'true' ? 'true' : 'false');
  }
  if (groups) {
    try {
      groups = eval(groups);
    } catch (e) {
      log.e(e);
      return;
    }
    param.groups = groups;
  }
  if (agroup) {
    try {
      agroup = eval(agroup);
    } catch (e) {
      log.e(e);
      return;
    }
    param.agroup = agroup;
  }
  if (rgroup) {
    try {
      rgroup = eval(rgroup);
    } catch (e) {
      log.e(e);
      return;
    }
    param.rgroup = rgroup;
  }
  if (privs) {
    try {
      privs = eval(privs);
    } catch (e) {
      log.e(e);
      return;
    }
    param.privs = privs;
  }
  if (aprivs) {
    try {
      aprivs = eval(aprivs);
    } catch (e) {
      log.e(e);
      return;
    }
    param.aprivs = aprivs;
  }
  if (rprivs) {
    try {
      rprivs = eval(rprivs);
    } catch (e) {
      log.e(e);
      return;
    }
    param.rprivs = rprivs;
  }
  if (info1) {
    try {
      info1 = eval(info1);
    } catch (e) {
      log.e(e);
      return;
    }
    param.info1 = info1;
  }
  if (info2) {
    try {
      info1 = eval(info2);
    } catch (e) {
      log.e(e);
      return;
    }
    param.info2 = info2;
  }
  if (desc) {
    try {
      desc = eval(desc);
    } catch (e) {
      log.e(e);
      return;
    }
    param.desc = desc;
  }
  var flags = dbg.getOptVal(arg, 'flags');
  if (flags) {
    if (util.isInteger(flags)) {
      param.flags = flags;
    } else {
      log.e('ERROR: flags should be an integer value');
      return;
    }
  }

  var req = {
    url: websys.basePath + 'websys/api.cgi',
    method: 'POST',
    data: param,
    cb: websys.cmdUserMod.cb
  };
  websys.http(req);
};
websys.cmdUserMod.cb = function(xhr, res) {
  websys.onResponseReceived(xhr, res);
};

/**
 * userdel
 */
websys.userdel = function(arg, tbl, echo) {
  var uid = dbg.splitCmdLine(arg)[0];
  if (!uid) {
    dbg.printUsage(tbl.help);
    return;
  }
  var param = {
    cmd: 'userdel',
    uid: uid
  };
  var req = {
    url: websys.basePath + 'websys/api.cgi',
    method: 'POST',
    data: param,
    cb: websys.userdel.cb
  };
  websys.http(req);
};
websys.userdel.cb = function(xhr, res) {
  websys.onResponseReceived(xhr, res);
};

/**
 * unlockuser
 */
websys.unlockuser = function(arg, tbl, echo) {
  var uid = dbg.splitCmdLine(arg)[0];
  if (!uid) {
    dbg.printUsage(tbl.help);
    return;
  }
  var param = {
    cmd: 'unlockuser',
    uid: uid
  };
  var req = {
    url: websys.basePath + 'websys/api.cgi',
    method: 'POST',
    data: param,
    cb: websys.unlockuser.cb
  };
  websys.http(req);
};
websys.unlockuser.cb = function(xhr, res) {
  websys.onResponseReceived(xhr, res);
};

/**
 * users
 */
websys.cmdUsers = function(arg, tbl, echo) {
  var param = {
    cmd: 'users'
  };
  var req = {
    url: websys.basePath + 'websys/api.cgi',
    method: 'POST',
    data: param,
    cb: websys.cmdUsers.cb
  };
  websys.http(req);
};
websys.cmdUsers.cb = function(xhr, res) {
  websys.onResponseReceived(xhr, res, true);
};

websys.cmdWhoAmI = function(arg, tbl, echo) {
  if (websys.sessionInfo) {
    log.res(websys.sessionInfo.uid);
  } else {
    log.res.err('NOT_LOGGED_IN');
  }
};

//-----------------------------------------------------------------------------
/**
 * addgroup
 */
websys.cmdAddGroup = function(arg, tbl, echo) {
  var gid = dbg.getOptVal(arg, '')[0];
  if (!gid) {
    dbg.printUsage(tbl.help);
    return;
  }
  var name = dbg.getOptVal(arg, 'name');
  var privs = dbg.getOptVal(arg, 'privs');
  var param = {
    cmd: 'addgroup',
    gid: gid
  };
  if (name) {
    try {
      name = eval(name);
    } catch (e) {
      log.e(e);
      return;
    }
    param.name = name;
  }
  if (privs) {
    try {
      privs = eval(privs);
    } catch (e) {
      log.e(e);
      return;
    }
    param.privs = privs;
  }
  var req = {
    url: websys.basePath + 'websys/api.cgi',
    method: 'POST',
    data: param,
    cb: websys.cmdAddGroup.cb
  };
  websys.http(req);
};
websys.cmdAddGroup.cb = function(xhr, res) {
  websys.onResponseReceived(xhr, res);
};

/**
 * modgroup
 */
websys.cmdModGroup = function(arg, tbl, echo) {
  var gid = dbg.getOptVal(arg, '')[0];
  var name = dbg.getOptVal(arg, 'name');
  var privs = dbg.getOptVal(arg, 'privs');
  var aprivs = dbg.getOptVal(arg, 'aPriv');
  var rprivs = dbg.getOptVal(arg, 'rPriv');
  var desc = dbg.getOptVal(arg, 'desc');

  if (!gid) {
    dbg.printUsage(tbl.help);
    return;
  }

  var param = {
    cmd: 'modgroup',
    gid: gid
  };
  if (name) {
    try {
      name = eval(name);
    } catch (e) {
      log.e(e);
      return;
    }
    param.name = name;
  }
  if (privs) {
    try {
      privs = eval(privs);
    } catch (e) {
      log.e(e);
      return;
    }
    param.privs = privs;
  }
  if (aprivs) {
    try {
      aprivs = eval(aprivs);
    } catch (e) {
      log.e(e);
      return;
    }
    param.aprivs = aprivs;
  }
  if (rprivs) {
    try {
      rprivs = eval(rprivs);
    } catch (e) {
      log.e(e);
      return;
    }
    param.rprivs = rprivs;
  }
  if (desc) {
    try {
      desc = eval(desc);
    } catch (e) {
      log.e(e);
      return;
    }
    param.desc = desc;
  }

  var req = {
    url: websys.basePath + 'websys/api.cgi',
    method: 'POST',
    data: param,
    cb: websys.cmdModGroup.cb
  };
  websys.http(req);
};
websys.cmdModGroup.cb = function(xhr, res) {
  websys.onResponseReceived(xhr, res);
};

/**
 * delgroup
 */
websys.delgroup = function(arg, tbl, echo) {
  var gid = dbg.splitCmdLine(arg)[0];
  if (!gid) {
    dbg.printUsage(tbl.help);
    return;
  }
  var param = {
    cmd: 'delgroup',
    gid: gid
  };
  var req = {
    url: websys.basePath + 'websys/api.cgi',
    method: 'POST',
    data: param,
    cb: websys.delgroup.cb
  };
  websys.http(req);
};
websys.delgroup.cb = function(xhr, res) {
  websys.onResponseReceived(xhr, res);
};

//-----------------------------------------------------------------------------
websys.auth = function(userCb) {
  var param = {
    cmd: 'auth'
  };
  var req = {
    url: websys.basePath + 'websys/api.cgi',
    method: 'POST',
    data: param,
    cb: websys.auth.cb,
    userCb: userCb
  };
  websys.http(req);
};
websys.auth.cb = function(xhr, res, req) {
  var status = 'ERR_HTTP';
  if (xhr.status == 200) {
    res = util.fromJSON(res);
    status = res.status;
  }
  var userCb = req.userCb;
  if (userCb) userCb(status);
};

/**
 * request user info
 */
websys.requestUserInfo = function(a1, a2) {
  var uid = null;
  var userCb = null;
  if (typeof a1 == 'string') {
    uid = a1;
    userCb = a2;
  } else if (typeof a1 == 'function') {
    userCb = a1;
  }
  if (!uid && !userCb) {
    return websys.sessionInfo;
  }
  var param = {
    cmd: 'user'
  };
  if (uid) {
    param.uid = uid
  }
  var req = {
    url: websys.basePath + 'websys/api.cgi',
    method: 'POST',
    data: param,
    cb: websys.requestUserInfo.cb,
    userCb: userCb
  };
  websys.http(req);
};
websys.requestUserInfo.cb = function(xhr, res, req) {
  var statusMsg = xhr.status + ' ' + xhr.statusText;
  var userinfo = null;
  if (xhr.status == 200) {
    res = util.fromJSON(res);
    if (res.status == 'OK') {
      userinfo = res.body;
    } else {
      websys.log.e('Get user info error: ' + res.status);
    }
  } else {
    websys.log.e('Get user info error: ' + xhr.status);
  }
  var userCb = req.userCb;
  if (userCb) userCb(userinfo);
};

/**
 * get user session info
 */
websys.getUserSessionInfo = function(cbFn) {
  var param = {
    cmd: 'session',
    userinfo: 'true'
  };
  var req = {
    url: websys.basePath + 'websys/api.cgi',
    method: 'POST',
    data: param,
    cb: websys.getUserSessionInfo.cb,
    cbFn: cbFn
  };
  websys.http(req);
};
websys.getUserSessionInfo.cb = function(xhr, res, req) {
  var statusMsg = xhr.status + ' ' + xhr.statusText;
  if (xhr.status == 200) {
    res = util.fromJSON(res);
    if (res.status == 'OK') {
      var sessionInfo = res.body;
      websys.sessionInfo = sessionInfo;
      if (websys.onUserInfoUpdated) {
        websys.onUserInfoUpdated(sessionInfo);
      }
    } else {
      websys.log.e('Get user info error: ' + res.status);
      websys.sessionInfo = null;
    }
  } else {
    websys.log.e('Get user info error: ' + xhr.status);
  }
  if (req.cbFn) req.cbFn();
};

websys.onUserInfoUpdated = null;

websys.updateUserInfo = function() {
  websys.getUserSessionInfo();
};

/**
 * HTTP Request
 */
websys.http = function(req, cb) {
  var data = req.data;
  if (!data) data = {};
  var tz = util.getLocalTzName();
  if (!tz) tz = util.getLocalTZ();
  data['_tz'] = tz;
  var newReq = {
    url: req.url,
    method: req.method,
    data: data,
    async: true,
    chache: false,
    cb: websys.http.onDone,
    req: req
  }
  var e = util.encodeBSB64;
  if (newReq.data) {
    if (newReq.data instanceof Object) {
      newReq.data = util.http.buildQueryString(newReq.data);
    }
    newReq.data = e(newReq.data, websys.sendEncKey);
  }
  websys.onHttpOn();
  websys.httpSessions++;
  util.http(newReq);
};
websys.http.onDone = function(xhr, res, req) {
  var orgReq = req.req;
  var d = util.decodeBSB64;
  websys.httpSessions--;
  if (websys.httpSessions <= 0) {
    websys.httpSessions = 0;
    websys.onHttpOff();
  }
  if (xhr.status == 200) {
    try {
      if (typeof res == 'string') {
        res = res.trim();
        res = d(res, websys.recvEncKey);
        var resObj = util.fromJSON(res);
      } else {
        resObj = res;
      }
      if (resObj.status == 'AUTH_ERROR') {
        setTimeout(websys.getUserSessionInfo, 0);
      }
    } catch (e) {}
    // always Content-Type: text/plain; charset=utf-8
    if (orgReq.responseType == 'json') {
      res = util.fromJSON(res);
    }
  }
  if (orgReq.cb) {
    orgReq.cb(xhr, res, orgReq);
  }
  if (((xhr.status >= 200) && (xhr.status < 300)) || (xhr.status == 304)) {
    if (orgReq.onsuccess) orgReq.onsuccess(xhr, res, orgReq);
  } else {
    if (orgReq.onerror) orgReq.onerror(xhr, res, orgReq);
  }
};
websys.httpSessions =0;

websys.onHttpOn = function() {
  if (websys.isDbgAvailable) {
    dbg.led.on(0);
  }
};
websys.onHttpOff = function() {
  if (websys.isDbgAvailable) {
    dbg.led.off(0);
  }
};

websys.authRedirection = function(srcUrl, extAuthUrl) {
  var authUrl = websys.basePath + 'auth/';
  var params = {
    srcurl: srcUrl
  };
  if (extAuthUrl) {
    authUrl = extAuthUrl;
    params.ext_auth = 'true';
  }
  util.submit(authUrl, 'POST', params);
};

websys.buildClientSig = function() {
  var b = util.getBrowserInfo();
  var brw = b.name;
  if (b.version) {
    brw += '_' + b.version;
  }
  var lngs = navigator.languages;
  var ln = '';
  if (lngs) {
    for (var i = 0; i < lngs.length; i++) {
      if (i > 0) {
        ln += ',';
      }
      ln += lngs[i];
    }
  } else {
    ln = navigator.language;
  }
  var scrn = 'W' + screen.width + 'xH' + screen.height;
  var tz = util.getLocalTZ();
  var sig = brw + '_' + scrn + '_TZ' + tz + '_' + ln;
  return sig;
};

//-----------------------------------------------------------------------------
websys.onResponseReceived = function(xhr, res, echo) {
  var statusMsg = xhr.status + ' ' + xhr.statusText;
  var status = '';
  if (xhr.status == 200) {
    var json = res;
    res = util.fromJSON(json);
    status = res.status;
    if (status == 'OK') {
      log.res('OK');
    } else {
      log.res.err(res.status);
    }
    if (echo && res.body) {
      log.p(res.body);
    }
  } else if (xhr.status == 0) {
    websys.log.e('NETWORK_CONNECTION_ERROR');
  } else {
    websys.log.e('ERROR: ' + xhr.status);
  }
  return status;
};

//-----------------------------------------------------------------------------
websys.getSessionInfo = function() {
  return websys.sessionInfo;
};

websys.getSessionId = function() {
  return (websys.sessionInfo ? websys.sessionInfo.sid : null);
};

websys.getUserInfo = function() {
  var info = null;
  if (websys.sessionInfo && websys.sessionInfo.userinfo) {
    info = websys.sessionInfo.userinfo;
  }
  return info;
};

websys.getUserId = function() {
  var uid = null;
  var userInfo = websys.getUserInfo();
  if (userInfo) {
    uid = userInfo.uid;
  }
  return uid;
};

websys.getUserFullname = function() {
  var fullname = null;
  var userInfo = websys.getUserInfo();
  if (userInfo) {
    fullname = userInfo.fullname;
  }
  return fullname;
};

websys.getUserLocalName = function() {
  var nameL = null;
  var userInfo = websys.getUserInfo();
  if (userInfo) {
    nameL = userInfo.localfullname;
  }
  return nameL;
};

websys.getUserAliasName = function() {
  var nameA = null;
  var userInfo = websys.getUserInfo();
  if (userInfo) {
    nameA = userInfo.a_name;
  }
  return nameA;
};

websys.isAdmin = function() {
  var userInfo = websys.getUserInfo();
  if (userInfo && userInfo.is_admin) {
    return true;
  }
  return false;
};

websys.isGuest = function() {
  var sessionInfo = websys.sessionInfo;
  if (sessionInfo) {
    return sessionInfo.is_guest;
  } else {
    return false;
  }
};

websys.getUserFlags = function() {
  var userInfo = websys.getUserInfo();
  var flags = 0;
  if (userInfo && userInfo.flags) {
    flags = userInfo.flags;
  }
  return flags;
};

/**
 * Ctrl+C
 */
websys.onCtrlC = function() {
  switch (websys.status) {
    case websys.ST_LOGIN_PW:
      websys.login.cancel();
      dbg.cmd.saveHistory(true);
      break;
    case websys.ST_CHANGE_PW:
      websys.cmdPasswd.cancel();
      dbg.cmd.saveHistory(true);
      break;
    case websys.ST_LOGIN_ID:
      dbg.cmd.saveHistory(true);
      break;
  }
  websys.status = 0;
};

/**
 * command listener
 */
websys.cmdListener = function(s) {
  switch (websys.status) {
    case websys.ST_LOGIN_ID:
      websys.login.inputId(s);
      return false;
    case websys.ST_LOGIN_PW:
      websys.login.inputPw(s);
      return false;
    case websys.ST_CHANGE_PW:
      websys.cmdPasswd.inputPw(s);
      return false;
  }
};

websys.log = function(m) {
  log(m);
};
websys.log.v = function(m) {
  log.v(m);
};
websys.log.d = function(m) {
  log.d(m);
};
websys.log.i = function(m) {
  log.i(m);
};
websys.log.w = function(m) {
  log.w(m);
};
websys.log.e = function(m) {
  log.e(m);
};
websys.log.f = function(m) {
  log.f(m);
};

websys.onDbgUnavailable = function() {
  var f = function() {};
  websys.log = f;
  websys.log.v = f;
  websys.log.d = f;
  websys.log.i = f;
  websys.log.w = f;
  websys.log.e = f;
};

/**
 * on ready
 */
websys.onReady = function() {
  if (websys.initStatus == 0) {
    websys.initStatus = 1;
    return;
  }
  if (window.dbg) {
    websys.isDbgAvailable = true;
    dbg.x.addCmdTbl(websys.CMD_TBL);
    dbg.addCmdListener(websys.cmdListener);
    dbg.addEvtListener('ctrlc', websys.onCtrlC);
  } else {
    websys.onDbgUnavailable();
  }
  websys.getUserSessionInfo(websys.onInfoReady);
  websys.initStatus = 2;
};

websys.onInfoReady = function() {
  var f = true;
  if (websys.onWebSysReadyUserFn) {
    f = websys.onWebSysReadyUserFn();
  }
  if (f !== false) {
    websys.onWebSysReady();
  }
};

websys.onWebSysReady = function() {
  var flags = websys.getUserFlags();
  if (flags & websys.U_FLG_NEED_PW_CHANGE) {
    websys.openChangePwDialog();
  }
};

websys.onWebSysReadyUserFn = null;
websys.init = function(basePath, readyFn) {
  websys.basePath = basePath;
  websys.onWebSysReadyUserFn = readyFn;
  if (websys.initStatus == 1) {
    websys.onReady();
  } else {
    websys.initStatus = 1;
  }
};

websys.CMD_TBL = [
  {cmd: 'addgroup', fn: websys.cmdAddGroup, desc: 'Add a group', help: 'addgroup GID [-privs "PRIVILEGE1 PRIVILEGE2"]'},
  {cmd: 'delgroup', fn: websys.delgroup, desc: 'Delete a group', help: 'delgroup gid'},
  {cmd: 'gencode', fn: websys.gencode, desc: 'Make a guest user', help: 'gencode [ID(A-Za-z0-9_-)] [-valid MIN] [-g "GROUP1 GROUP2"] [-privs "PRIVILEGE1 PRIVILEGE2"]'},
  {cmd: 'guests', fn: websys.guests, desc: 'Show all guest user info'},
  {cmd: 'hello', fn: websys.hello, desc: 'Hello'},
  {cmd: 'login', fn: websys.login, desc: 'Login', help: 'login [ID [-p PW]]'},
  {cmd: 'logout', fn: websys.cmdLogout, desc: 'Logout', help: 'logout [-sid sid]|[-u uid]'},
  {cmd: 'modgroup', fn: websys.cmdModGroup, desc: 'Mod a group', help: 'modgroup GID [-privs "PRIVILEGE1 PRIVILEGE2"] [-aPriv "PRIVILEGE"] [-rPriv "PRIVILEGE"]'},
  {cmd: 'passwd', fn: websys.cmdPasswd, desc: 'Change user\'s password', help: 'passwd [-u UID] [-p PW]'},
  {cmd: 'session', fn: websys.cmdSession, desc: 'Show current session info'},
  {cmd: 'sessions', fn: websys.cmdSessions, desc: 'Show session list'},
  {cmd: 'syslog', fn: websys.syslog, desc: 'Show sysyem log'},
  {cmd: 'unlockuser', fn: websys.unlockuser, desc: 'Unlock user login', help: 'unlockuser uid'},
  {cmd: 'user', fn: websys.cmdUser, desc: 'Show user info', help: 'user [uid]'},
  {cmd: 'useradd', fn: websys.cmdUserAdd, desc: 'Add a user', help: 'useradd -u UID -p PW [-n "NAME"] [-lname "LOCAL_NAME"] [-aname "ALIAS_NAME"] [-admin true|false] [-g "GROUP1 GROUP2"] [-privs "PRIVILEGE1 PRIVILEGE2"] [-flags FLAGS]'},
  {cmd: 'userdel', fn: websys.userdel, desc: 'Delete a user', help: 'userdel uid'},
  {cmd: 'usermod', fn: websys.cmdUserMod, desc: 'Mod a user', help: 'usermod -u UID [-p PW] [-n "NAME"] [-lname "LOCAL_NAME"] [-aname "ALIAS_NAME"] [-admin true|false] [-g "GROUP1 GROUP2"] [-aG "GROUP"] [-rG "GROUP"] [-privs "PRIVILEGE1 PRIVILEGE2"] [-aPriv "PRIVILEGE"] [-rPriv "PRIVILEGE"] [-flags FLAGS]'},
  {cmd: 'users', fn: websys.cmdUsers, desc: 'Show all user info'},
  {cmd: 'whoami', fn: websys.cmdWhoAmI, desc: 'Print effective userid'}
];

window.addEventListener('DOMContentLoaded', websys.onReady, true);
