/*!
 * Copyright (c) 2023 Takashi Harano
 */
var sysman = {};

sysman.LIST_COLUMNS = [
  {key: 'uid', label: 'UID', style: 'min-width:min-width:10em;'},
  {key: 'name', label: 'Full Name', style: 'min-width:13em;'},
  {key: 'local_name', label: 'Local Full Name', style: 'min-width:10em;'},
  {key: 'is_admin', label: 'Admin'},
  {key: 'group', label: 'Groups', style: 'min-width:15em;'},
  {key: 'privs', label: 'Privileges', style: 'min-width:20em;'},
  {key: 'status', label: 'Status'},
  {key: 'created_at', label: 'Created'},
  {key: 'updated_at', label: 'Updated'},
  {key: 'pw_changed_at', label: 'PwChanged'}
];

sysman.listStatus = {
  sortIdx: 0,
  sortOrder: 1
};

sysman.itemList = [];

sysman.editWindow = null;
sysman.mode = null;

$onReady = function() {
  $el('#user-list').innerHTML = '<span class="progdot">Loading</span>';
  sysman.drawGroupStatus('<span class="progdot">Loading</span>');
};

sysman.onSysReady = function() {
  sysman.getUserList();
  sysman.getGroups();
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
  sysman.execCmd('users', null, sysman.getUserListCb);
};
sysman.getUserListCb = function(xhr, res, req) {
  if (res.status != 'OK') {
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

sysman.drawList = function(items, sortIdx, sortOrder) {
  if (sortIdx >= 0) {
    if (sortOrder > 0) {
      var srtDef = sysman.LIST_COLUMNS[sortIdx];
      var desc = (sortOrder == 2);
      items = sysman.sortList(items, srtDef.key, desc, srtDef.meta);
    }
  }

  var currentUid = websys.getUserId();

  var htmlList = '';
  for (var i = 0; i < items.length; i++) {
    var item = items[i];
    var uid = item.uid;
    var name = item.name.replace(/ /g, '&nbsp');
    var local_name = item.local_name.replace(/ /g, '&nbsp');

    var createdDate = '---------- --:--:--';
    if (item.created_at > 0) {
      var createdAt = item.created_at;
      if (util.isInteger(createdAt)) createdAt *= 1000;
      createdDate = util.getDateTimeString(createdAt, '%YYYY-%MM-%DD %HH:%mm:%SS.%sss');
    }

    var updatedDate = '---------- --:--:--';
    if (item.updated_at > 0) {
      var updatedAt = item.updated_at;
      if (util.isInteger(updatedAt)) updatedAt *= 1000;
      updatedDate = util.getDateTimeString(updatedAt, '%YYYY-%MM-%DD %HH:%mm:%SS.%sss');
    }

    var pwChangedDate = '---------- --:--:--';
    if (item.pw_changed_at > 0) {
      var pwChangedAt = item.pw_changed_at;
      if (util.isInteger(pwChangedAt)) pwChangedAt *= 1000;
      pwChangedDate = util.getDateTimeString(pwChangedAt, '%YYYY-%MM-%DD %HH:%mm:%SS.%sss');
    }

    htmlList += '<tr class="item-list">';
    htmlList += '<td class="item-list">' + uid + '</td>';
    htmlList += '<td class="item-list">' + name + '</td>';
    htmlList += '<td class="item-list">' + local_name + '</td>';
    htmlList += '<td class="item-list" style="text-align:center;">' + (item.is_admin ? 'Y' : '') + '</td>';
    htmlList += '<td class="item-list">' + item.group + '</td>';
    htmlList += '<td class="item-list">' + item.privs + '</td>';
    htmlList += '<td class="item-list" style="text-align:center;">' + item.status + '</td>';
    htmlList += '<td class="item-list" style="text-align:center;">' + createdDate + '</td>';
    htmlList += '<td class="item-list" style="text-align:center;">' + updatedDate + '</td>';
    htmlList += '<td class="item-list" style="text-align:center;">' + pwChangedDate + '</td>';
    htmlList += '<td class="item-list"><span class="pseudo-link" style="color:#0cf;text-align:center;" onclick="sysman.editUser(\'' + uid + '\');">EDIT</span></td>';
    htmlList += '<td class="item-list" style="text-align:center;width:1.5em;">';
    if (uid == currentUid) {
      htmlList += '&nbsp;';
    } else {
      htmlList += '<span class="pseudo-link" style="color:#f88;" onclick="sysman.deleteUser(\'' + uid + '\');">X</span>';
    }
    htmlList += '</td>';
    htmlList += '</tr>';
  }
  htmlList += '</table>';

  var htmlHead = sysman.buildListHeader(sysman.LIST_COLUMNS, sortIdx, sortOrder);
  var html = htmlHead + htmlList; 

  sysman.drawListContent(html);
};

sysman.drawListContent = function(html) {
  $el('#user-list').innerHTML = html;
};

sysman.buildListHeader = function(columns, sortIdx, sortOrder) {
  var html = '<table>';
  html += '<tr class="item-list-header">';

  for (var i = 0; i < columns.length; i++) {
    var column = columns[i];
    var label = column['label'];

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
    html += '><span>' + label + '</span> ' + sortButton + '</th>';
  }
  html += '<th class="item-list">&nbsp;</th>';
  html += '<th class="item-list">&nbsp;</th>';
  html += '</tr>';
  return html;
};

sysman.sortItemList = function(sortIdx, sortOrder) {
  if (sortOrder > 2) {
    sortOrder = 0;
  }
  sysman.listStatus.sortIdx = sortIdx;
  sysman.listStatus.sortOrder = sortOrder;
  sysman.drawList(sysman.itemList, sortIdx, sortOrder);
};

//-----------------------------------------------------------------------------
sysman.newUser = function() {
  sysman.editUser(null);
};

sysman.editUser = function(uid) {
  sysman.mode = (uid ? 'edit' : 'new');
  if (!sysman.editWindow) {
    sysman.editWindow = sysman.openUserInfoEditorWindow(sysman.mode);
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

sysman.openUserInfoEditorWindow = function(mode) {
  var html = '';
  html += '<div style="position:relative;width:100%;height:100%;text-align:center;vertical-align:middle">';
  html += '<div style="padding:4px;position:absolute;top:0;right:0;bottom:0;left:0;margin:auto;width:360px;height:260px;text-align:left;">';

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
  html += '<button style="margin-left:8px;" onclick="sysman.editWindow.close();">Cancel</button>'
  html += '</div>';

  html += '</div>';
  html += '</div>';

  var opt = {
    draggable: true,
    resizable: true,
    pos: 'c',
    closeButton: true,
    width: 480,
    height: 360,
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
    onclose: sysman.onEditWindowClose,
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
log(res)
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
    status: ''
  };
  sysman.setUserInfoToEditor(info);
};

sysman.saveUserInfo = function() {
  if (sysman.mode == 'new') {
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
  sysman.editWindow.close();
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
  sysman.editWindow.close();
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
  var params = {
    uid: uid,
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
sysman.sortList = function(itemList, sortKey, desc) {
  var items = util.copyObject(itemList);
  var srcList = items;
  var asNum = true;
  var sortedList = util.sortObject(srcList, sortKey, desc, asNum);
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

sysman.getGroups = function() {
  sysman.callApi('get_groups', null, sysman.getGroupsCb);
};
sysman.getGroupsCb = function(xhr, res) {
  sysman.drawGroupStatus('');
  var s = util.decodeBase64(res.body.text);
  $el('#groups').value = s;
};

sysman.confirmSaveGroups = function() {
  util.confirm('Save?', sysman.saveGroups);
};
sysman.saveGroups = function() {
  var s = $el('#groups').value;
  var b64 = util.encodeBase64(s);
  var params = {
    text: b64
  }
  sysman.callApi('save_groups', params, sysman.saveGroupsCb);
};
sysman.saveGroupsCb = function(xhr, res) {
  sysman.showInfotip('OK');
};

//-----------------------------------------------------------------------------
sysman.onEditWindowClose = function() {
  sysman.editWindow = null;
  sysman.mode = null;
};

$onCtrlS = function(e) {
  if ($el('#groups').hasFocus()) {
    sysman.confirmSaveGroups();
  }
};

$onBeforeUnload = function(e) {
  if (sysman.editWindow) e.returnValue = '';
};
