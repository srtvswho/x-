# Dashboard 接入说明 — 给 MiniMax Code（v2，含分层总结）

UI 已做好（dashboard.html，单文件，深色情报终端）。你的任务：只接数据，不改 UI。
模板是 dashboard.template.html（带占位符）。每天 cron 跑完用 build_dashboard.py 生成
dashboard.html → push GitHub。

---

## ★ 这一版新增最重要的东西：分层总结（要 LLM 生成）

dashboard 现在有 4 段/类 LLM 生成的文字总结。dashboard 是静态的，不能自己调 LLM，
所以这些总结必须由你在 cron 里【预生成】好，存起来，build 时读出来注入。

注入点：模板末尾的 __SUMMARIES__ 占位符，结构：

{
  "today": "今日四人总结，≤100字，固定当天",
  "consensus": { "0":"今日共识","1":"近1月","3":"近3月","6":"近6月","12":"近1年" },
  "person": {
    "jukan":    {"0":"...","1":"...","3":"...","6":"...","12":"..."},
    "serenity": {"0":"...","1":"...","3":"...","6":"...","12":"..."},
    "zephyr":   {"0":"...","1":"...","3":"...","6":"...","12":"..."},
    "austin":   {"0":"...","1":"...","3":"...","6":"...","12":"..."}
  }
}

每天要生成的总结 = today(1) + consensus(5窗:0/1/3/6/12) + person(4人×5窗=20) = 26 段。
注：窗口"0"=今日(1D)。consensus["0"]和person[kol]["0"]是"今天"范围，
可与顶部today总结同源(today是综合，consensus["0"]可相同或略简，person[kol]["0"]是每人今天)。
DeepSeek 便宜，26 段几分钱。必须全部预生成，前端切时间窗直接读对应窗，不能实时调 LLM。

### 总结生成 prompt 要点（关键：必须带能力圈！）
把对应范围的结构化数据(direction/ticker/bottleneck/rebuts + R12 flag)喂 LLM，
并在 prompt 带上每人能力圈(强项/盲区)，要求：
1. 优先讲有方向(long/short)的表态 + 卡点焦点，过滤闲聊/neutral
2. 多人共同提的卡点=共识信号，点出来
3. 有人在盲区发言(zephyr看空/austin看空)→必须标注"注意是其盲区/看空历史全错，仅参考"
4. R12 过滤：is_retrospective/is_disclosure 不算"当下新表态"
5. today 按重要性组织(共识卡点、非共识反驳优先)，不按人流水账
6. 严格 ≤100 字，中文，客观

建议做成 intel_gen_summaries.py，cron 里在 build_dashboard 之前跑，
存 summaries.json 或 DB，build_dashboard 读它注入 __SUMMARIES__。

---

## 另外三块数据（不变）

### ① DATA(__RECORDS__) — extractions JOIN raw_posts，最近1年有效判断
字段：post_id, kol(source_id去tw_前缀), source_id, published_at, direction,
ticker[](★json.loads), company[](★json.loads), bottleneck|null, attribution,
rebuts(rebuts_narrative)|null, summary(summary_100),
is_retro, is_disc, is_selfret, raw_text, raw_url(拼 x.com/handle/status/post_id)
★ ticker/company 在 DB 是 JSON 字符串，必须 json.loads 成数组。

### ② KOLS(__KOLS__) — 人物卡，写死。见 build_dashboard.py 的 KOLS 常量。type: signal|cognition

### ③ TICKERS(__TICKERS__) — 标的，接金融数据库
每个(kol,ticker)最近一次有效喊单(排除 is_retrospective/is_disclosure)：
ticker, kol, direction, called_at,
call_price(★金融数据库 喊单当日收盘), now_price(★现价),
raw_pct(=(now-call)/call*100), excess_pct(=raw-板块ETF同期), in_field(bottleneck是否在strong里)
"现在还有空间?"列 UI 已留占位(显示"待判断序列·M3")，这列不用现在做，等模块3。

---

## dashboard 结构（最终顺序，不要改）
01 今日总结  ← __SUMMARIES__.today（hero）
02 近期态度  ← 时间窗 1D/1M/3M/6M/1Y
   ├ 近期四人共识 ← consensus[win]
   └ 每人：单人总结 ← person[kol][win] + 该人方向表态条目(DATA filter)
03 今日明细  ← DATA 当天，时间线，可展开/收起
04 标的追踪  ← TICKERS
05 追踪对象  ← KOLS（人物卡，最底）

## 接入步骤
1. 看 dashboard.template.html（4个占位符）
2. intel_gen_summaries.py：生成21段总结(带能力圈prompt) → summaries.json/DB
3. build_dashboard.py：query_extractions→DATA、KOLS常量、query_tickers(金融数据库)→TICKERS、
   读summaries→SUMMARIES，4处replace写出 dashboard.html
4. 接进 daily cron(push前)：模块1→模块2→gen_summaries→build_dashboard→自检→gzip→push

## 不要做
- 改 dashboard 的 style/布局/配色/JS/区块顺序
- 做"现在还有空间"那列（留占位等M3）
- 全量13000条塞进DATA（只放最近1年有效判断）
- 忘记 ticker/company json.loads
- 总结生成漏掉能力圈（否则平等对待所有人，失去"该信谁"的判断）

## 验证
浏览器打开 dashboard.html：① 今日总结hero有文字 ② 切1D/1M/3M/6M/1Y时
共识+每人单人总结+条目全部跟着变 ③ 明细可展开收起 ④ 标的绝对/超额分列 ⑤ 人物卡在最底
