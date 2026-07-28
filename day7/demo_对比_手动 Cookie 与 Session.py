# demo_对比_手动 Cookie 与 Session.py
# 演示 requests 中“手动传递 Cookie"与"Session 对象管理 Cookie"的区别
# 目标：通过 httpbin.org 测试接口，直观展示两种方式的差异

import requests

def demo_manual_cookie():
    """
    演示 1：手动传递 Cookie
    适用场景：只需临时发送一次 Cookie，不需要后续请求复用
    """
    print("="*50)
    print(" 演示一：手动传递 Cookie (一次性)")
    print("="*50)

    url = "http://httpbin.org/get"
    
    # 准备我们要发送的 Cookie (字典格式)
    # 就像你去游乐园，手里拿了一张单次体验券
    my_cookies = {
        "user_id": "10086",
        "login_status": "guest"
    }
    
    print(f"📡 正在发送请求到: {url}")
    print(f" 携带的 Cookie: {my_cookies}")
    
    # 使用 requests.get 的 cookies 参数发送
    response = requests.get(url, cookies=my_cookies)
    
    if response.status_code == 200:
        data = response.json()
        # httpbin.org/get 会在 headers 字段中返回它收到的 Cookie
        received_cookie = data['headers'].get('Cookie', '无')
        print(f"✅ 请求成功！")
        print(f" 服务器看到的 Cookie: {received_cookie}")
    else:
        print("❌ 请求失败")


def demo_session_cookie():
    """
    演示 2：使用 Session 对象管理 Cookie
    适用场景：需要维持登录状态，跨请求共享 Cookie (如爬虫登录后的后续操作)
    """
    print("\n" + "="*50)
    print("🛒 演示二：使用 Session 对象 (持久化)")
    print("="*50)

    # 1. 创建一个 Session 对象
    # 这相当于你办理了一张游乐园 VIP 年卡，以后每次来都能自动识别你的身份
    session = requests.Session()
    
    # 2. 设置 Cookie (或者通过第一次请求由服务器下发 Cookie)
    # 这里我们模拟：先向一个“设置 Cookie"的接口发送请求
    url_set_cookie = "http://httpbin.org/cookies/set/session_id/998877"
    print(f" 步骤 A: 首次请求设置 Cookie -> {url_set_cookie}")
    session.get(url_set_cookie)
    
    # 3. 发起后续请求 (Session 会自动带上之前设置的 Cookie)
    url_get_info = "http://httpbin.org/get"
    print(f"📡 步骤 B: 发起后续请求 -> {url_get_info}")
    response_1 = session.get(url_get_info)
    
    if response_1.status_code == 200:
        data = response_1.json()
        received_cookie = data['headers'].get('Cookie', '无')
        print(f"✅ 第一次请求成功！服务器识别到 Cookie: {received_cookie}")

    # 4. 再次发起请求 (证明 Cookie 被 Session 记住了)
    print(f"📡 步骤 C: 再次发起请求 (无需重新设置 Cookie) -> {url_get_info}")
    response_2 = session.get(url_get_info)
    
    if response_2.status_code == 200:
        data = response_2.json()
        received_cookie = data['headers'].get('Cookie', '无')
        print(f"✅ 第二次请求成功！服务器依然识别到 Cookie: {received_cookie}")

if __name__ == "__main__":
    demo_manual_cookie()
    demo_session_cookie()
    print("\n🎉 演示结束。对比输出结果，你会发现 Session 方式下的 Cookie 是持久存在的。")
