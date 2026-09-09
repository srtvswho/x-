export function mount(host,mode,data){
const document=host.attachShadow({mode:'open'});
document.innerHTML="<style>\n:host{\n  --bg:#f6f7f9;--panel:#ffffff;--panel-2:#f8fafc;--line:#e2e6ec;--line-soft:#edf0f4;\n  --ink:#172033;--ink-dim:#526075;--ink-faint:#8993a3;\n  --amber:#a86708;--amber-soft:#fff5df;--cyan:#126f78;--cyan-soft:#e8f5f5;\n  --rose:#b94258;--rose-soft:#fcecef;--violet:#6557c8;--blue:#315efb;--blue-soft:#eef2ff;\n  --mono:\"SF Mono\",ui-monospace,\"JetBrains Mono\",\"Roboto Mono\",Menlo,Consolas,monospace;\n  --sans:\"Inter\",-apple-system,\"PingFang SC\",\"Microsoft YaHei\",system-ui,sans-serif;\n}\n*{box-sizing:border-box}\nhtml,body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);\n  -webkit-font-smoothing:antialiased;font-size:14px;line-height:1.5}\na{color:inherit;text-decoration:none}\n::selection{background:#ffd58c;color:#172033}\n\n.topbar{position:sticky;top:0;z-index:40;display:flex;align-items:center;gap:18px;\n  padding:0 max(24px,calc((100vw - 1120px)/2));height:62px;background:rgba(255,255,255,.92);backdrop-filter:blur(16px);\n  border-bottom:1px solid rgba(226,230,236,.9);box-shadow:0 1px 8px rgba(23,32,51,.035)}\n.brand{display:flex;align-items:baseline;gap:10px}\n.brand .mark{font-family:var(--mono);font-weight:750;letter-spacing:.12em;font-size:15px;color:var(--ink)}\n.brand .sub{font-family:var(--mono);font-size:10.5px;letter-spacing:.22em;color:var(--ink-faint);text-transform:uppercase}\n.topbar .spacer{flex:1}\n.clock{font-family:var(--mono);font-size:11px;color:var(--ink-dim);letter-spacing:.06em}\n.clock b{color:var(--blue)}\n.live{display:inline-flex;align-items:center;gap:6px;font-family:var(--mono);font-size:10px;\n  letter-spacing:.16em;color:var(--ink-faint);text-transform:uppercase}\n.live .dot{width:7px;height:7px;border-radius:50%;background:#25a36f;animation:pulse 2.4s infinite}\n@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(72,201,214,.5)}70%{box-shadow:0 0 0 7px rgba(72,201,214,0)}100%{box-shadow:0 0 0 0 rgba(72,201,214,0)}}\n\n.layout{max-width:1360px;margin:0 auto;display:grid;grid-template-columns:176px minmax(0,1120px);gap:24px;padding:0 24px}\n.wrap{min-width:0;padding:20px 0 88px}\n.side-nav{position:sticky;top:84px;align-self:start;padding-top:20px}.side-nav a{display:block;padding:9px 12px;margin-bottom:5px;border-radius:9px;color:var(--ink-faint);font-size:12px}.side-nav a:hover{background:var(--blue-soft);color:var(--blue)}\n.side-nav .nav-title{font-family:var(--mono);font-size:9px;letter-spacing:.12em;color:var(--ink-faint);margin:0 0 9px 12px}.section-anchor{scroll-margin-top:78px}\n\n.shead{display:flex;align-items:center;gap:12px;margin:36px 0 14px}\n.shead:first-child{margin-top:18px}\n.shead .num{display:grid;place-items:center;width:25px;height:25px;border-radius:8px;background:var(--blue-soft);font-family:var(--mono);font-size:10px;font-weight:700;color:var(--blue);letter-spacing:.04em}\n.shead h2{margin:0;font-size:19px;font-weight:720;letter-spacing:-.02em}\n.shead .hint{font-family:var(--mono);font-size:10.5px;color:var(--ink-faint);letter-spacing:.04em}\n.shead .rule{flex:1;height:1px;background:var(--line-soft)}\n\n/* ===== 最近动态 时间 badge + 静默日 banner ===== */\n.rel{display:inline-block;margin-top:3px;padding:1px 5px;border-radius:3px;\n  font-family:var(--mono);font-size:9.5px;letter-spacing:.05em;line-height:1.4;font-weight:600;}\n.rt-today{background:rgba(72,201,214,.18);color:var(--cyan);border:1px solid rgba(72,201,214,.35);}\n.rt-1d{background:rgba(72,201,214,.14);color:var(--cyan);border:1px solid rgba(72,201,214,.25);}\n.rt-recent{background:rgba(240,167,60,.12);color:var(--amber);border:1px solid rgba(240,167,60,.25);}\n.rt-mid{background:rgba(154,140,255,.10);color:var(--violet);border:1px solid rgba(154,140,255,.20);}\n.rt-old{background:rgba(154,164,184,.08);color:var(--ink-faint);border:1px solid rgba(154,164,184,.15);}\n.banner-silent{margin:0 0 14px;padding:10px 14px;background:rgba(240,167,60,.08);\n  border:1px solid rgba(240,167,60,.25);border-radius:6px;\n  color:var(--amber);font-family:var(--mono);font-size:11.5px;letter-spacing:.04em;}\n\n/* ===== today brief (hero) ===== */\n.brief{background:var(--panel);border:1px solid var(--line);box-shadow:0 10px 30px rgba(23,32,51,.055);\n  border-radius:16px;padding:24px 26px;position:relative;overflow:hidden;margin-top:8px}\n.brief::before{content:\"\";position:absolute;left:0;right:0;top:0;height:4px;background:linear-gradient(90deg,var(--blue),#6c8cff 55%,#aab9ff)}\n.brief .bh{display:flex;align-items:center;gap:10px;margin-bottom:11px}\n.brief .blabel{font-family:var(--mono);font-size:10px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--blue)}\n.brief .bdate{font-family:var(--mono);font-size:10.5px;color:var(--ink-faint);margin-left:auto}\n.brief .btext{font-size:15px;line-height:1.65;color:var(--ink)}\n.brief .btext .mark-amber{color:var(--amber)}\n.brief .bstrip{display:flex;flex-wrap:wrap;gap:14px;margin-top:15px;padding-top:14px;border-top:1px solid var(--line-soft)}\n.brief .bstat{display:flex;align-items:baseline;gap:6px}\n.brief .bstat .v{font-family:var(--mono);font-weight:700;font-size:15px}\n.brief .bstat .v.cy{color:var(--cyan)}.brief .bstat .v.am{color:var(--amber)}\n.brief .bstat .k{font-family:var(--mono);font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-faint)}\n.brief .bdate-sub{font-family:var(--mono);font-size:10.5px;color:var(--ink-faint);margin-left:8px}\n.brief .bwin{font-family:var(--mono);font-size:10.5px;color:var(--ink-faint);margin-bottom:16px;padding:8px 10px;background:var(--panel-2);border-radius:8px}\n.feed-empty .win-range{font-family:var(--mono);font-size:10.5px;color:var(--ink-faint);margin-top:4px;display:block}\n.stmt .tag.ordinary{background:rgba(255,255,255,.05);color:var(--ink-faint);border:1px dashed rgba(255,255,255,.18)}\n.brief .bempty{padding:8px 12px;margin:0 0 12px;border-radius:6px;font-size:12.5px;line-height:1.4}\n.brief .bempty.warn{background:rgba(224,97,122,.12);border:1px solid rgba(224,97,122,.4);color:var(--pink)}\n.brief .bempty.info{background:rgba(72,201,214,.10);border:1px solid rgba(72,201,214,.32);color:var(--cyan)}\n.feed-empty{padding:8px 12px;margin:0 0 12px;border-radius:6px;font-size:12.5px;color:var(--ink-faint)}\n.feed-empty.warn{background:rgba(224,97,122,.12);border:1px solid rgba(224,97,122,.4);color:var(--pink)}\n.brief .bhot{margin-left:auto;display:flex;gap:6px;align-items:center}\n\n/* ===== window toggle ===== */\n.winrow{display:flex;align-items:center;gap:8px;margin-bottom:14px}\n.winrow .lab{font-family:var(--mono);font-size:10px;color:var(--ink-faint);letter-spacing:.08em;text-transform:uppercase}\n.seg{display:inline-flex;background:var(--panel);border:1px solid var(--line);border-radius:7px;padding:2px}\n.seg button{font-family:var(--mono);font-size:11px;color:var(--ink-dim);background:none;border:none;\n  padding:5px 12px;border-radius:5px;cursor:pointer;letter-spacing:.04em;transition:.15s}\n.seg button:hover{color:var(--ink)}\n.seg button.on{background:var(--amber);color:#fff;font-weight:600}\n.filters{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:0 0 14px}\n.filters label{font-family:var(--mono);font-size:10px;color:var(--ink-faint);letter-spacing:.06em;text-transform:uppercase}\n.filters select{background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:9px;\n  padding:8px 30px 8px 11px;font-family:var(--sans);font-size:12px;box-shadow:0 1px 2px rgba(23,32,51,.03)}\n.period-control{display:flex;align-items:center;gap:8px;margin:0 0 14px}\n.period-control label{font-family:var(--mono);font-size:10px;color:var(--ink-faint);letter-spacing:.06em;text-transform:uppercase}\n.period-control select{min-width:146px;background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:9px;padding:9px 32px 9px 12px;font-family:var(--sans);font-size:12px;box-shadow:0 1px 2px rgba(23,32,51,.03)}\n.structured-summary{display:grid;gap:0;border:1px solid var(--line-soft);border-radius:11px;overflow:hidden}\n.summary-line{display:grid;grid-template-columns:105px 1fr;gap:16px;align-items:start;padding:11px 14px;background:#fff;border-bottom:1px solid var(--line-soft)}\n.summary-line:last-child{border-bottom:none}.summary-line:nth-child(even){background:#fbfcfe}\n.summary-key{font-size:12px;color:var(--blue);font-weight:700;padding-top:1px}\n.summary-value{color:var(--ink);line-height:1.55}\n.pager{display:flex;justify-content:center;align-items:center;gap:10px;margin-top:14px}\n.pager button{background:var(--panel);color:var(--ink-dim);border:1px solid var(--line);border-radius:6px;\n  padding:6px 12px;cursor:pointer}.pager button:disabled{opacity:.35;cursor:default}\n.pager span{font-family:var(--mono);font-size:10.5px;color:var(--ink-faint)}\n.perfgrid{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin:0 0 14px}\n.perfstat{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:11px 13px}\n.perfstat .v{font-family:var(--mono);font-size:17px;font-weight:700}.perfstat .k{font-size:10px;color:var(--ink-faint);display:block}\n.pos{color:var(--cyan)}.neg{color:var(--rose)}\n\n/* consensus band */\n.consensus{background:linear-gradient(135deg,#f6f8ff,#fff);border:1px solid #dce3ff;border-radius:14px;padding:18px 20px;margin-bottom:16px;box-shadow:0 5px 18px rgba(49,94,251,.045)}\n.consensus .ch{display:flex;align-items:center;gap:8px;margin-bottom:9px}\n.consensus .clabel{font-family:var(--mono);font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--blue)}\n.consensus .cwin{font-family:var(--mono);font-size:10px;color:var(--ink-faint);margin-left:auto}\n.consensus .ctext{font-size:13px;line-height:1.66;color:var(--ink-dim)}\n\n/* ===== stance grid ===== */\n.stance-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}\n.stance{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px;box-shadow:0 5px 18px rgba(23,32,51,.035)}\n.stance .sh{display:flex;align-items:center;gap:9px;margin-bottom:11px}\n.stance .sh .av{width:30px;height:30px;border-radius:9px;display:grid;place-items:center;\n  font-family:var(--mono);font-weight:700;font-size:12px;color:#fff}\n.stance .sh .nm{font-weight:600;font-size:13.5px}\n.stance .sh .tp{font-family:var(--mono);font-size:9px;letter-spacing:.1em;text-transform:uppercase;\n  padding:2px 7px;border-radius:4px;background:var(--panel-2);border:1px solid var(--line);color:var(--ink-dim)}\n.stance .sh .tp.signal{color:var(--cyan);border-color:var(--cyan-soft);background:var(--cyan-soft)}\n.stance .ct{margin-left:auto;font-family:var(--mono);font-size:10px;color:var(--ink-faint)}\n.stance .psum{font-size:12.5px;line-height:1.6;color:var(--ink-dim);padding:12px;margin-bottom:12px;\n  background:var(--panel-2);border-radius:10px;border:1px solid var(--line-soft)}\n.stance .psum .lead{font-family:var(--mono);font-size:9px;letter-spacing:.1em;text-transform:uppercase;\n  color:var(--ink-faint);display:block;margin-bottom:4px}\n.stmt{display:flex;gap:10px;padding:8px 0;border-bottom:1px solid var(--line-soft)}\n.stmt:last-child{border-bottom:none;padding-bottom:0}\n.stmt .dir{flex:none;width:16px;text-align:center;font-family:var(--mono);font-weight:700;font-size:12px;margin-top:1px}\n.stmt .dir.long{color:var(--cyan)}.stmt .dir.short{color:var(--rose)}.stmt .dir.neutral{color:var(--ink-faint)}\n.stmt .body{flex:1;min-width:0}\n.stmt .txt{font-size:12px;color:var(--ink);line-height:1.5}\n.stmt .meta{display:flex;flex-wrap:wrap;align-items:center;gap:5px;margin-top:5px}\n.tag{font-family:var(--mono);font-size:9.5px;letter-spacing:.03em;padding:2px 6px;border-radius:4px;\n  background:var(--panel-2);border:1px solid var(--line);color:var(--ink-dim)}\n.tag.bk{color:var(--amber);border-color:var(--amber-soft);background:var(--amber-soft)}\n.tag.strong{color:var(--cyan);border-color:var(--cyan-soft);background:var(--cyan-soft)}\n.tag.weak{color:var(--rose);border-color:var(--rose-soft);background:var(--rose-soft)}\n.tag.date{color:var(--ink-faint)}\n.flag{font-family:var(--mono);font-size:9px;letter-spacing:.05em;padding:2px 6px;border-radius:4px;\n  background:#f0edff;border:1px solid #ddd7ff;color:var(--violet)}\n\n/* ===== daily feed ===== */\n.feed{display:flex;flex-direction:column}\n.fitem{display:grid;grid-template-columns:58px 28px 1fr;gap:14px;padding:16px 0;border-bottom:1px solid var(--line-soft)}\n.fitem:last-child{border-bottom:none}\n.fitem .ftime{font-family:var(--mono);font-size:10.5px;color:var(--ink-faint);text-align:right;padding-top:2px;line-height:1.4}\n.fitem .frail{display:flex;flex-direction:column;align-items:center}\n.fitem .fav{width:28px;height:28px;border-radius:8px;display:grid;place-items:center;\n  font-family:var(--mono);font-weight:700;font-size:11px;color:#fff}\n.fitem .fline{flex:1;width:1px;background:var(--line-soft);margin-top:6px;min-height:8px}\n.fitem:last-child .fline{display:none}\n.fbody{min-width:0}\n.fbody .ftop{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin-bottom:5px}\n.fbody .fnm{font-weight:600;font-size:12.5px}\n.fbody .fsum{font-size:13px;color:var(--ink-dim);line-height:1.62}\n.fbody .frebut{margin-top:6px;font-size:11.5px;color:var(--amber);line-height:1.45;padding-left:9px;border-left:2px solid var(--amber-soft)}\n.fbody .frow{display:flex;flex-wrap:wrap;gap:6px;margin-top:7px;align-items:center}\n.dirpill{font-family:var(--mono);font-size:10px;font-weight:600;letter-spacing:.05em;padding:2px 7px;border-radius:5px;text-transform:uppercase}\n.dirpill.long{background:var(--cyan-soft);color:var(--cyan)}.dirpill.short{background:var(--rose-soft);color:var(--rose)}\n.atb{font-family:var(--mono);font-size:9px;letter-spacing:.06em;padding:1.5px 6px;border-radius:3px;border:1px solid var(--line);color:var(--ink-faint)}\n.atb.ORIGINAL{color:var(--cyan);border-color:var(--cyan-soft)}\n.flink{font-family:var(--mono);font-size:10px;color:var(--ink-faint);margin-left:auto}\n.flink:hover{color:var(--cyan)}\n.feed-toggle{margin-top:14px;text-align:center}\n.feed-toggle button{font-family:var(--mono);font-size:11px;color:var(--ink-dim);background:var(--panel);\n  border:1px solid var(--line);border-radius:7px;padding:8px 18px;cursor:pointer;letter-spacing:.04em}\n.feed-toggle button:hover{color:var(--ink);border-color:#34405a}\n\n/* ===== ticker table ===== */\n.tcard{background:var(--panel);border:1px solid var(--line);border-radius:14px;overflow:auto;box-shadow:0 5px 18px rgba(23,32,51,.035)}\n.ttable{width:100%;border-collapse:collapse;font-size:12.5px}\n.ttable thead th{font-family:var(--mono);font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;\n  color:var(--ink-faint);text-align:left;padding:11px 14px;background:var(--panel-2);border-bottom:1px solid var(--line);font-weight:500;white-space:nowrap}\n.ttable tbody td{padding:12px 14px;border-bottom:1px solid var(--line-soft);vertical-align:top}\n.ttable tbody tr:last-child td{border-bottom:none}\n.ttable tbody tr:hover{background:var(--panel-2)}\n.tk{font-family:var(--mono);font-weight:700;font-size:13px}.tk.long{color:var(--cyan)}.tk.short{color:var(--rose)}\n.by{display:flex;align-items:center;gap:7px}\n.by .av{width:20px;height:20px;border-radius:5px;display:grid;place-items:center;font-family:var(--mono);font-weight:700;font-size:10px;color:#0c0e13;flex:none}\n.by .nm{font-size:12px}\n.when{font-family:var(--mono);font-size:11px;color:var(--ink-dim)}\n.circle{display:inline-flex;align-items:center;gap:5px;font-family:var(--mono);font-size:11px}\n.circle.in{color:var(--cyan)}.circle.out{color:var(--ink-faint)}\n.dirpill2{font-family:var(--mono);font-size:10px;font-weight:600;letter-spacing:.05em;padding:2px 7px;border-radius:5px;text-transform:uppercase}\n.dirpill2.long{background:var(--cyan-soft);color:var(--cyan)}.dirpill2.short{background:var(--rose-soft);color:var(--rose)}\n.pending{font-family:var(--mono);font-size:10px;letter-spacing:.04em;color:var(--ink-faint);border:1px dashed var(--line);border-radius:5px;padding:4px 9px;display:inline-flex;align-items:center;gap:6px}\n.pending .q{color:var(--amber)}\n\n/* ===== KOL cards (now at bottom, compact reference) ===== */\n.kolgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}\n.kol{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px;position:relative;overflow:hidden;box-shadow:0 4px 14px rgba(23,32,51,.03)}\n.kol::before{content:\"\";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--accent,var(--amber))}\n.kol .khead{display:flex;align-items:center;gap:9px;margin-bottom:3px}\n.kol .avatar{width:30px;height:30px;border-radius:9px;display:grid;place-items:center;font-family:var(--mono);font-weight:700;font-size:12px;color:#fff;background:var(--accent,var(--amber))}\n.kol .kname{font-weight:600;font-size:14px}\n.kol .khandle{font-family:var(--mono);font-size:10px;color:var(--ink-faint)}\n.kol .ktype{display:inline-block;margin-top:8px;font-family:var(--mono);font-size:9px;letter-spacing:.1em;text-transform:uppercase;padding:2px 7px;border-radius:4px;background:var(--panel-2);border:1px solid var(--line);color:var(--ink-dim)}\n.kol[data-type=\"signal\"] .ktype{color:var(--cyan);border-color:var(--cyan-soft);background:var(--cyan-soft)}\n.kol .kdesc{margin:10px 0 11px;font-size:11.5px;color:var(--ink-dim);line-height:1.45}\n.kgroup{margin-top:8px}\n.kgroup .glab{font-family:var(--mono);font-size:9px;letter-spacing:.1em;text-transform:uppercase;display:flex;align-items:center;gap:5px;margin-bottom:5px}\n.kgroup.strong .glab{color:var(--cyan)}.kgroup.weak .glab{color:var(--rose)}\n.chips{display:flex;flex-wrap:wrap;gap:4px}\n.chip{font-size:10.5px;padding:2px 7px;border-radius:5px;line-height:1.3;border:1px solid transparent}\n.chip.s{background:var(--cyan-soft);color:var(--cyan);border-color:#cce7e9}\n.chip.w{background:var(--rose-soft);color:var(--rose);border-color:#f2cfd6}\n\n.foot{margin-top:50px;padding-top:18px;border-top:1px solid var(--line);font-family:var(--mono);font-size:10.5px;color:var(--ink-faint);letter-spacing:.04em;display:flex;flex-wrap:wrap;gap:8px;align-items:center}\n.foot .sep{color:var(--line)}\n\n\n/* 原文依据 */\n.evidence{margin-top:8px;border-top:1px dashed var(--line);padding-top:7px;position:relative}\n.evidence summary{cursor:pointer;list-style:none;color:var(--blue);font-family:var(--mono);font-size:10.5px;font-weight:700}\n.evidence summary::-webkit-details-marker{display:none}.evidence summary:before{content:'＋';margin-right:5px}.evidence[open] summary:before{content:'－'}\n.thesis-change-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin:14px 0 22px}\n.thesis-change-card{border:1px solid var(--line);border-radius:14px;background:#fff;padding:17px;box-shadow:0 8px 28px rgba(31,47,78,.04)}\n.thesis-change-head{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:10px}.thesis-theme{font-size:17px;font-weight:750}.change-pill,.action-pill{font-family:var(--mono);font-size:9.5px;border-radius:999px;padding:4px 7px;background:var(--blue-soft);color:var(--blue)}\n.golden-pill{font-family:var(--mono);font-size:9.5px;border-radius:999px;padding:4px 7px;background:#e9f8f0;color:#148052;border:1px solid #bde8d5;font-weight:800}\n.action-pill{background:#f2f4f8;color:var(--ink-faint)}.thesis-row{display:grid;grid-template-columns:105px 1fr;gap:10px;padding:7px 0;border-top:1px solid var(--line-soft);font-size:12.5px;line-height:1.5}.thesis-row b{color:var(--ink-faint);font-size:10px;letter-spacing:.04em}.exposure{display:inline-block;margin:2px 5px 2px 0;padding:2px 6px;border-radius:5px;background:#f4f7fb}.thesis-actions{display:flex;gap:8px;margin-top:11px}.thesis-actions button,.thesis-actions a{border:1px solid var(--line);border-radius:7px;background:#fff;color:var(--blue);font-size:10.5px;padding:6px 8px;cursor:pointer}\n.cost-panel{border:1px solid var(--line);border-radius:14px;background:#fff;padding:16px;margin:14px 0 22px;box-shadow:0 8px 28px rgba(31,47,78,.04)}\n.cost-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px}.cost-stat{padding:11px;border-radius:10px;background:var(--panel-2);border:1px solid var(--line-soft)}.cost-stat b{display:block;font-family:var(--mono);font-size:17px}.cost-stat span{font-size:10px;color:var(--ink-faint)}\n.cost-controls{display:flex;flex-wrap:wrap;gap:7px;margin-top:11px}.cost-detail{margin-top:12px;font-family:var(--mono);font-size:10.5px;color:var(--ink-dim);line-height:1.7}\n.evidence-pop{position:fixed;z-index:90;left:50%;top:50%;transform:translate(-50%,-50%);width:min(560px,calc(100vw - 32px));max-height:min(70vh,620px);overflow:auto;padding:18px;border:1px solid #d7def1;border-radius:18px;background:#fff;box-shadow:0 24px 80px rgba(23,32,51,.24)}\n.evidence-pop:before{content:'原文';display:block;margin-bottom:10px;padding-right:42px;font-size:11px;font-weight:800;color:var(--blue);letter-spacing:.08em}.evidence-close{position:absolute;z-index:2;right:12px;top:12px;width:36px;height:36px;display:grid;place-items:center;border:1px solid var(--line);border-radius:50%;background:#fff;color:var(--ink-dim);font-size:22px;line-height:1;cursor:pointer;box-shadow:0 2px 8px rgba(23,32,51,.08)}.evidence-close:hover{background:var(--blue-soft);color:var(--blue);border-color:#cfd8ff}.evidence-close:focus-visible{outline:3px solid rgba(49,94,251,.25);outline-offset:2px}.evidence-text{padding:12px 13px;border-radius:11px;background:var(--panel-2);color:var(--ink-dim);font-size:13px;line-height:1.7;white-space:pre-wrap;overflow-wrap:anywhere}.evidence-link{margin-top:10px}.evidence-link a{color:var(--blue);font-size:11px;font-weight:650}.filter-note{font-size:11px;color:var(--ink-faint);margin:-5px 0 14px}\n/* ===== explainable signal strength ===== */\n.signal-strip{display:flex;flex-wrap:wrap;gap:7px;margin:10px 0 15px;padding:11px 13px;border:1px solid var(--line-soft);border-radius:10px;background:#fbfcfe}\n.signal-strip span{font-size:11px;color:var(--ink-dim)}.signal-strip b{color:var(--ink)}\n.sig{display:inline-flex;align-items:center;gap:4px;font-family:var(--mono);font-size:9.5px;font-weight:800;padding:2px 7px;border-radius:999px;border:1px solid}\n.sig.focus{color:#166f50;background:#eaf8f2;border-color:#bde8d5}.sig.reference{color:#8a5b08;background:#fff6df;border-color:#f0d89b}.sig.general{color:#697586;background:#f2f4f7;border-color:#dfe3e8}\n.sigwhy{font-size:10px;color:var(--ink-faint)}.cycle{font-family:var(--mono);font-size:9.5px;color:var(--violet);background:#f1efff;border:1px solid #ded9ff;border-radius:999px;padding:2px 6px}\n.review-note{margin-top:12px;padding-top:11px;border-top:1px solid var(--line-soft);font-size:10.5px;color:var(--ink-faint);line-height:1.55}\n.new-badge{display:inline-block;margin:5px 0 0 6px;padding:2px 6px;border-radius:999px;background:#e9f8f0;color:#148052;font-family:var(--mono);font-size:9px;font-weight:800;vertical-align:middle}\n.return-wrap{display:flex;align-items:center;gap:8px;margin-top:5px;min-width:145px}.return-track{position:relative;width:86px;height:8px;border-radius:999px;background:#edf0f4;overflow:hidden}\n.return-zero{position:absolute;left:50%;top:0;width:1px;height:100%;background:#aab2bf}.return-bar{position:absolute;top:1px;height:6px;border-radius:999px}\n.return-bar.in{left:50%;background:#25a36f}.return-bar.out{right:50%;background:#d45467}.return-value{min-width:50px;font-family:var(--mono);font-size:11px;font-weight:800}\n.return-value.in{color:#16845a}.return-value.out{color:#c13e55}\n\n@media(max-width:1080px){.layout{display:block}.side-nav{display:none}.kolgrid{grid-template-columns:repeat(2,1fr)}.stance-grid,.thesis-change-grid{grid-template-columns:1fr}.cost-grid{grid-template-columns:repeat(2,1fr)}}\n@media(max-width:680px){\n  .topbar{padding:0 14px;height:58px}.brand .sub,.clock{display:none}\n  .kolgrid,.cost-grid{grid-template-columns:1fr}.wrap{padding:12px 14px 60px}.shead{margin-top:30px}.shead:first-child{margin-top:14px}.shead .hint,.shead .rule{display:none}\n  .brief{padding:20px 16px}.brief .bh{flex-wrap:wrap}.brief .bdate{margin-left:0}.brief .bhot{width:100%;margin-left:0;margin-top:6px}\n  .summary-line{grid-template-columns:1fr;gap:4px;padding:10px 11px}.summary-key{font-size:11px}.summary-value{font-size:13px}\n  .ttable thead{display:none}.ttable,.ttable tbody,.ttable tr,.ttable td{display:block;width:100%}\n  .ttable tbody tr{border-bottom:1px solid var(--line);padding:6px 0}.ttable td{border:none;padding:5px 14px}\n  .fitem{grid-template-columns:42px 22px 1fr;gap:10px}\n  .perfgrid{grid-template-columns:repeat(2,1fr)}\n}\n@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}\n\n    :host{display:block;font:16px/1.6 var(--sans);color:var(--ink)}\n    .shead{margin-top:24px}.shead .num{display:none}.shead h2{font-size:26px}\n    .hint,.filter-note,.period-control label,.filters label,.ct,.cwin{font-size:14px}\n    .consensus,.stance,.tcard,.cost-panel{box-shadow:none;border-radius:14px}\n    .ttable{font-size:14px}.tcard{overflow-x:auto}.psum,.ctext{font-size:16px}\n    select{font-size:14px}.signal-strip{font-size:14px}.shead{flex-wrap:wrap}\n    </style>"+({"usage": "  <div class=\"shead section-anchor\" id=\"ai-cost\"><span class=\"num\">01</span><h2>AI 用量</h2>\n    <span class=\"hint\">实际费用、调用次数与预算</span><span class=\"rule\"></span></div>\n  <div class=\"cost-panel\" id=\"ai-cost-panel\"></div>\n\n  <!-- ===== 市场态度：今日总结与近期态度合并 ===== -->\n", "market": "  <div class=\"shead section-anchor\" id=\"market\"><span class=\"num\">02</span><h2>市场态度</h2>\n    <span class=\"hint\">共识结论 · 个人立场 · 每条判断可查看原文</span><span class=\"hint\" id=\"summary-date\"></span><span class=\"rule\"></span></div>\n  <div class=\"period-control\"><label for=\"daily-archive-date\">每日聚合与个人解读</label><select id=\"daily-archive-date\"></select></div>\n  <div class=\"consensus\" id=\"daily-archive\"></div>\n  <div class=\"period-control\"><label for=\"stance-window\">时间范围</label><select id=\"stance-window\">\n    <option value=\"0\" selected>今日</option><option value=\"0.25\">近 1 周</option><option value=\"1\">近 1 个月</option><option value=\"3\">近 3 个月</option>\n    <option value=\"6\">近 6 个月</option><option value=\"12\">近 1 年</option></select></div>\n  <div class=\"consensus\" id=\"consensus\"></div>\n  <div class=\"signal-strip\"><span><b>信号口径：</b>重点 = 能力圈内、方向明确并有行动证据；参考 = 有价值但不能直接跟单；一般 = 转述、回顾、模糊或已过期。</span><span><b>更新：</b>信号每日衰减 · 人物表现每月更新 · 定位每季度复核。</span></div>\n  <div class=\"stance-grid\" id=\"stancegrid\"></div>\n\n  <!-- ===== 标的追踪：优先于明细 ===== -->\n", "tracking": "  <div class=\"shead section-anchor\" id=\"tracking\"><span class=\"num\">03</span><h2>标的追踪</h2>\n    <span class=\"hint\">看谁在何时看多或看空、此后股价怎样变化。起点是已存历史中的最早明确方向。</span><span class=\"rule\"></span></div>\n  <div class=\"filters\"><label for=\"perf-kol\">人物</label><select id=\"perf-kol\"></select>\n    <label for=\"perf-window\">最近方向记录</label><select id=\"perf-window\"><option value=\"7\">近 1 周</option><option value=\"30\" selected>近 1 个月</option><option value=\"90\">近 3 个月</option><option value=\"365\">近 1 年</option><option value=\"0\">全部历史</option></select><label for=\"perf-sort\">排序</label><select id=\"perf-sort\"><option value=\"return_desc\">方向收益高 → 低</option><option value=\"return_asc\">方向收益低 → 高</option><option value=\"latest\" selected>最近提及优先</option><option value=\"first\">追踪起点最新</option></select></div>\n  <div class=\"filter-note\" id=\"perf-note\"></div>\n  <div class=\"perfgrid\" id=\"perf-summary\"></div>\n  <div class=\"tcard\"><table class=\"ttable\">\n    <thead><tr><th>标的</th><th>谁 · 起点方向</th><th>追踪周期</th><th>起点价</th>\n      <th>现价 / 方向收益</th><th>首条依据</th><th>能力圈</th><th>行情截至</th></tr></thead>\n    <tbody id=\"tbody\"></tbody></table></div>\n\n"})[mode];

const RECORDS=data['DATA'];
const KOLS=data['KOLS'];
const TICKERS=data['TICKERS'];
const CALL_PERFORMANCE=data['CALL_PERFORMANCE'];
const SUM=data['SUMMARIES'];
const TODAY_STATS=data['TODAY_STATS'];
const TODAY_RECORDS=data['TODAY_RECORDS'];
const BUILD_META=data['BUILD_META'];
const THESIS_CHANGES=data['THESIS_CHANGES'];
const AI_COST_PANEL=data['AI_COST_PANEL'];
// 单一今日窗口函数 (24h 滚动) — 跟 build_dashboard.py / intel_gen_summaries.py / query_today_stats 共用
function todayWindowUTC(){return [new Date(BUILD_META.window_start_utc), new Date(BUILD_META.window_end_utc)];}
const COLORS={jukan:'#48c9d6',serenity:'#f0a73c',zephyr:'#9a8cff',austin:'#e0617a',dgretta:'#2e9d69',feroce:'#d17c2f',tradex:'#5277d3',gsmferrari:'#8255b5'};
const ORDER=['jukan','serenity','zephyr','austin','dgretta','feroce','tradex','gsmferrari'];
function initials(n){return n.slice(0,1).toUpperCase()}
// 北京时间格式化 (统一时区, 不依赖浏览器本地时区)
const CST_FMT = new Intl.DateTimeFormat('zh-CN', { timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false });
const CST_FMT_DATE = new Intl.DateTimeFormat('zh-CN', { timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit' });
function _cstParts(iso, withTime){
  const d = new Date(iso);
  const parts = (withTime ? CST_FMT : CST_FMT_DATE).formatToParts(d);
  const m = {};
  for (const p of parts) m[p.type] = p.value;
  return m;
}
function fmtDate(iso){const m=_cstParts(iso,false);return `${parseInt(m.month)}/${parseInt(m.day)}`}
function fmtFull(iso){const m=_cstParts(iso,false);return `${m.year}.${m.month}.${m.day}`}
function fmtTime(iso){const m=_cstParts(iso,true);return `${m.hour}:${m.minute}`}
function fmtFullCST(iso){const m=_cstParts(iso,true);return `${m.year}-${m.month}-${m.day} ${m.hour}:${m.minute} CST`}
function cstDateKey(iso){const m=_cstParts(iso,false);return `${m.year}-${m.month}-${m.day}`}
function formatStructuredSummary(text){
  const lines=String(text||'').split(/\n+/).map(s=>s.trim()).filter(Boolean);
  if(lines.length<2||!lines.some(s=>s.includes('｜'))) return `<div class="summary-value">${text||'—'}</div>`;
  return `<div class="structured-summary">${lines.map(line=>{
    const i=line.indexOf('｜');
    const key=i>=0?line.slice(0,i):'结论';const value=i>=0?line.slice(i+1):line;
    return `<div class="summary-line"><span class="summary-key">${key}</span><span class="summary-value">${value}</span></div>`;
  }).join('')}</div>`;
}

function escHtml(value){return String(value||'').replace(/[&<>"']/g,function(ch){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch];});}
function safeUrl(value){try{const url=new URL(String(value||''),window.location.href);return /^(https?):$/.test(url.protocol)?escHtml(url.href):'#';}catch(_){return '#';}}
function renderThesisChanges(){
  const root=document.getElementById('thesis-change-grid');
  if(!THESIS_CHANGES.length){root.innerHTML='<div class="feed-empty">尚无达到质量门槛的 Thesis Change；旧 Post Feed 仍保留在下方。</div>';return;}
  root.innerHTML=THESIS_CHANGES.map(x=>{
    const evidence=(x.new_evidence||[]).map(e=>`<li>${e.source_url?`<a href="${safeUrl(e.source_url)}" target="_blank" rel="noopener">${escHtml(e.text)}</a>`:escHtml(e.text)} <span class="change-pill">${escHtml(e.status)}</span></li>`).join('');
    const tags=a=>(a||[]).map(v=>`<span class="exposure">${escHtml(v)}</span>`).join('')||'—';
    const lines=(label,items)=>(items||[]).length?`<div class="thesis-row"><b>${label}</b><span><ul>${items.map(v=>`<li>${escHtml(typeof v==='string'?v:(v.view||JSON.stringify(v)))}</li>`).join('')}</ul></span></div>`:'';
    const authorViews=(x.author_views||[]).map(v=>`${v.author}: ${v.view}`);
    const sources=(x.supporting_sources||[]).map(s=>`<li><a href="${safeUrl(s.url)}" target="_blank" rel="noopener">${escHtml(s.title||s.url)}</a> <span class="change-pill">${escHtml(s.source_class)}</span></li>`).join('');
    const researchDetail=x.is_research_case?`<details class="evidence research-detail"><summary>完整 Evidence Graph 与 AI 审计</summary>
      ${lines('AUTHOR VIEW',authorViews)}${lines('FACTS',x.facts)}${lines('LOGIC CHAIN',x.logic_chain)}${lines('CORRECTIONS',x.corrections)}
      ${lines('COUNTER CASE',x.counter_case)}${lines('SECOND ORDER',x.second_order_effects)}${lines('RISKS',x.risks)}${lines('UNKNOWNS',x.unknowns)}
      ${lines('CATALYSTS',x.catalysts)}${lines('INVALIDATION',x.invalidation_conditions)}
      ${sources?`<div class="thesis-row"><b>SOURCES</b><span><ul>${sources}</ul></span></div>`:''}
      </details>`:'';
    return `<article class="thesis-change-card"><div class="thesis-change-head"><span class="thesis-theme">${escHtml(x.theme)}</span><span class="change-pill">${escHtml(x.change_type)}</span><span class="action-pill">${escHtml(x.actionability)}</span>${x.golden_status?`<span class="golden-pill">GOLDEN ${escHtml(x.golden_status)}</span>`:''}</div>
      <div class="meta">${escHtml((x.authors||[]).join(' · '))} · Confidence ${x.confidence==null?'—':Math.round(x.confidence*100)} · Social ${x.social_mentions||0} / Independent ${x.independent_evidence||0}</div>
      <div class="thesis-row"><b>PREVIOUS VIEW</b><span>${escHtml(x.previous_view)}</span></div>
      <div class="thesis-row"><b>NEW EVIDENCE</b><span><ul>${evidence||'<li>—</li>'}</ul></span></div>
      <div class="thesis-row"><b>NEW VIEW</b><span>${escHtml(x.new_view)}</span></div>
      <div class="thesis-row"><b>AI ASSESSMENT</b><span>${escHtml(x.ai_assessment)}</span></div>
      ${(x.consensus||[]).length?`<div class="thesis-row"><b>CONSENSUS</b><span>${tags(x.consensus)}</span></div>`:''}
      ${(x.disagreement||[]).length?`<div class="thesis-row"><b>DISAGREEMENT</b><span>${tags(x.disagreement)}</span></div>`:''}
      <div class="thesis-row"><b>EXPOSURE</b><span>＋ ${tags(x.positive_exposure)}<br>－ ${tags(x.negative_exposure)}</span></div>
      ${researchDetail}
      <div class="thesis-actions"><button type="button" onclick="const d=this.closest('article').querySelector('details');if(d){d.open=true;d.scrollIntoView({behavior:'smooth'})}">View Thesis</button><button type="button" onclick="const u=this.closest('article').querySelector('ul');if(u)u.scrollIntoView({behavior:'smooth'})">View Evidence</button><button type="button" title="仅用户主动触发，Daily 不调用 Sol" onclick="alert('Deep Analysis 仅在你主动触发后运行，不会由 Daily Feed 自动调用。')">Deep Analysis</button></div></article>`;
  }).join('');
}
function renderAiCostPanel(){
  const x=AI_COST_PANEL,usd=v=>`$${Number(v||0).toFixed(4)}`,flag=v=>`<span class="${v?'sig focus':'sig general'}">${v?'YES':'NO'}</span>`;
  const stages=(x.by_stage||[]).map(v=>`${escHtml(v.name)} ${usd(v.cost)} / ${v.calls}`).join(' · ')||'No calls';
  const models=(x.by_model||[]).map(v=>`${escHtml(v.name)} ${usd(v.cost)} / ${v.calls}`).join(' · ')||'No calls';
  document.getElementById('ai-cost-panel').innerHTML=`<div class="cost-grid">
    <div class="cost-stat"><b>${usd(x.today_cost)}</b><span>Today AI Cost</span></div>
    <div class="cost-stat"><b>${usd(x.days_7_cost)}</b><span>Last 7 Days</span></div>
    <div class="cost-stat"><b>${usd(x.days_30_cost)}</b><span>Last 30 Days</span></div>
    <div class="cost-stat"><b>${x.calls_today||0}</b><span>Calls Today</span></div>
    <div class="cost-stat"><b>${x.pending_unknown_calls||0}</b><span>Pending / Unknown · ${usd(x.pending_unknown_risk)}</span></div></div>
    <div class="cost-controls"><span>AI Enabled ${flag(x.ai_enabled)}</span><span>Expensive Jobs ${flag(x.expensive_jobs_enabled)}</span><span class="change-pill">Daily ${usd(x.daily_budget)}</span><span class="change-pill">Run ${usd(x.run_budget)}</span><span class="change-pill">Calls ${x.call_limit}</span></div>
    <div class="cost-detail"><b>BY STAGE</b> · ${stages}<br><b>BY MODEL</b> · ${models}</div>`;
}
const SIGNAL_POLICY={
  jukan:{focus:'存储/HBM能力圈内的明确方向与实际操作',caution:'模糊、无行动证据的短线风险评论',review:'每月更新表现 · 每季度复核能力圈'},
  zephyr:{focus:'产业卡点与能力圈内做多',caution:'做空信号：历史多空表现不对称',review:'每月更新多空分项 · 每季度复核'},
  austin:{focus:'公司竞争格局与技术路线',caution:'短线买卖点与圈外标的',review:'每月更新表现 · 每季度复核'},
  serenity:{focus:'光通信/CPO/InP产业趋势与标的发现',caution:'高频重复喊多与具体买点',review:'每月更新时点表现 · 每季度复核'},
  dgretta:{focus:'明确原创的成长股启动和连续决策链',caution:'小盘高Beta仓位与大回撤',review:'轻测权重运行 · 完成长周期深测后再升级'},
  feroce:{focus:'成长主题的二次确认与仓位结构',caution:'不能单独触发重仓',review:'轻测权重运行 · 每月滚动复核'},
  tradex:{focus:'MU/SNDK及60–120日存储主题',caution:'20日短线择时、目标价与营销式回顾',review:'按中期主题使用 · 短线自动降权'},
  gsmferrari:{focus:'技术形态、多空择时与顶部风险',caution:'产业基本面和单条信号波动',review:'必须结合止损 · 每月更新双向表现'}
};
function inferHorizon(r){
  const s=((r.summary||'')+' '+(r.raw_text||'')).toLowerCase();
  if(/财报|earnings|发布会|event|催化/.test(s)) return {name:'事件',days:30};
  if(/短期|短线|这周|几天|near.?term/.test(s)) return {name:'短线',days:14};
  if(/季度|周期|库存|供给|dram|nand|hbm/.test(s)) return {name:'周期',days:120};
  if(/长期|未来.?年|多年|long.?term/.test(s)) return {name:'长期',days:365};
  return {name:'波段',days:60};
}
function attributionMultiplier(r){
  const a=String((r&&r.attribution)||'').toUpperCase();
  if(!a)return 1;
  if(a==='ENDORSED'||a==='RELAYED+COMMENT')return .5;
  if(['ORIGINAL','NA','DISAGREED'].includes(a))return 1;
  return 0;
}
function effectiveDirection(r){
  return attributionMultiplier(r)>0&&(r.direction==='long'||r.direction==='short')?r.direction:'neutral';
}
function signalWeight(r){
  const k=KOLS[r.kol]||{};
  const direction=effectiveDirection(r),multiplier=attributionMultiplier(r);
  if(direction==='neutral')return 0;
  if(direction==='short'&&k.shortWeight!==undefined)return (Number(k.shortWeight)||0)*multiplier;
  if(r.kol==='tradex'&&['短线','事件'].includes(inferHorizon(r).name))return (Number(k.shortTermWeight)||0)*multiplier;
  return (Number(k.consensusWeight)||0)*multiplier;
}
function signalStrength(r){
  const h=inferHorizon(r),age=Math.max(0,Math.floor((Date.now()-new Date(r.published_at).getTime())/86400000));
  const text=((r.summary||'')+' '+(r.raw_text||'')).toLowerCase();
  const action=!!r.is_disc||/买入|加仓|减仓|卖出|持有|仓位|bought|added|sold|position/.test(text);
  const explicit=effectiveDirection(r)!=='neutral';
  const k=KOLS[r.kol]||{}, strong=(k.strong||[]).some(s=>text.includes(String(s).toLowerCase())||(r.bottleneck&&String(r.bottleneck).includes(s)));
  const inField=r.in_field===true||strong;
  let level='general',why='普通信息或未形成方向';
  if(attributionMultiplier(r)===0&&['long','short'].includes(r.direction)){why='转述外部观点，不计作者方向与绩效';}
  if(explicit&&inField&&(action||r.is_disc)){level='focus';why='能力圈内 + 方向明确 + 有行动证据';}
  else if(explicit&&inField){level='reference';why='能力圈内且方向明确，但未披露行动';}
  else if(r.bottleneck&&inField){level='reference';why='能力圈内产业判断，不等于交易信号';}
  else if(explicit){level='reference';why='方向明确，但能力圈证据较弱';}
  if(r.is_retro){level='general';why='回顾性内容，不作为新信号';}
  if(r.kol==='zephyr'&&r.direction==='short'){level='reference';why='明确展示；历史做空分项较弱，谨慎参考';}
  if(r.kol==='jukan'&&h.name==='短线'&&!action){level='reference';why='短线风险提示但无行动证据';}
  if(r.kol==='serenity'&&explicit&&!action){level='reference';why='产业判断有价值；具体买点需价格过滤';}
  if(r.kol==='austin'&&explicit&&!action){level='reference';why='更适合作格局研究，不机械跟短线';}
  if(age>h.days){level='general';why='已超过默认有效期，保留作历史记录';}
  if(attributionMultiplier(r)===0&&['long','short'].includes(r.direction)){
    level='general';why='转述外部观点，不计作者方向与绩效';
  }
  return {level,label:{focus:'重点',reference:'参考',general:'一般'}[level],why,horizon:h.name,days:h.days,age};
}
function signalBadges(r){
  const s=signalStrength(r),left=Math.max(0,s.days-s.age);
  const authorExplicit=effectiveDirection(r)!=='neutral',relayed=attributionMultiplier(r)===0&&['long','short'].includes(r.direction),k=KOLS[r.kol]||{};
  const weight=authorExplicit?signalWeight(r):(relayed?0:(Number(k.researchWeight)||0)),weightLabel=authorExplicit?'方向权重':(relayed?'作者方向权重':'认知权重');
  return '<span class="sig '+s.level+'">'+s.label+'</span><span class="cycle">'+weightLabel+' '+weight.toFixed(2)+'</span><span class="cycle">'+s.horizon+' · '+(left?'约余 '+left+' 天':'已到期')+'</span><span class="sigwhy">'+s.why+'</span>';
}
function closeEvidence(el){
  const details=el&&el.closest?el.closest('details.evidence'):null;
  if(details)details.open=false;
}
function evidenceDetails(r,label){
  label=label||'查看原文';
  const text=r&&r.raw_text?escHtml(r.raw_text):'暂无原文';
  const link=r&&r.raw_url?'<a href="'+escHtml(r.raw_url)+'" target="_blank" rel="noopener">在 X 打开 ↗</a>':'';
  return '<details class="evidence"><summary>'+label+'</summary><div class="evidence-pop" role="dialog" aria-modal="true" aria-label="原文"><button type="button" class="evidence-close" aria-label="关闭原文" title="关闭" data-close-evidence>×</button><div class="evidence-text">'+text+'</div><div class="evidence-link">'+link+'</div></div></details>';
}

/* ---- 01 市场态度（原今日总结已合并） ---- */
/* 顶部 live 元信息 + 页脚 */
function renderLiveMeta(){
  const dataUntilTxt = BUILD_META.data_until_label || '—';
  const txt = `生成 ${BUILD_META.build_time_label} · 数据截至 ${dataUntilTxt}`;
  const el = document.getElementById('live-text');
  if (el) el.textContent = txt;
  const f1 = document.getElementById('foot-build');
  const f2 = document.getElementById('foot-datauntil');
  if (f1) f1.textContent = `生成 ${BUILD_META.build_time_label}`;
  if (f2) f2.textContent = `数据截至 ${dataUntilTxt}`;
}

/* ---- 02 近期态度 ---- */
let win=0;
function stanceTopic(r){
  const s=((r.summary||'')+' '+(r.raw_text||'')+' '+(r.bottleneck||'')+' '+((r.ticker||[]).join(' '))).toLowerCase();
  if(/hbm|dram|nand|memory|存储|内存|mu\b|sndk|海力士|三星/.test(s)) return '存储/HBM';
  if(/光通信|光模块|cpo|inp|激光器|aaoi|lite\b|cohr|axti|sive|mtsi/.test(s)) return '光通信/CPO/InP';
  if(/算力|gpu|ai芯片|nvda|amd\b|googl|nbis/.test(s)) return 'AI算力';
  if(/半导体|晶圆|代工|封装|tsm|asml/.test(s)) return '半导体';
  return '其他方向';
}
function recordStances(r){
  if(attributionMultiplier(r)===0)return [];
  const text=((r.summary||'')+' '+(r.raw_text||'')).toLowerCase();
  const topicDefs=[
    {topic:'存储/HBM',terms:'(?:hbm|dram|nand|memory|存储|内存|海力士|三星)'},
    {topic:'光通信/CPO/InP',terms:'(?:光通信|光模块|cpo|inp|激光器|aaoi|lite|cohr|axti|sive|mtsi)'},
    {topic:'AI算力',terms:'(?:算力|gpu|ai芯片|nvda|amd|googl|nbis)'},
    {topic:'半导体',terms:'(?:半导体|晶圆|代工|封装|tsm|asml)'}
  ];
  const out=[],seen=new Set();
  const add=(topic,direction)=>{const key=topic+'|'+direction;if(!seen.has(key)){seen.add(key);out.push({topic,direction});}};
  const effective=effectiveDirection(r);
  const baseDirection=(effective==='long'||effective==='short')?effective:null;
  const baseTopic=stanceTopic(r);
  if(baseDirection)add(baseTopic,baseDirection);
  topicDefs.forEach(def=>{
    const gap='[^，。；、\\n]{0,8}';
    const longPattern=new RegExp('(?:看多|偏多|做多|long|bullish)'+gap+def.terms+'|'+def.terms+gap+'(?:看多|偏多|做多|long|bullish)','i');
    const shortPattern=new RegExp('(?:看空|偏空|做空|short|bearish)'+gap+def.terms+'|'+def.terms+gap+'(?:看空|偏空|做空|short|bearish)','i');
    [['long',longPattern],['short',shortPattern]].forEach(([direction,pattern])=>{
      if(pattern.test(text)&&(def.topic!==baseTopic||direction===baseDirection))add(def.topic,direction);
    });
  });
  return out;
}
function resolveWindowStances(records){
  const sorted=records.slice().sort((a,b)=>new Date(b.published_at)-new Date(a.published_at));
  const resolved=[],seen=new Set();
  sorted.forEach(r=>{
    recordStances(r).forEach(s=>{
      const key=r.kol+'|'+s.topic;
      if(!seen.has(key)){
        seen.add(key);
        resolved.push({r,...s});
      }
    });
  });
  return resolved;
}
function selectStanceEvidence(records,limit){
  const sorted=records.slice().sort((a,b)=>new Date(b.published_at)-new Date(a.published_at));
  const chosen=[],usedPosts=new Set();
  resolveWindowStances(sorted).forEach(({r})=>{
    if(!usedPosts.has(r.post_id)){
      chosen.push(r);
      usedPosts.add(r.post_id);
    }
  });
  const target=Math.max(limit,chosen.length);
  sorted.forEach(r=>{
    if(chosen.length<target&&!usedPosts.has(r.post_id)){
      chosen.push(r);
      usedPosts.add(r.post_id);
    }
  });
  return chosen.sort((a,b)=>new Date(b.published_at)-new Date(a.published_at));
}
function liveConsensus(records){
  const directional=resolveWindowStances(records);
  if(!directional.length) return '共识方向｜本窗口无明确方向证据\n核心标的｜无明确标的\n分歧/风险｜暂无可由本窗口证据验证的分歧';
  const groups=new Map();
  directional.forEach(({r,topic,direction})=>{
    const key=topic+'|'+direction;
    if(!groups.has(key))groups.set(key,{topic,direction,kols:new Set(),tickers:new Set(),weight:0});
    const g=groups.get(key),w=signalWeight({...r,direction});
    if(!g.kols.has(r.kol)){g.kols.add(r.kol);g.weight+=w;}
    (r.ticker||[]).forEach(t=>g.tickers.add(t));
  });
  const all=[...groups.values()].filter(g=>g.weight>0).sort((a,b)=>b.weight-a.weight||b.kols.size-a.kols.size);
  const shared=all.filter(g=>g.kols.size>=2&&g.weight>=0.8);
  const singles=all.filter(g=>!shared.includes(g));
  const name=k=>KOLS[k]?KOLS[k].name:k;
  const describe=g=>`${g.topic}${g.direction==='long'?'看多':'看空'}（权重 ${g.weight.toFixed(2)}；${[...g.kols].map(name).join('、')}）`;
  const line1=shared.length?shared.map(describe).join('；'):'本窗口未形成“至少两人且合计权重≥0.80”的共识';
  const singleLine=singles.length?singles.slice(0,4).map(describe).join('；'):'无';
  const tickers=[...new Set(all.flatMap(g=>[...g.tickers]))];
  const conflicts=[];
  const topics=[...new Set(all.map(g=>g.topic))];
  topics.forEach(topic=>{const a=all.find(g=>g.topic===topic&&g.direction==='long'),b=all.find(g=>g.topic===topic&&g.direction==='short');if(a&&b)conflicts.push(`${topic}存在多空分歧（${[...a.kols].map(name).join('、')} vs ${[...b.kols].map(name).join('、')}）`);});
  return `共识方向｜${line1}\n单人方向｜${singleLine}\n核心标的｜${tickers.length?tickers.join('、'):'无明确标的'}\n分歧/风险｜${conflicts.length?conflicts.join('；'):'本窗口可见证据中暂无直接多空分歧'}`;
}
function livePersonSummary(records){
  const directional=resolveWindowStances(records);
  if(!directional.length)return '本窗口无明确方向证据';
  const groups=new Map();
  directional.forEach(({r,topic,direction})=>{const key=topic+'|'+direction;if(!groups.has(key))groups.set(key,{topic,direction,tickers:new Set()});(r.ticker||[]).forEach(t=>groups.get(key).tickers.add(t));});
  const all=[...groups.values()];
  const directions=all.map(g=>`${g.topic}${g.direction==='long'?'看多':'看空'}`).join('；');
  const tickers=[...new Set(all.flatMap(g=>[...g.tickers]))];
  return `核心方向｜${directions}\n明确标的｜${tickers.length?tickers.join('、'):'无明确标的'}\n证据口径｜扫描本窗口全部 ${records.length} 条记录；下方展示每个当前方向的对应证据`;
}
function renderStance(){
  const weekly=win===0.25;
  let cut;
  if(win===0){
    // 1D: 24h 滚动窗口 (跟 query_today_stats / SUM.consensus[0] / SUM.person[*][0] / renderBrief 共用同一窗口)
    cut = new Date(BUILD_META.window_start_utc);
  } else if(weekly){cut=new Date(Date.now()-7*86400000);} else { cut=new Date(); cut.setMonth(cut.getMonth()-win); }
  // 1D 必须使用 TODAY_RECORDS (含所有 raw_posts, 包括无 extraction 的普通推文)
  // 1M/3M/6M/1Y 仍用 RECORDS (有效判断)
  const dataSrc = (win===0) ? TODAY_RECORDS : RECORDS;
  const g=document.getElementById('stancegrid');
  const allByKol={},visibleByKol={};
  ORDER.forEach(key=>{
    let recs=dataSrc.filter(r=>r.kol===key&&new Date(r.published_at)>=cut);
    recs=recs.slice().sort((a,b)=>new Date(b.published_at)-new Date(a.published_at));
    if(win!==0)recs=recs.filter(r=>r.direction!=='neutral'||r.bottleneck);
    allByKol[key]=recs;
    visibleByKol[key]=selectStanceEvidence(recs,4);
  });
  const windowEvidence=ORDER.flatMap(key=>allByKol[key]);
  document.getElementById('consensus').innerHTML=`
    <div class="ch"><span class="clabel">◇ 当前窗口观点汇总</span><span class="cwin">${winLabel(win)}</span></div>
    <div class="ctext">${formatStructuredSummary(liveConsensus(windowEvidence))}</div>`;
  g.innerHTML=ORDER.map(key=>{
    const k=KOLS[key];const c=COLORS[key];
    const recs=visibleByKol[key];
    const rows=recs.length?recs.map(r=>{
      const displayDirection=effectiveDirection(r);
      const ic=displayDirection==='long'?'▲':displayDirection==='short'?'▼':'•';
      const isOrdinary = (displayDirection==='neutral' && !r.bottleneck);
      const bkStrong=r.bottleneck&&(k.strong||[]).some(s=>r.bottleneck.includes(s)||s.includes(r.bottleneck));
      const flags=[];if(r.is_disc)flags.push('<span class="flag">持仓披露</span>');if(r.is_retro)flags.push('<span class="flag">回顾</span>');
      const tk=(r.ticker||[]).map(t=>`<span class="tag">${t}</span>`).join('');
      const bk=r.bottleneck?`<span class="tag bk">${r.bottleneck}</span>`:'';
      const ft=r.bottleneck?(bkStrong?'<span class="tag strong">强项</span>':'<span class="tag weak">盲区</span>'):'';
      const ordinaryTag = isOrdinary ? '<span class="tag ordinary">普通动态</span>' : '';
      const relayTag=attributionMultiplier(r)===0&&['long','short'].includes(r.direction)?'<span class="tag ordinary">外部观点·不计作者方向</span>':'';
      return `<div class="stmt"><div class="dir ${displayDirection}">${ic}</div><div class="body">
        <div class="txt">${r.summary||r.raw_text||''}</div>
        <div class="meta">${tk}${bk}${ft}${ordinaryTag}${relayTag}${flags.join('')}<span class="tag date">${fmtFull(r.published_at)}</span></div><div class="meta">${signalBadges(r)}</div>${evidenceDetails(r,'查看这条原文')}</div></div>`;
    }).join(''):(win===0
      ? `<div class="stmt"><div class="dir neutral">·</div><div class="body"><div class="txt" style="color:var(--ink-faint)">${winLabel(0)} 无新推文</div></div></div>`
      : `<div class="stmt"><div class="dir neutral">·</div><div class="body"><div class="txt" style="color:var(--ink-faint)">该窗口内无强项方向性表态</div></div></div>`);
    const psum=livePersonSummary(allByKol[key]);
    return `<div class="stance">
      <div class="sh"><div class="av" style="background:${c}">${initials(k.name)}</div>
        <div class="nm">${k.name}</div><div class="tp ${k.type}">${k.rating}</div><div class="ct">原创基础方向权重 ${Number(k.consensusWeight||0).toFixed(2)} · 窗口 ${allByKol[key].length} 条 · 展示 ${recs.length} 条</div></div>
      <div class="psum"><span class="lead">${winLabel(win)} · 核心立场</span>${formatStructuredSummary(psum)}</div>
      ${rows}</div>`;
  }).join('');
}
function winLabel(w){return ({0:'今日',0.25:'近 1 周',1:'近 1 个月',3:'近 3 个月',6:'近 6 个月',12:'近 1 年'})[w]}

/* ---- 03 近期明细：按人筛选 + 全量分页 ---- */
let feedKol='all',feedLevel='all',feedPage=1,feedSize=30;
function initKolFilters(){
  const options=`<option value="all">全部人物</option>`+ORDER.map(k=>`<option value="${k}">${KOLS[k].name}</option>`).join('');
  document.getElementById('feed-kol').innerHTML=options;
  document.getElementById('perf-kol').innerHTML=options;
  document.getElementById('feed-kol').onchange=e=>{feedKol=e.target.value;feedPage=1;renderFeed();};
  document.getElementById('feed-level').onchange=e=>{feedLevel=e.target.value;feedPage=1;renderFeed();};
  document.getElementById('feed-size').onchange=e=>{feedSize=+e.target.value;feedPage=1;renderFeed();};
}
function renderFeed(){
  // TODAY_RECORDS 优先 (含所有 raw_posts, 包括无 extraction 的普通推文)
  // RECORDS 是有效判断. 合并去重 (按 post_id), TODAY 领先
  const seen = new Set();
  const merged = [];
  for (const r of (TODAY_RECORDS || [])) {
    if (!seen.has(r.post_id)) { seen.add(r.post_id); merged.push(r); }
  }
  for (const r of (RECORDS || [])) {
    if (!seen.has(r.post_id)) { seen.add(r.post_id); merged.push(r); }
  }
  // Signal Desk is intentionally scoped to the configured 8-person system.
  // New crawler sources must not abort the whole page before performance and
  // people panels render.
  const sorted = merged.filter(r=>KOLS[r.kol]&&(feedKol==='all'||r.kol===feedKol)&&(feedLevel==='all'||signalStrength(r).level===feedLevel))
    .sort((a,b)=>new Date(b.published_at)-new Date(a.published_at));
  // 顶部今日窗口横幅: 明确窗口跟计数
  const feedEmpty = document.getElementById('feed-empty');
  const winLabel = BUILD_META.window_label || '过去 24 小时';
  // 明确显示 窗口 跟 数据截止
  const winStartLabel = fmtFullCST(BUILD_META.window_start_utc);
  const winEndLabel = fmtFullCST(BUILD_META.window_end_utc);
  const dataUntilLabel = BUILD_META.data_until_label || '—';
  if (feedEmpty) {
    // 顶部: 窗口范围
    let winText = `统计窗口: ${winStartLabel} ~ ${winEndLabel} · 数据截至: ${dataUntilLabel}`;
    if (TODAY_STATS.empty_reason === 'no_posts') {
      feedEmpty.className = 'feed-empty warn';
      feedEmpty.innerHTML = `⚠ ${winLabel} 未抓到新推文, 以下为历史近端点<br><span class="win-range">${winText}</span>`;
    } else if (TODAY_STATS.empty_reason === 'no_directional') {
      feedEmpty.className = 'feed-empty';
      feedEmpty.innerHTML = `ℹ ${winLabel} 新增 ${TODAY_STATS.n_posts_24h} 条推文, 但无新增方向性投资判断, 以下混入历史近端点<br><span class="win-range">${winText}</span>`;
    } else {
      feedEmpty.className = 'feed-empty';
      feedEmpty.innerHTML = `✓ ${winLabel} 有 ${TODAY_STATS.n_posts_24h} 条推文, 含 ${TODAY_STATS.n_directional_24h} 条方向性判断<br><span class="win-range">${winText}</span>`;
    }
  }
  // 静默日不假装 - 头部标"最近动态 · N 天前"取代"最新批次 · 今天"
  if(sorted.length){
    const top=sorted[0];
    const now=new Date();
    const diffMs=now - new Date(top.published_at);
    const days=Math.floor(diffMs/86400000);
    const relLabel=days===0?'今天':(days===1?'1 天前':(days<=7?`${days} 天前`:(days<=30?`${days} 天前`:`${days} 天前 (历史)`)));
    const lastDate=fmtFullCST(top.published_at);
    document.getElementById('feed-date').innerHTML=
      `最近动态 · 共 ${sorted.length} 条 · 最新 <b style="color:var(--amber)">${relLabel}</b> (${lastDate})`;
  } else {
    document.getElementById('feed-date').textContent='最近动态 · 暂无数据';
  }
  const pages=Math.max(1,Math.ceil(sorted.length/feedSize));
  feedPage=Math.min(feedPage,pages);
  const show=sorted.slice((feedPage-1)*feedSize,feedPage*feedSize);
  // 静默日警告条 (如果最新一条不是今天)
  let banner='';
  if(sorted.length){
    const top=sorted[0];
    const now=new Date();
    const todayStart=new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const topDate=new Date(top.published_at);
    if(topDate < todayStart){
      const days=Math.floor((now - topDate)/86400000);
      banner=`<div class="banner-silent">⚠ 生产跟踪账号静默 ${days} 天, 以下为最近动态</div>`;
    }
  }
  document.getElementById('feed').innerHTML=banner + show.map(r=>{
    const c=COLORS[r.kol];const k=KOLS[r.kol];
    const tk=(r.ticker||[]).map(t=>`<span class="tag">${t}</span>`).join('');
    const bk=r.bottleneck?`<span class="tag bk">${r.bottleneck}</span>`:'';
    const authorDirection=effectiveDirection(r),isRelayedDirection=authorDirection==='neutral'&&['long','short'].includes(r.direction);
    const dp=authorDirection!=='neutral'?`<span class="dirpill ${authorDirection}">${authorDirection}</span>`:(isRelayedDirection?`<span class="tag ordinary">外部观点·${r.direction}</span>`:'');
    const flags=[];if(r.is_disc)flags.push('<span class="flag">持仓披露</span>');if(r.is_retro)flags.push('<span class="flag">回顾</span>');if(r.is_selfret)flags.push('<span class="flag">自报收益</span>');
    const rb=r.rebuts?`<div class="frebut">反驳叙事 · ${r.rebuts}</div>`:'';
    // 每条标 N 天前
    const now=new Date();
    const diffMs=now - new Date(r.published_at);
    const days=Math.floor(diffMs/86400000);
    let rtLabel, rtCls;
    if(days===0){rtLabel='今天';rtCls='rt-today';}
    else if(days===1){rtLabel='1 天前';rtCls='rt-1d';}
    else if(days<=7){rtLabel=`${days} 天前`;rtCls='rt-recent';}
    else if(days<=30){rtLabel=`${days} 天前`;rtCls='rt-mid';}
    else{rtLabel=`${days} 天前`;rtCls='rt-old';}
    return `<div class="fitem"><div class="ftime">${fmtDate(r.published_at)}<br>${fmtTime(r.published_at)}<br><span class="rel ${rtCls}">${rtLabel}</span></div>
      <div class="frail"><div class="fav" style="background:${c}">${initials(k.name)}</div><div class="fline"></div></div>
      <div class="fbody"><div class="ftop"><span class="fnm">${k.name}</span>${dp}${tk}${bk}${flags.join('')}</div>
        <div class="fsum">${r.summary||r.raw_text||''}</div>${rb}
        <div class="frow"><span class="atb ${r.attribution}">${r.attribution||'NA'}</span><a class="flink" href="${r.raw_url}" target="_blank">view on X ↗</a></div></div></div>`;
  }).join('');
  document.getElementById('feed-pager').innerHTML=`<button id="feed-prev" ${feedPage<=1?'disabled':''}>上一页</button>
    <span>第 ${feedPage} / ${pages} 页 · 共 ${sorted.length} 条</span>
    <button id="feed-next" ${feedPage>=pages?'disabled':''}>下一页</button>`;
  document.getElementById('feed-prev').onclick=()=>{if(feedPage>1){feedPage--;renderFeed();}};
  document.getElementById('feed-next').onclick=()=>{if(feedPage<pages){feedPage++;renderFeed();}};
  document.getElementById('foot-count').textContent=`${sorted.length} 条 records`;
}

/* ---- 04 标的 ---- */
let perfKol='all',perfDays=30,perfSort='latest';
function renderTickers(){
  const cut=perfDays?Date.now()-perfDays*86400000:-Infinity;
  const rows=CALL_PERFORMANCE.filter(t=>(perfKol==='all'||t.kol===perfKol)&&new Date(t.latest_published_at||t.published_at).getTime()>=cut);
  const sorters={return_desc:(a,b)=>(b.directional_return??-Infinity)-(a.directional_return??-Infinity),return_asc:(a,b)=>(a.directional_return??Infinity)-(b.directional_return??Infinity),latest:(a,b)=>new Date(b.latest_published_at||b.published_at)-new Date(a.latest_published_at||a.published_at),first:(a,b)=>new Date(b.published_at)-new Date(a.published_at)};
  rows.sort(sorters[perfSort]);
  document.getElementById('perf-note').textContent=`筛选后 ${rows.length} 个作者×标的样本 · 按最近方向记录筛选，起点始终回溯已存全历史。历史抓取及解读尚未覆盖完整，最早记录不等于真实首次喊单；以下为样本固定方向追踪收益，并非完整交易胜率。`;
  const valid=rows.filter(t=>t.directional_return!=null);
  const avg=valid.length?valid.reduce((s,t)=>s+t.directional_return,0)/valid.length:null;
  const wins=valid.filter(t=>t.directional_return>0).length;
  const longRows=valid.filter(t=>t.direction==='long'),shortRows=valid.filter(t=>t.direction==='short');
  const mean=a=>a.length?a.reduce((s,t)=>s+t.directional_return,0)/a.length:null;
  const fmt=v=>v==null?'—':`${v>=0?'+':''}${v.toFixed(1)}%`;
  const best=valid.length?[...valid].sort((a,b)=>b.directional_return-a.directional_return)[0]:null;
  const maxAbs=Math.max(10,...valid.map(t=>Math.abs(t.directional_return)));
  document.getElementById('perf-summary').innerHTML=`
    <div class="perfstat"><span class="v ${avg==null?'':(avg>=0?'pos':'neg')}">${fmt(avg)}</span><span class="k">样本综合等权方向收益</span></div>
    <div class="perfstat"><span class="v">${valid.length?wins+'/'+valid.length:'—'}</span><span class="k">样本上涨比例 ${valid.length?(wins/valid.length*100).toFixed(0)+'%':'—'}</span></div>
    <div class="perfstat"><span class="v">${fmt(mean(longRows))}</span><span class="k">Long 样本平均</span></div>
    <div class="perfstat"><span class="v">${fmt(mean(shortRows))}</span><span class="k">Short 样本平均</span></div>
    <div class="perfstat"><span class="v">${best?best.ticker+' '+fmt(best.directional_return):'—'}</span><span class="k">最高样本收益 · 行情覆盖 ${valid.length}/${rows.length}</span></div>`;
  document.getElementById('tbody').innerHTML=rows.map(t=>{
    const c=COLORS[t.kol];const k=KOLS[t.kol];
    const cp=t.call_price==null?'—':`${t.currency || 'USD'} ${Number(t.call_price).toFixed(2)}`;
    const np=t.now_price==null?'—':`${t.currency || 'USD'} ${Number(t.now_price).toFixed(2)}`;
    const dirRet=fmt(t.directional_return);
    const priceNote={ambiguous_asset_identity:'资产身份有歧义，暂不计算收益',latest_price_precedes_call:'报价早于喊单，暂不计算收益',missing_price_data:'行情缺失或代码待核实'}[t.price_unavailable_reason]||'';
    const cls=t.directional_return==null?'':(t.directional_return>=0?'in':'out');
    const ageDays=Math.floor((Date.now()-new Date(t.published_at).getTime())/86400000);
    const newBadge=ageDays<=7?'<span class="new-badge">NEW · 7D</span>':'';
    const barWidth=t.directional_return==null?0:Math.max(4,Math.min(100,Math.abs(t.directional_return)/maxAbs*100));
    const bar=`<div class="return-wrap"><div class="return-track"><span class="return-zero"></span><span class="return-bar ${cls}" style="width:${barWidth/2}%"></span></div><span class="return-value ${cls}">${dirRet}</span></div>`;
    const source={raw_text:t.raw_text,raw_url:t.raw_url};
    const earlier=(t.earlier_mentions||[]).map(p=>`<div class="meta">${fmtFull(p.published_at)} · ${p.analysis_status}${evidenceDetails(p,'更早提及原文')}</div>`).join('');
    const history=t.history_coverage||{};
    const gap=`<div class="meta">历史覆盖待核验${history.unprocessed_before_start?' · 起点前 '+history.unprocessed_before_start+' 条原帖待解读':''}${history.outdated_before_start?' · 起点前 '+history.outdated_before_start+' 条旧解读待复核':''}</div>`;
    const changed=t.direction_changed?`<div class="meta">期间出现相反方向 · 最近 ${t.latest_direction.toUpperCase()}<br>收益仅按起点方向固定追踪</div>`:'';
    return `<tr><td><span class="tk ${t.direction}">${t.ticker}</span>${newBadge}</td>
      <td><div class="by"><div class="av" style="background:${c}">${initials(k.name)}</div><span class="nm">${k.name}</span> <span class="dirpill2 ${t.direction}">${t.direction}</span></div></td>
      <td><span class="when">已识别最早 ${fmtFull(t.published_at)}<br>最近 ${fmtFull(t.latest_published_at||t.published_at)} · ${t.n_mentions||1} 次</span>${gap}${changed}</td>
      <td><span class="when">${cp}</span></td>
      <td><span class="when">${np}</span>${bar}${priceNote?'<div class="meta">'+priceNote+'</div>':''}</td>
      <td>${evidenceDetails(source,'查看起点原文')}${earlier?'<div class="meta">更早提及 '+t.earlier_mention_count+' 条（不等于喊单，列最早 3 条）</div>'+earlier:''}</td>
      <td>${t.in_field?'<span class="tag strong">强项</span>':'<span class="tag weak">圈外</span>'}<div class="meta" style="margin-top:6px">${signalBadges({...t,summary:t.bottleneck||'',raw_text:t.raw_text||''})}</div></td>
      <td><span class="when">${t.now_date||'行情待补'}</span></td></tr>`;
  }).join('');
}

/* ---- 05 人物卡 ---- */
function renderKols(){
  document.getElementById('kolgrid').innerHTML=ORDER.map(key=>{
    const k=KOLS[key];const c=COLORS[key];
    const st=(k.strong||[]).map(s=>`<span class="chip s">${s}</span>`).join('');
    const wk=(k.weak||[]).map(s=>`<span class="chip w">${s}</span>`).join('');
    return `<div class="kol" data-type="${k.type}" style="--accent:${c}">
      <div class="khead"><div class="avatar" style="background:${c}">${initials(k.name)}</div>
        <div><div class="kname">${k.name}</div><div class="khandle">${k.handle}</div></div></div>
      <div class="ktype">${k.typeLabel}</div>
      <div class="review-note"><b>评级：</b>${k.rating} · ${k.ratingStatus}<br><b>方向共识权重：</b>${Number(k.consensusWeight||0).toFixed(2)} · <b>认知验证权重：</b>${Number(k.researchWeight||0).toFixed(2)}${k.shortWeight===0?'<br><b>特别规则：</b>看空权重 0，不进入方向共识':''}${k.shortTermWeight?'<br><b>特别规则：</b>短线/事件权重 '+Number(k.shortTermWeight).toFixed(2):''}</div>
      <div class="kdesc">${k.desc}</div><div class="review-note"><b>重点参考：</b>${SIGNAL_POLICY[key].focus}<br><b>谨慎：</b>${SIGNAL_POLICY[key].caution}<br>${SIGNAL_POLICY[key].review}</div>
      <div class="kgroup strong"><div class="glab">▸ 信他</div><div class="chips">${st}</div></div>
      <div class="kgroup weak"><div class="glab">▸ 略过</div><div class="chips">${wk}</div></div></div>`;
  }).join('');
}

function renderDailyArchive(){
  const day=document.getElementById('daily-archive-date').value;
  const entry=(SUM.daily_history||{})[day];
  const escapeSummary=value=>String(value||'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  if(!entry){document.getElementById('daily-archive').textContent='每日摘要待补；原始 Post 可在下方查看。';return;}
  const pending=entry.complete===false;
  const persons=entry.person||{};
  document.getElementById('daily-archive').innerHTML=`<div class="ch"><span class="clabel">${escapeSummary(day)} · 每日信息聚合${pending?' · 部分解读待补':''}</span><span class="cwin">${entry.window_kind==='beijing_calendar_day'?'北京时间自然日':'历史存档'}</span></div>
    <div class="ctext">${formatStructuredSummary(escapeSummary(entry.summary))}</div>
    <details><summary>查看每个人当天的解读</summary>${ORDER.filter(k=>persons[k]).map(k=>`<div class="psum"><span class="lead">${escapeSummary(KOLS[k].name)}${entry.segment_errors&&entry.segment_errors[k]?' · 待补':''}</span>${formatStructuredSummary(escapeSummary(persons[k]))}</div>`).join('')||'<p>该历史日期尚无单独的人物摘要，请查看逐条 Post 解读。</p>'}</details>`;
}

    document.addEventListener('click',e=>{if(e.target.closest('[data-close-evidence]'))closeEvidence(e.target);});
    document.addEventListener('keydown',e=>{if(e.key==='Escape')document.querySelectorAll('details[open]').forEach(d=>d.open=false);});
    if(mode==='market'){
      const dates=Object.keys(SUM.daily_history||{}).sort().reverse();
      document.getElementById('daily-archive-date').innerHTML=dates.map(day=>`<option>${day}</option>`).join('');
      document.getElementById('daily-archive-date').onchange=renderDailyArchive;
      document.getElementById('stance-window').onchange=e=>{win=+e.target.value;renderStance();};
      renderDailyArchive();renderStance();
    }else if(mode==='tracking'){
      document.getElementById('perf-kol').innerHTML='<option value="all">全部人物</option>'+ORDER.map(k=>`<option value="${k}">${KOLS[k].name}</option>`).join('');
      document.getElementById('perf-kol').onchange=e=>{perfKol=e.target.value;renderTickers();};
      document.getElementById('perf-window').onchange=e=>{perfDays=+e.target.value;renderTickers();};
      document.getElementById('perf-sort').onchange=e=>{perfSort=e.target.value;renderTickers();};
      renderTickers();
    }else renderAiCostPanel();
    
}
