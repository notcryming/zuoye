from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, func
from datetime import datetime

# 创建数据库引擎
# 格式： mysql+pymysql://用户名:密码@主机:端口/数据库名?编码
engine = create_engine(
    "mysql+pymysql://root:123456@localhost:3306/test_db?charset=utf8mb4",
    echo=False)
# echo=True 打印SQL语句
# 创建模型基类,所有类都继承他
Base = declarative_base()
# 创建会话工厂
# 打开自动提交以后应该不用手动commit了，虽然偷懒，但是不安全
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

class ClassTable(Base):
    __tablename__ = "class"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    class_name = Column(String(20), nullable=False, unique=True, comment="班级名")
    teacher = Column(String(20), nullable=False, default=18, comment="班主任")
    student_num = Column(Integer, default=0, comment="人数")

#3.创建数据表
Base.metadata.create_all(bind=engine)
print("数据表创建成功！")

# execute里面可以写SELECT / INSERT / UPDATE / DELETE，就是单纯执行
result = db.execute("SELECT * from class")
for row in result:
    print(row)

# cla1 = ClassTable(class_name="java3班", teacher="王刚", student_num=18)
# cla2 = ClassTable(class_name="ai2班", teacher="张雪峰", student_num=30)
# cla3 = ClassTable(class_name="c++4班", teacher="孙笑川", student_num=28)
# db.add_all([cla1, cla2, cla3])
# db.commit()
result = db.query(ClassTable).order_by(-ClassTable.student_num).all()
for i in result:
    print(i.class_name,i.teacher,i.student_num)
result = db.query(ClassTable).offset(1).limit(1).all()
for i in result:
    print(i.class_name,i.teacher,i.student_num)
result = db.query(ClassTable).filter(ClassTable.class_name.like("%Python%")).all()
for i in result:
    print(i.class_name,i.teacher,i.student_num)
result = db.query(func.count(ClassTable.id)).scalar()
print(result)


