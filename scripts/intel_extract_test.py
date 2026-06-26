"""大V情报 — 模块 2: 结构化抽取 (test 版本, 跑样本给用户看质量)

v2.0.0-intel 简化 prompt (8 字段):
- ticker / company / direction / short_skeptical / bottleneck
- attribution / rebuts_narrative / summary_100

不在 test 模式做的事:
- 不入库 (先看质量)
- 不并发 (test 用)
- 不重试 (fail 就显示)
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

sys.path.insert(0, "/workspace")
from signalboard.extract.prompts_intel import (
    PROMPT_VERSION,
    SYSTEM_PROMPT,
    build_user_prompt,
    get_system_prompt,
)

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-v4-pro"  # 跨项目硬规则


def call_deepseek(system: str, user: str, max_retries: int = 2) -> dict:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY not set")
    data = json.dumps({
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.1,
        "max_tokens": 1500,
        "response_format": {"type": "json_object"},
    }).encode()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    for attempt in range(max_retries + 1):
        try:
            r = requests.post(DEEPSEEK_URL, data=data, headers=headers, timeout=60)
            r.raise_for_status()
            j = r.json()
            content = j["choices"][0]["message"]["content"]
            return {"ok": True, "content": content, "usage": j.get("usage", {})}
        except Exception as e:
            if attempt < max_retries:
                time.sleep(2 + attempt * 3)
                continue
            return {"ok": False, "error": str(e)}


def extract_one(post_id: str, raw_text: str) -> dict:
    """抽一条推文."""
    sys_p = get_system_prompt()
    usr_p = build_user_prompt(post_id, raw_text)
    res = call_deepseek(sys_p, usr_p)
    if not res["ok"]:
        return {"post_id": post_id, "ok": False, "error": res["error"]}
    try:
        parsed = json.loads(res["content"])
    except Exception as e:
        return {"post_id": post_id, "ok": False, "error": f"JSON parse fail: {e}", "raw": res["content"]}
    return {
        "post_id": post_id,
        "ok": True,
        "extraction": parsed,
        "usage": res.get("usage", {}),
    }


def main():
    """test 模式: 接受 post_id 列表 (从 raw_posts 查), 抽 12 条样本."""
    import sqlite3
    con = sqlite3.connect("/workspace/data/signalboard_full.db", timeout=20)
    con.row_factory = sqlite3.Row

    # 12 条样本 (从最近 30 天抽, 4 大V 各 3 条, 覆盖各种场景)
    target_ids = [
        # jukan 3 (产业 fact + 卡点)
        "2069388829841363242",  # TSM 涨价
        "2069266963965350136",  # TPU/Substrate 卡点
        "2069199186516701474",  # Samsung HBM4
        # serenity 3 (含自嘲, 长推)
        "2070189253573890167",  # 自嘲 + MU/SNDK
        "2070185814722834696",  # AAOI 估值
        "2070181783338184877",  # SIVE fabless 比较
        # zephyr 3 (算账 + 转推)
        "2070267916013187449",  # Anthropic 算账
        "2069824935967748247",  # $5B-10B ARR
        "2069447522314330569",  # CXMT IPO
        # austin 3 (明确 long + 反驳 + 消费误抽)
        "2067988055546314891",  # Intel Foundry good Thu
        "2064734302454030566",  # Malbec 消费误抽
        "2063984091779727574",  # Bullish NVDA
    ]
    # 看漏掉的能不能补一条
    for pid in target_ids:
        r = con.execute("SELECT post_id, source_id, substr(raw_text, 1, 250) FROM raw_posts WHERE post_id=?", (pid,)).fetchone()
        if not r:
            print(f"  ❌ {pid} 不在 DB!")
            sys.exit(1)
        print(f"  ✓ {pid} ({r['source_id']})")

    print(f"\n=== 抽 12 条样本 (deepseek-v4-pro, prompt {PROMPT_VERSION}) ===\n")

    results = []
    for i, pid in enumerate(target_ids, 1):
        r = con.execute("SELECT source_id, raw_text FROM raw_posts WHERE post_id=?", (pid,)).fetchone()
        print(f"[{i}/12] {pid} ({r['source_id']})")
        result = extract_one(pid, r["raw_text"])
        if result["ok"]:
            ext = result["extraction"]
            print(f"  direction={ext.get('direction')} | short_skeptical={ext.get('short_skeptical')}")
            print(f"  ticker={ext.get('ticker')}")
            print(f"  bottleneck={ext.get('bottleneck')}")
            print(f"  attribution={ext.get('attribution')}")
            print(f"  rebuts={ext.get('rebuts_narrative')}")
            print(f"  summary={ext.get('summary_100')}")
            print(f"  tokens={result['usage'].get('total_tokens', '?')}")
        else:
            print(f"  ❌ FAIL: {result.get('error')}")
        print()
        results.append(result)

    con.close()

    # 总结
    ok = sum(1 for r in results if r["ok"])
    short_count = sum(1 for r in results if r["ok"] and r["extraction"].get("direction") == "short")
    short_skeptical_count = sum(1 for r in results if r["ok"] and r["extraction"].get("direction") == "short" and r["extraction"].get("short_skeptical") == 1)
    print("=" * 70)
    print(f"总结: 12 条样本, 成功 {ok}/12")
    print(f"  short 抽取: {short_count}")
    print(f"  short_skeptical=1: {short_skeptical_count}")
    print(f"  误抽率: {short_skeptical_count}/{short_count if short_count else 1} (如果 short 少, 看 short_skeptical 默认值)")
    print()
    print("请看每条的方向 / 卡点 / 反驳叙事 抽得准不准, 决定是否继续扩到全量.")


if __name__ == "__main__":
    main()
