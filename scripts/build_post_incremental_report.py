#!/usr/bin/env python3
"""Render the full diagnostic result without promoting it to live confidence."""
import gzip
import hashlib
import html
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.backtest_post_incremental_value import OUT, ROOT, AUTHORS, DOMAINS

def pct(v):return '—' if v is None else f'{v*100:+.1f}%'
def pp(v):return '—' if v is None else f'{v*100:+.1f} pp'
def rate(v):return '—' if v is None else f'{v*100:.1f}%'
def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']
                     +['| '+' | '.join(str(v) for v in row)+' |'for row in rows])

def build():
    r=json.load(gzip.open(OUT/'results.json.gz','rt'))
    validation=json.loads((OUT/'validation.json').read_text())
    f=r['modes']['frozen_quarter'];rolling=r['modes']['rolling_at_post']
    g=f['groups'];rg=rolling['groups']
    bits=['# 看这些 Post 有没有增量价值？修正后的历史回放',
      '**结论：本次诊断回放中，预设领域内的新标的观点表现较好；把所有作者的所有喊单混在一起，并没有表现出相对大盘的优势。按过去成绩再筛作者，结果仍依赖评分更新频率，尚不能认定有稳定的额外选股优势。**',
      '价格截止：2026-09-09。主要检验：2025-10-01 至 2026-09-10 前，60 个交易日；20/120 日为敏感性比较。v2 在看到 v1 问题之后制定，是诊断性回放，不是盲测或真实账户收益。作者和领域也来自事后复评，不能把漂亮历史数据直接转成买入置信度。',
      '## 1. 现在终于能回答什么',
      table(['样本组','成熟信号 / 原帖','60 日中位涨跌','中位超额','跑赢基准比例'],[
        ['全部作者的首次看多',f"{g['all_first_us']['60']['n']} / {g['all_first_us']['60']['posts']}",pct(g['all_first_us']['60']['return_median']),pp(g['all_first_us']['60']['excess_median'])+' / SPY',rate(g['all_first_us']['60']['benchmark_beat'])],
        ['预设领域内、原帖复核通过',f"{g['field_discovery']['60']['n']} / {g['field_discovery']['60']['posts']}",pct(g['field_discovery']['60']['return_median']),pp(g['field_discovery']['60']['excess_median'])+' / SOXX',rate(g['field_discovery']['60']['benchmark_beat'])],
        ['季度节点：此前领域成绩达标',f"{g['field_positive']['60']['n']} / {g['field_positive']['60']['posts']}",pct(g['field_positive']['60']['return_median']),pp(g['field_positive']['60']['excess_median'])+' / SOXX',rate(g['field_positive']['60']['benchmark_beat'])],
        ['逐帖更新：此前领域成绩达标（敏感性）',f"{rg['field_positive']['60']['n']} / {rg['field_positive']['60']['posts']}",pct(rg['field_positive']['60']['return_median']),pp(rg['field_positive']['60']['excess_median'])+' / SOXX',rate(rg['field_positive']['60']['benchmark_beat'])],
      ]),
      '第一行与其余各行基准、股票和发帖日期组成不同，不能把两行数字直接相减称为“筛选带来的收益”。这些是逐条事件的中位数，不是可执行组合的累计收益。',
      '**对你的问题：这些帖子不应一概判为没用。领域内观点有值得继续验证的发现价值；但“作者过去好，所以他下一条更值得买”仍未稳定成立。** 季度固定画像选出的 8 条，中位 SOXX 超额为 +22.7 pp，低于同一领域发现集合的 +42.1 pp；逐帖更新则较好。两组有交集且发生时间不同，这还不是因果结论。',
      '## 2. 为什么上一轮是 0，这次有样本',
      '上一轮把“值得发现”和“已有充分历史证明”绑在一起，还对已审核帖子追加整帖关键词否决。本轮分开：明确观点进入发现集合；证据不足保留为未知；过去成绩只决定研究分组。',
      '逐条读了预设作者领域内的 48 条首次看多记录（含训练期、非美股），阅读输出不含后续收益。明确的 long、持仓、估值或组合推荐不再因同一帖的 if、would、sold out 被整帖误挡。四条仍隔离：GFS 条件买入、STX 财报转述/泛行业态度、DGretta 对 MU 空头的嘲讽、AEVA 潜在经营利好。对未复核的其余广义基线，沿用冻结审核标签，仍有语义误差风险。',
      '精确对照 v1：仅修复语义，保留旧期限、旧样本门槛和其余限制，四个节点仍全部为 0。因此新结果不是“仅修一个词就成功”：v2 同时把主检验统一为 60 日，并采用至少 2 个不同标的、2 篇不同帖子、历史 SOXX 中位超额为正且跑赢比例至少 60% 的研究分组。它不是高置信买入信号。',
      '保留旧“supported”样本条件、但统一 60 日的敏感性结果：季度固定模式只有 2 条成熟样本、来自 1 篇原帖，中位 SOXX 超额 −36.0 pp；逐帖模式只有 3 条、中位 +3.0 pp。提高门槛并没有在这份小样本里稳定改善后续表现。',
      '## 3. 样本数逐层对账',
      table(['步骤','数量','解释'],[
        ['原 v1 首次看多候选',467,'所有市场'],
        ['解除错误的整帖礼物否决后',468,'新增 Tradex/DELL；原文虽然谈礼物，最后明确写 Long $DELL'],
        ['可归入美股及指定股票 ETF',360,'另外 108 条为其他市场、证券身份或市场资料未解决'],
        ['全部组 60 日完整成熟',296,'64 条未成熟或该窗口数据缺失；不按零收益填充'],
        ['预设作者领域匹配',33,'其中 4 条非美股，4 条原帖复核后隔离'],
        ['领域发现集合',25,'无历史表现门槛'],
        ['领域集合 60 日完整成熟',23,'AOSL、POWI 未满 60 个交易日'],
        ['季度固定：历史成绩达标',10,'8 条 60 日成熟；2 条未成熟'],
        ['逐帖更新：历史成绩达标',14,'12 条 60 日成熟；2 条未成熟'],
      ]),
      '首次的含义始终是“已存审核记录中，作者对该证券的第一次有效方向观点”；若第一次是看空，以后转多不作为新标的。价格缺失不能用后来价格齐全的一条替代；隔离的首次观点也没有偷偷替换为后来的赢家。',
      '## 4. 逐季度看，优势没有一直同样强',
      table(['节点后观察期','领域集合 n / 中位 SOXX 超额','季度固定达标 n / 中位超额','逐帖达标 n / 中位超额'],[
        [w,
         str(v['field_discovery']['n'])+' / '+pp(v['field_discovery']['excess_median']),
         str(v['field_positive']['n'])+' / '+pp(v['field_positive']['excess_median']),
         str(rolling['windows'][w]['field_positive']['n'])+' / '+pp(rolling['windows'][w]['field_positive']['excess_median'])]
        for w,v in f['windows'].items()]),
      'Q4 2025 的 4 条逐帖达标记录，都是 Serenity 的 LITE、COHR、AAOI、AXTI。10 月 1 日冻结画像时，其更早观点尚未完成 60 日观察；12 月发帖时已经成熟。因此两种更新方式产生差异有时间上的原因，不能只挑结果好的一种报告。2026 年 7 月后的记录尚无成熟 60 日结果，不能宣称跨四个完整季度验证成功。',
      '## 5. 比较同行后，能给作者的功劳要收敛',
      table(['集合','60 日中位超额 / SOXX','60 日中位超额 / 同领域篮子','120 日中位超额 / 同领域篮子'],[
        ['领域全部发现',pp(g['field_discovery']['60']['excess_median']),pp(g['field_discovery']['60']['peer_excess_median']),pp(g['field_discovery']['120']['peer_excess_median'])],
        ['季度固定达标',pp(g['field_positive']['60']['excess_median']),pp(g['field_positive']['60']['peer_excess_median']),pp(g['field_positive']['120']['peer_excess_median'])],
        ['逐帖达标',pp(rg['field_positive']['60']['excess_median']),pp(rg['field_positive']['60']['peer_excess_median']),pp(rg['field_positive']['120']['peer_excess_median'])],
      ]),
      '同领域篮子在每条信号的相同入场和退出日计算，排除该信号本身，至少需要两个其他标的有价格。篮子沿用当前定义，存在事后股票池和存续偏差，而且“光通信链”含相关半导体供应商，不是严格纯行业指数；因此仅作诊断。领域发现集合的 60 日超额从相对 SOXX 的 +42.1 pp 收敛至相对同行的 +6.8 pp，120 日相对同行为 −14.0 pp，提示相当一部分漂亮结果与主题行情有关。',
      '进一步把“历史成绩达标”与同季度、同领域的未达标候选比较，只有 3 条达标记录能找到成熟对照。相对对照均值的差值中位数为 −3.7 pp。样本过小，既不能证明权重有效，也不能反过来证明没有价值。',
      '## 6. 各作者本轮可看到的增量',
      table(['作者','领域内成熟新标的','60 日中位 SOXX 超额','季度固定达标成熟数'],[
        [AUTHORS[s][0],a['field_discovery']['n'],pp(a['field_discovery']['excess_median']),a['field_positive']['n']]
        for s,a in f['authors'].items()]),
      'Serenity 占季度固定达标成熟样本的 6/8、逐帖模式的 10/12；不能把结果外推成八位作者都有效。Feroce、Tradex、Zephyr 的样本也太少，暂不把它们转成可靠胜率。gsmferrari 没有预设验证领域，领域表中的 0 不代表其全部帖子无效。',
      'Jukan 在本轮 10 月以后只剩 AMD、NVDA 两条新标的，60 日相对 SOXX 表现较弱；他的早期 MU、SNDK 已在 9 月出现，因此不会重复算作 10 月以后的新机会。DGretta 的早期 SNDK 同理。',
      '## 7. 早期发现：单列描述，不冒充后续验证',
      table(['作者 / 标的','首次观点日','60 日价格回报','60 日 SOXX 超额','120 日价格回报'],[
        [AUTHORS[c['source_id']][0]+' / '+c['ticker'],c['published_at'][:10],pct(c['outcomes'].get('60',{}).get('direction_return')),
         pp(c['outcomes'].get('60',{}).get('excess',{}).get('SOXX')),pct(c['outcomes'].get('120',{}).get('direction_return'))]
        for c in r['early_rows']]),
      '这 14 条早期领域观点的 60 日中位 SOXX 超额为 +13.3 pp，但相对同领域篮子的中位超额约为 0。这支持保留“捕捉主题”的可能价值，不能由此认定作者拥有跨周期独立选股能力。',
      '## 8. 风险、期限与复核',
      table(['集合','20 日 n / 中位 SOXX 超额','60 日 n / 中位 SOXX 超额','120 日 n / 中位 SOXX 超额'],[
        [name,*[str(source[key][str(h)]['n'])+' / '+pp(source[key][str(h)]['excess_median']) for h in [20,60,120]]]
        for name,source,key in [('领域发现',g,'field_discovery'),('季度固定达标',g,'field_positive'),('逐帖达标',rg,'field_positive')]]),
      '各期限成熟样本不同，不可把三列当成同一个组合持有更久的轨迹。季度固定达标的 8 条成熟 60 日记录中，有 2 条期间收盘相对入场价曾跌逾 20%；逐帖模式为 3/12。正的期末收益不等于低风险，未模拟止损或实际进出场。',
      f"技术验证通过：{validation['temporal_poison_checks']} 次未来结果污染测试、{validation['independent_entry_checks']} 次开盘入场核验、{validation['independent_return_and_benchmark_checks']} 次从原始缓存重算收益及 SPY/SOXX 对照。筛选文件先落盘且不含候选未来收益；训练只采用截止日前已经完整成熟的结果，排除候选自身。新增付费调用为 0。",
      '**当前可用的产品结论：保留领域内首次明确看好的发现提醒；旁边展示原帖、历史样本数、截止日和成熟表现。不要把历史证据不足等同于“不提醒”，也不要把本次 75%/83.3% 的回放比例显示成下一条标的的上涨概率。** 本轮只交付验证结果，生产提醒规则尚未改成 v2。',
      '## 9. 逐条检查季度固定达标的全部记录',
      table(['作者 / 标的','发帖日','当时成熟标的 / 原帖','60 日涨跌','SOXX 超额','原帖'],[
        [AUTHORS[c['source_id']][0]+' / '+c['ticker'],c['published_at'][:10],str(c['profile']['n'])+' / '+str(c['profile']['posts']),
         pct(c['outcomes'].get('60',{}).get('direction_return')),pp(c['outcomes'].get('60',{}).get('excess',{}).get('SOXX')),
         '[查看]('+c['raw_url']+')']for c in r['decisions'] if c['mode']=='frozen_quarter' and (c['profile']or{}).get('classification')=='positive']),
      '全部 720 条模式/候选记录、逐条训练证据、语义审核、冻结方法与 SHA-256 清单均随报告保存。results.json.gz 是完整证据，decisions.csv 便于筛选；protocol.json 是本次运行前固定的方法。',
    ]
    md='\n\n'.join(bits)+'\n'
    (OUT/'report.md').write_text(md)
    # Small deterministic renderer for this report's deliberately limited Markdown.
    import re
    def inline(s):
        s=html.escape(s)
        s=re.sub(r'\[([^]]+)\]\((https://[^)]+)\)',r'<a href="\2" target="_blank" rel="noopener">\1</a>',s)
        return re.sub(r'\*\*(.*?)\*\*',r'<strong>\1</strong>',s)
    body=[]
    for block in bits:
        if block.startswith('# '):body.append('<h1>'+inline(block[2:])+'</h1>')
        elif block.startswith('## '):body.append('<h2>'+inline(block[3:])+'</h2>')
        elif block.startswith('| '):
            lines=block.splitlines();head=[x.strip()for x in lines[0].strip('|').split('|')]
            rows=[[x.strip()for x in line.strip('|').split('|')]for line in lines[2:]]
            body.append('<div class="table"><table><thead><tr>'+''.join('<th>'+inline(x)+'</th>'for x in head)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+inline(x)+'</td>'for x in row)+'</tr>'for row in rows)+'</tbody></table></div>')
        else:body.append('<p>'+inline(block)+'</p>')
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SignalBoard · Post 增量价值回放</title><style>
body{margin:0;background:#f4f5f2;color:#172c31;font:16px/1.8 system-ui,-apple-system,"PingFang SC",sans-serif}main{max-width:1080px;margin:auto;padding:42px 24px 90px}h1{font-size:clamp(27px,4vw,40px);line-height:1.35}h2{font-size:23px;margin:48px 0 16px;border-top:1px solid #ccd5d2;padding-top:24px}p{max-width:960px}strong{color:#174e4a}a{color:#086b71}.table{overflow-x:auto;background:white;border:1px solid #d6dedb;border-radius:8px}table{border-collapse:collapse;width:100%;font-size:14px;white-space:normal}th,td{padding:12px 14px;text-align:left;border-bottom:1px solid #e3e9e6;min-width:80px}th{background:#e9efeb}td:first-child{min-width:140px}nav{font-size:13px;color:#54716a;letter-spacing:.08em}@media(max-width:600px){main{padding:24px 16px}table{min-width:650px}h2{font-size:21px}}
</style><main><nav>SIGNALBOARD · 历史验证 · 2026-09-10</nav>'''+''.join(body)+'</main></html>'
    (OUT/'report.html').write_text(page)
    (OUT/'README.md').write_text('''# Post incremental value replay\n\nStart with report.md or report.html. This is a diagnostic policy revision, not a live policy or blind backtest.\n\nReplay from the repository root (Python standard library; no paid calls):\n\n```sh\npython scripts/backtest_post_incremental_value.py run\npython scripts/build_post_incremental_report.py\n```\n\nDo not rerun `freeze`: protocol.json is already frozen. Inputs are the existing scored_events.json.gz, original v1 backtest, and adjacent peer_prices.json.gz. All current candidate future outcomes are attached only after decisions_before_outcomes.json.gz is persisted.\n\n`validate_post_incremental_value.py` additionally rechecks OHLC caches in outputs/kol_reaudit_20260910/prices; those full original quote caches are in the prior audit attachment, not duplicated here. validation.json records that completed check. The smaller peer-price archive makes the report replay standalone within this repository.\n\nCSV values are decimal returns, not percentages. Results are event studies, not portfolio P&L. No production recommendation thresholds are changed.\n''')
    files=[p for p in OUT.iterdir() if p.is_file() and p.name!='manifest.json']
    manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(files)}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print('Wrote',OUT/'report.html')
if __name__=='__main__':build()
