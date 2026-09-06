"""大V情报 — Dashboard Summaries 生成（按当前生产人物动态生成）

26 段结构:
- today (1) — 今日综合
- consensus (5 窗: 0/1/3/6/12 月) — 加权共识
- person (当前人物 × 5 窗) — 每人各窗总结

关键: prompt 必须带能力圈 (KOLS 强项/弱项), LLM 才知道:
- 谁的哪些方向可信 (强项)
- 谁的哪些发言要打折 (弱项/盲区, 比如 zephyr 看空/Austin 看空)

每个时间窗:
- 喂该范围内的 extractions_intel (含 R12 flag/bottleneck/direction)
- prompt 注入 KOLS 强项/弱项
- LLM 输出 ≤100 字 中文

段数随生产人物数量动态变化。

输出: summaries.json (build_dashboard.py 读它)
"""
from __future__ import annotations

import json
import hashlib
import tempfile
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone, timedelta
import sys
from pathlib import Path

# 共享窗口函数 — 跟 build_dashboard.py / dashboard.template.html / query_today_stats 共用同一窗口
# today/0M 用 24h 滚动 (不是北京自然日, 因为生产顺序 06:00 抓取 → 06:20 Dashboard,
# 北京自然日只覆盖 6h, 跟用户视角 "今日" 不符; 24h 滚动跟 cron 节奏对齐)
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from signalboard.ai.router import call_text, record_usage, resolve_route  # noqa: E402
from common import (  # noqa: E402
    CN_TZ, KOLS, SRC2KOL, cn_recent_24h_window_utc, cn_window_long_utc,
    is_author_signal, normalize_ticker, parse_json_arr,
)

DB_PATH = os.getenv("SIGNALBOARD_DB_PATH", "/workspace/data/signalboard_full.db")
OUT_PATH = os.getenv("SUMMARY_OUT_PATH", "/workspace/scripts/dashboard/summaries.json")
DEEPSEEK_MODEL = resolve_route("daily_summary").model

# 时间窗 (单位: 天) — "0" 跟 "1" 实际都是 1 (北京今日),
# 但 "1M/3M/6M/12M" 是相对滑动窗口 (今天往前推 N 天)
WINDOWS = {"0": 1, "1": 30, "3": 90, "6": 180, "12": 365}
AS_OF = None
ARCHIVE_DATE = None
STATE = None


def window_bounds(days):
    now = AS_OF or datetime.now(timezone.utc)
    if ARCHIVE_DATE:
        start = datetime.fromisoformat(ARCHIVE_DATE).replace(tzinfo=CN_TZ)
        end = min(start + timedelta(days=1), now)
    else:
        end = now
        start = end - timedelta(days=days)
    return start.astimezone(timezone.utc).isoformat(), end.astimezone(timezone.utc).isoformat()


