"""Attribution Classifier — 抽取层规则 3

铁律 3 (P4-12/P4-14 Jukan 教训): 区分判断归属
- ORIGINAL: 作者自己的判断
- RELAYED: 转述/搬运机构观点
- RELAYED+COMMENT: 搬运了别人观点, 但加了自己的明确判断

只有 ORIGINAL + RELAYED+COMMENT 里他自己的那部分, 计入他的能力分;
纯 RELAYED (搬运工模式) 单独统计, 不算他的能力 — 搬运的对错是研报的对错, 不是他的。

Jukan 数据:
- 705 条内容中 70% 是 ORIGINAL/RELAYED+COMMENT (481+13 = 494), 29% 是 RELAYED (207)
- 他发出的预测 144 条里 66 (45.8%) 是他自己判断, 78 (54.2%) 是纯搬运
- 他的 α 来自 ORIGINAL 部分, 搬运部分单独对照 (P4-14 验证)
"""
from __future__ import annotations
import json
import urllib.request
import os
from dataclasses import dataclass
from collections import Counter


DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-v4-pro"


# Attribution keywords (pre-LLM 启发式判断, 节省 API)
RELAYED_MARKERS = [
    # 机构/媒体引用
    "Goldman Sachs", "Morgan Stanley", "JP Morgan", "JPM", "Citi", "Citigroup",
    "Wells Fargo", "Bank of America", "Deutsche Bank", "Barclays", "UBS",
    "Bernstein", "Wedbush", "Piper Sandler", "Evercore", "Jefferies",
    "Susquehanna", "Raymond James", "Citi Research", "Morgan Stanley Research",
    "TrendForce", "Counterpoint", "IDC", "Gartner", "Canalys",
    "Nikkei", "Reuters", "Bloomberg", "WSJ", "Financial Times",
    "GF Securities", "Goldman", "Goldman says", "Goldman raised",
    "研报", "研报指出", "券商", "分析师认为", "分析师指出",
    "据彭博", "据路透", "据 TrendForce", "据 Counterpoint",
    # 形式标记
    "[Exclusive]", "据", "报告显示",
]

# ORIGINAL markers
ORIGINAL_MARKERS = [
    "I think", "in my view", "my view", "my take", "in my opinion",
    "my opinion", "I believe", "I expect", "I estimate",
    "我认为", "我看", "我的判断", "我的看法", "我判断", "我认为",
    "I'll buy", "I'll sell", "I am buying", "I am selling",
    "I'm buying", "I'm selling", "I'm long", "I'm short",
    "我买", "我卖", "我会买", "我会卖",
    "I still don't recommend", "I recommend", "I don't recommend",
    "不推荐", "推荐", "I think", "我看好", "我看衰",
]

RELAYED_PLUS_COMMENT_MARKERS = [
    "However, I", "But I think", "I disagree", "I see it differently",
    "My view is different", "但是我认为", "不过我认为", "我不同意",
    "I would add", "I'd add", "That said, I", "I however",
]


@dataclass
class AttributionResult:
    attribution: str              # "ORIGINAL" / "RELAYED" / "RELAYED+COMMENT" / "?"
    evidence: str                 # 一句话解释 (引用原文片段)
    method: str                   # "heuristic" / "llm"
    confidence: float             # 0-1, LLM 给出


# === 启发式 attribution (无 LLM, 节省 API) ===
def heuristic_attribution(text: str) -> AttributionResult:
    """基于关键词的 attribution (规则简单, 100% 覆盖率)。

    优先级:
    1. RELAYED+COMMENT 关键词出现 → "RELAYED+COMMENT"
    2. 只有 RELAYED 关键词 → "RELAYED"
    3. ORIGINAL 关键词出现 → "ORIGINAL"
    4. 都没有 → "?" (需 LLM)
    """
    has_relayed_marker = any(m in text for m in RELAYED_MARKERS)
    has_original_marker = any(m in text for m in ORIGINAL_MARKERS)
    has_rc_marker = any(m in text for m in RELAYED_PLUS_COMMENT_MARKERS)

    if has_relayed_marker and has_original_marker and has_rc_marker:
        return AttributionResult(
            attribution="RELAYED+COMMENT",
            evidence=f"含机构引用 + 个人反对/加评论 marker",
            method="heuristic",
            confidence=0.85,
        )
    if has_relayed_marker and not has_original_marker:
        return AttributionResult(
            attribution="RELAYED",
            evidence=f"含机构引用, 无 ORIGINAL marker",
            method="heuristic",
            confidence=0.90,
        )
    if has_original_marker and not has_relayed_marker:
        return AttributionResult(
            attribution="ORIGINAL",
            evidence=f"含 ORIGINAL marker, 无机构引用",
            method="heuristic",
            confidence=0.85,
        )
    # 没有 marker → LLM 判定
    return AttributionResult(
        attribution="?",
        evidence="启发式无法判定 (无明显 marker)",
        method="heuristic",
        confidence=0.0,
    )


