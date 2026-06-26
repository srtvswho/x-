"""Phase 3 P3-7 条件性预测全面排查

第一:全部预测(含 long/short)找条件句式
第二:核心多头票少数 short 原文判定
第三:统计条件性 if 是否在验证窗口内触发

输出:
- 全部条件性预测清单 (原文 + 提取的条件 + 验证窗口内是否触发)
- 核心多头票 short 原文逐条 (AAOI/AXTI/LITE/MU 等)
- 误判影响量化 (条件性被当建仓的负超额贡献)
"""
from __future__ import annotations
import os, sqlite3, re, json
from datetime import datetime, timedelta
from typing import Dict, List
from collections import Counter, defaultdict
import statistics, math

DB = "/workspace/data/signalboard_full.db"
OUT_DIR = "/workspace/outputs"
conn = sqlite3.connect(DB, timeout=30)
c = conn.cursor()

# ============== Step 1: 拉全部 prediction + raw_text ==============
print("=" * 80)
print("Step 1: 拉全部 3983 prediction + raw_text")
print("=" * 80)

sql = """
SELECT p.prediction_id, p.ticker, p.direction, p.horizon, p.conviction,
       p.thesis_summary, p.quantitative_claim,
       v.published_at, v.entry_date_actual, v.entry_price,
       v.h_1m_status, v.h_1m_excess_return, v.h_1m_raw_return,
       v.h_1w_status, v.h_1w_excess_return, v.h_1w_raw_return,
       v.h_3m_status, v.h_3m_excess_return, v.h_3m_raw_return,
       v.h_6m_status, v.h_6m_excess_return, v.h_6m_raw_return
FROM predictions p
JOIN verifications v ON p.prediction_id=v.prediction_id
WHERE p.price_source_available=1
"""
all_pred = c.execute(sql).fetchall()
print(f"全部: {len(all_pred)}")

# ============== Step 2: 拉 raw_text,关键词扫描 ==============
print()
print("=" * 80)
print("Step 2: 关键词扫描条件性预测")
print("=" * 80)

# 条件性关键词 (英文 + 中文)
CONDITIONAL_PATTERNS = [
    # 英文条件句
    (r'\bif\s+(it|the|a|an|price|dilution|funding|chip|deal|earnings|vote|hits|breaks|rallies|crashes|drops|falls|rises|breaks above|breaks below|falls below|rises above|goes|trade|holds|reaches|touches|approaches|comes|passes|fails|approves|approved|rejects|completes|complete|don\'t|doesn\'t|can|cannot|will|won\'t)\b', "if_conditional"),
    (r'\bunless\b', "unless_conditional"),
    (r'\bwhen\s+(it|the|a|an|price|dilution|if|funding|chip|deal)\b', "when_conditional"),
    (r'\bonce\b', "once_conditional"),
    (r'\bafter\s+(dilution|the|funding|deal|earnings|vote|chip|break|rally|crash|sell|drop|cut|unlock|open|approval)\b', "after_conditional"),
    (r'\bbefore\b', "before_conditional"),
    (r'\buntil\b', "until_conditional"),
    (r'\bshould\b', "should_conditional"),
    (r'\bbased on\b', "based_on"),  # 通常是条件
    (r'\bbreak(?:s|ing)?\s+(above|below|out)\b', "break_conditional"),
    (r'\bpasses?\b', "passes"),
    (r'\bfails?\b', "fails_conditional"),
    (r'\bbreaks?\b.*\$?\d+', "price_break"),
    (r'\$\d+', "price_target"),  # 价格目标也算条件
    (r'\bdip\s*buy', "dip_buy"),
    # 中文
    (r'如果', "if_zh"),
    (r'除非', "unless_zh"),
    (r'一旦', "once_zh"),
    (r'待.{1,5}之后', "after_zh"),
    (r'突破', "break_up_zh"),
    (r'跌破', "break_down_zh"),
    (r'跌到', "down_to_zh"),
    (r'涨到', "up_to_zh"),
    (r'增发.{0,10}(后|通过|完成|结束)', "after_dilution_zh"),
]

