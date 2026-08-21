# -*- coding: utf-8 -*-
import json

data = json.load(open("douluo_sharegpt.json", encoding="utf-8"))
print("总条数:", len(data))

ok = 0
sys_ok = 0
pair_ok = 0
issues = []
for i, rec in enumerate(data):
    if "conversations" in rec:
        ok += 1
    if "system" in rec and isinstance(rec["system"], str) and rec["system"]:
        sys_ok += 1
    conv = rec.get("conversations", [])
    roles = [m.get("from") for m in conv]
    # 必须以 human 开始，且 human/gpt 交替
    if roles and roles[0] == "human":
        expected = ["human", "gpt"] * (len(roles) // 2)
        if len(roles) % 2 != 0:
            expected.append("human")
        if roles == expected:
            pair_ok += 1
        else:
            issues.append((i, roles))
    else:
        issues.append((i, roles))

print("含conversations:", ok)
print("含非空system:", sys_ok)
print("role交替正确:", pair_ok)
print("role异常条数:", len(issues))
for i, roles in issues[:5]:
    print("  异常记录", i, roles)

# human/gpt 数量统计
from collections import Counter
role_counter = Counter()
for rec in data:
    for m in rec["conversations"]:
        role_counter[m["from"]] += 1
print("role分布:", dict(role_counter))

# 每条至少一轮 human->gpt
min_len = min(len(r["conversations"]) for r in data)
print("最短对话轮数:", min_len)

import os
print("文件大小(bytes):", os.path.getsize("douluo_sharegpt.json"))

# 展示几个不同类型样本
print("\n--- 样本1 对话还原 ---")
print(json.dumps(data[0], ensure_ascii=False))
print("\n--- 样本2 ---")
print(json.dumps(data[1500], ensure_ascii=False))
print("\n--- 样本3 章节介绍(截断) ---")
s = data[-3]
print(json.dumps({k: (v[:80] + '...') if isinstance(v, str) else v for k, v in s.items()}, ensure_ascii=False))