"""Directional Validator — 抽取层规则 (防止 directional 误抽)

铁律 1 (P4-19 教训): directional 预测必须有明确的建仓/推荐关键词才成立
铁律 2 (P4-19 教训): 区分对象 — 判断对象必须是"股票/标的",不是产品/供应/消费品

输入: 一条 raw 内容 + LLM 抽出的 prediction dict (含 ticker / direction / thesis)
输出: 校验后的 prediction (可能修正 direction 为 neutral, 或加 commentary/fact 标签)

Jukan 案例:
- MU 6-26: 原文 "Why MU CEO didn't announce HBM sold-out" → LLM 抽 short MU 180d (❌ 错)
  Validator 应改为 neutral (产业 fact, 不是建仓声明)
- AAPL 12-26: "Apple VR 不会出" → LLM 抽 short AAPL (❌ 错)
  Validator 应改为 neutral (product 预测, 不是 stock 建仓)
- AAPL 12-13: "if you are planning to buy electronics, buy them right now" → LLM 抽 short AAPL (❌ 错)
  Validator 应改为 neutral (消费建议, 对象不是 stock)
- QCOM 5-22: "I still don't recommend Qualcomm stock. It's way overvalued." → LLM 抽 short QCOM (✅ 对)
  Validator 应保持 short (有 "不推荐 stock" 关键词, 对象是 stock)
"""
from __future__ import annotations
import re
from dataclasses import dataclass


# === 铁律 1: directional 关键词 ===

# 看多类关键词 (必须出现 ≥ 1 个才允许 long)
LONG_KEYWORDS = [
    r"\bbuy\b",
    r"\blong\b",
    r"\bbullish\b",
    r"\b看多\b",
    r"\b做多\b",
    r"\b推荐\b",  # 推荐买入
    r"\b加仓\b",
    r"\b加注\b",
    r"\b逢低买\b",
    r"\b入场\b",
    r"\b建仓\b",
    r"\bcall\b",  # buy call
    r"\bconviction\b",  # "high conviction long"
    r"\btarget price\b",
    r"\bovervalued\b",  # 自身看空时反义是 long (此处不使用)
    r"\bundervalued\b",
    r"\bI will buy\b",
    r"\bI'm buying\b",
    r"\b加注\b",
    r"\b看好\b",
    r"\b我会买\b",
]

# 看空类关键词 (必须出现 ≥ 1 个才允许 short)
SHORT_KEYWORDS = [
    r"\bsell\b",
    r"\bshort\b",
    r"\bbearish\b",
    r"\b看空\b",
    r"\b做空\b",
    r"\b不推荐\b",
    r"\b减仓\b",
    r"\b清仓\b",
    r"\bput\b",
    r"\bovervalued\b",
    r"\bI don't recommend\b",
    r"\bavoid\b",
    r"\b跑输\b",
    r"\b我会卖\b",
    r"\b我会做空\b",
    r"\b看衰\b",
]

# 强对冲 (降低 conviction, 不直接废弃)
HEDGE_KEYWORDS = [
    r"\bpossible\b",
    r"\bmight\b",
    r"\bmaybe\b",
    r"\b我猜\b",
    r"\bperhaps\b",
    r"\bpossibly\b",
    r"\b如果\b",  # 条件性预测
    r"\bif\b",
]


# === 铁律 2: 对象区分 ===

# 消费建议/产品预测 不是 stock 建仓 (应改 neutral)
NON_STOCK_OBJECT_PATTERNS = [
    r"\bbuy electronics\b",
    r"\bbuy devices\b",
    r"\bbuy products\b",
    r"\bbuy now\b",
    r"\bbuy the product\b",
    r"\bbuy the device\b",
    r"\b购买电子产品\b",
    r"\b买电子产品\b",
    r"\bVR\s*(设备|device|不会出|推出)\b",
    r"\b推出.*VR\b",
    r"\bconsumer electronics\b",
    r"\bconsumer device\b",
]

# 产业 fact 模式 (不是个人建仓)
INDUSTRY_FACT_PATTERNS = [
    r"why\s+\w+\s+(CEO|chief)\s+(did not|didn't|won't)\s+announce",
    r"为什么.*CEO.*不宣布",
    r"why\s+\w+\s+(CEO|chief)\s+(is|are)\s+(delaying|hoping)",
    r"industry insiders? (probably )?know",
    r"cross-verified",
    r"内部人士.*知道",
]


