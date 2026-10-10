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
 const control={fail:null,pending:null}; for(const b of borrowers)b.updated_at="2026-10-10T12:00:00.000000";
 const loans=[
  {id:41,borrower_id:7,status:'active',due:'2026-10-08',paid:'50'},
  {id:42,borrower_id:8,status:'active',due:'2026-10-09',paid:'0'},
  {id:43,borrower_id:7,status:'paid',due:'2026-09-01',paid:'550'},
  {id:44,borrower_id:9,status:'cancelled',due:'2026-09-01',paid:'0'}
 ].map(x=>({...x,loan_type:'personal',currency:'DOP',principal_amount:'1000',total_interest:'100',total_due:'1100',installment_count:2,late_fee_enabled:false}));
 function detail(loan){return {...loan,installments:[{id:loan.id*10,sequence_number:1,due_date:loan.due,total_due:loan.id===41?(control.due||'550'):'550',principal_due:'500',interest_due:'50',paid_amount:loan.id===41?(control.paid||loan.paid):loan.paid,status:loan.paid==='550'?'paid':'pending'}]};}
 w.fetch=async(input,options={})=>{
  const u=new URL(input,'https://example.test');calls.push({url:u.pathname,options});let data=[],status=200;
  const tenant=Number(new Headers(options.headers).get('X-Tenant-ID')||4);
  if(options.method==='PATCH'&&u.pathname.endsWith('/contact')){
    if(control.pending)await control.pending;
    const record=borrowers.find(b=>b.id===Number(u.pathname.split('/').at(-2)));
    const payload=JSON.parse(options.body);
    if(control.fail==='network')throw new TypeError('Failed to fetch');
    if(control.fail===409||payload.expected_updated_at!==record.updated_at){status=409;data={detail:'conflict'};}
    else if(control.fail===422){status=422;data={detail:[]};}
    else {for(const key of ['phone','email','address','municipality','province','notes'])record[key]=payload[key];record.updated_at='2026-10-10T13:00:00.000000';data=record;}
  }
  else if(u.pathname.startsWith(base+'/borrowers/'))data=borrowers.find(b=>b.id===Number(u.pathname.split('/').pop()));
  else if(u.pathname.endsWith('/health'))data={status:'healthy'};
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
 await flush();return {w,dom,calls,borrowers,control,prompts:()=>prompts};
}
(async()=>{
 for(const role of ['owner','administrator','member'])for(const standalone of [false,true]){
  const s=await setup(role,standalone),w=s.w,d=w.document;
  if(role==='member'){assert(d.getElementById('borrowerStatementPanel').hidden);assert(!d.querySelector('[data-view-borrower]'));s.dom.window.close();continue;}
  let prints=0;w.print=()=>{prints++;assert(d.querySelector('.pd-borrower-print'));assert(!d.getElementById('borrowerStatementPanel').hidden);if(process.env.PD_STATEMENT_PREVIEW&&role==='owner'){
    const html=d.documentElement.outerHTML.replace(/href="(\/assets\/[^"]+)"/g,(_,p)=>'href="file://'+path.join(root,'app',p)+'"');fs.writeFileSync(process.env.PD_STATEMENT_PREVIEW+(standalone?'-standalone':'-workspace')+'.html',html);
  }};
  const open=id=>d.querySelector('[data-view-borrower="'+id+'"]').click();
  const prepare=()=>d.getElementById('openBorrowerStatement').click();
  const text=()=>d.getElementById('borrowerStatementContent').textContent;
  const requests=s.calls.length;open(7);prepare();assert(!d.getElementById('borrowerStatementPanel').hidden);assert.match(text(),/Ana Rodríguez/);assert.match(text(),/Synthetic First/);assert.match(text(),/Cliente #1/);assert.match(text(),/Fecha de consulta: 2026-10-09/);assert.match(text(),/no incluyen mora/);assert.match(text(),/Pagado a cuotas/);assert.match(text(),/600/);assert.match(text(),/500/);assert.equal(d.querySelectorAll('#borrowerStatementContent tbody tr').length,2);
  d.getElementById('printBorrowerStatement').click();assert.equal(prints,1);assert(!d.querySelector('.pd-borrower-print'));assert.equal(s.calls.length,requests,'statement must not make requests');
  d.getElementById('closeBorrowerStatement').click();assert(d.getElementById('borrowerStatementPanel').hidden);assert.equal(d.activeElement,d.getElementById('openBorrowerStatement'));
  open(9);prepare();assert(!d.querySelector('#borrowerStatementContent img'));assert.match(text(),/<img/);assert.match(text(),/Cancelado/);assert.match(text(),/Activos: 0/);assert.equal(d.querySelector('#borrowerStatementContent tbody tr').cells[3].textContent,'—');
  open(10);prepare();assert.match(text(),/No hay préstamos/);assert.match(text(),/Activos: 0/);
  open(7);d.getElementById('editBorrowerContact').click();await flush();const phone=d.getElementById('borrowerContactPhone');phone.value='unsaved';phone.dispatchEvent(new w.Event('input',{bubbles:true}));prepare();assert(d.getElementById('borrowerStatementPanel').hidden);w.confirm=()=>true;d.getElementById('cancelBorrowerContact').click();
  if(standalone){assert.equal(w.statementCents('0.30')-w.statementCents('0.10'),20);s.control.due='0.30';s.control.paid='0.10';await w.loadDashboard();prepare();assert(text().includes('0.20'));s.control.paid='1.00';await w.loadDashboard();prepare();assert(d.getElementById('borrowerStatementPanel').hidden);assert.match(d.getElementById('errorMessage').textContent,/saldos/);}
  else{open(7);prepare();d.querySelector('[data-pd-view="cashier"]').click();await flush();assert.equal(w.location.hash,'#cashier');assert.equal(s.prompts(),0);d.querySelector('[data-pd-view="loans"]').click();await flush();open(7);prepare();const t=d.getElementById('pdClient');t.value='9';t.dispatchEvent(new w.Event('change'));await flush();assert(d.getElementById('borrowerStatementPanel').hidden);assert.equal(d.getElementById('borrowerStatementContent').textContent,'');open(7);prepare();assert.match(text(),/Otro negocio/);assert(!text().includes('Ana'));}
  assert(!s.calls.some(c=>['POST','PATCH','PUT','DELETE'].includes(c.options.method)));s.dom.window.close();
 }
 console.log('6 borrower-statement scenarios passed: roles, standalone/workspace, active/paid/cancelled totals, overdue/date labels, integer-cent arithmetic, invalid balance rejection, safe text, print cleanup, close/focus, no writes/discard warnings and tenant clearing.');
})().catch(error=>{console.error(error);process.exitCode=1;});
