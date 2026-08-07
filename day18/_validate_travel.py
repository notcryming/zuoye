"""最小验证脚本：检查 5 个顾问 + 主管 + 汇总器 是否能正确工作（不进入交互模式）"""
import sys
sys.path.insert(0, r"c:\Users\ASUS\Desktop\shixun1\day18")
# 让导入时不要自动执行 main
# 直接导入模块（但 main 里面是 if __name__=="__main__"，所以没事）
from 旅行计划生成器 import (
    CONSULTANTS, supervisor_chain, parse_consultant_list,
    aggregate_answers, dispatch_question, build_travel_plan,
    print_result, print_travel_plan,
)

print("=== 1. 验证 5 个顾问独立工作 ===")
for key in ["destination", "budget", "transportation", "food", "culture"]:
    info = CONSULTANTS[key]
    try:
        ans = info["chain"].invoke({"context": f"简要测试：去东京玩"})
        print(f"✅ {info['name']}: {ans[:60].replace(chr(10), ' ')}...")
    except Exception as e:
        print(f"❌ {info['name']} 错误: {e}")

print("\n=== 2. 验证主管分发决策 ===")
test_q = [
    ("去成都玩有什么必去的景点？", ["destination"]),
    ("北京有什么好吃的？推荐几家餐厅。", ["food"]),
    ("两个人去泰国玩一周带12000元够吗？怎么花？", ["budget", "destination"]),
    ("帮我推荐一款笔记本电脑", []),
    ("去大理5天预算5000，吃住行玩都帮我看", ["destination","budget","transportation","food","culture"]),
]
for q, expect in test_q:
    try:
        raw = supervisor_chain.invoke({"question": q})
        parsed = parse_consultant_list(raw)
        print(f"  Q: {q[:40]} → 主管选: {parsed} (期望含: {expect})")
    except Exception as e:
        print(f"  ❌ 主管出错 Q={q[:30]}: {e}")

print("\n=== 3. 验证多顾问并发 + 汇总 (1 个复合问题) ===")
result = dispatch_question("两个人去泰国玩一周，带 12000 元够吗？吃什么？", verbose=True)
print_result(result)

print("\n=== 4. 验证旅行计划生成器 (简化 1 个案例) ===")
plan = build_travel_plan("西安", 3, 3000)
print_travel_plan(plan)

print("\n✅ 全部完成！")
