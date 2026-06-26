"""direction + 条件抽取规则升级 — Serenity 教训:

- 风险提示/谨慎/中性 ≠ 做空持仓 (A/B/C 分类)
- 条件句 "if X then Y" 必须标记
- 修辞句 (after/when/before/once) 大多是时间/语气修饰,不算条件
- 举证责任在"豁免" — 存疑保留,只有明确真条件 + 条件没发生才豁免

Serenity 实战分类规则:
- A 类: 真·反向持仓 (有持仓方向,赔率定价或仓位逻辑)
- B 类: 风险提示/谨慎/中性 (不改方向,verifications 标 skipped_risk_note)
- C 类: 明确误判 (LLM 抽错,人工改方向 + 重算)

导出:
- DIRECTION_CLASSIFY_RULES: 给 prompt 用的规则文本
- CONDITIONAL_DETECTION_RULES: 条件检测规则
- direction_classify_post(): 后处理 — 把 LLM 输出按 A/B/C 分类
- detect_conditional(): 检测条件句
"""
from __future__ import annotations
import re
from dataclasses import dataclass

# ==================== Prompt 升级规则文本 ====================

DIRECTION_CLASSIFY_RULES = """\
[方向判定铁律 — A/B/C 三类]

A 类 — 真·反向持仓:
  - 有明确持仓方向 (long/short) + 仓位逻辑 (赔率定价/分批建仓/止损)
  - 例: "I'm short IREN at $50 with stop at $60,target $30"  →  A short
  - 例: "Adding to my position at $X,target $Y"  →  A long

B 类 — 风险提示/谨慎/中性 (改 neutral):
  - "rating list / Strong Sell / Sell / Hold / Watchlist" 不构成持仓方向
  - "I'm cautious on X" / "avoid X for now" / "trim X" 不构成反向持仓
  - 例: "I have a Strong Sell on $XYZ"  →  B neutral
  - 例: "Adding RGTI to my Strong Sell list"  →  B neutral (B 类从 short 改 neutral)

C 类 — 明确误判 (改方向 + 重算):
  - LLM 抽错 (语境是看多被抽成 short,或反之)
  - 例: "AVGO is a buying opportunity here" 被抽成 short  →  C long
  - 例: "$X is a dip buying opportunity" 被抽成 short  →  C long (这是反向指标)

判定流程:
1) 看原文是否有明确持仓/加减仓动作 (buy/sell/add/trim/cover/short)
2) 有 → A 类,保留 LLM 抽的方向
3) 无 (仅评级/风险提示) → B 类,改 neutral
4) 看方向是否跟原文语境相反 → C 类,改相反方向

举证责任: 如果你不确定是哪类,**默认保留 LLM 抽取结果**(走 A 类),不要主动豁免。
"""

CONDITIONAL_DETECTION_RULES = """\
[条件性预测判定铁律]

真条件 — 必须满足:
  - "if X then Y" / "when X happens, Y" 形式
  - X 是**客观可判定**的事件: 具体价位/财报/数据/政策/产品发布/合同签署
  - Y 是预测结果 (会涨/会跌/会到 $X)

  ✓ 真条件例:
    - "if SIVE breaks $1.20,target $1.80"
    - "if MSFT announces $X contract,NBIS goes to $200"
    - "if ETH drops below $2200,buy"
    - "if Fed cuts 50bps in Sept,SPY to 580"

  ✗ 伪条件 (修辞/时间/语气,不算条件):
    - "after X happens" (大多时间顺序修饰)
    - "when X is the case" (假设语气)
    - "before X" (时间修饰)
    - "once X is set" (常用修辞)

判定流程:
1) 找 if/when/once/after/before + 主句
2) 真条件 → 标记 conditional=true + condition_trigger (X)
3) 伪条件 → 标记 conditional=false
4) 条件未触发 + 条件客观可判定 → 豁免 (D condition_not_triggered,移出分母)
5) 条件未触发 + 不可客观判定 (评级列表/弱条件) → 豁免但单独统计 (U unverifiable)
6) 条件已触发 → 正常验证

铁律: 判定"if 条件是否触发"必须**独立于盈亏结果**。亏的/赚的用同样规则。
"""

# ==================== 后处理逻辑 ====================

# B 类关键词 (评级/谨慎/中性)
RISK_NOTE_KEYWORDS = [
    r"\bStrong Sell\b", r"\bSell\b", r"\bHold\b", r"\bWatchlist\b",
    r"\bStrong Buy\b", r"\bcautious\b", r"\btrim\b", r"\bavoid\b",
    r"\brating\b", r"\bI'?m cautious\b", r"\bI have a\b",
    r"\badding to (my )?(Strong Sell|Sell)\b",
]

# C 类误判标志 (反向指标)
DIP_BUY_PATTERN = re.compile(r"\b(?:dip buying|buying opportunity|buy the dip)\b", re.IGNORECASE)
PRICE_OPPORTUNITY_PATTERN = re.compile(r"\b(?:buying opportunity|bullish setup)\b", re.IGNORECASE)


