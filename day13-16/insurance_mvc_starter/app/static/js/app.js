/**
 * app.js —— SPA 主逻辑：hash 路由 + 权限控制 + 页面渲染 + 公共交互工具
 *
 * 【架构】
 * 1. AppUtils：全局工具（loading/toast/pagination/escape/statusTag/modal）
 * 2. Router：hash 变化监听 → 解析 route/subroute → 分发到对应渲染函数
 * 3. 渲染函数：renderLogin / renderLayout(含侧边菜单) / renderData / renderModel / renderEmail / renderLogs
 *
 * 【路由设计】
 * #login                        登录页
 * #data/upload                  数据上传
 * #data/customers               客户列表
 * #data/overview                数据概览（统计+质量+EDA）
 * #model/train                  模型训练（admin）
 * #model/experiments            实验记录（admin）
 * #model/predict                全量预测
 * #model/visualization          评估图表
 * #model/io                     模型导入导出（admin）
 * #email/targets                高潜客户筛选
 * #email/records                邮件记录管理
 * #email/prompt                 Prompt 模板编辑
 * #logs                         操作日志（admin）
 *
 * 【约束】
 * - 技术栈：Bootstrap5 + 原生 JS，无构建工具
 * - 所有请求走 api.js 封装，自动携带 token + 统一错误处理
 * - 页面切换清空上一页查询条件
 * - 分页组件统一复用 renderPagination
 */
