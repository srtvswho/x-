import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const template=readFileSync(new URL('../scripts/dashboard/research_clue_preview.template.html',import.meta.url),'utf8');
const script=template.split('<script>')[1].split('</script>')[0].replace(/\s+route\(\);\s*$/,'');
const root={innerHTML:''};
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

test('load-more rendering retains earlier cards without duplicates and groups by display date',()=>{
 run('renderFeedRows(sample,2)');
 assert.equal((root.innerHTML.match(/data-post-id=/g)||[]).length,2);
 assert.ok(root.innerHTML.includes('feed-more'));
 run('renderFeedRows(sample,32)');
 assert.equal((root.innerHTML.match(/data-post-id=/g)||[]).length,3);
 assert.equal((root.innerHTML.match(/class="feed-day"/g)||[]).length,2);
 assert.ok(!root.innerHTML.includes('id="feed-more"'));
});
