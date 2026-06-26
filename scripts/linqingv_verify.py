"""LinQingV 判断兑现验证 — 22 条全跑, 硬/软 + 可操作/背景分类

铁律:
- 对错都列 (不许选择性记忆)
- 特别盯 #8 QQQ 几年看空
- 分"可操作具体判断" vs "宏观判断" 统计
"""
from __future__ import annotations
import json
from datetime import datetime, timedelta
from pathlib import Path


PRICE_DIR = Path("/workspace/data/price_cache")
DATA_END = "2026-06-22"   # 最后有效交易日 (Polygon 数据)
JUDGMENTS = json.load(open("/workspace/logs/p5_linqingv/judgments_deduped.json"))


# === 标的映射 (每条判断 → 可验证的 ticker + bench) ===
TARGET_MAP = {
    # 1. WTI 原油 5 月 200 刀 (2025-03-09)
    1: {
        "ticker": "USO",  # WTI 原油 ETF (替代 WTI 期货)
        "bench": "SPY",
        "rationale": "WTI 原油 → USO ETF proxy. 5 月前海峡不通 → 200 刀上. 用 entry=2025-03-10, exit=2025-05-31",
        "kind": "commodity",  # 商品
        "operable": False,  # 不可直接操作 (有专业门槛)
    },
    # 2. EM 新兴市场 2025 内跑赢 (2025-03-11)
    2: {
        "ticker": "EEM",  # iShares MSCI EM ETF
        "bench": "SPY",
        "rationale": "EM 跑赢 DM → EEM/SPY 相对走势. exit=2025-12-31",
        "kind": "macro",
        "operable": False,
    },
    # 3. 商品超级大年 (2025-03-12)
    3: {
        "ticker": "CPER",  # 铜 ETF
        "bench": "SPY",
        "rationale": "商品超级大年 → 至少铜价应涨. exit=2025-12-31",
        "kind": "macro",
        "operable": False,
    },
    # 4. 美国汽油下周必破 4 刀 (2025-03-14)
    4: {
        "ticker": "USO",  # 用 WTI 油价 proxy (零售汽油 = 原油 + 0.65 spread)
        "bench": "SPY",
        "rationale": "汽油破 4 刀 = 原油 + spread. 油价 entry 2025-03-14, exit 2025-03-21 (1 周)",
        "kind": "macro",
        "operable": False,
    },
    # 5. 美股金融板块年内最弱 (2025-03-15)
    5: {
        "ticker": "XLF",  # Financial Select Sector SPDR
        "bench": "SPY",
        "rationale": "美股金融 → XLF. entry=2025-03-17, exit=2025-12-31",
        "kind": "sector",
        "operable": True,  # 可操作 (有 ETF)
    },
    # 6. A 股银行 (2025-03-15) — A 股不能 Polygon 验
    6: {
        "ticker": None,  # 跳过
        "bench": None,
        "rationale": "A 股银行板块 → 512800 (中证银行 ETF) 等 A 股 ETF, Polygon 拉不到",
        "kind": "sector",
        "operable": True,
        "skip_reason": "A 股, Polygon 不支持",
    },
    # 7. 权益资产看空 (2025-03-19) — 用 SPY 代理
    7: {
        "ticker": "SPY",
        "bench": "QQQ",
        "rationale": "权益资产看空 → SPY 跌 (vs QQQ 跌更多或 SPY 跌). 整个 2025 年",
        "kind": "macro",
        "operable": True,
    },
    # 8. CDNS+SNPS 中短期 (2025-03-22) — 美股
    8: {
        "ticker": "CDNS",
        "bench": "SOXX",
        "rationale": "Cadence → CDNS. 中短期 ~ 6 月. entry=2025-03-24, exit=2025-09-30",
        "kind": "stock",
        "operable": True,
    },
    # 9. 全球增长看多 2025 H1 (2025-03-30) — 用 SPY proxy
    9: {
        "ticker": "SPY",
        "bench": "EEM",
        "rationale": "美国增长看多 → SPY 跑赢 EM. exit=2025-06-30",
        "kind": "macro",
        "operable": False,
    },
    # 10. 全球增长 2026 H2 走弱 (2025-03-30) — 还没到期
    10: {
        "ticker": "SPY",
        "bench": "EEM",
        "rationale": "2026 H2 走弱 → SPY < 2026 H1. 当前 2026-06, H2 未到, 标 pending",
        "kind": "macro",
        "operable": False,
    },
    # 11. 中国 PPI 不到一年消退 (2025-04-01) — 用 MCHI + FXI proxy
    11: {
        "ticker": "FXI",  # A50 ETF
        "bench": "SPY",
        "rationale": "中国 PPI 消退 → A 股/A50 不再通胀. 用 FXI proxy 1 年. exit=2026-04-01",
        "kind": "macro",
        "operable": False,
    },
    # 12. CCL 覆铜板 2025 涨 (2025-04-15) — A 股不能验, 用 PCB ETF 替代
    12: {
        "ticker": None,  # A 股
        "bench": None,
        "rationale": "CCL 覆铜板 → 600183 (生益科技) A 股, 拉不到. 用 iShares Semiconductor (SOXX) proxy 弱替代",
        "kind": "sector",
        "operable": True,
        "skip_reason": "A 股, Polygon 不支持",
    },
    # 13. AVGO 博通 2025-05-07 (硬)
    13: {
        "ticker": "AVGO",
        "bench": "SOXX",
        "rationale": "AVGO 推荐 → 跑赢 SOXX. 3-12 月 (entry=2025-05-08, exit=2026-05-08)",
        "kind": "stock",
        "operable": True,
    },
    # 14. 002384 (东山精密) 光模块 1M/月 2025-06-17 — A 股, 不能验
    14: {
        "ticker": None,
        "bench": None,
        "rationale": "002384.SZ (东山精密) A 股, Polygon 拉不到",
        "kind": "stock",
        "operable": True,
        "skip_reason": "A 股, Polygon 不支持",
    },
    # 15. QQQ 未来几年崩 (2026-02-28)
    15: {
        "ticker": "QQQ",
        "bench": "SPY",
        "rationale": "QQQ 几年看空 — 短期窗口: entry=2026-03-02, exit=2026-06-22 (~ 4 月). 看 QQQ 是否跌 / 跑输 SPY",
        "kind": "macro",  # 算宏观 (大盘判断)
        "operable": True,
    },
    # 16. 上证 4-5 月验证突破 (2026-03-22) — A 股, 不能验
    16: {
        "ticker": None,
        "bench": None,
        "rationale": "上证指数 → 用 FXI (A50) proxy 弱替代 (高相关 ~ 0.85)",
        "kind": "macro",
        "operable": True,
        "fallback_ticker": "FXI",  # 用 FXI 弱替代
    },
    # 17. SMIC 中芯 2Q26 Rev beat (2026-05-15) — 港股 0981.HK 不能验
    17: {
        "ticker": None,
        "bench": None,
        "rationale": "SMIC → 0981.HK Polygon 不支持. 用 SOXX (半导体 ETF) proxy 弱替代",
        "kind": "stock",
        "operable": True,
        "skip_reason": "港股, Polygon 不支持",
    },
    # 18. 华为链下半年 (2026-05-18) — A 股概念, 不能验
    18: {
        "ticker": None,
        "bench": None,
        "rationale": "华为链 → A 股概念 (昇腾/寒武纪/阿里), Polygon 拉不到",
        "kind": "sector",
        "operable": True,
        "skip_reason": "A 股/概念股, Polygon 不支持",
    },
    # 19. 先进封装设备/材料 (2026-05-25) — A 股, 不能验, 但有 AMAT/ASML 美股 proxy
    19: {
        "ticker": "AMAT",  # 应用材料
        "bench": "SOXX",
        "rationale": "先进封装设备 → AMAT (美股 设备龙头). 用 entry=2026-05-26, exit=2026-06-22 (1 月看)",
        "kind": "sector",
        "operable": True,
    },
    # 20. N1X AI PC 伪需求 (2026-05-31) — 卖空判断, 标的 INTC (N1X 用 x86) — 不直接对 INTC 价格, 难验
    20: {
        "ticker": "INTC",  # 假设 AI PC 看空 → 半导体设备/PC 链跌
        "bench": "SMH",
        "rationale": "AI PC 伪需求 → 半导体设备看空. 用 INTC (N1X 用 x86) proxy 1 月",
        "kind": "sector",
        "operable": True,
    },
    # 21. WFE 2026 涨 (2026-06-02) — 用 AMAT/LRCX proxy
    21: {
        "ticker": "AMAT",
        "bench": "SOXX",
        "rationale": "WFE 涨 → 设备股跑赢板块. 1 月窗口",
        "kind": "sector",
        "operable": True,
    },
    # 22. 日系半导体设备 26H2 回升 (2026-06-12) — 标 "未来", 现在没法验
    22: {
        "ticker": None,
        "bench": None,
        "rationale": "日系设备回升 → 26H2 预期, 当前 2026-06 H2 未到, pending",
        "kind": "sector",
        "operable": True,
    },
}


