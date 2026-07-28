import pymysql

conn = pymysql.connect( host="192.168.0.56",
                        port=3306,
                        user="root",
                        password="123456",
                        database="student_db",
                        charset="utf8mb4")


cursor = conn.cursor()

cursor.execute("SELECT * FROM student;")
print(cursor.fetchall())

cursor.close()
conn.close()