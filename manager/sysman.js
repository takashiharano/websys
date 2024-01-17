/*!
 * Copyright (c) 2023 Takashi Harano
 */
var sysman = {};

sysman.INTERVAL = 2 * 60 * 1000;
sysman.USER_LIST_COLUMNS = [
  {key: 'uid', label: 'UID', style: 'min-width:10em;'},
  {key: 'name', label: 'Full Name', style: 'min-width:13em;'},
  {key: 'local_name', label: 'Local Full Name', style: 'min-width:10em;'},
  {key: 'is_admin', label: 'Admin'},
  {key: 'group', label: 'Groups', style: 'min-width:15em;'},
  {key: 'privs', label: 'Privileges', style: 'min-width:15em;'},
  {key: 'desc', label: 'Description', style: 'min-width:15em;'},
  {key: 'status', label: 'Status'},
  {key: 'fail', label: 'Fail', sort: false},
  {key: 'created_at', label: 'Created'},
  {key: 'updated_at', label: 'Updated'},
  {key: 'pw_changed_at', label: 'PwChanged'}
];

sysman.listStatus = {
  sortIdx: 0,
  sortOrder: 1
};

sysman.itemList = [];
sysman.sessions = null;
sysman.userEditWindow = null;
sysman.groupEditWindow = null;
sysman.userEditMode = null;
sysman.groupEditMode = null;
sysman.tmrId = 0;
sysman.interval = 0;

$onReady = function() {
  util.clock('#clock');
  $el('#user-list').innerHTML = '<span class="progdot">Loading</span>';
  sysman.drawGroupStatus('<span class="progdot">Loading</span>');
};

sysman.onSysReady = function() {
  sysman.reload();
  sysman.queueNextUpdateSessionInfo();
};

sysman.reload = function() {
  sysman.reloadUserInfo();
  sysman.getGroupList();
};

sysman.reloadUserInfo = function() {
  sysman.getUserList();
  sysman.getSessionList();
};

sysman.queueNextUpdateSessionInfo = function() {
  sysman.tmrId = setTimeout(sysman.updateSessionInfo, sysman.INTERVAL);
};

sysman.updateSessionInfo = function() {
  sysman.interval = 1;
  sysman.getSessionList();
};

sysman.callApi = function(act, params, cb) {
  if (!params) params = {};
  var data = {act: act};
  if (params) {
    for (var k in params) {
      data[k] = params[k];
    }
  }
  var req = {
    url: 'api.cgi',
    method: 'POST',
    data: data,
    responseType: 'json'
  };
  sysman.http(req, cb);
};

sysman.execCmd = function(act, params, cb) {
  if (!params) params = {};
  var data = {cmd: act};
  if (params) {
    for (var k in params) {
      data[k] = params[k];
    }
  }
  var req = {
    url: '../api.cgi',
    method: 'POST',
    data: data,
    responseType: 'json'
  };
  sysman.http(req, cb);
};

sysman.http = function(req, cb) {
  req.cb = cb;
  websys.http(req);
};

sysman.showInfotip = function(m, d) {
  var opt = {
    style: {
      'font-size': '14px'
    }
  };
  util.infotip.show(m, d, opt);
};

sysman.getUserList = function() {
  sysman.callApi('get_user_list', null, sysman.getUserListCb);
};
sysman.getUserListCb = function(xhr, res, req) {
  if (res.status == 'FORBIDDEN') {
    location.href = location.href;
    return;
  } else if (res.status != 'OK') {
    sysman.showInfotip(res.status);
    return;
  }
  var users = res.body;
  var infoList = [];
  for (var k in users) {
    var user = users[k];
    infoList.push(user);
  }
  sysman.itemList = infoList;
  sysman.drawList(infoList, 0, 1);
};

sysman.buildListHeader = function(columns, sortIdx, sortOrder) {
  var html = '<table>';
  html += '<tr class="item-list-header">';

  for (var i = 0; i < columns.length; i++) {
    var column = columns[i];
    var label = column['label'];
    var sortable = (column['sort'] === false ? false : true);

    var sortAscClz = '';
    var sortDescClz = '';
    var nextSortType = 1;
    if (i == sortIdx) {
      if (sortOrder == 1) {
        sortAscClz = 'sort-active';
      } else if (sortOrder == 2) {
        sortDescClz = 'sort-active';
      }
      nextSortType = sortOrder + 1;
    }

    var sortButton = '<span class="sort-button" ';
    sortButton += ' onclick="sysman.sortItemList(' + i + ', ' + nextSortType + ');"';
    sortButton += '>';
    sortButton += '<span';
    if (sortAscClz) {
       sortButton += ' class="' + sortAscClz + '"';
    }
    sortButton += '>▲</span>';
    sortButton += '<br>';
    sortButton += '<span';
    if (sortDescClz) {
       sortButton += ' class="' + sortDescClz + '"';
    }
    sortButton += '>▼</span>';
    sortButton += '</span>';

    html += '<th class="item-list"';
    if (column.style) {
      html += ' style="' + column.style + '"';
    }
    html += '><span>' + label + '</span>';
    if (sortable) {
      html += ' ' + sortButton;
    }
    html += '</th>';
  }

  html += '</tr>';
  return html;
};

