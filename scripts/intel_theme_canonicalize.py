#!/usr/bin/env python3
"""Audit and conservatively canonicalize Themes using embeddings + Terra judgment."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signalboard.ai.router import AIResult, call_json, embed_texts, record_usage, stable_input_hash
from signalboard.db import init_db

DB_PATH = "/workspace/data/signalboard_full.db"
EMBED_MODEL = "text-embedding-3-small"
EMBED_DIMENSIONS = 256
PROMPT_VERSION = "theme-canonical-v1.1"

JUDGMENT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "judgments": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "pair_id": {"type": "string"},
                    "decision": {"type": "string", "enum": ["MERGE_ALIAS", "RELATED_DISTINCT", "DISTINCT"]},
                    "canonical_name": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "rationale": {"type": "string"},
                },
                "required": ["pair_id", "decision", "canonical_name", "confidence", "rationale"],
            },
        }
    },
    "required": ["judgments"],
}

SYSTEM = """你负责投资研究主题本体治理。Embedding 只负责召回相似候选，你必须根据语义和 Claim 语境独立判断。
MERGE_ALIAS 仅用于同一经济/技术主题的不同语言、缩写或同义表达；上下游、驱动因素、产品与受益逻辑必须保留为 RELATED_DISTINCT。
尤其不能因为共同出现就把 Agent Memory、AI demand、NAND、China WFE、CoPoS、CoWoP、ABF、PCB 合并。
canonical_name 必须逐字选择该 pair 的 left_name 或 right_name。宁可不合并，不可误合并。"""

CONSTRAINT_MARKERS = ("bottleneck", "shortage", "constraint", "瓶颈", "短缺", "约束")


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    denom = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / denom if denom else 0.0


def _themes(con: sqlite3.Connection) -> list[dict]:
    rows = con.execute(
        """
        SELECT t.theme_id, t.name, COALESCE(t.description,''), t.parent_theme_id,
               COUNT(DISTINCT ct.claim_id), COUNT(DISTINCT c.author_id),
               COUNT(DISTINCT c.source_post_id)
        FROM themes t
        LEFT JOIN claim_themes ct ON ct.theme_id=t.theme_id
        LEFT JOIN claims c ON c.claim_id=ct.claim_id
        GROUP BY t.theme_id, t.name, t.description, t.parent_theme_id
        ORDER BY t.name COLLATE NOCASE
        """
    ).fetchall()
    out = []
    for theme_id, name, description, parent, claims, authors, posts in rows:
        examples = [r[0] for r in con.execute(
            """SELECT c.claim_text FROM claims c JOIN claim_themes ct ON ct.claim_id=c.claim_id
               WHERE ct.theme_id=? ORDER BY c.confidence DESC, c.created_at DESC LIMIT 3""", (theme_id,)
        ).fetchall()]
        out.append({
            "theme_id": theme_id, "name": name, "description": description,
            "parent_theme_id": parent, "claim_count": claims, "author_count": authors,
            "post_count": posts, "examples": examples,
        })
    return out


def _embedding_text(theme: dict) -> str:
    return json.dumps({
        "theme": theme["name"], "description": theme["description"],
        "representative_claims": theme["examples"],
    }, ensure_ascii=False, sort_keys=True)


def _load_embeddings(con: sqlite3.Connection, themes: list[dict]) -> tuple[dict[str, list[float]], float]:
    vectors: dict[str, list[float]] = {}
    missing: list[dict] = []
    for theme in themes:
        text = _embedding_text(theme)
        input_hash = stable_input_hash(PROMPT_VERSION, text)
        row = con.execute(
            "SELECT input_hash, embedding_json FROM theme_embeddings WHERE theme_id=? AND model=?",
            (theme["theme_id"], EMBED_MODEL),
        ).fetchone()
        if row and row[0] == input_hash:
            vectors[theme["theme_id"]] = json.loads(row[1])
        else:
            theme["_input_hash"] = input_hash
            missing.append(theme)
    cost = 0.0
    for start in range(0, len(missing), 100):
        batch = missing[start:start + 100]
        result = embed_texts([_embedding_text(x) for x in batch], model=EMBED_MODEL, dimensions=EMBED_DIMENSIONS)
        cost += result.estimated_cost_usd
        for theme, vector in zip(batch, result.vectors):
            vectors[theme["theme_id"]] = vector
            con.execute(
                """INSERT OR REPLACE INTO theme_embeddings
                   (theme_id, model, dimensions, input_hash, embedding_json) VALUES (?, ?, ?, ?, ?)""",
                (theme["theme_id"], EMBED_MODEL, EMBED_DIMENSIONS, theme["_input_hash"], json.dumps(vector)),
            )
        usage = AIResult(
            text="", data=None, workload="theme_embedding", provider="openai", model=EMBED_MODEL,
            input_tokens=result.input_tokens, output_tokens=0, estimated_cost_usd=result.estimated_cost_usd,
            latency_ms=result.latency_ms, request_id=result.request_id,
        )
        record_usage(con, usage, workload="theme_embedding", object_type="theme_batch", object_id=str(start // 100 + 1))
        con.commit()
    return vectors, round(cost, 8)


def _nearest(themes: list[dict], vectors: dict[str, list[float]]) -> tuple[list[dict], list[dict]]:
    candidates: dict[tuple[str, str], dict] = {}
    for left in themes:
        ranked: list[tuple[float, dict]] = []
        for right in themes:
            if left["theme_id"] == right["theme_id"]:
                continue
            sim = _cosine(vectors[left["theme_id"]], vectors[right["theme_id"]])
            ranked.append((sim, right))
        ranked.sort(key=lambda x: x[0], reverse=True)
        if ranked:
            left["nearest_theme"] = ranked[0][1]["name"]
            left["nearest_theme_id"] = ranked[0][1]["theme_id"]
            left["nearest_similarity"] = round(ranked[0][0], 6)
            for sim, right in ranked[:4]:
                lexical_same = "".join(c for c in left["name"].casefold() if c.isalnum()) == \
                               "".join(c for c in right["name"].casefold() if c.isalnum())
                if sim < 0.65 and not lexical_same:
                    continue
                ids = tuple(sorted((left["theme_id"], right["theme_id"])))
                candidates[ids] = {
                    "pair_id": hashlib.sha256("\n".join(ids).encode()).hexdigest()[:16],
                    "left": left, "right": right, "similarity": round(sim, 6),
                }
    return themes, sorted(candidates.values(), key=lambda x: x["similarity"], reverse=True)


def _judge(con: sqlite3.Connection, candidates: list[dict], max_pairs: int) -> tuple[list[dict], float]:
    judgments: list[dict] = []
    cost = 0.0
    for start in range(0, min(len(candidates), max_pairs), 20):
        batch = candidates[start:start + 20]
        payload = [{
            "pair_id": x["pair_id"], "embedding_similarity": x["similarity"],
            "left_name": x["left"]["name"], "left_claims": x["left"]["examples"],
            "right_name": x["right"]["name"], "right_claims": x["right"]["examples"],
        } for x in batch]
        result = call_json(
            "theme_canonicalization", SYSTEM, json.dumps(payload, ensure_ascii=False), JUDGMENT_SCHEMA,
            schema_name="signalboard_theme_judgment", max_output_tokens=2400, timeout=150,
        )
        by_id = {x["pair_id"]: x for x in batch}
        for judgment in result.data["judgments"]:
            candidate = by_id.get(judgment["pair_id"])
            if not candidate:
                continue
            left, right = candidate["left"], candidate["right"]
            canonical_name = judgment["canonical_name"]
            if canonical_name not in {left["name"], right["name"]}:
                judgment["decision"] = "DISTINCT"
                judgment["canonical_name"] = ""
                judgment["rationale"] = "Invalid canonical name returned; merge rejected. " + judgment["rationale"]
            judgment.update({
                "left_theme_id": left["theme_id"], "left_name": left["name"],
                "right_theme_id": right["theme_id"], "right_name": right["name"],
                "embedding_similarity": candidate["similarity"], "model": result.model,
            })
            judgments.append(judgment)
            canonical_id = None
            if canonical_name == left["name"]:
                canonical_id = left["theme_id"]
            elif canonical_name == right["name"]:
                canonical_id = right["theme_id"]
            audit_id = "themeaudit_" + candidate["pair_id"]
            con.execute(
                """INSERT OR REPLACE INTO theme_canonicalization_audit
                   (audit_id,left_theme_id,right_theme_id,embedding_similarity,decision,
                    canonical_theme_id,confidence,rationale,model)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (audit_id, left["theme_id"], right["theme_id"], candidate["similarity"],
                 judgment["decision"], canonical_id, judgment["confidence"], judgment["rationale"], result.model),
            )
        record_usage(con, result, workload="theme_canonicalization", object_type="theme_pair_batch", object_id=str(start // 20 + 1))
        con.commit()
        cost += result.estimated_cost_usd
    return judgments, round(cost, 8)


def _apply_merges(con: sqlite3.Connection, judgments: list[dict]) -> int:
    merged = 0
    for item in judgments:
        if item["decision"] != "MERGE_ALIAS" or float(item["confidence"]) < 0.82:
            continue
        canonical_id = item["left_theme_id"] if item["canonical_name"] == item["left_name"] else item["right_theme_id"]
        alias_id = item["right_theme_id"] if canonical_id == item["left_theme_id"] else item["left_theme_id"]
        alias_name = item["right_name"] if canonical_id == item["left_theme_id"] else item["left_name"]
        left_constraint = any(x in item["left_name"].casefold() for x in CONSTRAINT_MARKERS)
        right_constraint = any(x in item["right_name"].casefold() for x in CONSTRAINT_MARKERS)
        if left_constraint != right_constraint:
            # A demand/supply constraint is a causal driver, not an alias of the product itself.
            item["decision"] = "RELATED_DISTINCT"
            item["canonical_name"] = ""
            item["rationale"] = "Deterministic guard: constraint/bottleneck theme must remain distinct from product theme."
            con.execute(
                """UPDATE theme_canonicalization_audit
                   SET decision='RELATED_DISTINCT',canonical_theme_id=NULL,
                       rationale=?
                   WHERE (left_theme_id=? AND right_theme_id=?) OR (left_theme_id=? AND right_theme_id=?)""",
                (item["rationale"], item["left_theme_id"], item["right_theme_id"],
                 item["right_theme_id"], item["left_theme_id"]),
            )
            continue
        if con.execute("SELECT parent_theme_id FROM themes WHERE theme_id=?", (canonical_id,)).fetchone()[0] == alias_id:
            continue
        collision = con.execute(
            """SELECT 1 FROM theses a JOIN theses c ON c.author_id=a.author_id
               WHERE a.theme_id=? AND c.theme_id=? LIMIT 1""", (alias_id, canonical_id),
        ).fetchone()
        if collision:
            # Never silently collapse two version histories. Keep the pair auditable for manual review.
            continue
        con.execute(
            """INSERT OR IGNORE INTO claim_themes (claim_id, theme_id, confidence)
               SELECT claim_id, ?, confidence FROM claim_themes WHERE theme_id=?""", (canonical_id, alias_id),
        )
        con.execute("DELETE FROM claim_themes WHERE theme_id=?", (alias_id,))
        con.execute("UPDATE theses SET theme_id=? WHERE theme_id=?", (canonical_id, alias_id))
        row = con.execute("SELECT aliases_json FROM themes WHERE theme_id=?", (canonical_id,)).fetchone()
        aliases = json.loads(row[0] or "[]")
        if alias_name not in aliases:
            aliases.append(alias_name)
        con.execute(
            "UPDATE themes SET aliases_json=?, updated_at=strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE theme_id=?",
            (json.dumps(sorted(aliases), ensure_ascii=False), canonical_id),
        )
        con.execute(
            "UPDATE themes SET parent_theme_id=?, updated_at=strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE theme_id=?",
            (canonical_id, alias_id),
        )
        merged += 1
    # Rebuild denormalized claim theme names from the canonical links.
    for (claim_id,) in con.execute("SELECT claim_id FROM claims").fetchall():
        names = [r[0] for r in con.execute(
            """SELECT t.name FROM claim_themes ct JOIN themes t ON t.theme_id=ct.theme_id
               WHERE ct.claim_id=? AND t.parent_theme_id IS NULL ORDER BY t.name""", (claim_id,)
        ).fetchall()]
        con.execute("UPDATE claims SET themes_json=? WHERE claim_id=?", (json.dumps(names, ensure_ascii=False), claim_id))
    con.commit()
    return merged


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_PATH)
    ap.add_argument("--output", default="outputs/thesis_engine_v11/theme_audit.json")
    ap.add_argument("--max-pairs", type=int, default=120)
    ap.add_argument("--apply", action="store_true", help="仅应用 Terra 高置信 MERGE_ALIAS；默认只审计")
    args = ap.parse_args()
    init_db(args.db)
    con = sqlite3.connect(args.db, timeout=120)
    themes = _themes(con)
    vectors, embedding_cost = _load_embeddings(con, themes)
    themes, candidates = _nearest(themes, vectors)
    judgments, judgment_cost = _judge(con, candidates, args.max_pairs)
    judgment_by_pair = {frozenset((x["left_theme_id"], x["right_theme_id"])): x for x in judgments}
    for theme in themes:
        theme["nearest_judgment"] = judgment_by_pair.get(
            frozenset((theme["theme_id"], theme.get("nearest_theme_id", "")))
        )
        theme.pop("_input_hash", None)
    merged = _apply_merges(con, judgments) if args.apply else 0
    report = {
        "theme_count": len(themes),
        "singleton_theme_count": sum(1 for x in themes if x["claim_count"] <= 1),
        "candidate_pair_count": len(candidates), "judged_pair_count": len(judgments),
        "applied_merge_count": merged, "themes": themes, "judgments": judgments,
        "cost": {"embedding_usd": embedding_cost, "terra_judgment_usd": judgment_cost,
                 "total_usd": round(embedding_cost + judgment_cost, 8)},
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    con.close()
    print(json.dumps({k: v for k, v in report.items() if k not in {"themes", "judgments"}}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
