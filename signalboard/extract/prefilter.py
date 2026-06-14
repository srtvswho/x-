"""预过滤器(LLM 抽取层入口)。

目的:在调 LLM 前先用规则筛掉大量纯社交/闲聊推文,省费用。
命中规则之一即送 LLM,否则标 prefilter_skipped(可回溯重跑)。

设计原则:
- **不过拟合类型**:回复/引用都可能含预测(样本#10 是 reply 含 4 个 quant 预测)。
  整体按类型跳过是大忌。只跳过明显无标的且无关键词的。
- **关键词和标的双轨**:cashtag / A股代码 / 别名命中任一即过;含预测关键词也过。
- **可解释**:每条过滤结果都带 matched_rules 列表,方便回溯。

规则集(R2.0 版本,基于金标 20 条经验调参):
1. cashtag 模式: $TICKER(2-6 大写字母,允许 . _ -)
2. A股 6 位代码: 6 位连续数字
3. 港股 5 位代码: 4-5 位数字(简单匹配,误报率低)
4. 常见预测关键词:
   - 英文: long, short, bullish, bearish, buy, sell, hold, target, mc, market cap,
            bottleneck, position, thesis, calls, prediction, forecast, calls for,
            moonthly, year, exit, entry, valuation, multiple
   - 中文: 看好, 看空, 看好, 重仓, 轻仓, 目标价, 仓位, 预测, 走势, 看涨, 看跌
5. 已知别名表命中(从 aliases 表读)
"""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union

DbPath = Union[str, Path]


# ---------------------------------------------------------------------------
# 模式
# ---------------------------------------------------------------------------

# Cashtag: $TICKER,2-6 大写字母,可选 . _ -
CASHTAG_RE = re.compile(r'\$([A-Z][A-Z0-9._-]{1,5})')

# A 股 6 位代码(沪深): 在文本里"裸奔"时易误报,但配合预测关键词时准。简化为纯数字连续 6 位。
A_SHARE_RE = re.compile(r'(?<![0-9.])([0-9]{6})(?![0-9])')

# 港股 5 位代码(0xxxx,5 位)
HK_RE = re.compile(r'(?<![0-9.])(0[0-9]{4})(?![0-9])')

# 预测关键词
KEYWORDS_EN = [
    "long", "short", "bullish", "bearish", "buy", "sell", "hold",
    "target", " mc", "market cap", "bottleneck", "position", "thesis",
    "calls", "prediction", "forecast", "calls for", "moonthly", "yearly",
    "exit", "entry", "valuation", "multiple", "conviction", "thesis",
    "moon", "rocket", "calls for", "pt ", "price target", "rating",
    "outperform", "underperform", "overweight", "underweight", "allocat",
    "accumulate", "distribution", "price action",
]
KEYWORDS_ZH = [
    "看好", "看空", "重仓", "轻仓", "目标价", "仓位", "预测", "走势",
    "看涨", "看跌", "买入", "卖出", "持仓", "加仓", "减仓", "涨", "跌",
    "目标", "市值", "百亿", "千亿", "万亿", "收益", "回报", "复合",
    "看好", "看衰", "押注", "梭哈", "看多",
]


@dataclass
class PrefilterResult:
    """一条 raw_post 的预过滤结果。"""
    post_id: str
    passed: bool
    matched_rules: List[str] = field(default_factory=list)
    reason: str = ""  # 未通过时的简短说明


def _normalize(text: str) -> str:
    """简单 normalize:小写、去多余空白。关键词匹配前用。"""
    return re.sub(r'\s+', ' ', text.lower()).strip()


def _keyword_match(text_norm: str) -> List[str]:
    """返回命中的关键词。"""
    hits = []
    for kw in KEYWORDS_EN:
        if kw in text_norm:
            hits.append(f"kw_en:{kw.strip()}")
    for kw in KEYWORDS_ZH:
        if kw in text_norm:
            hits.append(f"kw_zh:{kw}")
    return hits


