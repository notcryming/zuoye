from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime
import asyncio
from sqlalchemy import select
from sqlalchemy import create_engine

# 1. 异步引擎创建
# 注意：驱动从pymysql改成aiomysql，协议也用mysql+变成mysql+aiomysql
engine = create_async_engine(
    "mysql+aiomysql://root:123456@localhost:3306/job_db?charset=utf8mb4",
    echo=False
    )
# 异步会话工厂，需要指定class_=AsyncSession
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
# 基类，所有类的父类
Base = declarative_base()

# 2.定义模型
class JobPost(Base):
    __tablename__ = "job_post"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    title = Column(String(100), nullable=False, comment="职位名称")
    company = Column(String(100), nullable=False, comment="公司名称")
    salary_min = Column(Float, default=0, comment="最低薪资(k)")
    salary_max = Column(Float, default=0, comment="最高薪资(k)")
    experience = Column(String(50), default="不限", comment="经验要求")
    jd_text = Column(Text, comment="职位描述原文")
    vector_id = Column(String(100), comment="关联向量ID")
    create_time = Column(DateTime, default=datetime.now, comment="创建时间")

    def __repr__(self):
        return f"<JobPost(self.title)@{self.company}>"


# 3.异步建表
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("数据表创建成功！")


# 4.异步插入数据

async def insert_job(lst):
    """单批次异步插入一批JobPost对象"""
    async with AsyncSessionLocal() as db:
        try:
            db.add_all(lst)
            await db.commit()
        except Exception as e:
            await db.rollback()
            print(f"批次插入失败：{e}")
            raise e

async def batch_insert_job(lst):
    tasks = []
    for i in range(0, len(lst), 100):
        chunk_jobs = lst[i:i + 100]
        tasks.append(insert_job(chunk_jobs))
    start = datetime.now()
    await asyncio.gather(*tasks)
    end = datetime.now()
    return end - start

# 5.异步查询数据
async def query_jobs():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(JobPost))
        jobs = result.scalars().all()
        print(f"共{len(jobs)}条数据")
        for job in jobs:
            print(job)
        return jobs


def generator_jobs(count=50000):
    titles = ["Python后端开发工程师", "Java服务端开发工程师", "前端开发工程师（Vue/React）", "软件测试工程师",
        "自动化测试开发", "运维工程师", "云原生运维开发", "大数据开发工程师", "机器学习算法工程师",
        "计算机视觉算法工程师", "网络安全工程师", "渗透测试工程师", "嵌入式开发工程师", "Go语言后端开发",
        "数据库开发工程师", "全栈开发工程师", "数据分析师", "AI大模型应用开发", "芯片研发工程师",
        "运维监控开发", "产品经理（IT互联网）", "软件实施工程师", "爬虫开发工程师", "区块链开发工程师",
        "游戏客户端开发", "游戏服务端开发", "前端架构师", "后端架构师", "信息安全运维", "数据仓库开发工程师"]
    companies = [
        "腾讯", "字节跳动", "阿里巴巴", "百度", "华为", "小米", "美团", "京东",
        "网易", "快手", "哔哩哔哩", "拼多多", "滴滴", "携程", "360", "金山软件",
        "用友网络", "科大讯飞", "海康威视", "商汤科技", "旷视科技", "阿里云", "腾讯云",
        "深信服", "浪潮信息", "中兴通讯", "vivo", "OPPO", "理想汽车", "小鹏汽车"]
    experiences = ["1-3年", "3-5年", "5年以上", "不限"]
    jd_templates = [
        "岗位{i}：需要掌握Python、MySQL、Redis等技术，有Web开发经验优先...",
        "岗位{i}：负责Java微服务开发，熟悉Spring Cloud、Docker、K8s...",
        "岗位{i}：负责前端产品迭代，精通Vue3/React、TypeScript...",
        "岗位{i}：负责推荐算法优化，熟悉机器学习、深度学习框架...",
    ]
    jobs = []
    for i in range(count):
        jobs.append(JobPost(
            title=f"{titles[i % len(titles)]}-{i}",
            company=f"{companies[i % len(companies)]}-部门{i}",
            salary_min=10 + (i % 25),
            salary_max=20 + (i % 30),
            experience=experiences[i % len(experiences)],
            jd_text=jd_templates[i % len(jd_templates)].format(i=i)
        ))
    return jobs


def sync_batch_insert(jobs):
    """同步串行批量插入（与异步相同的批次大小，公平对比）"""
    sync_engine = create_engine(
        "mysql+pymysql://root:123456@localhost:3306/job_db?charset=utf8mb4",
        echo=False)
    SessionLoc = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
    db = SessionLoc()
    try:
        start = datetime.now()
        for i in range(0, len(jobs), 100):
            chunk = jobs[i:i + 100]
            db.add_all(chunk)
            db.commit()
        end = datetime.now()
        return end - start
    finally:
        db.close()
        sync_engine.dispose()


# ================主函数=================
async def main():
    try:
        # 1. 建表
        await init_db()
        jobs = generator_jobs()

        # 异步插入
        time1 = await batch_insert_job(jobs)

        # 同步插入（使用asyncio.to_thread避免阻塞事件循环）
        time2 = await asyncio.to_thread(sync_batch_insert, jobs)

        print(f"异步耗时：{time1}")
        print(f"同步耗时：{time2}")
        print(f"比例：{time2/time1}")

        # 2. 查询数据
        print("\n查询所有岗位数据==========")
        # await query_jobs()
    finally:
        # 3. 关闭引擎连接
        await engine.dispose()
        print("数据库引擎已关闭")


if __name__ == "__main__":
    asyncio.run(main())


