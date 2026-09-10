#!/usr/bin/env python3
"""Render the frozen replay, keeping rejected examples separate from selections."""
import gzip
import hashlib
import html
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/focus_backtest_20260910'
esc=lambda x:html.escape(str(x))
def pct(x):return '未成熟 / 缺价格' if x is None else f'{x*100:+.1f}%'
def pp(x):return '—' if x is None else f'{x*100:+.1f} pp'

def build():
    r=json.load(gzip.open(OUT/'backtest.json.gz','rt'))
    windows=[w for w in r['windows'] if w['mode']=='frozen_quarter']
    cases=[a for w in windows for a in w['decisions'] if a['control_eligible']]
    assert len(cases)==6 and sum(w['first_long_candidates'] for w in windows)==467
    assert all(not w['groups']['actionable_combined']['60']['signals'] for w in r['windows'])
    quarter_rows=''.join(f"<tr><td>{w['start']} 至 {w['end_exclusive']} 前</td><td>{w['first_long_candidates']}</td><td>{sum(bool(a['profile']) for a in w['decisions'])}</td><td>0 / 0</td><td>不适用</td></tr>" for w in windows)
    case_rows=''
    details=''
    for a in cases:
        out=a['outcomes']; p=a['profile']
        ret=lambda n:out.get(str(n),{}).get('direction_return')
        excess=out.get('60',{}).get('excess',{}).get('SOXX')
        case_rows+=f"<tr><td>{esc(a['author'])} · {esc(a['ticker'])}</td><td>{a['published_at'][:10]}</td><td>{p['n']}</td><td>{pct(ret(20))}</td><td>{pct(ret(60))}</td><td>{pp(excess)}</td><td>{pct(ret(120))}</td></tr>"
        details+=f"<details><summary>{esc(a['author'])} · {esc(a['ticker'])} · {a['published_at'][:10]}：原帖与筛选理由</summary><p>季度训练截止 {a['training_cutoff'][:10]}；领域 {esc(p['domain_label'])}，目标期限 {p['horizon']} 个交易日；历史成熟标的 {p['n']} 个。</p><p>{esc('；'.join(a['issues']))}</p><blockquote>{esc(a['raw_text'])}</blockquote><p><a href='{esc(a['raw_url'])}'>查看 X 原帖</a></p></details>"
    body=f'''<article class="replay-report">
<p class="eyebrow">SIGNALBOARD · 历史回放 · 2026-09-10</p>
<h1>这套规则还没有证明能选出可买的新标的</h1>
<p class="lead">冻结四个季度节点后，467 条首次多头候选中，33 条匹配作者预设领域，<strong>0 条达到重点关注或领域观察门槛</strong>。改为每次发帖前滚动更新历史证据，结果仍为 0。当前没有可估计的策略命中率或收益优势。</p>
<p>本轮保留原 v1 门槛，没有看完涨跌后调参。新增付费抓取及模型调用为 <strong>$0</strong>；复用已存帖子、DS 解读和价格记录。</p>
<h2>把时间拨回去，实际会选出什么？</h2>
<div class="table-wrap"><table class="table"><thead><tr><th>验证期间</th><th>首次多头候选</th><th>领域匹配</th><th>重点 / 观察</th><th>选中信号收益</th></tr></thead><tbody>{quarter_rows}</tbody></table></div>
<p>“没有选中”不等于收益 0%：没有交易样本，也没有定义现金账户收益。候选指已存历史中该作者首次对该证券给出有效方向且方向为多头；不声称全 X 历史首发。</p>
<h2>被历史证据门槛挡住的 6 条，后来怎样？</h2>
<p><strong>以下全部是未入选的诊断对照，不是这套策略的成交或业绩。</strong>它们通过领域、语义及其他检查，只剩历史样本或表现门槛未通过。6 条仅来自 3 篇帖子、5 个不同标的；DRAM 被两位作者分别提及。</p>
<div class="table-wrap"><table class="table"><thead><tr><th>作者 / 标的</th><th>发帖日</th><th>此前成熟标的</th><th>20 日</th><th>60 日</th><th>60 日超额 / SOXX</th><th>120 日</th></tr></thead><tbody>{case_rows}</tbody></table></div>
<p>例如，Serenity 同一帖中的 DRAM 在 60 日后上涨 105.6%，FN 却下跌 18.3%。单看赢家会误判作者的可复制能力。2026 年 4 月这批光通信候选预设期限为 120 日，截至价格截止日尚未成熟；60 日只是辅助观察。</p>
<h2>回跑暴露了两个需要先修的问题</h2>
<ol><li><strong>存储重点提醒的门槛在当前池内不可达。</strong>美股主检验池只有 MU、SNDK、WDC、STX、DRAM 五个标的；新标的必须排除自身，却又要求此前验证五个不同标的。该领域最多只剩四个可训练标的。其他市场的证券当前不能充当美股验证样本。</li>
<li><strong>整帖关键词会误挡观点。</strong>产业分析里的 if、产能售罄 sold out，可能触发条件单或卖出语义；invested in 等持仓表达也可能漏识别。必须区分“买入条件”“经营条件”“产能售罄”“卖出仓位”，再验证新的提取规则。</li></ol>
<p>下一版建议：领域内首次明确看好先给“发现提醒”，历史证据决定研究优先级；样本不足单列，不显示虚构胜率。语义规则先在不看后续价格的标注集上验证，再冻结阈值做新一轮验证。以上是后续方案，本报告没有用它重选赢家。</p>
<h2>如何防止偷看未来</h2>
<ul><li>主检验分别冻结 2025-10-01、2026-01-01、2026-04-01、2026-07-01 的作者画像，观察下一段首次喊单；滚动版本只用发帖前证据。</li>
<li>每位作者每标的只取最早多头训练记录；候选本身排除。训练结果必须在节点前完整到期，退出日收盘按次日 UTC 才可用。未来收益在筛选完成后才附加。</li>
<li>入场为帖子发布之后的第一次常规开盘，盘中发帖使用下个交易日；第 20 / 60 / 120 个交易日收盘退出，入场日计第 1 日。只计算截至 2026-09-09 已成熟的窗口。</li>
<li>回报不计股息、费用、滑点或仓位；超额为同窗口标的回报减 SOXX 回报。不同作者、同一帖子及持有区间存在相关性，均值不是账户盈亏。</li></ul>
<p><strong>这仍是事后历史回放，不是真正盲测。</strong>作者名单、领域和期限来自本次复评；帖子抓取与解读也发生在后来。系统最早抓取记录为 {esc(r['actual_capture_start'])}，没有这些历史节点的实际系统快照。回放假设当时已及时获得并审核公开帖子；缺失及删除帖子、价格缺口仍会影响结果。</p>
<h2>逐条核查</h2>{details}
<p><a href="https://github.com/srtvswho/x-/blob/master/outputs/kol_reaudit_20260910/report.md">八位作者复评</a> · <a href="https://github.com/srtvswho/x-/tree/master/outputs/focus_backtest_20260910">冻结输入、逐条结果与复算说明</a> · <a href="/">返回重点关注</a></p>
</article>'''
    css='body{margin:0;background:#f6f5f0;color:#202924;font:16px/1.75 system-ui,sans-serif}article{max-width:1120px;margin:auto;padding:40px 24px}h1{font-size:34px;line-height:1.3}h2{margin-top:40px;font-size:23px}.lead{font-size:20px}.eyebrow{color:#527467;font-size:13px;letter-spacing:.08em}.table-wrap{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:12px;text-align:left;border-bottom:1px solid #d8ded7;white-space:nowrap}th{background:#e8eee7}a{color:#245f4c}blockquote{white-space:pre-wrap;overflow-wrap:anywhere;border-left:3px solid #91a393;padding:12px 20px;margin:16px 0;background:#fff}details{border-bottom:1px solid #d8ded7;padding:16px 0}summary{cursor:pointer;font-weight:600}li{margin:10px 0}@media(max-width:600px){h1{font-size:27px}article{padding:24px 16px}}'
    (OUT/'report.html').write_text('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>新标的历史回放 · SignalBoard</title><style>'+css+'</style></head><body>'+body+'</body></html>')
    (OUT/'summary.json').write_text(json.dumps({'as_of':r['as_of'],'version':r['version'],'html':body},ensure_ascii=False))
    assets=['policy_evidence.json.gz','replay_context.json.gz','backtest.json.gz','report.html','summary.json']
    manifest={name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in assets}
    manifest['../kol_reaudit_20260910/scored_events.json.gz']=hashlib.sha256((OUT.parent/'kol_reaudit_20260910/scored_events.json.gz').read_bytes()).hexdigest()
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print('Rendered frozen replay: 467 candidates, 0 selected; 6 rejected diagnostic cases')

if __name__=='__main__':build()
