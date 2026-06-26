"""手动修正 5 条误抽 short + 重跑 verify"""
import json
import os
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

PRICE_DIR = Path("/workspace/data/price_cache")
DATA_END = "2026-06-22"

KOLS = ["amitisinvesting", "StockSavvyShay", "Sam_Badawi"]
dir_data = json.load(open("/workspace/logs/p5_4kol_triage/direction_3kols_v3.json"))

# === 5 条 short 修正 (基于原文 + 关键词扫描) ===
SHORT_FIXES = {
    "amitisinvesting": [
        {
            "date": "2026-05-19",
            "ticker": "HOOD",
            "old_direction": "short",
            "new_direction": "long",
            "reason": "作者说 'long term the global financial thesis is very much in tact', 短期谨慎但长期看多 — 是 long, 不是 short"
        },
        {
            "date": "2026-05-11",
            "ticker": "MU",
            "old_direction": "short",
            "new_direction": "neutral",
            "reason": "fomo warning, 不建议追高, 但没说看空也没说看多 — 不是 directional, 是 neutral/commentary"
        },
        {
            "date": "2026-05-07",
            "ticker": "IREN",
            "old_direction": "short",
            "new_direction": "neutral",
            "reason": "@joshrbob 回复, 说 IREN 稀释更多 — 是 commentary, 不是建仓"
        },
    ],
    "Sam_Badawi": [
        {
            "date": "2026-06-17",
            "ticker": "NBIS",
            "old_direction": "short",
            "new_direction": "neutral",
            "reason": "'inevitable 30% pullback' 是事件预测, 不是个人建仓声明 — neutral (P4-19 教训: 缺建仓关键词不算 directional)"
        },
        {
            "date": "2026-06-16",
            "ticker": "SNAP",
            "old_direction": "short",
            "new_direction": "neutral",
            "reason": "'going to 100. 100 cents that is' 是讽刺/搞笑, 不是真的看空建仓 — neutral"
        },
    ],
}

# 应用修正
n_fixed = 0
for h, fixes in SHORT_FIXES.items():
    print(f"\n=== {h} ===")
    for fix in fixes:
        matched = False
        for j in dir_data[h]["judgments"]:
            if j.get("date") == fix["date"] and j.get("ticker") == fix["ticker"]:
                old = j.get("llm_direction")
                if old != fix["old_direction"]:
                    print(f"  ⚠️ {fix['ticker']} {fix['date']}: 已经是 {old}, 跳过")
                    break
                j["llm_direction"] = fix["new_direction"]
                j["direction_corrected"] = True
                j["correction_note"] = fix["reason"]
                print(f"  ✓ {fix['ticker']} {fix['date']}: {old} → {fix['new_direction']}")
                print(f"    reason: {fix['reason']}")
                n_fixed += 1
                matched = True
                break
        if not matched:
            print(f"  ✗ {fix['ticker']} {fix['date']}: 未找到 ({fix['old_direction']})")

print(f"\n总修正: {n_fixed} 条")

# 重新统计
print("\n=== 修正后方向分布 ===")
for h in KOLS:
    c = Counter(j.get("llm_direction", "?") for j in dir_data[h]["judgments"])
    print(f"  @{h}: {dict(c)}")

# 保存
json.dump(dir_data, open("/workspace/logs/p5_4kol_triage/direction_3kols_v4.json", "w"), indent=2, ensure_ascii=False)
print("\n💾 saved direction_3kols_v4.json")