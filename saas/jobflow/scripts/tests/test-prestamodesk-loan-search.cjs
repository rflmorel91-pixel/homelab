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
 const calls=[],borrowers=[{id:7,full_name:'Ana Rodríguez',document_number:'001-1234567-8',status:'active'},{id:8,full_name:'José Castillo',document_number:'SYN-002',status:'active'},{id:9,full_name:'<img src=x onerror=alert(1)>',document_number:null,status:'active'}];
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
  else if(u.pathname===base+'/borrowers')data=borrowers;
  else if(u.pathname===base+'/loans')data=tenant===9?[]:loans;
  else if(u.pathname.startsWith(base+'/loans/'))data=detail(loans.find(l=>l.id===Number(u.pathname.split('/').pop())));
  else if(u.pathname.endsWith('/late-fee-policy')){status=404;data={detail:'not configured'};}
  else if(u.pathname.endsWith('/public-page'))data={tenant_slug:'synthetic'};
  else if(u.pathname.endsWith('/closing-preview'))data={payment_count:0,total_collected:'0',cash_expected:'0',bank_transfer_total:'0',card_total:'0',other_total:'0'};
  return new Response(JSON.stringify(data),{status,headers:{'content-type':'application/json'}});
 };
 for(const match of page.matchAll(/<script[^>]*src="([^"]+)"/g))w.eval(fs.readFileSync(path.join(root,'app',match[1]),'utf8'));
 await flush();return {w,dom,calls,prompts:()=>prompts};
}
(async()=>{
 for(const role of ['owner','administrator','member'])for(const standalone of [false,true]){
  const s=await setup(role,standalone),w=s.w,d=w.document;
  const query=d.getElementById('loanSearchQuery'),status=d.getElementById('loanStatusFilter');
  const ids=()=>[...d.querySelectorAll('[data-view-loan]')].map(b=>Number(b.dataset.viewLoan));
  const search=value=>{query.value=value;query.dispatchEvent(new w.Event('input',{bubbles:true}));};
  const filter=value=>{status.value=value;status.dispatchEvent(new w.Event('change',{bubbles:true}));};
  assert.equal(d.getElementById('authPanel').hidden,true);assert.deepEqual(ids(),[41,42,43,44]);
  const requests=s.calls.length,summary=d.getElementById('outstandingBalance').textContent;
  search('ANA   RODRIGUEZ');assert.deepEqual(ids(),[41,43]);
  search('00112345678');assert.deepEqual(ids(),[41,43],'document punctuation normalization');
  search('  préstamo #42  ');assert.deepEqual(ids(),[42]);
  search('jose');assert.deepEqual(ids(),[42]);filter('paid');assert.deepEqual(ids(),[]);
  assert.match(d.getElementById('loanList').textContent,/No hay préstamos que coincidan/);
  search('');assert.deepEqual(ids(),[43]);filter('active');assert.deepEqual(ids(),[41,42]);
  filter('overdue');assert.deepEqual(ids(),[41],'due today, fully paid and cancelled loans excluded');
  assert.equal(d.getElementById('loanResultCount').textContent,'1');
  assert.equal(d.getElementById('loanFilterResult').textContent,'Mostrando 1 de 4 préstamos.');
  filter('cancelled');assert.deepEqual(ids(),[44]);assert.equal(d.querySelector('#loanList img'),null,'borrower name must remain escaped');
  search('missing');d.getElementById('loanFilterClear').click();assert.equal(query.value,'');assert.equal(status.value,'all');assert.deepEqual(ids(),[41,42,43,44]);
  d.getElementById('loanFilterForm').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));
  assert.equal(s.calls.length,requests,'filtering must not send API requests');
  assert.equal(d.getElementById('outstandingBalance').textContent,summary,'portfolio summary must remain unfiltered');
  search('ana');d.querySelector('[data-view-loan="41"]').click();await flush();assert.equal(d.getElementById('loanDetailPanel').hidden,false);
  if(!standalone){
   d.querySelector('[data-pd-view="cashier"]').click();await flush();assert.equal(w.location.hash,'#cashier');assert.equal(s.prompts(),0,'search must not mark forms dirty');
   d.querySelector('[data-pd-view="loans"]').click();await flush();assert.deepEqual(ids(),[41,42,43,44]);
   const select=d.getElementById('pdClient');select.value='9';select.dispatchEvent(new w.Event('change'));await flush();
   assert.deepEqual(ids(),[]);assert.match(d.getElementById('loanList').textContent,/No hay préstamos registrados/);assert.equal(d.getElementById('loanFilterResult').textContent,'Mostrando 0 de 0 préstamos.');
  }
  if(role==='member')assert(!s.calls.some(c=>['/borrowers','/applications','/prospects','/prospects/public-page','/late-fee-policy'].some(p=>c.url.endsWith(p))),'member requested restricted data');
  s.dom.window.close();
 }
 console.log('6 loan-search scenarios passed: three roles, standalone/workspace, normalized name/document/number search, status and overdue boundaries, clear/empty results, safe rendering, unfiltered summaries, detail navigation, no writes/discard prompt and tenant switching.');
})().catch(error=>{console.error(error);process.exitCode=1;});
