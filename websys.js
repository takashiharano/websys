/*!
 * Copyright (c) 2020 Takashi Harano
 */
var websys = {};

websys.ST_LOGIN_ID = 1;
websys.ST_LOGIN_PW = 2;
websys.ST_CHANGE_PW = 3;
websys.initStatus = 0;
websys.status = 0;
websys.isDbgAvailable = false;
websys.basePath = '';
websys.sessionInfo = null;

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
    if (code.match(/^[A-Za-z\d_\-\.]+$/)) {
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

  var path = dbg.getOptVal(arg, 'path');
  if (path != null) {
    param['path'] = path;
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
    var res = util.fromJSON(res);
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
    var res = util.fromJSON(res);
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
  var uid = dbg.splitCmdLine(arg)[0];
  websys.status = websys.ST_LOGIN_ID;
  dbg.cmd.saveHistory(false);
  if (uid) {
    websys.login.inputId(uid);
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
  var param = {
    cmd: 'login',
    id: id
  };
  var hash = websys.sha.getHash('SHA-256', pw, id);
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
websys.logout = function(arg, tbl, echo) {
  var param = {
    cmd: 'logout'
  };

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

  if (!sid && !uid && !isAll && arg.trim()) {
    dbg.printUsage(tbl.help);
    return;
  }

  var req = {
    url: websys.basePath + 'websys/api.cgi',
    method: 'POST',
    data: param,
    cb: websys.logout.cb
  };
  websys.http(req);
};
websys.logout.cb = function(xhr, res) {
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

websys.loginlog = function(arg) {
  var n = arg.trim();
  var param = {
    cmd: 'loginlog',
    n: n
  };
  var req = {
    url: websys.basePath + 'websys/api.cgi',
    method: 'POST',
    data: param,
    cb: websys.loginlog.cb
  };
  websys.http(req);
};
websys.loginlog.cb = function(xhr, res) {
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
  var logs = res.body;
  var s = '';
  for (var i = 0; i < logs.length; i++) {
    var v = logs[i];
    var a = v.split('\t');
    var time = a[0];
    var st = a[2];
    var nm = a[3];
    var addr = a[4];
    var host = a[5];
    var ua = a[6];
    var sid = a[7];
    s += time + '\t' + st + '\t' + nm + '\t' + addr + '\t' + host + '\t' + ua + '\t' + sid + '\n';
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
  var pw = websys.sha.getHash('SHA-256', p, uid);
  var param = {
    cmd: 'usermod',
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
  var s = '\n' + websys.buildSessinInfo(info) + '\n';
  log(s);
};

/**
 * sessions
 */
websys.cmdSessions = function(arg, tbl, echo) {
  var param = {
    cmd: 'sessions'
  };
  if (dbg.hasOpt(arg, 'a')) {
    param.all = 'true'
  }
  var req = {
    url: websys.basePath + 'websys/api.cgi',
    method: 'POST',
    data: param,
    cb: websys.cmdSessions.cb
  };
  websys.http(req);
};
websys.cmdSessions.cb = function(xhr, res) {
  var status = websys.onResponseReceived(xhr, res);
  if (status != 'OK') return;
  res = util.fromJSON(res);
  var list = res.body;
  var s = '\n';
  if (list instanceof Array) {
    for (var i = 0; i < list.length; i++) {
      info = list[i];
      s += websys.buildSessinInfo(info) + '\n';
    }
  } else {
    for (var sid  in list) {
      info = list[sid];
      s += websys.buildSessinInfo(info) + '\n';
    }
  }
  log(s);
};

websys.buildSessinInfo = function(info) {
  var s = '';
  s += 'uid         : ' + info.uid + '\n';
  s += 'sid         : ' + info.sid + '\n';
  s += 'created_time: ' + util.getDateTimeString(info.created_time) + '\n';
  s += 'tz          : ' + info.tz + '\n';
  s += 'addr        : ' + info.addr + '\n';
  s += 'host        : ' + info.host + '\n';
  s += 'ua          : ' + info.ua + '\n';
  s += 'is_guest    : ' + info.is_guest + '\n';
  s += 'last_accessed:\n';
  s += '  time      : ' + util.getDateTimeString(info.last_accessed.time) + '\n';
  s += '  tz        : ' + info.last_accessed.tz + '\n';
  s += '  addr      : ' + info.last_accessed.addr + '\n';
  s += '  host      : ' + info.last_accessed.host + '\n';
  s += '  ua        : ' + info.last_accessed.ua + '\n';
  return s;
};

/**
 * sha
 */
websys.ALGORYTHMS = ['1', '224', '256', '384', '512', '3-224', '3-256', '3-384', '3-512'];
websys.sha = function(arg, tbl, echo) {
  var src, ret;
  var variant = dbg.getOptVal(arg, '')[0];
  if (variant == '') {
    dbg.printUsage(tbl.help);
    return;
  }

  var all = false;
  var noOptsLen = dbg.getOptVal(arg, '').length;
  if (noOptsLen == 0) {
    all = true;
    src = dbg.getOptVal(arg, '')[0];
  } else if (noOptsLen == 1) {
    if (!websys.sha.isValidVariant(variant)) {
      all = true;
    }
    src = dbg.getOptVal(arg, '')[0];
  } else {
    if (websys.sha.isValidVariant(variant)) {
      src = dbg.getOptVal(arg, '')[1];
    } else {
      dbg.printUsage(tbl.help);
      return;
    }
  }

  var input = dbg.getOptVal(arg, 'i');
  if (input != undefined) {
    src = input;
  }
  try {
    src = eval(src);
  } catch (e) {
    log.e(e);
    return;
  }
  if (src == undefined) {
    dbg.printUsage(tbl.help);
    return;
  }

  var salt = dbg.getOptVal(arg, 'salt');
  try {
    salt = eval(salt);
  } catch (e) {
    log.e(e);
    return;
  }

  if (all) {
    var ret = {};
    for (var i = 0; i < websys.ALGORYTHMS.length; i++) {
      if (i > 0) {
        if (echo) {
          log('');
        }
      }
      algorithm = websys.sha.getAlgorythmName(websys.ALGORYTHMS[i]);
      var hash = websys.sha.getHash(algorithm, src, salt, echo);
      if (echo) {
        log(algorithm);
        log.res(hash);
      }
      ret[algorithm] = hash;
    }
  } else {
    algorithm = websys.sha.getAlgorythmName(variant);
    hash = websys.sha.getHash(algorithm, src, salt, echo);
    if (echo) {
      log.res(hash);
    }
    ret = hash;
  }
  return ret;
};
websys.sha.getAlgorythmName = function(variant) {
  var algorithm = 'SHA'
  if (variant.match('-')) {
    algorithm += variant;
  } else {
    algorithm += '-' + variant;
  }
  return algorithm;
};
websys.sha.getHash = function(algorithm, src, salt) {
  var shaObj = new jsSHA(algorithm, 'TEXT');
  shaObj.update(src);
  if (salt != undefined) {
    shaObj.update(salt);
  }
  var hash = shaObj.getHash('HEX');
  return hash;
};
websys.sha.isValidVariant = function(v) {
  return dbg.arr.has(websys.ALGORYTHMS, v);
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
    var res = util.fromJSON(json);
    if (res.status == 'OK') {
      var res = util.fromJSON(json);
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
  var p = dbg.getOptVal(arg, 'p');
  var name = dbg.getOptVal(arg, 'name');
  if (!uid) {
    dbg.printUsage(tbl.help);
    return;
  }
  if (!p) p = '';
  var pw = websys.sha.getHash('SHA-256', p, uid);
  var param = {
    cmd: 'useradd',
    uid: uid,
    pw: pw
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
  if (dbg.hasOpt(arg, 'disabled')) {
    param.disabled = 'true';
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
  var name = dbg.getOptVal(arg, 'n');
  var disabled = dbg.getOptVal(arg, 'disabled');
  if (!uid || (disabled && (disabled != 'true') && (disabled != 'false'))) {
    dbg.printUsage(tbl.help);
    return;
  }

  var param = {
    cmd: 'usermod',
    uid: uid
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
  if (p) {
    var pw = websys.sha.getHash('SHA-256', p, uid);
    param.pw = pw;
  }
  if (disabled) {
    param.disabled = (disabled == 'true' ? 'true' : 'false');
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
 * get user info
 */
websys.getUserInfo = function(a1, a2) {
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
    cb: websys.getUserInfo.cb,
    userCb: userCb
  };
  websys.http(req);
};
websys.getUserInfo.cb = function(xhr, res, req) {
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
    newReq.data = e(newReq.data, 1);
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
    res = res.trim();
    try {
      res = d(res, 7);
      var resJson = util.fromJSON(res);
      if (resJson.status == 'AUTH_ERROR') {
        setTimeout(websys.getUserSessionInfo, 0);
      }
    } catch (e) {}
  }
  if (xhr.status == 200) {
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
  var b = util.getBrowserType();
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
    name = userInfo.uid;
  }
  return uid;
};

websys.getUserName = function() {
  var name = null;
  var userInfo = websys.getUserInfo();
  if (userInfo) {
    name = userInfo.name;
  }
  return name;
};

websys.hasAttr = function(a1, a2) {
  var user = null;
  var attr = null;
  if (typeof a1 == 'object') {
    user = a1;
    attr = a2;
  } else {
    attr = a1;
  }
  if (!user && websys.sessionInfo) {
    user = websys.sessionInfo.userinfo;
  }
  if (!user) {
    return false;
  }
  for (var i = 0; i < user.attr.length; i++) {
    if (user.attr[i] == attr) {
      return true;
    }
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
websys.cmdListener = function(str) {
  switch (websys.status) {
    case websys.ST_LOGIN_ID:
      websys.login.inputId(str);
      return false;
    case websys.ST_LOGIN_PW:
      websys.login.inputPw(str);
      return false;
    case websys.ST_CHANGE_PW:
      websys.cmdPasswd.inputPw(str);
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
  if (websys.readyFn) {
    websys.readyFn();
  }
};

websys.readyFn = null;
websys.init = function(path, readyFn) {
  websys.basePath = path;
  websys.readyFn = readyFn;
  if (websys.initStatus == 1) {
    websys.onReady();
  } else {
    websys.initStatus = 1;
  }
};

websys.CMD_TBL = [
  {cmd: 'gencode', fn: websys.gencode, desc: 'Make a guest user', help: 'gencode [ID(A-Za-z0-9_-)] [-valid MIN] [-path PATH]'},
  {cmd: 'guests', fn: websys.guests, desc: 'Show all guest user info'},
  {cmd: 'hello', fn: websys.hello, desc: 'Hello'},
  {cmd: 'login', fn: websys.login, desc: 'Login'},
  {cmd: 'loginlog', fn: websys.loginlog, desc: 'Show Login Log'},
  {cmd: 'logout', fn: websys.logout, desc: 'Logout', help: 'logout [-sid sid]|[-u uid]'},
  {cmd: 'passwd', fn: websys.cmdPasswd, desc: 'Change user\'s password', help: 'passwd [-u UID] [-p PW]'},
  {cmd: 'session', fn: websys.cmdSession, desc: 'Show current session info'},
  {cmd: 'sessions', fn: websys.cmdSessions, desc: 'Show session list'},
  {cmd: 'sha', fn: websys.sha, desc: 'Generate and display cryptographic hash', help: 'sha [1|224|3-224|256|3-256|384|3-384|512|3-512] -i "input" [-salt "salt"]'},
  {cmd: 'user', fn: websys.cmdUser, desc: 'Show user info', help: 'user [uid]'},
  {cmd: 'useradd', fn: websys.cmdUserAdd, desc: 'Add a user', help: 'useradd -u UID -p PW [-n "NAME"] [-disabled]'},
  {cmd: 'userdel', fn: websys.userdel, desc: 'Delete a user', help: 'userdel uid'},
  {cmd: 'usermod', fn: websys.cmdUserMod, desc: 'Mod a user', help: 'usermod -u UID [-p PW] [-n "NAME"] [-disabled true|false]'},
  {cmd: 'users', fn: websys.cmdUsers, desc: 'Show all user info'},
  {cmd: 'whoami', fn: websys.cmdWhoAmI, desc: 'Print effective userid'}
];

window.addEventListener('DOMContentLoaded', websys.onReady, true);
