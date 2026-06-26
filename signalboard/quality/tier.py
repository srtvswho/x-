"""tier 自动分层 — Serenity 教训:论证强度 ≠ 扫货数量

判定规则 (从 Serenity 348 / 1225 / 2410 三档验证得出):
- tier_A 核心论证: 同 post_id 抽出 ≤ 3 个 prediction AND thesis_summary > 50 字符 AND raw_text > 400 字符
- tier_B 清单扫货: 同 post_id 抽出 ≥ 8 个 prediction (典型 "Strong Buy/Buy/Hold/Sell/Strong Sell" 批量评级)
- tier_C 顺带提及: 中间地带 (post 4-7 个 prediction, 或 thesis 短)

使用:
    from signalboard.quality.tier import classify_all
    tiers = classify_all(conn)  # {prediction_id: "A"|"B"|"C"}
"""
from __future__ import annotations
import sqlite3
from collections import defaultdict

TIER_A_MAX_POST_PREDS = 3
TIER_A_MIN_THESIS_LEN = 50
TIER_A_MIN_RAW_LEN = 400
TIER_B_MIN_POST_PREDS = 8


def classify_one(n_post_preds: int, thesis_len: int, raw_text_len: int) -> str:
    """单条预测打 tier。"""
    if n_post_preds >= TIER_B_MIN_POST_PREDS:
        return "B"
    if n_post_preds <= TIER_A_MAX_POST_PREDS and thesis_len > TIER_A_MIN_THESIS_LEN and raw_text_len > TIER_A_MIN_RAW_LEN:
        return "A"
    return "C"


def classify_all(conn: sqlite3.Connection) -> dict[int, str]:
    """全量 prediction 自动分档。

    Returns: {prediction_id: tier}
    """
    c = conn.cursor()
    # 拉全部 prediction 的 post_id + thesis
    rows = c.execute("""
        SELECT p.prediction_id, p.thesis_summary, p.post_id
        FROM predictions p
        WHERE p.price_source_available=1
    """).fetchall()

    # 按 post_id 分组,统计每个 post_id 的 prediction 数
    post_count = defaultdict(int)
    for pid, thesis, post_id in rows:
        post_count[post_id] += 1

    # 拉 raw_text 长度
    raw_len = {}
    for post_id in post_count:
        r = c.execute("SELECT LENGTH(raw_text) FROM raw_posts WHERE post_id=?", (post_id,)).fetchone()
        raw_len[post_id] = r[0] if r and r[0] else 0

    tiers = {}
    for pid, thesis, post_id in rows:
        thesis_len = len(thesis) if thesis else 0
        tiers[pid] = classify_one(
            n_post_preds=post_count[post_id],
            thesis_len=thesis_len,
            raw_text_len=raw_len.get(post_id, 0),
        )
    return tiers


def tier_summary(tiers: dict[int, str]) -> dict[str, int]:
    """统计 tier 分布。"""
    out = {"A": 0, "B": 0, "C": 0}
    for t in tiers.values():
        out[t] += 1
    return out


def filter_by_tier(prediction_ids: list[int], tiers: dict[int, str], tier: str) -> list[int]:
    """筛出指定 tier 的 prediction_id 列表。"""
    return [pid for pid in prediction_ids if tiers.get(pid) == tier]