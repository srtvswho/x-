"""大V情报 — Dashboard Summaries 生成 (LLM 预生成 26 段)

26 段结构:
- today (1) — 今日综合
- consensus (5 窗: 0/1/3/6/12 月) — 四人共识
- person (4 人 × 5 窗 = 20) — 每人各窗总结

关键: prompt 必须带能力圈 (KOLS 强项/弱项), LLM 才知道:
- 谁的哪些方向可信 (强项)
- 谁的哪些发言要打折 (弱项/盲区, 比如 zephyr 看空/Austin 看空)

每个时间窗:
- 喂该范围内的 extractions_intel (含 R12 flag/bottleneck/direction)
- prompt 注入 KOLS 强项/弱项
- LLM 输出 ≤100 字 中文

DeepSeek 便宜, 26 段 ≈ $0.05.

输出: summaries.json (build_dashboard.py 读它)
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone, timedelta

import requests

DB_PATH = "/workspace/data/signalboard_full.db"
OUT_PATH = "/workspace/scripts/dashboard/summaries.json"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-v4-pro"

# 能力圈 (跟 build_dashboard.py 的 KOLS 一致 — 这是 LLM prompt 的"知识")
KOLS = {
    "jukan": {"name": "Jukan", "type": "signal",
              "strong": ["存储", "HBM", "代工", "卡点"],
              "weak": ["看多 AI 龙头(跑输板块)"]},
    "serenity": {"name": "Serenity", "type": "cognition",
              "strong": ["光通信", "CPO", "InP", "化合物半导体"],
              "weak": ["整体追高", "tier_B 清单=板块β"]},
    "zephyr": {"name": "zephyr", "type": "cognition",
              "strong": ["存储", "光通信", "HBM", "电力", "卡点"],
              "weak": ["看空全错(0/22)", "AI 泡沫论盲区"]},
    "austin": {"name": "Austin", "type": "cognition",
              "strong": ["商业格局", "AMD/CUDA 护城河", "Foundry 模式"],
              "weak": ["看多龙头(跑输板块)", "看空全错(1/8)"]},
}

# 时间窗 (单位: 天)
WINDOWS = {"0": 1, "1": 30, "3": 90, "6": 180, "12": 365}


def get_data_for_window(con: sqlite3.Connection, days: int) -> list[dict]:
    """拿最近 N 天的有效判断 (有 ticker / bottleneck / 非 neutral)."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    rows = con.execute("""
        SELECT e.post_id, e.source_id, e.direction, e.ticker, e.company,
               e.bottleneck, e.attribution, e.rebuts_narrative, e.summary_100,
               e.is_retrospective, e.is_disclosure, e.is_self_reported_returns,
               r.published_at, substr(r.raw_text, 1, 300) as raw_text
        FROM extractions_intel e
        JOIN raw_posts r ON r.post_id = e.post_id
        WHERE r.published_at >= ?
          AND (e.ticker IS NOT NULL OR e.bottleneck IS NOT NULL OR e.direction != 'neutral')
        ORDER BY r.published_at DESC
        LIMIT 200
    """, (cutoff,)).fetchall()
    out = []
    SRC2KOL = {  # source_id → 短名 (跟 build_dashboard.py 一致)
        "tw_jukan05": "jukan", "tw_aleabitoreddit": "serenity",
        "tw_zephyr_z9": "zephyr", "tw_austinsemis": "austin",
    }
    for x in rows:
        out.append({
            "post_id": x[0],
            "kol": SRC2KOL.get(x[1], x[1].replace("tw_", "")),
            "source_id": x[1], "published_at": x[12],
            "direction": x[2], "ticker": x[3], "company": x[4],
            "bottleneck": x[5], "attribution": x[6],
            "rebuts_narrative": x[7], "summary_100": x[8],
            "is_retro": x[9], "is_disc": x[10], "is_selfret": x[11],
            "raw_text": x[13],
        })
    return out


def build_kols_prompt() -> str:
    """能力圈 prompt 段 — LLM 必须知道每个人强项/弱项."""
    lines = ["【能力圈 (必须严格遵守)】"]
    for kol, info in KOLS.items():
        strong = ", ".join(info["strong"])
        weak = ", ".join(info["weak"])
        lines.append(f"- {info['name']} ({kol}): 强项={strong}; 弱项/盲区={weak}")
    lines.append("")
    lines.append("【关键规则】")
    lines.append("1. 有人在【强项】领域发言 → 高可信 (✅)")
    lines.append("2. 有人在【弱项/盲区】领域发言 → 标注'打折'或'仅参考' (⚠️)")
    lines.append("3. R12 flag (is_retrospective/is_disclosure) 不算'当下新表态'")
    lines.append("4. 共识 = 多人都提到同一卡点/方向")
    lines.append("5. 客观, ≤100 字, 中文")
    return "\n".join(lines)


def call_llm(system: str, user: str, max_retries: int = 2) -> str:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        # 明确报错而不是 fallback: 不可用空数据冒充今日总结
        raise SystemExit(
            "DEEPSEEK_API_KEY 未设置 — 不可生成今日总结. "
            "请设置 DEEPSEEK_API_KEY 环境变量 (或 docker run -e DEEPSEEK_API_KEY=...) "
            "或写降级 summaries.json (见 main() 中 GRACEFUL_DEGRADE 选项)."
        )
    data = json.dumps({
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
        "max_tokens": 400,
        "thinking": {"type": "disabled"},  # ★ 跨项目硬规则: 关闭思考模式
    }).encode()
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    for attempt in range(max_retries + 1):
        try:
            r = requests.post(DEEPSEEK_URL, data=data, headers=headers, timeout=30)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if attempt < max_retries:
                time.sleep(2 + attempt * 2)
                continue
            raise


def gen_today_summary(con: sqlite3.Connection) -> str:
    """今日总结 (1 段)."""
    data = get_data_for_window(con, days=1)
    if not data:
        return "今日四人无新推文或无新有效判断。"

    kols_prompt = build_kols_prompt()
    data_str = json.dumps(data[:50], ensure_ascii=False, indent=None, default=str)

    system = f"""你是大V情报分析师。从4个大V今天的推文抽取综合总结。
{kols_prompt}

