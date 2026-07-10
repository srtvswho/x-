#!/bin/bash
# 大V情报 — 每日 cron 主脚本
# 模块 1 (抓取) -> 模块 2 (抽取) -> 自检 -> DB gzip -> push GitHub
#
# 调度: mavis cron 0 6 * * * Asia/Shanghai = 北京 06:00
# 时区: server 是 UTC, mavis cron 'Asia/Shanghai' 解释
# 生产容器挂载: -v /home/admin/x--master:/workspace (保持 /workspace 字面量)
#
# 各阶段失败处理:
# - 阶段 -1 (漂移补偿 + cron_run_log 写入): 无条件 INSERT 一行到 cron_run_log (含 drift),
#   然后判断 scrape_state.max(last_fetched_at) < 4h → 写 SKIP_FILE 让阶段 1+2 跳过
# - 阶段 1 (抓取) 部分失败: set +e 包裹 wait, 某大V 失败不影响其他
# - 阶段 2 (抽取) 失败: set +e 捕获 EXIT, 不阻塞 cron
# - 阶段 3 (自检) 失败: set +e 捕获 HEALTH_EXIT, 跳阶段 4 push
# - 阶段 4 (push) 失败: set +e 捕获 PUSH_EXIT, 不阻塞 (NFS 本地备份还在)
# - 阶段 5 (quickcheck) 失败: set +e 捕获 QC_EXIT, 不阻塞 cron
#
# 关键设计 (修复原版 bug):
# 原版在 Python 子进程里 set os.environ["INTEL_SKIP_SCRAPE"] = "1", 但子进程 env 不会传回
# 父 shell, 后续 [ "${INTEL_SKIP_SCRAPE:-0}" = "1" ] 永远 False, 跳过逻辑失效.
# 本版用 SKIP_FILE 文件 flag 把 skip 决策传出来 (Python 写文件, shell 检查文件).

set -e

# ===== 顶部初始化 — 所有分支用到的变量 (A + C/D/E/F/G 都需要) =====
INTEL_SKIP_SCRAPE=0
PIDS=""
SCRAPE_OK=0
SCRAPE_EXIT=0
EXTRACT_EXIT=0
NEW_N=0
HEALTH_EXIT=0
PUSH_EXIT=0
QC_EXIT=0
SUMMARY="OK"

LOG_DIR=/workspace/logs/intel_cron
HEALTH_DIR=/workspace/logs
DATE=$(date -u +%Y%m%d)
SKIP_FILE="$LOG_DIR/skip_scrape_${DATE}.flag"
mkdir -p "$LOG_DIR"
# ===== 阶段 -1: cron_run_log 写入 (drift 日志) + 漂移补偿决策 (B) =====
echo ""
echo "=== 阶段 -1: 漂移补偿 + cron_run_log 写入 ==="
rm -f "$SKIP_FILE"  # 清理上次残留
python3 << PYEOF
import sqlite3, datetime, os, sys
DB = "/workspace/data/signalboard_full.db"
SKIP_FILE = "$SKIP_FILE"
now = datetime.datetime.now(datetime.timezone.utc)
scheduled_str = os.environ.get("MAVIS_CRON_SCHEDULED_AT", "")
drift_s = 0
if scheduled_str:
    try:
        sched = datetime.datetime.fromisoformat(scheduled_str.replace("Z", "+00:00"))
        drift_s = int((now - sched).total_seconds())
    except Exception:
        pass
try:
    con = sqlite3.connect(DB, timeout=30)
    # 1) 无条件 INSERT 一行 cron_run_log (含 drift) — 保留原版行为
    con.execute(
        "INSERT INTO cron_run_log (task_name, actual_run_at, scheduled_at, drift_seconds, drift_minutes, extra) VALUES (?, ?, ?, ?, ?, ?)",
        ("intel-daily-fetch", now.isoformat().replace("+00:00", "Z"),
         scheduled_str or now.isoformat().replace("+00:00", "Z"),
         drift_s, drift_s / 60.0, "{}"))
    con.commit()
    # 2) 漂移补偿判断: scrape_state < 4h → 写 SKIP_FILE
    row = con.execute("SELECT MAX(last_fetched_at) FROM scrape_state").fetchone()
    last = row[0] if row else None
    if last:
        last_dt = datetime.datetime.fromisoformat(last.replace("Z", "+00:00"))
        hours_since = (now - last_dt).total_seconds() / 3600
        print(f"  last fetch: {last} ({hours_since:.1f}h ago) | drift: {drift_s/60:.1f} min")
        if hours_since < 4.0:
            print(f"  >> {hours_since:.1f}h < 4.0h, 写 SKIP_FILE (阶段 1+2 跳过)")
            with open(SKIP_FILE, "w") as f:
                f.write(f"hours_since={hours_since:.2f}\nlast_fetch={last}\n")
        else:
            print(f"  >> {hours_since:.1f}h >= 4.0h, 正常跑阶段 1+2")
    else:
        print("  scrape_state 空, 首次跑 (阶段 1+2 正常)")
    con.close()