sysman.drawList = function(items, sortIdx, sortOrder) {
  if (sortIdx >= 0) {
    if (sortOrder > 0) {
      var srtDef = sysman.USER_LIST_COLUMNS[sortIdx];
      var desc = (sortOrder == 2);
      items = sysman.sortList(items, srtDef.key, desc, srtDef.meta);
    }
  }

  var htmlList = '';
  for (var i = 0; i < items.length; i++) {
    var item = items[i];
    var uid = item.uid;
    var name = item.name.replace(/ /g, '&nbsp');
    var local_name = item.local_name.replace(/ /g, '&nbsp');
    var loginFailedCount = 0;
    var loginFailedTime = '';
    var loginFailedInfo = item.login_failed_info;
    if (loginFailedInfo) {
      loginFailedCount = loginFailedInfo['count'];
      loginFailedTime = util.getDateTimeString(loginFailedInfo['time']);
    }

    var createdDate = '---------- --:--:--.---';
    if (item.created_at > 0) {
      var createdAt = item.created_at;
      if (util.isInteger(createdAt)) createdAt *= 1000;
      createdDate = util.getDateTimeString(createdAt, '%YYYY-%MM-%DD %HH:%mm:%SS.%sss');
    }

    var updatedDate = '---------- --:--:--.---';
    if (item.updated_at > 0) {
      var updatedAt = item.updated_at;
      if (util.isInteger(updatedAt)) updatedAt *= 1000;
      updatedDate = util.getDateTimeString(updatedAt, '%YYYY-%MM-%DD %HH:%mm:%SS.%sss');
    }

    var pwChangedDate = '---------- --:--:--.---';
    if (item.pw_changed_at > 0) {
      var pwChangedAt = item.pw_changed_at;
      if (util.isInteger(pwChangedAt)) pwChangedAt *= 1000;
      pwChangedDate = util.getDateTimeString(pwChangedAt, '%YYYY-%MM-%DD %HH:%mm:%SS.%sss');
    }

    var desc = (item.desc ? item.desc : '');
    var escDesc = util.escHtml(desc);
    var dispDesc = '<span style="display:inline-block;width:100%;overflow:hidden;text-overflow:ellipsis;"';
    if (util.lenW(desc) > 35) {
      dispDesc += ' data-tooltip="' + escDesc + '"';
    }
    dispDesc += '>' + escDesc + '</span>';

    htmlList += '<tr class="item-list">';

    htmlList += '<td class="item-list"><span class="pseudo-link link-button" onclick="sysman.editUser(\'' + uid + '\');" data-tooltip="Edit">' + uid + '</span></td>';
    htmlList += '<td class="item-list">' + name + '</td>';
    htmlList += '<td class="item-list">' + local_name + '</td>';
    htmlList += '<td class="item-list" style="text-align:center;">' + (item.is_admin ? 'Y' : '') + '</td>';
    htmlList += '<td class="item-list">' + item.group + '</td>';
    htmlList += '<td class="item-list">' + item.privs + '</td>';
    htmlList += '<td class="item-list" style="max-width:20em">' + dispDesc + '</td>';
    htmlList += '<td class="item-list" style="text-align:center;">' + item.status + '</td>';

    htmlList += '<td class="item-list" style="text-align:center;width:1.5em;">';
    if (loginFailedCount > 0) {
      var clz = 'pseudo-link';
      if ((sysman.websysconf.LOGIN_FAILURE_MAX > 0) && (loginFailedCount >= sysman.websysconf.LOGIN_FAILURE_MAX)) {
        clz += ' text-red';
      }
      htmlList += '<span class="' + clz + '" data-tooltip="' + loginFailedTime + '" onclick="sysman.confirmClearLoginFailedCount(\'' + uid + '\');">' + loginFailedCount + '</span>';
    } else {
      htmlList += '';
    }
    htmlList += '</td>';

    htmlList += '<td class="item-list" style="text-align:center;">' + createdDate + '</td>';
    htmlList += '<td class="item-list" style="text-align:center;">' + updatedDate + '</td>';
    htmlList += '<td class="item-list" style="text-align:center;">' + pwChangedDate + '</td>';
    htmlList += '</tr>';
  }
  htmlList += '</table>';

  var htmlHead = sysman.buildListHeader(sysman.USER_LIST_COLUMNS, sortIdx, sortOrder);
  var html = htmlHead + htmlList; 

  sysman.drawListContent(html);
};

sysman.getSessionList = function() {
  if (sysman.tmrId > 0) {
    clearTimeout(sysman.tmrId);
    sysman.tmrId = 0;
    sysman.interval = 1;
  }
  sysman.callApi('get_session_list', null, sysman.getSessionListCb);
};
sysman.getSessionListCb = function(xhr, res, req) {
  if (res.status == 'FORBIDDEN') {
    location.href = location.href;
    return;
  } else if (res.status != 'OK') {
    sysman.showInfotip(res.status);
    return;
  }
  var sessions = res.body;
  sysman.sessions = sessions;
  sysman.drawSessionList(sessions);

  if (sysman.interval) {
    sysman.interval = 0;
    sysman.queueNextUpdateSessionInfo();
  }
};