【输出要求】
- ≤100 字, 中文, 客观
- 按重要性组织 (共识卡点 / 非共识方向 优先, 不按人流水账)
- 标注能力圈 (✅强项 / ⚠️打折)
- 不写 R12 过滤掉的 (victory_lap/disclosure)
"""
    user = f"今日 4 大V 有效判断数据 ({len(data)} 条):\n{data_str}\n\n输出今日综合总结 (≤100 字):"

    return call_llm(system, user)


def gen_consensus_summary(con: sqlite3.Connection, window: str, days: int) -> str:
    """共识总结 (1 段 per window)."""
    data = get_data_for_window(con, days=days)
    if not data:
        return f"近 {window} 月无有效判断数据。"

    kols_prompt = build_kols_prompt()
    data_str = json.dumps(data[:80], ensure_ascii=False, default=str)

    window_label = {"0": "今日", "1": "近 1 月", "3": "近 3 月", "6": "近 6 月", "12": "近 1 年"}.get(window, f"近 {window}")

    system = f"""你是大V情报分析师。提炼 {window_label} 4 大V 共识 (多人共同提的方向/卡点)。
{kols_prompt}

【输出要求】
- ≤100 字, 中文
- 共识 = 多人都提到的卡点/方向
- 分歧 (有人相左) 简要标出, 注意相左方是否在盲区
- 客观, 不堆细节
"""
    user = f"{window_label} 4 大V 有效判断 ({len(data)} 条):\n{data_str}\n\n输出共识总结 (≤100 字):"

    return call_llm(system, user)


def gen_person_summary(con: sqlite3.Connection, kol: str, window: str, days: int) -> str:
    """单人单窗总结 (1 段)."""
    data_all = get_data_for_window(con, days=days)
    # 过滤该 KOL
    data = [d for d in data_all if d["kol"] == kol]
    if not data:
        return f"{KOLS[kol]['name']} 在该时间窗无有效判断。"

    info = KOLS[kol]
    kols_prompt = build_kols_prompt()
    data_str = json.dumps(data[:30], ensure_ascii=False, default=str)

    window_label = {"0": "今日", "1": "近 1 月", "3": "近 3 月", "6": "近 6 月", "12": "近 1 年"}.get(window, f"近 {window}")

    system = f"""你是大V情报分析师。总结 {info['name']} ({kol}) {window_label} 的核心表态。
{kols_prompt}

