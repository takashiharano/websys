/*!
 * Copyright (c) 2023 Takashi Harano
 */
var sysmgr = {};
sysmgr.INSEC = true;
sysmgr.dialogFgColor = '#fff';
sysmgr.dialogBgColor = '#000';
sysmgr.dialogTitleFgColor = '#fff';
sysmgr.dialogTitleBgColor = 'linear-gradient(150deg, rgba(0,32,255,0.8),rgba(0,82,255,0.8))';

sysmgr.LED_COLORS = [
  {t: 10 * util.MINUTE, color: '#0f0'},
  {t: 8 * util.HOUR, color: '#cc0'},
  {t: 0, color: '#a44'},
];

sysmgr.INTERVAL = 60000;
sysmgr.USER_LIST_COLUMNS = [
  {key: 'uid', label: 'UID', style: 'min-width:10em;'},
  {key: 'name', label: 'Full Name', style: 'min-width:10em;'},
  {key: 'local_name', label: 'Local Full Name', style: 'min-width:10em;'},
  {key: 'is_admin', label: 'Admin'},
  {key: 'group', label: 'Groups', style: 'min-width:15em;'},
  {key: 'privs', label: 'Privileges', style: 'min-width:10em;'},
  {key: 'desc', label: 'Description', style: 'min-width:15em;'},
  {key: 'flags', label: 'Flags'},
  {key: 'status_info.login_failed_count', label: 'Fail', sort: false},
  {key: 'status_info.sessions', label: 'S'},
  {key: 'status_info.last_accessed', label: 'Last Accessed'},
  {key: 'status_info.last_login', label: 'Last Login'},
  {key: 'status_info.last_logout', label: 'Last Logout'},
  {key: 'created_at', label: 'Created'},
  {key: 'updated_at', label: 'Updated'},
  {key: 'status_info.pw_changed_at', label: 'PwChanged'}
];

sysmgr.listStatus = {
  sortIdx: 0,
  sortOrder: 1
};

sysmgr.userList = [];
sysmgr.sessions = null;
sysmgr.userEditWindow = null;
sysmgr.groupEditWindow = null;
sysmgr.userEditMode = null;
sysmgr.groupEditMode = null;
sysmgr.tmrId = 0;
sysmgr.interval = 0;

$onReady = function() {
  util.clock('#clock');
  $el('#user-list').innerHTML = '<span class="progdot">Loading</span>';
  sysmgr.drawGroupStatus('<span class="progdot">Loading</span>');
};

sysmgr.onSysReady = function() {
  sysmgr.reload();
  sysmgr.queueNextUpdateSessionInfo();
};

sysmgr.reload = function() {
  sysmgr.reloadUserInfo();
  sysmgr.getGroupList();
};

sysmgr.reloadUserInfo = function() {
  sysmgr.getUserList();
  sysmgr.getSessionList();
};

sysmgr.queueNextUpdateSessionInfo = function() {
  sysmgr.tmrId = setTimeout(sysmgr.updateSessionInfo, sysmgr.INTERVAL);
};

sysmgr.updateSessionInfo = function() {
  sysmgr.interval = 1;
  sysmgr.reloadUserInfo();
};

sysmgr.callApi = function(act, params, cb) {
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
  sysmgr.http(req, cb);
};

sysmgr.execCmd = function(act, params, cb) {
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
  sysmgr.http(req, cb);
};

sysmgr.http = function(req, cb) {
  req.cb = cb;
  websys.http(req);
};

sysmgr.showInfotip = function(m, d) {
  var opt = {
    style: {
      'font-size': '14px'
    }
  };
  util.infotip.show(m, d, opt);
};

sysmgr.getUserList = function() {
  sysmgr.callApi('get_user_list', null, sysmgr.getUserListCb);
};
sysmgr.getUserListCb = function(xhr, res, req) {
  if (res.status == 'FORBIDDEN') {
    location.href = location.href;
    return;
  } else if (res.status != 'OK') {
    sysmgr.showInfotip(res.status);
    return;
  }
  var users = res.body;
  var infoList = [];
  for (var uid in users) {
    var user = users[uid];
    infoList.push(user);
  }
  sysmgr.userList = infoList;
  sysmgr.drawList(infoList, 0, 1);
};

