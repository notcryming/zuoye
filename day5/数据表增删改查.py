import pymysql
from pymysql.err import OperationalError

# 1. 数据库连接配置（和你现有代码保持一致）
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "port": 3306,
    "database": "test_db",
    "password": "123456",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor  # 查询返回字典，和你输出格式匹配
}

def get_connection():
    """获取数据库连接"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except OperationalError as e:
        print(f"数据库连接失败：{e}")
        return None

# ========== 增 CREATE ==========
def add_user(email, password):
    """新增用户"""
    conn = get_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        sql = "INSERT INTO users (email, password) VALUES (%s, %s)"
        cursor.execute(sql, (email, password))
        conn.commit()  # DML操作必须提交事务
        print(f"新增成功，自增ID：{cursor.lastrowid}")
        return True
    except Exception as e:
        conn.rollback()  # 出错回滚
        print(f"新增失败：{e}")
        return False
    finally:
        cursor.close()
        conn.close()

# ========== 查 READ ==========
def get_all_users():
    """查询全部用户"""
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    result = cursor.fetchall()  # 获取所有数据
    cursor.close()
    conn.close()
    return result

def get_user_by_id(uid):
    """根据ID查询单个用户"""
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (uid,))
    result = cursor.fetchone()  # 获取单条数据
    cursor.close()
    conn.close()
    return result

# ========== 改 UPDATE ==========
def update_user_password(uid, new_pwd):
    """根据ID修改用户密码"""
    conn = get_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        sql = "UPDATE users SET password = %s WHERE id = %s"
        row = cursor.execute(sql, (new_pwd, uid))
        conn.commit()
        print(f"更新影响行数：{row}")
        return row > 0
    except Exception as e:
        conn.rollback()
        print(f"更新失败：{e}")
        return False
    finally:
        cursor.close()
        conn.close()

# ========== 删 DELETE ==========
def delete_user(uid):
    """根据ID删除用户"""
    conn = get_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        sql = "DELETE FROM users WHERE id = %s"
        row = cursor.execute(sql, (uid,))
        conn.commit()
        print(f"删除影响行数：{row}")
        return row > 0
    except Exception as e:
        conn.rollback()
        print(f"删除失败：{e}")
        return False
    finally:
        cursor.close()
        conn.close()

# 主程序测试入口
if __name__ == "__main__":
    # 1. 新增
    add_user("test1@demo.com", "abc123")
    add_user("test2@demo.com", "xyz789")

    # 2. 查询全部
    print("\n所有用户：")
    users = get_all_users()
    for u in users:
        print(u)

    # 3. 单条查询
    print("\n查询ID=1的用户：")
    print(get_user_by_id(1))

    # 4. 修改密码
    update_user_password(1, "newpass666")
    print("\n修改后：")
    print(get_user_by_id(1))

    # 5. 删除用户
    delete_user(2)
    print("\n删除ID=2后全部数据：")
    print(get_all_users())