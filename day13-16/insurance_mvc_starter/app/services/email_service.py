"""邮件业务编排服务

【MVC 归属】业务层（Service 层）
【思路】
1. filter_high_target_customers：读 customers.predicted_prob → 按分位数筛选高潜客户
2. batch_generate_emails：循环调 llm_service 生成邮件 → 批量入库 → 返回成功/失败计数
3. get_active_prompt：读数据库生效 Prompt 模板
4. update_prompt_template：更新模板内容

严格遵循 AI 技术方案 3.x：
- LLM 调用失败、未配置 API_KEY 时不抛异常，返回 {success:False}，上层正常入库 failed 记录
- 单客户生成失败不阻断批量其他客户流程
- 分位筛选默认 0.9（取 top 10% 高潜客户）
"""
import numpy as np
from sqlalchemy.orm import Session
from app.core.response import BizException
from app.core.dependencies import record_operate_log
from app.models.customers import Customer
from app.models.email_record import EmailRecord
from app.models.prompt_template import PromptTemplate, DEFAULT_PROMPT_CONTENT, DEFAULT_PROMPT_NAME
from app.services.llm_service import llm_service


def filter_high_target_customers(db: Session, percentile: float = 0.9) -> dict:
    """高潜客户筛选：按 predicted_prob 分位数取 top (1-percentile) 客户

    逐字思路：
    1. 查 predicted_prob 非空的客户 → 无数据抛 BizException(3002)
    2. 算分位阈值 threshold = np.quantile(probs, percentile)
    3. 筛 predicted_prob >= threshold 的客户
    4. 返回 {threshold, total, customers}

    为什么用分位数而非固定阈值？
      不同模型概率分布不同，固定 0.5 没意义；分位数保证永远取 top 10%，与模型无关。
    """
    # 1. 查有预测概率的客户
    customers = db.query(Customer).filter(
        Customer.predicted_prob.isnot(None)
    ).order_by(Customer.predicted_prob.desc()).all()

    if not customers:
        raise BizException(3002, "无预测数据，请先执行模型预测", 400)

    # 2. 算分位阈值
    probs = np.array([c.predicted_prob for c in customers])
    threshold = float(np.quantile(probs, percentile))

    # 3. 筛选高潜客户
    targets = [c for c in customers if c.predicted_prob >= threshold]

    # 4. 组装返回
    customer_list = [
        {
            "id": c.id,
            "gender": c.gender,
            "age": c.age,
            "annual_premium": c.annual_premium,
            "predicted_prob": c.predicted_prob,
        }
        for c in targets
    ]

    return {
        "threshold": threshold,
        "total": len(customer_list),
        "customers": customer_list,
    }


def batch_generate_emails(
    db: Session, customer_ids: list = None, limit: int = 5, user_id: int = None,
) -> dict:
    """批量生成营销邮件：循环调 LLM → 批量入库 → 返回计数

    逐字思路：
    1. 确定目标客户列表
       - customer_ids 非空 → 按指定 id 查客户
       - customer_ids 为空 → 自动取 top N（按 predicted_prob 降序）
    2. 无预测数据抛 BizException(3002)
    3. 读生效 Prompt 模板
    4. 逐客户：build_customer_prompt → generate_marketing_email → 收集记录
       - 单客户失败不中断，标记 status=failed
    5. batch_create 批量入库
    6. 返回 {generated_count, failed_count, records}

    约束：无并发异步，同步串行调用。
    """
    # 1. 确定目标客户
    if customer_ids:
        customers = db.query(Customer).filter(Customer.id.in_(customer_ids)).all()
        if not customers:
            raise BizException(2001, "指定的客户不存在", 404)
    else:
        # 自动取 top N
        customers = db.query(Customer).filter(
            Customer.predicted_prob.isnot(None)
        ).order_by(Customer.predicted_prob.desc()).limit(limit).all()

        if not customers:
            raise BizException(3002, "无预测数据，请先执行模型预测", 400)

    # 2. 读生效 Prompt 模板
    tpl = PromptTemplate.get_active_template(db)
    template_content = tpl.content if tpl else None

    # 3. 逐客户生成邮件
    records_to_create = []
    results = []

    for customer in customers:
        try:
            # 构建 Prompt
            prompt = llm_service.build_customer_prompt(customer, template_content)
            # 调用 LLM
            llm_result = llm_service.generate_marketing_email(prompt)

            if llm_result.get("success"):
                # 成功
                records_to_create.append({
                    "customer_id": customer.id,
                    "subject": llm_result.get("subject", ""),
                    "content": llm_result.get("content", ""),
                    "status": "generated",
                    "created_by": user_id,
                })
                results.append({
                    "customer_id": customer.id,
                    "status": "generated",
                    "subject": llm_result.get("subject", ""),
                })
            else:
                # LLM 失败（降级）→ 入库 failed 记录
                records_to_create.append({
                    "customer_id": customer.id,
                    "subject": None,
                    "content": None,
                    "status": "failed",
                    "created_by": user_id,
                })
                results.append({
                    "customer_id": customer.id,
                    "status": "failed",
                    "subject": None,
                })

        except Exception as e:
            # 单客户异常不中断批量流程
            records_to_create.append({
                "customer_id": customer.id,
                "subject": None,
                "content": None,
                "status": "failed",
                "created_by": user_id,
            })
            results.append({
                "customer_id": customer.id,
                "status": "failed",
                "subject": None,
            })

    # 4. 批量入库
    if records_to_create:
        EmailRecord.batch_create(db, records_to_create)

    # 5. 统计
    generated_count = sum(1 for r in results if r["status"] == "generated")
    failed_count = sum(1 for r in results if r["status"] == "failed")

    # 记录操作日志（不阻断主业务流程）
    record_operate_log(db, user_id, "email_generation", {
        "generated_count": generated_count,
        "failed_count": failed_count,
        "customer_ids": customer_ids,
        "limit": limit if not customer_ids else None,
        "customer_count": len(customers),
    })

    return {
        "generated_count": generated_count,
        "failed_count": failed_count,
        "records": results,
    }


def get_active_prompt(db: Session) -> dict:
    """获取当前生效 Prompt 模板

    返回 {name, content}，无生效模板时用默认模板兜底。
    """
    tpl = PromptTemplate.get_active_template(db)
    if not tpl:
        return {"name": DEFAULT_PROMPT_NAME, "content": DEFAULT_PROMPT_CONTENT}

    return {"name": tpl.name, "content": tpl.content}


def update_prompt_template(db: Session, new_content: str) -> dict:
    """更新 Prompt 模板内容

    返回更新后的 {name, content}。
    """
    tpl = PromptTemplate.update_content(db, new_content)
    return {"name": tpl.name, "content": tpl.content}