@dataclass
class ValidationResult:
    original_direction: str       # LLM 原始判定
    final_direction: str          # 校验后 (可能 = original / neutral / drop)
    action: str                   # "keep" / "downgrade_to_neutral" / "mark_commentary" / "drop"
    reason: str                   # 一句话解释
    keyword_matched: list[str]    # 命中的关键词 (用于 audit)


def has_keyword(text: str, patterns: list[str]) -> tuple[bool, list[str]]:
    """检查 text 是否含任一 pattern (regex),返回 (命中, 命中列表)。"""
    matched = []
    for p in patterns:
        if re.search(p, text, re.IGNORECASE):
            matched.append(p)
    return (len(matched) > 0, matched)


def is_non_stock_object(text: str) -> tuple[bool, list[str]]:
    """判断 text 是否指向非 stock 对象 (消费/产品)。"""
    matched = []
    for p in NON_STOCK_OBJECT_PATTERNS:
        if re.search(p, text, re.IGNORECASE):
            matched.append(p)
    return (len(matched) > 0, matched)


def is_industry_fact(text: str) -> tuple[bool, list[str]]:
    """判断 text 是否纯产业 fact (不构成投资预测)。"""
    matched = []
    for p in INDUSTRY_FACT_PATTERNS:
        if re.search(p, text, re.IGNORECASE):
            matched.append(p)
    return (len(matched) > 0, matched)


def validate_directional(text: str, ticker: str, original_direction: str) -> ValidationResult:
    """主入口: 校验 LLM 抽取的 directional。

    Args:
        text: 原文 (推文/文章)
        ticker: 标的代码 (None 表示 LLM 没识别)
        original_direction: LLM 原始判定 ("long" / "short" / "neutral")

    Returns:
        ValidationResult with final_direction + action + reason

    规则顺序 (重要):
    1. 没有 ticker → drop (不算预测)
    2. 原文指向非 stock 对象 (消费/产品) → neutral + mark_commentary
    3. 原文纯产业 fact → neutral + mark_commentary
    4. direction = long: 必须有 LONG_KEYWORDS
    5. direction = short: 必须有 SHORT_KEYWORDS
    6. 都没有 → neutral + mark_commentary
    7. 都有 (既说多又说空) → neutral (矛盾, 不取平均)
    """
    # 1. 无 ticker
    if not ticker:
        return ValidationResult(
            original_direction=original_direction,
            final_direction="neutral",
            action="drop",
            reason="无 ticker, LLM 抽不出标的, 不算预测",
            keyword_matched=[],
        )

    # 2. 非 stock 对象 (消费建议 / 产品预测)
    is_non_stock, non_stock_matches = is_non_stock_object(text)
    if is_non_stock:
        return ValidationResult(
            original_direction=original_direction,
            final_direction="neutral",
            action="mark_commentary",
            reason=f"原文指向非 stock 对象 (消费/产品), 不是 stock 建仓: {non_stock_matches[:2]}",
            keyword_matched=non_stock_matches,
        )

    # 3. 纯产业 fact
    is_fact, fact_matches = is_industry_fact(text)
    if is_fact:
        return ValidationResult(
            original_direction=original_direction,
            final_direction="neutral",
            action="mark_commentary",
            reason=f"原文纯产业 fact, 不是个人建仓声明: {fact_matches[:2]}",
            keyword_matched=fact_matches,
        )

    # 4-6. directional 关键词校验
    if original_direction == "long":
        has_kw, kw_matched = has_keyword(text, LONG_KEYWORDS)
        if not has_kw:
            # 尝试 short 关键词 — 如果有,可能是 LLM 搞反了方向
            has_short, short_matched = has_keyword(text, SHORT_KEYWORDS)
            if has_short:
                return ValidationResult(
                    original_direction=original_direction,
                    final_direction="short",
                    action="flip_direction",
                    reason=f"LLM 判 long 但有 short 关键词 {short_matched[:2]}, 翻转为 short",
                    keyword_matched=short_matched,
                )
            return ValidationResult(
                original_direction=original_direction,
                final_direction="neutral",
                action="mark_commentary",
                reason="LLM 判 long 但无 long 关键词 (I think / 我看多 / buy / 推荐), 不是建仓声明",
                keyword_matched=[],
            )
        return ValidationResult(
            original_direction=original_direction,
            final_direction="long",
            action="keep",
            reason="long 关键词校验通过",
            keyword_matched=kw_matched,
        )

    if original_direction == "short":
        has_kw, kw_matched = has_keyword(text, SHORT_KEYWORDS)
        if not has_kw:
            # 尝试 long 关键词 — 如果有,可能是 LLM 搞反了方向
            has_long, long_matched = has_keyword(text, LONG_KEYWORDS)
            if has_long:
                return ValidationResult(
                    original_direction=original_direction,
                    final_direction="long",
                    action="flip_direction",
                    reason=f"LLM 判 short 但有 long 关键词 {long_matched[:2]}, 翻转为 long",
                    keyword_matched=long_matched,
                )
            return ValidationResult(
                original_direction=original_direction,
                final_direction="neutral",
                action="mark_commentary",
                reason="LLM 判 short 但无 short 关键词 (不推荐 / 做空 / overvalued), 不是建仓声明",
                keyword_matched=[],
            )
        return ValidationResult(
            original_direction=original_direction,
            final_direction="short",
            action="keep",
            reason="short 关键词校验通过",
            keyword_matched=kw_matched,
        )

    # neutral 原样
    return ValidationResult(
        original_direction=original_direction,
        final_direction="neutral",
        action="keep",
        reason="LLM 已判 neutral",
        keyword_matched=[],
    )