sysmgr.buildListHeader = function(columns, sortIdx, sortOrder) {
  var html = '<table>';
  html += '<tr class="item-list-header">';
  html += '<th class="item-list">&nbsp;</th>';

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
    sortButton += ' onclick="sysmgr.sortItemList(' + i + ', ' + nextSortType + ');"';
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

sysmgr.drawList = function(items, sortIdx, sortOrder) {
  var now = util.now();
  var currentUid = websys.getUserId();

  if (sortIdx >= 0) {
    if (sortOrder > 0) {
      var srtDef = sysmgr.USER_LIST_COLUMNS[sortIdx];
      var desc = (sortOrder == 2);
      items = sysmgr.sortList(items, srtDef.key, desc, srtDef.meta);
    }
  }

  var htmlList = '';
  for (var i = 0; i < items.length; i++) {
    var item = items[i];
    var uid = item.uid;
    var name = item.name.replace(/ /g, '&nbsp');
    var local_name = item.local_name.replace(/ /g, '&nbsp');
    var statusInfo = item.status_info;
    var loginFailedCount = statusInfo.login_failed_count;
    var loginFailedTime = util.getDateTimeString(statusInfo.login_failed_time);
    var sessions = statusInfo.sessions;
    var lastAccessedDate = sysmgr.getDateTimeString(statusInfo.last_accessed, sysmgr.INSEC);
    var lastLoginDate = sysmgr.getDateTimeString(statusInfo.last_login, sysmgr.INSEC);
    var lastLogoutDate = sysmgr.getDateTimeString(statusInfo.last_logout, sysmgr.INSEC);
    var createdDate = sysmgr.getDateTimeString(item.created_at, sysmgr.INSEC);
    var updatedDate = sysmgr.getDateTimeString(item.updated_at, sysmgr.INSEC);
    var pwChangedDate = sysmgr.getDateTimeString(statusInfo.pw_changed_at, sysmgr.INSEC);
    var desc = (item.desc ? item.desc : '');
    var escDesc = util.escHtml(desc);
    var dispDesc = '<span style="display:inline-block;width:100%;overflow:hidden;text-overflow:ellipsis;"';
    if (util.lenW(desc) > 35) {
      dispDesc += ' data-tooltip="' + escDesc + '"';
    }
    dispDesc += '>' + escDesc + '</span>';
    var active = (sessions > 0);
    var led = sysmgr.buildLedHtml(now, statusInfo.last_accessed, sysmgr.INSEC, active);

    var cInd = ((uid == currentUid) ? '<span class="text-skyblue" style="cursor:default;margin-right:2px;" data-tooltip="You">*</span>' : '<span style="margin-right:2px;">&nbsp;</span>');
    var dispUid = cInd + '<span class="pseudo-link link-button" onclick="sysmgr.editUser(\'' + uid + '\');" data-tooltip="Edit">' + uid + '</span>';

    htmlList += '<tr class="item-list">';
    htmlList += '<td class="item-list" style="text-align:center;">' + led + '</td>';
    htmlList += '<td class="item-list" style="padding-right:10px;">' + dispUid + '</td>';
    htmlList += '<td class="item-list">' + name + '</td>';
    htmlList += '<td class="item-list">' + local_name + '</td>';
    htmlList += '<td class="item-list" style="text-align:center;">' + (item.is_admin ? 'Y' : '') + '</td>';
    htmlList += '<td class="item-list">' + item.group + '</td>';
    htmlList += '<td class="item-list">' + item.privs + '</td>';
    htmlList += '<td class="item-list" style="max-width:20em">' + dispDesc + '</td>';
    htmlList += '<td class="item-list" style="text-align:center;">' + item.flags + '</td>';

    htmlList += '<td class="item-list" style="text-align:center;width:1.5em;">';
    if (loginFailedCount > 0) {
      var clz = 'pseudo-link';
      if ((sysmgr.websysconf.LOGIN_FAILURE_MAX > 0) && (loginFailedCount >= sysmgr.websysconf.LOGIN_FAILURE_MAX)) {
        clz += ' text-red';
      }
      htmlList += '<span class="' + clz + '" data-tooltip="' + loginFailedTime + '" onclick="sysmgr.confirmClearLoginFailedCount(\'' + uid + '\');">' + loginFailedCount + '</span>';
    } else {
      htmlList += '';
    }
    htmlList += '</td>';

    htmlList += '<td class="item-list" style="text-align:right;">' + sessions + '</td>';
    htmlList += '<td class="item-list" style="text-align:center;">' + lastAccessedDate + '</td>';
    htmlList += '<td class="item-list" style="text-align:center;">' + lastLoginDate + '</td>';
    htmlList += '<td class="item-list" style="text-align:center;">' + lastLogoutDate + '</td>';
    htmlList += '<td class="item-list" style="text-align:center;">' + createdDate + '</td>';
    htmlList += '<td class="item-list" style="text-align:center;">' + updatedDate + '</td>';
    htmlList += '<td class="item-list" style="text-align:center;">' + pwChangedDate + '</td>';
    htmlList += '</tr>';
  }
  htmlList += '</table>';

  var htmlHead = sysmgr.buildListHeader(sysmgr.USER_LIST_COLUMNS, sortIdx, sortOrder);
  var html = htmlHead + htmlList; 

  sysmgr.drawListContent(html);
};

sysmgr.buildLedHtml = function(now, ts, inSec, active) {
  var COLORS = sysmgr.LED_COLORS;
  var tMs = ts;
  if (inSec) tMs = Math.floor(tMs * 1000);
  var elapsed = now - tMs;
  var ledColor = '#888';
  if (active) {
    for (var i = 0; i < COLORS.length; i++) {
      var c = COLORS[i];
      if ((elapsed <= c.t) || (c.t == 0)) {
        ledColor = c.color;
        break;
      }
    }
  }
  var dt = sysmgr.getDateTimeString(tMs);
  var html = '<span class="led" style="color:' + ledColor + ';" data-tooltip="' + dt + '"></span>';
  return html;
};

sysmgr.getDateTimeString = function(ts, inSec) {
  var tMs = ts;
  if (inSec) tMs = Math.floor(tMs * 1000);
  var s = '---------- --:--:--.---';
  if (tMs > 0) {
    s = util.getDateTimeString(tMs, '%YYYY-%MM-%DD %HH:%mm:%SS.%sss');
  }
  return s;
};

sysmgr.getSessionList = function() {
  if (sysmgr.tmrId > 0) {
    clearTimeout(sysmgr.tmrId);
    sysmgr.tmrId = 0;
    sysmgr.interval = 1;
  }
  sysmgr.callApi('get_session_list', null, sysmgr.getSessionListCb);
};
sysmgr.getSessionListCb = function(xhr, res, req) {
  if (res.status == 'FORBIDDEN') {
    location.href = location.href;
    return;
  } else if (res.status != 'OK') {
    sysmgr.showInfotip(res.status);
    return;
  }
  var sessions = res.body;
  sysmgr.sessions = sessions;
  sysmgr.drawSessionList(sessions);

  if (sysmgr.interval) {
    sysmgr.interval = 0;
    sysmgr.queueNextUpdateSessionInfo();
  }
};

sysmgr.drawSessionList = function(sessions) {
  var now = util.now();
  var html = '<table>';
  html += '<tr style="font-weight:bold;">';
  html += '<td></td>';
  html += '<td>UID</td>';
  html += '<td>Name</td>';
  html += '<td><span style="margin-left:8px;">Session</span></td>';
  html += '<td>Last Accessed</td>';
  html += '<td style="min-width:98px;"">Elapsed</td>';
  html += '<td style="font-weight:normal;">' + sysmgr.buildTimeLineHeader(now) + '</td>';
  html += '<td>Addr</td>';
  html += '<td>User-Agent</td>';
  html += '<td>Logged in</td>';
  html += '</tr>';
  html += sysmgr.buildSessionInfoHtml(sessions, now);
  html += '</table>';
  $el('#session-list').innerHTML = html;
};

sysmgr.buildTimeLineHeader = function(now) {
  var currentInd = '<span class="blink1 text-skyblue">v</span>';

  var nowYYYYMMDD = util.getDateTimeString(now, '%YYYY%MM%DD');
  var nowHHMM = util.getDateTimeString(now, '%HH:%mm');
  var tmp = nowHHMM.split(':');
  var nowHH = tmp[0];
  var nowMM = tmp[1];

  var html = '';
  for (var i = 0; i <= 23; i++) {
    var ts = sysmgr.getTimeSlot(i, nowHH, nowMM);
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

sysmgr.buildSessionInfoHtml = function(sessions, now) {
  var html = '';
  if (!sessions) return html;
  var mn = util.getMidnightTimestamp(now);
  for (var i = 0; i < sessions.length; i++) {
    var session = sessions[i];
    html += sysmgr.buildSessionInfoOne(session, now, mn);
  }
  return html;
};
sysmgr.buildSessionInfoOne = function(session, now, mn) {
  var cSid = websys.getSessionId();
  var uid = session.uid;
  var name = session.user_name;
  var loginT = session.created_time;
  var la = session.last_accessed;
  var laTime = la['time'];
  if (sysmgr.INSEC) laTime = Math.floor(laTime * 1000);
  var loginTime = util.getDateTimeString(loginT, '%YYYY-%MM-%DD %HH:%mm:%SS.%sss');
  var laTimeStr = util.getDateTimeString(laTime, '%YYYY-%MM-%DD %HH:%mm:%SS.%sss');
  var sid = session['sid'];
  var ssid = util.snip(sid, 7, 3, '..');
  var sid7 = util.snip(sid, 7, 0, '');
  var addr = la['addr'];
  var brws = util.getBrowserInfo(la['ua']);
  var ua = brws.name + ' ' + brws.version;
  var led = sysmgr.buildLedHtml(now, laTime, false, true);
  var ssidLink = '<span class="pseudo-link link-button" onclick="sysmgr.confirmLogoutSession(\'' + uid + '\', \'' + sid + '\');" data-tooltip="' + sid + '">' + ssid + '</span>';
  var dispSid = ((sid == cSid) ? '<span class="text-skyblue" style="cursor:default;margin-right:2px;" data-tooltip="Current Session">*</span>' : '<span style="cursor:default;margin-right:2px;">&nbsp;</span>') + ssidLink;
  var timeId = 'tm-' + sid7;
  var tmspan = '<span id="' + timeId + '"></span>'
  var timeline = sysmgr.buildTimeLine(now, laTime);

  var html = '';
  html += '<tr class="item-list">';
  html += '<td style="padding-right:4px;">' + led + '</td>';
  html += '<td style="padding-right:10px;">' + uid + '</td>';
  html += '<td style="padding-right:6px;">' + name + '</td>';
  html += '<td style="padding-right:10px;">' + dispSid + '</td>';
  html += '<td style="padding-right:10px;">' + laTimeStr + '</td>';
  html += '<td style="padding-right:10px;text-align:right;">' + tmspan + '</td>';
  html += '<td>' + timeline + '</td>';
  html += '<td style="padding-right:10px;">' + addr + '</td>';
  html += '<td style="padding-right:10px;">' + ua + '</td>';
  html += '<td style="padding-right:10px;">' + loginTime + '</td>';
  html += '</tr>';

  setTimeout(sysmgr.startElapsedCounter, 0, {timeId: '#' + timeId, laTime: laTime});
  return html;
};
sysmgr.startElapsedCounter = function(param) {
  util.timecounter.start(param.timeId, param.laTime);
};
sysmgr.buildTimeLine = function(now, lastAccessedTime) {
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
      if ((accYYYYMMDD == nowYYYYMMDD) && (sysmgr.inTheTimeSlot(i, j, accHH, accMM))) {
        s = '</span><span style="color:#0f0;">*</span>' + span;
      }
      html += s;
      if (sysmgr.inTheTimeSlot(i, j, nowHH, nowMM)) {
        html += '<span style="opacity:0.5;">';
        f = true;
      }
    }
  }
  if (f) html += '</span>';
  html += '</span>';
  return html;
};

sysmgr.inTheTimeSlot = function(h, qM, hh, mm) {
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
sysmgr.getTimeSlot = function(h, hh, mm) {
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

sysmgr.drawListContent = function(html) {
  $el('#user-list').innerHTML = html;
};

sysmgr.sortItemList = function(sortIdx, sortOrder) {
  if (sortOrder > 2) {
    sortOrder = 0;
  }
  sysmgr.listStatus.sortIdx = sortIdx;
  sysmgr.listStatus.sortOrder = sortOrder;
  sysmgr.drawList(sysmgr.userList, sortIdx, sortOrder);
};

sysmgr.confirmLogoutSession = function(uid, sid) {
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
  util.confirm(m, sysmgr.logoutSession, {data: sid});
};
sysmgr.logoutSession = function(sid) {
  var params = {
    sid: sid
  };
  sysmgr.execCmd('logout', params, sysmgr.logoutSessionCb);
};
sysmgr.logoutSessionCb = function(xhr, res) {
  sysmgr.showInfotip(res.status);
  sysmgr.reloadUserInfo();
};

//-----------------------------------------------------------------------------
sysmgr.newUser = function() {
  sysmgr.editUser(null);
};

sysmgr.editUser = function(uid) {
  sysmgr.userEditMode = (uid ? 'edit' : 'new');
  if (!sysmgr.userEditWindow) {
    sysmgr.userEditWindow = sysmgr.openUserInfoEditorWindow(sysmgr.userEditMode, uid);
  }
  sysmgr.clearUserInfoEditor();
  if (uid) {
    var params = {
      uid: uid
    };
    sysmgr.execCmd('user', params, sysmgr.GetUserInfoCb);
  } else {
    $el('#uid').focus();
  }
};

sysmgr.openUserInfoEditorWindow = function(mode, uid) {
  var currentUid = websys.getUserId();

  var html = '';
  html += '<div style="position:relative;width:100%;height:100%;text-align:center;vertical-align:middle">';
  if (uid && (uid != currentUid)) {
    html += '<div style="position:absolute;top:8px;right:8px;"><button class="button-red" onclick="sysmgr.deleteUser(\'' + uid + '\');">DEL</button></div>';
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
  html += '    <td>Flags</td>';
  html += '    <td><input type="text" id="flags" style="width:1.5em;"></td>';
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
  html += '<button onclick="sysmgr.saveUserInfo();">OK</button>'
  html += '<button style="margin-left:8px;" onclick="sysmgr.userEditWindow.close();">Cancel</button>'
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
      text: ((mode == 'new') ? 'New' : 'Edit') +' User',
      style: {
        color: sysmgr.dialogTitleFgColor,
        background: sysmgr.dialogTitleBgColor
      }
    },
    body: {
      style: {
        color: sysmgr.dialogFgColor,
        background: sysmgr.dialogBgColor
      }
    },
    onclose: sysmgr.onUserEditWindowClose,
    content: html
  };

  var win = util.newWindow(opt);
  return win;
};

sysmgr.GetUserInfoCb = function(xhr, res) {
  if (res.status != 'OK') {
    sysmgr.showInfotip(res.status);
    return;
  }
  var info = res.body;
  sysmgr.setUserInfoToEditor(info);
};

sysmgr.setUserInfoToEditor = function(info) {
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
  $el('#flags').value = info.flags;
};

sysmgr.clearUserInfoEditor = function() {
  var info = {
    uid: '',
    name: '',
    local_name: '',
    is_admin: false,
    group: '',
    privs: '',
    desc: '',
    flags: ''
  };
  sysmgr.setUserInfoToEditor(info);
};

sysmgr.saveUserInfo = function() {
  if (sysmgr.userEditMode == 'new') {
    sysmgr.addUser();
  } else {
    sysmgr.updateUser();
  }
};

//-----------------------------------------------------------------------------
sysmgr.addUser = function() {
  var uid = $el('#uid').value;
  var name = $el('#name').value;
  var local_name = $el('#local_name').value;
  var isAdmin = ($el('#isadmin').checked ? 'true' : 'false');
  var group = $el('#group').value;
  var privs = $el('#privs').value;
  var desc = $el('#desc').value;
  var flags = $el('#flags').value.trim();
  var pw1 = $el('#pw1').value;
  var pw2 = $el('#pw2').value;

  var clnsRes = sysmgr.cleanseUsername(uid);
  if (clnsRes.msg) {
    sysmgr.showInfotip(clnsRes.msg, 2000);
    return;
  }
  uid = clnsRes.val;

  clnsRes = sysmgr.cleanseFullName(name);
  if (clnsRes.msg) {
    sysmgr.showInfotip(clnsRes.msg, 2000);
    return;
  }
  name = clnsRes.val;

  clnsRes = sysmgr.cleanseFullName(local_name);
  if (clnsRes.msg) {
    sysmgr.showInfotip(clnsRes.msg, 2000);
    return;
  }
  local_name = clnsRes.val;

  clnsRes = sysmgr.cleanseGroups(group);
  if (clnsRes.msg) {
    sysmgr.showInfotip(clnsRes.msg, 2000);
    return;
  }
  group = clnsRes.val;

  clnsRes = sysmgr.cleansePrivileges(privs);
  if (clnsRes.msg) {
    sysmgr.showInfotip(clnsRes.msg, 2000);
    return;
  }
  privs = clnsRes.val;

  clnsRes = sysmgr.cleansePW(pw1, pw2, 'new');
  if (clnsRes.msg) {
    sysmgr.showInfotip(clnsRes.msg, 2000);
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
    flags: flags,
    pw: pw
  };

  sysmgr.execCmd('useradd', params, sysmgr.updateUserCb);
};

sysmgr.addUserCb = function(xhr, res) {
  sysmgr.showInfotip(res.status);
  if (res.status != 'OK') {
    return;
  }
  sysmgr.userEditWindow.close();
  sysmgr.getUserList();
};

//-----------------------------------------------------------------------------
sysmgr.updateUser = function() {
  var uid = $el('#uid').value;
  var name = $el('#name').value;
  var local_name = $el('#local_name').value;
  var isAdmin = ($el('#isadmin').checked ? 'true' : 'false');
  var group = $el('#group').value;
  var privs = $el('#privs').value;
  var desc = $el('#desc').value;
  var flags = $el('#flags').value;
  var pw1 = $el('#pw1').value;
  var pw2 = $el('#pw2').value;

  var clnsRes = sysmgr.cleansePW(pw1, pw2, 'edit');
  if (clnsRes.msg) {
    sysmgr.showInfotip(clnsRes.msg, 2000);
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
    flags: flags
  };

  if (pw) {
    params.pw = websys.getUserPwHash(uid, pw);
  }

  sysmgr.execCmd('usermod', params, sysmgr.updateUserCb);
};

sysmgr.updateUserCb = function(xhr, res) {
  sysmgr.showInfotip(res.status);
  if (res.status != 'OK') {
    return;
  }
  sysmgr.userEditWindow.close();
  sysmgr.getUserList();
};

//-----------------------------------------------------------------------------
sysmgr.deleteUser = function(uid) {
  var opt = {
    data: uid
  };
  util.confirm('Delete ' + uid + ' ?', sysmgr._deleteUser, opt);
};
sysmgr._deleteUser = function(uid) {
  if (!uid) {
    return;
  }
  if (sysmgr.userEditWindow) {
    sysmgr.userEditWindow.close();
  }
  var params = {
    uid: uid
  };
  sysmgr.execCmd('userdel', params, sysmgr.deleteUserCb);
};

sysmgr.deleteUserCb = function(xhr, res) {
  if (res.status != 'OK') {
    sysmgr.showInfotip(res.status);
    return;
  }
  sysmgr.showInfotip('OK');
  sysmgr.getUserList();
};

//-----------------------------------------------------------------------------
sysmgr.confirmClearLoginFailedCount = function(uid) {
  var opt = {
    data: uid
  };
  util.confirm('Clear failure count for ' + uid + ' ?', sysmgr.clearLoginFailedCount, opt);
};
sysmgr.clearLoginFailedCount = function(uid) {
  if (!uid) {
    return;
  }
  var params = {
    uid: uid
  };
  sysmgr.execCmd('unlockuser', params, sysmgr.clearLoginFailedCountCb);
};

sysmgr.clearLoginFailedCountCb = function(xhr, res) {
  if (res.status != 'OK') {
    sysmgr.showInfotip(res.status);
    return;
  }
  sysmgr.showInfotip('OK');
  sysmgr.getUserList();
};

//-----------------------------------------------------------------------------
sysmgr.sortList = function(itemList, sortKey, isDesc) {
  var items = util.copyObject(itemList);
  var srcList = items;
  var asNum = true;
  var sortedList = util.sortObjectList(srcList, sortKey, isDesc, asNum);
  return sortedList;
};

//-----------------------------------------------------------------------------
sysmgr.cleanseCommon = function(s) {
  s = s.trim();
  s = s.replace(/\t/g, ' ');
  var res = {
    val: s,
    msg: null
  };
  return res;
};

sysmgr.cleanseUsername = function(s) {
  var res = sysmgr.cleanseCommon(s);
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

sysmgr.cleanseFullName = function(s) {
  var res = sysmgr.cleanseCommon(s);
  if (res.msg) {
    return res;
  }
  var msg = null;
  s = res.val;
  res.val = s;
  res.msg = msg;
  return res;
};

sysmgr.cleanseLocalFullName = function(s) {
  var res = sysmgr.cleanseCommon(s);
  if (res.msg) {
    return res;
  }
  var msg = null;
  s = res.val;
  res.val = s;
  res.msg = msg;
  return res;
};

sysmgr.cleansePW = function(pw1, pw2, mode) {
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

sysmgr.cleanseGroups = function(s) {
  var res = sysmgr.cleanseCommon(s);
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

sysmgr.cleansePrivileges = function(s) {
  var res = sysmgr.cleanseCommon(s);
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
sysmgr.drawGroupStatus = function(s) {
  $el('#groups-status').innerHTML = s;
};

sysmgr.getGroupList = function() {
  sysmgr.callApi('get_group_list', null, sysmgr.getGroupListCb);
};
sysmgr.getGroupListCb = function(xhr, res) {
  if (res.status == 'OK') {
    sysmgr.drawGroupStatus('');
    var list = res.body.group_list;
    sysmgr.drawGroupList(list);
  }
};

sysmgr.drawGroupList = function(list) {
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
    var createdDate = sysmgr.getDateTimeString(group.created_at, sysmgr.INSEC);
    var updatedDate = sysmgr.getDateTimeString(group.updated_at, sysmgr.INSEC);

    html += '<tr class="item-list">';
    html += '<td class="item-list"><span class="pseudo-link link-button" onclick="sysmgr.editGroup(\'' + gid + '\');" data-tooltip="Edit">' + gid + '</span></td>';
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
sysmgr.newGroup = function() {
  sysmgr.editGroup(null);
};

sysmgr.editGroup = function(gid) {
  sysmgr.groupEditMode = (gid ? 'edit' : 'new');
  if (!sysmgr.groupEditWindow) {
    sysmgr.groupEditWindow = sysmgr.openGroupInfoEditorWindow(sysmgr.groupEditMode, gid);
  }
  sysmgr.clearGroupInfoEditor();
  if (gid) {
    var params = {
      gid: gid
    };
    sysmgr.execCmd('group', params, sysmgr.getGroupInfoCb);
  } else {
    $el('#gid').focus();
  }
};

sysmgr.openGroupInfoEditorWindow = function(mode, gid) {
  var html = '';
  html += '<div style="position:relative;width:100%;height:100%;text-align:center;vertical-align:middle">';
  html += '<div style="position:absolute;top:8px;right:8px;"><button class="button-red" onclick="sysmgr.deleteGroup(\'' + gid + '\');">DEL</button></div>';
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
  html += '<button onclick="sysmgr.saveGroupInfo();">OK</button>'
  html += '<button style="margin-left:8px;" onclick="sysmgr.groupEditWindow.close();">Cancel</button>'
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
      text: ((mode == 'new') ? 'New' : 'Edit') +' Group',
      style: {
        color: sysmgr.dialogTitleFgColor,
        background: sysmgr.dialogTitleBgColor
      }
    },
    body: {
      style: {
        color: sysmgr.dialogFgColor,
        background: sysmgr.dialogBgColor
      }
    },
    onclose: sysmgr.onGroupEditWindowClose,
    content: html
  };

  var win = util.newWindow(opt);
  return win;
};

//-----------------------------------------------------------------------------
sysmgr.addGroup = function() {
  var gid = $el('#gid').value;
  var privs = $el('#group-privs').value;
  var desc = $el('#group-desc').value;

  clnsRes = sysmgr.cleansePrivileges(privs);
  if (clnsRes.msg) {
    sysmgr.showInfotip(clnsRes.msg, 2000);
    return;
  }
  privs = clnsRes.val;

  var params = {
    gid: gid,
    privs: privs,
    desc: desc
  };

  sysmgr.execCmd('addgroup', params, sysmgr.addGroupCb);
};

sysmgr.addGroupCb = function(xhr, res) {
  sysmgr.showInfotip(res.status);
  if (res.status != 'OK') {
    return;
  }
  sysmgr.groupEditWindow.close();
  sysmgr.getGroupList();
};

//-----------------------------------------------------------------------------
sysmgr.updateGroup = function() {
  var gid = $el('#gid').value;
  var privs = $el('#group-privs').value;
  var desc = $el('#group-desc').value;

  var params = {
    gid: gid,
    privs: privs,
    desc: desc
  };

  sysmgr.execCmd('modgroup', params, sysmgr.updateGroupCb);
};

sysmgr.updateGroupCb = function(xhr, res) {
  sysmgr.showInfotip(res.status);
  if (res.status != 'OK') {
    return;
  }
  sysmgr.groupEditWindow.close();
  sysmgr.getGroupList();
};

//-----------------------------------------------------------------------------
sysmgr.deleteGroup = function(gid) {
  var opt = {
    data: gid
  };
  util.confirm('Delete ' + gid + ' ?', sysmgr._deleteGroup, opt);
};
sysmgr._deleteGroup = function(gid) {
  if (!gid) {
    return;
  }
  if (sysmgr.groupEditWindow) {
    sysmgr.groupEditWindow.close();
  }
  var params = {
    gid: gid
  };
  sysmgr.execCmd('delgroup', params, sysmgr.deleteGroupCb);
};

sysmgr.deleteGroupCb = function(xhr, res) {
  if (res.status != 'OK') {
    sysmgr.showInfotip(res.status);
    return;
  }
  sysmgr.showInfotip('OK');
  sysmgr.getGroupList();
};

//-----------------------------------------------------------------------------
sysmgr.getGroupInfoCb = function(xhr, res) {
  if (res.status != 'OK') {
    sysmgr.showInfotip(res.status);
    return;
  }
  var info = res.body;
  sysmgr.setGroupInfoToEditor(info);
};

sysmgr.setGroupInfoToEditor = function(info) {
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

sysmgr.clearGroupInfoEditor = function() {
  var info = {
    gid: '',
    privs: '',
    desc: ''
  };
  sysmgr.setGroupInfoToEditor(info);
};

sysmgr.saveGroupInfo = function() {
  if (sysmgr.groupEditMode == 'new') {
    sysmgr.addGroup();
  } else {
    sysmgr.updateGroup();
  }
};

//-----------------------------------------------------------------------------
sysmgr.onUserEditWindowClose = function() {
  sysmgr.userEditWindow = null;
  sysmgr.userEditMode = null;
};

sysmgr.onGroupEditWindowClose = function() {
  sysmgr.groupEditWindow = null;
  sysmgr.groupEditMode = null;
};

$onCtrlS = function(e) {
};

$onBeforeUnload = function(e) {
  if ((sysmgr.userEditWindow) || (sysmgr.groupEditWindow)) e.returnValue = '';
};
