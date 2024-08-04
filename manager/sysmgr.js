/*!
 * Copyright (c) 2023 Takashi Harano
 */
var sysmgr = {};
var scnjs = sysmgr;
scnjs.INSEC = true;
scnjs.dialogFgColor = '#fff';
scnjs.dialogBgColor = '#1e1e1e';
scnjs.dialogTitleFgColor = '#fff';
scnjs.dialogTitleBgColor = 'linear-gradient(150deg, rgba(0,32,255,0.8),rgba(0,82,255,0.8))';
scnjs.userEditWindowW = 500;
scnjs.userEditWindowH = 480;
scnjs.userEditWindowH1 = 380;

scnjs.LED_COLORS = [
  {t: 10 * util.MINUTE, color: 'led-color-green'},
  {t: 3 * util.HOUR, color: 'led-color-yellow'},
  {t: 0, color: 'led-color-red'},
];

scnjs.DAY = 86400000;
scnjs.INTERVAL = 60000;
scnjs.USER_LIST_COLUMNS = [
  {key: 'elapsed', label: ''},
  {key: 'uid', label: 'UID', style: 'min-width:10em;'},
  {key: 'fullname', label: 'Full name', style: 'min-width:8em;'},
  {key: 'localfullname', label: 'Local full name', style: 'min-width:8em;'},
  {key: 'a_name', label: 'Alias name', style: 'min-width:5em;'},
  {key: 'email', label: 'Email', style: 'min-width:10em;'},
  {key: 'is_admin', label: 'Admin'},
  {key: 'groups', label: 'Groups', style: 'min-width:5em;'},
  {key: 'privs', label: 'Privileges', style: 'min-width:5em;'},
  {key: 'info1', label: 'Info1', style: 'min-width:5em;'},
  {key: 'info2', label: 'Info2', style: 'min-width:5em;'},
  {key: 'desc', label: 'Description', style: 'min-width:5em;'},
  {key: 'flags', label: 'Flags'},
  {key: 'status_info.sessions', label: 'S'},
  {key: 'status_info.login_failed_count', label: 'E'},
  {key: 'status_info.last_access', label: 'Last Access'},
  {key: 'status_info.last_login', label: 'Last Login'},
  {key: 'status_info.last_logout', label: 'Last Logout'},
  {key: 'created_at', label: 'Created'},
  {key: 'updated_at', label: 'Updated'},
  {key: 'status_info.pw_changed_at', label: 'PwChanged'}
];

scnjs.listStatus = {
  sortIdx: 0,
  sortOrder: 1
};

scnjs.userList = [];
scnjs.sessions = null;
scnjs.userEditWindow = null;
scnjs.userEditMode = null;
scnjs.groupEditWindow = null;
scnjs.groupEditMode = null;
scnjs.tmrId = 0;
scnjs.interval = 0;
scnjs.timelineOffset = 0;

$onReady = function() {
  util.clock('#clock');
  $el('#user-list').innerHTML = '<span class="progdot">Loading</span>';
  scnjs.drawGroupStatus('<span class="progdot">Loading</span>');
  $el('#search-text').focus();
};

scnjs.onSysReady = function() {
  scnjs.reload();
  scnjs.queueNextUpdateSessionInfo();
};

scnjs.reload = function() {
  scnjs.reloadUserInfo();
  scnjs.getGroupList();
};

scnjs.reloadUserInfo = function() {
  scnjs.getUserList();
  scnjs.getSessionList();
};

scnjs.queueNextUpdateSessionInfo = function() {
  scnjs.tmrId = setTimeout(scnjs.updateSessionInfo, scnjs.INTERVAL);
};

scnjs.updateSessionInfo = function() {
  scnjs.interval = 1;
  scnjs.reloadUserInfo();
};

scnjs.callApi = function(act, params, cb) {
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
  scnjs.http(req, cb);
};

scnjs.execCmd = function(act, params, cb) {
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
  scnjs.http(req, cb);
};

scnjs.http = function(req, cb) {
  req.cb = cb;
  websys.http(req);
};

scnjs.showInfotip = function(m, d) {
  var opt = {
    style: {
      'font-size': '14px'
    }
  };
  util.infotip.show(m, d, opt);
};

scnjs.getUserList = function() {
  scnjs.callApi('get_user_list', null, scnjs.getUserListCb);
};
scnjs.getUserListCb = function(xhr, res, req) {
  if (xhr.status != 200) {
    scnjs.showInfotip('HTTP ' + xhr.status);
    return;
  }
  if (res.status == 'FORBIDDEN') {
    location.href = location.href;
    return;
  } else if (res.status != 'OK') {
    scnjs.showInfotip(res.status);
    return;
  }
  var now = util.now();
  var users = res.body;
  var userList = [];
  for (var uid in users) {
    var user = users[uid];
    var statusInfo = user.status_info;
    var lastAccessDate = statusInfo.last_access;
    var dt = scnjs.elapsedSinceLastAccess(now, lastAccessDate);
    user.elapsed = dt;
    userList.push(user);
  }
  scnjs.userList = userList;
  var listStatus = scnjs.listStatus;
  var filter = $el('#search-filter').checked;
  scnjs.drawUserList(userList, listStatus.sortIdx, listStatus.sortOrder, filter);
};

scnjs.elapsedSinceLastAccess = function(now, t) {
  if (scnjs.INSEC) t = Math.floor(t * 1000);
  var dt = now - t;
  return dt;
};

