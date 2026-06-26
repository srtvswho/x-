#!/bin/bash
cd /workspace
python3 << 'EOF'
import os, json, urllib.request, sys
from collections import defaultdict
from email.utils import parsedate_to_datetime

API_TOKEN = os.environ['APIFY_TOKEN']
ACTOR_ID = '61RPP7dywgiy0JPD0'
runs_meta = json.load(open("/workspace/logs/p5_newcandidates/run_ids.json"))

all_data = {}
for label, rid in runs_meta.items():
    if not rid: continue
    try:
        with urllib.request.urlopen(f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs/{rid}?token={API_TOKEN}", timeout=15) as r:
            rd = json.loads(r.read().decode()).get("data", {})
        if rd.get("status") != "SUCCEEDED":
            print(f"{label}: {rd.get('status')}", flush=True)
            continue
        did = rd.get("defaultDatasetId")
        with urllib.request.urlopen(f"https://api.apify.com/v2/datasets/{did}/items?token={API_TOKEN}&limit=1500", timeout=60) as r:
            items = json.loads(r.read().decode())
        all_data[label] = items
        print(f"{label}: {len(items)}", flush=True)
    except Exception as e:
        print(f"{label}: err {e}", flush=True)

# 合并 by candidate
candidates_data = defaultdict(list)
for label, items in all_data.items():
    # label: "clausaasholm_2024-01-01_2024-12-31"
    cand = label.split("_")[0]
    for it in items:
        candidates_data[cand].append(it)

# 去重
for cand in candidates_data:
    seen = set()
    unique = []
    for it in candidates_data[cand]:
        tid = it.get("id")
        if tid and tid not in seen:
            seen.add(tid)
            unique.append(it)
    candidates_data[cand] = unique

# 保存每个候选
for cand, items in candidates_data.items():
    fp = f"/workspace/logs/p5_newcandidates/raw_{cand}.json"
    with open(fp, "w") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    # 月份分布
    from collections import Counter
    months = Counter()
    for it in items:
        try:
            mo = parsedate_to_datetime(it['createdAt']).strftime("%Y-%m")
            months[mo] += 1
        except:
            months['?'] += 1
    months_sorted = sorted(months.items())
    print(f"\n{cand}: {len(items)} tweets, span: {months_sorted[0][0] if months_sorted else '?'} ~ {months_sorted[-1][0] if months_sorted else '?'}", flush=True)
    for m, c in months_sorted:
        print(f"  {m}: {c}", flush=True)
EOF
