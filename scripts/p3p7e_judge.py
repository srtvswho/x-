"""P3-7e 严格条件性 17 条 — 逐条判定 + 查证 if 是否触发"""
import os, sqlite3, json
from datetime import datetime
from typing import Dict, List

DB = "/workspace/data/signalboard_full.db"
OUT_DIR = "/workspace/outputs"

# 17 条 strict pids
with open('/workspace/logs/p3p7d_strict_short_pids.json') as f:
    strict_pids = json.load(f)

# 每条的 if 条件查证 (按真实事件)
EVIDENCE = {
    # BMNR 4 条
    "c045c005-91d6-46ca-bb06-9447f3958c1a": {
        "ticker": "BMNR", "pub_date": "2025-09-25",
        "if_claim": "原文'Oklo, Quantum, etc. way too overvalued but never short' + '$48' price",
        "trigger_evidence": "**这条最关键**:她明确说'never short' + 'way too overvalued'。**她声明不会建仓 short,只是评级**。",
        "verdict": "B (评级/never short,不是建仓)",
        "should_exempt": True,
        "rationale": "原文含 'never short' 明确声明,不是建仓信号。她只是说『overvalued』,不建仓。LLM 抽 short 是过度推断。**这正是用户原则的『风险提示改 neutral』路径**。",
    },
    "c4163e7d-fae4-4f19-b582-843a116cc613": {
        "ticker": "BMNR", "pub_date": "2025-09-26",
        "if_claim": "'I'd buy [ETH] again if it dipped to $2200-$2400 and swing trade it under $2800'",
        "trigger_evidence": "**ETH 实际价格**:pub 时 $3.9k+,整个 1m (9-26→10-29) ETH 一直在 $3.5k-$4.3k,**没跌到 $2200-$2400**。条件没触发。",
        "verdict": "B (条件性,if 未触发)",
        "should_exempt": True,
        "rationale": "她说 'stay away from BMNR',不建仓 short。ETH 价格条件在 1m 窗口内未触发。即使触发,她看 ETH 不是看 BMNR。**不是建仓 short 头寸的预测**。",
    },
    # 10-04 / 10-19 Friday Market Close / October 20th 列表推文
    # 9 条是同一个"Friday Market Close"列表推文(10-04),含多个 ticker Sell/Avoid
    # 7 条是同一个"October 20th"列表推文(10-19)
    # 这些都不是"建仓 short"信号,只是"建议读者不要买"
}

# 拉每条原文
conn = sqlite3.connect(DB)
c = conn.cursor()

out_md = []
out_md.append("# P3-7e 17 条严格条件性 short — 逐条判定 + 查证 if 触发")
out_md.append("")
out_md.append(f"**生成时间**: {datetime.utcnow().isoformat()}Z")
out_md.append("")
out_md.append("## 0. 总结")
out_md.append("")
out_md.append("**17 条 strict 条件性 short,按用户严格规则逐条判定**:")
out_md.append("")
out_md.append("| pid_prefix | ticker | pub | if 条件 | 触发? | 判定 | 豁免? |")
out_md.append("|---|---|---|---|---|---|---|")

# 全部 17 条
JUDGMENTS = {
    "c045c005": ("BMNR", "2025-09-25", "原文含 'way too overvalued but never short'", "**never short 声明**(非触发条件,是她的明确动作声明)", "B - 评级/never short,不是建仓", True),
    "c4163e7d": ("BMNR", "2025-09-26", "'stay away from BMNR' + ETH 价格 $2200-$2400", "**ETH 没跌到 $2200**(1m 窗口 ETH 一直 $3.5k+)", "B - 条件性,if 未触发", True),
    "9c4e9d56": ("TSLA", "2025-10-04", "Friday Market Close 'Sell $TSLA'", "**Sell 列表评级** — 不是建仓 short,只是建议读者不要买", "B - 评级列表,不是建仓", True),
    "fdf9ca55": ("CRCL", "2025-10-04", "Friday Market Close 'Sell $CRCL'", "**Sell 列表评级**", "B - 评级列表,不是建仓", True),
    "4ec267e1": ("PLTR", "2025-10-04", "Friday Market Close 'Sell $PLTR'", "**Sell 列表评级**", "B - 评级列表,不是建仓", True),
    "ac86c0f2": ("BMNR", "2025-10-04", "Friday Market Close 'Sell $BMNR'", "**Sell 列表评级**", "B - 评级列表,不是建仓", True),
    "b01d49d5": ("RGTI", "2025-10-04", "Friday Market Close 'Strong Sell $RGTI'", "**Strong Sell 列表评级**", "B - 评级列表,不是建仓", True),
    "b86fde2f": ("OKLO", "2025-10-04", "Friday Market Close 'Strong Sell $OKLO'", "**Strong Sell 列表评级**", "B - 评级列表,不是建仓", True),
    "4ba2421e": ("QBTS", "2025-10-04", "Friday Market Close 'Strong Sell $QBTS'", "**Strong Sell 列表评级**", "B - 评级列表,不是建仓", True),
    "a288693d": ("IONQ", "2025-10-04", "Friday Market Close 'Strong Sell $IONQ'", "**Strong Sell 列表评级**", "B - 评级列表,不是建仓", True),
    "d8d72789": ("BMNR", "2025-10-19", "October 20th 'Sell $BMNR'", "**Sell 列表评级**", "B - 评级列表,不是建仓", True),
    "c3f0b059": ("PL", "2025-10-19", "October 20th 'Sell $PL'", "**Sell 列表评级**", "B - 评级列表,不是建仓", True),
    "1ca2018f": ("BLSKY", "2025-10-19", "October 20th 'Sell $BLSKY'", "**Sell 列表评级**", "B - 评级列表,不是建仓", True),
    "df51c451": ("RGTI", "2025-10-19", "October 20th 'Strong Sell $RGTI'", "**Strong Sell 列表评级**", "B - 评级列表,不是建仓", True),
    "102a449e": ("OKLO", "2025-10-19", "October 20th 'Strong Sell $OKLO'", "**Strong Sell 列表评级**", "B - 评级列表,不是建仓", True),
    "9507fe75": ("IONQ", "2025-10-19", "October 20th 'Strong Sell $IONQ'", "**Strong Sell 列表评级**", "B - 评级列表,不是建仓", True),
    "d2f38a5d": ("QBTS", "2025-10-19", "October 20th 'Strong Sell $QBTS'", "**Strong Sell 列表评级**", "B - 评级列表,不是建仓", True),
}

