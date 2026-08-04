"""邮件模块接口测试

覆盖端点：
1. GET  /api/v1/email/targets            高潜客户筛选
2. POST /api/v1/email/generate           批量生成营销邮件
3. GET  /api/v1/email/prompt             获取 Prompt 模板
4. PUT  /api/v1/email/prompt             更新 Prompt 模板
5. GET  /api/v1/email/records            邮件记录列表
6. GET  /api/v1/email/records/<rid>      邮件详情
7. PUT  /api/v1/email/records/<rid>      修改邮件主题/正文
8. PATCH /api/v1/email/records/<rid>     修改邮件状态
9. DELETE /api/v1/email/records/<rid>    删除单条邮件
10. DELETE /api/v1/email/records         批量删除邮件

测试维度：高潜筛选 + 批量生成 + Prompt 管理 + 邮件 CRUD + LLM 降级 + 权限 + 异常场景

【注意】测试环境 LLM_API_KEY 为空，邮件生成降级为 failed 状态，属于正常的降级场景测试。
"""
import io
import pytest


# ====================================================================
#  本地夹具：predicted_data —— 上传 + 训练 + 预测完成，返回 admin_token
# ====================================================================
@pytest.fixture
def predicted_data(test_client, trained_model):
    """在 trained_model 基础上执行全量预测，使客户 predicted_prob 非空"""
    resp = test_client.post(
        '/api/v1/model/predict',
        json={},
        headers={'Authorization': f'Bearer {trained_model}'},
    )
    body = resp.get_json()
    assert body['code'] == 0, f"预测失败: {body}"
    assert body['data']['predicted_count'] == 30
    return trained_model


# ====================================================================
#  本地夹具：generated_emails —— 预测后生成邮件，返回 admin_token
# ====================================================================
@pytest.fixture
def generated_emails(test_client, predicted_data):
    """生成邮件（LLM 降级 → failed），返回 admin_token"""
    resp = test_client.post(
        '/api/v1/email/generate',
        json={'limit': 5},
        headers={'Authorization': f'Bearer {predicted_data}'},
    )
    body = resp.get_json()
    assert body['code'] == 0, f"邮件生成失败: {body}"
    return predicted_data


# ===== 1. 高潜客户筛选 =====

