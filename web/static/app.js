'use strict';
const $ = (selector, root = document) => root.querySelector(selector);
const content = $('#content');
const state = {market:'tse',view:'overview', window:'20', start:'', end:'', chart:'net', selected:0, overview:null,
  symbolData:null, symbolChart:'both', flows:{q:'',direction:'all',minimum:'0',sort:'net_desc',page:1}, reports:{q:'',state:'',page:1}, symbol:'', status:null};
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
function price(value){return value==null?'—':num(value,1);}
function bytes(value){return num(Number(value)/1048576,1)+' MB';}
function scopeQuery(){return state.window==='custom'?{window:'all',start:state.start,end:state.end}:{window:state.window};}
function route(view){return '#'+(state.market==='ifb'?'ifb-':'')+view;}
function fileUrl(sha){return '/api/'+(state.market==='ifb'?'ifb/':'')+'files/'+encodeURIComponent(sha);}
function url(path,query={}){if(state.market==='ifb'&&path.startsWith('/api/'))path=path.replace('/api/','/api/ifb/');return path+'?'+new URLSearchParams(query).toString();}
async function api(path,query={},options={}){
 const response=await fetch(url(path,query),options);
 if(response.status===401){location.assign('/login');throw new Error('Please sign in.');}
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
 return `<div class="scope-note"><span>All reported instruments · Values in trillion toman${data.days.some(d=>d.partial)?' · Includes partial report totals':''}</span><span>${esc(data.scope.start||'—')} — ${esc(data.scope.end||'—')}</span></div>
 <div class="metrics">
 <div class="metric"><span class="metric-label">Individual net purchases</span><span class="metric-value ${cls(a.net_rial)}">${signed(a.net_rial)}<small>T</small></span><span class="metric-note">Ownership transfer over selection</span></div>
 <div class="metric"><span class="metric-label">Average daily trading value</span><span class="metric-value">${amount(a.average_turnover_rial)}<small>T</small></span><span class="metric-note">${integer(data.scope.reports)} selected daily reports</span></div>
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
 $('#inspector').innerHTML=`<h3>Selected report</h3>${d.partial?'<p class="table-note">Partial report: totals cover retained rows only. See source exclusions in the report library.</p>':''}<div class="inspector-date">${esc(d.date)}</div><dl>
 <div><dt>Individual net</dt><dd class="${cls(d.retail_net_rial)}">${signed(d.retail_net_rial)} T</dd></div>
 <div><dt>Trading value</dt><dd>${amount(d.turnover_rial)} T</dd></div>
 <div><dt>Instrument rows</dt><dd>${integer(d.symbols)}${d.partial?' · partial':''}</dd></div></dl>
 <div class="breadth" aria-label="Ownership flow breadth"><span id="breadth-buy"></span><span class="sell" id="breadth-sell"></span></div>
 <div class="breadth-caption">${integer(d.retail_net_positive_symbols)} net buying · ${integer(d.retail_net_negative_symbols)} net selling<br>${integer(d.retail_net_zero_symbols)} unchanged rows</div>
 <a class="button secondary" href="${fileUrl(d.sha)}">${icons.download}Original Excel</a>`;
 $('#breadth-buy').style.width=(total?d.retail_net_positive_symbols/total*100:0)+'%';
 $('#breadth-sell').style.width=(total?d.retail_net_negative_symbols/total*100:0)+'%';
 $('#scrubber-date').textContent=d.date;$('#report-scrubber').value=state.selected;
 $('#report-scrubber').setAttribute('aria-valuetext',d.date+', individual net purchases '+signed(d.retail_net_rial)+' trillion toman');
}
function drawChart(target,days,metric='net',interactive=false){
 const el=$(target);if(!el)return;
 if(interactive){const legend=$('.chart-meta .legend');if(legend)legend.innerHTML=metric==='net'?'<span><i></i>Individual net buying</span><span><i class="sell"></i>Net selling</span>':metric==='cumulative'?'<span><i class="series"></i>Cumulative individual net</span>':'<span><i class="series"></i>Reported trading value</span>';}
 if(!days.length){el.innerHTML=empty('No observations','Choose another period.');return;}
 const combined=metric==='both',isPrice=metric==='price',unit=isPrice?'rial':'trillion toman';
 let running=0;
 const points=days.map(d=>{const net=Number(d.retail_net_rial);running+=net;return {date:d.date,value:isPrice?(d.average_price_rial==null?null:Number(d.average_price_rial)):(metric==='cumulative'?running:metric==='turnover'?Number(d.turnover_rial):net)/1e13};});
 const valid=points.filter(p=>p.value!=null&&Number.isFinite(p.value));
 if(!valid.length){el.innerHTML=empty('No average prices available','Prices require valid trading value and positive volume.');return;}
 const width=Math.max(260,el.clientWidth),height=240,left=isPrice?85:48,right=combined?85:15,top=18,bottom=30,w=width-left-right,h=height-top-bottom;
 let min=Math.min(0,...valid.map(p=>p.value)),max=Math.max(0,...valid.map(p=>p.value));
 if(max===min){max+=1;min-=1;}const pad=(max-min)*.12;max+=pad;if(min<0)min-=pad;
 const x=i=>left+(i+.5)/points.length*w,y=v=>top+(max-v)/(max-min)*h;
 let svg=`<svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" role="img" aria-label="${esc(combined?'Daily individual net purchases in trillion toman and average traded price in rial':isPrice?'Daily average traded price':metric==='turnover'?'Daily trading value':metric==='cumulative'?'Cumulative individual net purchases':'Daily individual net purchases')}, ${esc(points[0].date)} to ${esc(points.at(-1).date)}, in ${unit}">`;
 for(let i=0;i<=4;i++){const value=max-(max-min)*i/4,py=y(value);svg+=`<line class="chart-grid" x1="${left}" x2="${width-right}" y1="${py}" y2="${py}"/><text x="${left-10}" y="${py+4}" text-anchor="end">${num(value,Math.max(Math.abs(max),Math.abs(min))<1?2:1)}</text>`;}
 svg+=`<line class="zero" x1="${left}" x2="${width-right}" y1="${y(0)}" y2="${y(0)}"/>`;
 if(metric==='cumulative'||isPrice){
  let connected=false;
  const path=points.map((p,i)=>{if(p.value==null){connected=false;return '';}const segment=(connected?'L':'M')+x(i)+','+y(p.value);connected=true;return segment;}).join(' ');
  svg+=`<path d="${path}" fill="none" stroke="var(--blue)" stroke-width="2.4" vector-effect="non-scaling-stroke"/>`;
  if(isPrice)points.forEach((p,i)=>{if(p.value!=null)svg+=`<circle cx="${x(i)}" cy="${y(p.value)}" r="3" fill="var(--blue)"><title>${esc(p.date)}: ${price(p.value)} rial</title></circle>`;});
  if(!isPrice&&points.length===1)svg+=`<circle cx="${x(0)}" cy="${y(points[0].value)}" r="4" fill="var(--blue)"/>`;
 }else{
  const bw=Math.max(.6,Math.min(23,w/points.length*.64));
  points.forEach((p,i)=>svg+=`<rect x="${x(i)-bw/2}" y="${Math.min(y(0),y(p.value))}" width="${bw}" height="${Math.max(.8,Math.abs(y(0)-y(p.value)))}" rx="${Math.min(2,bw/3)}" fill="${metric==='turnover'?'var(--blue)':p.value>=0?'#298e7d':'#c26b5e'}"><title>${esc(p.date)}: ${num(p.value,3)} trillion toman</title></rect>`);
 }
 if(combined){
  const prices=days.map(d=>d.average_price_rial==null?null:Number(d.average_price_rial));
  const validPrices=prices.filter(v=>v!=null&&Number.isFinite(v));
  if(validPrices.length){
   let low=Math.min(...validPrices),high=Math.max(...validPrices);
   const padding=(high-low)*.12||Math.max(1,high*.05);low=Math.max(0,low-padding);high+=padding;
   const py=v=>top+(high-v)/(high-low)*h;
   svg+=`<text x="${width-right+10}" y="12" fill="var(--blue)">rial</text>`;
   for(let i=0;i<=4;i++){const value=high-(high-low)*i/4;svg+=`<text x="${width-right+10}" y="${top+h*i/4+4}" fill="var(--blue)">${num(value,1)}</text>`;}
   let connected=false;
   const path=prices.map((v,i)=>{if(v==null||!Number.isFinite(v)){connected=false;return '';}const segment=(connected?'L':'M')+x(i)+','+py(v);connected=true;return segment;}).join(' ');
   svg+=`<path d="${path}" fill="none" stroke="var(--blue)" stroke-width="2.4" vector-effect="non-scaling-stroke"/>`;
   prices.forEach((v,i)=>{if(v!=null&&Number.isFinite(v))svg+=`<circle cx="${x(i)}" cy="${py(v)}" r="3" fill="var(--blue)"><title>${esc(days[i].date)}: ${price(v)} rial</title></circle>`;});
  }else svg+=`<text x="${left+w/2}" y="14" text-anchor="middle">Average prices unavailable</text>`;
  svg+=`<text x="${left-10}" y="12" text-anchor="end">T</text>`;
 }
 const labels=[0,Math.floor((points.length-1)/2),points.length-1].filter((n,i,a)=>a.indexOf(n)===i);
 labels.forEach(i=>svg+=`<text x="${x(i)}" y="${height-7}" text-anchor="${i===0?'start':i===points.length-1?'end':'middle'}">${esc(points[i].date)}</text>`);
 if(interactive)svg+=`<line class="selection" x1="${x(state.selected)}" x2="${x(state.selected)}" y1="${top}" y2="${height-bottom}"/>`;
 svg+='</svg><div class="chart-tooltip" hidden></div>';el.innerHTML=svg;
 const pick=event=>{const box=$('svg',el).getBoundingClientRect();return Math.max(0,Math.min(points.length-1,Math.floor(((event.clientX-box.left)/box.width*width-left)/w*points.length)));};
 const tip=$('.chart-tooltip',el);
 el.onpointermove=event=>{const index=pick(event),box=el.getBoundingClientRect();tip.innerHTML=`${esc(points[index].date)}<strong>${points[index].value==null?'Unavailable':num(points[index].value,isPrice?1:3)+' '+(isPrice?'rial':'T')}</strong>`;if(combined)tip.innerHTML+=`<strong>Average price: ${days[index].average_price_rial==null?'Unavailable':price(days[index].average_price_rial)+' rial'}</strong>`;tip.hidden=false;tip.style.left=Math.min(Math.max(0,event.clientX-box.left-45),Math.max(0,box.width-140))+'px';};
 el.onpointerleave=()=>tip.hidden=true;
 if(interactive)el.onclick=event=>{state.selected=pick(event);renderInspector();const line=$('.selection',el);line.setAttribute('x1',x(state.selected));line.setAttribute('x2',x(state.selected));};
}
function flowShell(){return `<section class="panel" aria-labelledby="flow-heading"><div class="section-head"><div><h2 id="flow-heading">Symbol flows</h2><p>Compare exact symbols across the selected reports.</p></div><a id="flow-export" class="button secondary small" href="#">${icons.download}Export CSV</a></div>
 <form id="flow-form" class="table-toolbar"><div class="field search"><label for="symbol-search">Symbol or instrument name</label><input type="search" id="symbol-search" name="q" placeholder="Search symbols, e.g. وبملت" value="${esc(state.flows.q)}"></div>
 <div class="field"><label for="direction">Individual flow</label><select name="direction" id="direction">${[['all','All directions'],['buy','Net buying'],['sell','Net selling']].map(([v,t])=>`<option value="${v}" ${state.flows.direction===v?'selected':''}>${t}</option>`).join('')}</select></div>
 <div class="field minimum"><label for="minimum">Min. trading value · T</label><input name="minimum" id="minimum" type="number" min="0" step="0.01" value="${esc(state.flows.minimum)}"></div>
 <div class="field"><label for="flow-sort">Sort by</label><select name="sort" id="flow-sort">${[['net_desc','Largest net buying'],['net_asc','Largest net selling'],['turnover','Trading value'],['ratio','Net / trading value'],['persistence','Buying persistence']].map(([v,t])=>`<option value="${v}" ${state.flows.sort===v?'selected':''}>${t}</option>`).join('')}</select></div><button type="submit" class="sr-only">Apply symbol filters</button></form><div id="flow-results">${loading('Loading symbol flows…')}</div></section>
 <p class="table-note">Average price = total trading value ÷ total volume across the selected reports, in rials. Positive = individuals bought more than they sold; institutions took the opposite side. Exact symbol suffixes are kept separate. Prices use only rows with valid volume. Missing observations are not counted as zero.</p>`;}