except Exception as e:
    print(f"  阶段 -1 err (不阻塞): {e}", file=sys.stderr)
PYEOF

if [ -f "$SKIP_FILE" ]; then
    INTEL_SKIP_SCRAPE=1
    echo "  ✓ SKIP flag 已写入 → INTEL_SKIP_SCRAPE=1"
    cat "$SKIP_FILE"
else
    INTEL_SKIP_SCRAPE=0
    echo "  → INTEL_SKIP_SCRAPE=0 (正常跑)"
fi

# ===== 阶段 0: 依赖检查 (sandbox 重启会丢包, 自动装回) =====
echo "=== 阶段 0: 依赖检查 ==="
python3 -c "import requests, apify_client" 2>/dev/null || {
  echo "  ⚠ 依赖丢失, pip install..."
  pip3 install --break-system-packages --timeout 300 -i https://mirrors.aliyun.com/pypi/simple/ requests apify-client 2>&1 | tail -3
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
if [ "$INTEL_SKIP_SCRAPE" = "1" ]; then
    echo "  ⏭ skipped (漂移补偿: 4h 内已抓取)"
    # 不伪造 SCRAPE_OK: skip 不是 4/4 成功
else
    PIDS=""
    for kol in jukan05 aleabitoreddit zephyr_z9 austinsemis; do
      LOG_FILE=$LOG_DIR/intel_cron_${kol}_${DATE}.log
      echo "  启动: $kol (log: $LOG_FILE)"
      nohup python /workspace/scripts/intel_incremental_scrape.py --kol $kol > $LOG_FILE 2>&1 &
      PIDS="$PIDS $!"
    done

    # 等所有增量跑完 (某大V 失败不阻塞其他) — set +e 保护 (C)
    set +e
    SCRAPE_OK=0
    for pid in $PIDS; do
      wait "$pid"
      EXIT=$?
      if [ "$EXIT" -ne 0 ]; then
        echo "  ⚠ PID $pid 抓取失败 (exit $EXIT)"
      else
        SCRAPE_OK=$((SCRAPE_OK + 1))
      fi
    done
    set -e
    SCRAPE_EXIT=0  # 即使部分失败也记 0, 让 cron 继续
    echo "  ✓ 4 大V 抓取完成: $SCRAPE_OK/4 成功"
fi

# ===== 阶段 2: 模块 2 - 增量抽取 (D: 受 INTEL_SKIP_SCRAPE 控制) =====
echo ""
echo "=== 阶段 2: 模块 2 — 增量抽取 (从 7 天 since, 跳过已抽取) ==="
EXTRACT_LOG=$LOG_DIR/intel_cron_extract_${DATE}.log

if [ "$INTEL_SKIP_SCRAPE" = "1" ]; then
    echo "  ⏭ skipped (漂移补偿: 4h 内已抓取)"
    # 不伪造 EXTRACT_EXIT/NEW_N: skip 没跑
else
    SINCE=$(TZ='Asia/Shanghai' date -d "7 days ago" +%Y-%m-%d)
    echo "  since: $SINCE (7 天, 覆盖可能漏抽窗口)"
    echo "  log: $EXTRACT_LOG"

    # 抽取失败不阻塞 cron (增量下次补)
    set +e
    python /workspace/scripts/intel_extract.py --since "$SINCE" > $EXTRACT_LOG 2>&1
    EXTRACT_EXIT=$?
    set -e

    if [ "$EXTRACT_EXIT" -ne 0 ]; then
        echo "  ⚠ 模块 2 抽取 exit $EXTRACT_EXIT (看 log, 下次重试)"
        NEW_N=0
    else
        # 解析 log 抽取数 (包 set +e 防 grep fail 退出)
        set +e
        NEW_N=$(grep -oE '成功 [0-9]+' $EXTRACT_LOG 2>/dev/null | tail -1 | grep -oE '[0-9]+' 2>/dev/null)
        if [ -z "$NEW_N" ]; then NEW_N=0; fi
        set -e
        echo "  ✓ 抽取完成: 成功 $NEW_N 条 (增量, 跳过已抽取)"
    fi
fi

# ===== 阶段 3: 自检 — set +e 捕获退出码 (E) =====
echo ""
echo "=== 阶段 3: 4 项自检 ==="
HEALTH_EXIT=0
set +e
python /workspace/scripts/intel_daily_health.py
HEALTH_EXIT=$?
set -e

# 自检不通过 -> 跳阶段 4 push (避免推损坏 DB)
if [ "$HEALTH_EXIT" -ne 0 ]; then
    echo ""
    echo "=========================================="
    echo "❌ cron 自检不通过 (exit $HEALTH_EXIT), 跳阶段 4 push"
    echo "  看 /workspace/logs/intel_health_${DATE}.log"
    echo "=========================================="
    PUSH_EXIT=0
    QC_EXIT=0
    SUMMARY="HEALTH_FAIL"
else
    # ===== 阶段 4: DB gzip + GitHub push — set +e 捕获退出码 (F) =====
    echo ""
    echo "=== 阶段 4: DB gzip + GitHub push ==="
    PUSH_EXIT=0
    set +e
    bash /workspace/scripts/intel_daily_github_push.sh
    PUSH_EXIT=$?
    set -e

    # ===== 阶段 5: 每日健康速查 — set +e 捕获退出码 (G) =====
    echo ""
    echo "=== 阶段 5: 每日健康速查 ==="
    QC_LOG=$LOG_DIR/intel_quickcheck_${DATE}.log
    QC_EXIT=0
    set +e
    python /workspace/scripts/intel_quickcheck.py > $QC_LOG 2>&1
    QC_EXIT=$?
    set -e
    if [ "$QC_EXIT" -eq 0 ]; then
        echo "  ✅ 速查全绿"
    else
        echo "  ⚠ 速查有异常 (exit $QC_EXIT), 看 $QC_LOG"
    fi
    # 也打印到 stdout (用户看得到)
    cat "$QC_LOG" | head -50

    SUMMARY="OK"
fi

# ===== 退出码 =====
echo ""
echo "=========================================="
case "$SUMMARY" in
    HEALTH_FAIL)
        echo "❌ cron 自检不通过 (exit $HEALTH_EXIT)"
        ;;
    OK)
        if [ "$PUSH_EXIT" -ne 0 ]; then
            echo "⚠ 自检通过但 push 失败 (exit $PUSH_EXIT), 数据安全 (NFS 本地备份还在)"
        elif [ "$QC_EXIT" -ne 0 ]; then
            echo "⚠ cron 完成但速查有异常 (exit $QC_EXIT), 看 quickcheck log"
        else
            echo "✅ cron 完成 + 抽取($NEW_N) + 自检 + push + 速查全绿"
        fi
        ;;
esac
if [ "$INTEL_SKIP_SCRAPE" = "1" ]; then
    echo "  阶段 1 抓取: skipped"
    echo "  阶段 2 抽取: skipped"
else
    echo "  阶段 1 抓取: $SCRAPE_OK/4 (exit=$SCRAPE_EXIT)"
    echo "  阶段 2 抽取: 成功 $NEW_N (exit=$EXTRACT_EXIT)"
fi
echo "  阶段 3 自检: exit=$HEALTH_EXIT"
echo "  阶段 4 push: exit=$PUSH_EXIT"
echo "  阶段 5 quickcheck: exit=$QC_EXIT"
echo "  INTEL_SKIP_SCRAPE: $INTEL_SKIP_SCRAPE"
echo "=========================================="

# 收尾: 清理 SKIP_FILE
rm -f "$SKIP_FILE"

exit $((HEALTH_EXIT + PUSH_EXIT + QC_EXIT))