print(f"扫描 {len(CONDITIONAL_PATTERNS)} 个条件性 pattern...")
matches_per_pred = []  # (pid, ticker, direction, hits)
for r in all_pred:
    pid = r[0]
    t = r[1]
    direction = r[2]
    # 拉 raw_text
    sql_t = 'SELECT rp.raw_text FROM predictions p JOIN raw_posts rp ON p.post_id = rp.post_id WHERE p.prediction_id = ?'
    text_row = c.execute(sql_t, (pid,)).fetchone()  # c is cursor
    text = text_row[0] if text_row else ""
    text = text_row[0] if text_row else ""
    if not text:
        matches_per_pred.append((pid, t, direction, [], text, r))
        continue
    text_lower = text.lower()
    hits = []
    for pat, label in CONDITIONAL_PATTERNS:
        m = re.findall(pat, text_lower if pat.isascii() and pat[0] == "\\" else text, re.IGNORECASE if pat[0] != "如果" else 0)
        if m:
            hits.append((label, len(m), m[:3]))
    matches_per_pred.append((pid, t, direction, hits, text, r))

# 统计:有条件关键词的预测数量
n_with_any_hit = sum(1 for x in matches_per_pred if x[3])
print(f"有条件关键词: {n_with_any_hit} 条 ({n_with_any_hit/len(all_pred)*100:.1f}%)")

# 按 label 统计
label_count = Counter()
for x in matches_per_pred:
    for h in x[3]:
        label_count[h[0]] += h[1]
print(f"\n各 pattern 命中次数:")
for lbl, cnt in label_count.most_common():
    print(f"  {lbl}: {cnt}")

# ============== Step 3: 核心多头票少数 short 原文(已读过的重新输出) ==============
print()
print("=" * 80)
print("Step 3: 核心多头票少数 short 原文 (AAOI/AXTI/LITE/MU/RKLB/HIMS/ALAB/RDDT)")
print("=" * 80)

# 重新拉现在的 short (应用 B/C 后剩 147 short)
sql = """
SELECT p.prediction_id, p.ticker, p.direction,
       v.published_at, v.entry_date_actual, v.entry_price,
       v.h_1m_status, v.h_1m_excess_return, v.h_1m_raw_return
FROM predictions p
JOIN verifications v ON p.prediction_id=v.prediction_id
WHERE p.price_source_available=1 AND p.direction='short'
  AND p.ticker IN ('AAOI','AXTI','LITE','MU','RKLB','HIMS','ALAB','RDDT','CRWV','AMD','ARM','NVDA','PLTR','CRCL','IREN','ORCL')
ORDER BY p.ticker, v.published_at
"""
core_shorts = c.execute(sql).fetchall()
print(f"核心票 short 总数: {len(core_shorts)}")

# 输出每条原文 + 条件性判定
core_md = []
core_md.append("# 核心多头票少数 short 原文 + 条件性判定")
core_md.append("")
core_md.append(f"**生成时间**: {datetime.utcnow().isoformat()}Z")
core_md.append("")
core_md.append("**判定标准**:")
core_md.append("- **真·无条件做空**: 明确开 short 仓位,无条件句")
core_md.append("- **条件性看空**: 原文含 if/unless/once/after/break 等,只在条件触发时看空")
core_md.append("- **纯风险提示**: 'overvalued'/'stay away'/'be careful',不是建仓")
core_md.append("")

# 已经分类 A/B 的状态
with open("/workspace/logs/p3p6_classes.json") as json_f:
    pred_class = json.load(json_f)

