"""模型模块接口测试

覆盖端点：
1. POST /api/v1/model/train                  模型训练（admin）
2. GET  /api/v1/model/experiments            实验记录分页
3. GET  /api/v1/model/best                   获取最优模型
4. POST /api/v1/model/predict                全量预测
5. POST /api/v1/model/predict_upload         上传 Excel 离线预测
6. GET  /api/v1/model/visualization/<type>   模型评估可视化
7. GET  /api/v1/model/export/<model_name>    导出模型文件（admin）
8. POST /api/v1/model/import                 导入模型文件（admin）

测试维度：训练 + 预测 + 可视化 + 导入导出 + 权限拦截 + 异常场景（无数据训练）
"""
import io
import pytest


# ===== 1. 模型训练 =====

class TestTrain:
    """模型训练接口测试"""

    def test_train_success(self, test_client, uploaded_data):
        """训练三模型：返回 best_model + 3 条 results"""
        resp = test_client.post(
            '/api/v1/model/train',
            json={},
            headers={'Authorization': f'Bearer {uploaded_data}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert 'best_model' in body['data']
        assert len(body['data']['results']) == 3
        for model_name, metrics in body['data']['results'].items():
            assert 'accuracy' in metrics
            assert 'roc_auc' in metrics

    def test_train_no_data(self, test_client, admin_token):
        """无数据训练：返回 2001"""
        resp = test_client.post(
            '/api/v1/model/train',
            json={},
            headers={'Authorization': f'Bearer {admin_token}'},
        )
        body = resp.get_json()
        assert body['code'] == 2001
        assert resp.status_code == 400

    def test_train_user_forbidden(self, test_client, user_token, uploaded_data):
        """普通 user 训练：返回 1003，HTTP 403"""
        resp = test_client.post(
            '/api/v1/model/train',
            json={},
            headers={'Authorization': f'Bearer {user_token}'},
        )
        body = resp.get_json()
        assert body['code'] == 1003
        assert resp.status_code == 403

    def test_train_without_token(self, test_client, uploaded_data):
        """无 token 训练：返回 1002"""
        resp = test_client.post('/api/v1/model/train', json={})
        body = resp.get_json()
        assert body['code'] == 1002
        assert resp.status_code == 401


# ===== 2. 实验记录 =====

class TestExperiments:
    """实验记录查询接口测试"""

    def test_experiments_list(self, test_client, trained_model):
        """训练后查询实验记录：total=3"""
        resp = test_client.get(
            '/api/v1/model/experiments',
            headers={'Authorization': f'Bearer {trained_model}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert body['data']['total'] == 3
        assert len(body['data']['items']) == 3

    def test_experiments_filter_model_name(self, test_client, trained_model):
        """按 model_name 过滤：logistic_regression → 1 条"""
        resp = test_client.get(
            '/api/v1/model/experiments?model_name=logistic_regression',
            headers={'Authorization': f'Bearer {trained_model}'},
        )
        body = resp.get_json()
        assert body['data']['total'] == 1
        assert body['data']['items'][0]['model_name'] == 'logistic_regression'

    def test_experiments_empty(self, test_client, admin_token):
        """未训练查询：total=0"""
        resp = test_client.get(
            '/api/v1/model/experiments',
            headers={'Authorization': f'Bearer {admin_token}'},
        )
        body = resp.get_json()
        assert body['data']['total'] == 0


# ===== 3. 最优模型 =====

class TestBestModel:
    """获取最优模型接口测试"""

    def test_best_model_after_train(self, test_client, trained_model):
        """训练后获取最优模型：返回 model_name + roc_auc"""
        resp = test_client.get(
            '/api/v1/model/best',
            headers={'Authorization': f'Bearer {trained_model}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert 'model_name' in body['data']
        assert 'roc_auc' in body['data']
        assert 'experiment_id' in body['data']

    def test_best_model_not_found(self, test_client, admin_token):
        """未训练获取最优模型：返回 3002"""
        resp = test_client.get(
            '/api/v1/model/best',
            headers={'Authorization': f'Bearer {admin_token}'},
        )
        body = resp.get_json()
        assert body['code'] == 3002
        assert resp.status_code == 400


# ===== 4. 全量预测 =====

class TestPredict:
    """全量预测接口测试"""

    def test_predict_success(self, test_client, trained_model):
        """训练后全量预测：predicted_count=30"""
        resp = test_client.post(
            '/api/v1/model/predict',
            json={},
            headers={'Authorization': f'Bearer {trained_model}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert body['data']['predicted_count'] == 30
        assert 'model_name' in body['data']

    def test_predict_no_data(self, test_client, admin_token):
        """无数据预测：无模型时返回 3002（模型检查先于数据检查）"""
        resp = test_client.post(
            '/api/v1/model/predict',
            json={},
            headers={'Authorization': f'Bearer {admin_token}'},
        )
        body = resp.get_json()
        assert body['code'] == 3002

    def test_predict_without_token(self, test_client, trained_model):
        """无 token 预测：返回 1002"""
        resp = test_client.post('/api/v1/model/predict', json={})
        body = resp.get_json()
        assert body['code'] == 1002


# ===== 5. 上传 Excel 预测 =====

class TestPredictUpload:
    """上传 Excel 离线预测接口测试"""

    def test_predict_upload_success(self, test_client, trained_model, test_excel_bytes):
        """上传 Excel 预测：返回 predictions 列表 + statistics"""
        resp = test_client.post(
            '/api/v1/model/predict_upload',
            data={'file': (io.BytesIO(test_excel_bytes), 'predict.xlsx')},
            content_type='multipart/form-data',
            headers={'Authorization': f'Bearer {trained_model}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert body['data']['total_count'] == 30
        assert 'statistics' in body['data']
        assert len(body['data']['predictions']) == 30
        assert 'predicted_prob' in body['data']['predictions'][0]

    def test_predict_upload_no_file(self, test_client, trained_model):
        """未传文件：返回 1001"""
        resp = test_client.post(
            '/api/v1/model/predict_upload',
            content_type='multipart/form-data',
            headers={'Authorization': f'Bearer {trained_model}'},
        )
        body = resp.get_json()
        assert body['code'] == 1001

    def test_predict_upload_wrong_extension(self, test_client, trained_model):
        """文件格式错误：返回 1001"""
        resp = test_client.post(
            '/api/v1/model/predict_upload',
            data={'file': (io.BytesIO(b'plain'), 'test.txt')},
            content_type='multipart/form-data',
            headers={'Authorization': f'Bearer {trained_model}'},
        )
        body = resp.get_json()
        assert body['code'] == 1001


# ===== 6. 模型评估可视化 =====

class TestModelVisualization:
    """模型评估可视化接口测试"""

    def test_visualization_roc_curve(self, test_client, trained_model):
        """ROC 曲线：返回 base64 PNG"""
        resp = test_client.get(
            '/api/v1/model/visualization/roc_curve',
            headers={'Authorization': f'Bearer {trained_model}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert body['data']['chart_type'] == 'roc_curve'
        assert len(body['data']['image_base64']) > 100

    def test_visualization_metrics_comparison(self, test_client, trained_model):
        """指标对比图：返回 base64 PNG"""
        resp = test_client.get(
            '/api/v1/model/visualization/metrics_comparison',
            headers={'Authorization': f'Bearer {trained_model}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0

    def test_visualization_confusion_matrix_with_model(self, test_client, trained_model):
        """混淆矩阵（指定 model）：返回 base64 PNG"""
        resp = test_client.get(
            '/api/v1/model/visualization/confusion_matrix?model=logistic_regression',
            headers={'Authorization': f'Bearer {trained_model}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0

    def test_visualization_confusion_matrix_without_model(self, test_client, trained_model):
        """混淆矩阵（未指定 model）：返回 1001"""
        resp = test_client.get(
            '/api/v1/model/visualization/confusion_matrix',
            headers={'Authorization': f'Bearer {trained_model}'},
        )
        body = resp.get_json()
        assert body['code'] == 1001

    def test_visualization_feature_importance_with_model(self, test_client, trained_model):
        """特征重要性（指定 model）：返回 base64 PNG"""
        resp = test_client.get(
            '/api/v1/model/visualization/feature_importance?model=logistic_regression',
            headers={'Authorization': f'Bearer {trained_model}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0

    def test_visualization_invalid_chart_type(self, test_client, trained_model):
        """未知图表类型：返回 1001"""
        resp = test_client.get(
            '/api/v1/model/visualization/nonexistent',
            headers={'Authorization': f'Bearer {trained_model}'},
        )
        body = resp.get_json()
        assert body['code'] == 1001


# ===== 7. 导出模型文件 =====

class TestExportModel:
    """导出模型文件接口测试"""

    def test_export_model_success(self, test_client, trained_model):
        """admin 导出模型：返回二进制文件流"""
        resp = test_client.get(
            '/api/v1/model/export/logistic_regression',
            headers={'Authorization': f'Bearer {trained_model}'},
        )
        assert resp.status_code == 200
        assert 'octet-stream' in resp.content_type
        assert len(resp.data) > 0

    def test_export_nonexistent_model(self, test_client, trained_model):
        """导出不存在的模型：返回 3002"""
        resp = test_client.get(
            '/api/v1/model/export/nonexistent_model',
            headers={'Authorization': f'Bearer {trained_model}'},
        )
        body = resp.get_json()
        assert body['code'] == 3002

    def test_export_user_forbidden(self, test_client, user_token, trained_model):
        """普通 user 导出模型：返回 1003，HTTP 403"""
        resp = test_client.get(
            '/api/v1/model/export/logistic_regression',
            headers={'Authorization': f'Bearer {user_token}'},
        )
        body = resp.get_json()
        assert body['code'] == 1003
        assert resp.status_code == 403

    def test_export_without_token(self, test_client, trained_model):
        """无 token 导出模型：返回 1002"""
        resp = test_client.get('/api/v1/model/export/logistic_regression')
        body = resp.get_json()
        assert body['code'] == 1002


# ===== 8. 导入模型文件 =====

class TestImportModel:
    """导入模型文件接口测试"""

    def test_import_model_success(self, test_client, trained_model):
        """admin 导入模型：先导出再导入，返回 model_name"""
        # 先导出
        export_resp = test_client.get(
            '/api/v1/model/export/logistic_regression',
            headers={'Authorization': f'Bearer {trained_model}'},
        )
        model_bytes = export_resp.data

        # 再导入
        resp = test_client.post(
            '/api/v1/model/import',
            data={'file': (io.BytesIO(model_bytes), 'imported.joblib')},
            content_type='multipart/form-data',
            headers={'Authorization': f'Bearer {trained_model}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert 'model_name' in body['data']

    def test_import_no_file(self, test_client, trained_model):
        """未传文件：返回 1001"""
        resp = test_client.post(
            '/api/v1/model/import',
            content_type='multipart/form-data',
            headers={'Authorization': f'Bearer {trained_model}'},
        )
        body = resp.get_json()
        assert body['code'] == 1001

    def test_import_user_forbidden(self, test_client, user_token, trained_model):
        """普通 user 导入模型：返回 1003，HTTP 403"""
        resp = test_client.post(
            '/api/v1/model/import',
            content_type='multipart/form-data',
            headers={'Authorization': f'Bearer {user_token}'},
        )
        body = resp.get_json()
        assert body['code'] == 1003
        assert resp.status_code == 403

    def test_import_without_token(self, test_client, trained_model):
        """无 token 导入模型：返回 1002"""
        resp = test_client.post('/api/v1/model/import', content_type='multipart/form-data')
        body = resp.get_json()
        assert body['code'] == 1002
