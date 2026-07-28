'''
NL2SQL，自然语言转换到sql

ORM，用python语句实现sql操作，将python对象和数据库表做自动映射，
不需要手动写原生SQL语句，通过面向对象的方式来操作数据库
python类 ——> 数据库数据表
类属性 ——> 数据字段
类实例对象 ——> 数据表中的一行数据example/instance

SQLAlchemy：SQLAlchemy 是 Python 最主流的ORM（对象关系映射）数据库工具库，
专门用来操作 MySQL、SQLite、PostgreSQL 等数据库。
核心作用：不用手写大量原生 SQL 语句，用面向对象的方式操作数据表，兼容性特别强，换数据库不用改业务代码
杜绝SQL注入
代码简洁，面向对象，可读性/可维护性极高
Python后端(django/flask/fastapi/tornado)，爬虫，数据分析项目主流标配ORM框架
'''
import pymysql