sysman.drawSessionList = function(sessions) {
  var now = util.now();

  var html = '<table>';
  html += '<tr style="font-weight:bold;">';
  html += '<td></td>';
  html += '<td>UID</td>';
  html += '<td>Name</td>';
  html += '<td>Session</td>';
  html += '<td>Last Accessed</td>';
  html += '<td>Elapsed</td>';
  html += '<td style="font-weight:normal;">' + sysman.buildTimeLineHeader(now) + '</td>';
  html += '<td>Addr</td>';
  html += '<td>User-Agent</td>';
  html += '<td>Logged in</td>';
  html += '</tr>';
  html += sysman.buildSessionInfoHtml(sessions, now);
  html += '</table>';
  $el('#session-list').innerHTML = html;
};

sysman.buildTimeLineHeader = function(now) {
  var currentInd = '<span class="blink1" style="color:#0cf;">v</span>';

  var nowYYYYMMDD = util.getDateTimeString(now, '%YYYY%MM%DD');
  var nowHHMM = util.getDateTimeString(now, '%HH:%mm');
  var tmp = nowHHMM.split(':');
  var nowHH = tmp[0];
  var nowMM = tmp[1];

  var html = '';
  for (var i = 0; i <= 23; i++) {
    var ts = sysman.getTimeSlot(i, nowHH, nowMM);
    var v = false;
    if (i < 10) {
      if (ts == 0) {
        html += currentInd;
      }
    } else {
      if (ts == 0) {
        html += currentInd + ' ';
      } else if (ts == 1) {
        html += ' ' + currentInd;
      }
    }

    if (!((ts == 0) || ((i >= 10) && (ts == 1)))) {
      html += i;
    }

    var st = ((i < 10) ? 1 : 2);
    for (var j = st; j <= 4; j++) {
      if (ts == j) {
        html += currentInd;
      } else {
        html += ' ';
      }
    }
  }
  return html;
};

sysman.buildSessionInfoHtml = function(sessions, now) {
  var html = '';
  if (!sessions) return html;
  var mn = util.getMidnightTimestamp(now);
  for (var i = 0; i < sessions.length; i++) {
    var session = sessions[i];
    html += sysman.buildSessionInfoOne(session, now, mn);
  }
  return html;
};
sysman.buildSessionInfoOne = function(session, now, mn) {
  var uid = session.uid;
  var name = session.user_name;
  var loginT = session.created_time;
  var la = session.last_accessed;
  var t = la['time'];
  var tMs = t * 1000;
  var loginTime = util.getDateTimeString(loginT, '%YYYY-%MM-%DD %HH:%mm:%SS.%sss')
  var laTime = util.getDateTimeString(t, '%YYYY-%MM-%DD %HH:%mm:%SS.%sss')
  var sid = session['sid'];
  var ssid = util.snip(sid, 7, 2, '..');
  var sid7 = util.snip(sid, 7, 0, '');
  var addr = la['addr'];
  var brws = util.getBrowserInfo(la['ua']);
  var ua = brws.name + ' ' + brws.version;

  var elapsed = now - tMs;
  var ledColor = '#888';
  if (elapsed <= 10 * util.MINUTE) {
    ledColor = '#0f0';
  } else if (elapsed <= 30 * util.MINUTE) {
    ledColor = '#0a0';
  } else if (elapsed <= 6 * util.HOUR) {
    ledColor = '#080';
  } else if (tMs >= mn) {
    ledColor = '#262';
  }

  var led = '<span class="led" style="color:' + ledColor + '"></span>'
  var ssidLink = '<span class="pseudo-link link-button" onclick="sysman.confirmLogoutSession(\'' + uid + '\', \'' + sid + '\');" data-tooltip="' + sid + '">' + ssid + '</span>';
  var timeId = 'tm-' + sid7;
  var tmspan = '<span id="' + timeId + '"></span>'
  var laTimeMs = Math.floor(t * 1000);
  var timeline = sysman.buildTimeLine(now, laTimeMs);

  var html = '';
  html += '<tr class="item-list">';
  html += '<td style="padding-right:4px;">' + led + '</td>';
  html += '<td style="padding-right:10px;">' + uid + '</td>';
  html += '<td style="padding-right:10px;">' + name + '</td>';
  html += '<td style="padding-right:10px;">' + ssidLink + '</td>';
  html += '<td style="padding-right:10px;">' + laTime + '</td>';
  html += '<td style="padding-right:10px;text-align:right;">' + tmspan + '</td>';
  html += '<td>' + timeline + '</td>';
  html += '<td style="padding-right:10px;">' + addr + '</td>';
  html += '<td style="padding-right:10px;">' + ua + '</td>';
  html += '<td style="padding-right:10px;">' + loginTime + '</td>';
  html += '</tr>';

  util.timecounter.start('#' + timeId, tMs);
  return html;
};
sysman.buildTimeLine = function(now, lastAccessedTime) {
  var mn = util.getMidnightTimestamp(now);
  var nowYYYYMMDD = util.getDateTimeString(now, '%YYYY%MM%DD');
  var nowHHMM = util.getDateTimeString(now, '%HH:%mm');
  var tmp = nowHHMM.split(':');
  var nowHH = tmp[0];
  var nowMM = tmp[1];
  var accYYYYMMDD = util.getDateTimeString(lastAccessedTime, '%YYYY%MM%DD');
  var accHHMM = util.getDateTimeString(lastAccessedTime, '%HH:%mm');
  tmp = accHHMM.split(':');
  var accHH = tmp[0];
  var accMM = tmp[1];

  var span = '<span style="opacity:0.6;">';
  var html = span;
  var f = false;
  for (var i = 0; i <= 23; i++) {
    if ((i == 0) && (lastAccessedTime < mn)) {
      html += '</span><span style="color:#d66;">&lt;</span>' + span;
    } else {
      html += '|';
    }
    for (var j = 0; j < 4; j++) {
      var s = '-';
      if ((accYYYYMMDD == nowYYYYMMDD) && (sysman.inTheTimeSlot(i, j, accHH, accMM))) {
        s = '</span><span style="color:#0f0;">*</span>' + span;
      }
      html += s;
      if (sysman.inTheTimeSlot(i, j, nowHH, nowMM)) {
        html += '<span style="opacity:0.5;">';
        f = true;
      }
    }
  }
  if (f) html += '</span>';
  html += '</span>';
  return html;
};

