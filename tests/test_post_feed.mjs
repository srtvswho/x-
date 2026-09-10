import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const template=readFileSync(new URL('../scripts/dashboard/research_clue_preview.template.html',import.meta.url),'utf8');
const script=template.split('<script>')[1].split('</script>')[0].replace(/\s+route\(\);\s*$/,'');
const root={innerHTML:'',querySelectorAll:()=>[]};
const context=vm.createContext({URLSearchParams,Intl,document:{getElementById:id=>id==='clue-data'?{textContent:'{"clues":[]}'}:root}});
vm.runInContext(script,context);
const run=code=>vm.runInContext(code,context);
run(`var sample=[
 {id:'1',author:'jukan',date:'2026-09-07T15:59:59Z',text:'original',summary:'存储价格',tickers:['MU'],themes:[]},
 {id:'2',author:'serenity',date:'2026-09-07T16:00:00Z',text:'second',summary:'',tickers:['TSM'],themes:[]},
 {id:'3',author:'jukan',date:'2026-09-08T02:00:00+09:00',text:'third',summary:'memory',tickers:['MU'],themes:[]}
];`);

test('chronology compares instants and filters the same Beijing date shown on cards',()=>{
 assert.equal(run("filterFeed(sample,new URLSearchParams()).map(p=>p.id).join(',')"),'3,2,1');
 assert.equal(run("filterFeed(sample,new URLSearchParams('date=2026-09-08')).map(p=>p.id).join(',')"),'3,2');
 assert.equal(run("filterFeed(sample,new URLSearchParams('from=2026-09-07&to=2026-09-07')).map(p=>p.id).join(',')"),'1');
 assert.equal(run("filterFeed(sample,new URLSearchParams('from=2026-09-09&to=2026-09-07')).length"),0);
});

test('search finds interpretation-only text and composes with author and ticker filters',()=>{
 assert.equal(run("filterFeed(sample,new URLSearchParams('q=存储&author=jukan&ticker=mu'))[0].id"),'1');
 assert.equal(run("filterFeed(sample,new URLSearchParams('q=存储&author=serenity')).length"),0);
});

test('cards keep the complete source and interpretation escaped, including missing interpretations',()=>{
 const html=run("postCard({...sample[0],text:'<script>original</script>',summary:'<b>解读</b>',quote:{text:'x'.repeat(900)}})");
 assert.ok(html.includes('&lt;script&gt;original&lt;/script&gt;'));
 assert.ok(html.includes('&lt;b&gt;解读&lt;/b&gt;'));
 assert.ok(html.includes('x'.repeat(900)));
 assert.ok(html.includes('非作者原话'));
 assert.ok(run('postCard(sample[1])').includes('暂无 DeepSeek 解读'));
});

test('pagination replaces cards without gaps or duplicates and clamps invalid pages',()=>{
 run("var many=Array.from({length:65},(_,i)=>({...sample[i%3],id:String(i)}))");
 const ids=()=>[...root.innerHTML.matchAll(/data-post-id="([^"]+)"/g)].map(m=>m[1]);
 run('renderFeedRows(many,1,30)');assert.deepEqual(ids().sort((a,b)=>a-b),Array.from({length:30},(_,i)=>String(i)));
 assert.ok(root.innerHTML.includes('第 1 / 3 页'));
 run('renderFeedRows(many,2,30)');assert.deepEqual(ids().sort((a,b)=>a-b),Array.from({length:30},(_,i)=>String(i+30)));
 run('renderFeedRows(many,99,30)');assert.deepEqual(ids().sort((a,b)=>a-b),['60','61','62','63','64']);
 assert.ok(root.innerHTML.includes('第 61–65 条 / 共 65 条'));
 run('renderFeedRows(many,-1,100)');assert.equal(ids().length,65);
 run('renderFeedRows([],99,0)');assert.ok(root.innerHTML.includes('共 0 条'));assert.ok(!root.innerHTML.includes('NaN'));
 assert.equal(run('feedSize(999)'),30);assert.equal(run('feedPage(Infinity)'),1);
});

test('pagination loads the full archive when a requested page exceeds the recent snapshot',async()=>{
 const navigation=readFileSync(new URL('../scripts/dashboard/unified_navigation.js',import.meta.url),'utf8');
 vm.runInContext(navigation.slice(navigation.indexOf('const fullFeedRows'),navigation.indexOf('function setFreshness')),context);
 run("var location={search:'?author=jukan'}; RAW={partial:true,total_posts:65}; raw=async()=>{RAW={posts:many};return RAW}");
 await run('renderFeedRows(many.slice(0,30),1,30)');
 assert.ok(root.innerHTML.includes('第 1 / 3 页'));
 await run('renderFeedRows(many.slice(0,30),2,30)');
 assert.equal(run('RAW.partial'),undefined);
 assert.ok(root.innerHTML.includes('共 43 条'));
 assert.equal((root.innerHTML.match(/data-post-id=/g)||[]).length,13);
});

test('page and size controls retain filters and reset the page on a size change',async()=>{
 const next={dataset:{feedPage:'2'},disabled:false},size={value:'10',disabled:false};
 root.querySelectorAll=selector=>selector==='[data-feed-page]'?[next]:selector==='[data-feed-size]'?[size]:[next,size];
 root.focus=()=>{};root.scrollIntoView=()=>{};
 run("location={pathname:'/posts/',search:'?author=jukan&ticker=MU'};var savedURL='';var history={replaceState:(a,b,url)=>{savedURL=url}}; RAW=null");
 await run('renderFeedRows(many,1,30)');await next.onclick();
 assert.ok(root.innerHTML.includes('第 2 / 3 页'));assert.ok(run('savedURL').includes('author=jukan&ticker=MU&page=2&page_size=30'));
 await size.onchange();assert.ok(root.innerHTML.includes('第 1 / 7 页'));assert.ok(run('savedURL').includes('page=1&page_size=10'));
 root.querySelectorAll=()=>[];
});
