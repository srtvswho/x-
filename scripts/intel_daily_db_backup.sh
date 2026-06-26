#!/bin/bash
# 大V情报 — 每日 DB 自动备份 (NFS gzip 副本, 保留 14 天)
#
# 时机: 每日模块1+模块2 cron 跑完后跑 (晚一点)
# 命名: signalboard_YYYYMMDD.db.gz (每天一份)
# 保留: 14 天 (超出删最旧)
# 异地: 用户手动 cp 到本地 (给脚本会打印路径)
# 理由: 刚出 git reset --hard 删库事故, 必须每天自动备份, 不能依赖周备份或手动

set -e

WORKSPACE=/workspace
DB=$WORKSPACE/data/signalboard_full.db
BACKUP_DIR=$WORKSPACE/data/backups/daily
LOG_DIR=$WORKSPACE/logs/intel_backup
DATE=$(date -u +%Y%m%d)
DATE_HUMAN=$(TZ='Asia/Shanghai' date +%Y-%m-%d_%H:%M:%S)
mkdir -p $BACKUP_DIR $LOG_DIR

echo "=========================================="
echo "每日 DB 备份 (UTC $(date -u +%Y-%m-%dT%H:%M:%S) / 北京 $DATE_HUMAN)"
echo "=========================================="

# 1. 确认 DB 存在 + 可读
if [ ! -f "$DB" ]; then
  echo "  ❌ DB 不存在: $DB"
  exit 1
fi

# 2. 备份前 DB 状态
DB_SIZE_BEFORE=$(du -h $DB | cut -f1)
echo "  DB 当前: $DB_SIZE_BEFORE"

# 3. 完整性检查 (PRAGMA integrity_check)
INTEGRITY=$(python3 -c "
import sqlite3
con = sqlite3.connect('$DB', timeout=30)
r = con.execute('PRAGMA integrity_check').fetchone()[0]
print(r)
con.close()
")
if [ "$INTEGRITY" != "ok" ]; then
  echo "  ❌ DB integrity_check 失败: $INTEGRITY"
  echo "  !!! 立即检查 / 不要继续 !!!"
  exit 1
fi
echo "  integrity_check: ok"

# 4. Gzip 备份 (不用 VACUUM, 因为 cron 可能在跑增量; VACUUM 锁表)
BACKUP_FILE=$BACKUP_DIR/signalboard_$DATE.db.gz
echo "  Gzip -> $BACKUP_FILE"
gzip -c $DB > $BACKUP_FILE
BACKUP_SIZE=$(du -h $BACKUP_FILE | cut -f1)
BACKUP_SIZE_BYTES=$(stat -c %s $BACKUP_FILE)
echo "  备份大小: $BACKUP_SIZE ($BACKUP_SIZE_BYTES bytes)"

# 5. 验证 gzip 完整性 (gunzip -t)
gzip -t $BACKUP_FILE
echo "  gzip integrity: ok"

# 6. 滚动 14 天 (超出删最旧)
echo "  ---"
echo "  Cleanup: 保留 14 天"
KEPT=$(ls -1t $BACKUP_DIR/signalboard_*.db.gz 2>/dev/null | wc -l)
ls -1t $BACKUP_DIR/signalboard_*.db.gz 2>/dev/null | tail -n +15 | while read OLD; do
  echo "    删除: $(basename $OLD)"
  rm -f $OLD
done
echo "  现存备份数: $KEPT (期望 ≤ 14)"

# 7. 写 manifest
MANIFEST=$BACKUP_DIR/MANIFEST.txt
echo "  ---"
echo "  写 manifest: $MANIFEST"
{
  echo "# 大V情报每日 DB 备份清单"
  echo "# 更新时间: $(date -u +%Y-%m-%dT%H:%M:%SZ) ($DATE_HUMAN 北京)"
  echo "# 备份源: $DB"
  echo "# 命名: signalboard_YYYYMMDD.db.gz"
  echo "# 保留: 14 天 (超出删最旧)"
  echo "# 恢复: gunzip -c <file> | sqlite3 data/signalboard_full.db"
  echo "# 异地: 见 /workspace/INSTRUCTIONS.txt 或 session 内告诉用户怎么下载"
  echo ""
  printf "%-15s %-10s %s\n" "DATE" "SIZE" "FILE"
  ls -1t $BACKUP_DIR/signalboard_*.db.gz 2>/dev/null | while read F; do
    D=$(basename $F .db.gz | sed 's/signalboard_//')
    S=$(du -h $F | cut -f1)
    printf "  %s      %-10s %s\n" "$D" "$S" "$(basename $F)"
  done
} > $MANIFEST
cat $MANIFEST | tail -20

# 8. 写下载指南 (用户手动拉)
INSTRUCTIONS=$WORKSPACE/INSTRUCTIONS.txt
cat > $INSTRUCTIONS << EOI
# 大V情报 — DB 异地备份指南

## 为什么
刚出 git reset --hard 删库事故 (2026-06-26), 13662 条差点丢光. 
虽然 git blob 救回来了, 但这是侥幸 — DB 跟 git 联动太脆弱.
现在做每日自动备份 + 异地副本 (你手动 cp 到本地).

## 每日自动备份
- 跑时: 北京时间每天 06:00 (cron 跑完后) — see cron task intel-daily-db-backup
- 命名: /workspace/data/backups/daily/signalboard_YYYYMMDD.db.gz
- 保留: 14 天 (超出删最旧)
- manifest: /workspace/data/backups/daily/MANIFEST.txt

## 你手动异地备份 (强烈建议)
每周/每月手动拉一份到本地:

### macOS / Linux
\`\`\`bash
# 用 scp (假设你 SSH 到 sandbox)
scp user@sandbox:/workspace/data/backups/daily/signalboard_\$(date +%Y%m%d).db.gz ~/backups/
# 或用 rsync 同步
rsync -avz user@sandbox:/workspace/data/backups/daily/ ~/backups/signalboard/
\`\`\`

### 或者下载单个
\`\`\`bash
# 从 sandbox URL (如果开放)
wget https://your-sandbox-url/workspace/data/backups/daily/signalboard_\$(date +%Y%m%d).db.gz
\`\`\`

## 恢复
\`\`\`bash
cd /workspace
# 备份当前 (如果还在)
cp data/signalboard_full.db data/signalboard_full.db.broken
# 恢复
gunzip -c data/backups/daily/signalboard_YYYYMMDD.db.gz > data/signalboard_full.db
sqlite3 data/signalboard_full.db "PRAGMA integrity_check"  # 应输出 ok
\`\`\`

## 铁律 (跨项目永久)
- ❌ \`git reset --hard\` 在含 DB 的项目上永远禁止
- ✅ 用 \`git reset --soft\` / \`git revert\` / 精确 \`git show <commit>:<path>\`
- ✅ 任何可能影响 DB 的操作前, 先单独备份 DB 到 /tmp 或独立路径
- ✅ DB 跟 git 解耦 (DB 文件永远在 .gitignore, 不进 commit)
EOI

# 9. 总结
echo ""
echo "=========================================="
echo "✅ 每日 DB 备份完成"
echo "   备份: $BACKUP_FILE ($BACKUP_SIZE)"
echo "   滚动: 14 天"
echo "   manifest: $MANIFEST"
echo "   下载指南: $INSTRUCTIONS"
echo "=========================================="
