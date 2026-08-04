"""认证模块接口测试

覆盖端点：
1. POST /api/v1/auth/register   注册
2. POST /api/v1/auth/login      登录
3. GET  /api/v1/auth/me         获取当前用户
4. POST /api/v1/auth/logout     登出
5. GET  /api/v1/auth/userlist   用户列表（admin）
6. PUT  /api/v1/auth/profile    修改用户名
7. PUT  /api/v1/auth/password   修改密码

测试维度：正常流程 + 用户名重复 + 密码错误 + 无 token + 参数缺失 + 权限拦截
"""
import pytest


# ===== 1. 注册 =====

class TestRegister:
    """注册接口测试"""

    def test_register_success(self, test_client):
        """正常注册：返回 JWT + user 信息，role 固定为 user"""
        resp = test_client.post('/api/v1/auth/register', json={
            'username': 'newuser',
            'password': 'pass123456',
        })
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert 'access_token' in body['data']
        assert body['data']['token_type'] == 'bearer'
        assert body['data']['user']['username'] == 'newuser'
        assert body['data']['user']['role'] == 'user'

    def test_register_duplicate(self, test_client):
        """用户名重复：admin 已存在，再注册返回 1004"""
        resp = test_client.post('/api/v1/auth/register', json={
            'username': 'admin',
            'password': 'pass123456',
        })
        body = resp.get_json()
        assert body['code'] == 1004
        assert resp.status_code == 400

    def test_register_short_password(self, test_client):
        """密码不足 6 位：Pydantic 校验失败返回 1001"""
        resp = test_client.post('/api/v1/auth/register', json={
            'username': 'shortpw',
            'password': '123',
        })
        body = resp.get_json()
        assert body['code'] == 1001
        assert resp.status_code == 400

    def test_register_missing_fields(self, test_client):
        """请求体缺字段：Pydantic 校验失败返回 1001"""
        resp = test_client.post('/api/v1/auth/register', json={})
        body = resp.get_json()
        assert body['code'] == 1001
        assert resp.status_code == 400


# ===== 2. 登录 =====

class TestLogin:
    """登录接口测试"""

    def test_login_admin_success(self, test_client):
        """admin 登录：返回 JWT，role=admin"""
        resp = test_client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123',
        })
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert 'access_token' in body['data']
        assert body['data']['user']['username'] == 'admin'
        assert body['data']['user']['role'] == 'admin'

    def test_login_wrong_password(self, test_client):
        """密码错误：返回 1002，HTTP 401"""
        resp = test_client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'wrongpassword',
        })
        body = resp.get_json()
        assert body['code'] == 1002
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, test_client):
        """用户不存在：返回 1002，HTTP 401"""
        resp = test_client.post('/api/v1/auth/login', json={
            'username': 'ghost',
            'password': 'pass123456',
        })
        body = resp.get_json()
        assert body['code'] == 1002
        assert resp.status_code == 401

    def test_login_missing_fields(self, test_client):
        """请求体缺字段：返回 1001"""
        resp = test_client.post('/api/v1/auth/login', json={})
        body = resp.get_json()
        assert body['code'] == 1001
        assert resp.status_code == 400


# ===== 3. 获取当前用户 =====

