#!/bin/bash
# P4-10d 用 curl 调 Apify API 抓 @jukan05 长段时间
APIFY_TOKEN="$APIFY_TOKEN"
ACTOR_ID="61RPP7dywgiy0JPD0"

mkdir -p /workspace/logs/p4p10d_x

for period in "2024-12-01:2024-12-31" "2025-01-01:2025-04-30" "2025-05-01:2025-08-31" "2025-09-01:2026-01-31" "2026-02-01:2026-06-22"; do
  SINCE=$(echo $period | cut -d: -f1)
  UNTIL=$(echo $period | cut -d: -f2)
  PERIOD_LABEL="${SINCE}_${UNTIL}"

  echo "=== Period: $PERIOD_LABEL ==="

  # 1. start run
  INPUT_JSON=$(cat <<EOF
{
  "searchTerms": ["from:jukan05 since:${SINCE} until:${UNTIL}"],
  "maxItems": 1000,
  "sort": "Latest"
}
EOF
)

  RUN_INFO=$(curl -sL -X POST "https://api.apify.com/v2/acts/${ACTOR_ID}/runs?token=${APIFY_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$INPUT_JSON" 2>/dev/null)

  RUN_ID=$(echo "$RUN_INFO" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('data',{}).get('id',''))" 2>/dev/null)
  if [ -z "$RUN_ID" ]; then
    echo "  ! start failed: $(echo "$RUN_INFO" | head -c 200)"
    continue
  fi
  echo "  run_id: $RUN_ID"

  # 2. poll
  for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
    sleep 10
    STATUS=$(curl -sL "https://api.apify.com/v2/acts/${ACTOR_ID}/runs/${RUN_ID}?token=${APIFY_TOKEN}" 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); s=d.get('data',{}).get('status',''); print(s)" 2>/dev/null)
    echo "  [poll $i] status: $STATUS"
    if [ "$STATUS" = "SUCCEEDED" ] || [ "$STATUS" = "FAILED" ] || [ "$STATUS" = "ABORTED" ]; then
      break
    fi
  done

  # 3. get dataset items
  DATASET_ID=$(curl -sL "https://api.apify.com/v2/acts/${ACTOR_ID}/runs/${RUN_ID}?token=${APIFY_TOKEN}" 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('data',{}).get('defaultDatasetId',''))" 2>/dev/null)

  if [ -n "$DATASET_ID" ]; then
    curl -sL "https://api.apify.com/v2/datasets/${DATASET_ID}/items?token=${APIFY_TOKEN}&format=json&limit=1000" \
      -o "/workspace/logs/p4p10d_x/${PERIOD_LABEL}.json" 2>/dev/null
    COUNT=$(python3 -c "import json; print(len(json.load(open('/workspace/logs/p4p10d_x/${PERIOD_LABEL}.json'))))" 2>/dev/null)
    echo "  → saved $COUNT items"
  fi
done

echo "=== Done ==="