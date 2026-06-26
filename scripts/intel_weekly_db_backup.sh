#!/bin/bash
# 大V情报 — 周日 DB 备份 (本地 NFS gzip 滚动 4 周)
# 原因: GitHub 100MB 单文件限制, DB 现在 110MB, gzip 后 ~25MB 但之前 commit 里的旧 DB 也算
# 策略: 每周日 gzip 备份到 /workspace/data/backups/, 滚动 4 周 (超出删最旧)
# 验证: 自动 gzip 后 1 周, 2 周, 4 周 size < X 健康阈值
# 恢复: gunzip < backup.gz | sqlite3 .db (手工)

set -e

WORKSPACE=/workspace
DB=$WORKSPACE/data/signalboard_full.db
BACKUP_DIR=$WORKSPACE/data/backups
LOG_DIR=$WORKSPACE/logs/intel_backup
DATE=$(date -u +%Y%m%d)
WEEKDAY=$(date -u +%u)  # 1=Mon, 7=Sun
mkdir -p $BACKUP_DIR $LOG_DIR

echo "=========================================="
echo "DB weekly backup (UTC $(date -u +%Y-%m-%dT%H:%M:%S), weekday=$WEEKDAY)"
echo "=========================================="

# 1. 安全性: weekday 7 (周日) 才跑 (cron 设了, 保险)
if [ "$WEEKDAY" != "7" ]; then
  echo "  ⚠ 今天不是周日 (weekday=$WEEKDAY), 跳过"
  exit 0
fi

# 2. VACUUM 缩 DB (减少 gzip 后 size)
echo "  VACUUM DB..."
sqlite3_path=$(which sqlite3 2>/dev/null || echo "")
if [ -n "$sqlite3_path" ]; then
  $sqlite3_path $DB "VACUUM"
else
  python3 -c "import sqlite3; con=sqlite3.connect('$DB', timeout=80, isolation_level=None); con.execute('VACUUM'); con.close()"
fi
ls -lh $DB | awk '{print "  DB post-VACUUM: " $5}'

# 3. Gzip 备份
BACKUP_FILE=$BACKUP_DIR/signalboard_$DATE.db.gz
echo "  Gzip -> $BACKUP_FILE"
gzip -c $DB > $BACKUP_FILE
BACKUP_SIZE=$(du -h $BACKUP_FILE | cut -f1)
echo "  Backup size: $BACKUP_SIZE"

# 4. 写 manifest (供 .gitignore 排除的 .gitkeep commit)
echo "  ---"
echo "  Manifest:"
ls -lh $BACKUP_DIR/signalboard_*.db.gz 2>&1 | tail -10

# 5. 滚动 4 周 (超出删最旧)
echo "  ---"
echo "  Cleanup: keep latest 4 weekly backups"
ls -1t $BACKUP_DIR/signalboard_*.db.gz 2>/dev/null | tail -n +5 | while read OLD; do
  echo "    删除: $OLD"
  rm -f $OLD
done

# 6. 验证完整性 (gunzip + 简单 SQL query)
echo "  ---"
echo "  Integrity check:"
gunzip -c $BACKUP_FILE | python3 -c "
import sys, sqlite3, tempfile, os
tf = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
tf.write(sys.stdin.buffer.read())
tf.close()
con = sqlite3.connect(tf.name, timeout=15)
n = con.execute('SELECT COUNT(*) FROM raw_posts').fetchone()[0]
print(f'    raw_posts: {n:,} rows')
con.close()
os.unlink(tf.name)
"

# 7. 健康检查
TOTAL_BACKUPS=$(ls $BACKUP_DIR/signalboard_*.db.gz 2>/dev/null | wc -l)
echo "  ---"
echo "  健康: $TOTAL_BACKUPS 个 backup 存在 (期望 1-4)"
if [ "$TOTAL_BACKUPS" -gt 4 ]; then
  echo "  ⚠ 太多 backup, 检查 cleanup 逻辑"
fi

echo ""
echo "✅ Weekly DB backup done (本地 NFS, 不 push GitHub)"
