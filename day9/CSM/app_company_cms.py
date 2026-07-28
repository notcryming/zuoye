import secrets
from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.json.ensure_ascii = False

# 数据库连接到本地文件 cms.db
engine = create_engine('sqlite:///cms.db', connect_args={"check_same_thread": False})
# 创建线程安全的会话工厂
Session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default='user')
    status = Column(String(20), default='active')

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "status": self.status,
        }


class News(Base):
    __tablename__ = 'news'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    content = Column(String, nullable=False)
    category = Column(String(50))
    commit = Column(String(80))
    created_at = Column(DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "commit": self.commit,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }


# 请求结束时清理会话，避免连接泄漏
@app.teardown_appcontext
def remove_session(exception=None):
    Session.remove()

# 创建所有表
Base.metadata.create_all(engine)

# 初始化管理员账号和新闻数据
with Session() as db_session:
    # 初始化管理员账号（如果不存在）
    if not db_session.query(User).filter_by(username='admin').first():
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            status='active'
        )
        db_session.add(admin)
        db_session.commit()

    # 初始化新闻数据（如果表为空）
    if not db_session.query(News).first():
        init_news_list = [
            {"title": "上半年行业运营数据汇总公示", "content": "相关部门已完成本年度上半年各项经营数据统计，包含营收、项目数量、人员配置等明细内容，全体员工可在内网下载查看。", "category": "公告", "commit": "admin", "created_at": "2026-07-20 08:15:22"},
            {"title": "系统后台新版本迭代更新通知", "content": "本次迭代优化了数据排序、文件上传、日志查询三大功能，修复已知5项bug，凌晨两点完成部署升级。", "category": "系统资讯", "commit": "admin", "created_at": "2026-07-20 14:32:10"},
            {"title": "7月线下工作交流会安排说明", "content": "本月28日将开展部门线下交流会议，各小组负责人需要提前整理工作汇报材料按时参会。", "category": "公告", "commit": "admin", "created_at": "2026-07-21 09:05:47"},
            {"title": "最新行业标准解读文档发布", "content": "国家更新了相关行业规范标准，文档附带逐条解析，业务岗位人员务必学习落实新规要求。", "category": "行业动态", "commit": "admin", "created_at": "2026-07-21 16:20:33"},
            {"title": "服务器定期维护时间段提醒", "content": "每周三凌晨0点至2点进行服务器例行维护，期间系统会短暂无法访问，请勿在该时段提交重要数据。", "category": "系统资讯", "commit": "admin", "created_at": "2026-07-21 22:11:06"},
            {"title": "员工夏季防暑福利发放通知", "content": "行政部将于本周内发放夏季防暑物资，各部门统一登记领取，领取清单已放置在行政办公区。", "category": "公告", "commit": "admin", "created_at": "2026-07-22 10:44:19"},
            {"title": "外部合作企业资质核验完成公示", "content": "本年度第二批合作方资质审核工作全部结束，合格企业名单对外公示，合作对接工作正常开启。", "category": "政策资讯", "commit": "admin", "created_at": "2026-07-22 15:18:55"},
            {"title": "数据库备份策略优化方案落地", "content": "调整数据库自动备份频次，增加异地备份机制，进一步保障业务数据安全，运维组已完成全部配置。", "category": "系统资讯", "commit": "admin", "created_at": "2026-07-22 18:30:27"},
            {"title": "八月项目申报通道正式开放", "content": "各类扶持项目申报入口现已开放，申报截止日期为8月15日，逾期系统自动关闭提交端口。", "category": "政策资讯", "commit": "admin", "created_at": "2026-07-23 10:22:41"},
            {"title": "日常数据上报填写规范补充说明", "content": "针对近期上报数据出现的格式错误问题，补充填写规范细则，所有填报人员严格按照新标准提交表单。", "category": "行业动态", "commit": "admin", "created_at": "2026-07-23 15:49:12"},
        ]
        for item in init_news_list:
            news = News(
                title=item["title"],
                content=item["content"],
                category=item["category"],
                commit=item["commit"],
                created_at=datetime.strptime(item["created_at"], "%Y-%m-%d %H:%M:%S"),
            )
            db_session.add(news)
        db_session.commit()



