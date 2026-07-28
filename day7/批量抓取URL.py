import requests
from requests.exceptions import RequestException

def demo_manual_cookies(url):
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
        return 1
    else:
        print("请求失败")
        print(response.status_code)
        return 0
if __name__ == "__main__":
    lst = ["http://httpbin.org/get",
           "http://httpbin.org/status/200",
           "http://httpbin.org/status/404"]
    success = fail = 0
    for url in lst:
        try:
            if demo_manual_cookies(url) == 1:
                success += 1
            else:
                fail += 1
        except RequestException as e:
            print(f"访问 {url} 出现网络/请求异常：{e}")
    print(f"成功：{success}个，失败：{fail}个")