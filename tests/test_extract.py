"""signalboard.extract 单元测试。

覆盖:
  - prefilter:cashtag / 关键词 / 别名命中
  - context:quote / reply / 自线程
  - postprocess:别名解析
  - evaluate:指标计算(用金标=LLM输入)
  - caller:缓存
  - prompts:版本号 + 渲染
"""
from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path


# 本地 fixture helper(无 pytest)
import tempfile
def _tmp_db():
    return Path(tempfile.mkdtemp()) / "test.db"

def _tmp_db_with_aliases():
    p = _tmp_db()
    from signalboard import init_db
    init_db(p)
    with sqlite3.connect(p, timeout=10) as conn:
        conn.executemany(
            "INSERT INTO aliases (alias_raw, ticker, market, asset_class, locale) VALUES (?, ?, ?, ?, ?)",
            [
                ("AXTI", "AXTI", "美股", "equity", "en"),
                ("绿的谐波", "688017", "A股", "equity", "zh_cn"),
                ("688017", "688017", "A股", "equity", "zh_cn"),
                ("Foci", "3363.TW", "TW", "equity", "en"),
            ],
        )
        conn.commit()
    return p


# 直接导入(不依赖 LLM API)
from signalboard.extract.prefilter import prefilter_post, prefilter_stats
from signalboard.extract.context import assemble, render_for_llm
from signalboard.extract.postprocess import resolve_alias, _load_alias_index
from signalboard.extract.evaluate import (
    LLMPostResult, LLMPrediction, evaluate, render_report,
)
from signalboard.extract.goldset import GOLD_V1
from signalboard.extract.prompts import (
    PROMPT_VERSION, get_system_prompt, build_user_prompt, FEW_SHOT_EXAMPLES,
)


# 共享 fixture: 临时 db(只用 schema,数据由 prefilter 测自行塞)
def db_with_aliases() -> Path:
    """建临时 db,塞几条 alias,返回路径。"""
    return _tmp_db_with_aliases()


# ===========================================================================
# prefilter
# ===========================================================================


def test_prefilter_cashtag_hit():
    """$TICKER 命中。"""
    r = prefilter_post("I think $AXTI is going up")
    assert r.passed
    assert any("cashtag" in m for m in r.matched_rules)


def test_prefilter_a_share_code_hit():
    """A股 6 位代码命中。"""
    r = prefilter_post("688017 绿的谐波是国产谐波减速器龙头")
    assert r.passed
    assert any("a_share" in m for m in r.matched_rules)


def test_prefilter_keyword_hit():
    """关键词命中。"""
    r = prefilter_post("This is a strong bottleneck thesis for AI industry")
    assert r.passed
    assert any("kw_en" in m for m in r.matched_rules)


def test_prefilter_chinese_keyword_hit():
    """中文关键词命中。"""
    r = prefilter_post("我重仓了这只股票,目标价 100")
    assert r.passed


def test_prefilter_pure_chitchat_skipped():
    """纯社交/闲聊应跳过。"""
    r = prefilter_post("Just chilling today, the weather is nice")
    assert not r.passed
    assert r.reason == "no_ticker_no_keyword"


def test_prefilter_empty_text_skipped():
    r = prefilter_post("")
    assert not r.passed


def test_prefilter_alias_hit():
    """aliases 表命中(不依赖 cashtag 或关键词)。"""
    r = prefilter_post("My buddy bought some AXTI last month", db_path=db_with_aliases())
    assert r.passed
    assert any("alias" in m for m in r.matched_rules)


def test_prefilter_stats_returns_breakdown():
    rows = [
        {"post_id": "1", "raw_text": "long $AXTI"},
        {"post_id": "2", "raw_text": "chilling"},
        {"post_id": "3", "raw_text": "688017 看涨"},
    ]
    s = prefilter_stats(rows)
    assert s["total"] == 3
    assert s["passed"] == 2
    assert "cashtag" in s["rule_breakdown"]


# ===========================================================================
# context assemble
# ===========================================================================