function pagination(total,page,size,type){const pages=Math.max(1,Math.ceil(total/size));return `<div class="pagination"><span>${total?integer((page-1)*size+1)+'–'+integer(Math.min(page*size,total))+' of '+integer(total):'0'} ${type==='flow'?'symbols':'workbooks'}</span><div class="pagination-controls"><button class="button secondary small" data-page-type="${type}" data-page="${page-1}" ${page<=1?'disabled':''}>Previous</button><span>${page} / ${pages}</span><button class="button secondary small" data-page-type="${type}" data-page="${page+1}" ${page>=pages?'disabled':''}>Next</button></div></div>`;}
async function loadFlows(){
 const version=++flowVersion;if(!$('#flow-results'))return;
 const query={...scopeQuery(),...state.flows,size:25};$('#flow-export').href=url('/api/export/flows',query);
 $('#flow-results').setAttribute('aria-busy','true');
 try{const data=await api('/api/flows',query);if(version!==flowVersion||!$('#flow-results'))return;
 $('#flow-results').innerHTML=data.items.length?`<div class="table-wrap"><table><thead><tr><th>Symbol</th><th>Instrument</th><th class="numeric">Average price · rial</th><th class="numeric">Individual net · T</th><th class="numeric">Trading value · T</th><th class="numeric">Net / value</th><th class="numeric">Buying days</th><th class="numeric">Observed days</th></tr></thead><tbody>${data.items.map(r=>`<tr><td class="symbol-cell"><button class="symbol-button" data-symbol="${esc(r.symbol)}">${esc(r.symbol)}</button></td><td class="company-cell" title="${esc(r.company)}">${esc(r.company)}</td><td class="numeric">${price(r.average_price_rial)}</td><td class="numeric flow-cell ${cls(r.net_rial)}">${signed(r.net_rial,3)}</td><td class="numeric">${amount(r.turnover_rial,3)}</td><td class="numeric ratio-cell ${cls(r.net_rial)}">${pct(r.flow_ratio)}<br><svg width="65" height="4" class="ratio-track" aria-hidden="true"><rect width="65" height="4" fill="#edf1f7"/><rect width="${Math.min(65,Math.abs(r.flow_ratio||0)*65)}" height="4" fill="${r.net_rial>=0?'#137465':'#ac493d'}"/></svg></td><td class="numeric">${r.positive_days} / ${r.observed_days}</td><td class="numeric">${r.observed_days}${r.partial_days?`<br><span class="file-sub">${r.partial_days} partial reports</span>`:''}</td></tr>`).join('')}</tbody></table></div>${pagination(data.total,state.flows.page,25,'flow')}`:empty('No matching symbols','Try another name, reduce minimum trading value, or choose a wider period.');
 }catch(error){if(version===flowVersion&&$('#flow-results'))$('#flow-results').innerHTML=empty('Symbol flows could not load',error.message);}
 finally{if(version===flowVersion&&$('#flow-results'))$('#flow-results').removeAttribute('aria-busy');}
}
async function renderResearch(view,version){
 const data=await api('/api/overview',scopeQuery());if(version!==routeVersion)return;
 state.overview=data;updateStatus(data.status);state.selected=Math.max(0,data.days.length-1);
 const title=view==='overview'?'Market overview':'Symbol explorer';
 const description=state.market==='ifb'?'Iran Fara Bourse reports only. IFB data is stored and analyzed separately from TSE.':view==='overview'?'Trading activity and ownership transfers, with the original reports one click away.':'Find persistent buying, compare net transfers, and inspect the history behind a symbol.';
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
 <div class="section-head"><h3>Symbol history</h3><div class="tabs" role="tablist" aria-label="Symbol chart metric">${[['both','Both'],['net','Net transfers'],['price','Average price']].map(([key,label])=>`<button role="tab" data-symbol-chart="${key}" aria-selected="${state.symbolChart===key}">${label}</button>`).join('')}</div></div>
 <div class="chart-meta"><span id="symbol-chart-label"></span></div><div id="symbol-chart" class="chart-box detail-chart"></div>
 <div class="table-wrap details-overflow"><table><thead><tr><th>Report date</th><th class="numeric">Average price · rial</th><th class="numeric">Individual net · T</th><th class="numeric">Buy share</th><th class="numeric">Sell share</th>${state.market==='ifb'?'<th class="numeric">Closing price · rial</th><th class="numeric">Last trade · rial</th>':''}<th class="numeric">Individual buy VWAP · rial</th><th class="numeric">Institution buy VWAP · rial</th><th>Source</th></tr></thead><tbody>${[...data.days].reverse().map(d=>`<tr><td>${esc(d.date)}${d.report_state==='partial'?'<br><span class="file-sub">Partial report</span>':''}</td><td class="numeric">${price(d.average_price_rial)}</td><td class="numeric ${cls(d.retail_net_rial)}">${signed(d.retail_net_rial,4)}</td><td class="numeric">${pct(d.retail_buy_value_share)}</td><td class="numeric">${pct(d.retail_sell_value_share)}</td>${state.market==='ifb'?`<td class="numeric">${price(d.closing_price_rial)}</td><td class="numeric">${price(d.last_price_rial)}</td>`:''}<td class="numeric">${d.retail_buy_vwap_rial==null?'—':num(d.retail_buy_vwap_rial,1)}</td><td class="numeric">${d.institutional_buy_vwap_rial==null?'—':num(d.institutional_buy_vwap_rial,1)}</td><td><a href="${fileUrl(d.sha)}">Ownership Excel</a>${d.price_sha?` · <a href="${fileUrl(d.price_sha)}">Price Excel</a>`:''}</td></tr>`).join('')}</tbody></table></div></section>
 <p class="table-note">Average price is total trading value ÷ traded volume for that report; the symbol list uses total value ÷ total volume across the selected period. It is not a closing or latest market price. Zero volume has no average price. VWAP is purchase value ÷ purchased volume. Missing investor-category purchases have no VWAP. Exact labels are not joined across renames or suffixes.</p>`;
 state.symbolData=data;drawSymbolChart();holder.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});
 }catch(error){if(version===symbolVersion)holder.innerHTML=`<section class="panel">${empty('Symbol history could not load',error.message)}</section>`;}
}
function drawSymbolChart(){
 if(!state.symbolData||!$('#symbol-chart'))return;
 $('#symbol-chart-label').textContent=state.symbolChart==='both'?'Bars: individual net · T (left) · Line: average price · rial (right)':state.symbolChart==='price'?'Daily average traded price · rial · gaps indicate unavailable prices':'Daily individual net purchases · trillion toman';
 drawChart('#symbol-chart',state.symbolData.days,state.symbolChart);
}
async function renderReports(version){
 content.innerHTML=heading('Report library','Browse the downloaded archive, inspect validation status, and open the original Excel files.')+
 `<p class="report-library-note">One file per unique workbook. Charts prefer fully validated revisions, then partial reports with retained valid rows. Partial totals cover retained rows only.</p>
 <form id="report-form" class="filters report-search"><div class="field search"><label for="report-search">Find a report</label><input id="report-search" name="q" type="search" value="${esc(state.reports.q)}" placeholder="Search by date, title, or filename"></div><div class="field"><label for="report-state">Analysis status</label><select id="report-state" name="state">${[['','All files'],['ready','Validated'],['partial','Partial · retained valid rows'],['warning','Validation warning'],['unsupported','Analysis unavailable'],...(state.market==='ifb'?[['reference','Price reference']]:[])].map(([v,t])=>`<option value="${v}" ${state.reports.state===v?'selected':''}>${t}</option>`).join('')}</select></div><button type="submit" class="button">Search reports</button></form><section class="panel" id="report-results">${loading()}</section>`;
 $('#report-form').addEventListener('submit',event=>{event.preventDefault();const data=new FormData(event.target);state.reports.q=String(data.get('q')||'');state.reports.state=String(data.get('state')||'');state.reports.page=1;loadReports();});
 $('#report-state').addEventListener('change',()=>$('#report-form').requestSubmit());
 $('#report-search').addEventListener('input',()=>{clearTimeout(debounceTimer);debounceTimer=setTimeout(()=>$('#report-form')?.requestSubmit(),300);});
 await loadReports();
}
async function loadReports(){const version=++reportVersion;if(!$('#report-results'))return;
 try{const data=await api('/api/reports',{...state.reports,size:20});if(version!==reportVersion||!$('#report-results'))return;
 $('#report-results').innerHTML=data.items.length?`<div class="table-wrap"><table><thead><tr><th>Workbook</th><th>Report date</th><th>Analysis status</th><th>Published</th><th class="numeric">File size</th><th>Downloads & source</th></tr></thead><tbody>${data.items.map(r=>`<tr><td><span class="file-name">${esc(r.source_name)}</span><span class="file-sub">Report #${r.report_id}${r.state==='ready'&&!r.active?' · Alternate revision':''}</span>${(r.error||JSON.parse(r.issues||'[]').length)?`<div class="error-details">${esc(r.error||JSON.parse(r.issues||'[]').slice(0,2).join('; '))}<details><summary>Extraction details</summary>${JSON.parse(r.issues||'[]').map(issue=>`<p>${esc(issue)}</p>`).join('')}</details></div>`:''}</td><td>${esc(r.date||'Not extracted')}${!r.date&&r.effective_date?'<br><span class="file-sub">'+esc(r.effective_date.slice(0,10))+' · Gregorian</span>':''}</td><td><span class="badge ${esc(r.state)}">${r.state==='ready'?'Validated':r.state==='reference'?'Price reference':r.state==='partial'?'Partial · valid rows':r.state==='warning'?'Check source':'Analysis unavailable'}</span></td><td>${esc(r.published_at?.slice(0,10)||'—')}<br><span class="file-sub">Gregorian date</span></td><td class="numeric">${bytes(r.bytes)}</td><td><div class="file-actions"><a class="button secondary" href="${fileUrl(r.sha)}">${icons.download}Excel</a><a href="${esc(r.detail_url)}" target="_blank" rel="noreferrer">${state.market.toUpperCase()} source ↗</a></div></td></tr>`).join('')}</tbody></table></div>${pagination(data.total,state.reports.page,20,'report')}`:empty('No matching reports','Try a different date or clear the analysis-status filter.');
 }catch(error){if(version===reportVersion&&$('#report-results'))$('#report-results').innerHTML=empty('Reports could not load',error.message);}
}
function renderMethodology(status){const c=status.counts,d=status.download;
 if(state.market==='ifb'){content.innerHTML=heading('IFB data & methodology','Iran Fara Bourse · independent archive')+`<article class="panel prose"><h2>Separate sources and dates</h2><p>IFB ownership reports provide individual and institutional purchase/sale values, volumes, and investor counts. Price workbooks provide closing and last-trade prices. Price references are joined by exact symbol and report date within IFB only; comparison-period start dates are not trading dates.</p><p>Only single-day ownership reports enter daily analytics. Market and submarket labels are preserved from merged cells. Group totals are excluded from symbol rows. Invalid value rows are excluded, while invalid volume leaves prices unavailable. Blank investor cells in this IFB layout represent zero and are checked against buy/sell balance.</p><p>Average traded price is value ÷ volume in rials. Published average price is a separate source field and can use another methodology. Price files remain reference reports and never count as another ownership session. Missing price references display —.</p><p>${integer(c.reports)} usable IFB dates · ${integer(status.downloaded_files)} archived workbooks. Update status: ${esc(d.phase||'not started')}. ${esc(d.error||'')}</p><a href="https://www.ifb.ir/datareporter/periodicalreport.aspx" target="_blank" rel="noreferrer">Open IFB periodical reports ↗</a></article>`;return;}
 content.innerHTML=heading('Data & methodology','Know what the reports measure, what the archive contains, and where the analysis stops.')+
 `<div class="method-layout"><article class="panel prose"><h2>Ownership transfers, with a source trail</h2><p>These are the TSE’s daily “خلاصه عملکرد بازار” reports. They split purchase and sale value and volume between individuals (حقیقی) and institutions (حقوقی), with detailed rows for each exact symbol.</p>
 <div class="formula">Individual net purchases = individual purchase value − individual sale value</div>
 <p>A positive number means ownership moved toward individuals. Institutions were net sellers by the same amount. This is a transfer between investors, not a measure of fresh cash entering the exchange.</p>
 <h2>Keep the scope consistent</h2><p>The detailed tables contain a mixture of shares, funds, and other instruments. The summary’s “shares and rights” percentages have a narrower apparent scope. This app calculates totals directly from the complete detailed tables; it does not multiply the summary percentages by the overall total.</p>
 <p>All displayed “T” values are <strong>trillion toman</strong>. The source files and CSV columns marked “rial” retain rial units: 10 rials = 1 toman, and 10¹³ rials = 1 trillion toman. Web charts use numeric approximations; the original workbook is authoritative.</p>
 <h2>Validation before aggregation</h2><ul><li>Individual and institutional purchases must equal combined sales in both value and volume.</li><li>Fully validated reports reconcile with published totals. Partial reports keep the reconciliation gap visible.</li><li>Hidden sheets that duplicate the report are not counted again.</li><li>Partial reports retain rows with valid value accounting; invalid value rows are excluded. Invalid or missing volume leaves prices unavailable. Partial chart totals cover retained value rows only, and reconciliation gaps remain visible in the library. Unsupported layouts stay downloadable.</li><li>One revision per report date enters analysis, preferring fully validated reports over partial reports. Older revisions remain in the library.</li></ul>
 <h2>History without accidental duplication</h2><p>The downloader scans every available category page. Report and attachment IDs remove repeated listings; SHA-256 hashes prevent storing identical workbooks twice. Existing file IDs are reused on the next refresh. Successful files and progress are saved after each attachment, so an interrupted refresh can resume.</p>
 <p>Exact symbol suffixes are kept separate. Renamed symbols are not automatically joined. Buying-day counts use observed reports only; a missing symbol is not an assumed zero.</p>
 <h2>What you cannot conclude from these files</h2><p>Net buying does not establish future returns. This dataset has no complete return series, valuation history, sector mapping, investor counts, or order-book sequence. Per-investor “buying power” cannot be calculated without investor counts. A fund’s institutional counterparty may be its market maker.</p>
 <p>Reports may be published after their trading date. Publication dates must be respected in any historical strategy test. These accounting checks establish internal consistency, not independent verification of the underlying trades.</p>
 <a class="button secondary" href="https://www.tse.ir/download-center" target="_blank" rel="noreferrer">Open the TSE download center ↗</a></article>
 <aside><section class="panel health"><h2>Archive coverage</h2><dl><div><dt>Source report entries</dt><dd>${integer(status.catalog_reports)}</dd></div><div><dt>Unique files downloaded</dt><dd>${integer(status.downloaded_files)}</dd></div><div><dt>Files indexed</dt><dd>${integer(c.indexed)}</dd></div><div><dt>Usable report dates</dt><dd>${integer(c.reports)}</dd></div><div><dt>Validation warnings</dt><dd>${integer(c.warning)}</dd></div><div><dt>Analysis unavailable</dt><dd>${integer(c.unsupported)}</dd></div><div><dt>Download errors</dt><dd>${integer(status.errors.length)}</dd></div></dl><p>Usable coverage: ${esc(c.first_date||'—')} to ${esc(c.last_date||'—')}.</p><p>Download: ${esc(d.phase||'not started')}. ${integer(d.processed)} / ${integer(d.attachments_total)} Excel attachments processed. ${integer(d.pages_scanned)} / ${integer(d.pages_total)} source pages scanned.</p><button class="button" data-action="sync">Update entire archive</button></section>
 <section class="panel health section-gap"><h2>Files needing attention</h2>${status.issues.length||status.errors.length?`<ul class="issues-list">${status.issues.slice(0,12).map(r=>`<li><strong>${esc(r.source_name)}</strong><p>${esc(r.error||JSON.parse(r.issues||'[]').slice(0,2).join('; '))}</p><a href="${fileUrl(r.sha)}">Download original</a></li>`).join('')}${status.errors.slice(0,8).map(r=>`<li><strong>${r.page?'Source page '+r.page:'Report '+r.report_id}</strong><p>${esc(r.error)}</p></li>`).join('')}</ul><a class="button link" href="${route('reports')}">Review all files</a>`:'<p>All indexed workbooks passed the current accounting checks. Download and indexing progress are reported separately.</p>'}</section></aside></div>`;
}
function updateStatus(status){state.status=status;const c=status.counts,d=status.download;
 $('#nav-count').textContent=integer(status.downloaded_files);
 const busy=['catalog','downloading'].includes(d.phase)||status.sync_running;
 const archive=$('#archive-state');archive.textContent=busy?'Updating · '+integer(d.processed)+' / '+integer(d.attachments_total):integer(c.reports)+' usable reports';archive.classList.toggle('busy',busy);
 const button=$('#sync-button');button.disabled=busy;button.title=busy?'An archive refresh is already running.':'Scan every page and download new files';
 const notice=$('#notice');
 if(d.phase==='failed'){notice.textContent=(state.market.toUpperCase()+' update failed: '+(d.error||'See methodology for details')+'. Existing reports remain available.');notice.hidden=false;}
 else if(busy){notice.innerHTML=`The archive is updating in the background. ${integer(status.downloaded_files)} unique workbooks downloaded; ${integer(c.reports)} report dates ready to explore. You can keep browsing.`;notice.hidden=false;}
 else if(Number(c.indexed)<Number(status.downloaded_files)){notice.textContent='Indexing downloaded workbooks. Newly validated reports will become available as indexing completes.';notice.hidden=false;}
 else if(state.overview&&state.view!=='reports'&&state.view!=='methodology'&&state.overview.dates.length!==c.reports){notice.innerHTML='More reports are ready. <button data-action="reload">Refresh this view</button>';notice.hidden=false;}
 else if(Number(c.warning)||Number(c.unsupported)){notice.innerHTML=`Charts include partial reports using retained valid rows; partial totals may understate market activity. ${integer(c.warning)} files have partial data or reconciliation warnings and ${integer(c.unsupported)} cannot be fully analyzed. All originals remain in the <a href="${route('reports')}">report library</a>. <a href="${route('methodology')}">View data status</a>.`;notice.hidden=false;}
 else notice.hidden=true;
}
async function startSync(){try{const data=await api('/api/sync',{}, {method:'POST',headers:{'X-TSE-Request':'sync'}});toast(data.message);$('#sync-button').disabled=true;setTimeout(pollStatus,800);}catch(error){showError(error.message);}}
async function pollStatus(){const market=state.market;try{const s=await api('/api/status');if(market===state.market)updateStatus(s);}catch{/* Existing data stays readable during a transient status failure. */}}
async function navigate(){const version=++routeVersion;++flowVersion;++reportVersion;++symbolVersion;clearTimeout(debounceTimer);showError('');
 const hash=location.hash.slice(1),[rawView,query='']=hash.split('?');const market=rawView.startsWith('ifb-')?'ifb':'tse',viewName=rawView.replace(/^ifb-/,'');if(state.market!==market){state.overview=null;state.symbolData=null;state.status=null;state.symbol='';state.flows.page=1;state.reports={q:'',state:'',page:1};state.flows={q:'',direction:'all',minimum:'0',sort:'net_desc',page:1};state.window='20';state.start='';state.end='';}state.market=market;state.view=['overview','reports','symbols','methodology'].includes(viewName)?viewName:'overview';
 if(state.view==='symbols')state.symbol=new URLSearchParams(query).get('symbol')||'';
 document.documentElement.dataset.market=state.market;
 $('#brand-market').textContent=state.market.toUpperCase();$('.brand').href=route('overview');$('.brand').setAttribute('aria-label',state.market.toUpperCase()+' Market Archive home');
 const otherMarket=state.market==='ifb'?'TSE':'IFB';$('#market-switch').innerHTML='Switch to '+otherMarket+' <span aria-hidden="true">⇄</span>';$('#market-switch').setAttribute('aria-label','Switch to '+otherMarket+' market');
 $('meta[name="theme-color"]').content=state.market==='ifb'?'#a52b35':'#2248a5';
 document.querySelectorAll('[data-nav]').forEach(el=>{el.href=route(el.dataset.nav);if(el.dataset.nav===state.view)el.setAttribute('aria-current','page');else el.removeAttribute('aria-current');});
 const names={overview:'Overview',reports:'Report library',symbols:'Symbol explorer',methodology:'Data & methodology'};$('#breadcrumb').textContent=state.market.toUpperCase()+' / '+names[state.view];document.title=names[state.view]+' · '+state.market.toUpperCase()+' Market Archive';$('.source-mark').textContent=state.market.toUpperCase()+' source archive';$('.sidebar-footer a').href=state.market==='ifb'?'https://www.ifb.ir/datareporter/periodicalreport.aspx':'https://www.tse.ir/download-center';$('#sync-button').setAttribute('aria-label','Update '+state.market.toUpperCase()+' archive');$('.page-footer span').textContent=(state.market==='ifb'?'Iran Fara Bourse':'Tehran Securities Exchange')+' · Separate market archive';
 content.innerHTML=loading();
 try{if(state.view==='reports')await renderReports(version);else if(state.view==='methodology'){const s=await api('/api/status');if(version!==routeVersion)return;updateStatus(s);renderMethodology(s);}else await renderResearch(state.view,version);}
 catch(error){if(version===routeVersion){content.innerHTML=empty('This view could not load','Check that the Python server is running, then try again.')+'<button class="button" data-action="reset-view">Reset filters and try again</button>';showError(error.message);}}
}
content.addEventListener('click',event=>{
 const symbol=event.target.closest('[data-symbol]');if(symbol){const value=symbol.dataset.symbol;if(state.view==='symbols'){state.symbol=value;history.replaceState(null,'',route('symbols')+'?symbol='+encodeURIComponent(value));loadSymbol(value);}else location.hash=route('symbols')+'?symbol='+encodeURIComponent(value);return;}
 const page=event.target.closest('[data-page-type]');if(page){if(page.dataset.pageType==='flow'){state.flows.page=Number(page.dataset.page);loadFlows();}else{state.reports.page=Number(page.dataset.page);loadReports();}return;}
 const symbolTab=event.target.closest('[data-symbol-chart]');if(symbolTab){state.symbolChart=symbolTab.dataset.symbolChart;document.querySelectorAll('[data-symbol-chart]').forEach(b=>b.setAttribute('aria-selected',b===symbolTab?'true':'false'));drawSymbolChart();return;}
 const tab=event.target.closest('[data-chart]');if(tab){state.chart=tab.dataset.chart;document.querySelectorAll('[data-chart]').forEach(b=>b.setAttribute('aria-selected',b===tab?'true':'false'));drawChart('#main-chart',state.overview.days,state.chart,true);return;}
 const action=event.target.closest('[data-action]')?.dataset.action;
 if(action==='close-symbol'){state.symbol='';state.symbolData=null;history.replaceState(null,'',route('symbols'));$('#symbol-detail').innerHTML='';}
 if(action==='sync')startSync();
 if(action==='reset-view'){state.window='20';state.start='';state.end='';navigate();}
});
$('#market-switch').addEventListener('click',()=>{location.hash='#'+(state.market==='tse'?'ifb-':'')+state.view;});
$('#sync-button').addEventListener('click',startSync);
$('#notice').addEventListener('click',event=>{if(event.target.closest('[data-action="reload"]'))navigate();});
window.addEventListener('hashchange',navigate);
let resizeFrame;
window.addEventListener('resize',()=>{cancelAnimationFrame(resizeFrame);resizeFrame=requestAnimationFrame(()=>{if(state.view==='overview'&&state.overview?.days.length)drawChart('#main-chart',state.overview.days,state.chart,true);if(state.symbolData?.days.length)drawSymbolChart();});});
navigate();setInterval(pollStatus,8000);
