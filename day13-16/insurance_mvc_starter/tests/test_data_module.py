"""数据模块接口测试

覆盖端点：
1. POST /api/v1/data/upload               上传 Excel
2. GET  /api/v1/data/customers            客户分页查询（含筛选）
3. GET  /api/v1/data/export               导出 Excel
4. GET  /api/v1/data/statistics           数据统计
5. GET  /api/v1/data/quality              数据质量报告
6. GET  /api/v1/data/visualization/<type>  EDA 可视化

测试维度：上传成功 + 无 token + 无文件 + 格式错误 + 分页 + 筛选 + 导出 + 统计 + 质量报告 + 可视化 + 异常场景
"""
import io
import pytest


# ===== 1. 上传 Excel =====

class TestUpload:
    """数据上传接口测试"""

    def test_upload_success(self, test_client, admin_token, test_excel_bytes):
        """正常上传：返回 imported_count=30 + quality_report"""
        resp = test_client.post(
            '/api/v1/data/upload',
            data={'file': (io.BytesIO(test_excel_bytes), 'test.xlsx')},
            content_type='multipart/form-data',
            headers={'Authorization': f'Bearer {admin_token}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert body['data']['imported_count'] == 30
        assert 'quality_report' in body['data']
        assert body['data']['quality_report']['total_rows'] == 30

    def test_upload_without_token(self, test_client, test_excel_bytes):
        """无 token 上传：返回 1002，HTTP 401"""
        resp = test_client.post(
            '/api/v1/data/upload',
            data={'file': (io.BytesIO(test_excel_bytes), 'test.xlsx')},
            content_type='multipart/form-data',
        )
        body = resp.get_json()
        assert body['code'] == 1002
        assert resp.status_code == 401

    def test_upload_no_file(self, test_client, admin_token):
        """未传文件：返回 1001"""
        resp = test_client.post(
            '/api/v1/data/upload',
            content_type='multipart/form-data',
            headers={'Authorization': f'Bearer {admin_token}'},
        )
        body = resp.get_json()
        assert body['code'] == 1001
        assert resp.status_code == 400

    def test_upload_wrong_extension(self, test_client, admin_token):
        """文件格式错误（.txt）：返回 1001"""
        resp = test_client.post(
            '/api/v1/data/upload',
            data={'file': (io.BytesIO(b'plain text'), 'test.txt')},
            content_type='multipart/form-data',
            headers={'Authorization': f'Bearer {admin_token}'},
        )
        body = resp.get_json()
        assert body['code'] == 1001
        assert resp.status_code == 400


# ===== 2. 客户分页查询 =====

class TestCustomers:
    """客户分页查询接口测试"""

    def test_customers_pagination(self, test_client, uploaded_data):
        """分页查询：total=30，默认 per_page=50 一次返回全部"""
        resp = test_client.get(
            '/api/v1/data/customers',
            headers={'Authorization': f'Bearer {uploaded_data}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert body['data']['total'] == 30
        assert len(body['data']['items']) == 30
        assert body['data']['page'] == 1
        assert body['data']['per_page'] == 50

    def test_customers_custom_per_page(self, test_client, uploaded_data):
        """自定义 per_page=10：返回 10 条，pages=3"""
        resp = test_client.get(
            '/api/v1/data/customers?per_page=10',
            headers={'Authorization': f'Bearer {uploaded_data}'},
        )
        body = resp.get_json()
        assert body['data']['total'] == 30
        assert len(body['data']['items']) == 10
        assert body['data']['pages'] == 3

    def test_customers_filter_gender(self, test_client, uploaded_data):
        """筛选 gender=Male：返回 15 条"""
        resp = test_client.get(
            '/api/v1/data/customers?gender=Male',
            headers={'Authorization': f'Bearer {uploaded_data}'},
        )
        body = resp.get_json()
        assert body['data']['total'] == 15
        for item in body['data']['items']:
            assert item['gender'] == 'Male'

    def test_customers_filter_age_range(self, test_client, uploaded_data):
        """筛选 age_min=30 & age_max=50"""
        resp = test_client.get(
            '/api/v1/data/customers?age_min=30&age_max=50',
            headers={'Authorization': f'Bearer {uploaded_data}'},
        )
        body = resp.get_json()
        for item in body['data']['items']:
            assert 30 <= item['age'] <= 50

    def test_customers_filter_previously_insured(self, test_client, uploaded_data):
        """筛选 previously_insured=1"""
        resp = test_client.get(
            '/api/v1/data/customers?previously_insured=1',
            headers={'Authorization': f'Bearer {uploaded_data}'},
        )
        body = resp.get_json()
        for item in body['data']['items']:
            assert item['previously_insured'] == 1

    def test_customers_filter_keyword(self, test_client, uploaded_data):
        """筛选 keyword=1：只返回 id=1 的客户"""
        resp = test_client.get(
            '/api/v1/data/customers?keyword=1',
            headers={'Authorization': f'Bearer {uploaded_data}'},
        )
        body = resp.get_json()
        assert body['data']['total'] == 1
        assert body['data']['items'][0]['id'] == 1

    def test_customers_invalid_page(self, test_client, uploaded_data):
        """page=0：返回 1001"""
        resp = test_client.get(
            '/api/v1/data/customers?page=0',
            headers={'Authorization': f'Bearer {uploaded_data}'},
        )
        body = resp.get_json()
        assert body['code'] == 1001
        assert resp.status_code == 400

    def test_customers_without_token(self, test_client):
        """无 token 查询：返回 1002"""
        resp = test_client.get('/api/v1/data/customers')
        body = resp.get_json()
        assert body['code'] == 1002
        assert resp.status_code == 401


# ===== 3. 数据导出 =====

class TestExport:
    """数据导出接口测试"""

    def test_export_success(self, test_client, uploaded_data):
        """导出 Excel：返回二进制文件流"""
        resp = test_client.get(
            '/api/v1/data/export',
            headers={'Authorization': f'Bearer {uploaded_data}'},
        )
        assert resp.status_code == 200
        assert 'spreadsheet' in resp.content_type
        assert len(resp.data) > 0

    def test_export_with_filter(self, test_client, uploaded_data):
        """带筛选导出：gender=Male → 15 条"""
        resp = test_client.get(
            '/api/v1/data/export?gender=Male',
            headers={'Authorization': f'Bearer {uploaded_data}'},
        )
        assert resp.status_code == 200
        assert 'spreadsheet' in resp.content_type

    def test_export_no_data(self, test_client, admin_token):
        """无数据导出：返回 2001，HTTP 404"""
        resp = test_client.get(
            '/api/v1/data/export',
            headers={'Authorization': f'Bearer {admin_token}'},
        )
        body = resp.get_json()
        assert body['code'] == 2001
        assert resp.status_code == 404


# ===== 4. 数据统计 =====

class TestStatistics:
    """数据统计接口测试"""

    def test_statistics_with_data(self, test_client, uploaded_data):
        """有数据统计：total=30，含性别/正负样本/年龄分布"""
        resp = test_client.get(
            '/api/v1/data/statistics',
            headers={'Authorization': f'Bearer {uploaded_data}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert body['data']['total'] == 30
        assert 'gender_distribution' in body['data']
        assert 'response_distribution' in body['data']
        assert 'age_stats' in body['data']
        assert body['data']['age_stats']['min'] == 22
        assert body['data']['age_stats']['max'] == 65

    def test_statistics_empty(self, test_client, admin_token):
        """无数据统计：total=0，空结构"""
        resp = test_client.get(
            '/api/v1/data/statistics',
            headers={'Authorization': f'Bearer {admin_token}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert body['data']['total'] == 0


# ===== 5. 数据质量报告 =====

class TestQuality:
    """数据质量报告接口测试"""

    def test_quality_with_data(self, test_client, uploaded_data):
        """有数据质量报告：total_rows=30"""
        resp = test_client.get(
            '/api/v1/data/quality',
            headers={'Authorization': f'Bearer {uploaded_data}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert body['data']['total_rows'] == 30
        assert 'missing_values' in body['data']
        assert 'duplicates' in body['data']
        assert 'dtypes' in body['data']

    def test_quality_empty(self, test_client, admin_token):
        """无数据质量报告：total_rows=0"""
        resp = test_client.get(
            '/api/v1/data/quality',
            headers={'Authorization': f'Bearer {admin_token}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert body['data']['total_rows'] == 0


# ===== 6. EDA 可视化 =====

class TestVisualization:
    """EDA 可视化接口测试"""

    def test_visualization_response_distribution(self, test_client, uploaded_data):
        """response_distribution 图表：返回 base64 PNG"""
        resp = test_client.get(
            '/api/v1/data/visualization/response_distribution',
            headers={'Authorization': f'Bearer {uploaded_data}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert body['data']['chart_type'] == 'response_distribution'
        assert body['data']['format'] == 'png'
        assert len(body['data']['image_base64']) > 100

    def test_visualization_gender_response(self, test_client, uploaded_data):
        """gender_response 图表：返回 base64 PNG"""
        resp = test_client.get(
            '/api/v1/data/visualization/gender_response',
            headers={'Authorization': f'Bearer {uploaded_data}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert body['data']['chart_type'] == 'gender_response'

    def test_visualization_no_data(self, test_client, admin_token):
        """无数据可视化：返回 2001，HTTP 404"""
        resp = test_client.get(
            '/api/v1/data/visualization/response_distribution',
            headers={'Authorization': f'Bearer {admin_token}'},
        )
        body = resp.get_json()
        assert body['code'] == 2001
        assert resp.status_code == 404

    def test_visualization_invalid_chart_type(self, test_client, uploaded_data):
        """未知图表类型：返回 1001"""
        resp = test_client.get(
            '/api/v1/data/visualization/nonexistent_chart',
            headers={'Authorization': f'Bearer {uploaded_data}'},
        )
        body = resp.get_json()
        assert body['code'] == 1001
        assert resp.status_code == 400