@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "用户名或密码缺失"}), 400
    username = data["username"]
    password = data["password"]
    db_session = Session()
    user = db_session.query(User).filter_by(username=username).first()
    if not user:
        return jsonify({"code": 401, "message": "用户不存在"}), 401
    if not check_password_hash(user.password_hash, password):
        return jsonify({"code": 401, "msg": "密码错误"}), 401
    # 登录成功，设置会话
    user.status = "active"
    db_session.commit()
    session["username"] = username
    session["role"] = user.role
    return jsonify({"code": 200, "msg": "登录成功", "username": username, "role": session["role"]})


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "用户名或密码缺失"}), 400
    username = data["username"]
    password = data["password"]
    db_session = Session()
    if db_session.query(User).filter_by(username=username).first():
        return jsonify({"code": 400, "message": "用户名已存在"}), 400
    password_hash = generate_password_hash(password)
    user = User(
        username=username,
        password_hash=password_hash,
        role="admin",
        status="inactive"
    )
    db_session.add(user)
    db_session.commit()
    return jsonify({"code": 200, "msg": "注册成功"}), 200


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            return jsonify({"code": 401, "msg": "请先登录"}), 401
        # 非 admin 角色返回 403 Forbidden
        if session.get("role") != "admin":
            return jsonify({"code": 403, "msg": "权限不足，需要管理员权限"}), 403
        return f(*args, **kwargs)
    return decorated


@app.route("/", methods=["GET"])
def index():
    db_session = Session()
    # 按 created_at 倒序，取最新 3 条
    top3_news = db_session.query(News).order_by(News.created_at.desc()).limit(3).all()
    result = [n.to_dict() for n in top3_news]
    company_intro = "辰途智科专注企业官网定制与自研 CMS 内容管理系统研发，为各类企业提供品牌官网搭建、后台内容托管、系统私有化部署与全站安全运维服务，用轻量化数字化工具，简化企业线上内容运营工作。"
    return render_template("index.html", company_intro=company_intro, top3_news=result)


@app.route("/api/home", methods=["GET"])
def api_home():
    """首页数据 JSON 接口（原 / 接口行为）"""
    db_session = Session()
    top3_news = db_session.query(News).order_by(News.created_at.desc()).limit(3).all()
    result = [n.to_dict() for n in top3_news]
    return jsonify({
        "公司简介": "辰途智科专注企业官网定制与自研 CMS 内容管理系统研发，为各类企业提供品牌官网搭建、后台内容托管、系统私有化部署与全站安全运维服务，用轻量化数字化工具，简化企业线上内容运营工作。",
        "list_news": result
    })


@app.route("/news", methods=["GET"])
def news_page():
    """新闻列表页"""
    return render_template("news_list.html")


@app.route("/news/<int:id>", methods=["GET"])
def news_detail_page(id):
    """新闻详情页"""
    db_session = Session()
    news = db_session.query(News).get(id)
    if not news:
        return render_template("news_detail.html", news=None, error="新闻不存在"), 404
    return render_template("news_detail.html", news=news.to_dict())


@app.route("/login", methods=["GET"])
def login_page():
    """登录页"""
    if session.get("role") == "admin":
        return redirect(url_for("admin_page"))
    return render_template("login.html")


@app.route("/admin", methods=["GET"])
def admin_page():
    """后台管理页"""
    if session.get("role") != "admin":
        return redirect(url_for("login_page"))
    return render_template("admin.html", username=session.get("username"))


@app.route("/api/news", methods=["GET"])
def list_news():
    db_session = Session()
    all_news = db_session.query(News).order_by(News.created_at.desc()).all()
    result = [n.to_dict() for n in all_news]
    return jsonify({"code": 200, "data": result})


@app.route("/api/news/<int:id>", methods=["GET"])
def get_news(id):
    db_session = Session()
    news = db_session.query(News).get(id)
    if not news:
        return jsonify({"code": 404, "msg": "新闻不存在"}), 404
    return jsonify({"code": 200, "data": news.to_dict()})



@app.route("/admin/news", methods=["POST"])
@login_required
def upload_news():
    data = request.get_json()
    if not data or not data.get("title") or not data.get("content"):
        return jsonify({"code": 400, "msg": "标题和内容不能为空"}), 400

    db_session = Session()
    news = News(
        title=data['title'],
        content=data['content'],
        category=data.get('category', ''),
        commit=session['username'],
        created_at=datetime.now()
    )
    db_session.add(news)
    db_session.commit()
    return jsonify({"code": 200, "msg": "新闻上传成功", "data": news.to_dict()}), 200


@app.route("/admin/news/<int:id>", methods=["DELETE"])
@login_required
def delete_news(id):
    db_session = Session()
    news = db_session.query(News).get(id)
    if not news:
        return jsonify({"code": 404, "msg": "新闻不存在"}), 404
    db_session.delete(news)
    db_session.commit()
    return jsonify({"code": 200, "msg": "删除成功"}), 200



@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return jsonify({"code": 200, "msg": "已成功退出"})



if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5005, debug=True)
