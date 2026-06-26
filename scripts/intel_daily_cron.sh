#!/bin/bash
# 大V情报 — 每日 cron 主脚本
# 跑 4 大V 增量 (并发) → 自检 (4 项)
#
# 调度: mavis cron 0 22 * * * (UTC) = 北京 06:00 (前一天的 22:00)
# 时区: server 是 UTC (Etc/UTC), 不要假设 Asia/Shanghai

set -e

LOG_DIR=/workspace/logs/intel_cron
HEALTH_DIR=/workspace/logs
DATE=$(date -u +%Y%m%d)
mkdir -p $LOG_DIR

echo "=========================================="
echo "大V情报 — daily cron (UTC $(date -u +%Y-%m-%dT%H:%M:%S))"
echo "北京: $(TZ='Asia/Shanghai' date +%Y-%m-%dT%H:%M:%S)"
echo "=========================================="

# 1. 并发跑 4 大V 增量抓取
echo ""
echo "=== 阶段 1: 4 大V 增量抓取 (并发) ==="
PIDS=""
for kol in jukan05 aleabitoreddit zephyr_z9 austinsemis; do
  LOG_FILE=$LOG_DIR/intel_cron_${kol}_${DATE}.log
  echo "  启动: $kol (log: $LOG_FILE)"
  nohup python /workspace/scripts/intel_incremental_scrape.py --kol $kol > $LOG_FILE 2>&1 &
  PIDS="$PIDS $!"
done

# 等所有增量跑完
echo "  PIDs: $PIDS"
for pid in $PIDS; do
  wait $pid
  EXIT=$?
  if [ $EXIT -ne 0 ]; then
    echo "  ⚠ PID $pid exit code: $EXIT"
  fi
done

echo ""
echo "=== 阶段 2: 4 项自检 ==="

# 2. 跑自检
python /workspace/scripts/intel_daily_health.py
HEALTH_EXIT=$?

# 3. 退出码
echo ""
echo "=========================================="
if [ $HEALTH_EXIT -ne 0 ]; then
  echo "❌ cron 自检不通过 (exit $HEALTH_EXIT)"
  echo "  看 /workspace/logs/intel_health_${DATE}.log"
  # 通知用户 (email/slack 后续加)
else
  echo "✅ cron 完成 + 自检通过"
fi
echo "=========================================="

exit $HEALTH_EXIT
