from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

# 创建数据库引擎
# 格式： mysql+pymysql://用户名:密码@主机:端口/数据库名?编码
engine = create_engine(
    "mysql+pymysql://root:123456@localhost:3306/test_db?charset=utf8mb4",
    echo=True)
# echo=True 打印SQL语句
# 创建模型基类,所有类都继承他
Base = declarative_base()
# 创建会话工厂
SessionLoc = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# 创建会话
db = SessionLoc()

# 用类定义表
class Student(Base):
    __tablename__ = "student"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    name = Column(String(20), nullable=False, comment="姓名")
    age = Column(Integer, nullable=False, default=18, comment="年龄")
    gender = Column(String(10), default="未知", comment="性别")
    score = Column(Float, default=0.0, comment="成绩")
    create_time = Column(DateTime, default=datetime.now, comment="创建时间")

#3.创建数据表
Base.metadata.create_all(bind=engine)
print("数据表创建成功！")

# execute里面可以写SELECT / INSERT / UPDATE / DELETE，就是单纯执行
result = db.execute("SELECT * from users")
print("数据库连接成功！")
for row in result:
    print(row)

if __name__ == "__main__":
    try:
        Base.metadata.create_all(bind=engine)
        print("数据表创建成功！")

        count = db.query(Student).count()
        print("学生表存在", count,"条数据")
    except Exception as e:
        print("数据表创建失败!", e)
    finally:
        db.close()