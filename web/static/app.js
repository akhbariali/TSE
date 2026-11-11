'use strict';
const $ = (selector, root = document) => root.querySelector(selector);
const content = $('#content');
const state = {view:'overview', window:'20', start:'', end:'', chart:'net', selected:0, overview:null,
  symbolData:null, flows:{q:'',direction:'all',minimum:'0',sort:'net_desc',page:1}, reports:{q:'',state:'',page:1}, symbol:'', status:null};
let routeVersion=0, flowVersion=0, reportVersion=0, symbolVersion=0, debounceTimer, toastTimer;
const icons = {
 download:'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v12m-4-4 4 4 4-4M5 16v5h14v-5"/></svg>',
 search:'<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/></svg>'
};
function esc(value){return String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));}
function num(value,digits=2){return Number(value||0).toLocaleString('en-US',{maximumFractionDigits:digits,minimumFractionDigits:digits});}
function amount(value,digits=2){return num(Number(value)/1e13,digits);}
function signed(value,digits=2){return (Number(value)>0?'+':Number(value)<0?'−':'')+amount(Math.abs(value),digits);}
function cls(value){return Number(value)>0?'positive':Number(value)<0?'negative':'';}
function pct(value,digits=1){return num(Number(value||0)*100,digits)+'%';}
function integer(value){return Number(value||0).toLocaleString('en-US',{maximumFractionDigits:0});}
function bytes(value){return num(Number(value)/1048576,1)+' MB';}
function scopeQuery(){return state.window==='custom'?{window:'all',start:state.start,end:state.end}:{window:state.window};}
function url(path,query={}){return path+'?'+new URLSearchParams(query).toString();}
async function api(path,query={},options={}){
 const response=await fetch(url(path,query),options);
 let data;try{data=await response.json();}catch{throw new Error('The server returned an unreadable response. Try again.');}
 if(!response.ok)throw new Error(data.error||'The request failed. Try again.');
 return data;
}
function showError(message){const box=$('#error');box.textContent=message;box.hidden=!message;}
function toast(message){const box=$('#toast');box.textContent=message;box.hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>box.hidden=true,5500);}
function empty(title,description){return `<div class="empty-state"><strong>${esc(title)}</strong>${esc(description)}</div>`;}
function loading(text='Loading reports…'){return `<div class="loading-state" role="status">${esc(text)}</div>`;}
function exportButton(path,label='Export CSV'){return `<a class="button secondary" href="${esc(url(path,scopeQuery()))}">${icons.download}${esc(label)}</a>`;}
function heading(title,description,action=''){return `<div class="page-head"><div><h1>${esc(title)}</h1><p>${esc(description)}</p></div>${action}</div>`;}
function filters(scope){
 const custom=state.window==='custom';
 return `<form id="scope-form" class="filters">
 <div class="field"><label for="window">Report window</label><select id="window" name="window">${[['5','Latest 5 reports'],['20','Latest 20 reports'],['60','Latest 60 reports'],['all','Entire archive'],['custom','Custom dates']].map(([value,label])=>`<option value="${value}" ${state.window===value?'selected':''}>${label}</option>`).join('')}</select></div>
 <div class="field date-field"><label for="start">From · Solar Hijri</label><input id="start" name="start" inputmode="numeric" placeholder="1405/07/22" pattern="[0-9]{4}/[0-9]{2}/[0-9]{2}" value="${esc(custom?state.start:scope?.start||'')}" ${custom?'':'disabled'}></div>
 <div class="field date-field"><label for="end">To · Solar Hijri</label><input id="end" name="end" inputmode="numeric" placeholder="1405/08/19" pattern="[0-9]{4}/[0-9]{2}/[0-9]{2}" value="${esc(custom?state.end:scope?.end||'')}" ${custom?'':'disabled'}></div>
 ${custom?'<button class="button" type="submit">Apply dates</button>':''}
 <span class="filter-summary">${scope?integer(scope.reports)+' reports in this selection':'Choose a period to compare'}</span></form>`;
}
function metrics(data){const a=data.aggregate,latest=data.latest;
 return `<div class="scope-note"><span>All reported instruments · Values in trillion toman</span><span>${esc(data.scope.start||'—')} — ${esc(data.scope.end||'—')}</span></div>
 <div class="metrics">
 <div class="metric"><span class="metric-label">Individual net purchases</span><span class="metric-value ${cls(a.net_rial)}">${signed(a.net_rial)}<small>T</small></span><span class="metric-note">Ownership transfer over selection</span></div>
 <div class="metric"><span class="metric-label">Average daily trading value</span><span class="metric-value">${amount(a.average_turnover_rial)}<small>T</small></span><span class="metric-note">${integer(data.scope.reports)} validated daily reports</span></div>
 <div class="metric"><span class="metric-label">Net buying sessions</span><span class="metric-value">${a.positive_days}<small>/ ${data.scope.reports}</small></span><span class="metric-note">${a.negative_days} net selling sessions</span></div>
 <div class="metric"><span class="metric-label">Top 10 trading share</span><span class="metric-value">${pct(latest?.top10_turnover_share)}</span><span class="metric-note">Latest report in this selection</span></div></div>`;
}
function chartPanel(){return `<section class="panel chart-layout" aria-labelledby="chart-heading"><div class="chart-work">
 <div class="section-head"><div><h2 id="chart-heading">Ownership transfers</h2><p>Track the direction, then inspect the report.</p></div>
 <div class="tabs" role="tablist" aria-label="Chart metric">${[['net','Net transfers'],['cumulative','Cumulative'],['turnover','Trading value']].map(([key,label])=>`<button role="tab" data-chart="${key}" aria-selected="${state.chart===key}">${label}</button>`).join('')}</div></div>
 <div class="chart-meta"><span>Trillion toman</span><div class="legend"><span><i></i>Individual net buying</span><span><i class="sell"></i>Net selling</span></div></div>
 <div id="main-chart" class="chart-box"></div>
 <div class="scrubber"><span>Inspect</span><label class="sr-only" for="report-scrubber">Choose a report to inspect with arrow keys</label><input id="report-scrubber" type="range" min="0" max="${Math.max(0,state.overview.days.length-1)}" value="${state.selected}"><span id="scrubber-date">${esc(state.overview.days[state.selected]?.date||'')}</span></div>
 </div><aside id="inspector" class="inspector" aria-label="Selected report"></aside></section>`;}
