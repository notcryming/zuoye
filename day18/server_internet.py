# server_internet.py (MCP服务端：互联网工具聚合，接入真实免费公开API)
import socket
import requests
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# 1. 实例化MCP服务端，相当于成立一个名为"InternetTools"的技能工具箱
mcp = FastMCP("InternetTools")

# 统一请求头与超时设置，便于复用与异常控制
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}
TIMEOUT = 8  # 单次请求超时时间（秒），避免长时间卡死


# 2. @mcp.tool() 像"USB接口"的暴露端，挂上后大模型即可通过MCP协议调用
@mcp.tool()
def get_ip_info(ip: str) -> str:
    """
    根据IP地址查询归属地信息，包括国家、地区、城市、运营商、时区、经纬度等
    参数ip: 要查询的IPv4地址，例如 8.8.8.8
    """
    url = f"http://ip-api.com/json/{ip}?lang=zh-CN"
    try:
        resp = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        return "查询IP信息超时，请稍后重试。"
    except requests.exceptions.RequestException as e:
        return f"查询IP信息网络异常: {e}"
    except Exception as e:
        return f"查询IP信息出错: {e}"

    # ip-api.com 返回 status 字段标识是否成功
    if data.get("status") != "success":
        return f"查询失败: {data.get('message', '未知原因')}"

    return (
        f"IP: {data.get('query', ip)}\n"
        f"国家: {data.get('country', '未知')} ({data.get('countryCode', '')})\n"
        f"地区: {data.get('regionName', '未知')}\n"
        f"城市: {data.get('city', '未知')}\n"
        f"运营商: {data.get('isp', '未知')}\n"
        f"组织: {data.get('org', '未知')}\n"
        f"时区: {data.get('timezone', '未知')}\n"
        f"经纬度: {data.get('lat', '?')}, {data.get('lon', '?')}"
    )


@mcp.tool()
def get_random_fact() -> str:
    """
    随机获取一条"毒鸡汤"（带点反转/扎心的励志短句），不需要任何参数
    """
    # 备选API列表，主API失败时自动尝试下一个，保证可用性
    apis = [
        ("http://api.btstu.cn/yan/api.php?lx=2", "text"),   # 毒鸡汤（纯文本）
        ("https://v1.hitokoto.cn/?c=b&encode=text", "text"),  # 一言备选（纯文本）
        ("https://api.imlolicon.top/api/DuJiTang", "json"),   # 毒鸡汤JSON备选
    ]
    for url, mode in apis:
        try:
            resp = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
            resp.raise_for_status()

            if mode == "json":
                try:
                    data = resp.json()
                except ValueError:
                    continue
                # 兼容不同字段名与类型（string 或 list）
                text = data.get("data") or data.get("text") or data.get("content") or ""
                if isinstance(text, list):
                    text = text[0] if text else ""
            else:
                text = resp.text.strip()

            if text:
                return f"毒鸡汤: {text}"
        except requests.exceptions.Timeout:
            continue
        except Exception:
            continue

    return "毒鸡汤获取失败，网络似乎不太给力，请稍后再试。"