def _make_item(post_id="1", *, is_reply=False, is_quote=False, is_retweet=False,
               text="hello", in_reply_to=None, quoted_tweet=None, user_id="u1"):
    item = {
        "id": post_id, "tweetId": post_id, "text": text, "full_text": text,
        "isReply": is_reply, "isQuote": is_quote, "isRetweet": is_retweet,
        "userId": user_id, "inReplyToId": in_reply_to,
    }
    if quoted_tweet is not None:
        item["quotedTweet"] = quoted_tweet
    return item


def test_context_quote_includes_quoted_text():
    db = _tmp_db()
    from signalboard import init_db
    init_db(db)
    item = _make_item(post_id="1", is_quote=True, text="看这只", quoted_tweet={"text": "好推文"})
    ctx = assemble(item, db)
    assert "好推文" in (ctx.quote_full_text or "")
    assert ctx.anchor_raw_text == "看这只"


def test_context_retweet_skipped():
    db = _tmp_db()
    from signalboard import init_db
    init_db(db)
    item = _make_item(post_id="1", is_retweet=True, text="RT hello")
    ctx = assemble(item, db)
    assert ctx.is_retweet is True


def test_context_reply_without_parent_marks_missing():
    db = _tmp_db()
    from signalboard import init_db
    init_db(db)
    item = _make_item(post_id="1", is_reply=True, text="@you hi", in_reply_to=None)
    ctx = assemble(item, db)
    assert ctx.context_missing is True


def test_context_reply_with_parent_in_library():
    """父推文在库中,parent_in_library=True 且 quote_full_text 含父推文。"""
    db = _tmp_db()
    from signalboard import init_db
    init_db(db)
    # 塞父推文
    with sqlite3.connect(db, timeout=10) as conn:
        conn.execute(
            "INSERT INTO raw_posts (post_id, source_id, platform, published_at, captured_at, raw_text, raw_url, raw_json, content_hash) "
            "VALUES (?, 'tw_x', 'twitter', '2026-01-01T00:00:00+00:00', '2026-01-01T00:00:00Z', ?, '', '{}', 'h_parent')",
            ("parent1", "parent content here"),
        )
        conn.commit()
    item = _make_item(post_id="child1", is_reply=True, text="reply text", in_reply_to="parent1", user_id="u1")
    ctx = assemble(item, db)
    assert ctx.parent_in_library is True
    assert "parent content here" in (ctx.quote_full_text or "")


def test_render_for_llm_basic():
    ctx = assemble(_make_item(post_id="1", text="hello"), Path("/tmp/nonexistent"))
    out = render_for_llm(ctx)
    assert "post_id: 1" in out
    assert "hello" in out


def test_render_for_llm_with_quote():
    item = _make_item(post_id="1", is_quote=True, text="main", quoted_tweet={"text": "QUOTED"})
    ctx = assemble(item, Path("/tmp/nonexistent"))
    out = render_for_llm(ctx)
    assert "QUOTED" in out


# ===========================================================================
# postprocess / alias resolution
# ===========================================================================


def test_resolve_alias_direct_match():
    idx = _load_alias_index(db_with_aliases())
    t, m, st = resolve_alias("AXTI", idx, db_path=db_with_aliases())
    assert t == "AXTI"
    assert m == "美股"
    assert st == "resolved"


def test_resolve_alias_chinese():
    idx = _load_alias_index(db_with_aliases())
    t, m, st = resolve_alias("绿的谐波", idx, db_path=db_with_aliases())
    assert t == "688017"
    assert m == "A股"
    assert st == "resolved"


def test_resolve_alias_fallthrough_to_a_share_code():
    """纯 6 位数字代码 → 命中 a_share alias。"""
    idx = _load_alias_index(db_with_aliases())
    t, m, st = resolve_alias("688017", idx, db_path=db_with_aliases())
    assert t == "688017"
    assert st == "resolved"


def test_resolve_alias_taiwan():
    idx = _load_alias_index(db_with_aliases())
    t, m, st = resolve_alias("Foci", idx, db_path=db_with_aliases())
    assert t == "3363.TW"
    assert m == "TW"
    assert st == "resolved"


def test_resolve_alias_unresolved():
    idx = _load_alias_index(db_with_aliases())
    t, m, st = resolve_alias("SomeRandomThing", idx, db_path=db_with_aliases())
    assert t is None
    assert m is None
    assert st == "unresolved"


