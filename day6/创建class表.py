from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime

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
class ClassTable(Base):
    __tablename__ = "class"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    class_name = Column(String(20), nullable=False, unique=True, comment="班级名")
    teacher = Column(String(20), nullable=False, default=18, comment="班主任")
    student_num = Column(Integer, default=0, comment="人数")

#3.创建数据表
Base.metadata.create_all(bind=engine)
print("数据表创建成功！")