class TestTargets:
    """高潜客户筛选接口测试"""

    def test_targets_success(self, test_client, predicted_data):
        """有预测数据筛选：返回 threshold + customers 列表"""
        resp = test_client.get(
            '/api/v1/email/targets?percentile=0.9',
            headers={'Authorization': f'Bearer {predicted_data}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert 'threshold' in body['data']
        assert body['data']['total'] > 0
        for c in body['data']['customers']:
            assert 'predicted_prob' in c

    def test_targets_no_prediction(self, test_client, uploaded_data):
        """无预测数据筛选：返回 3002"""
        resp = test_client.get(
            '/api/v1/email/targets',
            headers={'Authorization': f'Bearer {uploaded_data}'},
        )
        body = resp.get_json()
        assert body['code'] == 3002

    def test_targets_invalid_percentile(self, test_client, predicted_data):
        """percentile 超出范围（=1.5）：返回 1001"""
        resp = test_client.get(
            '/api/v1/email/targets?percentile=1.5',
            headers={'Authorization': f'Bearer {predicted_data}'},
        )
        body = resp.get_json()
        assert body['code'] == 1001

    def test_targets_without_token(self, test_client, predicted_data):
        """无 token 筛选：返回 1002"""
        resp = test_client.get('/api/v1/email/targets')
        body = resp.get_json()
        assert body['code'] == 1002


# ===== 2. 批量生成营销邮件 =====

class TestGenerate:
    """批量生成邮件接口测试"""

    def test_generate_by_limit(self, test_client, predicted_data):
        """按 limit=5 生成：LLM 降级 → failed_count=5"""
        resp = test_client.post(
            '/api/v1/email/generate',
            json={'limit': 5},
            headers={'Authorization': f'Bearer {predicted_data}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert body['data']['failed_count'] == 5
        assert body['data']['generated_count'] == 0  # LLM 降级
        assert len(body['data']['records']) == 5

    def test_generate_by_customer_ids(self, test_client, predicted_data):
        """按 customer_ids 指定客户生成"""
        resp = test_client.post(
            '/api/v1/email/generate',
            json={'customer_ids': [1, 2, 3]},
            headers={'Authorization': f'Bearer {predicted_data}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert len(body['data']['records']) == 3

    def test_generate_no_prediction(self, test_client, uploaded_data):
        """无预测数据生成（limit 模式）：返回 3002"""
        resp = test_client.post(
            '/api/v1/email/generate',
            json={'limit': 5},
            headers={'Authorization': f'Bearer {uploaded_data}'},
        )
        body = resp.get_json()
        assert body['code'] == 3002

    def test_generate_invalid_limit(self, test_client, predicted_data):
        """limit 非正整数：返回 1001"""
        resp = test_client.post(
            '/api/v1/email/generate',
            json={'limit': 0},
            headers={'Authorization': f'Bearer {predicted_data}'},
        )
        body = resp.get_json()
        assert body['code'] == 1001

    def test_generate_without_token(self, test_client, predicted_data):
        """无 token 生成：返回 1002"""
        resp = test_client.post('/api/v1/email/generate', json={'limit': 5})
        body = resp.get_json()
        assert body['code'] == 1002


# ===== 3. Prompt 模板管理 =====

class TestPrompt:
    """Prompt 模板管理接口测试"""

    def test_get_prompt(self, test_client, admin_token):
        """获取当前 Prompt 模板：返回 name + content"""
        resp = test_client.get(
            '/api/v1/email/prompt',
            headers={'Authorization': f'Bearer {admin_token}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert 'name' in body['data']
        assert 'content' in body['data']
        assert len(body['data']['content']) > 0

    def test_update_prompt(self, test_client, admin_token):
        """更新 Prompt 模板：返回更新后的 name + content"""
        new_content = '这是一个测试 Prompt 模板，包含 {customer_name} 占位符。'
        resp = test_client.put(
            '/api/v1/email/prompt',
            json={'content': new_content},
            headers={'Authorization': f'Bearer {admin_token}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert body['data']['content'] == new_content

    def test_update_prompt_empty_content(self, test_client, admin_token):
        """更新 Prompt 空内容：返回 1001"""
        resp = test_client.put(
            '/api/v1/email/prompt',
            json={'content': ''},
            headers={'Authorization': f'Bearer {admin_token}'},
        )
        body = resp.get_json()
        assert body['code'] == 1001

    def test_get_prompt_without_token(self, test_client):
        """无 token 获取 Prompt：返回 1002"""
        resp = test_client.get('/api/v1/email/prompt')
        body = resp.get_json()
        assert body['code'] == 1002


# ===== 4. 邮件记录列表 =====

class TestRecords:
    """邮件记录列表接口测试"""

    def test_records_list_admin(self, test_client, generated_emails):
        """admin 查看邮件记录：total >= 5"""
        resp = test_client.get(
            '/api/v1/email/records',
            headers={'Authorization': f'Bearer {generated_emails}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert body['data']['total'] >= 5
        assert len(body['data']['items']) >= 5
        # admin 能看到 created_by_username
        assert 'created_by_username' in body['data']['items'][0]

    def test_records_list_with_status_filter(self, test_client, generated_emails):
        """按 status=failed 过滤邮件记录"""
        resp = test_client.get(
            '/api/v1/email/records?status=failed',
            headers={'Authorization': f'Bearer {generated_emails}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        for item in body['data']['items']:
            assert item['status'] == 'failed'

    def test_records_pagination(self, test_client, generated_emails):
        """分页查询邮件记录：per_page=2"""
        resp = test_client.get(
            '/api/v1/email/records?per_page=2',
            headers={'Authorization': f'Bearer {generated_emails}'},
        )
        body = resp.get_json()
        assert len(body['data']['items']) == 2
        assert body['data']['per_page'] == 2

    def test_records_empty(self, test_client, admin_token):
        """无邮件记录查询：total=0"""
        resp = test_client.get(
            '/api/v1/email/records',
            headers={'Authorization': f'Bearer {admin_token}'},
        )
        body = resp.get_json()
        assert body['data']['total'] == 0

    def test_records_user_isolation(self, test_client, generated_emails, user_token):
        """普通 user 看不到 admin 生成的邮件记录"""
        resp = test_client.get(
            '/api/v1/email/records',
            headers={'Authorization': f'Bearer {user_token}'},
        )
        body = resp.get_json()
        assert body['data']['total'] == 0  # user 看不到 admin 的记录


# ===== 5. 邮件详情 =====

class TestRecordDetail:
    """邮件详情接口测试"""

    def test_record_detail_success(self, test_client, generated_emails):
        """查看邮件详情：返回含 content 正文"""
        # 先获取一条记录 id
        list_resp = test_client.get(
            '/api/v1/email/records',
            headers={'Authorization': f'Bearer {generated_emails}'},
        )
        record_id = list_resp.get_json()['data']['items'][0]['id']

        resp = test_client.get(
            f'/api/v1/email/records/{record_id}',
            headers={'Authorization': f'Bearer {generated_emails}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert body['data']['id'] == record_id
        assert 'content' in body['data']  # 详情含 content

    def test_record_detail_not_found(self, test_client, admin_token):
        """查看不存在的邮件：返回 2001"""
        resp = test_client.get(
            '/api/v1/email/records/99999',
            headers={'Authorization': f'Bearer {admin_token}'},
        )
        body = resp.get_json()
        assert body['code'] == 2001
        assert resp.status_code == 404

    def test_record_detail_user_isolation(self, test_client, generated_emails, user_token):
        """普通 user 查看 admin 的邮件：返回 2001（隔离）"""
        list_resp = test_client.get(
            '/api/v1/email/records',
            headers={'Authorization': f'Bearer {generated_emails}'},
        )
        record_id = list_resp.get_json()['data']['items'][0]['id']

        resp = test_client.get(
            f'/api/v1/email/records/{record_id}',
            headers={'Authorization': f'Bearer {user_token}'},
        )
        body = resp.get_json()
        assert body['code'] == 2001


# ===== 6. 修改邮件 =====

class TestUpdateRecord:
    """修改邮件主题/正文接口测试"""

    def test_update_subject(self, test_client, generated_emails):
        """修改邮件主题：返回更新后的 subject"""
        list_resp = test_client.get(
            '/api/v1/email/records',
            headers={'Authorization': f'Bearer {generated_emails}'},
        )
        record_id = list_resp.get_json()['data']['items'][0]['id']

        resp = test_client.put(
            f'/api/v1/email/records/{record_id}',
            json={'email_subject': '更新后的主题'},
            headers={'Authorization': f'Bearer {generated_emails}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert body['data']['subject'] == '更新后的主题'

    def test_update_content(self, test_client, generated_emails):
        """修改邮件正文：返回更新后的 content"""
        list_resp = test_client.get(
            '/api/v1/email/records',
            headers={'Authorization': f'Bearer {generated_emails}'},
        )
        record_id = list_resp.get_json()['data']['items'][0]['id']

        resp = test_client.put(
            f'/api/v1/email/records/{record_id}',
            json={'email_content': '更新后的正文内容'},
            headers={'Authorization': f'Bearer {generated_emails}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['data']['content'] == '更新后的正文内容'

    def test_update_no_fields(self, test_client, generated_emails):
        """未提供更新字段：返回 1001"""
        list_resp = test_client.get(
            '/api/v1/email/records',
            headers={'Authorization': f'Bearer {generated_emails}'},
        )
        record_id = list_resp.get_json()['data']['items'][0]['id']

        resp = test_client.put(
            f'/api/v1/email/records/{record_id}',
            json={},
            headers={'Authorization': f'Bearer {generated_emails}'},
        )
        body = resp.get_json()
        assert body['code'] == 1001


# ===== 7. 修改邮件状态 =====

class TestPatchStatus:
    """修改邮件状态接口测试"""

    def test_patch_status_sent(self, test_client, generated_emails):
        """标记邮件为 sent 状态"""
        list_resp = test_client.get(
            '/api/v1/email/records',
            headers={'Authorization': f'Bearer {generated_emails}'},
        )
        record_id = list_resp.get_json()['data']['items'][0]['id']

        resp = test_client.patch(
            f'/api/v1/email/records/{record_id}',
            json={'status': 'sent'},
            headers={'Authorization': f'Bearer {generated_emails}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert body['data']['status'] == 'sent'

    def test_patch_invalid_status(self, test_client, generated_emails):
        """非法状态值：返回 1001"""
        list_resp = test_client.get(
            '/api/v1/email/records',
            headers={'Authorization': f'Bearer {generated_emails}'},
        )
        record_id = list_resp.get_json()['data']['items'][0]['id']

        resp = test_client.patch(
            f'/api/v1/email/records/{record_id}',
            json={'status': 'invalid_status'},
            headers={'Authorization': f'Bearer {generated_emails}'},
        )
        body = resp.get_json()
        assert body['code'] == 1001

    def test_patch_empty_status(self, test_client, generated_emails):
        """空状态值：返回 1001"""
        list_resp = test_client.get(
            '/api/v1/email/records',
            headers={'Authorization': f'Bearer {generated_emails}'},
        )
        record_id = list_resp.get_json()['data']['items'][0]['id']

        resp = test_client.patch(
            f'/api/v1/email/records/{record_id}',
            json={'status': ''},
            headers={'Authorization': f'Bearer {generated_emails}'},
        )
        body = resp.get_json()
        assert body['code'] == 1001


# ===== 8. 删除单条邮件 =====

class TestDeleteRecord:
    """删除单条邮件接口测试"""

    def test_delete_success(self, test_client, generated_emails):
        """删除单条邮件：返回 success=true"""
        list_resp = test_client.get(
            '/api/v1/email/records',
            headers={'Authorization': f'Bearer {generated_emails}'},
        )
        record_id = list_resp.get_json()['data']['items'][0]['id']

        resp = test_client.delete(
            f'/api/v1/email/records/{record_id}',
            headers={'Authorization': f'Bearer {generated_emails}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert body['data']['success'] is True

    def test_delete_not_found(self, test_client, admin_token):
        """删除不存在的邮件：返回 2001"""
        resp = test_client.delete(
            '/api/v1/email/records/99999',
            headers={'Authorization': f'Bearer {admin_token}'},
        )
        body = resp.get_json()
        assert body['code'] == 2001
        assert resp.status_code == 404


# ===== 9. 批量删除邮件 =====

class TestBatchDelete:
    """批量删除邮件接口测试"""

    def test_batch_delete_success(self, test_client, generated_emails):
        """批量删除邮件：返回 deleted_count"""
        list_resp = test_client.get(
            '/api/v1/email/records?per_page=3',
            headers={'Authorization': f'Bearer {generated_emails}'},
        )
        ids = [item['id'] for item in list_resp.get_json()['data']['items']]

        resp = test_client.delete(
            '/api/v1/email/records',
            json={'record_ids': ids},
            headers={'Authorization': f'Bearer {generated_emails}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert body['data']['deleted_count'] == len(ids)

    def test_batch_delete_empty_list(self, test_client, admin_token):
        """空 record_ids：返回 1001"""
        resp = test_client.delete(
            '/api/v1/email/records',
            json={'record_ids': []},
            headers={'Authorization': f'Bearer {admin_token}'},
        )
        body = resp.get_json()
        assert body['code'] == 1001

    def test_batch_delete_missing_field(self, test_client, admin_token):
        """缺少 record_ids 字段：返回 1001"""
        resp = test_client.delete(
            '/api/v1/email/records',
            json={},
            headers={'Authorization': f'Bearer {admin_token}'},
        )
        body = resp.get_json()
        assert body['code'] == 1001