@dataclass
class DirectionClassification:
    """LLM 抽取后的方向复核结果。"""
    original_direction: str
    classified_class: str  # "A" / "B" / "C"
    final_direction: str   # "long" / "short" / "neutral"
    review_note: str


def direction_classify_post(llm_direction: str, raw_text: str, ticker: str) -> DirectionClassification:
    """后处理: 把 LLM 抽出的 direction 按 A/B/C 规则复核。

    Args:
        llm_direction: LLM 抽出的方向 ("long" / "short" / "neutral")
        raw_text: 原文
        ticker: 标的

    Returns:
        DirectionClassification with final_direction 已修正
    """
    if not raw_text:
        return DirectionClassification(llm_direction, "A", llm_direction, "")

    # C 类检测: 原文是 bullish setup 但 LLM 抽 short
    if llm_direction == "short":
        if DIP_BUY_PATTERN.search(raw_text):
            return DirectionClassification(
                original_direction="short",
                classified_class="C",
                final_direction="long",
                review_note=f"C 类反向指标:原文含 'dip buying/buying opportunity',LLM 误抽 short → 改 long",
            )
        if PRICE_OPPORTUNITY_PATTERN.search(raw_text):
            return DirectionClassification(
                original_direction="short",
                classified_class="C",
                final_direction="long",
                review_note=f"C 类反向指标:原文含 'buying opportunity/bullish setup'",
            )

    # B 类检测: 评级列表 / 风险提示
    if llm_direction in ("short", "long"):
        for kw_pattern in RISK_NOTE_KEYWORDS:
            if re.search(kw_pattern, raw_text, re.IGNORECASE):
                # 仅 short → neutral (long 也可以是 B,但不常见)
                if llm_direction == "short" and "Strong Sell" in raw_text:
                    return DirectionClassification(
                        original_direction="short",
                        classified_class="B",
                        final_direction="neutral",
                        review_note=f"B 类风险提示:原文是 'Strong Sell' 评级列表,非持仓方向 → 改 neutral",
                    )
                if llm_direction == "short" and re.search(r"\b(?:cautious|avoid|trim|risk)\b", raw_text, re.IGNORECASE):
                    return DirectionClassification(
                        original_direction="short",
                        classified_class="B",
                        final_direction="neutral",
                        review_note=f"B 类风险提示:原文是 cautious/avoid/trim,非持仓方向 → 改 neutral",
                    )

    # 默认 A 类
    return DirectionClassification(llm_direction, "A", llm_direction, "")


# ==================== 条件性检测 ====================

# 真条件触发词 (必须有客观可判定的 X)
# trigger 可以含 . $ 数字, 终止于 , ; then will would target goes to
# 使用 .{5,120}? 因为 \S+ 不能跨词匹配空格
TRUE_CONDITIONAL_PATTERN = re.compile(
    r"\bif\s+(?:the\s+)?(?P<trigger>.{5,120}?)(?:\s*,\s*|\s+then\s+|\s+will\s+|\s+would\s+|\s+(?:to|target)\s+)",
    re.IGNORECASE,
)

# 触发词中需含价格/数字/事件关键词才算客观可判定
OBJECTIVE_TRIGGER_HINTS = [
    r"\$\d+",            # 价格 $X
    r"\d+\.\d+",         # 数字 1.20
    r"\d+%",             # 百分比 50%
    r"\b(Fed|FOMC|SEC|EPS|earnings|guidance|merger|acquisition|IPO|contract|announce|launch|approval|break|drop|above|below|crosses?)\b",
]


def detect_conditional(raw_text: str) -> dict:
    """检测条件性预测。

    Returns:
        {
            "conditional": bool,
            "triggers": list[str],          # 客观可判定的条件
            "is_rhetorical": bool,          # 是否是修辞/时间/语气修饰
        }
    """
    if not raw_text:
        return {"conditional": False, "triggers": [], "is_rhetorical": False}

    matches = TRUE_CONDITIONAL_PATTERN.findall(raw_text)
    if matches:
        # 有 if + 终止词 → 检查是否客观可判定
        objective_triggers = []
        for m in matches:
            for hint in OBJECTIVE_TRIGGER_HINTS:
                if re.search(hint, m, re.IGNORECASE):
                    objective_triggers.append(m.strip())
                    break
        if objective_triggers:
            return {
                "conditional": True,
                "triggers": objective_triggers,
                "is_rhetorical": False,
            }
        else:
            return {
                "conditional": False,
                "triggers": [],
                "is_rhetorical": True,
            }

    # 没匹配 if + 终止词,但有 after/when/before/once → 修辞
    RHETORICAL_PATTERN = re.compile(r"\b(?:after|when|before|once)\s+\S+", re.IGNORECASE)
    if RHETORICAL_PATTERN.search(raw_text):
        return {"conditional": False, "triggers": [], "is_rhetorical": True}

    return {"conditional": False, "triggers": [], "is_rhetorical": False}