function renderInspector(){const d=state.overview?.days[state.selected];if(!d)return;
 const total=d.retail_net_positive_symbols+d.retail_net_negative_symbols+d.retail_net_zero_symbols;
 $('#inspector').innerHTML=`<h3>Selected report</h3><div class="inspector-date">${esc(d.date)}</div><dl>
 <div><dt>Individual net</dt><dd class="${cls(d.retail_net_rial)}">${signed(d.retail_net_rial)} T</dd></div>
 <div><dt>Trading value</dt><dd>${amount(d.turnover_rial)} T</dd></div>
 <div><dt>Instrument rows</dt><dd>${integer(d.symbols)}</dd></div></dl>
 <div class="breadth" aria-label="Ownership flow breadth"><span id="breadth-buy"></span><span class="sell" id="breadth-sell"></span></div>
 <div class="breadth-caption">${integer(d.retail_net_positive_symbols)} net buying · ${integer(d.retail_net_negative_symbols)} net selling<br>${integer(d.retail_net_zero_symbols)} unchanged rows</div>
 <a class="button secondary" href="/api/files/${encodeURIComponent(d.sha)}">${icons.download}Original Excel</a>`;
 $('#breadth-buy').style.width=(total?d.retail_net_positive_symbols/total*100:0)+'%';
 $('#breadth-sell').style.width=(total?d.retail_net_negative_symbols/total*100:0)+'%';
 $('#scrubber-date').textContent=d.date;$('#report-scrubber').value=state.selected;
 $('#report-scrubber').setAttribute('aria-valuetext',d.date+', individual net purchases '+signed(d.retail_net_rial)+' trillion toman');
}
function drawChart(target,days,metric='net',interactive=false){
 const el=$(target);if(!el)return;
 if(interactive){const legend=$('.chart-meta .legend');if(legend)legend.innerHTML=metric==='net'?'<span><i></i>Individual net buying</span><span><i class="sell"></i>Net selling</span>':metric==='cumulative'?'<span><i class="series"></i>Cumulative individual net</span>':'<span><i class="series"></i>Reported trading value</span>';}
 if(!days.length){el.innerHTML=empty('No observations','Choose another period.');return;}
 let running=0;
 const points=days.map(d=>{const net=Number(d.retail_net_rial);running+=net;return {date:d.date,value:(metric==='cumulative'?running:metric==='turnover'?Number(d.turnover_rial):net)/1e13};});
 const width=Math.max(260,el.clientWidth),height=240,left=48,right=15,top=18,bottom=30,w=width-left-right,h=height-top-bottom;
 let min=Math.min(0,...points.map(p=>p.value)),max=Math.max(0,...points.map(p=>p.value));
 if(max===min){max+=1;min-=1;}const pad=(max-min)*.12;max+=pad;if(min<0)min-=pad;
 const x=i=>left+(i+.5)/points.length*w,y=v=>top+(max-v)/(max-min)*h;
 let svg=`<svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" role="img" aria-label="${esc(metric==='turnover'?'Daily trading value':metric==='cumulative'?'Cumulative individual net purchases':'Daily individual net purchases')}, ${esc(points[0].date)} to ${esc(points.at(-1).date)}, in trillion toman">`;
 for(let i=0;i<=4;i++){const value=max-(max-min)*i/4,py=y(value);svg+=`<line class="chart-grid" x1="${left}" x2="${width-right}" y1="${py}" y2="${py}"/><text x="${left-10}" y="${py+4}" text-anchor="end">${num(value,Math.max(Math.abs(max),Math.abs(min))<1?2:1)}</text>`;}
 svg+=`<line class="zero" x1="${left}" x2="${width-right}" y1="${y(0)}" y2="${y(0)}"/>`;
 if(metric==='cumulative'){
  const path=points.map((p,i)=>(i?'L':'M')+x(i)+','+y(p.value)).join(' ');
  svg+=`<path d="${path}" fill="none" stroke="#2248a5" stroke-width="2.4" vector-effect="non-scaling-stroke"/>`;
  if(points.length===1)svg+=`<circle cx="${x(0)}" cy="${y(points[0].value)}" r="4" fill="#2248a5"/>`;
 }else{
  const bw=Math.max(.6,Math.min(23,w/points.length*.64));
  points.forEach((p,i)=>svg+=`<rect x="${x(i)-bw/2}" y="${Math.min(y(0),y(p.value))}" width="${bw}" height="${Math.max(.8,Math.abs(y(0)-y(p.value)))}" rx="${Math.min(2,bw/3)}" fill="${metric==='turnover'?'#5478c9':p.value>=0?'#298e7d':'#c26b5e'}"><title>${esc(p.date)}: ${num(p.value,3)} trillion toman</title></rect>`);
 }
 const labels=[0,Math.floor((points.length-1)/2),points.length-1].filter((n,i,a)=>a.indexOf(n)===i);
 labels.forEach(i=>svg+=`<text x="${x(i)}" y="${height-7}" text-anchor="${i===0?'start':i===points.length-1?'end':'middle'}">${esc(points[i].date)}</text>`);
 if(interactive)svg+=`<line class="selection" x1="${x(state.selected)}" x2="${x(state.selected)}" y1="${top}" y2="${height-bottom}"/>`;
 svg+='</svg><div class="chart-tooltip" hidden></div>';el.innerHTML=svg;
 const pick=event=>{const box=$('svg',el).getBoundingClientRect();return Math.max(0,Math.min(points.length-1,Math.floor(((event.clientX-box.left)/box.width*width-left)/w*points.length)));};
 const tip=$('.chart-tooltip',el);
 el.onpointermove=event=>{const index=pick(event),box=el.getBoundingClientRect();tip.innerHTML=`${esc(points[index].date)}<strong>${num(points[index].value,3)} T</strong>`;tip.hidden=false;tip.style.left=Math.min(Math.max(0,event.clientX-box.left-45),Math.max(0,box.width-140))+'px';};
 el.onpointerleave=()=>tip.hidden=true;
 if(interactive)el.onclick=event=>{state.selected=pick(event);renderInspector();const line=$('.selection',el);line.setAttribute('x1',x(state.selected));line.setAttribute('x2',x(state.selected));};
}
function flowShell(){return `<section class="panel" aria-labelledby="flow-heading"><div class="section-head"><div><h2 id="flow-heading">Symbol flows</h2><p>Compare exact symbols across the selected reports.</p></div><a id="flow-export" class="button secondary small" href="#">${icons.download}Export CSV</a></div>
 <form id="flow-form" class="table-toolbar"><div class="field search"><label for="symbol-search">Symbol or instrument name</label><input type="search" id="symbol-search" name="q" placeholder="Search symbols, e.g. وبملت" value="${esc(state.flows.q)}"></div>
 <div class="field"><label for="direction">Individual flow</label><select name="direction" id="direction">${[['all','All directions'],['buy','Net buying'],['sell','Net selling']].map(([v,t])=>`<option value="${v}" ${state.flows.direction===v?'selected':''}>${t}</option>`).join('')}</select></div>
 <div class="field minimum"><label for="minimum">Min. trading value · T</label><input name="minimum" id="minimum" type="number" min="0" step="0.01" value="${esc(state.flows.minimum)}"></div>
 <div class="field"><label for="flow-sort">Sort by</label><select name="sort" id="flow-sort">${[['net_desc','Largest net buying'],['net_asc','Largest net selling'],['turnover','Trading value'],['ratio','Net / trading value'],['persistence','Buying persistence']].map(([v,t])=>`<option value="${v}" ${state.flows.sort===v?'selected':''}>${t}</option>`).join('')}</select></div><button type="submit" class="sr-only">Apply symbol filters</button></form><div id="flow-results">${loading('Loading symbol flows…')}</div></section>
 <p class="table-note">Positive = individuals bought more than they sold; institutions took the opposite side. Exact symbol suffixes are kept separate. Missing observations are not counted as zero.</p>`;}
