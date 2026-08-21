# -*- coding: utf-8 -*-
"""
把《斗罗大陆》小说原文转换为 ShareGPT 格式的指令微调数据集。

目标：生成 1000+ 条、且"问题必须经过针对该小说的微调才能回答"的领域问答数据。
两种来源：
  A. 对话还原问答：利用小说真实角色台词构建 recall 型问答（核心，保证足够数量与领域相关性）
  B. 章节介绍问答：每章一条"介绍本章情节"的问答，答案为该章原文内容
输出：JSON 数组（ShareGPT 格式），字段 conversations / system
"""
import re
import json

SRC = "douluo_full.txt"
OUT = "douluo_sharegpt.json"

text = open(SRC, encoding="utf-8").read()
text = text.replace("\r\n", "\n")

# ---- 1. 划分章节：标题形如 "第一集 斗罗世界 第一章 斗罗大陆，异界唐三" ----
# 章节标题行：以"第X集"开头，中间含"集"，后面含"第Y章"，整行不长
chap_re = re.compile(r"^[ \t]*(第[^\n]{1,8}集[^\n]*第[^\n]{1,10}章[^\n]{1,40})[ \t]*$", re.M)
chap_matches = list(chap_re.finditer(text))

chapters = []  # (title, body)
for i, m in enumerate(chap_matches):
    title = m.group(1).strip()
    start = m.end()
    end = chap_matches[i + 1].start() if i + 1 < len(chap_matches) else len(text)
    chapters.append((title, text[start:end]))

def chapter_no(title):
    m = re.search(r"第([一二三四五六七八九十百零0-9０-９]{1,6})章", title)
    return m.group(1) if m else "?"

def short_title(title):
    # 章节标题中"第Y章"之后的名目，如"斗罗大陆，异界唐三"
    m = re.search(r"第.{1,10}章\s*(.{1,40})$", title)
    return m.group(1).strip() if m else title

print("chapters:", len(chapters))

# ---- 2. 对话行提取 ----
def dialogue_lines(body):
    out = []
    for m in re.finditer(r"“([^”]{4,160})”", body):
        line = m.group(1).strip()
        if len(line) < 8:
            continue
        if not re.search(r"[\u4e00-\u9fa5]{2,}", line):
            continue
        if re.fullmatch(r"[的了吗呢啊吧哦嗯呃呀哈呵呵哈哈哟…、。，！？\s]{1,}", line):
            continue
        out.append(line)
    return out

def prefix_hint(line, n=12):
    p = line[:n]
    for ch in "，。！？；、：":
        i = p.find(ch)
        if i > 3:
            return p[: i + 1]
    return p + "……"

# ---- 3. 问题模板（多种表述，增加多样性） ----
def gen_question_variant(ch_no, title, line, k):
    hint = prefix_hint(line, 12)
    st = short_title(title)
    if k % 4 == 0:
        q = f"《斗罗大陆》第{ch_no}章「{st}」中，有角色说出“……{hint}”。请把这句话的完整原文还原出来。"
    elif k % 4 == 1:
        q = f"请根据《斗罗大陆》的剧情，补全第{ch_no}章「{st}」里这样一句台词：「{hint}」。"
    elif k % 4 == 2:
        q = f"《斗罗大陆》第{ch_no}章「{st}」中有一句台词，开头是“{hint}”。这句话的完整原文是什么？"
    else:
        q = f"在《斗罗大陆》第{ch_no}章「{st}」的情节里，哪位角色说过一句以“{hint}”开头的台词？请原样写出来。"
    return q

SYSTEM_DIALOG = "你是一位精通唐家三少所著《斗罗大陆》剧情、人物与台词的专家。请根据小说原著的设定，准确还原角色的原话，不要编造。"
SYSTEM_CHAPTER = "你是一位熟悉唐家三少所著《斗罗大陆》全部剧情的讲解者。请结合小说设定，具体介绍所问章节的情节内容。"

records = []

# ---- 4a. 对话还原问答 ----
MAX_PER_CHAPTER = 12
SEQ = 0
for ch_no, (title, body) in enumerate(chapters, 1):
    chno = chapter_no(title)
    for lno, line in enumerate(dialogue_lines(body)):
        if lno >= MAX_PER_CHAPTER:
            break
        q = gen_question_variant(chno, title, line, SEQ)
        a = "“" + line + "”"
        records.append({
            "system": SYSTEM_DIALOG,
            "conversations": [
                {"from": "human", "value": q},
                {"from": "gpt", "value": a},
            ],
        })
        SEQ += 1

# ---- 4b. 章节介绍问答 ----
def clean_para(body):
    paras = []
    for seg in body.split("\n"):
        seg = seg.strip()
        if not seg:
            continue
        paras.append(seg)
    # 拼接前 ~5 段作为该章内容描述
    excerpt = "".join(paras[:6])
    return excerpt

for ch_no, (title, body) in enumerate(chapters, 1):
    chno = chapter_no(title)
    excerpt = clean_para(body)
    if len(excerpt) < 30:
        continue
    q = f"请详细介绍《斗罗大陆》第{chno}章「{short_title(title)}」的情节内容。"
    a = excerpt
    records.append({
        "system": SYSTEM_CHAPTER,
        "conversations": [
            {"from": "human", "value": q},
            {"from": "gpt", "value": a},
        ],
    })

print("total records:", len(records))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print("saved ->", OUT)

# ---- 校验 ----
data = json.load(open(OUT, encoding="utf-8"))
assert len(data) == len(records)
print("validate ok, sample record:")
print(json.dumps(data[0], ensure_ascii=False, indent=2))