import pymysql

class MySQLUtil:
    def __init__(self):
        self.conn = pymysql.connect(host='localhost',
                                    user='root',
                                    port=3306,
                                    password='123456',
                                    database='test_db',
                                    charset='utf8mb4',
                                    cursorclass=pymysql.cursors.DictCursor)
        self.cursor = self.conn.cursor()
        print("数据库服务已启动")

    def query(self, sql, args=None, one=False):
        self.cursor.execute(sql, args or [])
        if one:
            return self.cursor.fetchone()
        return self.cursor.fetchall()

    def execute(self, sql, args=None):
        self.cursor.execute(sql, args or [])
        self.conn.commit()
        return self.cursor.rowcount

    def close(self):
        self.cursor.close()
        self.conn.close()
        print("数据库连接已关闭")

if __name__ == "__main__":
    db = MySQLUtil()

    sql = "SELECT * FROM users"
    result = db.query(sql)
    print(result)

    db.close()


