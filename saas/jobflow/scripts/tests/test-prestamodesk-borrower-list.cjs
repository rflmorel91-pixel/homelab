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
  const query=d.getElementById('borrowerSearchQuery'),status=d.getElementById('borrowerStatusFilter');
  const names=()=>[...d.querySelectorAll('#borrowerList h3')].map(x=>x.textContent);
  const search=v=>{query.value=v;query.dispatchEvent(new w.Event('input',{bubbles:true}));};
  const filter=v=>{status.value=v;status.dispatchEvent(new w.Event('change',{bubbles:true}));};
  if(role==='member'){assert.equal(query.closest('section').hidden,true);assert.equal(query.disabled,true);assert(!s.calls.some(c=>c.url===base+'/borrowers'));s.dom.window.close();continue;}
  const requests=s.calls.length,chooser=d.getElementById('loanBorrower');chooser.value='7';
  assert.equal(names().length,5);search(' ANA   RODRIGUEZ ');assert.deepEqual(names(),['Ana Rodríguez']);
  search('00112345678');assert.deepEqual(names(),['Ana Rodríguez']);search('jose');assert.equal(names().length,2);
  search('SYN003');assert.deepEqual(names(),['José Castillo']);filter('inactive');assert.equal(names().length,0);assert.match(d.getElementById('borrowerList').textContent,/coincidan/);
  search('');assert.deepEqual(names(),['Inactivo']);filter('active');assert.equal(names().length,4);filter('all');assert.equal(names().length,5);
  assert.equal(d.querySelector('#borrowerList img'),null);assert.equal(d.getElementById('borrowerCount').textContent,'5');assert.equal(chooser.value,'7','list filtering must preserve new-loan selection');
  search('missing');d.getElementById('borrowerFilterClear').click();assert.equal(query.value,'');assert.equal(status.value,'all');assert.equal(names().length,5);assert.equal(d.activeElement,query);
  const submit=new w.Event('submit',{bubbles:true,cancelable:true});d.getElementById('borrowerFilterForm').dispatchEvent(submit);assert.equal(submit.defaultPrevented,true);assert.equal(s.calls.length,requests);
  search('ana');filter('active');assert.equal(d.getElementById('borrowerFilterResult').textContent,'Mostrando 1 de 5 prestatarios.');
  if(standalone){await w.loadDashboard();assert.equal(query.value,'ana');assert.equal(names().length,1);s.borrowers.splice(0);await w.loadDashboard();assert.match(d.getElementById('borrowerList').textContent,/No hay prestatarios registrados/);assert.equal(d.getElementById('borrowerFilterResult').textContent,'Mostrando 0 de 0 prestatarios.');}
  else{d.querySelector('[data-pd-view="cashier"]').click();await flush();assert.equal(w.location.hash,'#cashier');assert.equal(s.prompts(),0);d.querySelector('[data-pd-view="loans"]').click();await flush();const q=d.getElementById('borrowerSearchQuery');q.value='ana';q.dispatchEvent(new w.Event('input',{bubbles:true}));const t=d.getElementById('pdClient');t.value='9';t.dispatchEvent(new w.Event('change'));await flush();assert.equal(d.getElementById('borrowerSearchQuery').value,'');assert.equal(d.getElementById('borrowerStatusFilter').value,'all');assert.deepEqual(names(),['Otro negocio']);}
  assert(!s.calls.some(c=>['POST','PATCH','DELETE'].includes(c.options.method)));s.dom.window.close();
 }
 console.log('6 borrower-list scenarios passed: roles, standalone/workspace, normalized search, combined status filters, safe rendering, counts, clear/empty/refresh, preserved loan selection, no writes or discard warnings and tenant isolation.');
})().catch(error=>{console.error(error);process.exitCode=1;});
