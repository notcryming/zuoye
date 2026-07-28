'''
常见字段类型：
Integer:int(主键,数字)
String:varchar字符串(姓名,手机号)
Float:float浮点数(分数,薪资)
Datetime:datetime时间类型
常用字段约束：
primary_key = True:主键,唯一标识
autoincrement=True:自增
nullable=False:非空约束
unique=True:唯一约束
default=默认值:默认值
数据库创建和删除的核心方法：
Base.metadata.create_all(bind=engine):创建所有未存在的数据表
Base.metadata.drop_all(bind=engine):删除所有表,实际生产禁用
创建模型对象->db.add(对象)添加到对话->db.commit()提交事务
批量新增:db.add_all([对象1,对象2])
db.query(模型).all():查询所有属于,返回一个list
db.query(模型).first():查询第一条数据
db.query(模型).get(主键值):通过主键来查询单条数据
filter(模型.字段==值):条件查询
filter_by(字段=值):简易条件查询(匹配)
例:result = db.query(Student).filter(Student.name == "李四") .all()
          = db.query(Student).filter_by(name = "李四") .all()
大于、小于、模糊、不等于、or、多条件、联表查询:用filter
复杂业务优先用filter_by,不会受阻
数据修改需要先查询数据,再直接复制修改字段,commit提交
数据删除要查询到对象,db.delete(对象),commit
多条sql命令操作数据必须一起成功，一起失败，有任意一条失败时，需要做回滚操作db.rollback()
排序:order_by(字段)正序/order_by(-字段)反序
偏移量offset,limit，模糊查询.like("%%")，聚合统计func.count,func.avg,.scalar()
异步
execute()是直接把原始sql语句放进去执行，和面向对象的实现不同
'''