# === LLM attribution (fallback) ===
ATTRIBUTION_PROMPT = """你是内容归属判定器。给定一条内容 (X 推文/Substack), 判定判断归属。

【内容】{text}

【判定规则】

3 选 1:
- **ORIGINAL**: 作者自己的判断, 直接陈述观点, 没引用机构 (e.g. "I think / in my view / 我认为")
- **RELAYED**: 转述/搬运机构观点, 只引用没加立场 (e.g. "Morgan Stanley says / GF Securities 研报 / 据 Bloomberg")
- **RELAYED+COMMENT**: 搬运了别人观点, 但加了自己的明确判断 (e.g. 转述研报后说 "However, I see it differently" / "不过我认为")

【输出 JSON】
{{
  "attribution": "ORIGINAL" | "RELAYED" | "RELAYED+COMMENT",
  "evidence": "一句话解释 (引用原文片段)"
}}
"""


def llm_attribution(text: str, max_retries: int = 2) -> AttributionResult:
    """LLM 判定 attribution。"""
    prompt = ATTRIBUTION_PROMPT.format(text=text[:2000])
    data = json.dumps({
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
        "max_tokens": 400,
    }).encode()
    req = urllib.request.Request(
        DEEPSEEK_URL,
        data=data,
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
    )
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                resp = json.loads(r.read())
            content = json.loads(resp["choices"][0]["message"]["content"])
            return AttributionResult(
                attribution=content.get("attribution", "?"),
                evidence=content.get("evidence", ""),
                method="llm",
                confidence=0.85,
            )
        except Exception as e:
            if attempt == max_retries - 1:
                return AttributionResult(
                    attribution="?",
                    evidence=f"LLM failed: {str(e)[:100]}",
                    method="llm",
                    confidence=0.0,
                )


def classify_attribution(text: str, force_llm: bool = False) -> AttributionResult:
    """主入口: 先启发式, '?' 时走 LLM。"""
    if force_llm:
        return llm_attribution(text)
    h = heuristic_attribution(text)
    if h.attribution == "?":
        return llm_attribution(text)
    return h


# === 测试 ===
def _test_attribution():
    """6 个 case: 5 个启发式 + 1 个 fallback to LLM (无 marker)。"""
    cases = [
        # 启发式路径
        ("I think NVDA is going to $200. My view is bullish.", "ORIGINAL"),
        ("Morgan Stanley raised NVDA target to $200.", "RELAYED"),
        ("Morgan Stanley says NVDA at $200. However, I think it's overvalued.", "RELAYED+COMMENT"),
        ("我认为 NVDA 应该买。 这是我的判断。", "ORIGINAL"),
        ("据彭博报道, 高盛上调 NVDA 目标价至 $200。", "RELAYED"),
        # 无 marker → LLM fallback (实际 attribution 取决于 LLM)
        ("Today is a good day for markets.", "?"),  # 期望 ? 或 LLM 任意, 不检查
    ]
    print("\n=== Attribution unit tests ===")
    for text, expected in cases:
        r = classify_attribution(text, force_llm=False)
        # 启发式路径: 严格匹配
        if expected == "?":
            status = "ℹ️"  # 不检查 LLM fallback
        else:
            status = "✅" if r.attribution == expected else "❌"
        print(f"  {status} {r.attribution:18s} (expected {expected:18s}) | {text[:60]}")


if __name__ == "__main__":
    _test_attribution()