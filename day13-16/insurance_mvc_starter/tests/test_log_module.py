"""日志模块接口测试

覆盖端点：
1. GET /api/v1/logs  操作日志分页查询（admin）

测试维度：admin 查询 + user 权限拦截 + 无 token + action 过滤 + user_id 过滤 + 分页 + 非法参数

【依赖】需要先执行训练/预测/邮件生成等操作产生操作日志，复用 trained_model 夹具。
"""
import pytest


# ====================================================================
#  本地夹具：logs_data —— 执行训练 + 预测 + 邮件生成产生操作日志
# ====================================================================
@pytest.fixture
def logs_data(test_client, trained_model):
    """执行训练 + 预测 + 邮件生成，产生 model_training / prediction / email_generation 日志"""
    token = trained_model

    # 预测（产生 prediction 日志）
    resp = test_client.post(
        '/api/v1/model/predict',
        json={},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert resp.get_json()['code'] == 0

    # 邮件生成（产生 email_generation 日志）
    resp = test_client.post(
        '/api/v1/email/generate',
        json={'limit': 3},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert resp.get_json()['code'] == 0

    return token


# ===== 1. 操作日志查询 =====

class TestLogs:
    """操作日志查询接口测试"""

    def test_logs_admin_success(self, test_client, logs_data):
        """admin 查询操作日志：total >= 3（训练 + 预测 + 邮件生成）"""
        resp = test_client.get(
            '/api/v1/logs',
            headers={'Authorization': f'Bearer {logs_data}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert body['data']['total'] >= 3
        assert len(body['data']['items']) >= 3
        # 检查日志结构
        log = body['data']['items'][0]
        assert 'id' in log
        assert 'user_id' in log
        assert 'action' in log
        assert 'details' in log
        assert 'created_at' in log

    def test_logs_user_forbidden(self, test_client, user_token):
        """普通 user 查询日志：返回 1003，HTTP 403"""
        resp = test_client.get(
            '/api/v1/logs',
            headers={'Authorization': f'Bearer {user_token}'},
        )
        body = resp.get_json()
        assert body['code'] == 1003
        assert resp.status_code == 403

    def test_logs_without_token(self, test_client):
        """无 token 查询日志：返回 1002，HTTP 401"""
        resp = test_client.get('/api/v1/logs')
        body = resp.get_json()
        assert body['code'] == 1002
        assert resp.status_code == 401

    def test_logs_filter_action(self, test_client, logs_data):
        """按 action=model_training 过滤：只返回训练日志"""
        resp = test_client.get(
            '/api/v1/logs?action=model_training',
            headers={'Authorization': f'Bearer {logs_data}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert body['data']['total'] >= 1
        for item in body['data']['items']:
            assert item['action'] == 'model_training'

    def test_logs_filter_user_id(self, test_client, logs_data):
        """按 user_id=1 过滤（admin 的 user_id）"""
        resp = test_client.get(
            '/api/v1/logs?user_id=1',
            headers={'Authorization': f'Bearer {logs_data}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        for item in body['data']['items']:
            assert item['user_id'] == 1

    def test_logs_pagination(self, test_client, logs_data):
        """分页查询日志：per_page=2"""
        resp = test_client.get(
            '/api/v1/logs?per_page=2',
            headers={'Authorization': f'Bearer {logs_data}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert len(body['data']['items']) <= 2
        assert body['data']['per_page'] == 2

    def test_logs_invalid_action(self, test_client, logs_data):
        """非法 action 值：返回 1001"""
        resp = test_client.get(
            '/api/v1/logs?action=invalid_action',
            headers={'Authorization': f'Bearer {logs_data}'},
        )
        body = resp.get_json()
        assert body['code'] == 1001
        assert resp.status_code == 400

    def test_logs_invalid_page(self, test_client, logs_data):
        """page=0：返回 1001"""
        resp = test_client.get(
            '/api/v1/logs?page=0',
            headers={'Authorization': f'Bearer {logs_data}'},
        )
        body = resp.get_json()
        assert body['code'] == 1001
        assert resp.status_code == 400

    def test_logs_empty(self, test_client, admin_token):
        """无操作日志时查询：total=0"""
        resp = test_client.get(
            '/api/v1/logs',
            headers={'Authorization': f'Bearer {admin_token}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert body['data']['total'] == 0
