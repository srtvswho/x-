"""P4-6 新标准重新过 17 个 A 类 — 卡点判断 vs 废话分析

新标准:
- 必须有: 明确卡点(供需/产能/技术门槛) + 明确方向(多/空) + 非共识判断
- 排除: 中性罗列 / 转述机构 / 纯技术面 / 条件性无明确时间
"""
import json

with open("/workspace/logs/p4p5b_llm_pro_screened.json") as f:
    data = json.load(f)

# 新标准下重判每个 A 类
NEW_GRADES = {
    "@oopsguess": {
        "grade": "A+",
        "verdict": "✅ 强卡点+多+非共识",
        "rationale": "明确指出'中国存储厂商产能满载仍供不应求'是关键卡点 + 关税推涨 SNDK 受益 + 当时美国主流在 weaponize 视角,她看多 SNDK 是逆共识",
    },
    "@jukan05": {
        "grade": "A+",
        "verdict": "✅ 强卡点+空+非共识",
        "rationale": "明确 4Q25 downturn 卡点(关税 25% + 需求弱 + HBM 反成 headwind) + 看空 SNDK(下调 Underperform) + 是逆向看空(当时 +48% 已在顶部)",
    },
    "@wallstengine": {
        "grade": "C",
        "verdict": "❌ 转述 BofA 报告",
        "rationale": "转发 BofA Buy PT $61,无独立判断(机构观点搬运)",
    },
    "@corleonedon77": {
        "grade": "C",
        "verdict": "❌ 转述 Jefferies 报告",
        "rationale": "转发 Jefferies Buy $60 报告,无独立卡点判断",
    },
    "@allday_stocks": {
        "grade": "C",
        "verdict": "❌ 转述 Edgewater 报告",
        "rationale": "转述 Edgewater 1H25 强 2H25 弱,无独立判断",
    },
    "@iamlearningcry1": {
        "grade": "B-",
        "verdict": "🟡 有质疑但无独立卡点",
        "rationale": "质疑 Edgewater 把 MU/SNDK 并论(HBM vs NAND 差异),有独立分析感,但没明确'我自己的判断是什么'",
    },
    "@wmhuo168": {
        "grade": "A",
        "verdict": "✅ 卡点+空+非共识",
        "rationale": "明确卡点(中国 YMTC 蚕食 NAND 份额)+ 隐含看空 Sandisk('begs for handouts')+ 跟当时主流看多 Sandisk 相反",
    },
    "@mayorhardin": {
        "grade": "C",
        "verdict": "❌ 问技术问题,无方向",
        "rationale": "只是问 SNDK 怎么改善 pj/bit/endurance,没表态多空",
    },
    "@olrak29_": {
        "grade": "C",
        "verdict": "❌ 问技术问题,无方向",
        "rationale": "质疑 NAND 在 GPU 写入耐久,问号形式无方向",
    },
    "@nitininvests": {
        "grade": "B",
        "verdict": "🟡 列出需求但无明确卡点+非共识",
        "rationale": "列出 Micro SSD / AI PC / 数据中心需求,有自洽论述,但都是已知利好,不是'非共识的卡点'",
    },
    "@d__risk": {
        "grade": "C",
        "verdict": "❌ 罗列风险无方向",
        "rationale": "WDC 10-K 风险因子罗列,无独立判断",
    },
    "@mike10947310": {
        "grade": "B-",
        "verdict": "🟡 条件性无明确时间",
        "rationale": "'if 供给瓶颈出现'是条件性,没说瓶颈什么时候出现,没说是否会发生",
    },
    "@bezosric": {
        "grade": "B",
        "verdict": "🟡 有判断但卡点不硬",
        "rationale": "提出 MU-SNDK 分化 + SNDK 积累机会,有独立观点,但没指明具体卡点",
    },
    "@alex_intel_": {
        "grade": "C",
        "verdict": "❌ 政策话题非股票",
        "rationale": "建议 Intel 买 SNDK 废弃场地建 fab,不是股票判断",
    },
    "@lokoyacap": {
        "grade": "A",
        "verdict": "✅ 卡点(panic buying)+ 隐含多",
        "rationale": "明确指出'Hyperscalers panic buying NAND'是卡点,解释为什么不应被短期噪音影响,隐含看多 NAND/SNDK",
    },
    "@ch_imrankhalid": {
        "grade": "C",
        "verdict": "❌ 转述 MS 报告",
        "rationale": "转述 Morgan Stanley 看 NAND + BICS 8 量产,无独立卡点",
    },
    "@kmad": {
        "grade": "C",
        "verdict": "❌ 问技术问题,无方向",
        "rationale": "问 SNDK 产品速度,无明确判断",
    },
}

# 找所有 A 类作者
a_class = [a for a in data["authors_screened"] if a["classification"]["category"] == "A"]
a_class.sort(key=lambda x: x["pub_date"])

# 按新标准重新评级
graded = []
for a in a_class:
    h = "@" + a["author"]
    g = NEW_GRADES.get(h, {"grade": "?", "verdict": "?", "rationale": "未评估"})
    a["new_grade"] = g
    graded.append(a)

# 输出 17 个 A 类按新评级分组
print("=" * 80)
print("17 个 A 类作者按新标准 ('卡点判断' 严格筛选) 重新分级")
print("=" * 80)
print()

print("=" * 60)
print("✅ A+/A 真正做出卡点判断 (5 个):")
print("=" * 60)
for a in graded:
    if a["new_grade"]["grade"] in ("A+", "A"):
        print(f"\n  @{a['author']:25s} {a['pub_date']:12s} +{a['pct_above_low']:5.1f}% [{a['new_grade']['grade']}]")
        print(f"    verdict: {a['new_grade']['verdict']}")
        print(f"    rationale: {a['new_grade']['rationale']}")
        print(f"    原文: {a['text'][:300]}")

print("\n" + "=" * 60)
print("🟡 B/B- 有一定独立分析但未达卡点判断 (4 个):")
print("=" * 60)
for a in graded:
    if a["new_grade"]["grade"] in ("B", "B-"):
        print(f"\n  @{a['author']:25s} {a['pub_date']:12s} +{a['pct_above_low']:5.1f}% [{a['new_grade']['grade']}]")
        print(f"    verdict: {a['new_grade']['verdict']}")
        print(f"    rationale: {a['new_grade']['rationale']}")

print("\n" + "=" * 60)
print("❌ C 转述/无方向/非股票 (8 个):")
print("=" * 60)
for a in graded:
    if a["new_grade"]["grade"] == "C":
        print(f"\n  @{a['author']:25s} {a['pub_date']:12s} +{a['pct_above_low']:5.1f}% [C]")
        print(f"    verdict: {a['new_grade']['verdict']}")

# 统计
from collections import Counter
grades = Counter(a["new_grade"]["grade"] for a in graded)
print(f"\n\n=== 17 个 A 类按新标准分级 ===")
for g, n in sorted(grades.items()):
    print(f"  {g}: {n}")
print(f"\n真正 '卡点判断' (A+/A): {grades.get('A+', 0) + grades.get('A', 0)} 个")

# 保存
with open("/workspace/logs/p4p6_strict_filter.json", "w") as f:
    json.dump({
        "n_a_total": len(graded),
        "n_cardinal_calls": grades.get("A+", 0) + grades.get("A", 0),
        "n_partial": grades.get("B", 0) + grades.get("B-", 0),
        "n_rejected": grades.get("C", 0),
        "graded": graded,
    }, f, indent=2, default=str)
print(f"\n✅ saved /workspace/logs/p4p6_strict_filter.json")