# === 测试函数 ===
def _test_validate():
    """自带 unit test,跑 Jukan 那 3 条原文验证。"""
    # Case 1: MU 6-26 (产业 fact, 不应有 short)
    mu_text = (
        "The reason why Micron CEO SJ did not announce HBM sold-out for 2026 on the "
        "conference call is simple: Nvidia is delaying the contract. Nvidia is hoping "
        "that Samsung will pass HBM3E validation, allowing them to buy Micron's HBM "
        "at a lower price. That's why they're dragging out the negotiations. "
        "This information has been cross-verified multiple times. Most industry "
        "insiders probably know about it."
    )
    r = validate_directional(mu_text, "MU", "short")
    print(f"MU 6-26: {r.final_direction} ({r.action}) — {r.reason[:80]}")
    assert r.action in ("mark_commentary", "drop"), "MU 6-26 应该是 commentary/drop, 不该是 short"

    # Case 2: QCOM 5-22 (有 '不推荐' 关键词, 应保持 short)
    qcom_text = (
        "I expect Xiaomi will be able to cut Qualcomm's chip prices by about 10-15%. "
        "I still don't recommend Qualcomm stock. It's way overvalued."
    )
    r = validate_directional(qcom_text, "QCOM", "short")
    print(f"QCOM 5-22: {r.final_direction} ({r.action}) — {r.reason[:80]}")
    assert r.action == "keep" and r.final_direction == "short", "QCOM 5-22 应保持 short"

    # Case 3: AAPL 12-26 (product launch 预测, 不该 short)
    aapl_text = (
        "Sorry, but based on my investigation of the supply chain, it just doesn't "
        "seem feasible for Apple to launch a low-cost VR device by the end of 2025. "
        "Samsung Display recently placed an order for pre-mass-production research equipment."
    )
    r = validate_directional(aapl_text, "AAPL", "short")
    print(f"AAPL 12-26: {r.final_direction} ({r.action}) — {r.reason[:80]}")
    assert r.action in ("mark_commentary", "drop"), "AAPL 12-26 应该是 commentary"

    # Case 4: AAPL 12-13 (消费建议, 不该 short stock)
    aapl_consumer_text = (
        "Samsung and SK Hynix are planning to raise memory prices for Apple starting "
        "next January. If you are planning to buy electronics, buy them right now. "
        "This is the cheapest they will be. $AAPL"
    )
    r = validate_directional(aapl_consumer_text, "AAPL", "short")
    print(f"AAPL 12-13: {r.final_direction} ({r.action}) — {r.reason[:80]}")
    assert r.action in ("mark_commentary", "drop"), "AAPL 12-13 应该是 commentary (消费建议)"

    # Case 5: 真的 long (有 buy 关键词)
    long_text = "I am buying NVDA here. Strong conviction long. Target price $200."
    r = validate_directional(long_text, "NVDA", "long")
    print(f"NVDA long: {r.final_direction} ({r.action}) — {r.reason[:80]}")
    assert r.action == "keep" and r.final_direction == "long", "应保持 long"

    # Case 6: 真的 short (有 sell 关键词)
    short_text = "I am selling my QCOM position. The stock is overvalued and I'll short here."
    r = validate_directional(short_text, "QCOM", "short")
    print(f"QCOM short: {r.final_direction} ({r.action}) — {r.reason[:80]}")
    assert r.action == "keep" and r.final_direction == "short", "应保持 short"

    print("\n✅ All validation tests passed")


if __name__ == "__main__":
    _test_validate()