sysman.inTheTimeSlot = function(h, qM, hh, mm) {
  if (hh == h) {
    if ((qM == 0) && (mm < 15)) {
      return true;
    } else if ((qM == 1) && (mm >= 15) && (mm < 30)) {
      return true;
    } else if ((qM == 2) && (mm >= 30) && (mm < 45)) {
      return true;
    } else if ((qM == 3) && (mm >= 45)) {
      return true;
    }
  }
  return false;
};
sysman.getTimeSlot = function(h, hh, mm) {
  if (h == hh) {
    if (mm == 0) {
      return 0;
    } else if (mm < 15) {
      return 1;
    } else if ((mm >= 15) && (mm < 30)) {
      return 2;
    } else if ((mm >= 30) && (mm < 45)) {
      return 3;
    } else if (mm >= 45) {
      return 4;
    }
  }
  return -1;
};

sysman.drawListContent = function(html) {
  $el('#user-list').innerHTML = html;
};

sysman.sortItemList = function(sortIdx, sortOrder) {
  if (sortOrder > 2) {
    sortOrder = 0;
  }
  sysman.listStatus.sortIdx = sortIdx;
  sysman.listStatus.sortOrder = sortOrder;
  sysman.drawList(sysman.itemList,sortIdx, sortOrder);
};

sysman.confirmLogoutSession = function(uid, sid) {
  var cSid = websys.getSessionId();
  var ssid = util.snip(sid, 7, 7, '..');
  var m = 'Logout?\n\n';
  if (sid == cSid) {
    m += '<span style="color:#f44;font-weight:bold;">[CURRENT SESSION]</span>\n';
  }
  m += '<div style="text-align:left;">';
  m += 'uid: ' + uid + '\n';
  m += 'sid: ' + sid;
  m += '</div>';
  util.confirm(m, sysman.logoutSession, {data: sid});
};
sysman.logoutSession = function(sid) {
  var params = {
    sid: sid
  };
  sysman.execCmd('logout', params, sysman.logoutSessionCb);
};
sysman.logoutSessionCb = function(xhr, res) {
  sysman.showInfotip(res.status);
  if (res.status != 'OK') {
    return;
  }
  sysman.getSessionList();
};

//-----------------------------------------------------------------------------
sysman.newUser = function() {
  sysman.editUser(null);
};

sysman.editUser = function(uid) {
  sysman.userEditMode = (uid ? 'edit' : 'new');
  if (!sysman.userEditWindow) {
    sysman.userEditWindow = sysman.openUserInfoEditorWindow(sysman.userEditMode, uid);
  }
  sysman.clearUserInfoEditor();
  if (uid) {
    var params = {
      uid: uid
    };
    sysman.execCmd('user', params, sysman.GetUserInfoCb);
  } else {
    $el('#uid').focus();
  }
};

