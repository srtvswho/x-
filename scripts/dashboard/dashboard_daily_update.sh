#!/bin/bash
# dashboard_daily_update.sh — 一键刷新 Dashboard (price → summary → build → publish)
#
# 设计:
# - 生产容器挂载: -v /home/admin/x--master:/workspace
# - 线上静态目录: ${DASHBOARD_PUBLISH_DIR:-/home/admin/www}
# - 顺序固定: prices → summaries → build → validate → publish (不可调换)
# - POLYGON_API_KEY + DEEPSEEK_API_KEY 来自容器 env (docker run -e ...), 不进 DB
#
# 硬规则:
# - 不动 data/ DB *.db *.db.gz
# - 不 git push (部署由人工)
# - 不写 API key / env 文件
# - 中间失败: 立即停止 (set -e), 不静默
# - publish 用 .tmp + 原子 mv, 不留半文件

set -e
set -o pipefail

# ===== 配置 =====
SCRIPTS_DIR=/workspace/scripts/dashboard
PUBLISH_DIR="${DASHBOARD_PUBLISH_DIR:-/home/admin/www}"
SOURCE_HTML="$SCRIPTS_DIR/dashboard.html"
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

# 入口文件名: 跟 nginx 配置兼容
# 优先 index.html (历史 nginx 配置), fallback dashboard.html
detect_entry() {
    if [ -f "$PUBLISH_DIR/index.html" ] && [ ! -f "$PUBLISH_DIR/dashboard.html" ]; then
        echo "index.html"
    elif [ -f "$PUBLISH_DIR/dashboard.html" ]; then
        echo "dashboard.html"
    elif [ -f "$PUBLISH_DIR/index.html" ]; then
        echo "index.html"
    else
        echo "index.html dashboard.html"  # 默认两个都发
    fi
}
ENTRY_FILES=$(detect_entry)

ts() { date '+%Y-%m-%dT%H:%M:%S%z'; }
log() { echo "[$(ts)] $*"; }

log "===== Dashboard 每日更新开始 ====="
log "  SCRIPTS_DIR:  $SCRIPTS_DIR"
log "  PUBLISH_DIR:  $PUBLISH_DIR"
log "  ENTRY_FILES:  $ENTRY_FILES"
log "  POLYGON_API_KEY set: $([ -n "${POLYGON_API_KEY:-}" ] && echo YES || echo NO)"
log "  DEEPSEEK_API_KEY set: $([ -n "${DEEPSEEK_API_KEY:-}" ] && echo YES || echo NO)"

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

# ===== 5. Atomic publish =====
mkdir -p "$PUBLISH_DIR"
for fname in $ENTRY_FILES; do
    TMP_PUB="$PUBLISH_DIR/.${fname}.tmp.$$"
    cp -a "$SOURCE_HTML" "$TMP_PUB"
    chmod 644 "$TMP_PUB"
    mv -f "$TMP_PUB" "$PUBLISH_DIR/$fname"
    log "  ✓ published: $PUBLISH_DIR/$fname"
done

log ""
log "===== Dashboard 更新完成 ====="
log "  published files: $ENTRY_FILES"
log "  size: $SIZE bytes"