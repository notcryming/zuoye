/**
 * api.js —— 统一接口请求封装（Flask 后端 SPA 前端用）
 *
 * 【职责】
 * 1. 封装核心 request(method, url, data, isForm)：自动携带 token、统一解析 {code,message,data} 信封
 * 2. 按业务模块封装接口函数：authApi / dataApi / modelApi / emailApi / logApi
 * 3. 统一错误处理：code=1002 清存储跳登录、其他非 0 弹窗提示、网络异常兜底弹窗
 *
 * 【约束】
 * - 基础路径 BASE_URL = /api/v1（与后端蓝图 url_prefix 对齐）
 * - JSON 请求体用 JSON.stringify + Content-Type: application/json
 * - FormData 上传不手动设 Content-Type（浏览器自动加 boundary）
 * - 所有函数返回 Promise，成功 resolve 业务 data，失败 reject Error
 */
(function () {
  'use strict';

  // ===== 全局配置 =====
  // 后端各业务蓝图统一挂载在 /api/v1 前缀下
  var BASE_URL = '/api/v1';

  // ===== 内部工具函数 =====

  /**
   * 弹窗提示（依赖全局 window.AppUtils.showToast）
   * 若 AppUtils 未加载则降级为 console.warn，不阻断流程
   */
  function _toast(msg, type) {
    if (window.AppUtils && typeof window.AppUtils.showToast === 'function') {
      window.AppUtils.showToast(msg, type || 'danger');
    } else {
      console.warn('[api]', msg);
    }
  }

  /**
   * 把 params 对象拼成 query string（自动跳过 null/undefined/空串）
   * @returns 形如 "?page=1&per_page=20"，无参数返回 ""
   */
  function _buildQuery(params) {
    if (!params) return '';
    var parts = [];
    for (var k in params) {
      if (params.hasOwnProperty(k) && params[k] != null && params[k] !== '') {
        parts.push(encodeURIComponent(k) + '=' + encodeURIComponent(params[k]));
      }
    }
    return parts.length ? '?' + parts.join('&') : '';
  }

  // ===== 核心请求函数 =====

  /**
   * 统一请求入口
   * @param {string} method  GET/POST/PUT/PATCH/DELETE
   * @param {string} url     相对 BASE_URL 的路径，如 /auth/login
   * @param {object|FormData} data  请求体（GET 时忽略）
   * @param {boolean} isForm 是否为 FormData 上传
   * @returns {Promise} 成功 resolve data，失败 reject Error
   */
  function request(method, url, data, isForm) {
    // 1. 组装请求头：自动携带 Authorization: Bearer <token>
    var token = localStorage.getItem('access_token') || '';
    var headers = { 'Authorization': 'Bearer ' + token };
    var options = { method: method, headers: headers };

    // 2. 组装请求体：POST/PUT/PATCH/DELETE 才带 body
    var hasBody = ['POST', 'PUT', 'PATCH', 'DELETE'].indexOf(method) !== -1;
    if (hasBody) {
      if (isForm) {
        // FormData 上传：直接放 body，切勿手动设 Content-Type
        // （浏览器会自动附带 boundary，手动设反而会破坏分界）
        options.body = data;
      } else {
        // JSON 请求体：序列化 + 声明 Content-Type
        headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(data == null ? {} : data);
      }
    }

    // 3. 发起请求并统一处理响应信封
    return fetch(BASE_URL + url, options)
      .then(function (resp) {
        // 解析后端统一信封 {code, message, data}
        return resp.json().then(function (body) {
          // code=1002：未授权 / token 失效 → 清空本地存储 + 跳登录页
          if (body.code === 1002) {
            localStorage.clear();
            location.hash = '#login';
            var e1 = new Error(body.message || '未授权，请重新登录');
            e1._handled = true; // 标记已处理，避免 catch 重复弹窗
            throw e1;
          }
          // 非 0 业务码：弹窗提示后抛错
          if (body.code !== 0) {
            _toast(body.message || '请求失败');
            var e2 = new Error(body.message || '请求失败');
            e2._handled = true;
            throw e2;
          }
          // 成功：返回业务数据 data
          return body.data;
        });
      })
      .catch(function (err) {
        // 未标记的异常视为网络/解析错误，兜底弹窗
        if (!err || !err._handled) {
          _toast('网络异常，请稍后重试');
        }
        throw err;
      });
  }

  // ===== 认证模块 authApi（/auth） =====
  var authApi = {
    // 登录：用户名 + 密码 → 返回 token + 用户信息
    login: function (username, password) {
      return request('POST', '/auth/login', { username: username, password: password });
    },
    // 注册：用户名 + 密码 → 注册成功直接返回 token
    register: function (username, password) {
      return request('POST', '/auth/register', { username: username, password: password });
    },
    // 获取当前登录用户信息
    me: function () {
      return request('GET', '/auth/me');
    },
    // 登出
    logout: function () {
      return request('POST', '/auth/logout');
    }
  };

  // ===== 数据模块 dataApi（/data） =====
  var dataApi = {
    // 上传 Excel：FormData 形式
    upload: function (file) {
      var fd = new FormData();
      fd.append('file', file);
      return request('POST', '/data/upload', fd, true);
    },
    // 客户列表分页（params: page/per_page/gender/age_min/age_max/...）
    customers: function (params) {
      return request('GET', '/data/customers' + _buildQuery(params));
    },
    // 数据统计
    statistics: function () {
      return request('GET', '/data/statistics');
    },
    // 数据质量报告
    quality: function () {
      return request('GET', '/data/quality');
    },
    // EDA 可视化（chartType: gender_distribution / response_distribution / age_distribution ...）
    visualization: function (chartType) {
      return request('GET', '/data/visualization/' + encodeURIComponent(chartType));
    }
  };

  // ===== 模型模块 modelApi（/model） =====
  var modelApi = {
    // 训练模型（params: models/test_size/random_state/params）
    train: function (params) {
      return request('POST', '/model/train', params || {});
    },
    // 实验记录分页（params: page/per_page/model_name）
    experiments: function (params) {
      return request('GET', '/model/experiments' + _buildQuery(params));
    },
    // 获取当前最优模型
    best: function () {
      return request('GET', '/model/best');
    },
    // 全量预测（modelName 可选，缺省用最佳模型）
    predict: function (modelName) {
      var body = {};
      if (modelName) body.model_name = modelName;
      return request('POST', '/model/predict', body);
    },
    // 上传 Excel 离线预测（FormData: file + model）
    predictUpload: function (file, modelName) {
      var fd = new FormData();
      fd.append('file', file);
      if (modelName) fd.append('model', modelName);
      return request('POST', '/model/predict_upload', fd, true);
    },
    // 模型评估可视化（chartType: roc_curve/confusion_matrix/feature_importance/metrics_comparison）
    visualization: function (chartType, modelName) {
      var q = modelName ? ('?model=' + encodeURIComponent(modelName)) : '';
      return request('GET', '/model/visualization/' + encodeURIComponent(chartType) + q);
    },
    // 导出 .joblib 模型文件（后端用 header 鉴权，需 fetch 带 token → blob → 触发下载）
    exportModel: function (modelName) {
      var token = localStorage.getItem('access_token') || '';
      var exportUrl = BASE_URL + '/model/export/' + encodeURIComponent(modelName);
      var handled = false; // 标记业务错误是否已弹窗，避免重复提示
      return fetch(exportUrl, {
        method: 'GET',
        headers: { 'Authorization': 'Bearer ' + token }
      })
        .then(function (resp) {
          var ct = resp.headers.get('content-type') || '';
          // 后端报业务错误时返回 JSON 信封，按统一规则处理
          if (ct.indexOf('application/json') !== -1) {
            return resp.json().then(function (body) {
              handled = true;
              if (body.code === 1002) {
                localStorage.clear();
                location.hash = '#login';
              } else {
                _toast(body.message || '导出失败');
              }
              throw new Error(body.message || '导出失败');
            });
          }
          if (!resp.ok) {
            handled = true;
            _toast('导出失败，HTTP ' + resp.status);
            throw new Error('导出失败，HTTP ' + resp.status);
          }
          return resp.blob();
        })
        .then(function (blob) {
          // 转 blob URL，创建临时 <a> 触发下载
          var url = URL.createObjectURL(blob);
          var a = document.createElement('a');
          a.href = url;
          a.download = modelName + '.joblib';
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          return url; // 返回 blob URL
        })
        .catch(function (err) {
          if (!handled) {
            _toast('导出模型失败：' + (err && err.message ? err.message : err));
          }
          throw err;
        });
    },
    // 导入 .joblib 模型文件（FormData）
    importModel: function (file) {
      var fd = new FormData();
      fd.append('file', file);
      return request('POST', '/model/import', fd, true);
    }
  };

  // ===== 邮件模块 emailApi（/email） =====
  var emailApi = {
    // 高潜客户筛选（params: percentile/page/per_page）
    targets: function (params) {
      return request('GET', '/email/targets' + _buildQuery(params));
    },
    // 批量生成营销邮件（body: customer_ids 或 limit）
    generate: function (body) {
      return request('POST', '/email/generate', body || {});
    },
    // 获取当前生效 Prompt 模板
    getPrompt: function () {
      return request('GET', '/email/prompt');
    },
    // 更新 Prompt 模板
    updatePrompt: function (content) {
      return request('PUT', '/email/prompt', { content: content });
    },
    // 邮件记录分页（params: page/per_page/status）
    records: function (params) {
      return request('GET', '/email/records' + _buildQuery(params));
    },
    // 单条邮件详情
    recordDetail: function (id) {
      return request('GET', '/email/records/' + encodeURIComponent(id));
    },
    // 修改邮件主题/正文（body: email_subject/email_content）
    updateRecord: function (id, body) {
      return request('PUT', '/email/records/' + encodeURIComponent(id), body || {});
    },
    // 修改邮件状态（status: generated/failed/sent）
    patchStatus: function (id, status) {
      return request('PATCH', '/email/records/' + encodeURIComponent(id), { status: status });
    },
    // 删除单条邮件
    deleteRecord: function (id) {
      return request('DELETE', '/email/records/' + encodeURIComponent(id));
    },
    // 批量删除邮件（ids: number[]）
    batchDeleteRecords: function (ids) {
      return request('DELETE', '/email/records', { record_ids: ids || [] });
    }
  };

  // ===== 日志模块 logApi（/logs，蓝图挂在 /api/v1 根下） =====
  var logApi = {
    // 操作日志分页（params: page/per_page/user_id/action，仅 admin）
    logs: function (params) {
      return request('GET', '/logs' + _buildQuery(params));
    }
  };

  // ===== 暴露到全局 =====
  window.apiRequest = request; // 暴露核心请求函数，供 app.js 等做自定义调用
  window.authApi = authApi;
  window.dataApi = dataApi;
  window.modelApi = modelApi;
  window.emailApi = emailApi;
  window.logApi = logApi;
})();