scnjs.buildListHeader = function(columns, sortIdx, sortOrder) {
  var html = '<tr class="item-list-header">';
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
    sortButton += ' onclick="scnjs.sortItemList(' + i + ', ' + nextSortType + ');"';
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

scnjs.onSearchInput = function(el) {
  var filter = $el('#search-filter').checked;
  scnjs.searchUserList(el.value, filter);
};

scnjs.clearSeachKey = function() {
  var elId = '#search-text';
  if ($el(elId).value) {
    $el(elId).value = '';
    scnjs.onSearchInput($el(elId));
  }
};

scnjs.searchUserList = function(searchKey, filter) {
  var userList = scnjs.userList;
  var listStatus = scnjs.listStatus;
  scnjs._drawUserList(userList, listStatus.sortIdx, listStatus.sortOrder, searchKey, filter);
};

scnjs.onFilterChange = function() {
  var userList = scnjs.userList;
  var listStatus = scnjs.listStatus;
  var searchKey = $el('#search-text').value;
  var filter = $el('#search-filter').checked;
  scnjs.drawUserList(userList, listStatus.sortIdx, listStatus.sortOrder, searchKey, filter);
};

scnjs.drawUserList = function(userList, sortIdx, sortOrder) {
  var searchKey = $el('#search-text').value;
  var filter = $el('#search-filter').checked;
  scnjs._drawUserList(userList, sortIdx, sortOrder, searchKey, filter);
};

scnjs._drawUserList = function(items, sortIdx, sortOrder, searchKey, filter) {
  var now = util.now();
  var currentUid = websys.getUserId();

  if (sortIdx >= 0) {
    if (sortOrder > 0) {
      var srtDef = scnjs.USER_LIST_COLUMNS[sortIdx];
      var isDesc = (sortOrder == 2);
      items = scnjs.sortList(items, srtDef.key, isDesc);
    }
  }

  var searchCaseSensitive = false;

  var count = 0;
  var htmlList = '';
  for (var i = 0; i < items.length; i++) {
    var item = items[i];
    if (filter && !scnjs.searchUserByKeyword(item, searchKey, searchCaseSensitive)) continue;
    count++;
    var uid = item.uid;
    var fullname = item.fullname;
    var localfullname = item.localfullname;
    var a_name = item.a_name;
    var email = item.email;
    var groups = item.groups;
    var privs = item.privs;
    var flags = item.flags;
    var statusInfo = item.status_info;
    var loginFailedCount = statusInfo.login_failed_count;
    var loginFailedTime = util.getDateTimeString(statusInfo.login_failed_time);
    var sessions = statusInfo.sessions;
    var lastAccessDate = scnjs.getDateTimeString(statusInfo.last_access, scnjs.INSEC);
    var lastLoginDate = scnjs.getDateTimeString(statusInfo.last_login, scnjs.INSEC);
    var lastLogoutDate = scnjs.getDateTimeString(statusInfo.last_logout, scnjs.INSEC);
    var createdDate = scnjs.getDateTimeString(item.created_at, scnjs.INSEC);
    var updatedDate = scnjs.getDateTimeString(item.updated_at, scnjs.INSEC);
    var pwChangedDate = scnjs.getDateTimeString(statusInfo.pw_changed_at, scnjs.INSEC);
    var info1 = item.info1;
    var info2 = item.info2;
    var desc = (item.desc ? item.desc : '');

    var escDesc = util.escHtml(desc);
    var dispDesc = '<span style="display:inline-block;width:100%;overflow:hidden;text-overflow:ellipsis;"';
    if (util.lenW(desc) > 15) {
      dispDesc += ' data-tooltip="' + escDesc + '"';
    }
    dispDesc += '>' + escDesc + '</span>';

    var active = (sessions > 0);
    var led = scnjs.buildLedHtml(now, statusInfo.last_access, scnjs.INSEC, active);
    var cInd = ((uid == currentUid) ? '<span class="text-skyblue" style="cursor:default;margin-right:2px;" data-tooltip2="You">*</span>' : '<span style="margin-right:2px;">&nbsp;</span>');

    var dispUid = uid;
    var dispFullname = fullname;
    var dispLocalFullname = localfullname;
    var dispAname = a_name;
    var dispEmail = email;
    var dispGroups = groups;
    var dispPrivs = privs;
    var dispInfo1 = info1;
    var dispInfo2 = info2;

    if (searchKey) {
      dispUid = scnjs.highlightKeyword(uid, searchKey, searchCaseSensitive);
      dispFullname = scnjs.highlightKeyword(fullname, searchKey, searchCaseSensitive);
      dispLocalFullname = scnjs.highlightKeyword(localfullname, searchKey, searchCaseSensitive);
      dispAname = scnjs.highlightKeyword(a_name, searchKey, searchCaseSensitive);
      dispEmail = scnjs.highlightKeyword(email, searchKey, searchCaseSensitive);
      dispGroups = scnjs.highlightKeyword(groups, searchKey, searchCaseSensitive);
      dispPrivs = scnjs.highlightKeyword(privs, searchKey, searchCaseSensitive);
      dispInfo1 = scnjs.highlightKeyword(info1, searchKey, searchCaseSensitive);
      dispInfo2 = scnjs.highlightKeyword(info2, searchKey, searchCaseSensitive);
    }

    dispUid = cInd + '<span class="pseudo-link link-button" onclick="scnjs.editUser(\'' + uid + '\');" data-tooltip2="Edit">' + dispUid + '</span>';
    dispFullname = scnjs.buildCopyableLabel(fullname, dispFullname);
    dispLocalFullname = scnjs.buildCopyableLabel(localfullname, dispLocalFullname);
    dispAname = scnjs.buildCopyableLabel(a_name, dispAname);
    dispEmail = scnjs.buildCopyableLabel(email, dispEmail);
    dispInfo1 = scnjs.buildCopyableLabel(info1, dispInfo1);
    dispInfo2 = scnjs.buildCopyableLabel(info2, dispInfo2);

    var failedCount = '<td class="item-list" style="text-align:right;width:1.5em;">';
    if (loginFailedCount > 0) {
      var clz = 'pseudo-link';
      if ((scnjs.websysconf.LOGIN_FAILURE_MAX > 0) && (loginFailedCount >= scnjs.websysconf.LOGIN_FAILURE_MAX)) {
        clz += ' login-locked';
      } else {
        clz += ' text-red';
      }
      failedCount += '<span class="' + clz + '" data-tooltip="Last failed: ' + loginFailedTime + '" onclick="scnjs.confirmClearLoginFailedCount(\'' + uid + '\');">' + loginFailedCount + '</span>';
    } else {
      failedCount += '';
    }
    failedCount += '</td>';

    clz = ((i % 2 == 0) ? 'row-odd' : 'row-even');
    var ttFlg = scnjs.buildFlagsTooltip(flags);

    htmlList += '<tr class="item-list ' + clz + '">';
    htmlList += '<td class="item-list" style="text-align:center;">' + led + '</td>';
    htmlList += '<td class="item-list" style="padding-right:10px;">' + dispUid + '</td>';
    htmlList += '<td class="item-list">' + dispFullname + '</td>';
    htmlList += '<td class="item-list">' + dispLocalFullname + '</td>';
    htmlList += '<td class="item-list">' + dispAname + '</td>';
    htmlList += '<td class="item-list">' + dispEmail + '</td>';
    htmlList += '<td class="item-list" style="text-align:center;">' + (item.is_admin ? 'Y' : '') + '</td>';
    htmlList += '<td class="item-list">' + dispGroups + '</td>';
    htmlList += '<td class="item-list">' + dispPrivs + '</td>';
    htmlList += '<td class="item-list">' + dispInfo1 + '</td>';
    htmlList += '<td class="item-list">' + dispInfo2 + '</td>';
    htmlList += '<td class="item-list" style="max-width:15em;">' + dispDesc + '</td>';
    htmlList += '<td class="item-list" style="text-align:center;" data-tooltip="' + ttFlg + '">' + flags + '</td>';
    htmlList += '<td class="item-list" style="text-align:right;">' + sessions + '</td>';
    htmlList += failedCount;
    htmlList += '<td class="item-list" style="text-align:center;">' + lastAccessDate + '</td>';
    htmlList += '<td class="item-list" style="text-align:center;">' + lastLoginDate + '</td>';
    htmlList += '<td class="item-list" style="text-align:center;">' + lastLogoutDate + '</td>';
    htmlList += '<td class="item-list" style="text-align:center;">' + createdDate + '</td>';
    htmlList += '<td class="item-list" style="text-align:center;">' + updatedDate + '</td>';
    htmlList += '<td class="item-list" style="text-align:center;">' + pwChangedDate + '</td>';
    htmlList += '</tr>';
  }

  var listInfo = 'count = ' + count;
  if (count == 0) {
    listInfo = '<div style="margin-top:8px;margin-bottom:40px;">- DATA NOT FOUND -</div>';
  }

  var htmlHead = scnjs.buildListHeader(scnjs.USER_LIST_COLUMNS, sortIdx, sortOrder);
  var html = '<table>' + htmlHead + htmlList + '</table>';
  html += '<div style="margin-bottom:4px;" class="list-info">' + listInfo + '</div>';

  $el('#user-list').innerHTML = html;
};

scnjs.buildFlagsTooltip = function(flags) {
  var d = 8;
  var s = '';
  for (var i = d - 1; i >= 0; i--) {
    s += ((flags & Math.pow(2, i)) ? '1' : '0');
  }
  s += ' (' + flags + ')';
  s += '\n';
  for (i = 0; i <= d; i++) {
    for (var j = d; j >= 0; j--) {
      if (!((i == 0) && (j == 0))) {
        if (j == i) {
          s += '+';
        } else if (j > i - 1) {
          s += '|';
        } else {
          s += '-';
        }
      }
      if (j == 0) {
        if (i > 0) {
          var flgName = websys.USER_FLAGS[i - 1];
          if (!flgName) flgName = '';
          s += ' ';
          s += ((flags & Math.pow(2, (i - 1))) ? 'Y' : 'N');
          s += ' ';
          s += flgName;
        }
      }
    }
    s += '\n';
  }
  return s;
};

scnjs.highlightKeyword = function(v, searchKey, caseSensitive) {
  if (!caseSensitive) searchKey = searchKey.toLowerCase();
  try {
    var pos = (caseSensitive ? v.indexOf(searchKey) : v.toLowerCase().indexOf(searchKey));
    if (pos != -1) {
      var key = v.slice(pos, pos + searchKey.length);
      var hl = '<span class="search-highlight">' + key + '</span>';
      v = v.replace(key, hl, 'ig');
    }
  } catch (e) {}
  return v;
};

scnjs.searchUserByKeyword = function(item, key, caseSensitive) {
  if (!key) return true;
  var targets = [];
  targets.push(item.uid);
  targets.push(item.fullname);
  targets.push(item.localfullname);
  targets.push(item.a_name);
  targets.push(item.email);
  targets.push(item.groups);
  targets.push(item.privs);
  targets.push(item.info1);
  targets.push(item.info2);
  return scnjs.searchByKeyword(targets, key, caseSensitive);
};
scnjs.searchByKeyword = function(targets, key, caseSensitive) {
  var flg = (caseSensitive ? 'g' : 'gi');
  for (var i = 0; i < targets.length; i++) {
    var v = targets[i];
    try {
      var re = new RegExp(key, flg);
      var r = re.exec(v);
      if (r != null) return true;
    } catch (e) {}
  }
  return false;
};

scnjs.buildCopyableLabel = function(v, s) {
  if (!s) s = v;
  v = v.replace(/\\/g, '\\\\').replace(/'/g, '\\\'').replace(/"/g, '&quot;');
  var label = s;
  var r = '<pre class="pseudo-link" onclick="scnjs.copy(\'' + v + '\');" data-tooltip2="Click to copy">' + label + '</pre>';
  return r;
};

scnjs.buildLedHtml = function(now, ts, inSec, active) {
  var COLORS = scnjs.LED_COLORS;
  var tMs = ts;
  if (inSec) tMs = Math.floor(tMs * 1000);
  var elapsed = now - tMs;
  var ledColor = 'led-color-gray';
  if (active) {
    for (var i = 0; i < COLORS.length; i++) {
      var c = COLORS[i];
      if ((elapsed <= c.t) || (c.t == 0)) {
        ledColor = c.color;
        break;
      }
    }
  }
  var dt = scnjs.getDateTimeString(tMs);
  var html = '<span class="led ' + ledColor + '" data-tooltip="Last access: ' + dt + '"></span>';
  return html;
};

scnjs.getDateTimeString = function(ts, inSec) {
  var tMs = ts;
  if (inSec) tMs = Math.floor(tMs * 1000);
  var s = '---------- --:--:--.---';
  if (tMs > 0) {
    s = util.getDateTimeString(tMs, '%YYYY-%MM-%DD %HH:%mm:%SS.%sss');
  }
  return s;
};

scnjs.getSessionListN = function() {
  scnjs.timelineOffset = $el('#timeline-offset').value | 0;
  scnjs.getSessionList();
};
scnjs.getSessionListRst = function() {
  scnjs.timelineOffset = 0;
  scnjs.getSessionList();
};
scnjs.getSessionListPrev = function() {
  scnjs.timelineOffset++;
  scnjs.getSessionList();
};
scnjs.getSessionListNext = function() {
  scnjs.timelineOffset--;
  if (scnjs.timelineOffset < 0) scnjs.timelineOffset = 0;
  scnjs.getSessionList();
};
scnjs.getSessionList = function() {
  if (scnjs.tmrId > 0) {
    clearTimeout(scnjs.tmrId);
    scnjs.tmrId = 0;
    scnjs.interval = 1;
  }
  var param = {logs: '1', offset: scnjs.timelineOffset};
  scnjs.callApi('get_session_list', param, scnjs.getSessionListCb);
};
scnjs.getSessionListCb = function(xhr, res, req) {
  if (xhr.status != 200) {
    scnjs.showInfotip('HTTP ' + xhr.status);
    return;
  }
  if (res.status == 'FORBIDDEN') {
    location.href = location.href;
    return;
  } else if (res.status != 'OK') {
    scnjs.showInfotip(res.status);
    return;
  }
  var sessions = res.body;
  scnjs.sessions = sessions;
  scnjs.drawSessionList(sessions);

  if (scnjs.interval) {
    scnjs.interval = 0;
    scnjs.queueNextUpdateSessionInfo();
  }
};

scnjs.drawSessionList = function(sessions) {
  var now = util.now();
  sessions = util.sortObjectList(sessions, 'time', true, true);
  var html = '<table>';
  html += '<tr style="font-weight:bold;">';
  html += '<td></td>';
  html += '<td class="timeline-head">UID</td>';
  html += '<td class="timeline-head">Name</td>';
  html += '<td class="timeline-head"><span style="margin-left:8px;">Session</span></td>';
  html += '<td class="timeline-head">Last Access</td>';
  html += '<td class="timeline-head" style="min-width:98px;">Elapsed</td>';
  html += '<td class="timeline-head"style="font-weight:normal;">' + scnjs.buildTimeLineHeader1(now) + scnjs.buildTimeLineHeader2(now) + '</td>';
  html += '<td class="timeline-head">Addr</td>';
  html += '<td class="timeline-head">User-Agent</td>';
  html += '<td class="timeline-head">Logged in</td>';
  html += '</tr>';
  html += scnjs.buildSessionInfoHtml(sessions, now);
  html += '</table>';
  $el('#session-list').innerHTML = html;
  scnjs.updateTimeline();
};

scnjs.buildTimeLineHeader1 = function(now) {
  var os = scnjs.timelineOffset;
  if (os > 0) {
    now = now - (scnjs.DAY * os);
  }

  var mmddw = util.getDateTimeString(now, '%MM/%DD %W');
  mmddw = mmddw.replace(/(SAT)/, '<span class="wday-sat">$1</span>');
  mmddw = mmddw.replace(/(SUN)/, '<span class="wday-sun">$1</span>');
  var v = (os ? os : '');

  var html = '<div style="position:relative;margin-bottom:4px;">';
  html += '<span style="margin-right:16px;">' + mmddw + '</span>';
  html += '<span style="position:absolute;right:0;">';
  html += '<span class="pseudo-link link-button" onclick="scnjs.getSessionListPrev();">&lt;</span>&nbsp;';
  html += '<span class="pseudo-link link-button" onclick="scnjs.getSessionListNext();">&gt;</span>';
  html += '<input type="text" id="timeline-offset" style="margin-left:8px;width:20px;text-align:right;" value="' + v + '">';
  html += '<span class="pseudo-link link-button" style="margin-left:2px;" onclick="scnjs.getSessionListN();">SHOW</span>';
  html += '<span class="pseudo-link link-button" style="margin-left:8px;" onclick="scnjs.getSessionListRst();">RST</span>';
  html += '</span>';
  html += '</div>';
  return html;
};
scnjs.buildTimeLineHeader2 = function(now) {
  var os = scnjs.timelineOffset;
  if (os > 0) {
    now = now - (scnjs.DAY * os);
  }

  var nowHHMM = util.getDateTimeString(now, '%HH:%mm');
  var tmp = nowHHMM.split(':');
  var nowHH = tmp[0];
  var nowMM = tmp[1];
  var currentInd = '<span id="timeline-now" class="timeline-current blink1 text-skyblue" data-tooltip="' + nowHHMM + '">v</span>';

  var html = '';
  for (var i = 0; i <= 23; i++) {
    var ts = scnjs.getTimeSlot(i, nowHH, nowMM);
    if (i < 10) {
      if ((os == 0) && (ts == 0)) {
        html += currentInd;
      }
    } else if (os == 0) {
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
      if ((os == 0) && (ts == j)) {
        html += currentInd;
      } else {
        html += ' ';
      }
    }
  }
  return html;
};

scnjs.timelineTmrId = 0;
scnjs.updateTimeline = function() {
  if (scnjs.timelineTmrId > 0) {
    clearTimeout(scnjs.timelineTmrId);
  }
  scnjs.updateTimelineCurrentTime();
  if (scnjs.timelineTmrId != -1) {
    scnjs.timelineTmrId = setTimeout(scnjs.updateTimeline, 1000);
  }
};
scnjs.updateTimelineCurrentTime = function() {
  var now = util.now();
  var nowHHMM = util.getDateTimeString(now, '%HH:%mm');
  $el('#timeline-now').dataset.tooltip = nowHHMM;
};

scnjs.buildSessionInfoHtml = function(sessions, now) {
  var html = '';
  if (!sessions) return html;
  for (var i = 0; i < sessions.length; i++) {
    var session = sessions[i];
    html += scnjs.buildSessionInfoOne(session, now);
  }
  return html;
};
scnjs.buildSessionInfoOne = function(session, now) {
  var cSid = websys.getSessionId();
  var uid = session['uid'];
  var fullname = session['user_fullname'];
  var loginT = session['c_time'];
  var ua = session['ua'];
  var laTime = session['time'];
  var sid = session['sid'];
  var addr = session['addr'];
  if (scnjs.INSEC) laTime = Math.floor(laTime * 1000);
  var loginTime = util.getDateTimeString(loginT, '%YYYY-%MM-%DD %HH:%mm:%SS.%sss');
  var laTimeStr = util.getDateTimeString(laTime, '%YYYY-%MM-%DD %HH:%mm:%SS.%sss');
  var ssid = util.snip(sid, 7, 3, '..');
  var sid7 = util.snip(sid, 7, 0, '');
  var brws = util.getBrowserInfo(ua);
  var dispUa = brws.name + ' ' + brws.version;
  var led = scnjs.buildLedHtml(now, laTime, false, true);
  var ssidLink = '<span class="pseudo-link link-button" onclick="scnjs.confirmLogoutSession(\'' + uid + '\', \'' + sid + '\');" data-tooltip="' + sid + '">' + ssid + '</span>';
  var dispSid = ((sid == cSid) ? '<span class="text-skyblue" style="cursor:default;margin-right:2px;" data-tooltip2="Current Session">*</span>' : '<span style="cursor:default;margin-right:2px;">&nbsp;</span>') + ssidLink;
  var timeId = 'tm-' + sid7;
  var tmspan = '<span id="' + timeId + '"></span>';

  var slotTimestampHistories = session['timeline_log'];
  var timeline = scnjs.buildTimeLine(now, laTime, slotTimestampHistories);

  var html = '';
  html += '<tr class="item-list">';
  html += '<td style="padding-right:4px;">' + led + '</td>';
  html += '<td style="padding-right:10px;">' + uid + '</td>';
  html += '<td style="padding-right:6px;">' + fullname + '</td>';
  html += '<td style="padding-right:10px;">' + dispSid + '</td>';
  html += '<td style="padding-right:10px;">' + laTimeStr + '</td>';
  html += '<td style="padding-right:10px;text-align:right;">' + tmspan + '</td>';
  html += '<td>' + timeline + '</td>';
  html += '<td style="padding-right:10px;">' + addr + '</td>';
  html += '<td style="padding-right:10px;">' + dispUa + '</td>';
  html += '<td style="padding-right:10px;">' + loginTime + '</td>';
  html += '</tr>';

  setTimeout(scnjs.startElapsedCounter, 0, {timeId: '#' + timeId, laTime: laTime});
  return html;
};
scnjs.startElapsedCounter = function(param) {
  var o = {zero: true};
  util.timecounter.start(param.timeId, param.laTime, o);
};

scnjs.buildTimeLine = function(now, lastAccessTime, slotTimestampHistories) {
  var os = scnjs.timelineOffset;
  if (os > 0) {
    now = now - (scnjs.DAY * os);
  }

  var accYearDateTime = util.getDateTimeString(lastAccessTime, '%YYYY-%MM-%DD %HH:%mm');
  var accDateTime = util.getDateTimeString(lastAccessTime, '%W %DD %MMM %HH:%mm');
  var accTime = util.getDateTimeString(lastAccessTime, '%HH:%mm');
  var accTp = scnjs.getTimePosition(now, lastAccessTime);
  var nowTp = scnjs.getTimePosition(now, now);
  var hrBlk = 5;
  var ttlPs = hrBlk * 24;
  var dispAccDateTime = ' ' + accDateTime + ' ';
  var dispAccTime = ' ' + accTime + ' ';

  var tsPosList = scnjs.getPosList4History(now, slotTimestampHistories);

  var html = '<span class="timeline-span">';
  var s;
  var f = false;
  for (var i = 0; i <= ttlPs; i++) {
    if (!f && (os == 0) && (i > nowTp)) {
      html += '<span class="timeline-forward">';
      f = true;
    }

    if ((os == 0) && (i == 0) && (accTp == -1)) {
      s = '<span class="timeline-acc-ind-out" data-tooltip="' + accYearDateTime + '">&lt;</span>';
      s += '<span class="timeline-acc-ind-time">' + dispAccDateTime + '</san>';
      html += s;
      i += dispAccDateTime.length;
      continue;
    } else if (i % hrBlk == 0) {
      html += '|';
      continue;
    }

    s = '';
    if (i == accTp) {
      s += '<span class="timeline-acc-ind" data-tooltip="' + accTime + '">*</span>';
      s += '<span class="timeline-acc-ind-time">' + dispAccTime + '</span>';
      i += dispAccTime.length;
    } else {
      s += scnjs.getTimeslotInd(tsPosList, i);
    }
    html += s;
  }

  if (f) html += '</span>';
  html += '</span>';
  return html;
};

scnjs.getTimeslotInd = function(tsPosList, pos) {
  var s = '-';
  for (var i = 0; i < tsPosList.length; i++) {
    var tsPos = tsPosList[i];
    var p = tsPos.p;
    if (p == pos) {
      var t = tsPos.t;
      var tt = util.getDateTimeString(t, '%HH:%mm');
      s = '<span class="timeline-acc-ind timeline-acc-ind-past" data-tooltip="' + tt + '">*</span>';
      break;
    }
  }
  return s;
};

scnjs.getPosList4History = function(now, slotTimestampHistories) {
  var posList = [];
  for (var i = 0; i < slotTimestampHistories.length; i++) {
    var t = slotTimestampHistories[i];
    if (scnjs.INSEC) t *= 1000;
    var p = scnjs.getTimePosition(now, t);
    if (p >= 0) {
      posList.push({p: p, t: t});
    }
  }
  return posList;
};

scnjs.getTimePosition = function(now, timestamp) {
  var nowYYYYMMDD = util.getDateTimeString(now, '%YYYY%MM%DD');
  var accYYYYMMDD = util.getDateTimeString(timestamp, '%YYYY%MM%DD');
  var accHHMM = util.getDateTimeString(timestamp, '%HH:%mm');
  var wk = accHHMM.split(':');
  var accHH = wk[0];
  var accMM = wk[1];
  var p = 0;
  for (var i = 0; i <= 23; i++) {
    p++;
    for (var j = 0; j < 4; j++) {
      if ((accYYYYMMDD == nowYYYYMMDD) && (scnjs.inTheTimeSlot(i, j, accHH, accMM))) {
        return p;
      }
      p++;
    }
  }
  return -1;
};

scnjs.inTheTimeSlot = function(h, qM, hh, mm) {
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
scnjs.getTimeSlot = function(h, hh, mm) {
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

scnjs.sortItemList = function(sortIdx, sortOrder) {
  if (sortOrder > 2) {
    sortOrder = 0;
  }
  scnjs.listStatus.sortIdx = sortIdx;
  scnjs.listStatus.sortOrder = sortOrder;
  scnjs.drawUserList(scnjs.userList, sortIdx, sortOrder);
};

scnjs.confirmLogoutSession = function(uid, sid) {
  var cSid = websys.getSessionId();
  var currentUid = websys.getUserId();
  var m = 'Logout?\n\n';
  if (sid == cSid) {
    m += '<span class="warn-red" style="font-weight:bold;">[CURRENT SESSION]</span>\n';
  }
  m += '<div style="text-align:left;">';
  m += 'uid: ' + uid;
  if (uid == currentUid) m += ' <span class="you">(You)</span>';
  m += '\n';
  m += 'sid: ' + sid;
  m += '</div>';
  util.confirm(m, scnjs.logoutSession, {data: sid});
};
scnjs.logoutSession = function(sid) {
  var params = {
    sid: sid
  };
  scnjs.execCmd('logout', params, scnjs.logoutSessionCb);
};
scnjs.logoutSessionCb = function(xhr, res) {
  if (xhr.status != 200) {
    scnjs.showInfotip('HTTP ' + xhr.status);
    return;
  }
  scnjs.showInfotip(res.status);
  scnjs.reloadUserInfo();
};

//-----------------------------------------------------------------------------
scnjs.newUser = function() {
  scnjs.editUser(null);
};

scnjs.editUser = function(uid) {
  var mode = (uid ? 'edit' : 'new');
  scnjs.userEditMode = mode;
  if (!scnjs.userEditWindow) {
    scnjs.userEditWindow = scnjs.openUserInfoEditorWindow(mode, uid);
  }
  scnjs.clearUserInfoEditor();
  if (mode == 'edit') {
    var params = {
      uid: uid
    };
    scnjs.execCmd('user', params, scnjs.GetUserInfoCb);
  } else {
    $el('#flags').value = '1';
    $el('#uid').focus();
  }
  $el('#flags').addEventListener('input', scnjs.onInputFlags);
};

scnjs.openUserInfoEditorWindow = function(mode, uid) {
  var currentUid = websys.getUserId();

  var html = '';
  html += '<div style="position:relative;width:100%;height:100%;text-align:center;vertical-align:middle">';
  if (uid && (uid != currentUid)) {
    html += '<div style="position:absolute;top:8px;right:8px;"><button class="button-red" onclick="scnjs.deleteUser(\'' + uid + '\');">DEL</button></div>';
  }
  html += '<div style="padding:4px;position:absolute;top:0;right:0;bottom:0;left:0;margin:auto;width:400px;height:' + scnjs.userEditWindowH1 + 'px;text-align:left;">';

  html += '<table class="edit-table">';
  html += '  <tr>';
  html += '    <td>UID</td>';
  html += '    <td><input type="text" id="uid" style="width:100%;" onblur="scnjs.onUidBlur();"></td>';
  html += '  </tr>';
  html += '  <tr>';
  html += '    <td>Full name</td>';
  html += '    <td><input type="text" id="fullname" style="width:100%;"></td>';
  html += '  </tr>';
  html += '  <tr>';
  html += '    <td>Local Full name</td>';
  html += '    <td><input type="text" id="localfullname" style="width:100%;"></td>';
  html += '  </tr>';
  html += '  <tr>';
  html += '    <td>Alias name</td>';
  html += '    <td><input type="text" id="a_name" style="width:100%;"></td>';
  html += '  </tr>';
  html += '  <tr>';
  html += '    <td>Email</td>';
  html += '    <td><input type="text" id="email" style="width:100%;"></td>';
  html += '  </tr>';
  html += '  <tr>';
  html += '    <td>isAdmin</td>';
  html += '    <td><input type="checkbox" id="isadmin">';
  html += '    </td>';
  html += '  </tr>';
  html += '  <tr>';
  html += '    <td>Groups</td>';
  html += '    <td><input type="text" id="groups" style="width:100%;"></td>';
  html += '  </tr>';
  html += '  <tr>';
  html += '    <td>Privileges</td>';
  html += '    <td><input type="text" id="privs" style="width:100%;"></td>';
  html += '  </tr>';
  html += '  <tr>';
  html += '    <td>Info1</td>';
  html += '    <td><input type="text" id="info1" style="width:100%;"></td>';
  html += '  </tr>';
  html += '  <tr>';
  html += '    <td>Info2</td>';
  html += '    <td><input type="text" id="info2" style="width:100%;"></td>';
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
  html += '</table>';

  html += '<div style="margin-top:40px;text-align:center;">';
  html += '<button onclick="scnjs.saveUserInfo();">OK</button>'
  html += '<button style="margin-left:8px;" onclick="scnjs.userEditWindow.close();">Cancel</button>'
  html += '</div>';

  html += '</div>';
  html += '</div>';

  var opt = {
    draggable: true,
    resizable: true,
    pos: 'c',
    closeButton: true,
    width: scnjs.userEditWindowW,
    height: scnjs.userEditWindowH,
    minWidth: scnjs.userEditWindowW,
    minHeight: scnjs.userEditWindowH,
    scale: 1,
    hidden: false,
    modal: false,
    title: {
      text: ((mode == 'new') ? 'New' : 'Edit') +' User',
      style: {
        color: scnjs.dialogTitleFgColor,
        background: scnjs.dialogTitleBgColor
      }
    },
    body: {
      style: {
        color: scnjs.dialogFgColor,
        background: scnjs.dialogBgColor
      }
    },
    onclose: scnjs.onUserEditWindowClose,
    content: html
  };

  var win = util.newWindow(opt);
  return win;
};

scnjs.onUidBlur = function() {
  var fullname = $el('#fullname').value;
  if (fullname) return;
  var uid = $el('#uid').value;
  if (uid.match()) {
    fullname = scnjs.mail2name(uid);
  }
  $el('#fullname').value = fullname;
};

scnjs.mail2name = function(m) {
  var a = m.split('@');
  a = a[0].split('.');
  if (a.length == 1) return a[0];
  var s = '';
  for (var i = 0; i < a.length; i++) {
    if (i > 0) {
      s += ' ';
    }
    s += util.capitalize(a[i]);
  }
  return s;
};

scnjs.GetUserInfoCb = function(xhr, res) {
  if (xhr.status != 200) {
    scnjs.showInfotip('HTTP ' + xhr.status);
    return;
  }
  if (res.status != 'OK') {
    scnjs.showInfotip(res.status);
    return;
  }
  var info = res.body;
  scnjs.setUserInfoToEditor(info);
};

scnjs.setUserInfoToEditor = function(info) {
  var uid = info.uid;
  $el('#uid').value = uid;
  if (uid) {
    $el('#uid').disabled = true;
    $el('#uid').addClass('edit-disabled');
  } else {
    $el('#uid').disabled = false;
    $el('#uid').removeClass('edit-disabled');
  }
  $el('#fullname').value = info.fullname;
  $el('#localfullname').value = info.localfullname;
  $el('#a_name').value = info.a_name;
  $el('#email').value = info.email;
  $el('#isadmin').checked = info.is_admin;
  $el('#groups').value = info.groups;
  $el('#privs').value = info.privs;
  $el('#info1').value = info.info1;
  $el('#info2').value = info.info2;
  $el('#desc').value = (info.desc ? info.desc : '');
  $el('#flags').value = info.flags;
  $el('#flags').dataset.tooltip = scnjs.buildFlagsTooltip(info.flags);
};

scnjs.onInputFlags = function() {
  var flags = $el('#flags').value;
  $el('#flags').dataset.tooltip = scnjs.buildFlagsTooltip(flags);
};

scnjs.clearUserInfoEditor = function() {
  var info = {
    uid: '',
    fullname: '',
    localfullname: '',
    a_name: '',
    email: '',
    is_admin: false,
    groups: '',
    privs: '',
    info1: '',
    info2: '',
    desc: '',
    flags: ''
  };
  scnjs.setUserInfoToEditor(info);
};

scnjs.saveUserInfo = function() {
  if (scnjs.userEditMode == 'new') {
    scnjs.addUser();
  } else {
    scnjs.updateUser();
  }
};

//-----------------------------------------------------------------------------
scnjs.addUser = function() {
  var uid = $el('#uid').value;
  var fullname = $el('#fullname').value;
  var localfullname = $el('#localfullname').value;
  var a_name = $el('#a_name').value;
  var email = $el('#email').value;
  var isAdmin = ($el('#isadmin').checked ? 'true' : 'false');
  var groups = $el('#groups').value;
  var privs = $el('#privs').value;
  var info1 = $el('#info1').value;
  var info2 = $el('#info2').value;
  var desc = $el('#desc').value;
  var flags = $el('#flags').value.trim();
  var pw1 = $el('#pw1').value;
  var pw2 = $el('#pw2').value;

  var clnsRes = scnjs.cleanseUid(uid);
  if (clnsRes.msg) {
    scnjs.showInfotip(clnsRes.msg, 2000);
    return;
  }
  uid = clnsRes.val;

  clnsRes = scnjs.cleanseFullName(fullname);
  if (clnsRes.msg) {
    scnjs.showInfotip(clnsRes.msg, 2000);
    return;
  }
  fullname = clnsRes.val;

  clnsRes = scnjs.cleanseFullName(localfullname);
  if (clnsRes.msg) {
    scnjs.showInfotip(clnsRes.msg, 2000);
    return;
  }
  localfullname = clnsRes.val;

  clnsRes = scnjs.cleanseFullName(a_name);
  if (clnsRes.msg) {
    scnjs.showInfotip(clnsRes.msg, 2000);
    return;
  }
  a_name = clnsRes.val;

  clnsRes = scnjs.cleanseGroups(groups);
  if (clnsRes.msg) {
    scnjs.showInfotip(clnsRes.msg, 2000);
    return;
  }
  groups = clnsRes.val;

  clnsRes = scnjs.cleansePrivileges(privs);
  if (clnsRes.msg) {
    scnjs.showInfotip(clnsRes.msg, 2000);
    return;
  }
  privs = clnsRes.val;

  clnsRes = scnjs.cleansePW(pw1, pw2, 'new');
  if (clnsRes.msg) {
    scnjs.showInfotip(clnsRes.msg, 2000);
    return;
  }
  var pw = clnsRes.val;
  pw = websys.getUserPwHash(uid, pw);

  var params = {
    uid: uid,
    fullname: fullname,
    localfullname: localfullname,
    a_name: a_name,
    email: email,
    is_admin: isAdmin,
    groups: groups,
    privs: privs,
    info1: info1,
    info2: info2,
    desc: desc,
    flags: flags,
    pw: pw
  };

  scnjs.execCmd('useradd', params, scnjs.updateUserCb);
};

scnjs.addUserCb = function(xhr, res) {
  if (xhr.status != 200) {
    scnjs.showInfotip('HTTP ' + xhr.status);
    return;
  }
  scnjs.showInfotip(res.status);
  if (res.status != 'OK') {
    return;
  }
  scnjs.userEditWindow.close();
  scnjs.getUserList();
};

//-----------------------------------------------------------------------------
scnjs.updateUser = function() {
  var uid = $el('#uid').value;
  var fullname = $el('#fullname').value;
  var localfullname = $el('#localfullname').value;
  var a_name = $el('#a_name').value;
  var email = $el('#email').value;
  var isAdmin = ($el('#isadmin').checked ? 'true' : 'false');
  var groups = $el('#groups').value;
  var privs = $el('#privs').value;
  var info1 = $el('#info1').value;
  var info2 = $el('#info2').value;
  var desc = $el('#desc').value;
  var flags = $el('#flags').value;
  var pw1 = $el('#pw1').value;
  var pw2 = $el('#pw2').value;

  var clnsRes = scnjs.cleansePW(pw1, pw2, 'edit');
  if (clnsRes.msg) {
    scnjs.showInfotip(clnsRes.msg, 2000);
    return;
  }
  var pw = clnsRes.val;

  var params = {
    uid: uid,
    fullname: fullname,
    localfullname: localfullname,
    a_name: a_name,
    email: email,
    is_admin: isAdmin,
    groups: groups,
    privs: privs,
    info1: info1,
    info2: info2,
    desc: desc,
    flags: flags
  };

  if (pw) {
    params.pw = websys.getUserPwHash(uid, pw);
  }

  scnjs.execCmd('usermod', params, scnjs.updateUserCb);
};

scnjs.updateUserCb = function(xhr, res) {
  if (xhr.status != 200) {
    scnjs.showInfotip('HTTP ' + xhr.status);
    return;
  }
  scnjs.showInfotip(res.status);
  if (res.status != 'OK') {
    return;
  }
  scnjs.userEditWindow.close();
  scnjs.getUserList();
};

//-----------------------------------------------------------------------------
scnjs.deleteUser = function(uid) {
  var opt = {
    data: uid
  };
  util.confirm('Delete ' + uid + ' ?', scnjs._deleteUser, opt);
};
scnjs._deleteUser = function(uid) {
  if (!uid) {
    return;
  }
  if (scnjs.userEditWindow) {
    scnjs.userEditWindow.close();
  }
  var params = {
    uid: uid
  };
  scnjs.execCmd('userdel', params, scnjs.deleteUserCb);
};

scnjs.deleteUserCb = function(xhr, res) {
  if (xhr.status != 200) {
    scnjs.showInfotip('HTTP ' + xhr.status);
    return;
  }
  if (res.status != 'OK') {
    scnjs.showInfotip(res.status);
    return;
  }
  scnjs.showInfotip('OK');
  scnjs.getUserList();
};

//-----------------------------------------------------------------------------
scnjs.confirmClearLoginFailedCount = function(uid) {
  var opt = {
    data: uid
  };
  util.confirm('Clear failure count for ' + uid + ' ?', scnjs.clearLoginFailedCount, opt);
};
scnjs.clearLoginFailedCount = function(uid) {
  if (!uid) {
    return;
  }
  var params = {
    uid: uid
  };
  scnjs.execCmd('unlockuser', params, scnjs.clearLoginFailedCountCb);
};

scnjs.clearLoginFailedCountCb = function(xhr, res) {
  if (xhr.status != 200) {
    scnjs.showInfotip('HTTP ' + xhr.status);
    return;
  }
  if (res.status != 'OK') {
    scnjs.showInfotip(res.status);
    return;
  }
  scnjs.showInfotip('OK');
  scnjs.getUserList();
};

//-----------------------------------------------------------------------------
scnjs.sortList = function(itemList, sortKey, isDesc) {
  var items = util.copyObject(itemList);
  var srcList = items;
  var asNum = true;
  var sortedList = util.sortObjectList(srcList, sortKey, isDesc, asNum);
  return sortedList;
};

//-----------------------------------------------------------------------------
scnjs.cleanseCommon = function(s) {
  s = s.trim();
  s = s.replace(/\t/g, ' ');
  var res = {
    val: s,
    msg: null
  };
  return res;
};

scnjs.cleanseUid = function(s) {
  var res = scnjs.cleanseCommon(s);
  if (res.msg) {
    return res;
  }
  var msg = null;
  s = res.val;
  if (!s) {
    msg = 'User ID is required';
  }
  res.val = s;
  res.msg = msg;
  return res;
};

scnjs.cleanseFullName = function(s) {
  var res = scnjs.cleanseCommon(s);
  if (res.msg) {
    return res;
  }
  var msg = null;
  s = res.val;
  res.val = s;
  res.msg = msg;
  return res;
};

scnjs.cleanseLocalFullName = function(s) {
  var res = scnjs.cleanseCommon(s);
  if (res.msg) {
    return res;
  }
  var msg = null;
  s = res.val;
  res.val = s;
  res.msg = msg;
  return res;
};

scnjs.cleansePW = function(pw1, pw2, mode) {
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

scnjs.cleanseGroups = function(s) {
  var res = scnjs.cleanseCommon(s);
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

scnjs.cleansePrivileges = function(s) {
  var res = scnjs.cleanseCommon(s);
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
scnjs.drawGroupStatus = function(s) {
  $el('#groups-status').innerHTML = s;
};

scnjs.getGroupList = function() {
  scnjs.callApi('get_group_list', null, scnjs.getGroupListCb);
};
scnjs.getGroupListCb = function(xhr, res) {
  if (xhr.status != 200) {
    scnjs.showInfotip('HTTP ' + xhr.status);
    return;
  }
  if (res.status == 'OK') {
    scnjs.drawGroupStatus('');
    var list = res.body.group_list;
    scnjs.drawGroupList(list);
  }
};

scnjs.drawGroupList = function(list) {
  var html = '<table>';
  html += '<tr class="item-list-header">';
  html += '<th class="item-list" style="min-width:10em;">GID</th>';
  html += '<th class="item-list" style="min-width:15em;">Name</th>';
  html += '<th class="item-list" style="min-width:20em;">Prvileges</th>';
  html += '<th class="item-list" style="min-width:20em;">Description</th>';
  html += '<th class="item-list">Created</th>';
  html += '<th class="item-list">Updated</th>';
  html += '</tr>';

  for (var i = 0; i < list.length; i++) {
    var group = list[i];
    var gid = group.gid;
    var name = group.name;
    var privs = (group.privs ? group.privs : '');
    var desc = (group.desc ? group.desc : '');
    var createdDate = scnjs.getDateTimeString(group.created_at, scnjs.INSEC);
    var updatedDate = scnjs.getDateTimeString(group.updated_at, scnjs.INSEC);

    var clz = ((i % 2 == 0) ? 'row-odd' : 'row-even');

    html += '<tr class="item-list ' + clz + '">';
    html += '<td class="item-list"><span class="pseudo-link link-button" onclick="scnjs.editGroup(\'' + gid + '\');" data-tooltip2="Edit">' + gid + '</span></td>';
    html += '<td class="item-list">' + name + '</td>';
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
scnjs.newGroup = function() {
  scnjs.editGroup(null);
};

scnjs.editGroup = function(gid) {
  scnjs.groupEditMode = (gid ? 'edit' : 'new');
  if (!scnjs.groupEditWindow) {
    scnjs.groupEditWindow = scnjs.openGroupInfoEditorWindow(scnjs.groupEditMode, gid);
  }
  scnjs.clearGroupInfoEditor();
  if (gid) {
    var params = {
      gid: gid
    };
    scnjs.execCmd('group', params, scnjs.getGroupInfoCb);
  } else {
    $el('#gid').focus();
  }
};

scnjs.openGroupInfoEditorWindow = function(mode, gid) {
  var html = '';
  html += '<div style="position:relative;width:100%;height:100%;text-align:center;vertical-align:middle">';
  if (mode == 'edit') {
    html += '<div style="position:absolute;top:8px;right:8px;"><button class="button-red" onclick="scnjs.deleteGroup(\'' + gid + '\');">DEL</button></div>';
  }
  html += '<div style="padding:4px;position:absolute;top:0;right:0;bottom:0;left:0;margin:auto;width:360px;height:120px;text-align:left;">';

  html += '<table>';
  html += '  <tr>';
  html += '    <td>GID</td>';
  html += '    <td style="width:256px;">';
  html += '      <input type="text" id="gid" style="width:100%;">';
  html += '    </td>';
  html += '  </tr>';
  html += '  <tr>';
  html += '    <td>Name</td>';
  html += '    <td><input type="text" id="group-name" style="width:100%;"></td>';
  html += '  </tr>';
  html += '  <tr>';
  html += '    <td>Privileges</td>';
  html += '    <td><input type="text" id="group-privs" style="width:100%;"></td>';
  html += '  </tr>';
  html += '  <tr>';
  html += '    <td>Description</td>';
  html += '    <td><input type="text" id="group-desc" style="width:100%;"></td>';
  html += '  </tr>';
  html += '</table>';

  html += '<div style="margin-top:24px;text-align:center;">';
  html += '<button onclick="scnjs.saveGroupInfo();">OK</button>'
  html += '<button style="margin-left:8px;" onclick="scnjs.groupEditWindow.close();">Cancel</button>'
  html += '</div>';

  html += '</div>';
  html += '</div>';

  var opt = {
    draggable: true,
    resizable: true,
    pos: 'c',
    closeButton: true,
    width: 480,
    height: 240,
    minWidth: 480,
    minHeight: 240,
    scale: 1,
    hidden: false,
    modal: false,
    title: {
      text: ((mode == 'new') ? 'New' : 'Edit') +' Group',
      style: {
        color: scnjs.dialogTitleFgColor,
        background: scnjs.dialogTitleBgColor
      }
    },
    body: {
      style: {
        color: scnjs.dialogFgColor,
        background: scnjs.dialogBgColor
      }
    },
    onclose: scnjs.onGroupEditWindowClose,
    content: html
  };

  var win = util.newWindow(opt);
  return win;
};

//-----------------------------------------------------------------------------
scnjs.addGroup = function() {
  var gid = $el('#gid').value.trim();
  var name = $el('#group-name').value;
  var privs = $el('#group-privs').value;
  var desc = $el('#group-desc').value;

  if (!gid) {
    scnjs.showInfotip('Group ID is required.', 2000);
    return;
  }

  var clnsRes = scnjs.cleansePrivileges(privs);
  if (clnsRes.msg) {
    scnjs.showInfotip(clnsRes.msg, 2000);
    return;
  }
  privs = clnsRes.val;

  var params = {
    gid: gid,
    name: name,
    privs: privs,
    desc: desc
  };

  scnjs.execCmd('addgroup', params, scnjs.addGroupCb);
};

scnjs.addGroupCb = function(xhr, res) {
  if (xhr.status != 200) {
    scnjs.showInfotip('HTTP ' + xhr.status);
    return;
  }
  scnjs.showInfotip(res.status);
  if (res.status != 'OK') {
    return;
  }
  scnjs.groupEditWindow.close();
  scnjs.getGroupList();
};

//-----------------------------------------------------------------------------
scnjs.updateGroup = function() {
  var gid = $el('#gid').value;
  var name = $el('#group-name').value;
  var privs = $el('#group-privs').value;
  var desc = $el('#group-desc').value;

  var params = {
    gid: gid,
    name: name,
    privs: privs,
    desc: desc
  };

  scnjs.execCmd('modgroup', params, scnjs.updateGroupCb);
};

scnjs.updateGroupCb = function(xhr, res) {
  if (xhr.status != 200) {
    scnjs.showInfotip('HTTP ' + xhr.status);
    return;
  }
  scnjs.showInfotip(res.status);
  if (res.status != 'OK') {
    return;
  }
  scnjs.groupEditWindow.close();
  scnjs.getGroupList();
};

//-----------------------------------------------------------------------------
scnjs.deleteGroup = function(gid) {
  var opt = {
    data: gid
  };
  util.confirm('Delete ' + gid + ' ?', scnjs._deleteGroup, opt);
};
scnjs._deleteGroup = function(gid) {
  if (!gid) {
    return;
  }
  if (scnjs.groupEditWindow) {
    scnjs.groupEditWindow.close();
  }
  var params = {
    gid: gid
  };
  scnjs.execCmd('delgroup', params, scnjs.deleteGroupCb);
};

scnjs.deleteGroupCb = function(xhr, res) {
  if (xhr.status != 200) {
    scnjs.showInfotip('HTTP ' + xhr.status);
    return;
  }
  if (res.status != 'OK') {
    scnjs.showInfotip(res.status);
    return;
  }
  scnjs.showInfotip('OK');
  scnjs.getGroupList();
};

//-----------------------------------------------------------------------------
scnjs.getGroupInfoCb = function(xhr, res) {
  if (xhr.status != 200) {
    scnjs.showInfotip('HTTP ' + xhr.status);
    return;
  }
  if (res.status != 'OK') {
    scnjs.showInfotip(res.status);
    return;
  }
  var info = res.body;
  scnjs.setGroupInfoToEditor(info);
};

scnjs.setGroupInfoToEditor = function(info) {
  var gid = info.gid;
  $el('#gid').value = gid;
  if (gid) {
    $el('#gid').disabled = true;
    $el('#gid').addClass('edit-disabled');
  } else {
    $el('#gid').disabled = false;
    $el('#gid').removeClass('edit-disabled');
  }
  $el('#group-name').value = info.name;
  $el('#group-privs').value = info.privs;
  $el('#group-desc').value = (info.desc ? info.desc : '');
};

scnjs.clearGroupInfoEditor = function() {
  var info = {
    gid: '',
    name: '',
    privs: '',
    desc: ''
  };
  scnjs.setGroupInfoToEditor(info);
};

scnjs.saveGroupInfo = function() {
  if (scnjs.groupEditMode == 'new') {
    scnjs.addGroup();
  } else {
    scnjs.updateGroup();
  }
};

//-----------------------------------------------------------------------------
scnjs.onUserEditWindowClose = function() {
  scnjs.userEditWindow = null;
  scnjs.userEditMode = null;
};

scnjs.onGroupEditWindowClose = function() {
  scnjs.groupEditWindow = null;
  scnjs.groupEditMode = null;
};

scnjs.copy = function(s) {
  util.copy(s);
  var o = {pos: 'pointer'};
  scnjs.showInfotip('Copied', 1000, o);
};

scnjs.showInfotip = function(m, d, o) {
  if (!o) o = {};
  o.style = {
    'font-size': '14px'
  };
  util.infotip.show(m, d, o);
};

$onEnterKey = function(e) {
  if ($el('#timeline-offset').hasFocus()) {
    scnjs.getSessionListN();
  }
};

$onEscKey = function(e) {
  if ($el('#search-text').hasFocus()) {
    scnjs.clearSeachKey();
  }
};

$onCtrlS = function(e) {
};

$onBeforeUnload = function(e) {
  if ((scnjs.userEditWindow) || (scnjs.groupEditWindow)) e.returnValue = '';
};
