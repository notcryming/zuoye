# MySQL 课程必备基础SQL语句（适配你当前 student_db 库）
## 一、数据库操作
### 1. 创建数据库
```sql
-- 创建，不存在才创建，utf8mb4支持中文、表情
CREATE DATABASE IF NOT EXISTS student_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
### 2. 查看所有数据库
```sql
SHOW DATABASES;
```
### 3. 切换使用数据库
```sql
USE student_db;
```
### 4. 删除数据库（谨慎使用）
```sql
DROP DATABASE IF EXISTS test_db;
```

---
## 二、数据表操作
### 1. 创建数据表（示例学生表）
```sql
CREATE TABLE IF NOT EXISTS student (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键自增ID',
    name VARCHAR(50) NOT NULL COMMENT '学生姓名',
    age TINYINT COMMENT '年龄',
    score DECIMAL(5,2) COMMENT '分数',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 2. 查看当前库所有表
```sql
SHOW TABLES;
```

### 3. 查看表结构
```sql
DESC student;
```

### 4. 删除数据表
```sql
DROP TABLE IF EXISTS student;
```

---
## 三、增删改查（CRUD 核心，Python SQLAlchemy高频使用）
### 1. 新增数据 INSERT
```sql
-- 插入完整字段
INSERT INTO student(name, age, score) VALUES ('张三', 18, 92.5);

-- 批量插入多条
INSERT INTO student(name, age, score)
VALUES 
('李四', 19, 88),
('王五', 18, 95.5);
```

### 2. 查询数据 SELECT
```sql
-- 查询整张表所有数据
SELECT * FROM student;

-- 查询指定字段
SELECT id,name,score FROM student;

-- 条件查询（年龄大于18）
SELECT * FROM student WHERE age > 18;

-- 排序（分数降序）
SELECT * FROM student ORDER BY score DESC;

-- 分页，只取前2条
SELECT * FROM student LIMIT 2;
```

### 3. 修改数据 UPDATE（必须加WHERE，否则全表修改）
```sql
-- 修改张三的分数
UPDATE student SET score=96 WHERE name='张三';
```

### 4. 删除数据 DELETE（必须加WHERE）
```sql
-- 删除id=3的学生
DELETE FROM student WHERE id=3;
```

---
## 四、用户/权限相关（你刚重置root用到）
```sql
-- 刷新权限
FLUSH PRIVILEGES;

-- 修改root密码为兼容模式
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '123456';
```

---
## 五、辅助常用语句
```sql
-- 查看当前正在使用哪个库
SELECT DATABASE();

-- 退出mysql终端
exit;
```