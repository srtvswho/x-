#!/bin/bash
# dashboard_daily_update.sh — 一键刷新 Dashboard (price → summary → build → validate → publish)
#
# 生产环境 (Docker):
#   宿主机代码: /home/admin/x--master    → 容器 /workspace
#   宿主机网站: /home/admin/www           → 容器 /publish
#   docker run ... -e DASHBOARD_PUBLISH_DIR=/publish -v /home/admin/www:/publish ...
#   此脚本在容器内跑, 看到的 /publish 就是宿主机 /home/admin/www.
#
# 顺序固定: prices → summaries → build → validate → publish (不可调换)
# - prices: refresh_prices_polygon.py (Polygon apiKey 来自 POLYGON_API_KEY 环境变量)
# - summaries: intel_gen_summaries.py (DEEPSEEK_API_KEY 必需, 缺失 → exit 2)
# - build: build_dashboard.py (注入 __TODAY_STATS__ / __TODAY_RECORDS__ / __BUILD_META__)
# - validate: 校验 dashboard.html 存在 + size >= 10000 bytes
# - publish: 原子发布 /publish/index.html + /publish/dashboard.html (两个, 不依赖旧文件)
#
# 硬规则:
# - 不动 data/ DB *.db *.db.gz
# - 不 git push (部署由人工)
# - 不写 API key / env 文件
# - 中间失败: 立即停止 (set -e), 不静默
# - publish 用 .tmp + 原子 mv, 不留半文件
# - 总是同时发布 index.html + dashboard.html, 避免 nginx 首页与 dashboard.html 版本不一致

set -e
set -o pipefail

# ===== 配置 =====
SCRIPTS_DIR=/workspace/scripts/dashboard
# Docker 默认值: /publish (宿主机 /home/admin/www 挂载点).
# 本地开发可以 DASHBOARD_PUBLISH_DIR=/home/admin/www override.
PUBLISH_DIR="${DASHBOARD_PUBLISH_DIR:-/publish}"
SOURCE_HTML="$SCRIPTS_DIR/dashboard.html"
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

ts() { date '+%Y-%m-%dT%H:%M:%S%z'; }
log() { echo "[$(ts)] $*"; }

log "===== Dashboard 每日更新开始 ====="
log "  SCRIPTS_DIR:  $SCRIPTS_DIR"
log "  PUBLISH_DIR:  $PUBLISH_DIR"
log "  source html:  $SOURCE_HTML"
log "  POLYGON_API_KEY set: $([ -n "${POLYGON_API_KEY:-}" ] && echo YES || echo NO)"
log "  DEEPSEEK_API_KEY set: $([ -n "${DEEPSEEK_API_KEY:-}" ] && echo YES || echo NO)"
log "  POLYGON_REQUEST_INTERVAL: ${POLYGON_REQUEST_INTERVAL:-0.6}s"

# ===== 1. Refresh prices (Polygon) =====
log ""
log "[1/4] refresh_prices_polygon.py"
POLYGON_API_KEY="${POLYGON_API_KEY:-}" \
    python3 "$SCRIPTS_DIR/refresh_prices_polygon.py" 2>&1 | tee "$TMP_DIR/01_prices.log"
log "  ✓ prices refreshed"

# ===== 2. Generate summaries (DeepSeek LLM) =====
log ""
log "[2/4] intel_gen_summaries.py"
DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-}" \
    python3 "$SCRIPTS_DIR/intel_gen_summaries.py" 2>&1 | tee "$TMP_DIR/02_summaries.log"
log "  ✓ summaries generated"

# ===== 3. Build dashboard.html =====
log ""
log "[3/4] build_dashboard.py"
python3 "$SCRIPTS_DIR/build_dashboard.py" 2>&1 | tee "$TMP_DIR/03_build.log"
log "  ✓ dashboard built"

# ===== 4. Validate dashboard.html =====
log ""
log "[4/4] validate + publish"
if [ ! -s "$SOURCE_HTML" ]; then
    log "  ✗ $SOURCE_HTML 不存在或为空, 停止发布"
    exit 1
fi
SIZE=$(stat -c%s "$SOURCE_HTML" 2>/dev/null || stat -f%z "$SOURCE_HTML")
if [ "$SIZE" -lt 10000 ]; then
    log "  ✗ dashboard.html 太小 ($SIZE bytes), 可能生成失败, 停止发布"
    exit 1
fi
log "  ✓ validate OK ($SIZE bytes)"

# ===== 5. Atomic publish (总是同时发布 index.html + dashboard.html) =====
mkdir -p "$PUBLISH_DIR"
for fname in index.html dashboard.html; do
    TMP_PUB="$PUBLISH_DIR/.${fname}.tmp.$$"
    cp -a "$SOURCE_HTML" "$TMP_PUB"
    chmod 644 "$TMP_PUB"
    mv -f "$TMP_PUB" "$PUBLISH_DIR/$fname"
    log "  ✓ published: $PUBLISH_DIR/$fname"
done

log ""
log "===== Dashboard 更新完成 ====="
log "  published: $PUBLISH_DIR/index.html"
log "  published: $PUBLISH_DIR/dashboard.html"
log "  size: $SIZE bytes"