import requests
from requests.exceptions import RequestException
from lxml import etree
from sqlalchemy import create_engine, Column, String, Integer, Text
from sqlalchemy.orm import declarative_base, sessionmaker
import pymysql

# 先创建库，如果已存在就不创建
connection = pymysql.connect(host='localhost',
                             user='root',
                             port=3306,
                             password='123456',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

cursor = connection.cursor()

db_name = "quotes_db"
create_db_sql = f"""
CREATE DATABASE IF NOT EXISTS {db_name}
DEFAULT CHARACTER SET utf8mb4
DEFAULT COLLATE utf8mb4_unicode_ci;
"""

cursor.execute(create_db_sql)
cursor.close()
connection.close()
# 所有类要继承的基类
Base = declarative_base()

class Quote(Base):
    __tablename__ = 'quotes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    author = Column(String(100), nullable=False)
    tags = Column(String(200))


# 数据库配置字典
DB_CONFIG = {
    'sqlite': 'sqlite:///quotes.db',
    'mysql': 'mysql+pymysql://root:123456@localhost:3306/quotes_db?charset=utf8mb4'
}

# 已创建的引擎缓存
_engines = {}


def get_engine(db_type):
    if db_type not in DB_CONFIG:
        raise ValueError(f"不支持的数据库类型: {db_type}")
    
    if db_type not in _engines:
        engine = create_engine(DB_CONFIG[db_type])
        Base.metadata.create_all(engine)
        # 创建键值对，通过数据库名访问对应的engine
        _engines[db_type] = engine
    return _engines[db_type]


def get_session(db_type):
    engine = get_engine(db_type)
    return sessionmaker(bind=engine)()


# 发起html请求，并返回网页源代码
def get_html(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    print(f"请求URL: {url}")
    print(f"请求headers: {headers}")
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            print(f"请求成功，状态码: {response.status_code}")
            return response.text
        else:
            print(f"请求失败，状态码: {response.status_code}")
            return None
    except RequestException as e:
        print(f"访问 {url} 出现网络/请求异常：{e}")
        return None


# 提取网页源代码中我们需要的部分
def parse_html_xpath(html):
    quotes = []
    if not html:
        return quotes
    tree = etree.HTML(html)
    quote_items = tree.xpath('//div[@class="quote"]')
    '''
    <div class="row">
    <div class="col-md-8">
    <div class="quote" itemscope itemtype="http://schema.org/CreativeWork">
        <span class="text" itemprop="text">“The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking.”</span>
        <span>by <small class="author" itemprop="author">Albert Einstein</small>
        <a href="/author/Albert-Einstein">(about)</a>
        </span>
        <div class="tags">
            Tags:
            <meta class="keywords" itemprop="keywords" content="change,deep-thoughts,thinking,world" /    > 
            <a class="tag" href="/tag/change/page/1/">change</a>
            <a class="tag" href="/tag/deep-thoughts/page/1/">deep-thoughts</a>
            <a class="tag" href="/tag/thinking/page/1/">thinking</a>
            <a class="tag" href="/tag/world/page/1/">world</a>
        </div>
    </div>
    '''
    for item in quote_items:
        # 拿到手的都是字符串类型
        content_list = item.xpath('.//span[@class="text"]/text()')
        content = content_list[0] if content_list else ''
        author_list = item.xpath('.//small[@class="author"]/text()')
        author = author_list[0] if author_list else ''
        tags = item.xpath('.//a[@class="tag"]/text()')
        quotes.append({
            # strip()去掉字符串首位的空格
            'content': content.strip(),
            'author': author.strip(),
            # 用,把列表拼成字符串
            'tags': ','.join(tags)
        })
    return quotes


# 保存数据到数据库
def save_to_db(quotes, db_type='sqlite'):
    session = get_session(db_type)
    try:
        for quote in quotes:
            existing = session.query(Quote).filter_by(content=quote['content'], author=quote['author']).first()
            if not existing:
                new_quote = Quote(content=quote['content'], author=quote['author'], tags=quote['tags'])
                session.add(new_quote)
        session.commit()
        print(f"成功保存 {len(quotes)} 条名言到 {db_type} 数据库")
    except Exception as e:
        session.rollback()
        print(f"保存到 {db_type} 数据库失败: {e}")
    finally:
        session.close()


# 批量操作爬数据
def crawl_quotes(x, y, db_type='sqlite'):
    '''
    urls = ["http://quotes.toscrape.com/page/1/",
            "http://quotes.toscrape.com/page/2/"]
    '''
    urls = [f"http://quotes.toscrape.com/page/{i}/" for i in range(x, y+1)]
    all_quotes = []
    for url in urls:
        html = get_html(url)
        if html:
            quotes = parse_html_xpath(html)
            all_quotes.extend(quotes)
            print(f"从 {url} 解析到 {len(quotes)} 条名言")
    if all_quotes:
        save_to_db(all_quotes, db_type)
        print(f"爬取完成，共获取 {len(all_quotes)} 条名言")
    else:
        print("未获取到任何名言数据")


# 展示数据
def show_quotes(db_type='sqlite'):
    session = get_session(db_type)
    try:
        quotes = session.query(Quote).all()
        if quotes:
            print(f"\n{db_type} 数据库中共有 {len(quotes)} 条名言：")
            for i, quote in enumerate(quotes, 1):
                print(f"\n{i}. {quote.content}")
                print(f"   —— {quote.author}")
                if quote.tags:
                    print(f"   标签: {quote.tags}")
        else:
            print(f"{db_type} 数据库中暂无数据，请先爬取")
    finally:
        session.close()


def select_database():
    while True:
        print("\n请选择数据库：")
        print("1. SQLite")
        print("2. MySQL")
        print("0. 返回上级菜单")
        choice = input("请输入选择（0/1/2）：")
        
        if choice == '1':
            return 'sqlite'
        elif choice == '2':
            return 'mysql'
        elif choice == '0':
            return None
        else:
            print("无效输入，请重新选择")


def main():
    while True:
        print("\n" + "="*40)
        print("        名人名言爬虫系统")
        print("="*40)
        print("1. 爬取数据")
        print("2. 显示数据库中的数据")
        print("3. 退出系统")
        print("="*40)
        choice = input("请输入选择（1/2/3）：")
        
        if choice == '1':
            db_type = select_database()
            if db_type is None:
                continue
            while True:
                try:
                    print("要爬取从x页到y页的数据，x，y？(输入用空格分隔)：", end="")
                    x, y = map(int, input().split())
                    break
                except ValueError:
                    print("输入格式错误！请确保输入两个用空格分隔的数字，例如：1 2")
                    continue
            crawl_quotes(x, y, db_type)
        elif choice == '2':
            db_type = select_database()
            if db_type is None:
                continue
            show_quotes(db_type)
        elif choice == '3':
            print("退出系统")
            break
        else:
            print("无效输入，请输入1、2或3")


if __name__ == "__main__":
    main()