def atomic_save(data):
    path = Path(OUT_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_document():
    try:
        data = json.loads(Path(OUT_PATH).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}



def get_data_for_window(con: sqlite3.Connection, days: int) -> list[dict]:
    """拿最近 N 天的有效判断 (有 ticker / bottleneck / 非 neutral).

    days=1 → 24h 滚动窗口 [now-24h, now) (跟 dashboard 1D / consensus[0] / person[*][0] 共用)
    days>1 → 近 N 天滑动窗口: [now-N days, now)

    为什么 24h 滚动不是北京自然日:
    - 生产顺序 06:00 抓取 → 06:20 Dashboard
    - 北京自然日 [00:00, 06:20) 只覆盖 6h, 不是 "今日总结"
    - 24h 滚动 [昨日 06:20, 今日 06:20) 跟 cron 节奏对齐, 跟 "上次抓取" 边界对齐
    """
    start_iso, end_iso = window_bounds(days)
    rows = con.execute("""
        SELECT e.post_id, e.source_id, e.direction, e.ticker, e.company,
               e.bottleneck, e.attribution, e.rebuts_narrative, e.summary_100,
               e.is_retrospective, e.is_disclosure, e.is_self_reported_returns,
               r.published_at, substr(r.raw_text, 1, 300) as raw_text
        FROM extractions_intel e
        JOIN raw_posts r ON r.post_id = e.post_id
        WHERE julianday(r.published_at) >= julianday(?) AND julianday(r.published_at) < julianday(?)
          AND (e.ticker IS NOT NULL OR e.bottleneck IS NOT NULL OR e.direction != 'neutral')
        ORDER BY r.published_at DESC
    """, (start_iso, end_iso)).fetchall()
    out = []
    for x in rows:
        # 纯转述保留在明细信息流，但不进入人物立场、共识或能力评价。
        if not is_author_signal(x[6]):
            continue
        context = f"{x[4] or ''} {x[13] or ''}"
        tickers = [normalize_ticker(t, context) for t in parse_json_arr(x[3])]
        out.append({
            "post_id": x[0],
            "kol": SRC2KOL.get(x[1], x[1].replace("tw_", "")),
            "source_id": x[1], "published_at": x[12],
            "direction": x[2], "ticker": tickers, "company": x[4],
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
        lines.append(
            f"- {info['name']} ({kol}): 评级={info['rating']}({info['ratingStatus']}); "
            f"方向权重={info['consensusWeight']}; 认知权重={info['researchWeight']}; "
            f"强项={strong}; 弱项/盲区={weak}"
        )
    lines.append("")
    lines.append("【关键规则】")
    lines.append("1. 有人在【强项】领域发言 → 高可信 (✅)")
    lines.append("2. 有人在【弱项/盲区】领域发言 → 标注'打折'或'仅参考' (⚠️)")
    lines.append("3. R12 flag (is_retrospective/is_disclosure) 不算'当下新表态'")
    lines.append("4. RELAYED/RC 是外部观点，不归属转发者，不进入方向或共识")
    lines.append("5. 共识 = 多人都提到同一卡点/方向")
    lines.append("6. 客观、结论先行；禁止写成散文或按人物流水账")
    return "\n".join(lines)


def balanced_consensus_sample(data: list[dict], per_kol: int = 12) -> list[dict]:
    """按人物限额抽样，避免高频账号淹没低频账号的共识证据。"""
    counts: dict[str, int] = {}
    out = []
    for row in data:
        kol = row["kol"]
        if kol not in KOLS or counts.get(kol, 0) >= per_kol:
            continue
        counts[kol] = counts.get(kol, 0) + 1
        out.append(row)
    return out


def call_llm(system: str, user: str, max_retries: int = 2) -> str:
    # Include the actual evidence period in the request. Historical summaries
    # must never interpret subsequent posts as evidence available on that day.
    period = ARCHIVE_DATE or (AS_OF or datetime.now(timezone.utc)).astimezone(CN_TZ).date().isoformat()
    user = f"研究日期（北京时间）：{period}。仅解读提供的窗口内证据，不使用此后信息。\n" + user
    route = resolve_route("daily_summary")
    key = hashlib.sha256(json.dumps(
        [route.provider, route.model, system, user, 400], ensure_ascii=False
    ).encode()).hexdigest()
    document = STATE if STATE is not None else load_document()
    cache = document.setdefault("request_cache", {})
    if cache.get(key, {}).get("text"):
        print("  ↪ reuse successful summary", flush=True)
        return cache[key]["text"]
    result = call_text(
        "daily_summary", system, user,
        max_output_tokens=400, timeout=30, max_retries=max_retries,
    )
    if not result.text.strip():
        raise ValueError("EMPTY_SUMMARY")
    cache[key] = {"text": result.text, "generated_at": datetime.now(timezone.utc).isoformat()}
    # Save successful output immediately, even if a later segment fails.
    atomic_save(document)
    usage_con = sqlite3.connect(DB_PATH, timeout=30)
    try:
        record_usage(usage_con, result, workload="daily_summary", object_type="dashboard", object_id=key)
        usage_con.commit()
    finally:
        usage_con.close()
    return result.text


def generate_segment(target, key, generator, errors, label):
    previous = target.get(key)
    try:
        target[key] = generator()
    except Exception as exc:
        # A guardrail remains enforced: no forced duplicate call or budget bypass.
        reason = getattr(exc, "reason", type(exc).__name__)
        errors[label] = reason
        target[key] = previous or "（摘要待补；请查看该日期的原始 Post 和逐条解读）"
        print(f"::warning::Summary {label} pending: {reason}", flush=True)
    if STATE is not None:
        atomic_save(STATE)


def gen_today_summary(con: sqlite3.Connection) -> str:
    """今日总结 (1 段)."""
    data = get_data_for_window(con, days=1)
    if not data:
        return "今日生产跟踪账号无新推文或无新有效判断。"

    kols_prompt = build_kols_prompt()
    sampled = balanced_consensus_sample(data, per_kol=8)
    data_str = json.dumps(sampled, ensure_ascii=False, indent=None, default=str)

    system = f"""你是大V情报分析师。从当前生产跟踪账号今天的推文抽取综合总结。
{kols_prompt}

【输出要求】严格输出以下4行，每行只写一个结论；没有则写“无”。总计≤180字：
市场主线｜行业/主题 + 一句话结论
模块/标的｜模块；标的（若原文没有明确标的则写“无明确标的”）
方向/共识｜看多/看空/中性 + 谁形成共识
风险/分歧｜最重要的反方、盲区或待验证点
标注能力圈 (✅强项 / ⚠️打折)，不写 R12 过滤项。
"""
    user = f"今日 {len(KOLS)} 个跟踪账号有效判断数据 ({len(data)} 条；已按人物均衡抽样 {len(sampled)} 条):\n{data_str}\n\n输出今日综合总结 (≤100 字):"

    return call_llm(system, user)


def gen_consensus_summary(con: sqlite3.Connection, window: str, days: int) -> str:
    """共识总结 (1 段 per window)."""
    data = get_data_for_window(con, days=days)
    if not data:
        return f"近 {window} 月无有效判断数据。"

    kols_prompt = build_kols_prompt()
    sampled = balanced_consensus_sample(data)
    data_str = json.dumps(sampled, ensure_ascii=False, default=str)

    window_label = {"0": "今日", "1": "近 1 月", "3": "近 3 月", "6": "近 6 月", "12": "近 1 年"}.get(window, f"近 {window}")

    system = f"""你是大V情报分析师。提炼 {window_label} 加权共识 (多人共同提的方向/卡点)。
{kols_prompt}

【输出要求】严格输出以下3行，总计≤160字：
共识方向｜模块/主题 + 看多/看空/中性 + 参与者
核心标的｜按方向列出明确 ticker；没有则写“无明确标的”
分歧/风险｜相左观点、盲区或待验证点；没有则写“暂无明显分歧”
- 共识必须至少2人同向，且方向权重合计≥0.80
- Zephyr看空权重为0；Austin主要是认知验证，不得与Jukan等权计票
"""
    user = f"{window_label} {len(KOLS)} 个跟踪账号有效判断 ({len(data)} 条；已按人物均衡抽样 {len(sampled)} 条):\n{data_str}\n\n输出共识总结 (≤100 字):"

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

【输出要求】严格输出以下3行，总计≤140字：
核心方向｜模块 + 看多/看空/中性
明确标的｜ticker + 方向；没有则写“无明确标的”
依据/风险｜最核心依据 + 能力圈可信度
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


def load_daily_history() -> dict:
    """保留此前每天生成的总结；旧格式 summaries.json 自动兼容。"""
    try:
        with open(OUT_PATH, "r", encoding="utf-8") as f:
            old = json.load(f)
        return old.get("daily_history", {}) if isinstance(old, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def main():
    import argparse
    global STATE, AS_OF, ARCHIVE_DATE
    parser = argparse.ArgumentParser()
    parser.add_argument("--graceful-degrade", action="store_true")
    parser.add_argument("--backfill-days", type=int, default=2,
                        help="Refresh daily archives for the last N Beijing dates (including today; max 7)")
    args = parser.parse_args()
    if not 0 <= args.backfill_days <= 7:
        parser.error("--backfill-days must be between 0 and 7")
    AS_OF = datetime.now(timezone.utc)
    STATE = summaries = load_document()
    summaries.setdefault("daily_history", load_daily_history())
    summaries.setdefault("consensus", {})
    summaries.setdefault("person", {})
    summaries["stale"] = True
    summaries["stale_reason"] = "摘要更新中；未完成部分保留此前内容"
    errors = {}
    summaries["segment_errors"] = errors
    con = sqlite3.connect(DB_PATH, timeout=60)
    try:
        data_until = get_data_until(con)
        print(f"Summary input data_until: {data_until}", flush=True)
        summaries["source_data_until"] = data_until
        generate_segment(summaries, "today", lambda: gen_today_summary(con), errors, "today")
        # Prioritize the current daily view before optional long-window segments.
        ordered_windows = list(WINDOWS.items())
        for win, days in ordered_windows:
            generate_segment(summaries["consensus"], win,
                             lambda w=win, d=days: gen_consensus_summary(con, w, d), errors, f"consensus/{win}")
            for kol in KOLS:
                target = summaries["person"].setdefault(kol, {})
                generate_segment(target, win,
                                 lambda k=kol, w=win, d=days: gen_person_summary(con, k, w, d), errors, f"person/{kol}/{win}")
        current_errors = dict(errors)
        if not current_errors:
            summaries.update(generated_at=AS_OF.isoformat(), data_until=data_until, stale=False)
            summaries.pop("stale_reason", None)
        else:
            summaries["stale_reason"] = "部分摘要待补；旧内容保留，原始 Post 正常更新"
        for offset in range(args.backfill_days - 1, -1, -1):
            archive_date = (AS_OF.astimezone(CN_TZ).date() - timedelta(days=offset)).isoformat()
            ARCHIVE_DATE = archive_date
            start, end = window_bounds(1)
            rows = con.execute("SELECT post_id,published_at,raw_text FROM raw_posts WHERE julianday(published_at)>=julianday(?) AND julianday(published_at)<julianday(?) ORDER BY post_id", (start, end)).fetchall()
            judgments = get_data_for_window(con, 1)
            source_hash = hashlib.sha256(json.dumps([rows, judgments, build_kols_prompt(), resolve_route("daily_summary").model], ensure_ascii=False, default=str).encode()).hexdigest()
            existing = summaries["daily_history"].get(archive_date, {})
            if existing.get("source_hash") == source_hash and existing.get("complete"):
                continue
            entry = summaries["daily_history"][archive_date] = dict(existing)
            entry.update(window_start_utc=start, window_end_utc=end, window_kind="beijing_calendar_day",
                         source_data_until=max((row[1] for row in rows), default=None), post_count=len(rows),
                         complete=False)
            entry.setdefault("person", {})
            day_errors = {}
            entry["segment_errors"] = day_errors
            generate_segment(entry, "summary", lambda: gen_today_summary(con), day_errors, "summary")
            generate_segment(entry, "consensus", lambda: gen_consensus_summary(con, "0", 1), day_errors, "consensus")
            for kol in KOLS:
                generate_segment(entry["person"], kol, lambda k=kol: gen_person_summary(con, k, "0", 1), day_errors, kol)
            if not day_errors:
                entry.update(complete=True, source_hash=source_hash, generated_at=AS_OF.isoformat(),
                             data_until=entry["source_data_until"])
            errors.update({f"daily/{archive_date}/{k}": v for k, v in day_errors.items()})
            atomic_save(summaries)
        ARCHIVE_DATE = None
        summaries["last_attempt_at"] = AS_OF.isoformat()
        summaries["refresh_complete"] = not errors
        atomic_save(summaries)
        print(f"Summary refresh: complete={not errors}, pending={len(errors)}, data_until={data_until}", flush=True)
    finally:
        con.close()
        ARCHIVE_DATE = None
        STATE = None


if __name__ == "__main__":
    main()
