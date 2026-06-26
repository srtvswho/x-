#!/bin/bash
cd /workspace
python3 << 'EOF'
import os, json, urllib.request
from collections import defaultdict, Counter
from email.utils import parsedate_to_datetime
import sys

API_TOKEN = os.environ['APIFY_TOKEN']
ACTOR_ID = '61RPP7dywgiy0JPD0'

# 36 run_ids
runs_meta = json.load(open("/workspace/logs/p5_directional_search/run_ids.json"))

all_authors = defaultdict(lambda: {"tweets": [], "followers": 0, "name": "", "description": "", "months": set(), "kws": set()})
total_tweets = 0
n_done = 0

for label, rid in runs_meta.items():
    if not rid: continue
    try:
        url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs/{rid}?token={API_TOKEN}"
        with urllib.request.urlopen(url, timeout=15) as r:
            rd = json.loads(r.read().decode()).get("data", {})
        if rd.get("status") != "SUCCEEDED":
            print(f"{label}: {rd.get('status')}", flush=True)
            continue
        did = rd.get("defaultDatasetId")
        url2 = f"https://api.apify.com/v2/datasets/{did}/items?token={API_TOKEN}&limit=1500"
        with urllib.request.urlopen(url2, timeout=60) as r:
            items = json.loads(r.read().decode())
        total_tweets += len(items)
        n_done += 1
        # 解析 (ticker, term) from label
        parts = label.rsplit("_", 1)
        ticker = parts[0]
        term = parts[1] if len(parts) > 1 else "?"
        for it in items:
            au = it.get("author") or {}
            h = (au.get("userName") or "").strip()
            if not h: continue
            ca = it.get("createdAt", "")
            try:
                mo = parsedate_to_datetime(ca).strftime("%Y-%m")
            except Exception:
                mo = "?"
            all_authors[h]["tweets"].append({"ticker": ticker, "term": term, "date": ca})
            all_authors[h]["months"].add(mo)
            all_authors[h]["kws"].add(f"{ticker}+{term}")
            all_authors[h]["followers"] = au.get("followers", 0)
            all_authors[h]["name"] = au.get("name", "")
            all_authors[h]["description"] = (au.get("description") or "")[:300]
    except Exception as e:
        print(f"{label}: err {e}", flush=True)
    if n_done % 10 == 0:
        print(f"  done {n_done}/{len(runs_meta)}, authors={len(all_authors)}", flush=True)

out = {h: {"handle": h, "n_tweets": len(d["tweets"]), "n_months": len(d["months"]),
         "months": sorted(d["months"]), "followers": d["followers"],
         "name": d["name"], "description": d["description"], "kws": sorted(d["kws"])}
       for h, d in all_authors.items()}
json.dump(out, open("/workspace/logs/p5_directional_search/authors.json", "w"), indent=2, ensure_ascii=False)
print(f"\n💾 saved: {len(all_authors)} authors, {total_tweets} tweets")
EOF
