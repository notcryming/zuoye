from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime
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

# stu1 = Student(id=5, name="赵五", age=19, gender="男", score=80.5)
# db.add(stu1)
# db.commit()
# cla1 = ClassTable(class_name="python1班", teacher="李军", student_num=22)
# cla2 = ClassTable(class_name="java3班", teacher="王刚", student_num=18)
# db.add_all([cla1, cla2])
# db.commit()

# execute里面可以写SELECT / INSERT / UPDATE / DELETE，就是单纯执行
result = db.execute("SELECT * from class")
for row in result:
    print(row)

all_classes = db.query(ClassTable).all()
print("所有班级：")
for i in all_classes:
    print(i.class_name, i.teacher)
print("主键为1的班级：")
one_class = db.query(ClassTable).filter(ClassTable.id==1).all()
print(one_class[0].class_name, one_class[0].teacher)
print("人数大于0的班级：")
notnone_class = db.query(ClassTable).filter(ClassTable.student_num>0).all()
for i in notnone_class:
    print(i.class_name, i.teacher)