@mcp.tool()
def search_wikipedia(keyword: str) -> str:
    """
    根据关键词在维基百科中搜索并返回条目摘要
    参数keyword: 要搜索的关键词，例如 LangChain
    """
    # 第一步：先用搜索接口找到最匹配的条目标题，避免直接取摘要时标题不匹配
    search_url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": keyword,
        "format": "json",
        "utf8": "",
        "srlimit": "1",
    }
    try:
        resp = requests.get(search_url, params=params, timeout=TIMEOUT, headers=HEADERS)
        resp.raise_for_status()
        sdata = resp.json()
    except requests.exceptions.Timeout:
        return "维基百科搜索超时，可能是网络受限，请稍后重试或检查网络。"
    except Exception as e:
        return f"维基百科搜索出错（可能网络受限）: {e}"

    search_hits = sdata.get("query", {}).get("search", [])

    # 英文维基没找到，回退到中文维基
    if not search_hits:
        try:
            resp = requests.get("https://zh.wikipedia.org/w/api.php", params=params,
                                timeout=TIMEOUT, headers=HEADERS)
            resp.raise_for_status()
            sdata = resp.json()
            search_hits = sdata.get("query", {}).get("search", [])
        except Exception:
            search_hits = []

    if not search_hits:
        return f"未在维基百科找到与「{keyword}」相关的条目。"

    title = search_hits[0]["title"]

    # 第二步：根据标题获取条目摘要
    summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(title)}"
    try:
        sresp = requests.get(summary_url, timeout=TIMEOUT, headers=HEADERS)
        sresp.raise_for_status()
        summary = sresp.json()
    except Exception as e:
        return f"已找到条目「{title}」，但获取摘要失败: {e}"

    extract = summary.get("extract") or "暂无摘要内容。"
    return f"【{title}】（维基百科）\n{extract}"


@mcp.tool()
def get_time_zone(location: str) -> str:
    """
    根据地名查询该地的时区和当前时间
    参数location: 城市或地区名称，例如 东京、London、北京、Paris
    """
    # 常见城市 -> IANA时区 映射，命中则直接查询，避免地理编码开销
    city_timezone = {
        "东京": "Asia/Tokyo", "tokyo": "Asia/Tokyo",
        "北京": "Asia/Shanghai", "beijing": "Asia/Shanghai",
        "上海": "Asia/Shanghai", "shanghai": "Asia/Shanghai",
        "伦敦": "Europe/London", "london": "Europe/London",
        "纽约": "America/New_York", "new york": "America/New_York", "newyork": "America/New_York",
        "巴黎": "Europe/Paris", "paris": "Europe/Paris",
        "洛杉矶": "America/Los_Angeles", "los angeles": "America/Los_Angeles",
        "首尔": "Asia/Seoul", "seoul": "Asia/Seoul",
        "新加坡": "Asia/Singapore", "singapore": "Asia/Singapore",
        "悉尼": "Australia/Sydney", "sydney": "Australia/Sydney",
        "迪拜": "Asia/Dubai", "dubai": "Asia/Dubai",
        "莫斯科": "Europe/Moscow", "moscow": "Europe/Moscow",
        "柏林": "Europe/Berlin", "berlin": "Europe/Berlin",
        "香港": "Asia/Hong_Kong", "hong kong": "Asia/Hong_Kong", "hongkong": "Asia/Hong_Kong",
        "台北": "Asia/Taipei", "taipei": "Asia/Taipei",
        "曼谷": "Asia/Bangkok", "bangkok": "Asia/Bangkok",
        "孟买": "Asia/Kolkata", "mumbai": "Asia/Kolkata",
    }

    tz = city_timezone.get(location.strip())

    # 未命中映射，使用OpenStreetMap Nominatim进行地理编码，再解析时区
    if not tz:
        geo_url = "https://nominatim.openstreetmap.org/search"
        geo_params = {"q": location, "format": "json", "limit": "1"}
        try:
            gresp = requests.get(geo_url, params=geo_params, timeout=TIMEOUT, headers=HEADERS)
            gresp.raise_for_status()
            gdata = gresp.json()
        except requests.exceptions.Timeout:
            return f"查询「{location}」时区超时，请稍后重试。"
        except Exception as e:
            return f"查询「{location}」时区失败: {e}"

        if not gdata:
            return f"未找到「{location}」对应的地理位置。"

        lat, lon = gdata[0]["lat"], gdata[0]["lon"]
        # BigDataCloud 免费反向地理编码（无需Key），可返回IANA时区
        rev_url = "https://api.bigdatacloud.net/data/reverse-geocode-client"
        rev_params = {"latitude": lat, "longitude": lon, "localityLanguage": "en"}
        try:
            rresp = requests.get(rev_url, params=rev_params, timeout=TIMEOUT, headers=HEADERS)
            rresp.raise_for_status()
            tz = rresp.json().get("ianaTimeId")
        except Exception as e:
            return f"已定位到「{location}」(经纬度 {lat}, {lon})，但获取时区失败: {e}"

        if not tz:
            return f"已定位到「{location}」，但未能解析出时区信息。"

    # 优先通过 timeapi.io 获取该时区的当前时间
    time_str = None
    source = ""
    try:
        tresp = requests.get(
            f"https://timeapi.io/api/Time/current/zone?timeZone={requests.utils.quote(tz)}",
            timeout=TIMEOUT, headers=HEADERS
        )
        tresp.raise_for_status()
        tdata = tresp.json()
        time_str = f"{tdata.get('date', '')} {tdata.get('time', '')}".strip()
        source = "timeapi.io"
    except Exception:
        time_str = None

    # timeapi.io 失败时，使用本地 zoneinfo 计算当前时间（无需联网）
    if not time_str:
        try:
            from zoneinfo import ZoneInfo
            now = datetime.now(ZoneInfo(tz))
            time_str = now.strftime("%Y-%m-%d %H:%M:%S")
            source = "本地时区计算(zoneinfo)"
        except Exception as e:
            return f"已识别时区「{tz}」，但获取当前时间失败: {e}"

    return (
        f"地点: {location}\n"
        f"时区: {tz}\n"
        f"当前时间: {time_str}\n"
        f"(数据来源: {source})"
    )


