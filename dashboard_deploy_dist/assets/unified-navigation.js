/* The only product router. Existing deep links resolve inside the same shell. */
const gzipCache = new Map();
async function readData(url) {
  if (!gzipCache.has(url)) gzipCache.set(url, (async () => {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`数据暂时无法读取（${response.status}），请刷新重试。`);
    const bytes = new Uint8Array(await response.arrayBuffer());
    const text = bytes[0] === 31 && bytes[1] === 139
      ? await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).text()
      : new TextDecoder().decode(bytes);
    return JSON.parse(text);
  })().catch(error => { gzipCache.delete(url); throw error; }));
  return gzipCache.get(url);
}
raw = async function(mode='full') {
  if (RAW && !RAW.partial) return RAW;
  const data = await readData(mode === 'recent' ? '/data/recent-posts.json.gz' : '/data/raw-intelligence.json.gz');
  if (!RAW || RAW.partial) RAW = data;
  return data;
};
const fullFeedRows = renderFeedRows;
renderFeedRows = function(rows, limit=30) {
  fullFeedRows(rows, limit);
  if (!RAW?.partial) return;
  const count = document.querySelector('.feed-count');
  if (count) count.textContent = `已展示 ${Math.min(limit, rows.length)} 条 · 最近 ${rows.length} 条已载入 · 历史共 ${RAW.total_posts.toLocaleString()} 条`;
  if (limit < rows.length) return;
  const loader = document.querySelector('.feed-load');
  loader.innerHTML += '<button class="btn" id="load-history">继续查看更早的推文</button>';
  document.getElementById('load-history').onclick = async e => {
    e.target.disabled = true; e.target.textContent = '正在读取历史推文…';
    try { const d = await raw(); renderFeedRows(filterFeed(d.posts, new URLSearchParams(location.search)), limit+30); }
    catch(error) { e.target.disabled=false; e.target.textContent='读取失败，点击重试'; }
  };
};
function setFreshness() {
  document.getElementById('updated').textContent = `数据截至 ${fmtDate(REPORT.data_until)} · 北京时间`;
}
async function panels(mode) {
  nav(mode);
  const names = {market:'市场态度',tracking:'标的追踪',usage:'AI 用量'};
  document.title = `${names[mode]} · SignalBoard`;
  app.innerHTML = '<div class="loading">正在读取最新数据…</div>';
  const [module, data] = await Promise.all([import('/assets/market-panels.js'), readData(`/data/${mode}-panels.json.gz`)]);
  app.innerHTML = '<div id="market-view"></div>';
  module.mount(document.getElementById('market-view'), mode, data);
  setFreshness();
}
let linesLoaded = false;
async function loadLines() {
  if (!linesLoaded) {
    const data = await readData('/data/research-lines.json.gz');
    CLUES.splice(0, CLUES.length, ...data.clues);
    linesLoaded = true;
  }
}
const statusName = x => ({STRENGTHENING:'证据增强',BUILDING:'形成中',NEW:'新线索',MATURE:'较成熟',WEAKENING:'证据减弱',CONTRADICTED:'出现反证'})[x] || x || '待判断';
const confidenceName = x => ({HIGH:'高',MEDIUM:'中',LOW:'低'})[x] || x || '未评估';
const eventName = x => ({THESIS_ORIGIN:'原研究起点',NEW_COMPANY:'新增公司关联',NEW_EVIDENCE:'新增证据',RELATED_POST:'相关推文 · 待研究复核',THESIS_STRENGTHENING:'观点增强',THESIS_WEAKENING:'观点减弱',CONTRADICTION:'出现分歧'})[x] || '研究节点';
const authorFeed = e => `/posts/?${e.author_key?'author='+encodeURIComponent(e.author_key):'q='+encodeURIComponent(e.author||'')}`;
function lineEvent(c,e,i) {
  const id=postId(e.post_url);
  return `<article class="event"><div class="meta"><time>${esc(fmtDate(e.date))}</time><a href="${authorFeed(e)}">${esc(e.author)}</a><span class="chip">${i===0?'已存相关记录起点':eventName(e.event_type)}</span></div><h3>${esc(e.what_changed||'相关推文')}</h3>${e.kind==='reviewed'&&e.ai_interpretation?`<p>${esc(e.ai_interpretation)}</p>`:''}<details class="event-details"><summary>查看原文</summary><p>${esc(e.post)}</p></details><div class="event-actions">${id?`<a href="/posts/${id}">完整推文与解读</a>`:''}</div></article>`;
}
function lineCard(c) {
  const events=arr(c.timeline), first=events[0], last=events.at(-1);
  return `<article class="card"><h2><a href="${clueHref(c)}" style="text-decoration:none">${esc(c.title)}</a></h2><div class="line-facts"><span>起点 <strong>${esc((c.observed_start||'').slice(0,10))}</strong> · ${esc(first?.author||'未知')}</span><span>最新相关推文 <strong>${esc((c.latest_post_at||'').slice(0,10))}</strong> · ${esc(last?.author||'未知')}</span><span>${events.length} 个节点</span></div><p class="thesis">${esc(c.one_line_thesis)}</p><div class="line-latest"><span class="label">最新相关情况</span><p>${esc(last?.what_changed||c.what_changed)}</p></div><div class="meta"><span class="status ${esc(c.status)}">上次判断：${esc(statusName(c.status))}</span><span>置信度：${esc(confidenceName(c.confidence))} · 判断截至 ${esc(c.assessment_at)}</span>${c.unreviewed_count?`<span>${c.unreviewed_count} 条后续推文待复核</span>`:''}</div><div class="timeline">${[first,...(events.length>2?[events[Math.floor(events.length/2)]]:[]),...(events.length>1?[last]:[])].filter(Boolean).map(e=>lineEvent(c,e,events.indexOf(e))).join('')}</div><div class="card-foot"><a class="btn primary" href="${clueHref(c)}">查看完整时间轴（${events.length}）</a></div></article>`;
}
allClues = async function() {
  nav('clues'); await loadLines(); document.title='全部研究线 · SignalBoard';
  const q=new URLSearchParams(location.search),query=(q.get('q')||'').trim().toLowerCase();
  const rows=CLUES.filter(c=>!query||[c.title,c.one_line_thesis,c.theme].join(' ').toLowerCase().includes(query)).sort((a,b)=>(b.latest_post_at||'').localeCompare(a.latest_post_at||''));
  app.innerHTML=`<div class="page"><div class="page-head"><h1>全部研究线</h1><p>一条研究线围绕一个问题，按时间串起不同作者的观点、证据与分歧。</p></div><form class="feed-filters" action="/research-clues/"><label class="feed-search">查找研究线<input name="q" value="${esc(query)}" placeholder="例如 NAND、封装、CPO"></label><button class="btn">查找</button></form><p class="line-start">起点仅指已保存的相关记录，不代表全网首次提出。后续相关推文不会自动改变研究判断或置信度。</p><div class="list">${rows.map(lineCard).join('')||'<div class="empty">没有匹配的研究线。</div>'}</div></div>`;
};
clueDetail = function(c) {
  nav('clues');document.title=`${c.title} · SignalBoard`;
  const events=arr(c.timeline),latest=events.at(-1),ai=c.ai_research_view||{};
  app.innerHTML=`<div class="page">${crumbs([['全部研究线','/research-clues/'],[c.title]])}<div class="page-head"><h1>${esc(c.title)}</h1><p>${esc(c.one_line_thesis)}</p><div class="line-facts"><span>已存起点 ${esc((c.observed_start||'').slice(0,10))}</span><span>最新相关推文 ${esc((c.latest_post_at||'').slice(0,10))}</span><span>${events.length} 个节点</span></div></div><section class="panel"><h2>最新相关情况</h2><p>${esc(latest?.what_changed||c.what_changed)}</p><div class="meta">${esc(latest?.author)} · ${esc(fmtDate(latest?.date))}</div></section><section class="panel"><h2>研究判断与置信度</h2><p><strong>${esc(statusName(c.status))} · 置信度 ${esc(confidenceName(c.confidence))}</strong> · 判断截至 ${esc(c.assessment_at)}</p><p>${esc(ai.overall_assessment||c.ai_initial_view||c.one_line_thesis)}</p>${c.unreviewed_count?`<p class="assessment-note">此后新增 ${c.unreviewed_count} 条相关推文，尚未完成整条研究线的复核。上述置信度属于上次判断。</p>`:''}<details><summary>判断依据与待验证问题</summary><h3>为什么重要</h3><p>${esc(c.why_this_matters)}</p><h3>逻辑与前提</h3>${list(c.full_logic_chain)}<h3>待验证问题</h3>${list(c.key_unknowns||ai.what_is_still_unknown||c.what_to_research_next)}<h3>可能的反证</h3>${list(c.disconfirming_evidence||c.risks||ai.what_may_be_wrong)}</details></section><section class="panel"><h2>完整时间轴 · 从早到晚</h2><p class="line-start">作者名可查看其推文。相关记录的时间先后不代表作者之间存在引用或因果关系。</p><div id="line-timeline" class="timeline"></div><div id="line-more"></div></section></div>`;
  let limit=40;
  const draw=()=>{
    document.getElementById('line-timeline').innerHTML=events.slice(0,limit).map((e,i)=>lineEvent(c,e,i)).join('');
    document.getElementById('line-more').innerHTML=limit<events.length?`<button class="btn timeline-more" id="more-events">继续展开（已展示 ${limit} / ${events.length}）</button>`:'';
    const more=document.getElementById('more-events');if(more)more.onclick=()=>{limit+=40;draw();};
  };draw();
};
postDetail = async function(id) {
  nav('posts'); const data=await raw(),p=data.posts.find(p=>p.id===id);
  if(!p)return notFound('未找到这条推文');
  document.title=`${p.author_name} 的推文 · SignalBoard`;
  app.innerHTML=`<div class="page">${crumbs([['推文','/posts/'],['推文详情']])}${postCard(p)}${p.links?.length?`<section class="panel"><h2>外部来源</h2>${p.links.filter(x=>/^https?:\/\//.test(x)).map(x=>`<p><a href="${esc(x)}" target="_blank" rel="noreferrer">${esc(x)}</a></p>`).join('')}</section>`:''}</div>`;
};
const focusPriority = {priority:'重点关注',field_watch:'领域观察',review:'待核实'};
const evidenceTier = {strong:'较强',supported:'有支持，样本仍少',insufficient:'证据不足'};
const focusPercent = x => x == null ? '—' : `${(x*100).toFixed(1)}%`;
const focusPP = x => x == null ? '—' : `${x>=0?'+':''}${(x*100).toFixed(1)} 个百分点`;
function focusRead(){try{return new Set(JSON.parse(localStorage.getItem('signalboard-focus-read-v1')||'[]'));}catch{return new Set();}}
function focusCard(a,read){
  const p=a.profile, label=focusPriority[a.priority],fresh=!read.has(a.id);
  return `<article class="card focus-card ${esc(a.priority)}" id="focus-${esc(a.id)}"><div class="meta"><span class="status ${a.priority==='priority'?'STRENGTHENING':'BUILDING'}">${esc(label)}</span>${fresh?'<span class="chip">未读</span>':''}<span>${esc(fmtDate(a.published_at))}</span></div><h2>${esc(a.author)} · ${esc(a.ticker)} ${a.priority==='review'?'新标的候选':'首次看好'}</h2><p class="focus-note">已存历史内首次明确方向 · ${a.backfill?'历史补录':'近 '+7+' 天发布'} · 本次复核 ${esc(fmtDate(a.evaluated_at))}</p>${p?`<div class="focus-evidence"><p><strong>${esc(p.domain_label)} · ${p.horizon} 个交易日</strong> · 历史证据${esc(evidenceTier[p.tier])}</p><p>${p.n} 个不同标的 / ${p.posts} 篇帖子 / ${p.quarters} 个季度；方向命中 ${p.wins}/${p.n}；中位超额 ${focusPP(p.median_excess)}（${esc(p.benchmark)}）</p><p class="focus-note">只使用这条帖发出之前已经成熟的结果；这不是新标的的上涨概率。</p></div>`:'<p class="assessment-note">尚未匹配该作者已验证的能力领域。</p>'}${a.issues.length?`<p class="assessment-note">${a.issues.map(esc).join('；')}</p>`:'<p>作者领域匹配、历史支持和新标的条件已通过，可以优先研究买入条件。</p>'}<details><summary>这次究竟说了什么</summary><blockquote>${esc(a.raw_text)}</blockquote><p class="focus-note">历史覆盖：${Number(a.history_scope.raw_posts||0).toLocaleString()} 篇，起于 ${esc(a.history_scope.history_start?.slice(0,10))}。全量历史覆盖尚未证明。</p></details><details><summary>买入前需要确认什么</summary><p class="focus-note">当前阶段：研究候选。估值、安全边际及退出条件尚未核实。</p>${list(a.decision_checks)}</details>${p?.samples?.length?`<details><summary>核对历史样本（含失败样本）</summary><div class="table-wrap"><table class="table"><thead><tr><th>标的</th><th>原帖日期</th><th>期末方向回报</th><th>相对行业超额</th></tr></thead><tbody>${p.samples.map(e=>`<tr><td>${esc(e.ticker)}</td><td><a href="/posts/${encodeURIComponent(e.post_id)}">${esc(e.published_at.slice(0,10))}</a></td><td>${focusPercent(e.return)}</td><td>${focusPP(e.excess)}</td></tr>`).join('')}</tbody></table></div></details>`:''}<div class="focus-actions"><a class="btn primary" href="/posts/${encodeURIComponent(a.post_id)}">原帖与解读</a><a class="btn" href="/posts/?ticker=${encodeURIComponent(a.ticker)}">该标的全部推文</a>${fresh?`<button class="btn" data-focus-read="${esc(a.id)}">标为已读</button>`:'<span class="chip">已读</span>'}</div></article>`;
}
async function focusBacktest(){
  nav('focus');document.title='新标的历史回放 · SignalBoard';
  const d=await readData('/data/focus-backtest.json.gz');
  app.innerHTML=`<div class="page"><p><a class="btn" href="/">返回重点关注</a> <a class="btn" href="/reports/focus-backtest.html">打开完整报告</a></p>${d.html}</div>`;
}
async function focusHome(){
  nav('focus');document.title='重点关注 · SignalBoard';
  const d=await readData('/data/focus-signals.json.gz'),read=focusRead(),q=new URLSearchParams(location.search),filter=q.get('level')||'all';
  const rows=d.alerts.filter(a=>filter==='all'||a.priority===filter),unread=d.alerts.filter(a=>a.priority==='priority'&&!read.has(a.id)).length;
  app.innerHTML=`<div class="page"><div class="page-head"><h1>可信作者的新标的</h1><p>在擅长领域里，谁第一次明确看好一家公司？把值得研究的新观点放到买入决策之前。</p></div><p class="assessment-note">实验规则：四段历史回放共 467 条首次多头候选，尚无合格提醒，收益优势未验证。<a href="/focus/backtest/">查看回放与漏选诊断</a></p><div class="focus-counts"><a href="/?level=priority"><strong>${d.counts.priority||0}</strong>重点关注${unread?` · ${unread} 条未读`:''}</a><a href="/?level=field_watch"><strong>${d.counts.field_watch||0}</strong>领域观察</a><a href="/?level=review"><strong>${d.counts.review||0}</strong>待核实</a><a href="/">查看全部</a></div>${d.evidence_stale?'<p class="assessment-note">历史表现基准已过期或缺失，本轮停止生成高优先级提醒，等待证据刷新。</p>':''}<p class="focus-note">近 ${d.recent_days} 天新发帖；历史价格截至 ${esc(d.evidence_prices_as_of||'缺失')}。旧帖补录、反讽、条件单及重复标的不会直接变成重点提醒。</p>${!d.counts.priority?'<section class="panel"><h2>目前没有达到重点关注门槛的新标的</h2><p>这不代表作者没有发帖。重复喊单、跨领域及证据不足的观点继续保留在推文或待核实区。</p></section>':''}<div class="list">${rows.map(a=>focusCard(a,read)).join('')||'<div class="empty">这个分类暂时没有新提醒。</div>'}</div><details class="panel" style="margin-top:24px"><summary>作者能力领域与提醒门槛</summary><p class="focus-note">证据等级是研究优先级，尚未校准为买入胜率。领域与持有期来自本次复评；历史样本尚不构成前瞻验证。</p><p>${esc(d.policy.strong)}</p><p>领域观察：${esc(d.policy.supported)}</p><div class="focus-profile-grid">${d.profiles.map(p=>`<section class="panel"><h3>${esc(p.author)} · ${esc(p.domain_label)}</h3><p>${p.horizon} 日 · ${esc(evidenceTier[p.tier])}</p><p>${p.n} 标的 / ${p.posts} 帖子；中位行业超额 ${focusPP(p.median_excess)}</p></section>`).join('')}</div></details></div>`;
  document.querySelectorAll('[data-focus-read]').forEach(button=>button.onclick=()=>{const ids=focusRead();ids.add(button.dataset.focusRead);try{localStorage.setItem('signalboard-focus-read-v1',JSON.stringify([...ids].slice(-2000)));button.disabled=true;button.textContent='已读';}catch{button.textContent='此浏览器暂时无法保存已读状态';}});
}
route = async function() {
  setFreshness();
  const s=location.pathname.split('/').filter(Boolean).map(decodeURIComponent),q=new URLSearchParams(location.search);
  const aliases={'#ai-cost':'/ai-usage/','#market':'/market/','#tracking':'/tracking/','#feed-section':'/posts/','#people':'/posts/'};
  if(aliases[location.hash])return location.replace(aliases[location.hash]);
  if(location.hash.startsWith('#clue/'))return location.replace('/clues/'+location.hash.slice(6));
  try {
    if(s[0]==='focus'&&s[1]==='backtest')return await focusBacktest();
    if(!s.length||s[0]==='focus')return await focusHome();
    if(s[0]==='market'||s[0]==='legacy')return await panels('market');
    if(s[0]==='tracking'||(s[0]==='tickers'&&!s[1])||s[0]==='companies')return await panels('tracking');
    if(s[0]==='ai-usage'||s[0]==='admin')return await panels('usage');
    if(s[0]==='posts')return s[1]?await postDetail(s[1]):await rawFeed();
    if(s[0]==='authors')return location.replace('/posts/'+(s[1]?'?author='+encodeURIComponent(authorKey(s[1])):''));
    if(s[0]==='themes')return location.replace('/posts/'+(s[1]?'?theme='+encodeURIComponent(s.slice(1).join('/')):''));
    if(s[0]==='tickers')return location.replace('/posts/?ticker='+encodeURIComponent(s[1]));
    if(s[0]==='research-clues'||s[0]==='research-changes')return await allClues();
    if(s[0]==='clues'||s[0]==='evidence') {
      await loadLines();const c=clueById(s[1]);if(!c)return await allClues();
      return clueDetail(c);
    }
    notFound('页面不存在');
  }catch(error){console.error(error);app.innerHTML=`<div class="page"><div class="error">${esc(error.message)} <button class="btn" onclick="location.reload()">重试</button></div></div>`;}
};
route();
