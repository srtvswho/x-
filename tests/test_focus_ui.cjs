/* Execute the actual focus renderer with the built data, no browser/network. */
const fs=require('node:fs'),vm=require('node:vm'),zlib=require('node:zlib'),assert=require('node:assert/strict');
const data=JSON.parse(zlib.gunzipSync(fs.readFileSync('dashboard_deploy_dist/data/focus-signals.json.gz')));
const source=fs.readFileSync('scripts/dashboard/unified_navigation.js','utf8');
const snippet=source.slice(source.indexOf('const focusPriority ='),source.indexOf('route = async function()'));
const app={innerHTML:''},readButtons=[],storage=new Map();
const escape=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const ctx=vm.createContext({app,URLSearchParams,console,
  location:{search:''},nav:()=>{},document:{querySelectorAll:()=>readButtons},
  readData:async path=>path.includes('post-incremental')?JSON.parse(zlib.gunzipSync(fs.readFileSync('dashboard_deploy_dist/data/post-incremental-summary.json.gz'))):path.includes('backtest')?JSON.parse(zlib.gunzipSync(fs.readFileSync('dashboard_deploy_dist/data/focus-backtest.json.gz'))):data,esc:escape,fmtDate:x=>x,list:a=>'<ul>'+a.map(x=>'<li>'+escape(x)+'</li>').join('')+'</ul>',
  localStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v)}});
vm.runInContext(snippet,ctx);
(async()=>{
  await vm.runInContext('focusHome()',ctx);
  assert(app.innerHTML.includes('可信作者的新标的'));
  assert(app.innerHTML.includes('作者能力领域与提醒门槛'));
  const labels=data.research_labels;
  const recent=labels.alerts.filter(a=>a.recent&&!a.backfill&&!a.withdrawn&&a.tags.length);
  assert.equal((app.innerHTML.match(/class="card research-card/g)||[]).length,recent.length);
  assert(app.innerHTML.includes('领域内新观点')&&app.innerHTML.includes('季度历史达标')&&app.innerHTML.includes('发帖前历史达标'));
  ctx.location.search='?scope=history&label=quarter_supported';
  await vm.runInContext('focusHome()',ctx);
  assert.equal((app.innerHTML.match(/class="card research-card/g)||[]).length,labels.alerts.filter(a=>a.tags.includes('quarter_supported')).length);
  const example=structuredClone(data.alerts[0]||{id:'fixture',priority:'review',author:'Test',ticker:'TEST',
    post_id:'fixture',published_at:'2026-09-10',evaluated_at:'2026-09-10',history_scope:{},
    profile:null,issues:[],decision_checks:[]});
  example.author='<img src=x onerror=alert(1)>';example.raw_text='<script>alert(1)</script>';
  ctx.example=example;
  const html=vm.runInContext('focusCard(example,new Set())',ctx);
  assert(!html.includes('<script>')&&!html.includes('<img src=x'));
  assert(html.includes('&lt;script&gt;'));
  ctx.location.search='?level=priority';
  await vm.runInContext('focusHome()',ctx);
  assert(!app.innerHTML.includes('class="card focus-card review"'));
  await vm.runInContext('focusBacktest()',ctx);
  assert(app.innerHTML.includes('三个口径的历史回放')&&app.innerHTML.includes('完整方法与失败样本'));
  ctx.badgePost={id:'<bad>',research_labels:[{id:'fixture',ticker:'<img>',tags:['field_discovery','rolling_supported'],semantic_origin:'test'}]};
  const badges=vm.runInContext('researchPostBadges(badgePost)',ctx);
  assert(badges.includes('领域内新观点')&&badges.includes('发帖前历史达标')&&!badges.includes('<img>'));
  assert(!app.innerHTML.includes('<script>'));
  console.log(`PASS focus render, empty state, filter and HTML escaping: ${data.alerts.length} real candidates`);
})().catch(e=>{console.error(e);process.exit(1);});
