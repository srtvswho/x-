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

## 2026-11-16 有限恢复续接

自动抓取暂由 `twitterapi-finite-recovery.yml` 负责。共享额度仍为 30,000 credits，累计预留不归零，绝对截止为 2026-11-22 08:10 UTC；到期不自动回退至旧 Apify/DeepSeek 日更。旧日更的自动入口暂停，手动入口仍保留。新增 AI 解读未启用，不把原帖恢复宣称为解读更新。

推送本恢复 workflow 只回放缓存，不带 provider key；定时入口仅处理既有有限策略中到期的完整日窗口。发布前以原 Actions 身份做 dry-run push 预检，写入被拒时停止，不替换凭据、不强推。仍须核对 production receipt。

同一帖若先作为引用上下文保存为 `ctx_tw_*`，后在本人时间线出现，只有原 JSON 作者、字符串帖子 ID、原文及发布时间全部一致时，才把 source_id 升为对应 `tw_*`。保留原文字段、原 JSON、归档/删除标记和所有既有解读；`twitterapi_source_promotions` 留存旧来源、原 JSON 哈希及验证时间。冲突或证据不完整继续拒绝，整批事务回滚。此规则共用于历史与日窗口缓存回放。

健康检查读取经过验证的时间线覆盖，按覆盖截止时刻检查新鲜度，不以重新导入时刻洗新日期，也不改旧 scrape_state。核验过的空窗口可表示未发帖，部分抓取和无证据的零新增仍不算成功。

## 2026-11-18 缺失 AI 解读续跑

用户明确要求补跑 AI。`ai-missing-recovery.yml` 独立处理 8 个既有作者 11 月 5 日至 18 日（不含）已保存原帖的缺失解读；不是全历史重抽，不调用抓取、行情或 OpenAI。固定 campaign `missing-ai-20261118`，抽取累计上限 $2，含逐证券复核及摘要的全部阶段累计上限 $2.30，每日仍受 $3 限额。500 次/分片的旧单次请求上限保留；分片、重启、重跑不能重置 campaign 累计费用。截止 11 月 22 日 08:10 UTC，此 workflow 无付费定时入口。

先单条真实请求验证，再最多五条并发。每条回答在语义入库前保存，每批最多 75 条后压缩并提交数据库检查点；接口/预算异常停止后续批次。HTTP 4xx 不再重复相同请求。旧逐证券回答校验失败原因从数据库恢复，允许针对具体校验错误修正一次；保留原回答及证据门槛，不绕过 DUPLICATE_SUCCESS。JSON 不完整的结果进入 deferred，不宣称全部完成。产物发布仍须原有内容哈希验收。

最新原帖、解读队列、摘要各自记录状态。作者周/月/季观点回顾由既有 `author_briefs.py` 用保存的解读重建；模型摘要刷新当前窗口及最近三个北京时间日期，较早归档保持原样。

未来新采集场景的接口、范围与验收见 `docs/INGESTION_OPERATING_MODEL.md`。现有 TwitterAPI 30,000 credits 授权及绝对截止未改变，长期额度尚未配置，不能称为永久日更已经完成。