class TestMe:
    """获取当前用户信息测试"""

    def test_me_success(self, test_client, admin_token):
        """带 token 访问 /me：返回用户信息"""
        resp = test_client.get(
            '/api/v1/auth/me',
            headers={'Authorization': f'Bearer {admin_token}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert body['data']['user']['username'] == 'admin'
        assert body['data']['user']['role'] == 'admin'

    def test_me_without_token(self, test_client):
        """无 token 访问 /me：返回 1002，HTTP 401"""
        resp = test_client.get('/api/v1/auth/me')
        body = resp.get_json()
        assert body['code'] == 1002
        assert resp.status_code == 401

    def test_me_invalid_token(self, test_client):
        """无效 token 访问 /me：返回 1002，HTTP 401"""
        resp = test_client.get(
            '/api/v1/auth/me',
            headers={'Authorization': 'Bearer invalid.token.here'},
        )
        body = resp.get_json()
        assert body['code'] == 1002
        assert resp.status_code == 401


# ===== 4. 登出 =====

class TestLogout:
    """登出接口测试"""

    def test_logout_success(self, test_client, admin_token):
        """带 token 登出：返回成功消息"""
        resp = test_client.post(
            '/api/v1/auth/logout',
            headers={'Authorization': f'Bearer {admin_token}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert '登出' in body['data']['msg']

    def test_logout_without_token(self, test_client):
        """无 token 登出：返回 1002，HTTP 401"""
        resp = test_client.post('/api/v1/auth/logout')
        body = resp.get_json()
        assert body['code'] == 1002
        assert resp.status_code == 401


# ===== 5. 用户列表（admin）=====

class TestUserList:
    """用户列表接口测试：RBAC 权限校验"""

    def test_userlist_admin(self, test_client, admin_token):
        """admin 访问用户列表：返回用户数组"""
        resp = test_client.get(
            '/api/v1/auth/userlist',
            headers={'Authorization': f'Bearer {admin_token}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert isinstance(body['data'], list)
        assert len(body['data']) >= 1
        assert body['data'][0]['username'] == 'admin'

    def test_userlist_user_forbidden(self, test_client, user_token):
        """普通 user 访问用户列表：返回 1003，HTTP 403"""
        resp = test_client.get(
            '/api/v1/auth/userlist',
            headers={'Authorization': f'Bearer {user_token}'},
        )
        body = resp.get_json()
        assert body['code'] == 1003
        assert resp.status_code == 403

    def test_userlist_without_token(self, test_client):
        """无 token 访问用户列表：返回 1002，HTTP 401"""
        resp = test_client.get('/api/v1/auth/userlist')
        body = resp.get_json()
        assert body['code'] == 1002
        assert resp.status_code == 401


# ===== 6. 修改用户名 =====

class TestProfile:
    """修改用户名接口测试"""

    def test_profile_update_username(self, test_client, user_token):
        """修改用户名：返回新 token + 新用户名"""
        resp = test_client.put(
            '/api/v1/auth/profile',
            json={'username': 'renamed_user', 'password': 'test123456'},
            headers={'Authorization': f'Bearer {user_token}'},
        )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 0
        assert body['data']['user']['username'] == 'renamed_user'

    def test_profile_duplicate_username(self, test_client, user_token):
        """修改为已存在的用户名：返回 1004"""
        resp = test_client.put(
            '/api/v1/auth/profile',
            json={'username': 'admin', 'password': 'test123456'},
            headers={'Authorization': f'Bearer {user_token}'},
        )
        body = resp.get_json()
        assert body['code'] == 1004
        assert resp.status_code == 400

    def test_profile_without_token(self, test_client):
        """无 token 修改用户名：返回 1002，HTTP 401"""
        resp = test_client.put(
            '/api/v1/auth/profile',
            json={'username': 'whatever', 'password': 'test123456'},
        )
        body = resp.get_json()
        assert body['code'] == 1002
        assert resp.status_code == 401


# ===== 7. 修改密码 =====

class TestPassword:
    """修改密码接口测试"""

    def test_password_without_token(self, test_client):
        """无 token 修改密码：返回 1002，HTTP 401"""
        resp = test_client.put(
            '/api/v1/auth/password',
            json={'username': 'admin', 'password': 'admin123'},
        )
        body = resp.get_json()
        assert body['code'] == 1002
        assert resp.status_code == 401

    def test_password_missing_fields(self, test_client, admin_token):
        """请求体缺字段：Pydantic 校验失败返回 1001"""
        resp = test_client.put(
            '/api/v1/auth/password',
            json={},
            headers={'Authorization': f'Bearer {admin_token}'},
        )
        body = resp.get_json()
        assert body['code'] == 1001
        assert resp.status_code == 400
