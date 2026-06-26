#!/bin/bash
cd /workspace
python3 << 'EOF'
import os, json, urllib.request
API_TOKEN = os.environ['APIFY_TOKEN']
rid = "u6i2d6o75cvuaXlb3"
url = f"https://api.apify.com/v2/acts/61RPP7dywgiy0JPD0/runs/{rid}?token={API_TOKEN}"
with urllib.request.urlopen(url, timeout=15) as r:
    data = json.loads(r.read().decode())
    did = data.get("data", {}).get("defaultDatasetId")
url2 = f"https://api.apify.com/v2/datasets/{did}/items?token={API_TOKEN}&limit=1500"
with urllib.request.urlopen(url2, timeout=60) as r:
    items = json.loads(r.read().decode())
json.dump(items, open('/workspace/logs/p5_dnystedt/raw2_2026-01-01_2026-06-22.json', 'w'), indent=2, ensure_ascii=False)
print(f"saved {len(items)}")
EOF