sysman.openUserInfoEditorWindow = function(mode, uid) {
  var currentUid = websys.getUserId();

  var html = '';
  html += '<div style="position:relative;width:100%;height:100%;text-align:center;vertical-align:middle">';
  if (uid && (uid != currentUid)) {
    html += '<div style="position:absolute;top:8px;right:8px;"><button class="button-red" onclick="sysman.deleteUser(\'' + uid + '\');">DEL</button></div>';
  }
  html += '<div style="padding:4px;position:absolute;top:0;right:0;bottom:0;left:0;margin:auto;width:360px;height:290px;text-align:left;">';

  html += '<table>';
  html += '  <tr>';
  html += '    <td>UID</td>';
  html += '    <td style="width:256px;">';
  html += '      <input type="text" id="uid" style="width:100%;">';
  html += '    </td>';
  html += '  </tr>';
  html += '  <tr>';
  html += '    <td>Full name</td>';
  html += '    <td><input type="text" id="name" style="width:100%;"></td>';
  html += '  </tr>';
  html += '  <tr>';
  html += '    <td>Local Full name</td>';
  html += '    <td><input type="text" id="local_name" style="width:100%;"></td>';
  html += '  </tr>';
  html += '  <tr>';
  html += '    <td>isAdmin</td>';
  html += '    <td><input type="checkbox" id="isadmin">';
  html += '    </td>';
  html += '  </tr>';
  html += '  <tr>';
  html += '    <td>Groups</td>';
  html += '    <td><input type="text" id="group" style="width:100%;"></td>';
  html += '  </tr>';
  html += '  <tr>';
  html += '    <td>Privileges</td>';
  html += '    <td><input type="text" id="privs" style="width:100%;"></td>';
  html += '  </tr>';
  html += '  <tr>';
  html += '    <td>Description</td>';
  html += '    <td><input type="text" id="desc" style="width:100%;"></td>';
  html += '  </tr>';
  html += '  <tr>';
  html += '    <td>Status</td>';
  html += '    <td><input type="text" id="status" style="width:1.5em;"></td>';
  html += '  </tr>';

  html += '  <tr>';
  html += '    <td>&nbsp;</td>';
  html += '    <td>&nbsp;</td>';
  html += '  </tr>';

  html += '  <tr>';
  html += '    <td>Password</td>';
  html += '    <td><input type="password" id="pw1" style="width:100%;"></td>';
  html += '  </tr>';
  html += '  <tr>';
  html += '    <td>Re-type</td>';
  html += '    <td><input type="password" id="pw2" style="width:100%;"></td>';
  html += '  </tr>';
  html += '<table>';

  html += '<div style="margin-top:24px;text-align:center;">';
  html += '<button onclick="sysman.saveUserInfo();">OK</button>'
  html += '<button style="margin-left:8px;" onclick="sysman.userEditWindow.close();">Cancel</button>'
  html += '</div>';

  html += '</div>';
  html += '</div>';

  var opt = {
    draggable: true,
    resizable: true,
    pos: 'c',
    closeButton: true,
    width: 480,
    height: 380,
    minWidth: 480,
    minHeight: 360,
    scale: 1,
    hidden: false,
    modal: false,
    title: {
      text: ((mode == 'new') ? 'New' : 'Edit') +' User'
    },
    body: {
      style: {
        background: '#000'
      }
    },
    onclose: sysman.onUserEditWindowClose,
    content: html
  };

  var win = util.newWindow(opt);
  return win;
};

sysman.GetUserInfoCb = function(xhr, res) {
  if (res.status != 'OK') {
    sysman.showInfotip(res.status);
    return;
  }
  var info = res.body;
  sysman.setUserInfoToEditor(info);
};

sysman.setUserInfoToEditor = function(info) {
  var uid = info.uid;
  $el('#uid').value = uid;
  if (uid) {
    $el('#uid').disabled = true;
    $el('#uid').addClass('edit-disabled');
  } else {
    $el('#uid').disabled = false;
    $el('#uid').removeClass('edit-disabled');
  }
  $el('#name').value = info.name;
  $el('#local_name').value = info.local_name;
  $el('#isadmin').checked = info.is_admin;
  $el('#group').value = info.group;
  $el('#privs').value = info.privs;
  $el('#desc').value = (info.desc ? info.desc : '');
  $el('#status').value = info.status;
};

sysman.clearUserInfoEditor = function() {
  var info = {
    uid: '',
    name: '',
    local_name: '',
    is_admin: false,
    group: '',
    privs: '',
    desc: '',
    status: ''
  };
  sysman.setUserInfoToEditor(info);
};

sysman.saveUserInfo = function() {
  if (sysman.userEditMode == 'new') {
    sysman.addUser();
  } else {
    sysman.updateUser();
  }
};