def find_price(bars, target):
    """找 >= target 的第一个 close。"""
    for b in bars:
        if b["date"] >= target:
            return b["c"], b["date"]
    return None, None


def parse_signal_date(date_str):
    """'YYYY-MM-DD' → next trading day。"""
    if not date_str:
        return None
    d = datetime.strptime(date_str, "%Y-%m-%d")
    # 推到 next weekday
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d.strftime("%Y-%m-%d")


def verify_judgment(idx, j, info):
    """验一条。"""
    ticker = info.get("ticker") or info.get("fallback_ticker")
    bench = info.get("bench")
    if not ticker:
        return {
            "idx": idx,
            "judge": j,
            "info": info,
            "verdict": "skipped",
            "reason": info.get("skip_reason", "无可验证 ticker"),
        }
    entry_date = parse_signal_date(j["date"])
    # exit date: 默认 entry + 1 年 (保守), 但 DATA_END 是上限
    # 用 (1年, DATA_END) min
    exit_date = min(DATA_END, (datetime.strptime(entry_date, "%Y-%m-%d") + timedelta(days=365)).strftime("%Y-%m-%d"))
    # 另加: 退到 2026-06-12 (QQQ 等 cache 最后一天)
    exit_date = min(exit_date, "2026-06-12")

    # 拉数据
    try:
        bars = json.load(open(PRICE_DIR / f"{ticker}_FULL_HISTORY.json"))
    except FileNotFoundError:
        return {
            "idx": idx, "judge": j, "info": info,
            "verdict": "no_data", "reason": f"无 {ticker} 价格数据",
        }
    e_px, e_actual = find_price(bars, entry_date)
    x_px, x_actual = find_price(bars, exit_date)
    if not e_px or not x_px:
        return {
            "idx": idx, "judge": j, "info": info,
            "verdict": "no_px", "reason": f"{ticker} entry/exit px 缺失",
        }

    raw_ret = (x_px - e_px) / e_px * 100
    bench_ret = 0
    excess = 0
    hit = None
    if bench:
        try:
            bbars = json.load(open(PRICE_DIR / f"{bench}_FULL_HISTORY.json"))
            be, _ = find_price(bbars, entry_date)
            bx, _ = find_price(bbars, exit_date)
            if be and bx:
                bench_ret = (bx - be) / be * 100
                excess = raw_ret - bench_ret
        except FileNotFoundError:
            pass

    # hit 判定 — 默认看 raw_ret, 轮动/防御看 excess
    direction = j.get("direction", "")
    jtype = j.get("type", "")
    is_short = any(k in direction for k in ["看空", "防御", "看跌", "崩"])
    is_long = any(k in direction for k in ["看多", "看涨", "推荐"])
    is_rotation = jtype in ("板块轮动",) or "轮动" in direction or "防御" in direction
    if is_rotation:
        # 轮动/防御 — 看 excess (跑赢/跑输对手)
        if is_short:
            hit = excess < 0  # 跑输对手 = 对
        elif is_long:
            hit = excess > 0  # 跑赢对手 = 对
        else:
            hit = None
    else:
        # 默认看 raw_ret
        if is_short:
            hit = raw_ret < 0
        elif is_long:
            hit = raw_ret > 0
        else:
            hit = None

    return {
        "idx": idx,
        "judge": j,
        "info": info,
        "entry_date": entry_date,
        "exit_date": exit_date,
        "entry_px": e_px,
        "exit_px": x_px,
        "raw_ret": raw_ret,
        "bench_ret": bench_ret,
        "excess_ret": excess,
        "hit": hit,
        "verdict": "verified",
    }


