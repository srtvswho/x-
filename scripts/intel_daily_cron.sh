#!/bin/bash
# 大V情报 — 每日 cron 主脚本
# 跑 4 大V 增量 (并发) → 自检 (4 项) → DB gzip + GitHub push
#
# 调度: mavis cron 0 6 * * * Asia/Shanghai = 北京 06:00
# 时区: server 是 UTC, mavis cron 'Asia/Shanghai' 解释
# 增补: 阶段 3 GitHub push (gzip 压缩版 DB, 不推原始 111MB)

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

# 自检不通过 → 不 push (避免推损坏 DB)
if [ $HEALTH_EXIT -ne 0 ]; then
  echo ""
  echo "=========================================="
  echo "❌ cron 自检不通过 (exit $HEALTH_EXIT), 跳阶段 3 GitHub push"
  echo "  看 /workspace/logs/intel_health_${DATE}.log"
  echo "=========================================="
  exit $HEALTH_EXIT
fi

echo ""
echo "=== 阶段 3: DB gzip + GitHub push (异地备份, 用户可从 GitHub 下载 .gz) ==="

# 3. DB 备份 + push (gzip 压缩版, 永不推原始 111MB DB)
bash /workspace/scripts/intel_daily_github_push.sh
PUSH_EXIT=$?

# 4. 退出码
echo ""
echo "=========================================="
if [ $HEALTH_EXIT -ne 0 ]; then
  echo "❌ cron 自检不通过 (exit $HEALTH_EXIT)"
elif [ $PUSH_EXIT -ne 0 ]; then
  echo "⚠ 自检通过但 push 失败 (exit $PUSH_EXIT), 数据安全 (NFS 本地备份还在)"
else
  echo "✅ cron 完成 + 自检通过 + push 成功"
fi
echo "=========================================="

exit $((HEALTH_EXIT + PUSH_EXIT))