//-----------------------------------------------------------------------------
sysman.addUser = function() {
  var uid = $el('#uid').value;
  var name = $el('#name').value;
  var local_name = $el('#local_name').value;
  var isAdmin = ($el('#isadmin').checked ? 'true' : 'false');
  var group = $el('#group').value;
  var privs = $el('#privs').value;
  var desc = $el('#desc').value;
  var status = $el('#status').value.trim();
  var pw1 = $el('#pw1').value;
  var pw2 = $el('#pw2').value;

  var clnsRes = sysman.cleanseUsername(uid);
  if (clnsRes.msg) {
    sysman.showInfotip(clnsRes.msg, 2000);
    return;
  }
  uid = clnsRes.val;

  clnsRes = sysman.cleanseFullName(name);
  if (clnsRes.msg) {
    sysman.showInfotip(clnsRes.msg, 2000);
    return;
  }
  name = clnsRes.val;

  clnsRes = sysman.cleanseFullName(local_name);
  if (clnsRes.msg) {
    sysman.showInfotip(clnsRes.msg, 2000);
    return;
  }
  local_name = clnsRes.val;

  clnsRes = sysman.cleanseGroups(group);
  if (clnsRes.msg) {
    sysman.showInfotip(clnsRes.msg, 2000);
    return;
  }
  group = clnsRes.val;

  clnsRes = sysman.cleansePrivileges(privs);
  if (clnsRes.msg) {
    sysman.showInfotip(clnsRes.msg, 2000);
    return;
  }
  privs = clnsRes.val;

  clnsRes = sysman.cleansePW(pw1, pw2, 'new');
  if (clnsRes.msg) {
    sysman.showInfotip(clnsRes.msg, 2000);
    return;
  }
  var pw = clnsRes.val;
  pw = websys.getUserPwHash(uid, pw);

  var params = {
    uid: uid,
    name: name,
    local_name: local_name,
    admin: isAdmin,
    group: group,
    privs: privs,
    desc: desc,
    st: status,
    pw: pw
  };

  sysman.execCmd('useradd', params, sysman.updateUserCb);
};

sysman.addUserCb = function(xhr, res) {
  sysman.showInfotip(res.status);
  if (res.status != 'OK') {
    return;
  }
  sysman.userEditWindow.close();
  sysman.getUserList();
};

//-----------------------------------------------------------------------------
sysman.updateUser = function() {
  var uid = $el('#uid').value;
  var name = $el('#name').value;
  var local_name = $el('#local_name').value;
  var isAdmin = ($el('#isadmin').checked ? 'true' : 'false');
  var group = $el('#group').value;
  var privs = $el('#privs').value;
  var desc = $el('#desc').value;
  var status = $el('#status').value;
  var pw1 = $el('#pw1').value;
  var pw2 = $el('#pw2').value;

  var clnsRes = sysman.cleansePW(pw1, pw2, 'edit');
  if (clnsRes.msg) {
    sysman.showInfotip(clnsRes.msg, 2000);
    return;
  }
  var pw = clnsRes.val;

  var params = {
    uid: uid,
    name: name,
    local_name: local_name,
    admin: isAdmin,
    group: group,
    privs: privs,
    desc: desc,
    st: status
  };

  if (pw) {
    params.pw = websys.getUserPwHash(uid, pw);
  }

  sysman.execCmd('usermod', params, sysman.updateUserCb);
};

sysman.updateUserCb = function(xhr, res) {
  sysman.showInfotip(res.status);
  if (res.status != 'OK') {
    return;
  }
  sysman.userEditWindow.close();
  sysman.getUserList();
};

//-----------------------------------------------------------------------------
sysman.deleteUser = function(uid) {
  var opt = {
    data: uid
  };
  util.confirm('Delete ' + uid + ' ?', sysman._deleteUser, opt);
};
sysman._deleteUser = function(uid) {
  if (!uid) {
    return;
  }
  if (sysman.userEditWindow) {
    sysman.userEditWindow.close();
  }
  var params = {
    uid: uid
  };
  sysman.execCmd('userdel', params, sysman.deleteUserCb);
};

sysman.deleteUserCb = function(xhr, res) {
  if (res.status != 'OK') {
    sysman.showInfotip(res.status);
    return;
  }
  sysman.showInfotip('OK');
  sysman.getUserList();
};

//-----------------------------------------------------------------------------
sysman.confirmClearLoginFailedCount = function(uid) {
  var opt = {
    data: uid
  };
  util.confirm('Clear failure count for ' + uid + ' ?', sysman.clearLoginFailedCount, opt);
};
sysman.clearLoginFailedCount = function(uid) {
  if (!uid) {
    return;
  }
  var params = {
    uid: uid
  };
  sysman.execCmd('unlockuser', params, sysman.clearLoginFailedCountCb);
};

sysman.clearLoginFailedCountCb = function(xhr, res) {
  if (res.status != 'OK') {
    sysman.showInfotip(res.status);
    return;
  }
  sysman.showInfotip('OK');
  sysman.getUserList();
};

//-----------------------------------------------------------------------------
sysman.sortList = function(itemList, sortKey, isDesc) {
  var items = util.copyObject(itemList);
  var srcList = items;
  var asNum = true;
  var sortedList = util.sortObjectList(srcList, sortKey, isDesc, asNum);
  return sortedList;
};

//-----------------------------------------------------------------------------
sysman.cleanseCommon = function(s) {
  s = s.trim();
  s = s.replace(/\t/g, ' ');
  var res = {
    val: s,
    msg: null
  };
  return res;
};

sysman.cleanseUsername = function(s) {
  var res = sysman.cleanseCommon(s);
  if (res.msg) {
    return res;
  }
  var msg = null;
  s = res.val;
  if (!s) {
    msg = 'Username is required';
  }
  res.val = s;
  res.msg = msg;
  return res;
};