(function () {
  'use strict';

  // ===== 全局状态 =====
  var currentUser = null; // { id, username, role }

  // ========================================================================
  //  1. 公共工具 AppUtils
  // ========================================================================
  var AppUtils = {

    /** Loading 遮罩 */
    showLoading: function () {
      var el = document.getElementById('loadingOverlay');
      if (el) el.style.display = 'flex';
    },
    hideLoading: function () {
      var el = document.getElementById('loadingOverlay');
      if (el) el.style.display = 'none';
    },

    /** Toast 提示（type: success/danger/warning/info） */
    showToast: function (msg, type) {
      var container = document.getElementById('toastContainer');
      if (!container) return;
      var item = document.createElement('div');
      item.className = 'toast-item toast-' + (type || 'info');
      var iconMap = { success: 'check-circle', danger: 'x-circle', warning: 'exclamation-triangle', info: 'info-circle' };
      item.innerHTML = '<i class="bi bi-' + (iconMap[type] || 'info-circle') + ' me-2"></i>' + AppUtils.escapeHtml(msg);
      container.appendChild(item);
      setTimeout(function () {
        item.style.opacity = '0';
        item.style.transition = 'opacity 0.3s';
        setTimeout(function () { if (item.parentNode) item.parentNode.removeChild(item); }, 300);
      }, 3000);
    },

    /** HTML 转义防 XSS */
    escapeHtml: function (str) {
      if (str == null) return '';
      return String(str).replace(/[&<>"']/g, function (c) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
      });
    },

    /** 格式化时间（ISO → yyyy-mm-dd HH:MM） */
    formatTime: function (isoStr) {
      if (!isoStr) return '-';
      var d = new Date(isoStr);
      if (isNaN(d.getTime())) return isoStr;
      var pad = function (n) { return n < 10 ? '0' + n : n; };
      return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) +
        ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
    },

    /**
     * 统一分页渲染
     * @param {object} pageData - { total, page, per_page, pages }
     * @param {function} goPage - 点击页码回调，接收 page 参数
     * @returns {string} HTML 字符串
     */
    renderPagination: function (pageData, goPage) {
      if (!pageData || pageData.pages <= 1) return '';
      var page = pageData.page, pages = pageData.pages;
      var html = '<nav><ul class="pagination justify-content-center">';

      // 上一页
      html += '<li class="page-item ' + (page <= 1 ? 'disabled' : '') + '">';
      html += '<a class="page-link" href="javascript:void(0)" onclick="' + goPage + '(' + (page - 1) + ')">&laquo;</a></li>';

      // 页码：显示当前页前后各 2 页
      var start = Math.max(1, page - 2), end = Math.min(pages, page + 2);
      if (start > 1) {
        html += '<li class="page-item"><a class="page-link" href="javascript:void(0)" onclick="' + goPage + '(1)">1</a></li>';
        if (start > 2) html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
      }
      for (var i = start; i <= end; i++) {
        html += '<li class="page-item ' + (i === page ? 'active' : '') + '">';
        html += '<a class="page-link" href="javascript:void(0)" onclick="' + goPage + '(' + i + ')">' + i + '</a></li>';
      }
      if (end < pages) {
        if (end < pages - 1) html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
        html += '<li class="page-item"><a class="page-link" href="javascript:void(0)" onclick="' + goPage + '(' + pages + ')">' + pages + '</a></li>';
      }

      // 下一页
      html += '<li class="page-item ' + (page >= pages ? 'disabled' : '') + '">';
      html += '<a class="page-link" href="javascript:void(0)" onclick="' + goPage + '(' + (page + 1) + ')">&raquo;</a></li>';
      html += '</ul></nav>';
      return html;
    },

    /** 邮件状态标签 */
    statusTag: function (status) {
      var map = { generated: 'status-generated', failed: 'status-failed', sent: 'status-sent' };
      var labelMap = { generated: '已生成', failed: '生成失败', sent: '已发送' };
      var cls = map[status] || 'status-failed';
      var label = labelMap[status] || status;
      return '<span class="status-tag ' + cls + '">' + label + '</span>';
    },

    /** 操作日志 action 标签 */
    actionTag: function (action) {
      var map = {
        model_training: { cls: 'action-training', label: '模型训练' },
        prediction: { cls: 'action-prediction', label: '概率预测' },
        model_import: { cls: 'action-import', label: '模型导入' },
        email_generation: { cls: 'action-email-gen', label: '邮件生成' },
        email_update: { cls: 'action-email-update', label: '邮件修改' },
        email_mark: { cls: 'action-email-mark', label: '邮件标记' },
        email_delete: { cls: 'action-email-delete', label: '邮件删除' }
      };
      var info = map[action] || { cls: 'action-import', label: action };
      return '<span class="action-tag ' + info.cls + '">' + info.label + '</span>';
    },

    /**
     * 通用弹窗
     * @param {object} opts - { title, bodyHtml, footerHtml, size, onShown }
     */
    showModal: function (opts) {
      var container = document.getElementById('modalContainer');
      var sizeClass = opts.size === 'lg' ? 'modal-lg' : (opts.size === 'xl' ? 'modal-xl' : '');
      container.innerHTML =
        '<div class="modal fade" id="appModal" tabindex="-1">' +
        '  <div class="modal-dialog modal-dialog-centered ' + sizeClass + '">' +
        '    <div class="modal-content">' +
        '      <div class="modal-header">' +
        '        <h5 class="modal-title">' + AppUtils.escapeHtml(opts.title || '') + '</h5>' +
        '        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>' +
        '      </div>' +
        '      <div class="modal-body">' + (opts.bodyHtml || '') + '</div>' +
        (opts.footerHtml ? '      <div class="modal-footer">' + opts.footerHtml + '</div>' : '') +
        '    </div>' +
        '  </div>' +
        '</div>';
      var modalEl = document.getElementById('appModal');
      var bsModal = new bootstrap.Modal(modalEl);
      bsModal.show();
      if (typeof opts.onShown === 'function') {
        modalEl.addEventListener('shown.bs.modal', opts.onShown, { once: true });
      }
      // 关闭时清理 DOM
      modalEl.addEventListener('hidden.bs.modal', function () {
        container.innerHTML = '';
      });
      return bsModal;
    },

    /** 关闭弹窗 */
    hideModal: function () {
      var modalEl = document.getElementById('appModal');
      if (modalEl) {
        var bsModal = bootstrap.Modal.getInstance(modalEl);
        if (bsModal) bsModal.hide();
      }
    },

    /** 空状态 HTML */
    emptyState: function (text) {
      return '<div class="empty-state"><div class="empty-icon"><i class="bi bi-inbox"></i></div><div class="empty-text">' + (text || '暂无数据') + '</div></div>';
    },

    /** 文件大小校验（.xlsx, 50MB） */
    validateExcelFile: function (file) {
      if (!file) return '请选择文件';
      var name = file.name.toLowerCase();
      if (!name.endsWith('.xlsx') && !name.endsWith('.xls')) return '仅支持 .xlsx / .xls 格式';
      if (file.size > 50 * 1024 * 1024) return '文件大小不能超过 50MB';
      return null;
    },

    /** 模型文件校验（.joblib） */
    validateModelFile: function (file) {
      if (!file) return '请选择文件';
      var name = file.name.toLowerCase();
      if (!name.endsWith('.joblib')) return '仅支持 .joblib 格式';
      return null;
    }
  };

  // 暴露到全局（api.js 的 _toast 依赖 window.AppUtils.showToast）
  window.AppUtils = AppUtils;

  // ========================================================================
  //  2. 菜单配置
  // ========================================================================
  // admin 可见全部 11 项，user 可见 7 项（隐藏 adminOnly 的 4 项）
  var MENUS = [
    // 数据管理（3 项，全员可见）
    { hash: 'data/upload',      label: '数据上传',   icon: 'cloud-upload',     adminOnly: false },
    { hash: 'data/customers',   label: '客户列表',   icon: 'people',           adminOnly: false },
    { hash: 'data/overview',    label: '数据概览',   icon: 'bar-chart-line',   adminOnly: false },
    // 模型管理（4 项，训练/实验/导入导出 admin-only，预测/图表全员）
    { hash: 'model/train',      label: '模型训练',   icon: 'cpu',              adminOnly: true  },
    { hash: 'model/experiments',label: '实验记录',   icon: 'list-check',       adminOnly: true  },
    { hash: 'model/predict',    label: '模型预测',   icon: 'lightning-charge', adminOnly: false },
    { hash: 'model/visualization', label: '评估图表',icon: 'graph-up-arrow',   adminOnly: false },
    { hash: 'model/io',         label: '模型导入导出',icon: 'box-arrow-in-down',adminOnly: true  },
    // 邮件营销（2 项，全员可见）
    { hash: 'email/targets',    label: '高潜客户',   icon: 'bullseye',         adminOnly: false },
    { hash: 'email/records',    label: '邮件管理',   icon: 'envelope',         adminOnly: false },
    // 操作日志（1 项，admin-only）
    { hash: 'logs',             label: '操作日志',   icon: 'journal-text',     adminOnly: true  }
  ];

  /** 根据角色过滤菜单 */
  function getMenus() {
    var role = currentUser ? currentUser.role : 'user';
    return MENUS.filter(function (m) {
      return !m.adminOnly || role === 'admin';
    });
  }

  // ========================================================================
  //  3. 路由系统
  // ========================================================================

  /** 解析当前 hash → { route, subroute } */
  function parseHash() {
    var hash = location.hash.replace(/^#/, '');
    if (!hash) hash = 'data/upload';
    var parts = hash.split('/');
    return { route: parts[0], subroute: parts[1] || '', full: hash };
  }

  /** 路由分发 */
  function router() {
    var parsed = parseHash();
    var app = document.getElementById('app');

    // 未登录 → 强制登录页
    if (!currentUser && parsed.route !== 'login') {
      location.hash = '#login';
      return;
    }
    // 已登录访问登录页 → 跳首页
    if (currentUser && parsed.route === 'login') {
      location.hash = '#data/upload';
      return;
    }

    if (parsed.route === 'login') {
      renderLogin(app);
      return;
    }

    // 权限校验：adminOnly 路由
    var menu = MENUS.find(function (m) { return m.hash === parsed.full; });
    if (menu && menu.adminOnly && currentUser.role !== 'admin') {
      AppUtils.showToast('权限不足，无法访问该页面', 'danger');
      location.hash = '#data/upload';
      return;
    }

    // 渲染主布局 + 对应页面
    renderLayout(app, parsed.full);
  }

  // ========================================================================
  //  4. 登录页
  // ========================================================================
  function renderLogin(app) {
    app.innerHTML =
      '<div class="login-wrapper">' +
      '  <div class="login-card">' +
      '    <div class="login-logo"><i class="bi bi-shield-shaded"></i></div>' +
      '    <div class="login-title">保险精准营销系统</div>' +
      '    <div class="login-subtitle">Insurance AI Marketing Platform</div>' +
      '    <div class="login-form">' +
      '      <div class="mb-3">' +
      '        <label class="form-label">用户名</label>' +
      '        <input type="text" class="form-control" id="loginUsername" placeholder="请输入用户名" autocomplete="username">' +
      '      </div>' +
      '      <div class="mb-3">' +
      '        <label class="form-label">密码</label>' +
      '        <input type="password" class="form-control" id="loginPassword" placeholder="请输入密码" autocomplete="current-password">' +
      '      </div>' +
      '      <div id="loginError" class="form-error mb-2" style="display:none;"></div>' +
      '      <button class="btn btn-primary" id="btnLogin" onclick="window._handleLogin()">登 录</button>' +
      '    </div>' +
      '    <div class="login-toggle">还没有账号？<a onclick="window._toggleRegister()">注册新用户</a></div>' +
      '  </div>' +
      '</div>';

    // 回车登录
    document.getElementById('loginPassword').addEventListener('keydown', function (e) {
      if (e.key === 'Enter') window._handleLogin();
    });
    document.getElementById('loginUsername').addEventListener('keydown', function (e) {
      if (e.key === 'Enter') document.getElementById('loginPassword').focus();
    });
  }

  /** 切换注册表单 */
  window._toggleRegister = function () {
    var card = document.querySelector('.login-card');
    var isRegister = card.dataset.mode === 'register';
    if (isRegister) {
      card.dataset.mode = 'login';
      card.querySelector('.login-title').textContent = '保险精准营销系统';
      card.querySelector('.btn-primary').textContent = '登 录';
      card.querySelector('.btn-primary').setAttribute('onclick', 'window._handleLogin()');
      card.querySelector('.login-toggle').innerHTML = '还没有账号？<a onclick="window._toggleRegister()">注册新用户</a>';
    } else {
      card.dataset.mode = 'register';
      card.querySelector('.login-title').textContent = '注册新账号';
      card.querySelector('.btn-primary').textContent = '注 册';
      card.querySelector('.btn-primary').setAttribute('onclick', 'window._handleRegister()');
      card.querySelector('.login-toggle').innerHTML = '已有账号？<a onclick="window._toggleRegister()">返回登录</a>';
    }
  };

  /** 处理登录 */
  window._handleLogin = function () {
    var username = document.getElementById('loginUsername').value.trim();
    var password = document.getElementById('loginPassword').value.trim();
    var errEl = document.getElementById('loginError');

    if (!username || !password) {
      errEl.textContent = '请输入用户名和密码';
      errEl.style.display = 'block';
      return;
    }
    errEl.style.display = 'none';
    AppUtils.showLoading();

    authApi.login(username, password).then(function (data) {
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('user_info', JSON.stringify(data.user));
      currentUser = data.user;
      AppUtils.showToast('登录成功', 'success');
      location.hash = '#data/upload';
    }).catch(function () {}).finally(function () {
      AppUtils.hideLoading();
    });
  };

  /** 处理注册 */
  window._handleRegister = function () {
    var username = document.getElementById('loginUsername').value.trim();
    var password = document.getElementById('loginPassword').value.trim();
    var errEl = document.getElementById('loginError');

    if (!username || !password) {
      errEl.textContent = '请输入用户名和密码';
      errEl.style.display = 'block';
      return;
    }
    if (password.length < 6) {
      errEl.textContent = '密码至少 6 位';
      errEl.style.display = 'block';
      return;
    }
    errEl.style.display = 'none';
    AppUtils.showLoading();

    authApi.register(username, password).then(function (data) {
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('user_info', JSON.stringify(data.user));
      currentUser = data.user;
      AppUtils.showToast('注册成功', 'success');
      location.hash = '#data/upload';
    }).catch(function () {}).finally(function () {
      AppUtils.hideLoading();
    });
  };

  // ========================================================================
  //  5. 主布局（侧边栏 + 顶栏 + 内容容器）
  // ========================================================================
  function renderLayout(app, activeHash) {
    var menus = getMenus();
    var menuHtml = '';
    for (var i = 0; i < menus.length; i++) {
      var m = menus[i];
      var isActive = activeHash === m.hash ? 'active' : '';
      menuHtml +=
        '<li class="nav-item">' +
        '  <a href="#' + m.hash + '" class="' + isActive + '">' +
        '    <span class="menu-icon"><i class="bi bi-' + m.icon + '"></i></span>' +
        '    <span>' + m.label + '</span>' +
        '  </a>' +
        '</li>';
    }

    var initial = currentUser.username.charAt(0).toUpperCase();
    app.innerHTML =
      '<div class="app-layout">' +
      // 侧边栏
      '  <div class="sidebar">' +
      '    <div class="sidebar-brand">' +
      '      <span class="brand-icon"><i class="bi bi-shield-shaded"></i></span>' +
      '      <span>保险精准营销</span>' +
      '    </div>' +
      '    <ul class="sidebar-menu">' + menuHtml + '</ul>' +
      '    <div class="sidebar-footer">' +
      '      <div class="sidebar-user">' +
      '        <span class="user-avatar">' + initial + '</span>' +
      '        <span>' + AppUtils.escapeHtml(currentUser.username) + ' (' + currentUser.role + ')</span>' +
      '      </div>' +
      '    </div>' +
      '  </div>' +
      // 主内容
      '  <div class="main-content">' +
      '    <div class="topbar">' +
      '      <span class="topbar-title" id="pageTitle">保险精准营销系统</span>' +
      '      <span class="topbar-subtitle" id="pageSubtitle"></span>' +
      '      <div class="topbar-actions">' +
      '        <button class="btn btn-sm btn-outline-secondary" onclick="window._handleLogout()">' +
      '          <i class="bi bi-box-arrow-right"></i> 退出' +
      '        </button>' +
      '      </div>' +
      '    </div>' +
      '    <div class="page-container" id="pageContent"></div>' +
      '  </div>' +
      '</div>';

    // 渲染对应页面
    var parsed = parseHash();
    var contentEl = document.getElementById('pageContent');
    var titleEl = document.getElementById('pageTitle');
    var subtitleEl = document.getElementById('pageSubtitle');

    var menuInfo = MENUS.find(function (m) { return m.hash === activeHash; });
    if (menuInfo) {
      titleEl.textContent = menuInfo.label;
    }

    if (parsed.route === 'data') renderDataPage(contentEl, parsed.subroute);
    else if (parsed.route === 'model') renderModelPage(contentEl, parsed.subroute);
    else if (parsed.route === 'email') renderEmailPage(contentEl, parsed.subroute);
    else if (parsed.route === 'logs') renderLogsPage(contentEl);
    else contentEl.innerHTML = AppUtils.emptyState('页面不存在');
  }

  /** 退出登录 */
  window._handleLogout = function () {
    authApi.logout().catch(function () {}).finally(function () {
      localStorage.clear();
      currentUser = null;
      location.hash = '#login';
    });
  };

  // ========================================================================
  //  6. 数据管理页
  // ========================================================================
  function renderDataPage(el, sub) {
    if (sub === 'upload') renderDataUpload(el);
    else if (sub === 'customers') renderDataCustomers(el);
    else if (sub === 'overview') renderDataOverview(el);
    else renderDataUpload(el);
  }

  // --- 6.1 数据上传 ---
  function renderDataUpload(el) {
    el.innerHTML =
      '<div class="card">' +
      '  <div class="card-header"><i class="bi bi-cloud-upload me-2"></i>Excel 数据上传</div>' +
      '  <div class="card-body">' +
      '    <div class="upload-zone" id="uploadZone" onclick="document.getElementById(\'fileInput\').click()">' +
      '      <div class="upload-icon"><i class="bi bi-file-earmark-spreadsheet"></i></div>' +
      '      <div class="upload-text">点击或拖拽文件到此处上传</div>' +
      '      <div class="upload-hint">支持 .xlsx / .xls 格式，最大 50MB</div>' +
      '    </div>' +
      '    <input type="file" id="fileInput" accept=".xlsx,.xls" style="display:none;" onchange="window._handleFileSelect(this)">' +
      '    <div id="fileInfo" class="mt-3" style="display:none;">' +
      '      <div class="d-flex align-items-center gap-2">' +
      '        <i class="bi bi-file-earmark text-primary"></i>' +
      '        <span id="fileName" class="text-secondary"></span>' +
      '        <span id="fileSize" class="text-muted" style="font-size:12px;"></span>' +
      '      </div>' +
      '    </div>' +
      '    <div class="mt-3">' +
      '      <button class="btn btn-primary" id="btnUpload" onclick="window._handleUpload()" disabled>' +
      '        <i class="bi bi-upload me-1"></i>开始上传' +
      '      </button>' +
      '    </div>' +
      '    <div id="uploadResult" class="mt-3"></div>' +
      '  </div>' +
      '</div>' +
      '<div class="card mt-3">' +
      '  <div class="card-header"><i class="bi bi-info-circle me-2"></i>字段说明</div>' +
      '  <div class="card-body">' +
      '    <p class="text-secondary mb-1">上传文件须包含以下字段（表头名称须完全一致）：</p>' +
      '    <code class="text-muted" style="font-size:12px;">id, Gender, Age, Driving_License, Region_Code, Previously_Insured, Vehicle_Age, Vehicle_Damage, Annual_Premium, Policy_Sales_Channel, Vintage, Response</code>' +
      '    <p class="text-muted mt-2 mb-0" style="font-size:13px;">注意：上传会清空旧数据并重新导入。</p>' +
      '  </div>' +
      '</div>';

    // 拖拽支持
    var zone = document.getElementById('uploadZone');
    zone.addEventListener('dragover', function (e) { e.preventDefault(); zone.classList.add('dragover'); });
    zone.addEventListener('dragleave', function () { zone.classList.remove('dragover'); });
    zone.addEventListener('drop', function (e) {
      e.preventDefault();
      zone.classList.remove('dragover');
      if (e.dataTransfer.files.length > 0) {
        document.getElementById('fileInput').files = e.dataTransfer.files;
        window._handleFileSelect(document.getElementById('fileInput'));
      }
    });
  }

  var selectedFile = null;

  window._handleFileSelect = function (input) {
    var file = input.files[0];
    var err = AppUtils.validateExcelFile(file);
    var errEl = document.getElementById('uploadResult');
    if (err) {
      errEl.innerHTML = '<div class="alert alert-danger py-2">' + err + '</div>';
      document.getElementById('btnUpload').disabled = true;
      document.getElementById('fileInfo').style.display = 'none';
      selectedFile = null;
      return;
    }
    selectedFile = file;
    errEl.innerHTML = '';
    document.getElementById('fileName').textContent = file.name;
    document.getElementById('fileSize').textContent = (file.size / 1024).toFixed(1) + ' KB';
    document.getElementById('fileInfo').style.display = 'block';
    document.getElementById('btnUpload').disabled = false;
  };

  window._handleUpload = function () {
    if (!selectedFile) return;
    AppUtils.showLoading();
    dataApi.upload(selectedFile).then(function (data) {
      var html = '<div class="alert alert-success">' +
        '<i class="bi bi-check-circle me-2"></i>上传成功！共导入 ' + data.imported_count + ' 条数据' +
        '</div>';
      if (data.quality_report) {
        var qr = data.quality_report;
        html += '<div class="card mt-2"><div class="card-header py-2">数据质量报告</div><div class="card-body py-2">' +
          '<div class="row g-2">' +
          '<div class="col-4"><small class="text-muted">总行数</small><div class="fw-600">' + (qr.total_rows || 0) + '</div></div>' +
          '<div class="col-4"><small class="text-muted">总列数</small><div class="fw-600">' + (qr.total_cols || 0) + '</div></div>' +
          '<div class="col-4"><small class="text-muted">重复行</small><div class="fw-600">' + (qr.duplicates || 0) + '</div></div>' +
          '</div></div></div>';
      }
      document.getElementById('uploadResult').innerHTML = html;
      AppUtils.showToast('上传成功', 'success');
    }).catch(function () {}).finally(function () {
      AppUtils.hideLoading();
    });
  };

  // --- 6.2 客户列表 ---
  var customerFilters = { page: 1, per_page: 20, gender: '', age_min: '', age_max: '', previously_insured: '', keyword: '' };

  function renderDataCustomers(el) {
    // 重置筛选条件
    customerFilters = { page: 1, per_page: 20, gender: '', age_min: '', age_max: '', previously_insured: '', keyword: '' };

    el.innerHTML =
      '<div class="card mb-3">' +
      '  <div class="card-header"><i class="bi bi-funnel me-2"></i>筛选条件</div>' +
      '  <div class="card-body">' +
      '    <div class="row g-3">' +
      '      <div class="col-md-3"><label class="form-label">性别</label>' +
      '        <select class="form-select" id="filterGender"><option value="">全部</option><option value="Male">男</option><option value="Female">女</option></select></div>' +
      '      <div class="col-md-2"><label class="form-label">最小年龄</label><input type="number" class="form-control" id="filterAgeMin"></div>' +
      '      <div class="col-md-2"><label class="form-label">最大年龄</label><input type="number" class="form-control" id="filterAgeMax"></div>' +
      '      <div class="col-md-2"><label class="form-label">是否已投保</label>' +
      '        <select class="form-select" id="filterInsured"><option value="">全部</option><option value="1">是</option><option value="0">否</option></select></div>' +
      '      <div class="col-md-3"><label class="form-label">客户ID搜索</label><input type="text" class="form-control" id="filterKeyword" placeholder="输入客户ID"></div>' +
      '    </div>' +
      '    <div class="mt-3">' +
      '      <button class="btn btn-primary btn-sm" onclick="window._searchCustomers()"><i class="bi bi-search me-1"></i>查询</button>' +
      '      <button class="btn btn-outline-secondary btn-sm ms-2" onclick="window._resetCustomerFilter()"><i class="bi bi-arrow-counterclockwise me-1"></i>重置</button>' +
      '    </div>' +
      '  </div>' +
      '</div>' +
      '<div class="card">' +
      '  <div class="card-header"><i class="bi bi-table me-2"></i>客户列表</div>' +
      '  <div class="card-body" id="customerTableBody">' + AppUtils.emptyState('点击查询加载数据') + '</div>' +
      '</div>';

    window._searchCustomers();
  }

  window._searchCustomers = function () {
    customerFilters.page = 1;
    customerFilters.gender = document.getElementById('filterGender').value;
    customerFilters.age_min = document.getElementById('filterAgeMin').value;
    customerFilters.age_max = document.getElementById('filterAgeMax').value;
    customerFilters.previously_insured = document.getElementById('filterInsured').value;
    customerFilters.keyword = document.getElementById('filterKeyword').value;
    loadCustomers();
  };

  window._resetCustomerFilter = function () {
    document.getElementById('filterGender').value = '';
    document.getElementById('filterAgeMin').value = '';
    document.getElementById('filterAgeMax').value = '';
    document.getElementById('filterInsured').value = '';
    document.getElementById('filterKeyword').value = '';
    window._searchCustomers();
  };

  window._goCustomerPage = function (page) {
    customerFilters.page = page;
    loadCustomers();
  };

  function loadCustomers() {
    var body = document.getElementById('customerTableBody');
    AppUtils.showLoading();
    dataApi.customers(customerFilters).then(function (data) {
      var items = data.items || [];
      if (items.length === 0) {
        body.innerHTML = AppUtils.emptyState('暂无客户数据');
        return;
      }
      var html = '<div class="table-responsive"><table class="table table-hover">' +
        '<thead><tr>' +
        '<th>ID</th><th>性别</th><th>年龄</th><th>驾照</th><th>已投保</th><th>车龄</th><th>曾受损</th><th>年保费</th><th>购买</th><th>预测概率</th>' +
        '</tr></thead><tbody>';
      for (var i = 0; i < items.length; i++) {
        var c = items[i];
        var prob = c.predicted_prob != null ? (c.predicted_prob * 100).toFixed(1) + '%' : '-';
        html += '<tr>' +
          '<td>' + c.id + '</td>' +
          '<td>' + (c.gender === 'Male' ? '男' : '女') + '</td>' +
          '<td>' + c.age + '</td>' +
          '<td>' + (c.driving_license ? '有' : '无') + '</td>' +
          '<td>' + (c.previously_insured ? '是' : '否') + '</td>' +
          '<td>' + AppUtils.escapeHtml(c.vehicle_age || '-') + '</td>' +
          '<td>' + (c.vehicle_damage ? '是' : '否') + '</td>' +
          '<td>' + (c.annual_premium || '-') + '</td>' +
          '<td>' + (c.response ? '<span class="text-success">是</span>' : '<span class="text-muted">否</span>') + '</td>' +
          '<td>' + prob + '</td>' +
          '</tr>';
      }
      html += '</tbody></table></div>';
      html += '<div class="d-flex justify-content-between align-items-center mt-3">' +
        '<span class="text-muted" style="font-size:13px;">共 ' + data.total + ' 条</span>' +
        AppUtils.renderPagination(data, 'window._goCustomerPage') +
        '</div>';
      body.innerHTML = html;
    }).catch(function () {}).finally(function () {
      AppUtils.hideLoading();
    });
  }

  // --- 6.3 数据概览 ---
  function renderDataOverview(el) {
    el.innerHTML =
      '<div class="row g-3 mb-3" id="statCards"></div>' +
      '<div class="row g-3 mb-3" id="qualityRow"></div>' +
      '<div class="card"><div class="card-header"><i class="bi bi-bar-chart me-2"></i>EDA 可视化</div>' +
      '  <div class="card-body" id="edaCharts">' + AppUtils.emptyState('加载中...') + '</div>' +
      '</div>';

    // 加载统计
    AppUtils.showLoading();
    dataApi.statistics().then(function (stat) {
      var cards = '';
      cards += '<div class="col-md-3"><div class="stat-card"><div class="stat-label">客户总数</div><div class="stat-value text-primary">' + stat.total + '</div></div></div>';
      cards += '<div class="col-md-3"><div class="stat-card"><div class="stat-label">男性客户</div><div class="stat-value">' + (stat.gender_distribution.Male || 0) + '</div></div></div>';
      cards += '<div class="col-md-3"><div class="stat-card"><div class="stat-label">女性客户</div><div class="stat-value">' + (stat.gender_distribution.Female || 0) + '</div></div></div>';
      var respDist = stat.response_distribution;
      var resp1 = resp1 = (respDist['1'] || respDist[1] || 0);
      var resp0 = (respDist['0'] || respDist[0] || 0);
      var rate = stat.total > 0 ? (resp1 / stat.total * 100).toFixed(1) : '0';
      cards += '<div class="col-md-3"><div class="stat-card"><div class="stat-label">购买率</div><div class="stat-value text-success">' + rate + '%</div><div class="stat-sub">购买 ' + resp1 + ' / 不买 ' + resp0 + '</div></div></div>';
      document.getElementById('statCards').innerHTML = cards;
    }).catch(function () {});

    // 加载质量报告
    dataApi.quality().then(function (qr) {
      // 原始上传列缺失值展示（这些是用户上传的原始字段，缺失=真异常）
      var missingParts = [];
      var missingCount = 0;
      if (qr.missing_values) {
        for (var k in qr.missing_values) {
          if (qr.missing_values[k] > 0) { missingParts.push(k + ': ' + qr.missing_values[k]); missingCount += qr.missing_values[k]; }
        }
      }
      var missingHtml = missingParts.length > 0
        ? '<span class="' + (missingCount > 0 ? 'text-warning' : 'text-success') + '">' + missingParts.join('，') + '</span>'
        : '<span class="text-success">无缺失值 <i class="bi bi-check-circle ms-1"></i></span>';

      // 系统衍生列填充状态（predicted_prob 等是预测后才填，全空=正常，不再误导）
      var derivedHtml = '';
      if (qr.derived_column_status) {
        var labelMap = {
          predicted_prob: '预测概率',
          uploaded_by: '上传者',
          created_at: '入库时间',
        };
        derivedHtml = '<div class="mt-3 pt-3 border-top"><div class="stat-label mb-2">系统衍生列填充进度（非缺失，预测/上传后自动填充）</div><div class="row g-2">';
        var keys = Object.keys(qr.derived_column_status);
        for (var i = 0; i < keys.length; i++) {
          var key = keys[i];
          var s = qr.derived_column_status[key];
          var label = labelMap[key] || key;
          var ratio = (s.ratio || 0) * 100;
          var barClass = ratio >= 100 ? 'bg-success' : (ratio > 0 ? 'bg-info' : 'bg-secondary');
          var statusText = ratio >= 100
            ? '<span class="text-success ms-1">已完整</span>'
            : (ratio > 0
                ? '<span class="text-info ms-1">部分填充</span>'
                : '<span class="text-muted ms-1">待填充</span>');
          derivedHtml += '<div class="col-md-4"><div class="small mb-1">' + label + statusText +
            '<div class="form-text">' + (s.description || '') + '</div></div>' +
            '<div class="progress" style="height:8px;"><div class="progress-bar ' + barClass + '" style="width:' + ratio.toFixed(0) + '%"></div></div>' +
            '<div class="small text-muted mt-1">' + s.filled + ' / ' + s.total + '（' + ratio.toFixed(1) + '%）</div></div>';
        }
        derivedHtml += '</div></div>';
      }

      var html = '<div class="col-md-12"><div class="card"><div class="card-header"><i class="bi bi-clipboard-check me-2"></i>数据质量报告</div>' +
        '<div class="card-body"><div class="row g-3">' +
        '<div class="col-md-2"><div class="stat-label">总行数</div><div class="fw-600 fs-5">' + (qr.total_rows || 0) + '</div></div>' +
        '<div class="col-md-2"><div class="stat-label">总列数</div><div class="fw-600 fs-5">' + (qr.total_cols || 0) + '</div></div>' +
        '<div class="col-md-2"><div class="stat-label">重复行</div><div class="fw-600 fs-5 ' + (qr.duplicates > 0 ? 'text-warning' : 'text-success') + '">' + (qr.duplicates || 0) + '</div></div>' +
        '<div class="col-md-6"><div class="stat-label">缺失值统计（上传原始列）</div>' +
        missingHtml +
        derivedHtml +
        '</div></div></div></div></div>';
      document.getElementById('qualityRow').innerHTML = html;
    }).catch(function () {});

    // 加载 EDA 图表
    var chartTypes = ['response_distribution', 'gender_response', 'age_distribution', 'premium_distribution'];
    Promise.all(chartTypes.map(function (ct) {
      return dataApi.visualization(ct).then(function (d) { return { type: ct, data: d }; }).catch(function () { return { type: ct, data: null }; });
    })).then(function (results) {
      var html = '<div class="row g-3">';
      var titleMap = {
        response_distribution: '响应分布', gender_response: '性别×响应交叉',
        age_distribution: '年龄分布', premium_distribution: '保费分布'
      };
      for (var i = 0; i < results.length; i++) {
        var r = results[i];
        html += '<div class="col-md-6"><div class="chart-container">' +
          '<div class="chart-title">' + (titleMap[r.type] || r.type) + '</div>';
        if (r.data && r.data.image_base64) {
          html += '<img src="data:image/png;base64,' + r.data.image_base64 + '">';
        } else {
          html += AppUtils.emptyState('图表加载失败');
        }
        html += '</div></div>';
      }
      html += '</div>';
      document.getElementById('edaCharts').innerHTML = html;
    }).finally(function () {
      AppUtils.hideLoading();
    });
  }

  // ========================================================================
  //  7. 模型管理页
  // ========================================================================
  function renderModelPage(el, sub) {
    if (sub === 'train') renderModelTrain(el);
    else if (sub === 'experiments') renderModelExperiments(el);
    else if (sub === 'predict') renderModelPredict(el);
    else if (sub === 'visualization') renderModelVisualization(el);
    else if (sub === 'io') renderModelIO(el);
    else renderModelPredict(el);
  }

  // --- 7.1 模型训练 ---
  function renderModelTrain(el) {
    el.innerHTML =
      '<div class="card">' +
      '  <div class="card-header"><i class="bi bi-cpu me-2"></i>模型训练</div>' +
      '  <div class="card-body">' +
      '    <div class="alert alert-info py-2"><i class="bi bi-info-circle me-1"></i>训练会自动对 Logistic Regression / XGBoost / RandomForest 三算法建模，按 ROC-AUC 自动选优。</div>' +
      '    <div class="row g-3">' +
      '      <div class="col-md-3"><label class="form-label">测试集比例</label><input type="number" class="form-control" id="testSize" value="0.2" step="0.05" min="0.1" max="0.5"></div>' +
      '      <div class="col-md-3"><label class="form-label">随机种子</label><input type="number" class="form-control" id="randomState" value="42"></div>' +
      '      <div class="col-md-6 d-flex align-items-end">' +
      '        <button class="btn btn-primary" onclick="window._handleTrain()"><i class="bi bi-play-circle me-1"></i>开始训练</button>' +
      '      </div>' +
      '    </div>' +
      '    <div id="trainResult" class="mt-3"></div>' +
      '  </div>' +
      '</div>';
  }

  window._handleTrain = function () {
    var testSize = parseFloat(document.getElementById('testSize').value) || 0.2;
    var randomState = parseInt(document.getElementById('randomState').value) || 42;
    AppUtils.showLoading();
    modelApi.train({ test_size: testSize, random_state: randomState }).then(function (data) {
      var html = '<div class="alert alert-success"><i class="bi bi-trophy me-2"></i>训练完成！最优模型：<strong>' + data.best_model + '</strong></div>';
      html += '<div class="table-responsive"><table class="table table-hover"><thead><tr>' +
        '<th>模型</th><th>准确率</th><th>精确率</th><th>召回率</th><th>F1</th><th>ROC-AUC</th><th>状态</th>' +
        '</tr></thead><tbody>';
      for (var name in data.results) {
        var r = data.results[name];
        var isBest = name === data.best_model;
        html += '<tr' + (isBest ? ' class="table-warning"' : '') + '>' +
          '<td class="fw-600">' + name + '</td>' +
          '<td>' + (r.accuracy || 0).toFixed(4) + '</td>' +
          '<td>' + (r.precision || 0).toFixed(4) + '</td>' +
          '<td>' + (r.recall || 0).toFixed(4) + '</td>' +
          '<td>' + (r.f1_score || 0).toFixed(4) + '</td>' +
          '<td>' + (r.roc_auc || 0).toFixed(4) + '</td>' +
          '<td>' + (isBest ? '<span class="status-tag status-best">最优</span>' : '-') + '</td>' +
          '</tr>';
      }
      html += '</tbody></table></div>';
      document.getElementById('trainResult').innerHTML = html;
      AppUtils.showToast('训练成功', 'success');
    }).catch(function () {}).finally(function () {
      AppUtils.hideLoading();
    });
  };

  // --- 7.2 实验记录 ---
  var experimentFilters = { page: 1, per_page: 20, model_name: '' };

  function renderModelExperiments(el) {
    experimentFilters = { page: 1, per_page: 20, model_name: '' };
    el.innerHTML =
      '<div class="card">' +
      '  <div class="card-header"><i class="bi bi-list-check me-2"></i>实验记录' +
      '    <div class="float-end"><input type="text" class="form-control form-control-sm d-inline-block" style="width:150px;" id="expFilter" placeholder="模型名过滤" onkeydown="if(event.key===\'Enter\')window._searchExperiments()">' +
      '    <button class="btn btn-sm btn-primary ms-1" onclick="window._searchExperiments()"><i class="bi bi-search"></i></button></div>' +
      '  </div>' +
      '  <div class="card-body" id="expTableBody">' + AppUtils.emptyState('加载中...') + '</div>' +
      '</div>';
    loadExperiments();
  }

  window._searchExperiments = function () {
    experimentFilters.page = 1;
    experimentFilters.model_name = document.getElementById('expFilter').value.trim();
    loadExperiments();
  };

  window._goExpPage = function (page) {
    experimentFilters.page = page;
    loadExperiments();
  };

  function loadExperiments() {
    var body = document.getElementById('expTableBody');
    AppUtils.showLoading();
    modelApi.experiments(experimentFilters).then(function (data) {
      var items = data.items || [];
      if (items.length === 0) { body.innerHTML = AppUtils.emptyState('暂无实验记录'); return; }
      var html = '<div class="table-responsive"><table class="table table-hover">' +
        '<thead><tr><th>ID</th><th>模型</th><th>准确率</th><th>精确率</th><th>召回率</th><th>F1</th><th>ROC-AUC</th><th>最优</th><th>时间</th></tr></thead><tbody>';
      for (var i = 0; i < items.length; i++) {
        var e = items[i];
        html += '<tr>' +
          '<td>' + e.id + '</td>' +
          '<td>' + AppUtils.escapeHtml(e.model_name) + '</td>' +
          '<td>' + (e.accuracy || 0).toFixed(4) + '</td>' +
          '<td>' + (e.precision || 0).toFixed(4) + '</td>' +
          '<td>' + (e.recall || 0).toFixed(4) + '</td>' +
          '<td>' + (e.f1_score || 0).toFixed(4) + '</td>' +
          '<td>' + (e.roc_auc || 0).toFixed(4) + '</td>' +
          '<td>' + (e.is_best ? '<span class="status-tag status-best">最优</span>' : '-') + '</td>' +
          '<td style="font-size:12px;">' + AppUtils.formatTime(e.created_at) + '</td>' +
          '</tr>';
      }
      html += '</tbody></table></div>';
      html += '<div class="d-flex justify-content-between align-items-center mt-3"><span class="text-muted" style="font-size:13px;">共 ' + data.total + ' 条</span>' + AppUtils.renderPagination(data, 'window._goExpPage') + '</div>';
      body.innerHTML = html;
    }).catch(function () {}).finally(function () {
      AppUtils.hideLoading();
    });
  }

  // --- 7.3 模型预测 ---
  function renderModelPredict(el) {
    el.innerHTML =
      '<div class="card mb-3">' +
      '  <div class="card-header"><i class="bi bi-trophy me-2"></i>当前最优模型</div>' +
      '  <div class="card-body" id="bestModelInfo">' + AppUtils.emptyState('加载中...') + '</div>' +
      '</div>' +
      '<div class="card">' +
      '  <div class="card-header"><i class="bi bi-lightning-charge me-2"></i>全量预测</div>' +
      '  <div class="card-body">' +
      '    <div class="alert alert-info py-2"><i class="bi bi-info-circle me-1"></i>加载最佳模型，对全部客户预测投保概率并回写到数据库。</div>' +
      '    <button class="btn btn-primary" onclick="window._handlePredict()"><i class="bi bi-play-circle me-1"></i>执行预测</button>' +
      '    <div id="predictResult" class="mt-3"></div>' +
      '  </div>' +
      '</div>';

    // 加载最优模型信息
    modelApi.best().then(function (data) {
      document.getElementById('bestModelInfo').innerHTML =
        '<div class="row g-3">' +
        '<div class="col-md-4"><div class="stat-label">模型名称</div><div class="fw-600 fs-5 text-primary">' + AppUtils.escapeHtml(data.model_name) + '</div></div>' +
        '<div class="col-md-4"><div class="stat-label">ROC-AUC</div><div class="fw-600 fs-5 text-success">' + (data.roc_auc || 0).toFixed(4) + '</div></div>' +
        '<div class="col-md-4"><div class="stat-label">实验ID</div><div class="fw-600 fs-5">' + (data.experiment_id || '-') + '</div></div>' +
        '</div>';
    }).catch(function () {
      document.getElementById('bestModelInfo').innerHTML = '<div class="alert alert-warning py-2"><i class="bi bi-exclamation-triangle me-1"></i>暂无最佳模型，请先训练。</div>';
    });
  }

  window._handlePredict = function () {
    AppUtils.showLoading();
    modelApi.predict().then(function (data) {
      document.getElementById('predictResult').innerHTML =
        '<div class="alert alert-success"><i class="bi bi-check-circle me-2"></i>预测完成！使用模型 <strong>' + data.model_name + '</strong>，共预测 ' + data.predicted_count + ' 条客户数据。</div>';
      AppUtils.showToast('预测成功', 'success');
    }).catch(function () {}).finally(function () {
      AppUtils.hideLoading();
    });
  };

  // --- 7.4 评估图表 ---
  function renderModelVisualization(el) {
    el.innerHTML =
      '<div class="card">' +
      '  <div class="card-header"><i class="bi bi-graph-up me-2"></i>模型评估可视化</div>' +
      '  <div class="card-body">' +
      '    <div class="mb-3">' +
      '      <label class="form-label">图表类型</label>' +
      '      <select class="form-select d-inline-block" style="width:auto;" id="chartType" onchange="window._loadModelChart()">' +
      '        <option value="roc_curve">ROC 曲线</option>' +
      '        <option value="metrics_comparison">指标对比</option>' +
      '        <option value="confusion_matrix">混淆矩阵</option>' +
      '        <option value="feature_importance">特征重要性</option>' +
      '      </select>' +
      '      <select class="form-select d-inline-block ms-2" style="width:auto;display:none;" id="modelSelect" onchange="window._loadModelChart()">' +
      '        <option value="logistic_regression">Logistic Regression</option>' +
      '        <option value="xgboost">XGBoost</option>' +
      '        <option value="random_forest">Random Forest</option>' +
      '      </select>' +
      '    </div>' +
      '    <div id="chartDisplay">' + AppUtils.emptyState('请选择图表类型') + '</div>' +
      '  </div>' +
      '</div>';
    window._loadModelChart();
  }

  window._loadModelChart = function () {
    var chartType = document.getElementById('chartType').value;
    var modelSelect = document.getElementById('modelSelect');
    var needsModel = chartType === 'confusion_matrix' || chartType === 'feature_importance';
    modelSelect.style.display = needsModel ? 'inline-block' : 'none';
    var modelName = needsModel ? modelSelect.value : null;

    var display = document.getElementById('chartDisplay');
    display.innerHTML = '<div class="text-center py-4"><div class="loading-spinner mx-auto"></div></div>';

    modelApi.visualization(chartType, modelName).then(function (data) {
      if (data && data.image_base64) {
        display.innerHTML = '<div class="chart-container"><img src="data:image/png;base64,' + data.image_base64 + '"></div>';
      } else {
        display.innerHTML = AppUtils.emptyState('图表加载失败');
      }
    }).catch(function () {
      display.innerHTML = AppUtils.emptyState('图表加载失败');
    });
  };

  // --- 7.5 模型导入导出 ---
  function renderModelIO(el) {
    el.innerHTML =
      '<div class="row g-3">' +
      '  <div class="col-md-6">' +
      '    <div class="card">' +
      '      <div class="card-header"><i class="bi bi-box-arrow-down me-2"></i>导出模型</div>' +
      '      <div class="card-body">' +
      '        <label class="form-label">选择模型</label>' +
      '        <select class="form-select mb-3" id="exportModel">' +
      '          <option value="logistic_regression">Logistic Regression</option>' +
      '          <option value="xgboost">XGBoost</option>' +
      '          <option value="random_forest">Random Forest</option>' +
      '        </select>' +
      '        <button class="btn btn-primary" onclick="window._handleExport()"><i class="bi bi-download me-1"></i>导出 .joblib</button>' +
      '      </div>' +
      '    </div>' +
      '  </div>' +
      '  <div class="col-md-6">' +
      '    <div class="card">' +
      '      <div class="card-header"><i class="bi bi-box-arrow-up me-2"></i>导入模型</div>' +
      '      <div class="card-body">' +
      '        <div class="upload-zone" onclick="document.getElementById(\'modelFileInput\').click()">' +
      '          <div class="upload-icon"><i class="bi bi-file-earmark-binary"></i></div>' +
      '          <div class="upload-text">点击选择 .joblib 文件</div>' +
      '          <div class="upload-hint">仅支持 .joblib 格式</div>' +
      '        </div>' +
      '        <input type="file" id="modelFileInput" accept=".joblib" style="display:none;" onchange="window._handleModelFileSelect(this)">' +
      '        <div id="modelFileInfo" class="mt-2" style="display:none;">' +
      '          <span id="modelFileName" class="text-secondary"></span>' +
      '          <button class="btn btn-primary btn-sm ms-2" onclick="window._handleImport()"><i class="bi bi-upload me-1"></i>导入</button>' +
      '        </div>' +
      '        <div id="importResult" class="mt-2"></div>' +
      '      </div>' +
      '    </div>' +
      '  </div>' +
      '</div>';
  }

  var selectedModelFile = null;

  window._handleModelFileSelect = function (input) {
    var file = input.files[0];
    var err = AppUtils.validateModelFile(file);
    if (err) {
      AppUtils.showToast(err, 'danger');
      selectedModelFile = null;
      document.getElementById('modelFileInfo').style.display = 'none';
      return;
    }
    selectedModelFile = file;
    document.getElementById('modelFileName').textContent = file.name;
    document.getElementById('modelFileInfo').style.display = 'block';
  };

  window._handleImport = function () {
    if (!selectedModelFile) return;
    AppUtils.showLoading();
    modelApi.importModel(selectedModelFile).then(function (data) {
      document.getElementById('importResult').innerHTML =
        '<div class="alert alert-success py-2"><i class="bi bi-check-circle me-1"></i>导入成功！模型名：' + AppUtils.escapeHtml(data.model_name) + '</div>';
      AppUtils.showToast('导入成功', 'success');
    }).catch(function () {}).finally(function () {
      AppUtils.hideLoading();
    });
  };

  window._handleExport = function () {
    var modelName = document.getElementById('exportModel').value;
    AppUtils.showLoading();
    modelApi.exportModel(modelName).then(function () {
      AppUtils.showToast('导出成功', 'success');
    }).catch(function () {}).finally(function () {
      AppUtils.hideLoading();
    });
  };

  // ========================================================================
  //  8. 邮件营销页
  // ========================================================================
  function renderEmailPage(el, sub) {
    if (sub === 'targets') renderEmailTargets(el);
    else if (sub === 'records') renderEmailRecords(el);
    else if (sub === 'prompt') renderEmailPrompt(el);
    else renderEmailTargets(el);
  }

  // --- 8.1 高潜客户 ---
  var targetFilters = { percentile: 0.9, page: 1, per_page: 20 };

  function renderEmailTargets(el) {
    targetFilters = { percentile: 0.9, page: 1, per_page: 20 };
    el.innerHTML =
      '<div class="card mb-3">' +
      '  <div class="card-header"><i class="bi bi-bullseye me-2"></i>高潜客户筛选</div>' +
      '  <div class="card-body">' +
      '    <div class="row g-3 align-items-end">' +
      '      <div class="col-md-3"><label class="form-label">分位阈值</label>' +
      '        <select class="form-select" id="percentileSelect">' +
      '          <option value="0.9">Top 10%</option>' +
      '          <option value="0.95">Top 5%</option>' +
      '          <option value="0.99">Top 1%</option>' +
      '          <option value="0.8">Top 20%</option>' +
      '        </select></div>' +
      '      <div class="col-md-3">' +
      '        <button class="btn btn-primary" onclick="window._searchTargets()"><i class="bi bi-search me-1"></i>筛选</button>' +
      '        <button class="btn btn-success ms-1" onclick="window._generateEmails()"><i class="bi bi-magic me-1"></i>生成邮件</button>' +
      '      </div>' +
      '      <div class="col-md-6 text-end"><span class="text-muted" style="font-size:13px;" id="targetThreshold"></span></div>' +
      '    </div>' +
      '  </div>' +
      '</div>' +
      '<div class="card">' +
      '  <div class="card-header"><i class="bi bi-people me-2"></i>高潜客户列表</div>' +
      '  <div class="card-body" id="targetTableBody">' + AppUtils.emptyState('点击筛选加载高潜客户') + '</div>' +
      '</div>';
    window._searchTargets();
  }

  window._searchTargets = function () {
    targetFilters.percentile = parseFloat(document.getElementById('percentileSelect').value);
    targetFilters.page = 1;
    loadTargets();
  };

  window._goTargetPage = function (page) {
    targetFilters.page = page;
    loadTargets();
  };

  function loadTargets() {
    var body = document.getElementById('targetTableBody');
    AppUtils.showLoading();
    emailApi.targets(targetFilters).then(function (data) {
      var customers = data.customers || [];
      // 显示阈值
      var thresholdEl = document.getElementById('targetThreshold');
      if (thresholdEl) thresholdEl.textContent = '概率阈值：' + (data.threshold || 0).toFixed(4) + '，共 ' + data.total + ' 位高潜客户';

      if (customers.length === 0) {
        body.innerHTML = AppUtils.emptyState('暂无高潜客户，请先执行预测');
        return;
      }
      var html = '<div class="table-responsive"><table class="table table-hover">' +
        '<thead><tr><th><input type="checkbox" id="checkAllTargets" onchange="window._toggleAllTargets(this)"></th><th>ID</th><th>性别</th><th>年龄</th><th>年保费</th><th>预测概率</th></tr></thead><tbody>';
      for (var i = 0; i < customers.length; i++) {
        var c = customers[i];
        var prob = c.predicted_prob != null ? (c.predicted_prob * 100).toFixed(1) + '%' : '-';
        html += '<tr>' +
          '<td><input type="checkbox" class="target-check" value="' + c.id + '"></td>' +
          '<td>' + c.id + '</td>' +
          '<td>' + (c.gender === 'Male' ? '男' : '女') + '</td>' +
          '<td>' + c.age + '</td>' +
          '<td>' + (c.annual_premium || '-') + '</td>' +
          '<td><span class="text-success fw-600">' + prob + '</span></td>' +
          '</tr>';
      }
      html += '</tbody></table></div>';
      // 分页信息
      var pageData = { total: data.total, page: targetFilters.page, per_page: targetFilters.per_page, pages: data.pages };
      html += '<div class="d-flex justify-content-between align-items-center mt-3"><span class="text-muted" style="font-size:13px;">共 ' + data.total + ' 条</span>' + AppUtils.renderPagination(pageData, 'window._goTargetPage') + '</div>';
      body.innerHTML = html;
    }).catch(function () {}).finally(function () {
      AppUtils.hideLoading();
    });
  }

  window._toggleAllTargets = function (checkAll) {
    var checks = document.querySelectorAll('.target-check');
    for (var i = 0; i < checks.length; i++) checks[i].checked = checkAll.checked;
  };

  window._generateEmails = function () {
    var selected = [];
    var checks = document.querySelectorAll('.target-check:checked');
    for (var i = 0; i < checks.length; i++) selected.push(parseInt(checks[i].value));

    var body = {};
    if (selected.length > 0) {
      body.customer_ids = selected;
    } else {
      body.limit = 5;
    }

    AppUtils.showLoading();
    emailApi.generate(body).then(function (data) {
      var html = '<div class="alert alert-success"><i class="bi bi-check-circle me-2"></i>邮件生成完成！成功 ' + data.generated_count + ' 封，失败 ' + data.failed_count + ' 封。</div>';
      if (data.records && data.records.length > 0) {
        html += '<div class="table-responsive mt-2"><table class="table table-sm"><thead><tr><th>客户ID</th><th>状态</th><th>主题</th></tr></thead><tbody>';
        for (var i = 0; i < data.records.length; i++) {
          var r = data.records[i];
          html += '<tr><td>' + r.customer_id + '</td><td>' + AppUtils.statusTag(r.status) + '</td><td>' + AppUtils.escapeHtml(r.subject || '-') + '</td></tr>';
        }
        html += '</tbody></table></div>';
      }
      AppUtils.showModal({
        title: '邮件生成结果',
        bodyHtml: html,
        footerHtml: '<button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>'
      });
    }).catch(function () {}).finally(function () {
      AppUtils.hideLoading();
    });
  };

  // --- 8.2 邮件记录管理 ---
  var recordFilters = { page: 1, per_page: 20, status: '' };

  function renderEmailRecords(el) {
    recordFilters = { page: 1, per_page: 20, status: '' };
    el.innerHTML =
      '<div class="card">' +
      '  <div class="card-header"><i class="bi bi-envelope me-2"></i>邮件记录管理' +
      '    <div class="float-end d-flex gap-2">' +
      '      <select class="form-select form-select-sm" style="width:120px;" id="statusFilter" onchange="window._filterRecords()">' +
      '        <option value="">全部状态</option>' +
      '        <option value="generated">已生成</option>' +
      '        <option value="failed">生成失败</option>' +
      '        <option value="sent">已发送</option>' +
      '      </select>' +
      '      <button class="btn btn-sm btn-outline-danger" onclick="window._batchDeleteRecords()"><i class="bi bi-trash"></i>批量删除</button>' +
      '    </div>' +
      '  </div>' +
      '  <div class="card-body" id="recordTableBody">' + AppUtils.emptyState('加载中...') + '</div>' +
      '</div>';
    loadRecords();
  }

  window._filterRecords = function () {
    recordFilters.status = document.getElementById('statusFilter').value;
    recordFilters.page = 1;
    loadRecords();
  };

  window._goRecordPage = function (page) {
    recordFilters.page = page;
    loadRecords();
  };

  function loadRecords() {
    var body = document.getElementById('recordTableBody');
    AppUtils.showLoading();
    emailApi.records(recordFilters).then(function (data) {
      var items = data.items || [];
      if (items.length === 0) { body.innerHTML = AppUtils.emptyState('暂无邮件记录'); return; }
      var html = '<div class="table-responsive"><table class="table table-hover">' +
        '<thead><tr><th><input type="checkbox" id="checkAllRecords" onchange="window._toggleAllRecords(this)"></th><th>ID</th><th>客户ID</th><th>主题</th><th>状态</th>';
      if (currentUser.role === 'admin') html += '<th>创建者</th>';
      html += '<th>创建时间</th><th>操作</th></tr></thead><tbody>';
      for (var i = 0; i < items.length; i++) {
        var r = items[i];
        html += '<tr>' +
          '<td><input type="checkbox" class="record-check" value="' + r.id + '"></td>' +
          '<td>' + r.id + '</td>' +
          '<td>' + (r.customer_id || '-') + '</td>' +
          '<td class="text-truncate" style="max-width:250px;">' + AppUtils.escapeHtml(r.subject || '-') + '</td>' +
          '<td>' + AppUtils.statusTag(r.status) + '</td>';
        if (currentUser.role === 'admin') html += '<td>' + AppUtils.escapeHtml(r.created_by_username || '-') + '</td>';
        html += '<td style="font-size:12px;">' + AppUtils.formatTime(r.created_at) + '</td>' +
          '<td><button class="btn btn-sm btn-outline-primary" onclick="window._viewRecord(' + r.id + ')"><i class="bi bi-eye"></i></button>' +
          ' <button class="btn btn-sm btn-outline-success" onclick="window._editRecord(' + r.id + ')"><i class="bi bi-pencil"></i></button>' +
          ' <button class="btn btn-sm btn-outline-danger" onclick="window._deleteRecord(' + r.id + ')"><i class="bi bi-trash"></i></button></td>' +
          '</tr>';
      }
      html += '</tbody></table></div>';
      html += '<div class="d-flex justify-content-between align-items-center mt-3"><span class="text-muted" style="font-size:13px;">共 ' + data.total + ' 条</span>' + AppUtils.renderPagination(data, 'window._goRecordPage') + '</div>';
      body.innerHTML = html;
    }).catch(function () {}).finally(function () {
      AppUtils.hideLoading();
    });
  }

  window._toggleAllRecords = function (checkAll) {
    var checks = document.querySelectorAll('.record-check');
    for (var i = 0; i < checks.length; i++) checks[i].checked = checkAll.checked;
  };

  window._viewRecord = function (id) {
    AppUtils.showLoading();
    emailApi.recordDetail(id).then(function (r) {
      var html = '<div class="mb-3"><label class="form-label">邮件主题</label><div class="fw-600">' + AppUtils.escapeHtml(r.subject || '-') + '</div></div>' +
        '<div class="mb-3"><label class="form-label">状态</label>' + AppUtils.statusTag(r.status) + '</div>' +
        '<div class="mb-3"><label class="form-label">客户ID</label><div>' + (r.customer_id || '-') + '</div></div>' +
        '<div><label class="form-label">邮件正文</label><div class="email-content-preview">' + AppUtils.escapeHtml(r.content || '(空)') + '</div></div>';
      AppUtils.showModal({
        title: '邮件详情 #' + id,
        bodyHtml: html,
        size: 'lg',
        footerHtml: '<button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>'
      });
    }).catch(function () {}).finally(function () {
      AppUtils.hideLoading();
    });
  };

  window._editRecord = function (id) {
    AppUtils.showLoading();
    emailApi.recordDetail(id).then(function (r) {
      var html =
        '<div class="mb-3"><label class="form-label">邮件主题</label>' +
        '<input type="text" class="form-control" id="editSubject" value="' + AppUtils.escapeHtml(r.subject || '') + '"></div>' +
        '<div class="mb-3"><label class="form-label">邮件正文</label>' +
        '<textarea class="form-control" id="editContent" rows="10">' + AppUtils.escapeHtml(r.content || '') + '</textarea></div>' +
        '<div class="mb-3"><label class="form-label">状态</label>' +
        '<select class="form-select" id="editStatus">' +
        '<option value="generated"' + (r.status === 'generated' ? ' selected' : '') + '>已生成</option>' +
        '<option value="sent"' + (r.status === 'sent' ? ' selected' : '') + '>已发送</option>' +
        '<option value="failed"' + (r.status === 'failed' ? ' selected' : '') + '>生成失败</option>' +
        '</select></div>';
      AppUtils.showModal({
        title: '编辑邮件 #' + id,
        bodyHtml: html,
        size: 'lg',
        footerHtml: '<button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>' +
          '<button type="button" class="btn btn-primary" onclick="window._saveRecord(' + id + ')">保存</button>'
      });
    }).catch(function () {}).finally(function () {
      AppUtils.hideLoading();
    });
  };

  window._saveRecord = function (id) {
    var subject = document.getElementById('editSubject').value.trim();
    var content = document.getElementById('editContent').value.trim();
    var status = document.getElementById('editStatus').value;
    AppUtils.showLoading();

    // 先更新主题/正文
    emailApi.updateRecord(id, { email_subject: subject, email_content: content }).then(function () {
      // 再更新状态
      return emailApi.patchStatus(id, status);
    }).then(function () {
      AppUtils.hideModal();
      AppUtils.showToast('保存成功', 'success');
      loadRecords();
    }).catch(function () {}).finally(function () {
      AppUtils.hideLoading();
    });
  };

  window._deleteRecord = function (id) {
    AppUtils.showModal({
      title: '确认删除',
      bodyHtml: '<p>确定要删除邮件记录 #' + id + ' 吗？此操作不可撤销。</p>',
      footerHtml: '<button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>' +
        '<button type="button" class="btn btn-danger" onclick="window._confirmDeleteRecord(' + id + ')">删除</button>'
    });
  };

  window._confirmDeleteRecord = function (id) {
    AppUtils.showLoading();
    emailApi.deleteRecord(id).then(function () {
      AppUtils.hideModal();
      AppUtils.showToast('删除成功', 'success');
      loadRecords();
    }).catch(function () {}).finally(function () {
      AppUtils.hideLoading();
    });
  };

  window._batchDeleteRecords = function () {
    var selected = [];
    var checks = document.querySelectorAll('.record-check:checked');
    for (var i = 0; i < checks.length; i++) selected.push(parseInt(checks[i].value));
    if (selected.length === 0) {
      AppUtils.showToast('请先勾选要删除的记录', 'warning');
      return;
    }
    AppUtils.showModal({
      title: '批量删除',
      bodyHtml: '<p>确定要删除选中的 ' + selected.length + ' 条邮件记录吗？</p>',
      footerHtml: '<button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>' +
        '<button type="button" class="btn btn-danger" onclick="window._confirmBatchDelete()">删除</button>'
    });
    window._batchDeleteIds = selected;
  };

  window._confirmBatchDelete = function () {
    AppUtils.showLoading();
    emailApi.batchDeleteRecords(window._batchDeleteIds).then(function (data) {
      AppUtils.hideModal();
      AppUtils.showToast('删除成功，共删除 ' + data.deleted_count + ' 条', 'success');
      loadRecords();
    }).catch(function () {}).finally(function () {
      AppUtils.hideLoading();
    });
  };

  // --- 8.3 Prompt 模板 ---
  function renderEmailPrompt(el) {
    el.innerHTML =
      '<div class="card">' +
      '  <div class="card-header"><i class="bi bi-card-text me-2"></i>Prompt 模板管理</div>' +
      '  <div class="card-body" id="promptBody">' + AppUtils.emptyState('加载中...') + '</div>' +
      '</div>';

    emailApi.getPrompt().then(function (data) {
      document.getElementById('promptBody').innerHTML =
        '<div class="alert alert-info py-2"><i class="bi bi-info-circle me-1"></i>模板中可使用占位符：{gender}、{age}、{driving_license}、{previously_insured}、{vehicle_age}、{vehicle_damage}、{annual_premium} 等。</div>' +
        '<div class="mb-3"><label class="form-label">模板名称</label><div class="fw-600">' + AppUtils.escapeHtml(data.name || '-') + '</div></div>' +
        '<div class="mb-3"><label class="form-label">模板内容</label>' +
        '<textarea class="form-control" id="promptContent" rows="15" style="font-family:monospace;font-size:13px;">' + AppUtils.escapeHtml(data.content || '') + '</textarea></div>' +
        '<button class="btn btn-primary" onclick="window._savePrompt()"><i class="bi bi-save me-1"></i>保存模板</button>';
    }).catch(function () {
      document.getElementById('promptBody').innerHTML = '<div class="alert alert-danger">加载 Prompt 模板失败</div>';
    });
  }

  window._savePrompt = function () {
    var content = document.getElementById('promptContent').value.trim();
    if (!content) {
      AppUtils.showToast('模板内容不能为空', 'warning');
      return;
    }
    AppUtils.showLoading();
    emailApi.updatePrompt(content).then(function () {
      AppUtils.showToast('保存成功', 'success');
    }).catch(function () {}).finally(function () {
      AppUtils.hideLoading();
    });
  };

  // ========================================================================
  //  9. 操作日志页（admin only）
  // ========================================================================
  var logFilters = { page: 1, per_page: 20, user_id: '', action: '' };

  function renderLogsPage(el) {
    logFilters = { page: 1, per_page: 20, user_id: '', action: '' };
    el.innerHTML =
      '<div class="card mb-3">' +
      '  <div class="card-header"><i class="bi bi-funnel me-2"></i>筛选条件</div>' +
      '  <div class="card-body">' +
      '    <div class="row g-3">' +
      '      <div class="col-md-3"><label class="form-label">用户ID</label><input type="number" class="form-control" id="logFilterUser"></div>' +
      '      <div class="col-md-3"><label class="form-label">操作类型</label>' +
      '        <select class="form-select" id="logFilterAction">' +
      '          <option value="">全部</option>' +
      '          <option value="model_training">模型训练</option>' +
      '          <option value="prediction">概率预测</option>' +
      '          <option value="model_import">模型导入</option>' +
      '          <option value="email_generation">邮件生成</option>' +
      '          <option value="email_update">邮件修改</option>' +
      '          <option value="email_mark">邮件标记</option>' +
      '          <option value="email_delete">邮件删除</option>' +
      '        </select></div>' +
      '      <div class="col-md-3 d-flex align-items-end">' +
      '        <button class="btn btn-primary btn-sm" onclick="window._searchLogs()"><i class="bi bi-search me-1"></i>查询</button>' +
      '        <button class="btn btn-outline-secondary btn-sm ms-2" onclick="window._resetLogFilter()"><i class="bi bi-arrow-counterclockwise me-1"></i>重置</button>' +
      '      </div>' +
      '    </div>' +
      '  </div>' +
      '</div>' +
      '<div class="card">' +
      '  <div class="card-header"><i class="bi bi-journal-text me-2"></i>操作日志</div>' +
      '  <div class="card-body" id="logTableBody">' + AppUtils.emptyState('点击查询加载日志') + '</div>' +
      '</div>';
    window._searchLogs();
  }

  window._searchLogs = function () {
    logFilters.page = 1;
    logFilters.user_id = document.getElementById('logFilterUser').value;
    logFilters.action = document.getElementById('logFilterAction').value;
    loadLogs();
  };

  window._resetLogFilter = function () {
    document.getElementById('logFilterUser').value = '';
    document.getElementById('logFilterAction').value = '';
    window._searchLogs();
  };

  window._goLogPage = function (page) {
    logFilters.page = page;
    loadLogs();
  };

  function loadLogs() {
    var body = document.getElementById('logTableBody');
    AppUtils.showLoading();
    logApi.logs(logFilters).then(function (data) {
      var items = data.items || [];
      if (items.length === 0) { body.innerHTML = AppUtils.emptyState('暂无操作日志'); return; }
      var html = '<div class="table-responsive"><table class="table table-hover">' +
        '<thead><tr><th>ID</th><th>用户ID</th><th>操作类型</th><th>详情</th><th>时间</th></tr></thead><tbody>';
      for (var i = 0; i < items.length; i++) {
        var log = items[i];
        var detailStr = '';
        if (log.details) {
          try { detailStr = JSON.stringify(JSON.parse(log.details), null, 2); }
          catch (e) { detailStr = log.details; }
        }
        html += '<tr>' +
          '<td>' + log.id + '</td>' +
          '<td>' + (log.user_id || '-') + '</td>' +
          '<td>' + AppUtils.actionTag(log.action) + '</td>' +
          '<td><div class="json-detail">' + AppUtils.escapeHtml(detailStr || '-') + '</div></td>' +
          '<td style="font-size:12px;white-space:nowrap;">' + AppUtils.formatTime(log.created_at) + '</td>' +
          '</tr>';
      }
      html += '</tbody></table></div>';
      html += '<div class="d-flex justify-content-between align-items-center mt-3"><span class="text-muted" style="font-size:13px;">共 ' + data.total + ' 条</span>' + AppUtils.renderPagination(data, 'window._goLogPage') + '</div>';
      body.innerHTML = html;
    }).catch(function () {}).finally(function () {
      AppUtils.hideLoading();
    });
  }

  // ========================================================================
  //  10. 初始化
  // ========================================================================
  function init() {
    // 读取 localStorage 中的 token 和用户信息
    var token = localStorage.getItem('access_token');
    var userInfoStr = localStorage.getItem('user_info');

    if (token && userInfoStr) {
      try { currentUser = JSON.parse(userInfoStr); } catch (e) { currentUser = null; }
    }

    // 如果有 token，验证是否仍然有效
    if (token) {
      authApi.me().then(function (data) {
        // /auth/me 返回完整 token 响应 {access_token, user}，需提取 user
        currentUser = data.user || data;
        // 刷新 token（后端 me 接口会重新签发 token）
        if (data.access_token) {
          localStorage.setItem('access_token', data.access_token);
        }
        localStorage.setItem('user_info', JSON.stringify(currentUser));
      }).catch(function () {
        // token 失效
        localStorage.clear();
        currentUser = null;
      }).finally(function () {
        // 监听 hash 变化
        window.addEventListener('hashchange', router);
        router();
      });
    } else {
      // 监听 hash 变化
      window.addEventListener('hashchange', router);
      router();
    }
  }

  // DOM 就绪后启动
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
