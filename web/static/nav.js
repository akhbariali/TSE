'use strict';
let navDocument;
async function navRequest(options={}){
 const response=await fetch('/api/nav',options);
 if(response.status===401){location.assign('/login');throw new Error('Please sign in.');}
 const data=await response.json();if(!response.ok)throw new Error(data.error||'Portfolio could not load.');return data;
}
async function renderNav(version){
 if(location.pathname!=='/nav/manage'){
  const response=await fetch('/api/nav/balances');
  if(response.status===401){location.assign('/login');return;}
  const data=await response.json();if(!response.ok)throw new Error(data.error||'Balances could not load.');
  if(version===routeVersion)content.innerHTML=balancePage(data);return;
 }
 const data=await navRequest();if(version!==routeVersion)return;navDocument=data;drawNav();
}
function balancePage(data){
 const money=value=>value==null?'Not calculated yet':num(value,2)+' tomans';
 return heading('Investor balances','Current money belonging to each investor')+
 (data.people.length?data.people.map(person=>`<section class="panel investor-balance">
 <h2>${esc(person.person)}</h2><p class="balance-label">Money now</p>
 <strong class="balance-amount">${money(person.value)}</strong>
 ${person.value==null?'<p class="balance-explanation">The current balance is not confirmed yet. The recorded contribution below is the starting investment, not today’s balance.</p>':`<p class="balance-explanation">As of ${esc(data.as_of)}. This is the latest saved valuation.</p>`}
 <dl class="balance-breakdown"><div><dt>Net money invested</dt><dd>${money(person.net_contributed)}</dd></div><div><dt>Profit / loss</dt><dd class="${cls(person.profit)}">${money(person.profit)}</dd></div></dl>
 ${person.value!=null?'<p class="table-note">Money now = net money invested + profit / loss.</p>':'<p class="table-note">The calculation needs the shared cash balance and later contributions to be completed.</p>'}
 </section>`).join(''):empty('No investor balances','No other investors have been recorded.'));
}
function drawNav(){
 const b=navDocument.book,r=navDocument.result;
 const money=v=>v==null?'Pending':num(v,2);
 const input=(label,value,key,type='text')=>`<input aria-label="${esc(label)}" data-key="${key}" type="${type}" ${type==='number'?'step="any"':''} value="${esc(value)}">`;
 content.innerHTML=heading('Manage calculation','Owner workspace · contains your private portfolio details', '<a class="button secondary" href="/nav">View investor balances</a>')+`
 <div class="metrics">${[['Shared net assets',money(r.nav)],['NAV per unit',money(r.unit_price)],['Included holdings',money(r.included)],['Personal holdings excluded',money(r.excluded)]].map(([label,value])=>`<div class="metric"><span class="metric-label">${label}</span><strong class="metric-value nav-value">${value}</strong></div>`).join('')}</div>
 ${!r.ready?'<p class="notice">Profit is pending: reconcile shared cash, later contributions, and the valuation date, then confirm the valuation below. Unit shares reflect only the recorded ledger; unrecorded contributions will change them.</p>':''}
 <section class="panel"><div class="section-head"><div><h2>Each person’s share</h2><p>Current value − net contributions = lifetime profit (withdrawals are already deducted from net contributions).</p></div></div>
 <div class="table-wrap"><table><thead><tr><th>Person</th><th class="numeric">Net contributions</th><th class="numeric">Units</th><th class="numeric">Recorded unit share</th><th class="numeric">Current value</th><th class="numeric">Profit / loss</th></tr></thead><tbody>${r.people.map(p=>`<tr><td>${esc(p.person)}</td><td class="numeric">${money(p.net_contributed)}</td><td class="numeric">${num(p.units,6)}</td><td class="numeric">${pct(p.ownership,2)}</td><td class="numeric">${money(p.value)}</td><td class="numeric ${cls(p.profit)}">${money(p.profit)}</td></tr>`).join('')}</tbody></table></div></section>
 <form id="nav-form" class="section-gap"><section class="panel nav-editor"><label class="field">Your participant — hidden from investor balances<select id="nav-owner">${b.people.map(person=>`<option value="${esc(person)}" ${person===(b.owner||'Me')?'selected':''}>${esc(person)}</option>`).join('')}</select></label></section>
 <section class="panel nav-editor"><h2>Current shared valuation</h2><p class="table-note">Enter broker-reported current values, including any broker fee adjustment. These are manual snapshots, not live quotes. 10 rials = 1 toman. Shared cash must exclude personal sale proceeds and deposits.</p>
 <div class="nav-fields">${[['Valuation date / time','as_of','text'],['Shared cash · toman','cash','number'],['Shared liabilities · toman','liabilities','number']].map(([label,key,type])=>`<label class="field">${label}${input(label,b[key],key,type)}</label>`).join('')}</div>
 <div class="table-wrap"><table><thead><tr><th>Symbol</th><th>Current value · toman</th><th>Personal / excluded</th><th>Action</th></tr></thead><tbody id="nav-holdings">${b.holdings.map((h,i)=>`<tr data-holding><td>${input('Symbol '+(i+1),h.symbol,'symbol')}</td><td>${input('Holding value '+(i+1),h.value,'value','number')}</td><td><input type="checkbox" data-key="personal" aria-label="Personal holding ${i+1}" ${h.personal||['وتوصا','خاور','خصدرا','توان','آب','کاوان','vetoosa','khavar','khesadra','tavan','ab','kavan'].includes(h.symbol.replace(/[\s\u200c]/g,'').replace(/ي/g,'ی').replace(/ك/g,'ک').replace(/[1۱]$/,'').toLowerCase())?'checked':''}></td><td><button type="button" class="button secondary" data-remove-holding="${i}">Remove</button></td></tr>`).join('')}</tbody></table></div>
 <button class="button secondary" type="button" id="nav-add-holding">Add holding</button><p class="table-note">Always excluded: وتوصا، خاور، خصدرا، توان، آب، کاوان (and their symbol aliases). Other holdings are shared unless marked personal.</p>
 <label class="field section-gap">Source / reconciliation notes<textarea id="nav-note" rows="3">${esc(b.note||'')}</textarea></label>
 <label class="fund-filter section-gap"><input id="nav-confirmed" type="checkbox" ${b.confirmed?'checked':''}>I have reconciled shared assets, cash, liabilities, and all contributions for this snapshot.</label></section>
 <section class="panel nav-editor section-gap"><h2>Contributions & withdrawals</h2><p class="table-note">Opening contributions: 5,000,000 tomans each at 1 toman per unit. For later flows, enter the NAV immediately BEFORE the flow, not today’s NAV. Positive amounts buy units; negative amounts redeem units. Keep entries in chronological order. Add a person by entering a new name.</p>
 <div class="table-wrap"><table><thead><tr><th>Person</th><th>Date · YYYY/MM/DD</th><th>Amount · toman</th><th>Entry NAV · toman/unit</th><th>Action</th></tr></thead><tbody>${b.flows.map((f,i)=>`<tr data-flow>${[['person','text'],['date','text'],['amount','number'],['unit_price','number']].map(([key,type])=>`<td>${input(key+' '+(i+1),f[key],key,type)}</td>`).join('')}<td><button type="button" class="button secondary" data-remove-flow="${i}">Remove</button></td></tr>`).join('')}</tbody></table></div><button class="button secondary" type="button" id="nav-add-flow">Add cash flow</button></section>
 <div class="nav-save section-gap"><button type="submit" class="button">Save & calculate</button><span id="nav-save-status" role="status">Saved revision ${navDocument.revision}. Results above reflect saved inputs.</span></div></form>
 <p class="table-note">Based on the example’s unit method: units = cash flow ÷ entry NAV; net assets = included holdings + shared cash − liabilities; NAV = net assets ÷ outstanding units. No management fee is applied. Historical fee percentages in the example are not assumed for your portfolio. Saved revisions remain on the server.</p>`;
 const collect=()=>{
  b.holdings=[...content.querySelectorAll('[data-holding]')].map(row=>Object.fromEntries([...row.querySelectorAll('[data-key]')].map(el=>[el.dataset.key,el.type==='checkbox'?el.checked:el.value])));
  b.flows=[...content.querySelectorAll('[data-flow]')].map(row=>Object.fromEntries([...row.querySelectorAll('[data-key]')].map(el=>[el.dataset.key,el.value])));
  b.people=[...new Set(b.flows.map(f=>f.person))];
  b.owner=$('#nav-owner').value;
  for(const key of ['cash','liabilities','as_of'])b[key]=content.querySelector(`[data-key="${key}"]`).value;
  b.note=$('#nav-note').value;b.confirmed=$('#nav-confirmed').checked;
 };
 const edit=change=>{collect();change();drawNav();$('#nav-save-status').textContent='Unsaved changes. Save to recalculate.';};
 $('#nav-add-holding').onclick=()=>edit(()=>b.holdings.push({symbol:'',value:'0',personal:false}));
 $('#nav-add-flow').onclick=()=>edit(()=>b.flows.push({person:'',date:'',amount:'',unit_price:''}));
 content.querySelectorAll('[data-remove-holding]').forEach(el=>el.onclick=()=>edit(()=>b.holdings.splice(Number(el.dataset.removeHolding),1)));
 content.querySelectorAll('[data-remove-flow]').forEach(el=>el.onclick=()=>edit(()=>b.flows.splice(Number(el.dataset.removeFlow),1)));
 $('#nav-form').oninput=()=>{$('#nav-save-status').textContent='Unsaved changes. Save to recalculate.';};
 $('#nav-form').onsubmit=async event=>{
  event.preventDefault();collect();const button=event.submitter;button.disabled=true;showError('');
  try{navDocument=await navRequest({method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:navDocument.revision,book:b})});if(state.view==='nav'){drawNav();toast('Portfolio saved and recalculated.');}}
  catch(error){showError(error.message);button.disabled=false;}
 };
}