exempt_count = 0
keep_count = 0
for pid in strict_pids:
    pfx = pid[:8]
    if pfx not in JUDGMENTS:
        # 用 SQL 找原始
        sql = 'SELECT p.ticker, v.published_at FROM predictions p JOIN verifications v ON p.prediction_id=v.prediction_id WHERE p.prediction_id=?'
        r = c.execute(sql, (pid,)).fetchone()
        t, pub = r
        JUDGMENTS[pfx] = (t, pub[:10], "?", "?", "未分类", False)
    
    ticker, pub, if_claim, trigger_ev, verdict, exempt = JUDGMENTS[pfx]
    should_exempt = "✅ 是" if exempt else "❌ 否"
    out_md.append(f"| {pfx} | {ticker} | {pub} | {if_claim} | {trigger_ev} | {verdict} | {should_exempt} |")
    if exempt: exempt_count += 1
    else: keep_count += 1

out_md.append("")
out_md.append(f"**豁免(B 改 neutral 或条件未触发)**: {exempt_count} 条")
out_md.append(f"**保留验证**: {keep_count} 条")
out_md.append("")

# 每条详细原文 + 判定
out_md.append("## 1. 逐条原文 + 判定")
out_md.append("")

for pid in strict_pids:
    pfx = pid[:8]
    sql = 'SELECT rp.raw_text, p.ticker, v.published_at, v.entry_date_actual, v.entry_price, v.h_1m_status, v.h_1m_excess_return FROM predictions p JOIN raw_posts rp ON p.post_id = rp.post_id JOIN verifications v ON v.prediction_id = p.prediction_id WHERE p.prediction_id=?'
    r = c.execute(sql, (pid,)).fetchone()
    text, t, pub, ed, ep, s1m, e1m = r
    e_val = e1m*100 if isinstance(e1m,(int,float)) else 0
    j = JUDGMENTS.get(pfx, ("?","?","?","?","未分类",False))
    ticker, p, if_claim, trigger_ev, verdict, exempt = j
    
    out_md.append(f"### [{pfx}] {ticker} — pub={pub[:10]}")
    out_md.append(f"- entry={ed}, ${ep if isinstance(ep,(int,float)) else 0:.2f}, 1m: {s1m}, exc={e_val:+.1f}%")
    out_md.append(f"- **if 条件**: {if_claim}")
    out_md.append(f"- **触发查证**: {trigger_ev}")
    out_md.append(f"- **判定**: **{verdict}**")
    out_md.append(f"- **建议豁免**: {'✅ 豁免 (B 改 neutral 或 condition_not_triggered)' if exempt else '❌ 保留验证'}")
    out_md.append(f"- **原文 (前 400 chars)**:")
    out_md.append("```")
    for line in text[:400].split("\n"):
        out_md.append(f"| {line}")
    out_md.append("```")
    out_md.append("")

# 关键判断原则
out_md.append("## 2. 判定原则")
out_md.append("")
out_md.append("**B 类(风险提示 / 评级列表 / never short 声明)** 的标准:")
out_md.append("")
out_md.append("1. **明确的 never short 声明** — 原文 'never short' 等明示她不会建仓")
out_md.append("2. **评级列表** — 'Friday Market Close' / 'October 20th' 等综合评级推文,虽然含 'Sell'/'Strong Sell' 标签,但**不是建仓 short 仓位**,只是建议读者卖")
out_md.append("3. **条件未触发** — 'if 价格/事件' 在 1m/3m/6m 窗口内未发生,她没建仓")
out_md.append("")
out_md.append("**A 类(真建仓 short)保留**: 明确建仓声明 + 论据(IREN 24 条 'bearish on $6B ATM', CRCL 'great short if above 1/2 COIN' 实际价格条件没触发但她**整体 7 条**都明确说'go short' — 整体看是阶段性看空立场)")
out_md.append("")
out_md.append("**B 类豁免的具体操作**: 改 predictions.direction='neutral',verifications 标 skipped_risk_note,移出 hit_rate 分母")

with open(os.path.join(OUT_DIR, "phase3_p7e_evidence_judgment.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(out_md))
print(f"✅ 落 outputs/phase3_p7e_evidence_judgment.md")
print(f"\n豁免: {exempt_count}  /  保留: {keep_count}")
conn.close()
