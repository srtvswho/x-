#!/bin/bash
# 大V情报 — 每日 cron 主脚本
# 模块 1 (抓取) -> 模块 2 (抽取) -> 自检 -> DB gzip -> push GitHub
#
# 调度: mavis cron 0 6 * * * Asia/Shanghai = 北京 06:00
# 时区: server 是 UTC, mavis cron 'Asia/Shanghai' 解释
#
# 各阶段失败处理:
# - 阶段 1 (抓取) 部分失败: 不阻塞, 记录; 某大V 失败不影响其他
# - 阶段 2 (抽取) 失败: 不阻塞, 记录 (增量数据下次补抽)
# - 阶段 3 (自检) 失败: 跳阶段 4 push (不推损坏 DB)
# - 阶段 4 (push) 失败: 不阻塞, 数据安全 (NFS 本地备份还在)

set -e

LOG_DIR=/workspace/logs/intel_cron
HEALTH_DIR=/workspace/logs
DATE=$(date -u +%Y%m%d)
mkdir -p $LOG_DIR

# ===== 阶段 0: 依赖检查 (sandbox 重启会丢包, 自动装回) =====
echo "=== 阶段 0: 依赖检查 ==="
python3 -c "import requests, apify_client" 2>/dev/null || {
  echo "  ⚠ 依赖丢失, pip install..."
  pip3 install --break-system-packages --timeout 300 requests apify-client 2>&1 | tail -3
  python3 -c "import requests, apify_client; print('  ✓ 依赖恢复')" || {
    echo "  ❌ 依赖装不上, cron 跳过本次"
    exit 1
  }
}
echo "  ✓ 依赖 OK"

echo "=========================================="
echo "大V情报 — daily cron (UTC $(date -u +%Y-%m-%dT%H:%M:%S))"
echo "北京: $(TZ='Asia/Shanghai' date +%Y-%m-%dT%H:%M:%S)"
echo "=========================================="

# ===== 阶段 1: 模块 1 - 4 大V 增量抓取 (并发) =====
echo ""
echo "=== 阶段 1: 模块 1 — 4 大V 增量抓取 (并发) ==="
PIDS=""
for kol in jukan05 aleabitoreddit zephyr_z9 austinsemis; do
  LOG_FILE=$LOG_DIR/intel_cron_${kol}_${DATE}.log
  echo "  启动: $kol (log: $LOG_FILE)"
  nohup python /workspace/scripts/intel_incremental_scrape.py --kol $kol > $LOG_FILE 2>&1 &
  PIDS="$PIDS $!"
done

# 等所有增量跑完 (某大V 失败不阻塞其他)
SCRAPE_OK=0
for pid in $PIDS; do
  wait $pid
  EXIT=$?
  if [ $EXIT -ne 0 ]; then
    echo "  ⚠ PID $pid 抓取失败 (exit $EXIT)"
  else
    SCRAPE_OK=$((SCRAPE_OK + 1))
  fi
done
echo "  ✓ 4 大V 抓取完成: $SCRAPE_OK/4 成功"

# ===== 阶段 2: 模块 2 - 增量抽取 (仅今天新入库 + 未抽取过的) =====
echo ""
echo "=== 阶段 2: 模块 2 — 增量抽取 (从 7 天 since, 跳过已抽取) ==="
EXTRACT_LOG=$LOG_DIR/intel_cron_extract_${DATE}.log

# since 7 天前覆盖可能的 cron 漏抽窗口
SINCE=$(TZ='Asia/Shanghai' date -d "7 days ago" +%Y-%m-%d)
echo "  since: $SINCE (7 天, 覆盖可能漏抽窗口)"
echo "  log: $EXTRACT_LOG"

# 抽取失败不阻塞 cron (增量下次补)
set +e
python /workspace/scripts/intel_extract.py --since "$SINCE" > $EXTRACT_LOG 2>&1
EXTRACT_EXIT=$?
set -e

if [ $EXTRACT_EXIT -ne 0 ]; then
  echo "  ⚠ 模块 2 抽取 exit $EXTRACT_EXIT (看 log, 下次重试)"
else
  # 解析 log 抽取数 (包 set +e 防 grep fail 退出)
  set +e
  NEW_N=$(grep -oE '成功 [0-9]+' $EXTRACT_LOG 2>/dev/null | tail -1 | grep -oE '[0-9]+' 2>/dev/null)
  if [ -z "$NEW_N" ]; then NEW_N=0; fi
  set -e
  echo "  ✓ 抽取完成: 成功 $NEW_N 条 (增量, 跳过已抽取)"
fi

# ===== 阶段 3: 自检 =====
echo ""
echo "=== 阶段 3: 4 项自检 ==="
python /workspace/scripts/intel_daily_health.py
HEALTH_EXIT=$?

# 自检不通过 -> 跳阶段 4 push (避免推损坏 DB)
if [ $HEALTH_EXIT -ne 0 ]; then
  echo ""
  echo "=========================================="
  echo "❌ cron 自检不通过 (exit $HEALTH_EXIT), 跳阶段 4 push"
  echo "  看 /workspace/logs/intel_health_${DATE}.log"
  echo "=========================================="
  exit $HEALTH_EXIT
fi

# ===== 阶段 4: DB gzip + GitHub push =====
echo ""
echo "=== 阶段 4: DB gzip + GitHub push ==="
bash /workspace/scripts/intel_daily_github_push.sh
PUSH_EXIT=$?

# ===== 阶段 5: 每日健康速查 (4 项一眼看) =====
echo ""
echo "=== 阶段 5: 每日健康速查 ==="
QC_LOG=$LOG_DIR/intel_quickcheck_${DATE}.log
python /workspace/scripts/intel_quickcheck.py > $QC_LOG 2>&1
QC_EXIT=$?
if [ $QC_EXIT -eq 0 ]; then
  echo "  ✅ 速查全绿"
else
  echo "  ⚠ 速查有异常 (exit $QC_EXIT), 看 $QC_LOG"
fi
# 也打印到 stdout (用户看得到)
cat $QC_LOG | head -50

# ===== 退出码 =====
echo ""
echo "=========================================="
if [ $HEALTH_EXIT -ne 0 ]; then
  echo "❌ cron 自检不通过 (exit $HEALTH_EXIT)"
elif [ $PUSH_EXIT -ne 0 ]; then
  echo "⚠ 自检通过但 push 失败 (exit $PUSH_EXIT), 数据安全 (NFS 本地备份还在)"
elif [ $QC_EXIT -ne 0 ]; then
  echo "⚠ cron 完成但速查有异常 (exit $QC_EXIT), 看 quickcheck log"
else
  echo "✅ cron 完成 + 抽取 + 自检 + push + 速查全绿"
fi
echo "=========================================="

exit $((HEALTH_EXIT + PUSH_EXIT + QC_EXIT))