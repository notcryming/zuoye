import requests
import random
import time
import csv
from requests.exceptions import RequestException
from lxml import etree
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, String, Integer, Text
from sqlalchemy.orm import declarative_base, sessionmaker

# 所有类要继承的基类
Base = declarative_base()


class Gov_news(Base):
    __tablename__ = 'gov_news'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)
    publish_time = Column(String(100), nullable=False)
    link = Column(String(200))


# 创建SQLite数据库引擎
engine = create_engine('sqlite:///gov_news.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


# 发起html请求，并返回网页源代码和状态码
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
            response.encoding = 'utf-8'
            return response.text, response.status_code
        else:
            print(f"请求失败，状态码: {response.status_code}")
            return None, response.status_code
    except RequestException as e:
        print(f"访问 {url} 出现网络/请求异常：{e}")
        return None, 0


# 使用XPath解析网页源代码
def parse_html(html):
    news_list = []
    if not html:
        return news_list
    tree = etree.HTML(html)
    # 定位每个li节点
    items = tree.xpath('//div[@class="news_box"]//li')
    for item in items:
        title_list = item.xpath('.//h4/a/text()')
        title = title_list[0].strip() if title_list else ''
        link_list = item.xpath('.//h4/a/@href')
        link = link_list[0] if link_list else ''
        date_list = item.xpath('.//span[@class="date"]/text()')
        publish_time = date_list[0].strip() if date_list else ''
        news_list.append({
            'title': title,
            'publish_time': publish_time,
            'link': link
        })
    return news_list


# 使用BeautifulSoup解析网页源代码
def parse_html_bs(html):
    news_list = []
    if not html:
        return news_list
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select('div.news_box li')
    for item in items:
        a_tag = item.select_one('h4 a')
        title = a_tag.get_text(strip=True) if a_tag else ''
        link = a_tag['href'] if a_tag and a_tag.has_attr('href') else ''
        date_tag = item.select_one('span.date')
        publish_time = date_tag.get_text(strip=True) if date_tag else ''
        news_list.append({
            'title': title,
            'publish_time': publish_time,
            'link': link
        })
    return news_list


# 保存数据到数据库
def save_to_db(news_list):
    session = Session()
    try:
        saved_count = 0
        for news in news_list:
            if not news['title'] or not news['publish_time']:
                continue
            existing = session.query(Gov_news).filter_by(title=news['title'], publish_time=news['publish_time']).first()
            if not existing:
                new_news = Gov_news(title=news['title'], publish_time=news['publish_time'], link=news['link'])
                session.add(new_news)
                saved_count += 1
        session.commit()
        print(f"成功保存 {saved_count} 条新闻到数据库（过滤 {len(news_list) - saved_count} 条空值或重复数据）")
    except Exception as e:
        session.rollback()
        print(f"保存到数据库失败: {e}")
    finally:
        session.close()


# 批量爬取新闻
def crawl_news(x, y):
    urls = [f"https://www.gov.cn/toutiao/liebiao/home_{i}.htm" for i in range(x, y+1)]
    all_news = []
    for url in urls:
        html, status_code = get_html(url)
        if status_code == 403:
            print("遇到403状态码，被服务器拒绝访问，终止抓取")
            return
        if html:
            news = parse_html(html)
            all_news.extend(news)
            print(f"从 {url} 解析到 {len(news)} 条新闻")
        sleep_time = random.uniform(2, 4)
        print(f"休眠 {sleep_time:.2f} 秒")
        time.sleep(sleep_time)
    if all_news:
        save_to_db(all_news)
        print(f"爬取完成，共获取 {len(all_news)} 条新闻")
    else:
        print("未获取到任何新闻数据")


# 展示数据库中的新闻
def show_news():
    session = Session()
    try:
        news_list = session.query(Gov_news).all()
        if news_list:
            print(f"\n数据库中共有 {len(news_list)} 条新闻：")
            for i, news in enumerate(news_list, 1):
                print(f"\n{i}. {news.title}")
                print(f"   发布时间: {news.publish_time}")
                print(f"   链接: {news.link}")
        else:
            print("数据库中暂无数据，请先爬取")
    finally:
        session.close()


# 导出数据库数据为CSV文件
def export_csv():
    session = Session()
    try:
        news_list = session.query(Gov_news).all()
        if not news_list:
            print("数据库中暂无数据，无法导出")
            return
        filename = "gov_news.csv"
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['序号', '标题', '发布时间', '链接'])
            for i, news in enumerate(news_list, 1):
                writer.writerow([i, news.title, news.publish_time, news.link])
        print(f"成功导出 {len(news_list)} 条新闻到 {filename}")
    except Exception as e:
        print(f"导出CSV失败: {e}")
    finally:
        session.close()


def main():
    while True:
        print("\n" + "="*40)
        print("        政府网新闻爬虫系统")
        print("="*40)
        print("1. 单页抓取")
        print("2. 批量抓取")
        print("3. 显示数据库中的新闻")
        print("4. 导出为CSV文件")
        print("5. XPath与BeautifulSoup对比")
        print("6. 退出系统")
        print("="*40)
        choice = input("请输入选择（1-6）：")
        
        if choice == '1':
            while True:
                try:
                    page = int(input("请输入要抓取的页码："))
                    if page < 1:
                        print("页码必须大于等于1")
                        continue
                    break
                except ValueError:
                    print("输入格式错误！请输入一个数字")
                    continue
            crawl_news(page, page)
        elif choice == '2':
            while True:
                try:
                    print("要爬取从x页到y页的数据，x，y？(输入用空格分隔)：", end="")
                    x, y = map(int, input().split())
                    if x < 1 or x > y:
                        print("页码范围不合法，x 必须大于等于1且不大于 y")
                        continue
                    break
                except ValueError:
                    print("输入格式错误！请确保输入两个用空格分隔的数字，例如：1 2")
                    continue
            crawl_news(x, y)
        elif choice == '3':
            show_news()
        elif choice == '4':
            export_csv()
        elif choice == '5':
            print("\n--- XPath 与 BeautifulSoup 对比 ---")
            url = "https://www.gov.cn/toutiao/liebiao/home_3.htm"
            html, status_code = get_html(url)
            if status_code == 403:
                print("遇到403状态码，被服务器拒绝访问")
                continue
            if html:
                xpath_news = parse_html(html)
                bs_news = parse_html_bs(html)
                print(f"\nXPath 解析结果：{len(xpath_news)} 条")
                print(f"BeautifulSoup 解析结果：{len(bs_news)} 条")
                print("\n两者区别：")
                print("  1. XPath 使用路径表达式定位元素，语法简洁，速度快")
                print("  2. BeautifulSoup 使用 CSS 选择器或find方法，上手简单")
                print("  3. XPath 适合复杂的层级定位，BeautifulSoup 适合简单选择")
                print("  4. lxml(XPath底层) 解析速度比 BeautifulSoup 快")
                print("  5. BeautifulSoup 对不规范 HTML 容错性更好")
        elif choice == '6':
            print("退出系统")
            break
        else:
            print("无效输入，请输入1-6之间的数字")


if __name__ == "__main__":
    main()