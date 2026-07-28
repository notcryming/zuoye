from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, func
from datetime import datetime

engine = create_engine(
	"mysql+pymysql://root:123456@localhost:3306/test_db?charset=utf8mb4")
Base = declarative_base
SessionLoc = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLoc()

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

stu1 = Student(name="张三", age=18, gender="男", score=90.5)
stu2 = Student(name="韩梅梅", age=16, gender="女", score=90.5)
stu3 = Student(id=5, name="赵五", age=19, gender="男", score=80.5)
db.add([stu1, stu2, stu3])
db.commit()
cla1 = ClassTable(class_name="python1班", teacher="李军", student_num=22)
cla2 = ClassTable(class_name="java3班", teacher="王刚", student_num=18)
cla3 = ClassTable(class_name="ai2班", teacher="张雪峰", student_num=30)
cla4 = ClassTable(class_name="c++4班", teacher="孙笑川", student_num=28)
db.add_all([cla1, cla2, cla3, cla4])
db.commit()

one_class = db.query(ClassTable).filter(ClassTable.id==1).first()
print(one_class.class_name, one_class.teacher)
result = db.query(ClassTable).order_by(-ClassTable.student_num).all()
for i in result:
	print(i.class_name,i.teacher,i.student_num)
result = db.query(ClassTable).offset(1).limit(1).all()
for i in result:
    print(i.class_name,i.teacher,i.student_num)

cla = db.query(ClassTable).filter(ClassTable.class_name=="python1班").first()
if cla:
    cla.teacher = "张老师"
    cla.student_num = 40
    db.commit()
cla = db.query(ClassTable).filter(ClassTable.teacher=="王刚").first()
if cla:
    db.delete(cla)
    db.commit()


cla = db.query(ClassTable).filter(ClassTable.class_name=="python1班").first()
if cla:
    cla.teacher = "张老师"
    cla.student_num = 40
    db.commit()
cla = db.query(ClassTable).filter(ClassTable.teacher=="王刚").first()
if cla:
    db.delete(cla)
    db.commit()

total_class = db.query(func.count(ClassTable.id)).scalar()
avg_student = db.query(func.avg(ClassTable.student_num)).scalar()
print(f"总共有{total_class}个班，平均每个班有{avg_student}个学生")