# ===========================================================================
# evaluate
# ===========================================================================


def _gold_to_llm_results(gold):
    """金标 → 完美 LLM 输出(供 evaluate 测)。"""
    out = []
    for g in gold:
        preds = [
            LLMPrediction(
                post_id=g["post_id"], ticker=p["ticker"], market=p["market"],
                direction=p["direction"], claim_type=p.get("claim_type", "directional"),
                horizon=p.get("horizon", "6m"), conviction=p["conviction"],
                thesis_summary=p.get("thesis_summary", ""),
            )
            for p in g["predictions"]
        ]
        out.append(LLMPostResult(
            post_id=g["post_id"], has_prediction=g["has_prediction"],
            predictions=preds, flags=list(g.get("flags", [])),
        ))
    return out


def test_evaluate_perfect_pass():
    rep = evaluate(_gold_to_llm_results(GOLD_V1))
    assert rep.passed
    assert rep.post_precision == 1.0
    assert rep.post_recall == 1.0
    assert rep.record_f1 == 1.0
    assert rep.flags_recall == 1.0
    assert rep.victory_lap_clean is True


def test_evaluate_victory_lap_violation_caught():
    """胜利巡游帖误抽 → 报告 flag 违规。"""
    gold = _gold_to_llm_results(GOLD_V1)
    # 在金标 #19(2058230354063102028)硬塞一条假阳记录
    for r in gold:
        if r.post_id == "2058230354063102028":
            r.has_prediction = True
            r.predictions = [LLMPrediction(
                post_id=r.post_id, ticker="FAKE", market="美股",
                direction="long", claim_type="directional",
                horizon="6m", conviction=3,
            )]
    rep = evaluate(gold)
    assert not rep.victory_lap_clean
    assert any(v["post_id"] == "2058230354063102028" for v in rep.victory_lap_violations)


def test_evaluate_false_positive_lowers_precision():
    """在无预测帖上硬抽 → precision 降。"""
    gold = _gold_to_llm_results(GOLD_V1)
    # 金标 #2 (无预测) 硬抽一条
    for r in gold:
        if r.post_id == "2059606040417812549":
            r.has_prediction = True
            r.predictions = [LLMPrediction(
                post_id=r.post_id, ticker="FAKE", market="美股",
                direction="long", claim_type="directional",
                horizon="6m", conviction=3,
            )]
    rep = evaluate(gold)
    assert rep.post_precision < 1.0
    assert rep.post_false_pos >= 1


def test_evaluate_missed_flag_counted():
    """金标有 flag,LLM 漏 → flags_recall < 1。"""
    gold = _gold_to_llm_results(GOLD_V1)
    # 金标 #19 有 self_reported_returns + victory_lap,清空 LLM flags
    for r in gold:
        if r.post_id == "2058230354063102028":
            r.flags = []
    rep = evaluate(gold)
    assert rep.flags_recall < 1.0
    assert any(f["post_id"] == "2058230354063102028" for f in rep.flags_missed)


def test_evaluate_render_includes_all_metrics():
    rep = evaluate(_gold_to_llm_results(GOLD_V1))
    text = render_report(rep)
    assert "帖子级" in text
    assert "记录级" in text
    assert "conviction" in text
    assert "flags" in text
    assert "胜利巡游" in text
    assert "✅" in text or "❌" in text


# ===========================================================================
# prompts
# ===========================================================================


def test_prompt_version_is_v1():
    """spec 要求首版 v1。"""
    assert PROMPT_VERSION == "v1.0"


def test_system_prompt_includes_all_rules():
    sp = get_system_prompt()
    for rule in ["提及标的", "供应链", "批评", "victory", "self_reported", "对冲",
                 "清单式", "短期", "conviction 标尺", "raw_asset_mention", "context_missing"]:
        assert rule in sp, f"rule not in prompt: {rule}"


def test_few_shot_has_seven_examples():
    """spec 第 5 节要 7 例 few-shot。"""
    n = FEW_SHOT_EXAMPLES.count("[例 ")
    assert n == 7


def test_build_user_prompt_includes_post_id():
    out = build_user_prompt("abc123", "推文正文")
    assert "abc123" in out
    assert "推文正文" in out