sysman.cleanseFullName = function(s) {
  var res = sysman.cleanseCommon(s);
  if (res.msg) {
    return res;
  }
  var msg = null;
  s = res.val;
  res.val = s;
  res.msg = msg;
  return res;
};

sysman.cleanseLocalFullName = function(s) {
  var res = sysman.cleanseCommon(s);
  if (res.msg) {
    return res;
  }
  var msg = null;
  s = res.val;
  res.val = s;
  res.msg = msg;
  return res;
};

sysman.cleansePW = function(pw1, pw2, mode) {
  var msg = null;
  if (mode == 'new') {
    if (pw1 == '') {
      msg = 'Password is required';
    }
  }
  if ((pw1 != '') || (pw2 != '')) {
    if (pw1 != pw2) {
      msg = 'Password mismatched';
    }
  }
  var res = {
    val: pw1,
    msg: msg
  };
  return res;
};

sysman.cleanseGroups = function(s) {
  var res = sysman.cleanseCommon(s);
  if (res.msg) {
    return res;
  }
  var msg = null;
  s = res.val;
  s = s.replace(/\s{2,}/g, ' ');
  res.val = s;
  res.msg = msg;
  return res;
};

sysman.cleansePrivileges = function(s) {
  var res = sysman.cleanseCommon(s);
  if (res.msg) {
    return res;
  }
  var msg = null;
  s = res.val;
  s = s.replace(/\s{2,}/g, ' ');
  res.val = s;
  res.msg = msg;
  return res;
};

//-----------------------------------------------------------------------------
sysman.drawGroupStatus = function(s) {
  $el('#groups-status').innerHTML = s;
};

sysman.getGroupList = function() {
  sysman.callApi('get_group_list', null, sysman.getGroupListCb);
};
sysman.getGroupListCb = function(xhr, res) {
  if (res.status == 'OK') {
    sysman.drawGroupStatus('');
    var list = res.body.group_list;
    sysman.drawGroupList(list);
  }
};

sysman.drawGroupList = function(list) {
  var html = '<table>';
  html += '<tr class="item-list-header">';
  html += '<th class="item-list" style="min-width:10em;">GID</th>';
  html += '<th class="item-list" style="min-width:20em;">Prvileges</th>';
  html += '<th class="item-list" style="min-width:20em;">Description</th>';
  html += '<th class="item-list">Created</th>';
  html += '<th class="item-list">Updated</th>';
  html += '</tr>';

  for (var i = 0; i < list.length; i++) {
    var group = list[i];
    var gid = group.gid;
    var privs = (group.privs ? group.privs : '');
    var desc = (group.desc ? group.desc : '');

    var createdDate = '---------- --:--:--.---';
    if (group.created_at > 0) {
      var createdAt = group.created_at;
      if (util.isInteger(createdAt)) createdAt *= 1000;
      createdDate = util.getDateTimeString(createdAt, '%YYYY-%MM-%DD %HH:%mm:%SS.%sss');
    }

    var updatedDate = '---------- --:--:--.---';
    if (group.updated_at > 0) {
      var updatedAt = group.updated_at;
      if (util.isInteger(updatedAt)) updatedAt *= 1000;
      updatedDate = util.getDateTimeString(updatedAt, '%YYYY-%MM-%DD %HH:%mm:%SS.%sss');
    }

    html += '<tr class="item-list">';
    html += '<td class="item-list"><span class="pseudo-link link-button" onclick="sysman.editGroup(\'' + gid + '\');" data-tooltip="Edit">' + gid + '</span></td>';
    html += '<td class="item-list">' + privs + '</td>';
    html += '<td class="item-list">' + desc + '</td>';
    html += '<td class="item-list">' + createdDate + '</td>';
    html += '<td class="item-list">' + updatedDate + '</td>';
    html += '</tr>';
  }
  html += '</table>';
  $el('#group-list').innerHTML = html;
};

//-----------------------------------------------------------------------------
sysman.newGroup = function() {
  sysman.editGroup(null);
};

sysman.editGroup = function(gid) {
  sysman.groupEditMode = (gid ? 'edit' : 'new');
  if (!sysman.groupEditWindow) {
    sysman.groupEditWindow = sysman.openGroupInfoEditorWindow(sysman.groupEditMode, gid);
  }
  sysman.clearGroupInfoEditor();
  if (gid) {
    var params = {
      gid: gid
    };
    sysman.execCmd('group', params, sysman.getGroupInfoCb);
  } else {
    $el('#gid').focus();
  }
};

