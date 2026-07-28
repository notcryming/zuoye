import requests


def demo_manual_cookies():
    '''
    演示1：手动传递cookies请求
    适用场景：只需要临时发送一次cookie，不需要后续反复请求复用
    '''
    print("===================================")
    print("演示1：手动传递cookies请求")
    print("===================================")

    url = "http://httpbin.org/get"

    # 准备cookies
    my_cookies = {
        "user_id": "10086",
        "login_status": "guest"
    }

    print(f"请求URL: {url}")
    print(f"请求cookies: {my_cookies}")

    # 使用requests.get的cookie参数发送
    response = requests.get(url, cookies=my_cookies)
    if response.status_code == 200:
        data = response.json()
        received_cookies = data["headers"].get("Cookie")
        print("请求成功", received_cookies)
    else:
        print("请求失败")
        print(response.status_code)


def demo_session_cookie():
    '''
    演示2：session管理对象cookie请求
    适用场景：需要在多个请求之间复用cookie，例如登录后保持登录状态
    '''
    print("===================================")
    print("演示2：session管理对象cookie请求")
    print("===================================")

    # 1.创建一个session对象
    session = requests.Session()

    # 2.设置cookie
    # 模拟向一个“设置cookie”的接口发送请求
    url_set_cookie = "http://httpbin.org/cookies/set/session_id/998877"
    print(f"步骤A:首次请求设置Cookie-->{url_set_cookie}")
    session.get(url_set_cookie)

    # 3.发起后续请求(Session自动带上之前设置的cookie)
    url_get_info = "http://httpbin.org/get"
    print(f"步骤B:发起后续请求-->{url_get_info}")
    response_1 = session.get(url_get_info)

    if response_1.status_code == 200:
        data = response_1.json()
        received_cookies = data["headers"].get("Cookie")
        print(f"第一次请求收到的cookies：{received_cookies}")
    else:
        print("请求失败")

    # 再次发起请求(证明cookie被session记住了)
    print(f"步骤C:再次发起请求(无需重新设置cookie)-->{url_get_info}")
    response_2 = session.get(url_get_info)

    if response_1.status_code == 200:
        data = response_2.json()
        received_cookies = data["headers"].get("Cookie")
        print(f"第二次请求收到的cookie：{received_cookies}")
    else:
        print("请求失败")




if __name__ == "__main__":
    demo_manual_cookies()
    demo_session_cookie()