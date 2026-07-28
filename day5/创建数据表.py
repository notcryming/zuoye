import pymysql

# Connect to the database
connection = pymysql.connect(host='localhost',
                             user='root',
                             port=3306,
                             database='test_db',
                             password='123456',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

# 2. 获取游标，相当于已经打开数据库了
cursor = connection.cursor()

create_table_sql='''
CREATE TABLE IF NOT EXISTS `users` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `email` varchar(255) COLLATE utf8_bin NOT NULL,
    `password` varchar(255) COLLATE utf8_bin NOT NULL,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin AUTO_INCREMENT=1 ;
'''

# 4. 执行SQL，里面直接写命令其实也是可以的
cursor.execute(create_table_sql)

# ---------------------- 第二步：查看当前库中所有数据表 ----------------------
cursor.execute("SHOW TABLES;")
table_list = cursor.fetchall()
print("\n当前数据库里的所有表：")
for table in table_list:
    print(table)

# ---------------------- 拓展：查看表结构详情 ----------------------
cursor.execute("DESC users;")
table_struct = cursor.fetchall()
print("\nuser 表结构详情：")
for field in table_struct:
    print(field)


# 5. 关闭资源
cursor.close()
connection.close()
