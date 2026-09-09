/* Exercise the retained market renderers without a browser or network. */
const fs=require('node:fs'),vm=require('node:vm'),zlib=require('node:zlib'),assert=require('node:assert/strict');
class Root {
  constructor(){this.nodes=new Map();}
  set innerHTML(html){this.html=html;this.scan(html);}
  scan(html){
    for(const m of html.matchAll(/<([\w-]+)[^>]*\bid="([^"]+)"[^>]*>/g)){
      if(this.nodes.has(m[2]))continue;
      const root=this,node={value:''};
      Object.defineProperty(node,'innerHTML',{set(value){this.html=value;root.scan(value);if(m[1]==='select')this.value=(value.match(/<option[^>]*value="([^"]*)"/)||value.match(/<option[^>]*>([^<]*)/))?.[1]||'';},get(){return this.html||'';}});
      this.nodes.set(m[2],node);
    }
  }
  getElementById(id){assert(this.nodes.has(id),`renderer requested missing element ${id}`);return this.nodes.get(id);}
  addEventListener(){}
  querySelectorAll(){return [];}
}
const mod=fs.readFileSync('dashboard_deploy_dist/assets/market-panels.js','utf8').replace('export function mount','function mount');
for(const mode of ['market','tracking','usage']){
  const root=new Root(),host={attachShadow:()=>root},data=JSON.parse(zlib.gunzipSync(fs.readFileSync(`dashboard_deploy_dist/data/${mode}-panels.json.gz`)));
  const context=vm.createContext({console,host,data,mode,Intl,Date,URL,window:{location:{href:'https://example.test/'}}});
  vm.runInContext(mod+'\nmount(host,mode,data);',context);
  const id={market:'stancegrid',tracking:'tbody',usage:'ai-cost-panel'}[mode];
  assert(root.getElementById(id).innerHTML.length>100,mode+' did not render');
  if(mode==='market'){
    assert(root.getElementById('daily-archive').innerHTML.includes('每日信息聚合'));
    root.getElementById('stance-window').onchange({target:{value:'1'}});
    assert(root.getElementById('consensus').innerHTML.includes('近 1 个月'));
  }
  if(mode==='tracking'){
    root.getElementById('perf-kol').onchange({target:{value:'jukan'}});
    root.getElementById('perf-window').onchange({target:{value:'0'}});
    assert(root.getElementById('tbody').innerHTML.includes('MU'));
    root.getElementById('perf-sort').onchange({target:{value:'first'}});
  }
  console.log('PASS render and filter: '+mode);
}