function pagination(total,page,size,type){const pages=Math.max(1,Math.ceil(total/size));return `<div class="pagination"><span>${total?integer((page-1)*size+1)+'–'+integer(Math.min(page*size,total))+' of '+integer(total):'0'} ${type==='flow'?'symbols':'workbooks'}</span><div class="pagination-controls"><button class="button secondary small" data-page-type="${type}" data-page="${page-1}" ${page<=1?'disabled':''}>Previous</button><span>${page} / ${pages}</span><button class="button secondary small" data-page-type="${type}" data-page="${page+1}" ${page>=pages?'disabled':''}>Next</button></div></div>`;}
async function loadFlows(){
 const version=++flowVersion;if(!$('#flow-results'))return;
 const query={...scopeQuery(),...state.flows,size:25};$('#flow-export').href=url('/api/export/flows',query);
 $('#flow-results').setAttribute('aria-busy','true');
 try{const data=await api('/api/flows',query);if(version!==flowVersion||!$('#flow-results'))return;
 $('#flow-results').innerHTML=data.items.length?`<div class="table-wrap"><table><thead><tr><th>Symbol</th><th>Instrument</th><th class="numeric">Individual net · T</th><th class="numeric">Trading value · T</th><th class="numeric">Net / value</th><th class="numeric">Buying days</th><th class="numeric">Observed days</th></tr></thead><tbody>${data.items.map(r=>`<tr><td class="symbol-cell"><button class="symbol-button" data-symbol="${esc(r.symbol)}">${esc(r.symbol)}</button></td><td class="company-cell" title="${esc(r.company)}">${esc(r.company)}</td><td class="numeric flow-cell ${cls(r.net_rial)}">${signed(r.net_rial,3)}</td><td class="numeric">${amount(r.turnover_rial,3)}</td><td class="numeric ratio-cell ${cls(r.net_rial)}">${pct(r.flow_ratio)}<br><svg width="65" height="4" class="ratio-track" aria-hidden="true"><rect width="65" height="4" fill="#edf1f7"/><rect width="${Math.min(65,Math.abs(r.flow_ratio||0)*65)}" height="4" fill="${r.net_rial>=0?'#137465':'#ac493d'}"/></svg></td><td class="numeric">${r.positive_days} / ${r.observed_days}</td><td class="numeric">${r.observed_days}</td></tr>`).join('')}</tbody></table></div>${pagination(data.total,state.flows.page,25,'flow')}`:empty('No matching symbols','Try another name, reduce minimum trading value, or choose a wider period.');
 }catch(error){if(version===flowVersion&&$('#flow-results'))$('#flow-results').innerHTML=empty('Symbol flows could not load',error.message);}
 finally{if(version===flowVersion&&$('#flow-results'))$('#flow-results').removeAttribute('aria-busy');}
}
async function renderResearch(view,version){
 const data=await api('/api/overview',scopeQuery());if(version!==routeVersion)return;
 state.overview=data;updateStatus(data.status);state.selected=Math.max(0,data.days.length-1);
 const title=view==='overview'?'Market overview':'Symbol explorer';
 const description=view==='overview'?'Trading activity and ownership transfers, with the original reports one click away.':'Find persistent buying, compare net transfers, and inspect the history behind a symbol.';
 content.innerHTML=heading(title,description,exportButton('/api/export/daily'))+filters(data.scope);
 if(!data.days.length){content.insertAdjacentHTML('beforeend',`<section class="panel">${empty('No validated reports in this period','Choose another date range. Downloaded reports with analysis issues remain available in the report library.')}</section>`);bindScope();return;}
 if(view==='overview')content.insertAdjacentHTML('beforeend',metrics(data)+chartPanel());
 content.insertAdjacentHTML('beforeend',flowShell()+'<div id="symbol-detail" class="symbol-detail"></div>');
 bindScope();bindFlows();
 if(view==='overview'){renderInspector();drawChart('#main-chart',data.days,state.chart,true);
  $('#report-scrubber').addEventListener('input',event=>{state.selected=Number(event.target.value);renderInspector();drawChart('#main-chart',state.overview.days,state.chart,true);});}
 await loadFlows();
 if(state.symbol&&view==='symbols')await loadSymbol(state.symbol);
}
function bindScope(){const form=$('#scope-form');if(!form)return;
 $('#window').addEventListener('change',event=>{const old=state.overview?.scope;state.window=event.target.value;state.flows.page=1;if(state.window==='custom'){state.start=old?.start||'';state.end=old?.end||'';}navigate();});
 form.addEventListener('submit',event=>{event.preventDefault();const data=new FormData(form);const start=String(data.get('start')||''),end=String(data.get('end')||'');if(start&&end&&start>end){showError('The start date must be before the end date. Adjust the dates and apply again.');return;}state.start=start;state.end=end;state.flows.page=1;navigate();});
}
function bindFlows(){const form=$('#flow-form');
 const apply=()=>{const data=new FormData(form);for(const key of ['q','direction','minimum','sort'])state.flows[key]=String(data.get(key)||'');state.flows.page=1;loadFlows();};
 form.addEventListener('submit',event=>{event.preventDefault();clearTimeout(debounceTimer);apply();});
 form.addEventListener('change',event=>{if(event.target.name!=='q')apply();});
 $('#symbol-search').addEventListener('input',()=>{clearTimeout(debounceTimer);debounceTimer=setTimeout(apply,280);});
}
async function loadSymbol(symbol){
 const version=++symbolVersion;state.symbol=symbol;const holder=$('#symbol-detail');if(!holder)return;
 holder.innerHTML=`<section class="panel">${loading('Loading '+symbol+' history…')}</section>`;
 try{const data=await api('/api/symbol',{...scopeQuery(),symbol});if(version!==symbolVersion||!$('#symbol-detail'))return;
 if(!data.days.length){holder.innerHTML=`<section class="panel">${empty('No history in this period','This exact symbol has no observations in the selected reports.')}</section>`;return;}
 holder.innerHTML=`<section class="panel"><div class="detail-head"><div class="detail-title"><h2 dir="rtl">${esc(data.symbol)}</h2><p dir="rtl">${esc(data.company)}</p></div><button class="button secondary small" data-action="close-symbol">Close history</button></div>
 <div class="detail-stats"><div><span>Individual net · trillion toman</span><strong class="${cls(data.net_rial)}">${signed(data.net_rial,3)}</strong></div><div><span>Trading value · trillion toman</span><strong>${amount(data.turnover_rial,3)}</strong></div><div><span>Net buying days</span><strong>${data.positive_days} / ${data.days.length}</strong></div><div><span>Observed / selected reports</span><strong>${data.days.length} / ${data.scope.reports}</strong></div></div>
 <div class="chart-meta"><span>Daily individual net purchases · trillion toman</span></div><div id="symbol-chart" class="chart-box detail-chart"></div>
 <div class="table-wrap details-overflow"><table><thead><tr><th>Report date</th><th class="numeric">Individual net · T</th><th class="numeric">Buy share</th><th class="numeric">Sell share</th><th class="numeric">Individual buy VWAP · rial</th><th class="numeric">Institution buy VWAP · rial</th><th>Source</th></tr></thead><tbody>${[...data.days].reverse().map(d=>`<tr><td>${esc(d.date)}</td><td class="numeric ${cls(d.retail_net_rial)}">${signed(d.retail_net_rial,4)}</td><td class="numeric">${pct(d.retail_buy_value_share)}</td><td class="numeric">${pct(d.retail_sell_value_share)}</td><td class="numeric">${d.retail_buy_vwap_rial==null?'—':num(d.retail_buy_vwap_rial,1)}</td><td class="numeric">${d.institutional_buy_vwap_rial==null?'—':num(d.institutional_buy_vwap_rial,1)}</td><td><a href="/api/files/${encodeURIComponent(d.sha)}">Excel</a></td></tr>`).join('')}</tbody></table></div></section>
 <p class="table-note">VWAP is purchase value ÷ purchased volume. Missing investor-category purchases have no VWAP. Exact labels are not joined across renames or suffixes.</p>`;
 state.symbolData=data;drawChart('#symbol-chart',data.days,'net');holder.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});
 }catch(error){if(version===symbolVersion)holder.innerHTML=`<section class="panel">${empty('Symbol history could not load',error.message)}</section>`;}
}
async function renderReports(version){
 content.innerHTML=heading('Report library','Browse the downloaded archive, inspect validation status, and open the original Excel files.')+
 `<p class="report-library-note">One file per unique workbook. Revisions stay available; charts use the latest validated revision for each date.</p>
 <form id="report-form" class="filters report-search"><div class="field search"><label for="report-search">Find a report</label><input id="report-search" name="q" type="search" value="${esc(state.reports.q)}" placeholder="Search by date, title, or filename"></div><div class="field"><label for="report-state">Analysis status</label><select id="report-state" name="state">${[['','All files'],['ready','Validated'],['warning','Validation warning'],['unsupported','Analysis unavailable']].map(([v,t])=>`<option value="${v}" ${state.reports.state===v?'selected':''}>${t}</option>`).join('')}</select></div><button type="submit" class="button">Search reports</button></form><section class="panel" id="report-results">${loading()}</section>`;
 $('#report-form').addEventListener('submit',event=>{event.preventDefault();const data=new FormData(event.target);state.reports.q=String(data.get('q')||'');state.reports.state=String(data.get('state')||'');state.reports.page=1;loadReports();});
 $('#report-state').addEventListener('change',()=>$('#report-form').requestSubmit());
 $('#report-search').addEventListener('input',()=>{clearTimeout(debounceTimer);debounceTimer=setTimeout(()=>$('#report-form')?.requestSubmit(),300);});
 await loadReports();
}
function reportDiagnostics(r){
 const issues=JSON.parse(r.issues||'[]');
 const notes=r.normalizations||[];
 const layouts=r.layouts||[];
 if(!issues.length&&!notes.length&&!layouts.length)return '';
 return `<details class="report-diagnostics"><summary>Layout & validation details${issues.length?' · '+integer(issues.length)+' issues':''}</summary>
 ${issues.length?`<p>Excluded from analytics until the source discrepancies are resolved.</p><ul>${issues.map(t=>`<li dir="auto">${esc(t)}</li>`).join('')}</ul>`:''}
 ${notes.length?`<ul>${notes.map(t=>`<li dir="auto">${esc(t)}</li>`).join('')}</ul>`:''}
 ${layouts.map(l=>`<p><strong>${l.measure==='volume'?'Volume':'Value'}</strong> · <bdi>${esc(l.sheet)}</bdi><br>Symbol: ${esc(l.symbol_column)} · Company: ${esc(l.company_column||'absent')} · Data starts at row ${integer(l.data_start_row)}<br>${Object.entries(l.columns).map(([key,col])=>esc(key.replaceAll('_',' '))+': '+esc(col)).join(' · ')}</p>`).join('')}</details>`;
}
async function loadReports(){const version=++reportVersion;if(!$('#report-results'))return;
 try{const data=await api('/api/reports',{...state.reports,size:20});if(version!==reportVersion||!$('#report-results'))return;
 $('#report-results').innerHTML=data.items.length?`<div class="table-wrap"><table><thead><tr><th>Workbook</th><th>Report date</th><th>Analysis status</th><th>Published</th><th class="numeric">File size</th><th>Downloads & source</th></tr></thead><tbody>${data.items.map(r=>`<tr><td><span class="file-name">${esc(r.source_name)}</span><span class="file-sub">Report #${r.report_id}${r.state==='ready'&&!r.active?' · Alternate revision':''}</span>${r.state!=='ready'?`<div class="error-details">${esc(r.error||JSON.parse(r.issues||'[]').slice(0,2).join('; '))}</div>`:''}${reportDiagnostics(r)}</td><td>${esc(r.date||'Not extracted')}${!r.date&&r.effective_date?'<br><span class="file-sub">'+esc(r.effective_date.slice(0,10))+' · Gregorian</span>':''}</td><td><span class="badge ${esc(r.state)}">${r.state==='ready'?'Validated':r.state==='warning'?'Check source':'Analysis unavailable'}</span></td><td>${esc(r.published_at?.slice(0,10)||'—')}<br><span class="file-sub">Gregorian date</span></td><td class="numeric">${bytes(r.bytes)}</td><td><div class="file-actions"><a class="button secondary" href="/api/files/${encodeURIComponent(r.sha)}">${icons.download}Excel</a><a href="${esc(r.detail_url)}" target="_blank" rel="noreferrer">TSE source ↗</a></div></td></tr>`).join('')}</tbody></table></div>${pagination(data.total,state.reports.page,20,'report')}`:empty('No matching reports','Try a different date or clear the analysis-status filter.');
 }catch(error){if(version===reportVersion&&$('#report-results'))$('#report-results').innerHTML=empty('Reports could not load',error.message);}
}
function renderMethodology(status){const c=status.counts,d=status.download;
 content.innerHTML=heading('Data & methodology','Know what the reports measure, what the archive contains, and where the analysis stops.')+
 `<div class="method-layout"><article class="panel prose"><h2>Ownership transfers, with a source trail</h2><p>These are the TSE’s daily “خلاصه عملکرد بازار” reports. They split purchase and sale value and volume between individuals (حقیقی) and institutions (حقوقی), with detailed rows for each exact symbol.</p>
 <div class="formula">Individual net purchases = individual purchase value − individual sale value</div>
 <p>A positive number means ownership moved toward individuals. Institutions were net sellers by the same amount. This is a transfer between investors, not a measure of fresh cash entering the exchange.</p>
 <h2>Keep the scope consistent</h2><p>The detailed tables contain a mixture of shares, funds, and other instruments. The summary’s “shares and rights” percentages have a narrower apparent scope. This app calculates totals directly from the complete detailed tables; it does not multiply the summary percentages by the overall total.</p>
 <p>All displayed “T” values are <strong>trillion toman</strong>. The source files and CSV columns marked “rial” retain rial units: 10 rials = 1 toman, and 10¹³ rials = 1 trillion toman. Web charts use numeric approximations; the original workbook is authoritative.</p>
 <h2>Reading different workbook layouts</h2><p>Investor roles, buy/sell groups, and value/volume columns are matched by their headers, including Persian and Arabic letter variants. Column positions and investor order may change. Missing required amounts are never treated as zero. Ambiguous layouts stay excluded; company names are optional. The report library’s layout details show the interpreted columns, adjustments, and all validation issues.</p><h2>Validation before aggregation</h2><ul><li>Individual and institutional purchases must equal combined sales in both value and volume.</li><li>Extracted instrument rows must reproduce the workbook’s total trading value and volume.</li><li>Hidden sheets that duplicate the report are not counted again.</li><li>Workbooks with warnings or unsupported layouts stay downloadable and are excluded from charts.</li><li>Only one validated revision per report date enters the analysis. Older revisions remain in the library.</li></ul>
 <h2>History without accidental duplication</h2><p>The downloader scans every available category page. Report and attachment IDs remove repeated listings; SHA-256 hashes prevent storing identical workbooks twice. Existing file IDs are reused on the next refresh. Successful files and progress are saved after each attachment, so an interrupted refresh can resume.</p>
 <p>Exact symbol suffixes are kept separate. Renamed symbols are not automatically joined. Buying-day counts use observed reports only; a missing symbol is not an assumed zero.</p>
 <h2>What you cannot conclude from these files</h2><p>Net buying does not establish future returns. This dataset has no complete return series, valuation history, sector mapping, investor counts, or order-book sequence. Per-investor “buying power” cannot be calculated without investor counts. A fund’s institutional counterparty may be its market maker.</p>
 <p>Reports may be published after their trading date. Publication dates must be respected in any historical strategy test. These accounting checks establish internal consistency, not independent verification of the underlying trades.</p>
 <a class="button secondary" href="https://www.tse.ir/download-center" target="_blank" rel="noreferrer">Open the TSE download center ↗</a></article>
 <aside><section class="panel health"><h2>Archive coverage</h2><dl><div><dt>Source report entries</dt><dd>${integer(status.catalog_reports)}</dd></div><div><dt>Unique files downloaded</dt><dd>${integer(status.downloaded_files)}</dd></div><div><dt>Files indexed</dt><dd>${integer(c.indexed)}</dd></div><div><dt>Validated report dates</dt><dd>${integer(c.reports)}</dd></div><div><dt>Validation warnings</dt><dd>${integer(c.warning)}</dd></div><div><dt>Analysis unavailable</dt><dd>${integer(c.unsupported)}</dd></div><div><dt>Download errors</dt><dd>${integer(status.errors.length)}</dd></div></dl><p>Validated coverage: ${esc(c.first_date||'—')} to ${esc(c.last_date||'—')}.</p><p>Download: ${esc(d.phase||'not started')}. ${integer(d.processed)} / ${integer(d.attachments_total)} Excel attachments processed. ${integer(d.pages_scanned)} / ${integer(d.pages_total)} source pages scanned.</p><button class="button" data-action="sync">Update entire archive</button></section>
 <section class="panel health section-gap"><h2>Files needing attention</h2>${status.issues.length||status.errors.length?`<ul class="issues-list">${status.issues.slice(0,12).map(r=>`<li><strong>${esc(r.source_name)}</strong><p>${esc(r.error||JSON.parse(r.issues||'[]').slice(0,2).join('; '))}</p><a href="/api/files/${encodeURIComponent(r.sha)}">Download original</a></li>`).join('')}${status.errors.slice(0,8).map(r=>`<li><strong>${r.page?'Source page '+r.page:'Report '+r.report_id}</strong><p>${esc(r.error)}</p></li>`).join('')}</ul><a class="button link" href="#reports">Review all files</a>`:'<p>All indexed workbooks passed the current accounting checks. Download and indexing progress are reported separately.</p>'}</section></aside></div>`;
}
function updateStatus(status){state.status=status;const c=status.counts,d=status.download;
 $('#nav-count').textContent=integer(status.downloaded_files);
 const busy=['catalog','downloading'].includes(d.phase)||status.sync_running;
 const archive=$('#archive-state');archive.textContent=busy?'Updating · '+integer(d.processed)+' / '+integer(d.attachments_total):integer(c.reports)+' validated reports';archive.classList.toggle('busy',busy);
 const button=$('#sync-button');button.disabled=busy;button.title=busy?'An archive refresh is already running.':'Scan every page and download new files';
 const notice=$('#notice');
 if(busy){notice.innerHTML=`The archive is updating in the background. ${integer(status.downloaded_files)} unique workbooks downloaded; ${integer(c.reports)} report dates ready to explore. You can keep browsing.`;notice.hidden=false;}
 else if(Number(c.indexed)<Number(status.downloaded_files)){notice.textContent='Indexing downloaded workbooks. Newly validated reports will become available as indexing completes.';notice.hidden=false;}
 else if(state.overview&&state.view!=='reports'&&state.view!=='methodology'&&state.overview.dates.length!==c.reports){notice.innerHTML='More reports are ready. <button data-action="reload">Refresh this view</button>';notice.hidden=false;}
 else if(Number(c.warning)||Number(c.unsupported)){notice.innerHTML=`Charts use validated reports only. ${integer(c.warning)} files have reconciliation warnings and ${integer(c.unsupported)} cannot be fully analyzed. All originals remain in the <a href="#reports">report library</a>. <a href="#methodology">View data status</a>.`;notice.hidden=false;}
 else notice.hidden=true;
}
async function startSync(){try{const data=await api('/api/sync',{}, {method:'POST',headers:{'X-TSE-Request':'sync'}});toast(data.message);$('#sync-button').disabled=true;setTimeout(pollStatus,800);}catch(error){showError(error.message);}}
async function pollStatus(){try{const s=await api('/api/status');updateStatus(s);}catch{/* Existing data stays readable during a transient status failure. */}}
async function navigate(){const version=++routeVersion;++flowVersion;++reportVersion;++symbolVersion;clearTimeout(debounceTimer);showError('');
 const hash=location.hash.slice(1),[viewName,query='']=hash.split('?');state.view=['overview','reports','symbols','methodology'].includes(viewName)?viewName:'overview';
 if(state.view==='symbols')state.symbol=new URLSearchParams(query).get('symbol')||'';
 document.querySelectorAll('[data-nav]').forEach(el=>{if(el.dataset.nav===state.view)el.setAttribute('aria-current','page');else el.removeAttribute('aria-current');});
 const names={overview:'Overview',reports:'Report library',symbols:'Symbol explorer',methodology:'Data & methodology'};$('#breadcrumb').textContent='Research / '+names[state.view];document.title=names[state.view]+' · TSE Market Archive';
 content.innerHTML=loading();
 try{if(state.view==='reports')await renderReports(version);else if(state.view==='methodology'){const s=await api('/api/status');if(version!==routeVersion)return;updateStatus(s);renderMethodology(s);}else await renderResearch(state.view,version);}
 catch(error){if(version===routeVersion){content.innerHTML=empty('This view could not load','Check that the Python server is running, then try again.')+'<button class="button" data-action="reset-view">Reset filters and try again</button>';showError(error.message);}}
}
content.addEventListener('click',event=>{
 const symbol=event.target.closest('[data-symbol]');if(symbol){const value=symbol.dataset.symbol;if(state.view==='symbols'){state.symbol=value;history.replaceState(null,'','#symbols?symbol='+encodeURIComponent(value));loadSymbol(value);}else location.hash='symbols?symbol='+encodeURIComponent(value);return;}
 const page=event.target.closest('[data-page-type]');if(page){if(page.dataset.pageType==='flow'){state.flows.page=Number(page.dataset.page);loadFlows();}else{state.reports.page=Number(page.dataset.page);loadReports();}return;}
 const tab=event.target.closest('[data-chart]');if(tab){state.chart=tab.dataset.chart;document.querySelectorAll('[data-chart]').forEach(b=>b.setAttribute('aria-selected',b===tab?'true':'false'));drawChart('#main-chart',state.overview.days,state.chart,true);return;}
 const action=event.target.closest('[data-action]')?.dataset.action;
 if(action==='close-symbol'){state.symbol='';state.symbolData=null;history.replaceState(null,'','#symbols');$('#symbol-detail').innerHTML='';}
 if(action==='sync')startSync();
 if(action==='reset-view'){state.window='20';state.start='';state.end='';navigate();}
});
$('#sync-button').addEventListener('click',startSync);
$('#notice').addEventListener('click',event=>{if(event.target.closest('[data-action="reload"]'))navigate();});
window.addEventListener('hashchange',navigate);
let resizeFrame;
window.addEventListener('resize',()=>{cancelAnimationFrame(resizeFrame);resizeFrame=requestAnimationFrame(()=>{if(state.view==='overview'&&state.overview?.days.length)drawChart('#main-chart',state.overview.days,state.chart,true);if(state.symbolData?.days.length)drawChart('#symbol-chart',state.symbolData.days,'net');});});
navigate();setInterval(pollStatus,8000);
