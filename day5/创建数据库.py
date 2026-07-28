import pymysql

# Connect to the database
connection = pymysql.connect(host='localhost',
                             user='root',
                             port=3306,
                             password='123456',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

# 2. 获取游标
cursor = connection.cursor()

# 3. 定义创建数据库SQL
db_name = "job_db"
create_db_sql = f"""
CREATE DATABASE IF NOT EXISTS {db_name}
DEFAULT CHARACTER SET utf8mb4
DEFAULT COLLATE utf8mb4_unicode_ci;
"""

# 4. 执行SQL
cursor.execute(create_db_sql)
print(f"数据库 {db_name} 创建完成（已存在不会报错）")

# 5. 关闭资源
cursor.close()
connection.close()