_ALIAS_CACHE: dict = {}  # db_path -> List[str]


def _get_aliases(db_path: DbPath) -> List[str]:
    """读 alias_raw 列表(NFS 上重复 sqlite3.open 慢,缓存)。"""
    if db_path is None:
        return []
    key = str(db_path)
    if key in _ALIAS_CACHE:
        return _ALIAS_CACHE[key]
    try:
        with sqlite3.connect(db_path, timeout=10) as conn:
            rows = conn.execute(
                "SELECT alias_raw FROM aliases WHERE asset_class != 'commodity'"
            ).fetchall()
    except sqlite3.OperationalError:
        _ALIAS_CACHE[key] = []
        return []
    aliases = [r[0] for r in rows]
    _ALIAS_CACHE[key] = aliases
    return aliases


def _alias_match(text: str, db_path: DbPath) -> List[str]:
    """从 aliases 表读 raw_mention,看 text 里是否含(大小写不敏感)。"""
    hits = []
    aliases = _get_aliases(db_path)
    text_lower = text.lower()
    for alias in aliases:
        a_low = alias.lower()
        if a_low in text_lower or alias in text:
            hits.append(f"alias:{alias}")
    return hits


def prefilter_post(
    text: str,
    *,
    db_path: Optional[DbPath] = None,
) -> PrefilterResult:
    """对单条文本跑预过滤。

    注意:post_id 由调用方填,因为这里只看文本。
    """
    if not text:
        return PrefilterResult(post_id="", passed=False, reason="empty_text")

    matched = []

    # 1) cashtag
    for m in CASHTAG_RE.finditer(text):
        matched.append(f"cashtag:{m.group(1)}")

    # 2) A 股代码
    for m in A_SHARE_RE.finditer(text):
        matched.append(f"a_share:{m.group(1)}")

    # 3) 港股代码
    for m in HK_RE.finditer(text):
        matched.append(f"hk:{m.group(1)}")

    # 4) 关键词
    matched.extend(_keyword_match(_normalize(text)))

    # 5) 别名
    if db_path is not None:
        matched.extend(_alias_match(text, db_path))

    # 去重保序
    seen = set()
    deduped = []
    for m in matched:
        if m not in seen:
            seen.add(m)
            deduped.append(m)
    matched = deduped

    if matched:
        return PrefilterResult(post_id="", passed=True, matched_rules=matched)
    return PrefilterResult(post_id="", passed=False, reason="no_ticker_no_keyword")


def prefilter_batch(
    rows: List[dict],
    *,
    db_path: Optional[DbPath] = None,
) -> List[PrefilterResult]:
    """对多条 raw_post 跑预过滤。rows 元素需含 post_id + raw_text。"""
    results = []
    for r in rows:
        res = prefilter_post(r["raw_text"], db_path=db_path)
        res.post_id = r["post_id"]
        results.append(res)
    return results


# ---------------------------------------------------------------------------
# 统计(给"先取 200 条做实测"用)
# ---------------------------------------------------------------------------

def prefilter_stats(
    rows: List[dict],
    *,
    db_path: Optional[DbPath] = None,
) -> dict:
    """返回通过率、命中规则 top-N 等统计。"""
    results = prefilter_batch(rows, db_path=db_path)
    n = len(results)
    passed = sum(1 for r in results if r.passed)
    rule_counter: dict = {}
    for r in results:
        for rule in r.matched_rules:
            # 去掉具体值,只统计规则类型
            kind = rule.split(":", 1)[0]
            rule_counter[kind] = rule_counter.get(kind, 0) + 1
    return {
        "total": n,
        "passed": passed,
        "pass_rate": round(passed / n * 100, 1) if n else 0.0,
        "rule_breakdown": dict(sorted(rule_counter.items(), key=lambda x: -x[1])),
    }
