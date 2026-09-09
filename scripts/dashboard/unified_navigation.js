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
route = async function() {
  setFreshness();
  const s=location.pathname.split('/').filter(Boolean).map(decodeURIComponent),q=new URLSearchParams(location.search);
  const aliases={'#ai-cost':'/ai-usage/','#market':'/','#tracking':'/tracking/','#feed-section':'/posts/','#people':'/posts/'};
  if(aliases[location.hash])return location.replace(aliases[location.hash]);
  if(location.hash.startsWith('#clue/'))return location.replace('/clues/'+location.hash.slice(6));
  try {
    if(!s.length||s[0]==='market'||s[0]==='legacy')return await panels('market');
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