def main():
    print("=" * 60)
    print("LinQingV 22 条判断兑现验证")
    print("=" * 60)

    results = []
    for i, j in enumerate(JUDGMENTS, 1):
        info = TARGET_MAP.get(i, {})
        r = verify_judgment(i, j, info)
        results.append(r)

    # 统计
    verified = [r for r in results if r.get("verdict") == "verified"]
    skipped = [r for r in results if r.get("verdict") == "skipped"]
    no_data = [r for r in results if r.get("verdict") == "no_data"]

    # 硬/软 分类 (用户给的分类)
    HARD_BY_USER = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]  # 用户原 11 条 → 全部
    SOFT_BY_USER = [12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]
    # 修正: 用户标 #1 #10 软, #2 #3 #4 #5 #6 #7 #8 #9 #11 硬
    # 但 #1 #10 是 1 2 12 (我加) - 让我用 idx 标
    # 实际我的 idx: 1=原油, 2=EM, 3=商品, 4=汽油, 5=金融, 6=银行, 7=权益, 8=CDNS, 9=增长, 10=2026H2, 11=PPI
    # 用户原 11 条: 1=EM 软, 2=AVGO 硬, 3=商品 硬, 4=上证 硬, 5=CDNS 硬, 6=银行, 7=宝丰, 8=QQQ 硬, 9=华为链 硬, 10=EM 软, 11=美 26H2 硬
    # 跟我新 22 条的 idx 不一致 — 我用 j["type"] 区分

    # 按 type 分类
    by_type = {"宏观择时": [], "个股选股": [], "板块轮动": [], "产业卡点": []}
    for r in verified:
        t = r["judge"].get("type", "?")
        if t in by_type:
            by_type[t].append(r)

    # 按 operable 分类
    operable = [r for r in verified if r["info"].get("operable")]
    macro_only = [r for r in verified if not r["info"].get("operable")]

    print(f"\n--- 验证统计 ---")
    print(f"总判断: {len(JUDGMENTS)}")
    print(f"已验证: {len(verified)}")
    print(f"跳过 (A 股等): {len(skipped)}")
    print(f"无数据: {len(no_data)}")

    if verified:
        n_hit = sum(1 for r in verified if r["hit"])
        print(f"\n已验证中 hit: {n_hit}/{len(verified)} = {n_hit/len(verified)*100:.1f}%")
        n_op_hit = sum(1 for r in operable if r["hit"])
        n_macro_hit = sum(1 for r in macro_only if r["hit"])
        print(f"  可操作 ({len(operable)}): hit {n_op_hit}/{len(operable)} = {n_op_hit/max(len(operable),1)*100:.1f}%")
        print(f"  仅宏观 ({len(macro_only)}): hit {n_macro_hit}/{len(macro_only)} = {n_macro_hit/max(len(macro_only),1)*100:.1f}%")

    print(f"\n--- 逐条结果 ---")
    for r in results:
        idx = r["idx"]
        j = r["judge"]
        if r["verdict"] == "verified":
            status = "✅" if r["hit"] else "❌"
            jt = str(j.get("type", "?"))
            direction = str(j.get("direction", "?"))
            target = str(j.get("target", "?"))[:30]
            ticker = r["info"].get("ticker") or r["info"].get("fallback_ticker") or "?"
            raw = r.get("raw_ret")
            exc = r.get("excess_ret")
            try:
                raw_str = f"{raw:+.1f}%" if raw is not None else "—"
            except (TypeError, ValueError):
                raw_str = "—"
            try:
                exc_str = f"{exc:+.1f}%" if exc is not None else "—"
            except (TypeError, ValueError):
                exc_str = "—"
            operable_str = "🔧" if r["info"].get("operable") else "🌐"
            print(f"  {status} {operable_str} #{idx:2d} {jt:8s} | {ticker:5s} | {direction[:8]:8s} | raw {raw_str} | exc {exc_str} | {target}")
        elif r["verdict"] == "skipped":
            print(f"  ⏭  ⏭   #{idx:2d} {j.get('type','?'):8s} | SKIP: {r['reason'][:50]}")
        else:
            print(f"  ?  #{idx:2d} {j.get('type','?'):8s} | {r.get('verdict')}: {r.get('reason','')[:50]}")

    # 写 JSON + 报告
    out_json = Path("/workspace/logs/p5_linqingv/verifications.json")
    json.dump(results, open(out_json, "w"), indent=2, ensure_ascii=False)
    print(f"\n📄 JSON: {out_json}")

    # 写 markdown 报告
    report = render_report(results, verified, skipped, operable, macro_only, by_type)
    out_md = Path("/workspace/outputs/p5_linqingv_verifications.md")
    out_md.write_text(report)
    print(f"📄 MD: {out_md}")


