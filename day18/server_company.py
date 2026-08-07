# server.py (MCP服务端：扮演“技能专员”，提供本地工具和数据)
from mcp.server.fastmcp import FastMCP

# 1. 实例化MCP服务端，相当于成立一个名为"JobAssistant"的技能工具箱
mcp = FastMCP("JobAssistant2")


# 2. @mcp.tool() 是核心！它像是一个“USB接口”的暴露端
# 挂上这个装饰器，大模型就能通过MCP协议“看”到并调用这个本地函数
@mcp.tool()
def get_company_info(company_name: str) -> str:
    """
    根据公司名字获取公司信息，包括公司名字，主营业务，所在城市，员工福利，旗下软件，招聘岗位
    参数company_name:公司的名字
    """
    mock_company_db = {
        "字节跳动": {
            "company_name": "字节跳动",
            "industry": "互联网",
            "scale": "超大型",
            "city": "北京",
            "welfare": "六险一金、免费三餐、下午茶、年终奖、健身房",
            "core_business": "抖音、今日头条、飞书、豆包大模型",
            "recruit_position": "AI工程师、后端开发、产品经理、算法研究员",
            "salary_range": "20‑45k",
            "requirement": "学历本科及以上，有大模型/分布式开发相关项目经验优先"
        },
        "阿里巴巴": {
            "company_name": "阿里巴巴",
            "industry": "互联网电商",
            "scale": "超大型",
            "city": "杭州",
            "welfare": "五险一金、股票期权、节日福利、员工购房补贴",
            "core_business": "淘宝、天猫、阿里云、钉钉",
            "recruit_position": "Java开发、大数据开发、云计算工程师、运营",
            "salary_range": "18‑40k",
            "requirement": "本科起步，熟悉Java生态、中间件、分布式架构优先"
        },
        "腾讯": {
            "company_name": "腾讯",
            "industry": "互联网社交游戏",
            "scale": "超大型",
            "city": "深圳",
            "welfare": "五险一金、年终奖金、带薪年假、企业年金",
            "core_business": "微信、QQ、腾讯云、游戏业务",
            "recruit_position": "C++后端、游戏开发、前端、AI算法",
            "salary_range": "19‑42k",
            "requirement": "本科及以上，扎实计算机基础，有项目落地经验优先"
        },
        "美团": {
            "company_name": "美团",
            "industry": "本地生活互联网",
            "scale": "大型",
            "city": "北京",
            "welfare": "五险一金、餐补、年终奖、团建经费",
            "core_business": "外卖、到店餐饮、美团优选",
            "recruit_position": "Go后端、数据开发、测试开发、产品",
            "salary_range": "17‑35k",
            "requirement": "本科，熟悉高并发业务开发，有大数据处理经验加分"
        },
        "百度": {
            "company_name": "百度",
            "industry": "人工智能搜索",
            "scale": "大型",
            "city": "北京",
            "welfare": "五险一金、股票激励、免费班车、年度体检",
            "core_business": "百度搜索、文心大模型、智能云",
            "recruit_position": "大模型算法、搜索后端、AI应用开发",
            "salary_range": "21‑43k",
            "requirement": "本科及以上，深度学习、NLP相关项目经验优先"
        },
        "京东": {
            "company_name": "京东",
            "industry": "电商物流",
            "scale": "大型",
            "city": "北京",
            "welfare": "五险一金、员工购物折扣、节日礼品",
            "core_business": "京东商城、京东物流、京东云",
            "recruit_position": "Java开发、供应链开发、测试工程师",
            "salary_range": "15‑30k",
            "requirement": "本科，了解电商业务，会MySQL、Redis优先"
        },
        "科大讯飞": {
            "company_name": "科大讯飞",
            "industry": "AI智能语音",
            "scale": "中大型",
            "city": "合肥",
            "welfare": "五险一金、项目奖金、人才补贴",
            "core_business": "语音识别、大模型、智慧教育",
            "recruit_position": "语音算法、NLP工程师、后端开发",
            "salary_range": "16‑32k",
            "requirement": "本科，熟悉语音或者大模型相关技术栈优先"
        },
        "小米": {
            "company_name": "小米",
            "industry": "消费电子互联网",
            "scale": "大型",
            "city": "北京",
            "welfare": "五险一金、员工内购、年终奖",
            "core_business": "手机、IoT智能家居、小米汽车",
            "recruit_position": "安卓开发、嵌入式、后端、产品经理",
            "salary_range": "17‑36k",
            "requirement": "本科，熟悉硬件或者互联网业务开发均可"
        }
    }

    try:
        result = []
        # 遍历数据库模糊匹配，把字典转为字符串存入result
        for name, info_dict in mock_company_db.items():
            if company_name in name:
                # 将字典格式化为可读文本
                item_str = (
                    f"【{info_dict['company_name']}】\n"
                    f"行业：{info_dict['industry']}，规模：{info_dict['scale']}，所在地：{info_dict['city']}\n"
                    f"核心业务：{info_dict['core_business']}\n"
                    f"招聘岗位：{info_dict['recruit_position']}\n"
                    f"薪资区间：{info_dict['salary_range']}\n"
                    f"岗位要求：{info_dict['requirement']}\n"
                    f"员工福利：{info_dict['welfare']}"
                )
                result.append(item_str)

    except Exception as e:
            return f"搜索出错: {str(e)}"

    if result:
        return "找到以下信息:\n" + "\n".join(result)
    else:
        return "暂未找到相关公司信息，请尝试其他公司。"

if __name__ == "__main__":
    # 3. 启动服务端，"stdio"表示通过标准输入输出与客户端(大模型)进行通信对话
    mcp.run(transport="stdio")
