import json
import os

BASE = r"c:\Users\ASUS\Desktop\shixun1\8.20"
SRC = os.path.join(BASE, "cluener_public", "train.json")
DST = os.path.join(BASE, "cluener_100_alpaca.json")
N = 100

LABEL_CN = {
    "address": "地址",
    "book": "书名",
    "company": "公司",
    "game": "游戏",
    "goverment": "政府",
    "movie": "电影",
    "name": "姓名",
    "organization": "组织机构",
    "position": "职位",
    "scene": "景点",
}

INSTRUCTION = (
    "请识别给定句子中出现的命名实体，并标注其类别。"
    "类别包括：地址、书名、公司、游戏、政府、电影、姓名、组织机构、职位、景点。"
    "请以“实体:类别”的形式列出，多个用逗号分隔。"
)

records = []
with open(SRC, encoding="utf-8") as f:
    for i, line in enumerate(f):
        if i >= N:
            break
        line = line.strip()
        if not line:
            continue
        item = json.loads(line)
        text = item["text"]
        label = item.get("label", {})
        outs = []
        for en_type, entities in label.items():
            cn = LABEL_CN.get(en_type, en_type)
            for ent, spans in entities.items():
                outs.append("%s:%s" % (ent, cn))
        output = "，".join(outs) if outs else "无"
        records.append(
            {
                "instruction": INSTRUCTION,
                "input": text,
                "output": output,
            }
        )

with open(DST, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print("生成条数:", len(records))
for r in records[:3]:
    print(json.dumps(r, ensure_ascii=False))