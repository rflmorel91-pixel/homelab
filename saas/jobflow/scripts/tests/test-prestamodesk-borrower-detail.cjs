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
 for(const role of ['owner','administrator','member'])for(const standalone of [false,true]){
  const s=await setup(role,standalone),w=s.w,d=w.document;
  if(role==='member'){assert.equal(d.getElementById('borrowerDetailPanel').hidden,true);assert(!d.querySelector('[data-view-borrower]'));assert(!s.calls.some(c=>c.url===base+'/borrowers'));s.dom.window.close();continue;}
  const requests=s.calls.length;
  const open=id=>d.querySelector('[data-view-borrower="'+id+'"]').click();
  open(7);assert.equal(d.getElementById('borrowerDetailPanel').hidden,false);assert.equal(d.activeElement,d.getElementById('borrowerDetailTitle'));
  assert.equal(d.getElementById('borrowerDetailTitle').textContent,'Ana Rodríguez');assert.match(d.getElementById('borrowerContactDetails').textContent,/001-1234567-8/);assert.match(d.getElementById('borrowerContactDetails').textContent,/No registrado/);
  assert.match(d.getElementById('borrowerBalanceSummary').textContent,/Préstamos: 2 · Activos: 1/);assert.match(d.getElementById('borrowerBalanceSummary').textContent,/500/);
  assert.deepEqual([...d.querySelectorAll('[data-borrower-loan]')].map(x=>Number(x.dataset.borrowerLoan)),[41,43]);
  const q=d.getElementById('borrowerSearchQuery');q.value='missing';q.dispatchEvent(new w.Event('input',{bubbles:true}));assert.equal(d.getElementById('borrowerDetailTitle').textContent,'Ana Rodríguez');
  d.getElementById('closeBorrowerDetail').click();assert.equal(d.getElementById('borrowerDetailPanel').hidden,true);assert.equal(d.activeElement,q);d.getElementById('borrowerFilterClear').click();
  open(10);assert.match(d.getElementById('borrowerLoanList').textContent,/No hay préstamos/);assert.match(d.getElementById('borrowerBalanceSummary').textContent,/Activos: 0/);
  open(9);assert.equal(d.querySelector('#borrowerDetailPanel img'),null);assert.match(d.getElementById('borrowerDetailTitle').textContent,/<img/);assert(!d.getElementById('borrowerLoanList').textContent.includes('Saldo ordinario:'));
  open(11);assert.match(d.getElementById('borrowerContactDetails').textContent,/Inactivo/);
  assert.equal(s.calls.length,requests,'borrower details must reuse loaded data');
  open(7);d.querySelector('[data-borrower-loan="41"]').click();await flush();assert.equal(d.getElementById('loanDetailPanel').hidden,false);assert.match(d.getElementById('loanDetailTitle').textContent,/#41/);d.getElementById('closeLoanDetail').click();
  if(standalone){s.borrowers.find(b=>b.id===7).full_name='Actualizado';await w.loadDashboard();assert.equal(d.getElementById('borrowerDetailTitle').textContent,'Actualizado');s.borrowers.splice(s.borrowers.findIndex(b=>b.id===7),1);await w.loadDashboard();assert.equal(d.getElementById('borrowerDetailPanel').hidden,true);assert.equal(d.getElementById('borrowerContactDetails').textContent,'');}
  else{d.querySelector('[data-pd-view="cashier"]').click();await flush();assert.equal(w.location.hash,'#cashier');assert.equal(s.prompts(),0);d.querySelector('[data-pd-view="loans"]').click();await flush();open(7);const t=d.getElementById('pdClient');t.value='9';t.dispatchEvent(new w.Event('change'));await flush();assert.equal(d.getElementById('borrowerDetailPanel').hidden,true);assert.equal(d.getElementById('borrowerContactDetails').textContent,'');open(7);assert.equal(d.getElementById('borrowerDetailTitle').textContent,'Otro negocio');assert.match(d.getElementById('borrowerLoanList').textContent,/No hay préstamos/);}
  assert(!s.calls.some(c=>['POST','PATCH','DELETE'].includes(c.options.method)));s.dom.window.close();
 }
 console.log('6 borrower-detail scenarios passed: roles, standalone/workspace, contact/empty/inactive data, safe text, active-only balances, linked loan navigation, filtering, focus, refresh/removal, no writes or discard warning and tenant isolation.');
})().catch(error=>{console.error(error);process.exitCode=1;});
