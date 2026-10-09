// Synthetic data only. No real requests, users or payments.
const {JSDOM}=require('jsdom');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..'),base='/api/v1/products/prestamodesk';
const wait=()=>new Promise(r=>setTimeout(r,15));
async function flush(){for(let i=0;i<12;i++)await wait();}
async function setup(role,standalone=false){
 const page=fs.readFileSync(path.join(root,'app',standalone?'prestamodesk-app.html':'prestamodesk-workspace.html'),'utf8');
 const dom=new JSDOM(page,{url:'https://example.test/prestamodesk/workspace#loans',runScripts:'outside-only'}),w=dom.window;
 w.Headers=Headers;w.Response=Response;w.AbortController=AbortController;w.CSS={escape:v=>v};w.HTMLElement.prototype.scrollIntoView=()=>{};w.print=()=>{};
 let prompts=0;w.confirm=()=>{prompts++;return false;};
 const OriginalDate=w.Date;w.Date=class extends OriginalDate{constructor(...args){super(...(args.length?args:['2026-10-10T01:00:00Z']));}static now(){return new OriginalDate('2026-10-10T01:00:00Z').getTime();}};
 if(standalone)w.localStorage.setItem('prestamodesk_tenant_id','4');
 const calls=[],borrowers=[{id:7,full_name:'Ana Rodríguez',document_number:'001-1234567-8',status:'active'},{id:8,full_name:'José Castillo',document_number:'SYN-002',status:'active'},{id:9,full_name:'<img src=x onerror=alert(1)>',document_number:null,status:'active'},{id:10,full_name:'José Castillo',document_number:'SYN-003',status:'active'},{id:11,full_name:'Inactivo',document_number:'INACTIVE-001',status:'inactive'}];
 const loans=[
  {id:41,borrower_id:7,status:'active',due:'2026-10-08',paid:'50'},
  {id:42,borrower_id:8,status:'active',due:'2026-10-09',paid:'0'},
  {id:43,borrower_id:7,status:'paid',due:'2026-09-01',paid:'550'},
  {id:44,borrower_id:9,status:'cancelled',due:'2026-09-01',paid:'0'}
 ].map(x=>({...x,loan_type:'personal',currency:'DOP',principal_amount:'1000',total_interest:'100',total_due:'1100',installment_count:2,late_fee_enabled:false}));
 function detail(loan){return {...loan,installments:[{id:loan.id*10,sequence_number:1,due_date:loan.due,total_due:'550',principal_due:'500',interest_due:'50',paid_amount:loan.paid,status:loan.paid==='550'?'paid':'pending'}]};}
 w.fetch=async(input,options={})=>{
  const u=new URL(input,'https://example.test');calls.push({url:u.pathname,options});let data=[],status=200;
  const tenant=Number(new Headers(options.headers).get('X-Tenant-ID')||4);
  if(u.pathname.endsWith('/health'))data={status:'healthy'};
  else if(u.pathname.endsWith('/access'))data={clients:[{tenant_id:4,client_number:1,name:'Synthetic First',role},{tenant_id:9,client_number:2,name:'Synthetic Second',role}].slice(0,standalone?1:2)};
  else if(role==='member'&&['/borrowers','/applications','/prospects','/prospects/public-page','/late-fee-policy'].some(p=>u.pathname.endsWith(p))){status=403;data={detail:'Tenant owner access required'};}
  else if(u.pathname===base+'/cashier/loans')data=loans.map(l=>({...l,borrower_full_name:borrowers.find(b=>b.id===l.borrower_id).full_name,borrower_document_number:borrowers.find(b=>b.id===l.borrower_id).document_number}));
  else if(u.pathname===base+'/borrowers')data=tenant===9?[{id:7,full_name:'Otro negocio',document_number:'SECOND-001',status:'active'}]:borrowers;
  else if(u.pathname===base+'/loans')data=tenant===9?[]:loans;
  else if(u.pathname.startsWith(base+'/loans/'))data=detail(loans.find(l=>l.id===Number(u.pathname.split('/').pop())));
  else if(u.pathname.endsWith('/late-fee-policy')){status=404;data={detail:'not configured'};}
  else if(u.pathname.endsWith('/public-page'))data={tenant_slug:'synthetic'};
  else if(u.pathname.endsWith('/closing-preview'))data={payment_count:0,total_collected:'0',cash_expected:'0',bank_transfer_total:'0',card_total:'0',other_total:'0'};
  return new Response(JSON.stringify(data),{status,headers:{'content-type':'application/json'}});
 };
 for(const match of page.matchAll(/<script[^>]*src="([^"]+)"/g))w.eval(fs.readFileSync(path.join(root,'app',match[1]),'utf8'));
 await flush();return {w,dom,calls,borrowers,prompts:()=>prompts};
}
(async()=>{
 let scenarios=0;
 for(const role of ['owner','administrator','member'])for(const standalone of [false,true]){
  const s=await setup(role,standalone),w=s.w,d=w.document;
  let query=d.getElementById('loanBorrowerSearch'),select=d.getElementById('loanBorrower'),clear=d.getElementById('loanBorrowerSearchClear'),notice=d.getElementById('loanBorrowerSearchStatus');
  const search=value=>{query.value=value;query.dispatchEvent(new w.Event('input',{bubbles:true}));};
  const ids=()=>[...select.options].filter(o=>o.value).map(o=>Number(o.value));
  if(role==='member'){
   assert.equal(query.closest('section').hidden,true);assert.equal(query.disabled,true);assert.equal(select.disabled,true);
   assert(!s.calls.some(c=>c.url===base+'/borrowers'),'member must not request restricted borrower data');
   s.dom.window.close();scenarios++;continue;
  }
  assert.deepEqual(ids(),[7,8,9,10]);assert.match(select.options[1].textContent,/001-1234567-8/);assert(!select.querySelector('img'),'unsafe name inserted as HTML');
  const initialCalls=s.calls.length;search('  ANA   RODRIGUEZ ');assert.deepEqual(ids(),[7]);search('00112345678');assert.deepEqual(ids(),[7]);search('jose');assert.deepEqual(ids(),[8,10]);search('SYN003');assert.deepEqual(ids(),[10]);search('no coincidencia');assert.deepEqual(ids(),[]);assert.match(notice.textContent,/0 coincidencias/);assert.equal(select.value,'');assert.equal(s.calls.length,initialCalls,'typing search must not call the API');
  const enter=new w.KeyboardEvent('keydown',{key:'Enter',bubbles:true,cancelable:true});query.dispatchEvent(enter);assert.equal(enter.defaultPrevented,true);
  if(!standalone){d.querySelector('[data-pd-view="cashier"]').click();await flush();assert.equal(s.prompts(),0,'search text must not mark forms dirty');assert.equal(w.location.hash,'#cashier');d.querySelector('[data-pd-view="loans"]').click();await flush();query=d.getElementById('loanBorrowerSearch');select=d.getElementById('loanBorrower');clear=d.getElementById('loanBorrowerSearchClear');notice=d.getElementById('loanBorrowerSearchStatus');}
  clear.click();assert.deepEqual(ids(),[7,8,9,10]);select.value='7';select.dispatchEvent(new w.Event('change',{bubbles:true}));search('jose');assert.deepEqual(ids(),[7,8,10]);assert.equal(select.value,'7');assert.match(notice.textContent,/Se conserva/);assert.match(select.options[1].textContent,/Selección actual/);
  clear.click();assert.equal(select.value,'7');assert.equal(query.value,'');assert.equal(d.activeElement,query);
  if(standalone){await w.loadDashboard();assert.equal(select.value,'7','refresh must preserve active selection');s.borrowers.find(b=>b.id===7).status='inactive';await w.loadDashboard();assert.equal(select.value,'','inactive selection must clear');assert(!ids().includes(7));s.borrowers.splice(0);await w.loadDashboard();assert.equal(select.disabled,true);assert.equal(query.disabled,true);assert.match(notice.textContent,/No hay prestatarios activos/);}
  else{search('jose');d.querySelector('[data-pd-view="cashier"]').click();await flush();assert.equal(w.location.hash,'#loans','real borrower selection must retain unsaved-edit protection');assert(s.prompts()>0);w.confirm=()=>true;const tenant=d.getElementById('pdClient');tenant.value='9';tenant.dispatchEvent(new w.Event('change'));await flush();assert.equal(d.getElementById('loanBorrowerSearch').value,'');assert.equal(d.getElementById('loanBorrower').value,'');assert.match(d.getElementById('loanBorrower').textContent,/Otro negocio/);assert(!d.getElementById('loanBorrower').textContent.includes('Ana'));}
  assert(!s.calls.some(c=>['POST','PATCH','DELETE'].includes(c.options.method)),'search must never write records');
  s.dom.window.close();scenarios++;
 }
 console.log(`${scenarios} borrower-search scenarios passed: owner/administrator/member, standalone/workspace, name/document normalization, duplicate names, inactive/empty results, preserved selection, clear/refresh, safe text, no writes or search-only discard prompt, real-edit guards and business isolation.`);
})().catch(error=>{console.error(error);process.exitCode=1;});
