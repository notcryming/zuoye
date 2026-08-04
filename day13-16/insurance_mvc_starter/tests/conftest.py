"""pytest 全局夹具：测试 Flask 应用 + 内存 SQLite + JWT 令牌 + 测试数据

【设计思路】
1. 在任何 app 模块导入前覆盖环境变量（DATABASE_URL / LLM_API_KEY / MODEL_DIR）
2. 用 StaticPool 替换 engine，使 :memory: SQLite 可跨请求共享
3. 每条用例执行前 drop_all → create_all → init admin/prompt，保证数据隔离
4. admin_token / user_token 夹具自动登录拿 JWT
5. test_excel_bytes 夹具生成 30 行测试 Excel（含正负样本，可分层拆分）
6. trained_model 夹具完成上传→训练全流程，供模型/邮件测试复用
"""
import os
import io
import tempfile

# ====================================================================
#  关键：在任何 app 模块导入前覆盖环境变量
# ====================================================================
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['LLM_API_KEY'] = ''               # 禁用 LLM → 邮件生成降级为 failed
_TEMP_MODEL_DIR = tempfile.mkdtemp(prefix='test_models_')
os.environ['MODEL_DIR'] = _TEMP_MODEL_DIR     # 模型文件存临时目录，不污染生产

# ====================================================================
#  导入 app 模块 + 替换 engine 为 StaticPool
# ====================================================================
import app.core.database as db_module
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# :memory: SQLite 默认每个连接独立，StaticPool 保持单连接跨请求共享
_test_engine = create_engine(
    'sqlite:///:memory:',
    connect_args={'check_same_thread': False},
    poolclass=StaticPool,
)
db_module.engine = _test_engine
db_module.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)

# 此时导入 create_app
# 【关键坑】import app.core.database 会先触发 import app（因为 app.core.database
#   是 app 的子模块），导致 app/__init__.py 在替换前就执行了
#   from app.core.database import engine, SessionLocal，
#   把原始 engine/SessionLocal 绑定到 app 模块命名空间。
#   因此除了替换 db_module 上的属性，还必须替换 app 模块上的同名属性，
#   否则 create_app() 内部的 Base.metadata.create_all(bind=engine) 会用原始 engine，
#   而 get_db() 用的是替换后的 SessionLocal → 表建在错误的引擎上 → no such table。
from app import create_app
import app as _app_module
_app_module.engine = _test_engine
_app_module.SessionLocal = db_module.SessionLocal

from app.core.database import Base

import pandas as pd
import pytest


# ====================================================================
#  夹具：test_client —— 每条用例创建干净 Flask 应用 + 内存数据库
# ====================================================================
@pytest.fixture
def test_client():
    """创建测试 Flask 应用，使用内存 SQLite，每条用例前后自动重建数据表"""
    # 清空所有表（隔离上一条用例的残留数据）
    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)

    # create_app 内部会 create_all + init_admin + init_prompt_template
    app = create_app()
    app.config['TESTING'] = True

    with app.test_client() as client:
        yield client

    # 用例结束后清空
    Base.metadata.drop_all(bind=_test_engine)


# ====================================================================
#  夹具：admin_token —— admin 账号登录 JWT
# ====================================================================
@pytest.fixture
def admin_token(test_client):
    """获取 admin 账号登录 JWT 令牌"""
    resp = test_client.post('/api/v1/auth/login', json={
        'username': 'admin',
        'password': 'admin123',
    })
    body = resp.get_json()
    assert body['code'] == 0, f"admin 登录失败: {body}"
    return body['data']['access_token']


# ====================================================================
#  夹具：user_token —— 普通用户注册+登录 JWT
# ====================================================================
@pytest.fixture
def user_token(test_client):
    """注册并登录普通 user 账号，返回 JWT 令牌"""
    # 注册
    resp = test_client.post('/api/v1/auth/register', json={
        'username': 'testuser',
        'password': 'test123456',
    })
    body = resp.get_json()
    assert body['code'] == 0, f"注册失败: {body}"
    return body['data']['access_token']


# ====================================================================
#  夹具：test_excel_bytes —— 30 行测试 Excel（bytes，可重复使用）
# ====================================================================
@pytest.fixture
def test_excel_bytes():
    """生成 30 行测试客户 Excel 文件的 bytes（含正负样本，可分层拆分）

    字段严格对齐 data_processor.COLUMN_MAP 的原始列名。
    """
    data = {
        'id': list(range(1, 31)),
        'Gender': ['Male', 'Female'] * 15,
        'Age': [25, 30, 35, 40, 45, 50, 55, 60, 28, 33,
                38, 42, 47, 52, 57, 62, 27, 32, 37, 48,
                22, 26, 31, 36, 41, 46, 51, 56, 61, 65],
        'Driving_License': [1] * 30,
        'Region_Code': [28.0, 8.0, 46.0, 41.0, 15.0] * 6,
        'Previously_Insured': [0, 1, 0, 1, 0] * 6,
        'Vehicle_Age': ['< 1 Year', '1-2 Year', '> 2 Years'] * 10,
        'Vehicle_Damage': ['Yes', 'No'] * 15,
        'Annual_Premium': [30000.0, 40000.0, 50000.0, 35000.0, 45000.0] * 6,
        'Policy_Sales_Channel': [152.0, 26.0, 124.0, 160.0, 14.0] * 6,
        'Vintage': [100, 150, 200, 250, 300] * 6,
        # 6 个正样本（Response=1），24 个负样本（Response=0），约 20% 正例率
        'Response': [0, 0, 0, 0, 1, 0, 0, 0, 0, 1,
                     0, 0, 0, 1, 0, 0, 0, 0, 1, 0,
                     0, 0, 1, 0, 0, 0, 0, 1, 0, 0],
    }
    df = pd.DataFrame(data)
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()


# ====================================================================
#  夹具：uploaded_data —— 已上传 Excel 数据（供数据/模型/邮件测试复用）
# ====================================================================
@pytest.fixture
def uploaded_data(test_client, admin_token, test_excel_bytes):
    """已上传测试 Excel 数据，返回 admin_token 供后续操作"""
    resp = test_client.post(
        '/api/v1/data/upload',
        data={'file': (io.BytesIO(test_excel_bytes), 'test.xlsx')},
        content_type='multipart/form-data',
        headers={'Authorization': f'Bearer {admin_token}'},
    )
    body = resp.get_json()
    assert body['code'] == 0, f"上传失败: {body}"
    assert body['data']['imported_count'] == 30
    return admin_token


# ====================================================================
#  夹具：trained_model —— 上传 + 训练完成（供模型评估/预测/邮件测试复用）
# ====================================================================
@pytest.fixture
def trained_model(test_client, uploaded_data, test_excel_bytes):
    """上传数据 + 训练三模型完成，返回 admin_token

    训练后 experiments 表有 3 条记录，is_best 唯一为真，
    data/models 目录下有 3 个 .joblib 文件。
    """
    resp = test_client.post(
        '/api/v1/model/train',
        json={},
        headers={'Authorization': f'Bearer {uploaded_data}'},
    )
    body = resp.get_json()
    assert body['code'] == 0, f"训练失败: {body}"
    assert 'best_model' in body['data']
    assert len(body['data']['results']) == 3
    return uploaded_data


# ====================================================================
#  辅助函数：构造鉴权 headers
# ====================================================================
def auth_headers(token):
    """构造 Authorization Bearer headers"""
    return {'Authorization': f'Bearer {token}'}
