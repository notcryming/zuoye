"""大模型 LLM 底层调用服务

【MVC 归属】业务层（Service 层）
【思路】
1. 构造函数读取 .env 的 LLM_API_BASE / LLM_MODEL / LLM_API_KEY 配置
   - 无 API_KEY → client=None，系统照常跑（邮件功能自动降级）
2. build_customer_prompt：客户编码字段反译为自然语言 → str.format 填充模板占位符
3. generate_marketing_email：调用通义千问 qwen-flash，temperature=0.7
   - 正则清理 markdown ```json 标记
   - 捕获所有异常返回 success=False 降级结果（不抛异常拖垮业务）

严格遵循 AI 技术方案 3.x：
- OpenAI 兼容协议（openai SDK 一行调用，换模型只改 base_url/model）
- Prompt 四要素：角色设定 + 客户画像（自然语言）+ 任务要求 + 输出格式
- 降级策略：LLM 不可用 → {success: False}，业务层照常建失败记录
- 禁止直接传 0/1 编码给 LLM，全部通过反编码转中文描述
"""
import re
import json as json_lib
from app.core.config import settings
from app.utils.data_processor import customer_to_natural_text
from app.models.prompt_template import DEFAULT_PROMPT_CONTENT


class LLMService:
    """大模型 LLM 调用服务

    单例模式：模块级实例化 llm_service = LLMService()，全局复用。
    无 API_KEY 时 client=None，所有调用自动降级返回 success=False。
    """

    def __init__(self):
        """构造函数：读取配置，有 API_KEY 则创建 OpenAI client，无则降级

        逐字思路：
        1. 从 settings 读 LLM_API_KEY / LLM_API_BASE / LLM_MODEL
        2. API_KEY 为空 → client=None（降级模式，不导入 openai）
        3. API_KEY 非空 → 创建 OpenAI client（OpenAI 兼容协议）
        """
        self.api_key = settings.LLM_API_KEY
        self.api_base = settings.LLM_API_BASE
        self.model = settings.LLM_MODEL

        if not self.api_key:
            # 降级模式：不创建 client，调用时直接返回 success=False
            self.client = None
        else:
            # 延迟导入：无 API_KEY 时不加载 openai（减少无谓依赖初始化）
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key, base_url=self.api_base)

    def build_customer_prompt(self, customer_row, template_content: str = None) -> str:
        """构建完整 Prompt：客户画像反编码 → 填充模板占位符

        逐字思路：
        1. customer_row 转 natural_text dict（0/1 编码 → 中文描述）
        2. template_content 为空 → 用 DEFAULT_PROMPT_CONTENT 兜底
        3. str.format(**natural_text) 填充 {gender}/{age} 等占位符
        4. 返回完整 Prompt 文本

        【关键】用 str.format 而非 f-string：模板从 DB 读，是运行时拼接，
        f-string 是代码期拼接，不能用于 DB 模板。
        """
        # 1. 客户画像反编码
        natural_text = customer_to_natural_text(customer_row)

        # 2. 模板兜底
        tpl = template_content or DEFAULT_PROMPT_CONTENT

        # 3. str.format 填充占位符
        #    模板中 {{ }} 会被 format 转义为字面 { }，保住 JSON 示例
        prompt = tpl.format(**natural_text)

        return prompt

    def generate_marketing_email(self, prompt_text: str) -> dict:
        """调用 LLM 生成营销邮件：发送 Prompt → 清理输出 → 解析 JSON

        逐字思路：
        1. client=None → 直接返回 {success: False, error: "LLM_API_KEY 未配置"}
        2. 调 chat.completions.create（temperature=0.7，平衡创造力与稳定性）
        3. 正则清理 markdown ```json 包裹标记
        4. json.loads 解析 → 返回 {success: True, subject, content}
        5. 任何异常 → 返回 {success: False, error: str(e)}（降级，不抛异常）

        返回结构：
        - 成功：{"success": True, "subject": "邮件主题", "content": "HTML正文"}
        - 失败：{"success": False, "error": "错误描述"}
        """
        # 1. 降级检查
        if not self.client:
            return {"success": False, "error": "LLM_API_KEY 未配置，邮件生成功能不可用"}

        # 2. 调用 LLM
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt_text}],
                temperature=0.7,
            )
            content = resp.choices[0].message.content.strip()
        except Exception as e:
            return {"success": False, "error": f"LLM 调用失败：{e}"}

        # 3. 正则清理 markdown 代码块标记
        #    LLM 输出可能带 ```json ... ``` 包裹，需清理后才能 json.loads
        content = re.sub(r'^```json\s*', '', content)   # 去开头 ```json
        content = re.sub(r'^```\s*', '', content)       # 去开头 ```（无 json 标记）
        content = re.sub(r'\s*```$', '', content)        # 去结尾 ```
        content = content.strip()

        # 4. 解析 JSON
        try:
            result = json_lib.loads(content)
            return {
                "success": True,
                "subject": result.get("subject", ""),
                "content": result.get("content", ""),
            }
        except json_lib.JSONDecodeError as e:
            return {"success": False, "error": f"LLM 输出 JSON 解析失败：{e}"}


# 模块级单例：import 时构造，全局复用
llm_service = LLMService()