for r in core_shorts:
    pid = r[0]
    t = r[1]
    direction = r[2]
    pub = r[3]
    edate = r[4]
    eprice = r[5]
    s1m = r[6]
    e1m = r[7]
    r1m = r[8]
    # 原文
    sql_t = 'SELECT rp.raw_text FROM predictions p JOIN raw_posts rp ON p.post_id = rp.post_id WHERE p.prediction_id = ?'
    text_row = c.execute(sql_t, (pid,)).fetchone()
    text = text_row[0] if text_row else ""
    
    # 条件性检测
    conditional_keywords = []
    text_lower = text.lower()
    if re.search(r'\bunless\b', text_lower): conditional_keywords.append("unless")
    if re.search(r'\bonce\b', text_lower): conditional_keywords.append("once")
    if re.search(r'\bafter\s+(dilution|funding|deal|earnings|vote|chip|break|rally|crash|sell|drop|cut|unlock|approval)', text_lower): conditional_keywords.append("after-X")
    if re.search(r'\bbreak(?:s|ing)?\s+(above|below|out)', text_lower): conditional_keywords.append("break-X")
    if re.search(r'\bpasses?\b', text_lower): conditional_keywords.append("passes")
    if re.search(r'\bfails?\b', text_lower): conditional_keywords.append("fails")
    if re.search(r'\bbased on\b', text_lower): conditional_keywords.append("based_on")
    if "如果" in text: conditional_keywords.append("如果")
    if "除非" in text: conditional_keywords.append("除非")
    if "一旦" in text: conditional_keywords.append("一旦")
    if "突破" in text or "跌破" in text: conditional_keywords.append("突破/跌破")
    if "增发" in text: conditional_keywords.append("增发")
    if re.search(r'\$\d+', text): conditional_keywords.append("价格目标")
    
    cat = pred_class.get(pid, "未明确")
    
    core_md.append(f"## {t} — pub={pub[:19]} (entry={edate}, ${eprice:.2f})")
    core_md.append(f"- direction: {direction}, 1m: {s1m}, excess={e1m*100 if isinstance(e1m,(int,float)) else 0:+.2f}%, raw={r1m*100 if isinstance(r1m,(int,float)) else 0:+.2f}%")
    core_md.append(f"- **P3-6 分类**: {cat}")
    core_md.append(f"- **条件关键词**: {conditional_keywords if conditional_keywords else '无'}")
    core_md.append(f"- **原文**:")
    core_md.append("```")
    for line in text.split("\n"):
        core_md.append(f"| {line}")
    core_md.append("```")
    core_md.append("")


# ============== Step 4: 全部条件性预测清单 ==============
print()
print("=" * 80)
print("Step 4: 全部条件性预测清单 (含原文摘要 + if 条件是否触发)")
print("=" * 80)

# 核心:对每条命中的,提取条件 + 给出判定
def extract_condition(text):
    """简单提取 if 后的关键条件"""
    text_lower = text.lower()
    # if X happens, then Y
    m = re.search(r'if\s+(?:the\s+)?([^,.]{5,80})?(?:then|,|\.|;|$)', text_lower)
    if m:
        return m.group(1).strip()
    m = re.search(r'if\s+(it|the|a|an|price|dilution|funding|deal|earnings|vote|hits|breaks|drops|falls|rises|passes|fails|approves|completes)\s+([^,.]{0,60})?(?:then|,|\.|;|$)', text_lower)
    if m:
        return " ".join([g for g in m.groups() if g]).strip()
    return None

cond_list = []
for x in matches_per_pred:
    pid, t, direction, hits, text, full_row = x
    if not hits:
        continue
    # 只取最相关的条件关键词
    primary_hit = hits[0]
    if primary_hit[0] in ("price_target", "based_on"):
        continue  # 太宽泛,不算严格条件
    cond_text = extract_condition(text)
    cond_list.append({
        "pid": pid, "ticker": t, "direction": direction,
        "primary_label": primary_hit[0],
        "all_hits": [h[0] for h in hits],
        "cond_text": cond_text,
        "text": text,
        "row": full_row,
    })

print(f"严格条件性预测: {len(cond_list)} 条")

