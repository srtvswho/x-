"""Jukan 网络挖掘 v2 — 重跑, 1 批 4 个并发 (避免 archon-server 超时)"""
import sys
sys.path.insert(0, '/workspace')

# 复用 jukan_network.py 的逻辑, 但分批跑
from scripts.jukan_network import (
    extract_network, is_noise, apify_fetch, llm_triage,
    OUT_DIR, DEEPSEEK_API_KEY
)
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

network, relation = extract_network()

# Top 12 候选 (>= 3 次)
candidates = []
for h, c in network.most_common(30):
    if c < 3:
        break
    if h == "jukan05":
        continue
    if is_noise(h):
        continue
    candidates.append((h, c, relation[h]))

# 排除 PatrickMoorhead (AMD CMO, 大V)
candidates = [(h, c, r) for h, c, r in candidates if h.lower() != "patrickmoorhead"]
print(f"候选: {len(candidates)} 个")

# 分批 4 个并发
results = {}
batch_size = 4
for i in range(0, len(candidates), batch_size):
    batch = candidates[i:i+batch_size]
    print(f"\n批 {i//batch_size + 1}/{(len(candidates)+batch_size-1)//batch_size}: {[h for h,_,_ in batch]}")
    with ThreadPoolExecutor(max_workers=batch_size) as pool:
        futures = {pool.submit(apify_fetch, h, 30): h for h, _, _ in batch}
        for fut in as_completed(futures):
            h = futures[fut]
            try:
                items = fut.result()
            except Exception as e:
                items = []
                print(f"  {h}: error {e}")
            results[h] = {"n_items": len(items), "items": items}
            print(f"  {h}: {len(items)} items")

# LLM 分诊 (并发 8 路)
print("\nLLM 分诊 (并发 8 路)...")
def triage_one(h, c, rel):
    r = results.get(h, {})
    items = r.get("items", [])
    if not items:
        return h, {"n_items": 0, "triage": {"lookalike_jukan": 0, "evidence": "no_data"}, "interaction_count": c, "interaction_type": f"R{rel.get('reply',0)}/Q{rel.get('quote',0)}/RT{rel.get('retweet',0)}"}
    triage = llm_triage(h, items)
    return h, {"n_items": len(items), "triage": triage, "interaction_count": c, "interaction_type": f"R{rel.get('reply',0)}/Q{rel.get('quote',0)}/RT{rel.get('retweet',0)}"}

with ThreadPoolExecutor(max_workers=8) as pool:
    futures = {pool.submit(triage_one, h, c, rel): h for h, c, rel in candidates}
    for fut in as_completed(futures):
        h = futures[fut]
        try:
            _, r = fut.result()
        except Exception as e:
            r = {"n_items": 0, "triage": {"lookalike_jukan": 0, "evidence": f"err: {e}"}}
        results[h].update(r)
        lj = r.get("triage", {}).get("lookalike_jukan", 0)
        type_str = r.get("triage", {}).get("type", "?")
        market = r.get("triage", {}).get("market", "?")
        print(f"  {h}: n={r.get('n_items',0)} lookalike={lj}/3 type={type_str} market={market}")

# 保存
(OUT_DIR / "triage_results_v2.json").write_text(json.dumps({
    h: {"n_items": r["n_items"], "interaction_count": r.get("interaction_count", 0),
         "interaction_type": r.get("interaction_type", "?"), "triage": r.get("triage", {})}
    for h, r in results.items()
}, indent=2, ensure_ascii=False))

# 每个候选的 items 也存一份
for h, r in results.items():
    if r.get("items"):
        json.dump(r["items"], open(OUT_DIR / f"items_{h}.json", "w"), indent=2, ensure_ascii=False)

# 输出报告
ranked = sorted(results.items(), key=lambda x: -x[1].get("triage", {}).get("lookalike_jukan", 0))

lines = [
    "# Jukan 网络挖掘 v2 — 找『第二个 Jukan』(P5-5)",
    "",
    f"**网络账号**: {len(network)} | 筛后 (≥3 互动 + 排除大V + 排除 Moorhead): {len(candidates)}",
    "",
    "## Top 候选 (按 lookalike_jukan 排序)",
    "",
    "| # | 账号 | 互动 | n | type | market | signals | **像 Jukan** | 证据 |",
    "|---|---|---|---|---|---|---|---|---|",
]
for i, (h, r) in enumerate(ranked, 1):
    t = r.get("triage", {})
    type_str = t.get("type", "?")
    market = t.get("market", "?")
    sigs = t.get("signals_strength", 0)
    lj = t.get("lookalike_jukan", 0)
    ev = (t.get("evidence", "") or "")[:50].replace("|", "/")
    n = r.get("n_items", 0)
    rel_str = r.get("interaction_type", "?")
    lines.append(f"| {i} | @{h} | {rel_str} | {n} | {type_str} | {market} | {sigs} | **{lj}/3** | {ev} |")

# lookalike >= 2 重点
top_picks = [(h, r) for h, r in ranked if r.get("triage", {}).get("lookalike_jukan", 0) >= 2]
lines.extend([
    "",
    "## 🎯 像 Jukan ≥ 2 候选",
    "",
])
if top_picks:
    for h, r in top_picks:
        t = r.get("triage", {})
        lines.extend([
            f"### @{h}",
            f"- **lookalike: {t.get('lookalike_jukan', 0)}/3** | type: {t.get('type', '?')} | market: {t.get('market', '?')}",
            f"- signals_strength: {t.get('signals_strength', 0)}/3 | tickers: {t.get('tickers_mentioned', [])}",
            f"- 证据: {t.get('evidence', '')}",
            f"- 互动: {r.get('interaction_count', 0)} 次 ({r.get('interaction_type', '?')})",
            "",
            "**代表内容**:",
        ])
        for it in (r.get("items", []) or [])[:5]:
            text = (it.get("text") or "")[:200]
            lines.append(f"> [{it.get('createdAt','?')[:10]}] {text}")
        lines.append("")
else:
    lines.append("⚠️ 没有 lookalike ≥ 2")
    # 给 lookalike = 1 的
    backup = [(h, r) for h, r in ranked if r.get("triage", {}).get("lookalike_jukan", 0) == 1]
    if backup:
        lines.append("\n### lookalike = 1 候选 (备选)")
        for h, r in backup[:5]:
            t = r.get("triage", {})
            lines.append(f"- @{h}: {t.get('type','?')} / {t.get('market','?')} — {t.get('evidence','')[:80]}")

out = Path("/workspace/outputs/p5_jukan_network_candidates_v2.md")
out.write_text("\n".join(lines))
print(f"\n📄 {out}")