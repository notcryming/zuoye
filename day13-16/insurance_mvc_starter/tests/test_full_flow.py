"""端到端全链路集成测试

完整业务闭环：
登录 admin → 上传 Excel → 训练三模型 → 全量预测 → 筛选 top10% 高潜客户
→ 批量生成营销邮件 → 查询操作日志

每一步校验数据库表数据变更，确保业务链路完整性。
覆盖 PRD 验收标准：数据上传、模型训练、预测、高潜筛选、邮件生成、操作审计。
"""
import io
import pytest


class TestFullFlow:
    """端到端全链路集成测试：一次性跑完完整业务链路"""

    def test_full_business_flow(self, test_client, admin_token, test_excel_bytes):
        """完整业务闭环：登录→上传→训练→预测→筛选→邮件→日志

        每步断言数据库状态与 API 返回结构，确保业务链路无断裂。
        """
        headers = {'Authorization': f'Bearer {admin_token}'}

        # ===== Step 1: 登录验证（admin_token 夹具已完成）=====
        resp = test_client.get('/api/v1/auth/me', headers=headers)
        assert resp.get_json()['data']['user']['username'] == 'admin'

        # ===== Step 2: 上传 Excel =====
        resp = test_client.post(
            '/api/v1/data/upload',
            data={'file': (io.BytesIO(test_excel_bytes), 'test.xlsx')},
            content_type='multipart/form-data',
            headers=headers,
        )
        body = resp.get_json()
        assert body['code'] == 0
        assert body['data']['imported_count'] == 30
        assert body['data']['quality_report']['total_rows'] == 30

        # 验证数据库：customers 表有 30 条记录
        resp = test_client.get('/api/v1/data/customers?per_page=100', headers=headers)
        assert resp.get_json()['data']['total'] == 30

        # ===== Step 3: 训练三模型 =====
        resp = test_client.post('/api/v1/model/train', json={}, headers=headers)
        body = resp.get_json()
        assert body['code'] == 0
        assert 'best_model' in body['data']
        assert len(body['data']['results']) == 3
        best_model = body['data']['best_model']

        # 验证数据库：experiments 表有 3 条记录
        resp = test_client.get('/api/v1/model/experiments', headers=headers)
        exp_data = resp.get_json()['data']
        assert exp_data['total'] == 3

        # 验证数据库：best 模型可查到
        resp = test_client.get('/api/v1/model/best', headers=headers)
        assert resp.get_json()['data']['model_name'] == best_model

        # ===== Step 4: 全量预测 =====
        resp = test_client.post('/api/v1/model/predict', json={}, headers=headers)
        body = resp.get_json()
        assert body['code'] == 0
        assert body['data']['predicted_count'] == 30

        # 验证数据库：customers 的 predicted_prob 已回写
        resp = test_client.get('/api/v1/data/customers?per_page=5', headers=headers)
        customers = resp.get_json()['data']['items']
        for c in customers:
            assert c['predicted_prob'] is not None

        # ===== Step 5: 筛选 top 10% 高潜客户 =====
        resp = test_client.get(
            '/api/v1/email/targets?percentile=0.9',
            headers=headers,
        )
        body = resp.get_json()
        assert body['code'] == 0
        assert body['data']['total'] > 0
        assert 'threshold' in body['data']
        target_customers = body['data']['customers']
        for c in target_customers:
            assert c['predicted_prob'] >= body['data']['threshold']

        # ===== Step 6: 批量生成营销邮件 =====
        # 使用 limit 模式取 top 5 客户
        resp = test_client.post(
            '/api/v1/email/generate',
            json={'limit': 5},
            headers=headers,
        )
        body = resp.get_json()
        assert body['code'] == 0
        # LLM 降级场景：generated_count=0, failed_count=5
        assert body['data']['failed_count'] == 5
        assert body['data']['generated_count'] == 0
        assert len(body['data']['records']) == 5

        # 验证数据库：email_records 表有 5 条记录
        resp = test_client.get('/api/v1/email/records', headers=headers)
        assert resp.get_json()['data']['total'] == 5

        # ===== Step 7: 查询操作日志 =====
        resp = test_client.get('/api/v1/logs', headers=headers)
        body = resp.get_json()
        assert body['code'] == 0
        # 至少有 model_training + prediction + email_generation 三条日志
        assert body['data']['total'] >= 3

        # 验证日志包含训练日志
        resp = test_client.get(
            '/api/v1/logs?action=model_training',
            headers=headers,
        )
        train_logs = resp.get_json()['data']
        assert train_logs['total'] >= 1
        assert train_logs['items'][0]['action'] == 'model_training'
        assert train_logs['items'][0]['details']['best_model'] == best_model

        # 验证日志包含预测日志
        resp = test_client.get(
            '/api/v1/logs?action=prediction',
            headers=headers,
        )
        predict_logs = resp.get_json()['data']
        assert predict_logs['total'] >= 1
        assert predict_logs['items'][0]['details']['predicted_count'] == 30

        # 验证日志包含邮件生成日志
        resp = test_client.get(
            '/api/v1/logs?action=email_generation',
            headers=headers,
        )
        email_logs = resp.get_json()['data']
        assert email_logs['total'] >= 1

    def test_full_flow_with_customer_ids(self, test_client, admin_token, test_excel_bytes):
        """完整链路变体：使用 customer_ids 指定客户生成邮件"""
        headers = {'Authorization': f'Bearer {admin_token}'}

        # 上传
        test_client.post(
            '/api/v1/data/upload',
            data={'file': (io.BytesIO(test_excel_bytes), 'test.xlsx')},
            content_type='multipart/form-data',
            headers=headers,
        )

        # 训练
        test_client.post('/api/v1/model/train', json={}, headers=headers)

        # 预测
        test_client.post('/api/v1/model/predict', json={}, headers=headers)

        # 按 customer_ids 生成邮件
        resp = test_client.post(
            '/api/v1/email/generate',
            json={'customer_ids': [1, 2, 3, 4, 5]},
            headers=headers,
        )
        body = resp.get_json()
        assert body['code'] == 0
        assert len(body['data']['records']) == 5

        # 验证邮件记录
        resp = test_client.get('/api/v1/email/records', headers=headers)
        assert resp.get_json()['data']['total'] == 5

        # 修改第一条邮件状态为 sent
        records = resp.get_json()['data']['items']
        record_id = records[0]['id']
        resp = test_client.patch(
            f'/api/v1/email/records/{record_id}',
            json={'status': 'sent'},
            headers=headers,
        )
        assert resp.get_json()['data']['status'] == 'sent'

        # 删除一条邮件
        resp = test_client.delete(
            f'/api/v1/email/records/{record_id}',
            headers=headers,
        )
        assert resp.get_json()['data']['success'] is True

        # 验证删除后数量减一
        resp = test_client.get('/api/v1/email/records', headers=headers)
        assert resp.get_json()['data']['total'] == 4

    def test_full_flow_user_permission(self, test_client, admin_token, user_token, test_excel_bytes):
        """权限验证：普通用户无法训练、导出模型、查看日志"""
        headers = {'Authorization': f'Bearer {user_token}'}

        # 普通用户可以上传数据
        resp = test_client.post(
            '/api/v1/data/upload',
            data={'file': (io.BytesIO(test_excel_bytes), 'test.xlsx')},
            content_type='multipart/form-data',
            headers=headers,
        )
        assert resp.get_json()['code'] == 0

        # 普通用户不能训练模型 → 403
        resp = test_client.post('/api/v1/model/train', json={}, headers=headers)
        assert resp.get_json()['code'] == 1003
        assert resp.status_code == 403

        # 普通用户不能导出模型 → 403
        resp = test_client.get(
            '/api/v1/model/export/logistic_regression',
            headers=headers,
        )
        assert resp.get_json()['code'] == 1003

        # 普通用户不能导入模型 → 403
        resp = test_client.post(
            '/api/v1/model/import',
            content_type='multipart/form-data',
            headers=headers,
        )
        assert resp.get_json()['code'] == 1003

        # 普通用户不能查看操作日志 → 403
        resp = test_client.get('/api/v1/logs', headers=headers)
        assert resp.get_json()['code'] == 1003

        # 普通用户不能查看用户列表 → 403
        resp = test_client.get('/api/v1/auth/userlist', headers=headers)
        assert resp.get_json()['code'] == 1003


class TestRootRoute:
    """根路由测试：返回前端 SPA 入口页"""

    def test_root_returns_html(self, test_client):
        """GET /：返回 200 + HTML 内容"""
        resp = test_client.get('/')
        assert resp.status_code == 200
        assert 'text/html' in resp.content_type