# 输出条件性预测清单 (前 50 条)
cond_md = []
cond_md.append("# 全部条件性预测清单")
cond_md.append("")
cond_md.append(f"**生成时间**: {datetime.utcnow().isoformat()}Z")
cond_md.append("")
cond_md.append("**判定维度**:")
cond_md.append("- A 类: 真·无条件做空 → 正常验证 (A)")
cond_md.append("- B 类: 纯风险提示 → 改 neutral (B)")
cond_md.append("- C 类: 明确误判 → 改回正确方向 (C)")
cond_md.append("- **D 类 (新)**: 条件性预测,if 未触发 → 移出胜率分母 (condition_not_triggered)")
cond_md.append("")

for i, c in enumerate(cond_list, 1):
    pid = c['pid']
    t = c['ticker']
    direction = c['direction']
    pub = c['row'][7]  # published_at
    edate = c['row'][8]
    eprice = c['row'][9]
    s1m = c['row'][10]
    e1m = c['row'][11]
    r1m = c['row'][12]
    
    cond_md.append(f"## [{i}] {t} {direction} — pub={pub[:19]}")
    cond_md.append(f"- entry={edate}, ${eprice if isinstance(eprice,(int,float)) else 0:.2f}, 1m: {s1m}, excess={e1m*100 if isinstance(e1m,(int,float)) else 0:+.2f}%, raw={r1m*100 if isinstance(r1m,(int,float)) else 0:+.2f}%")
    cond_md.append(f"- **条件关键词**: {c['primary_label']} (all: {c['all_hits']})")
    if c['cond_text']:
        cond_md.append(f"- **提取的条件**: if {c['cond_text'][:100]}")
    cond_md.append(f"- **原文** (前 400 chars):")
    cond_md.append("```")
    txt = c['text'][:400]
    for line in txt.split("\n"):
        cond_md.append(f"| {line}")
    cond_md.append("```")
    cond_md.append("")


# ============== Step 5: 验证窗口内 if 条件是否触发 ==============
print()
print("=" * 80)
print("Step 5: 验证窗口内 if 条件是否触发 (量化)")
print("=" * 80)

# 关键问题: 如果她的 if 条件没触发,但代码无脑建仓,负超额全怪这个
# 我们需要按 ticker + 已知事件,逐条判定

# 已知事件清单 (人工)
EVENTS = {
    "AAOI": {
        "ATM_$250m_2026-03-12": {"date": "2026-03-12", "triggered": True, "outcome": "$250m ATM 增发成功"},
    },
    "AXTI": {
        "50m_share_vote_2026-04-14": {"date": "2026-04-14", "triggered": True, "outcome": "50m 增发 vote 通过"},
    },
    "IREN": {
        "$6B_ATM_2026-03-08": {"date": "2026-03-08", "triggered": True, "outcome": "$6B ATM filed"},
    },
    "CRCL": {
        "December_unlock_2025-12-02": {"date": "2025-12-02", "triggered": True, "outcome": "Class A unlock"},
        "trade_above_half_COIN": {"date": None, "triggered": False, "outcome": "CRCL 始终未到 COIN 一半"},
    },
    "BMNR": {
        "ETH_appreciation": {"date": None, "triggered": "varies", "outcome": "BMNR depends on ETH"},
    },
    "RGTI": {
        "no_meaningful_revenue": {"date": None, "triggered": True, "outcome": "估值始终 high,revenue 没来"},
    },
    "QBTS": {
        "no_meaningful_revenue": {"date": None, "triggered": True, "outcome": "估值始终 high,revenue 没来"},
    },
    "NVDA": {
        "OpenAI_deal": {"date": "2025-12-17", "triggered": True, "outcome": "OpenAI + AMZN 10B 资金"},
    },
    "AMD": {
        "OpenAI_dominance": {"date": None, "triggered": True, "outcome": "Gemini/Claude leapfrog GPT"},
    },
    "MU": {
        "MU_dg_hold": {"date": None, "triggered": True, "outcome": "MU 是 long 不是 short,LLM 误抽"},
    },
    "RDDT": {
        "in_sell_list": {"date": "2025-09-29", "triggered": True, "outcome": "在 Monday Thoughts Sell 列表"},
    },
    "HIMS": {
        "drop_50_70_pct": {"date": "2026-02-17", "triggered": False, "outcome": "HIMS 实际涨 50%,LLM 抽 short 对,但预测错方向"},
    },
    "ALAB": {
        "opened_up_short_hedge": {"date": "2025-09-08", "triggered": True, "outcome": "明确开 short"},
    },
}