def render_report(results, verified, skipped, operable, macro_only, by_type):
    n = len(verified)
    n_hit = sum(1 for r in verified if r["hit"])
    n_op = len(operable)
    n_op_hit = sum(1 for r in operable if r["hit"])
    n_mc = len(macro_only)
    n_mc_hit = sum(1 for r in macro_only if r["hit"])

    lines = [
        "# LinQingV 22 条判断兑现验证 (P5-3)",
        "",
        f"**生成时间**: {datetime.now().isoformat()[:19]}  ",
        f"**数据截止**: 2026-06-22 (Polygon)  ",
        f"**总判断**: {len(results)} | 已验证: {n} | 跳过 (A 股等): {len(skipped)}",
        "",
        "## 0. 整体统计",
        "",
        f"| 类别 | n | hit | 兑现率 |",
        f"|---|---|---|---|",
        f"| **总已验证** | **{n}** | **{n_hit}** | **{n_hit/max(n,1)*100:.1f}%** |",
        f"| 可操作 (个股 + 板块 ETF) | {n_op} | {n_op_hit} | {n_op_hit/max(n_op,1)*100:.1f}% |",
        f"| 仅宏观 (商品/指数/方向) | {n_mc} | {n_mc_hit} | {n_mc_hit/max(n_mc,1)*100:.1f}% |",
        "",
    ]

    # 跳过/无法验证的
    if skipped:
        lines.append("### 跳过 (A 股 / 港股, Polygon 不支持)")
        lines.append("")
        for r in skipped:
            j = r["judge"]
            lines.append(f"- **#{r['idx']}** [{j['date']}] {j['type']} | {j['target'][:30]} — {r['reason']}")
        lines.append("")

    # 逐条结果
    lines.extend([
        "## 1. 逐条验证结果 (对错都列)",
        "",
        "| # | 日期 | 类型 | 标的 | 方向 | entry | exit | raw | excess | 兑现 | 可操作 |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ])
    for r in results:
        idx = r["idx"]
        j = r["judge"]
        direction = j.get("direction", "?")
        target = j.get("target", "?")[:25]
        if r["verdict"] == "verified":
            ticker = r["info"].get("ticker", "?")
            entry = r.get("entry_date", "?")
            exit_ = r.get("exit_date", "?")
            raw = r.get("raw_ret")
            exc = r.get("excess_ret")
            raw_str = f"{raw:+.1f}%" if raw is not None else "—"
            exc_str = f"{exc:+.1f}%" if exc is not None else "—"
            status = "✅ hit" if r["hit"] else "❌ miss"
            op = "🔧 可操作" if r["info"].get("operable") else "🌐 仅背景"
            lines.append(f"| {idx} | {j['date']} | {j['type']} | {ticker} | {direction} | {entry} | {exit_} | {raw_str} | {exc_str} | {status} | {op} |")
        elif r["verdict"] == "skipped":
            lines.append(f"| {idx} | {j['date']} | {j['type']} | — | {direction} | — | — | — | — | ⏭ skip | — |")
        else:
            lines.append(f"| {idx} | {j['date']} | {j['type']} | — | {direction} | — | — | — | — | ❓ {r.get('verdict')} | — |")

    # 重点: #8 QQQ 单独看
    qqq = next((r for r in results if r["idx"] == 15), None)
    if qqq and qqq.get("verdict") == "verified":
        lines.extend([
            "",
            "## 2. 重点: #15 QQQ 几年看空 (用户重点盯)",
            "",
            f"**判断**: {qqq['judge']['excerpt']}",
            f"**方向**: {qqq['judge']['direction']} | **时间窗**: 未来几年 (LLM 取 4 月窗口)  ",
            f"**标的**: {qqq['info']['ticker']} vs {qqq['info']['bench']}  ",
            f"**窗口**: {qqq['entry_date']} → {qqq['exit_date']} (entry px {qqq['entry_px']} → exit px {qqq['exit_px']})  ",
            f"**raw_ret (QQQ 实际涨跌)**: **{qqq['raw_ret']:+.1f}%**  ",
            f"**excess_ret (vs SPY)**: **{qqq['excess_ret']:+.1f}%**  ",
            f"**兑现**: {'✅ 对' if qqq['hit'] else '❌ 错'}",
            "",
            f"**结论**: QQQ 实际 raw {'涨' if qqq['raw_ret'] > 0 else '跌'} {abs(qqq['raw_ret']):.1f}%, 看空判断{'错' if not qqq['hit'] else '对'} ({'跌' if qqq['raw_ret'] < 0 else '涨'}).",
        ])

    # 分类型兑现
    lines.extend([
        "",
        "## 3. 按类型分兑现",
        "",
        "| 类型 | n | hit | 兑现率 |",
        "|---|---|---|---|",
    ])
    for t, lst in by_type.items():
        n = len(lst)
        nh = sum(1 for r in lst if r["hit"])
        if n:
            lines.append(f"| {t} | {n} | {nh} | {nh/n*100:.1f}% |")

    # 错的对的分别列
    lines.extend([
        "",
        "## 4. 对错分别列 (对称验证, 不许选择性记忆)",
        "",
        "### 4.1 ✅ 命中",
        "",
    ])
    for r in verified:
        if r["hit"]:
            j = r["judge"]
            raw = r.get("raw_ret")
            exc = r.get("excess_ret")
            raw_str = f"{raw:+.1f}%" if raw is not None else "—"
            exc_str = f"{exc:+.1f}%" if exc is not None else "—"
            lines.append(f"- **#{r['idx']}** [{j['date']}] {j['type']} | {r['info']['ticker']} | {j['target'][:30]} | raw {raw_str} / exc {exc_str} — {j['excerpt'][:60]}")

    lines.extend([
        "",
        "### 4.2 ❌ 未命中 (错的不许放过)",
        "",
    ])
    for r in verified:
        if not r["hit"]:
            j = r["judge"]
            raw = r.get("raw_ret")
            exc = r.get("excess_ret")
            raw_str = f"{raw:+.1f}%" if raw is not None else "—"
            exc_str = f"{exc:+.1f}%" if exc is not None else "—"
            lines.append(f"- **#{r['idx']}** [{j['date']}] {j['type']} | {r['info']['ticker']} | {j['target'][:30]} | raw {raw_str} / exc {exc_str} — {j['excerpt'][:60]}")

    return "\n".join(lines)


if __name__ == "__main__":
    main()