【该 KOL 重点】强项: {', '.join(info['strong'])}; 弱项/盲区: {', '.join(info['weak'])}

【输出要求】
- ≤100 字, 中文, 客观
- 优先讲【强项】领域的方向性表态 (✅可信)
- 弱项领域如有发言 → 标注'打折/仅参考'
- 过滤 R12 (victory_lap/disclosure/自报收益) 不算当下表态
- 这个人没说就别说, 不要编
"""
    user = f"{info['name']} ({kol}) {window_label} 有效判断 ({len(data)} 条):\n{data_str}\n\n输出单人总结 (≤100 字):"

    return call_llm(system, user)


def get_data_until(con) -> str | None:
    """数据覆盖到什么时候 (max published_at)."""
    r = con.execute("SELECT MAX(published_at) FROM raw_posts").fetchone()
    return r[0] if r else None


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--graceful-degrade", action="store_true",
                        help="DEEPSEEK_API_KEY 缺失时, 不报错退出, 而是写一个 stale 标记的 summaries.json")
    args = parser.parse_args()

    if not os.environ.get("DEEPSEEK_API_KEY"):
        if args.graceful_degrade:
            print("⚠ DEEPSEEK_API_KEY 未设置, 但 --graceful-degrade 开启 — 写 stale 标记 summaries.json", flush=True)
            stale = {
                "generated_at": "1970-01-01T00:00:00Z",
                "data_until": None,
                "stale": True,
                "stale_reason": "DEEPSEEK_API_KEY 未设置",
                "today": "（今日总结缺失 — DEEPSEEK_API_KEY 未配置, 请联系管理员）",
                "consensus": {w: "（缺失 — DEEPSEEK_API_KEY 未配置）" for w in WINDOWS},
                "person": {k: {w: "（缺失 — DEEPSEEK_API_KEY 未配置）" for w in WINDOWS} for k in KOLS},
            }
            with open(OUT_PATH, "w", encoding="utf-8") as f:
                json.dump(stale, f, indent=2, ensure_ascii=False)
            print(f"  ✓ stale summaries.json 写好: {OUT_PATH}")
            return
        print("✗ DEEPSEEK_API_KEY 未设置 — 不可生成今日总结", flush=True)
        print("  (如要明确降级, 加 --graceful-degrade)", flush=True)
        sys.exit(2)

    print("===== Dashboard Summaries 生成 (LLM 预生成 26 段) =====\n")
    con = sqlite3.connect(DB_PATH, timeout=60)

    data_until = get_data_until(con)
    print(f"  data_until: {data_until}")

    summaries = {
        "today": "",
        "consensus": {},
        "person": {},
        # metadata (供 build_dashboard.py / 前端判断是否过期)
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "data_until": data_until,
        "stale": False,
    }
    # 初始化 person
    for kol in KOLS:
        summaries["person"][kol] = {}

    # === 1. today ===
    print("[1/26] 今日综合...")
    summaries["today"] = gen_today_summary(con)
    print(f"  ✓ {summaries['today'][:80]}...")

    # === 2. consensus × 5 ===
    for i, (win, days) in enumerate(WINDOWS.items(), 2):
        print(f"[{i}/26] 共识 {win}M ({days}d)...")
        summaries["consensus"][win] = gen_consensus_summary(con, win, days)
        print(f"  ✓ {summaries['consensus'][win][:80]}...")

    # === 3. person × 4 × 5 ===
    idx = 7
    for kol in KOLS:
        for win, days in WINDOWS.items():
            print(f"[{idx}/26] {KOLS[kol]['name']} {win}M...")
            summaries["person"][kol][win] = gen_person_summary(con, kol, win, days)
            print(f"  ✓ {summaries['person'][kol][win][:80]}...")
            idx += 1

    con.close()

    # === 写文件 ===
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2, ensure_ascii=False)

    print(f"\n✅ summaries.json 写好: {OUT_PATH}")
    print(f"   1 today + 5 consensus + {len(KOLS)*len(WINDOWS)} person = {1 + len(WINDOWS) + len(KOLS)*len(WINDOWS)} 段")
    print(f"   generated_at: {summaries['generated_at']}")
    print(f"   data_until:   {summaries['data_until']}")


if __name__ == "__main__":
    main()