# 输出每条条件性预测的 if 触发评估
eval_md = []
eval_md.append("# 条件性预测 if 触发评估")
eval_md.append("")
eval_md.append(f"**生成时间**: {datetime.utcnow().isoformat()}Z")
eval_md.append("")

trigger_count = {"triggered": 0, "not_triggered": 0, "uncertain": 0}
total_excess_contribution = {"triggered_neg": 0.0, "not_triggered_neg": 0.0}

for c in cond_list[:50]:  # 只列前 50
    pid = c['pid']
    t = c['ticker']
    direction = c['direction']
    pub = c['row'][7]
    edate = c['row'][8]
    eprice = c['row'][9]
    s1m = c['row'][10]
    e1m = c['row'][11]
    r1m = c['row'][12]
    
    # 启发式判定
    if t in EVENTS:
        ticker_events = EVENTS[t]
    else:
        ticker_events = {}
    
    eval_md.append(f"## {t} {direction} — pub={pub[:19]}")
    eval_md.append(f"- entry={edate}, ${eprice if isinstance(eprice,(int,float)) else 0:.2f}, 1m: {s1m}, excess={e1m*100 if isinstance(e1m,(int,float)) else 0:+.2f}%")
    eval_md.append(f"- 条件: if {c['cond_text'][:120] if c['cond_text'] else '(unknown)'}")
    eval_md.append(f"- 原文 (摘要): `{c['text'][:300]}`")
    eval_md.append(f"- 已知事件: {ticker_events if ticker_events else 'N/A — 用户需判定'}")
    eval_md.append("")

# 落报告
all_md = core_md + ["\n---\n"] + cond_md + ["\n---\n"] + eval_md
with open(os.path.join(OUT_DIR, "phase3_p7_conditional_audit.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(all_md))
print(f"✅ 落 outputs/phase3_p7_conditional_audit.md")

# 简短摘要
print()
print("=" * 80)
print("摘要")
print("=" * 80)
print(f"- 总预测: {len(all_pred)}")
print(f"- 命中条件关键词: {n_with_any_hit} 条 ({n_with_any_hit/len(all_pred)*100:.1f}%)")
print(f"- 严格条件性 (排除 price_target/based_on): {len(cond_list)} 条")
print()
print("**核心发现** (我已读过的):")
print("1. AAOI 3 short 全部含 'if/short-term bearish + long-term bullish',hedged/条件性")
print("2. AXTI 1 short 'if dilution passes... I personally would not hold... if it fails, I expect a recovery',hedged")
print("3. ALAB 2 short: [1] 'opened up short as hedge' 真建仓, [2] 'is a bit overvalued' 风险提示")
print("4. ARM 'personally pretty bearish' 真看空,但无具体 if")
print("5. AMD 'My stance changed' 立场转变,但 her own words: 偏向 OpenAI 看空")
print("6. IREN 24 几乎全是 'I'd consider flipping long again [after dilution]' - 阶段性方向")
print("7. CRCL 8 'great short if above 1/2 of COIN' - 价格条件,if 未触发")
print("8. CRWV 11 'short term upside but medium-long term debt' - 时间条件,if 部分触发")
print("9. NVDA 'De-Risking AI DC trade' - 行业分析,不是个人持仓")
print("10. BKSY [2] 'dip buying opportunity' - 反指,LLM 抽 short 错 (C 类)")
print()
print("**当前验证代码 (verify_one) 完全忽略 if 条件**:")
print("```python")
print("entry_date = next_trading_day(pub_dt)  # 直接次日建仓")
print("# 后面 for h_name, h_days: 直接 exit_date = add_trading_days(entry_date, h_days)")
print("```")
print("→ 所有 if 条件未触发的预测,都被当建仓算,直接计入 hit/miss")

conn.close()
