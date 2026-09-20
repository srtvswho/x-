# SignalBoard 续跑手册

生产入口：https://signalboard-602.pages.dev 。源仓库 srtvswho/x-，master。生产由现有 GitHub Actions 生成静态快照并由 Cloudflare Pages 发布；不要把未发布的 Sites 同名占位项目当作生产。

## 每次开始

读取本文件和 WORKFLOW_STATE.json，运行 `python scripts/workflow_status.py`。检查远端 master、当前 Actions 运行及 `/build-manifest.json`。源码提交、产物提交和线上验收是三个不同状态；缺少最后一项时保留“待验收”。

## 语义修正

`config/semantic_reviews.json` 保存原帖 ID、作者、证券、原文 SHA256、决定和原因。`signalboard/semantic_review.py` 是普通喊单追踪、市场记录和原帖复核说明共用入口。原文变化后旧裁决失效并进入待复核；不能按相同关键词把裁决扩散到其他帖子。

购买硬件不等于买股票；sold out 及反讽未核实时不进入方向统计。明确更正只作用于对应证券。原文和已有模型解读保留。重点关注继续使用既有冻结回放、历史时点和证券归因门槛，标签仍为 research_candidate，automatic_buy=false。

作者画像引用 2026-09-10 冻结复评，必须保留样本少、周期及同一赢家集中等限制。研究使用评级不是交易胜率，也不自动重新校准原有共识权重。

## 不调用付费 API 的修复发布

从当前 `data/signalboard.db.gz` 恢复到本地临时工作数据库；不要修改原始压缩快照。将 SIGNALBOARD_DB 指向恢复后的工作库。依次运行：

```
python tests/test_semantic_review.py
python tests/test_publication_receipt.py
python tests/test_focus_signals.py
python tests/test_focus_labels.py
python scripts/dashboard/build_dashboard.py
python scripts/dashboard/build_unified_research_data.py --database data/signalboard_full.db --output dashboard_deploy_dist/data/raw-intelligence.json.gz
python scripts/dashboard/build_research_clue_preview.py --deploy-root dashboard_deploy_dist
python scripts/dashboard/validate_unified_app.py
```

UI-only 提交带 `[skip daily]`；现有 unified UI workflow 完成同一组离线步骤并保存完整页面快照。避免重新提取历史内容、调用模型或强制抓取行情。缓存价格可以离线读取，缺失价格继续显示缺失。

## 生产完成条件

构建生成 build-manifest.json，记录源提交、复核规则哈希及各页面/数据内容哈希。构建前后的原帖、6 个复核案例、方向及页面一致性必须通过本地门禁。

发布后运行 `python scripts/dashboard/verify_production.py --wait-seconds 600 --receipt production-receipt.json`，或 `python scripts/workflow_status.py --live`。必须核对线上 manifest 与预期完全一致，并实际读取首页、脚本、追踪、市场、原始情报和重点关注数据的内容哈希。Actions 自动保存 production-receipt 工件；失败不会显示绿色验收。

如果源码已合入但线上旧版，先查看 UI workflow 的具体失败步骤；若构建成功而上线等待，只重跑只读生产校验，不重采数据、不修改语义规则。Cloudflare 尚未发布时保留源提交、预期 manifest 和失败原因。遇到并发数据提交，以最新 master 为基础保留已有数据；不要用本地旧快照覆盖。

每次代码维护完成后更新 WORKFLOW_STATE.json 的真实证据、未完成项和下一步，随代码提交。自动生成产物/回执是运行事实；交接文件是上次维护记录。

## 作者阶段观点（2026-09-20）

市场页默认近一个月，以作者观点回顾为主体，每日归档折叠保留。`author_briefs.py` 在既有离线构建中刷新 8 人 × 6 个窗口，不新增模型、抓取或行情调用。时间边界冻结在构建时刻，不随浏览器当前时间漂移。主线摘读来自已存逐帖解读，原帖日期和链接始终可见；时间轴覆盖所选窗口的不同阶段。

证券方向只使用已有逐证券复核事件，不把一帖的整体方向赋给所有提及证券。条件性表态单列，其余未能确认的提及保留。前后多空记录只显示对照，期限或条件不同不自动判定改口，未观察到变化也不等于观点不变。主题关键词只用于整理阅读段落，不生成买卖结论。

该功能维护时运行 `python tests/test_author_briefs.py` 和原有 publication gate，检查作者筛选、6 个周期、每日归档、原帖跳转。源码发布和实际线上验收仍为两个状态。