sysman.openGroupInfoEditorWindow = function(mode, gid) {
  var html = '';
  html += '<div style="position:relative;width:100%;height:100%;text-align:center;vertical-align:middle">';
  html += '<div style="position:absolute;top:8px;right:8px;"><button class="button-red" onclick="sysman.deleteGroup(\'' + gid + '\');">DEL</button></div>';
  html += '<div style="padding:4px;position:absolute;top:0;right:0;bottom:0;left:0;margin:auto;width:360px;height:110px;text-align:left;">';

  html += '<table>';
  html += '  <tr>';
  html += '    <td>GID</td>';
  html += '    <td style="width:256px;">';
  html += '      <input type="text" id="gid" style="width:100%;">';
  html += '    </td>';
  html += '  </tr>';
  html += '  <tr>';
  html += '    <td>Privileges</td>';
  html += '    <td><input type="text" id="group-privs" style="width:100%;"></td>';
  html += '  </tr>';
  html += '  <tr>';
  html += '    <td>Description</td>';
  html += '    <td><input type="text" id="group-desc" style="width:100%;"></td>';
  html += '  </tr>';
  html += '<table>';

  html += '<div style="margin-top:24px;text-align:center;">';
  html += '<button onclick="sysman.saveGroupInfo();">OK</button>'
  html += '<button style="margin-left:8px;" onclick="sysman.groupEditWindow.close();">Cancel</button>'
  html += '</div>';

  html += '</div>';
  html += '</div>';

  var opt = {
    draggable: true,
    resizable: true,
    pos: 'c',
    closeButton: true,
    width: 480,
    height: 200,
    minWidth: 480,
    minHeight: 360,
    scale: 1,
    hidden: false,
    modal: false,
    title: {
      text: ((mode == 'new') ? 'New' : 'Edit') +' Group'
    },
    body: {
      style: {
        background: '#000'
      }
    },
    onclose: sysman.onGroupEditWindowClose,
    content: html
  };

  var win = util.newWindow(opt);
  return win;
};

//-----------------------------------------------------------------------------
sysman.addGroup = function() {
  var gid = $el('#gid').value;
  var privs = $el('#group-privs').value;
  var desc = $el('#group-desc').value;

  clnsRes = sysman.cleansePrivileges(privs);
  if (clnsRes.msg) {
    sysman.showInfotip(clnsRes.msg, 2000);
    return;
  }
  privs = clnsRes.val;

  var params = {
    gid: gid,
    privs: privs,
    desc: desc
  };

  sysman.execCmd('addgroup', params, sysman.addGroupCb);
};

sysman.addGroupCb = function(xhr, res) {
  sysman.showInfotip(res.status);
  if (res.status != 'OK') {
    return;
  }
  sysman.groupEditWindow.close();
  sysman.getGroupList();
};

//-----------------------------------------------------------------------------
sysman.updateGroup = function() {
  var gid = $el('#gid').value;
  var privs = $el('#group-privs').value;
  var desc = $el('#group-desc').value;

  var params = {
    gid: gid,
    privs: privs,
    desc: desc
  };

  sysman.execCmd('modgroup', params, sysman.updateGroupCb);
};

sysman.updateGroupCb = function(xhr, res) {
  sysman.showInfotip(res.status);
  if (res.status != 'OK') {
    return;
  }
  sysman.groupEditWindow.close();
  sysman.getGroupList();
};

//-----------------------------------------------------------------------------
sysman.deleteGroup = function(gid) {
  var opt = {
    data: gid
  };
  util.confirm('Delete ' + gid + ' ?', sysman._deleteGroup, opt);
};
sysman._deleteGroup = function(gid) {
  if (!gid) {
    return;
  }
  if (sysman.groupEditWindow) {
    sysman.groupEditWindow.close();
  }
  var params = {
    gid: gid
  };
  sysman.execCmd('delgroup', params, sysman.deleteGroupCb);
};

sysman.deleteGroupCb = function(xhr, res) {
  if (res.status != 'OK') {
    sysman.showInfotip(res.status);
    return;
  }
  sysman.showInfotip('OK');
  sysman.getGroupList();
};

//-----------------------------------------------------------------------------
sysman.getGroupInfoCb = function(xhr, res) {
  if (res.status != 'OK') {
    sysman.showInfotip(res.status);
    return;
  }
  var info = res.body;
  sysman.setGroupInfoToEditor(info);
};

sysman.setGroupInfoToEditor = function(info) {
  var gid = info.gid;
  $el('#gid').value = gid;
  if (gid) {
    $el('#gid').disabled = true;
    $el('#gid').addClass('edit-disabled');
  } else {
    $el('#gid').disabled = false;
    $el('#gid').removeClass('edit-disabled');
  }
  $el('#group-privs').value = info.privs;
  $el('#group-desc').value = (info.desc ? info.desc : '');
};

sysman.clearGroupInfoEditor = function() {
  var info = {
    gid: '',
    privs: '',
    desc: ''
  };
  sysman.setGroupInfoToEditor(info);
};

sysman.saveGroupInfo = function() {
  if (sysman.groupEditMode == 'new') {
    sysman.addGroup();
  } else {
    sysman.updateGroup();
  }
};

//-----------------------------------------------------------------------------
sysman.onUserEditWindowClose = function() {
  sysman.userEditWindow = null;
  sysman.userEditMode = null;
};

sysman.onGroupEditWindowClose = function() {
  sysman.groupEditWindow = null;
  sysman.groupEditMode = null;
};

$onCtrlS = function(e) {
};

$onBeforeUnload = function(e) {
  if ((sysman.userEditWindow) || (sysman.groupEditWindow)) e.returnValue = '';
};