@mcp.tool()
def get_domain_info(domain: str) -> str:
    """
    查询域名的DNS解析信息，包括A记录(IP地址)和NS记录(域名服务器)
    参数domain: 域名，例如 google.com
    """
    # 清理输入：去掉协议前缀和路径，统一小写
    domain = domain.strip().lower()
    for prefix in ("https://", "http://", "www."):
        if domain.startswith(prefix):
            domain = domain[len(prefix):]
    domain = domain.split("/")[0]

    results = []

    # --- 查询A记录（IP地址）---
    # 优先使用 Google DNS over HTTPS（真实公开API），失败时回退到系统DNS解析
    a_records = []
    try:
        resp = requests.get(
            f"https://dns.google/resolve?name={domain}&type=A",
            timeout=TIMEOUT, headers=HEADERS
        )
        resp.raise_for_status()
        answers = resp.json().get("Answer", [])
        a_records = [a["data"] for a in answers if a.get("type") == 1]
    except Exception:
        a_records = []

    # API未拿到结果，回退到 socket 本地DNS解析（走系统DNS，兼容性好）
    if not a_records:
        try:
            info = socket.getaddrinfo(domain, None)
            a_records = sorted(set(i[4][0] for i in info if ":" not in i[4][0]))
        except socket.gaierror as e:
            results.append(f"IP地址(A记录): 解析失败 ({e})")

    if a_records:
        results.append(f"IP地址(A记录): {', '.join(a_records)}")

    # --- 查询NS记录（域名服务器）---
    try:
        resp = requests.get(
            f"https://dns.google/resolve?name={domain}&type=NS",
            timeout=TIMEOUT, headers=HEADERS
        )
        resp.raise_for_status()
        answers = resp.json().get("Answer", [])
        ns_records = [a["data"] for a in answers if a.get("type") == 2]
        results.append(f"域名服务器(NS): {', '.join(ns_records) if ns_records else '未找到(可能网络受限)'}")
    except Exception as e:
        results.append(f"域名服务器(NS): 查询失败 ({str(e)[:50]})")

    return f"域名: {domain}\n" + "\n".join(results)


if __name__ == "__main__":
    # 3. 启动服务端，"stdio"表示通过标准输入输出与客户端(大模型)进行通信对话
    mcp.run(transport="stdio")
