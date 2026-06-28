#!/bin/bash
# 大V情报 — 每日 DB gzip + GitHub push
#
# 为什么必须 gzip:
# - 原始 DB 111MB > GitHub 100MB 单文件限制
# - 推不上去 → 历史教训: 用 git reset --hard 拉回老 DB → 删库
# - 这次: 文件大就压缩, 绝不回滚 DB
#
# 流程:
# 1. gzip 当前 DB → data/signalboard.db.gz (~16MB)
# 2. commit .gz
# 3. push 到 GitHub
# 4. 失败处理: 不要重试 reset / 任何可能动 DB 的操作, 只重试 push

set -e

WORKSPACE=/workspace
DB=$WORKSPACE/data/signalboard_full.db
GZ=$WORKSPACE/data/signalboard.db.gz
LOG_DIR=$WORKSPACE/logs/intel_backup
DATE=$(date -u +%Y%m%d)
mkdir -p $LOG_DIR

LOG_FILE=$LOG_DIR/github_push_$DATE.log

echo "==========================================" | tee -a $LOG_FILE
echo "GitHub push (UTC $(date -u +%Y-%m-%dT%H:%M:%S))" | tee -a $LOG_FILE
echo "==========================================" | tee -a $LOG_FILE

# 0. 安全检查
echo "" | tee -a $LOG_FILE
echo "=== 0. 安全检查 ===" | tee -a $LOG_FILE
if [ ! -f "$DB" ]; then
  echo "  ❌ DB 不存在: $DB" | tee -a $LOG_FILE
  exit 1
fi
if [ -z "${GH_TOKEN}" ]; then
  echo "  ❌ GH_TOKEN 未设置 (用 secret tool 加密存)" | tee -a $LOG_FILE
  exit 1
fi

# 1. 完整性检查
INTEGRITY=$(python3 -c "
import sqlite3
con = sqlite3.connect('$DB', timeout=30)
r = con.execute('PRAGMA integrity_check').fetchone()[0]
print(r)
con.close()
")
if [ "$INTEGRITY" != "ok" ]; then
  echo "  ❌ DB integrity_check 失败: $INTEGRITY" | tee -a $LOG_FILE
  echo "  !!! 不要重试, 立即检查 DB !!!" | tee -a $LOG_FILE
  exit 1
fi
echo "  ✓ DB integrity: ok ($(du -h $DB | cut -f1))" | tee -a $LOG_FILE

# 2. Gzip
echo "" | tee -a $LOG_FILE
echo "=== 1. Gzip 压缩 ===" | tee -a $LOG_FILE
gzip -c $DB > $GZ
GZ_SIZE=$(du -h $GZ | cut -f1)
GZ_BYTES=$(stat -c %s $GZ)
echo "  ✓ $GZ" | tee -a $LOG_FILE
echo "  ✓ Size: $GZ_SIZE ($GZ_BYTES bytes)" | tee -a $LOG_FILE

# 3. Gzip 完整性验证
gzip -t $GZ
echo "  ✓ gzip integrity: ok" | tee -a $LOG_FILE

# 安全阀: 超过 90MB 警告 (但仍 push, 因为比原始 111MB 至少小一半)
if [ $GZ_BYTES -gt 94371840 ]; then
  echo "  ⚠ gzip 后 $GZ_BYTES bytes > 90MB (90MB threshold)" | tee -a $LOG_FILE
  echo "  ⚠ 数据增长太快, 但仍然 PUSH (用户要求)" | tee -a $LOG_FILE
fi

# 4. Git add + commit
echo "" | tee -a $LOG_FILE
echo "=== 2. Git commit ===" | tee -a $LOG_FILE
cd $WORKSPACE

git status --short data/ 2>&1 | tee -a $LOG_FILE
echo "  ---" | tee -a $LOG_FILE

git add data/signalboard.db.gz 2>&1 | tee -a $LOG_FILE
git add .gitignore 2>&1 | tee -a $LOG_FILE

# 检查是否有实质变化 (跳过空 commit)
if git diff --cached --quiet; then
  echo "  ⚠️ .gz 未变 (DB 无数据变化), 跳过 commit + push" | tee -a $LOG_FILE
  echo "" | tee -a $LOG_FILE
  echo "==========================================" | tee -a $LOG_FILE
  echo "✅ Daily DB backup — 无变化, 跳过" | tee -a $LOG_FILE
  echo "==========================================" | tee -a $LOG_FILE
  exit 0
fi

git status --short data/ 2>&1 | tee -a $LOG_FILE

git commit -m "Daily DB backup $DATE (gzip $GZ_SIZE)" 2>&1 | tee -a $LOG_FILE || echo "  (无变化可 commit, 跳过)"

# 5. Push (失败重试 1 次, 不动 DB)
echo "" | tee -a $LOG_FILE
echo "=== 3. GitHub push ===" | tee -a $LOG_FILE
PUSH_OK=0
for attempt in 1 2; do
  echo "  尝试 #$attempt" | tee -a $LOG_FILE
  if GIT_TERMINAL_PROMPT=0 timeout 300 git push https://x-access-token:${GH_TOKEN}@github.com/srtvswho/x-.git master 2>&1 | tee -a $LOG_FILE; then
    PUSH_OK=1
    break
  else
    echo "  push 失败, 重试..." | tee -a $LOG_FILE
    sleep 10
  fi
done

if [ $PUSH_OK -eq 0 ]; then
  echo "" | tee -a $LOG_FILE
  echo "❌ push 失败 2 次" | tee -a $LOG_FILE
  echo "  不要 reset / 任何动 DB 操作!" | tee -a $LOG_FILE
  echo "  可能原因: 网络 / GitHub 限速 / 100MB 限制" | tee -a $LOG_FILE
  echo "  NFS 本地备份还有 14 天, 数据安全" | tee -a $LOG_FILE
  exit 1
fi

# 6. 验证 (GitHub API)
echo "" | tee -a $LOG_FILE
echo "=== 4. GitHub 验证 ===" | tee -a $LOG_FILE
LATEST=$(curl -s -H "Authorization: token ${GH_TOKEN}" "https://api.github.com/repos/srtvswho/x-/commits?per_page=1" 2>&1 | python3 -c "
import json, sys
d = json.load(sys.stdin)
c = d[0]
print(f\"  {c['sha'][:8]} | {c['commit']['message'].split(chr(10))[0]}\")
")
echo "$LATEST" | tee -a $LOG_FILE

# 7. token 安全检查
TOKEN_IN_CONFIG=$(git config --get remote.origin.url 2>/dev/null | grep "ghp_" | wc -l)
TOKEN_IN_LOG=$(grep -E "ghp_" $LOG_FILE 2>/dev/null | wc -l)
echo "" | tee -a $LOG_FILE
echo "=== 5. Token 安全 ===" | tee -a $LOG_FILE
echo "  .git/config 含 token: $TOKEN_IN_CONFIG (应 0)" | tee -a $LOG_FILE
echo "  log 含 token: $TOKEN_IN_LOG (应 0)" | tee -a $LOG_FILE

# 8. 总结
echo "" | tee -a $LOG_FILE
echo "==========================================" | tee -a $LOG_FILE
echo "✅ Daily DB backup + GitHub push 完成" | tee -a $LOG_FILE
echo "   DB: $DB ($(du -h $DB | cut -f1))" | tee -a $LOG_FILE
echo "   GZ: $GZ ($GZ_SIZE)" | tee -a $LOG_FILE
echo "   Push: GitHub master" | tee -a $LOG_FILE
echo "==========================================" | tee -a $LOG_FILE
