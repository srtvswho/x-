/* Execute the actual focus renderer with the built data, no browser/network. */
const fs=require('node:fs'),vm=require('node:vm'),zlib=require('node:zlib'),assert=require('node:assert/strict');
const data=JSON.parse(zlib.gunzipSync(fs.readFileSync('dashboard_deploy_dist/data/focus-signals.json.gz')));
const source=fs.readFileSync('scripts/dashboard/unified_navigation.js','utf8');
const snippet=source.slice(source.indexOf('const focusPriority ='),source.indexOf('route = async function()'));
const app={innerHTML:''},readButtons=[],storage=new Map();
const escape=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const ctx=vm.createContext({app,URLSearchParams,console,
  location:{search:''},nav:()=>{},document:{querySelectorAll:()=>readButtons},
  readData:async path=>path.includes('backtest')?JSON.parse(zlib.gunzipSync(fs.readFileSync('dashboard_deploy_dist/data/focus-backtest.json.gz'))):data,esc:escape,fmtDate:x=>x,list:a=>'<ul>'+a.map(x=>'<li>'+escape(x)+'</li>').join('')+'</ul>',
  localStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v)}});
vm.runInContext(snippet,ctx);
(async()=>{
  await vm.runInContext('focusHome()',ctx);
  assert(app.innerHTML.includes('可信作者的新标的'));
  assert(app.innerHTML.includes('作者能力领域与提醒门槛'));
  assert.equal(app.innerHTML.includes('目前没有达到重点关注门槛'),!(data.counts.priority||0));
  assert.equal((app.innerHTML.match(/class="card focus-card/g)||[]).length,data.alerts.length);
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
  assert(app.innerHTML.includes('467')&&app.innerHTML.includes('未入选的诊断对照'));
  assert(!app.innerHTML.includes('<script>'));
  console.log(`PASS focus render, empty state, filter and HTML escaping: ${data.alerts.length} real candidates`);
})().catch(e=>{console.error(e);process.exit(1);});
