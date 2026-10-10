// Synthetic data only. No real requests, users or payments.
const {JSDOM}=require('jsdom');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..'),base='/api/v1/products/prestamodesk';
const wait=()=>new Promise(r=>setTimeout(r,15));
async function flush(){for(let i=0;i<12;i++)await wait();}
async function setup(role,standalone=false,stored=null){
 const page=fs.readFileSync(path.join(root,'app',standalone?'prestamodesk-app.html':'prestamodesk-workspace.html'),'utf8');
 const dom=new JSDOM(page,{url:'https://example.test/prestamodesk/workspace#loans',runScripts:'outside-only'}),w=dom.window;
 w.Headers=Headers;w.Response=Response;w.AbortController=AbortController;w.CSS={escape:v=>v};w.HTMLElement.prototype.scrollIntoView=()=>{};w.print=()=>{};
 let prompts=0;w.confirm=()=>{prompts++;return false;};
 const OriginalDate=w.Date;w.Date=class extends OriginalDate{constructor(...args){super(...(args.length?args:['2026-10-10T01:00:00Z']));}static now(){return new OriginalDate('2026-10-10T01:00:00Z').getTime();}};
 if(standalone)w.localStorage.setItem('prestamodesk_tenant_id','4');
 if(stored!==null)w.sessionStorage.setItem('prestamodesk_loan_creation_v1:4',stored);
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
  if(options.method==='POST'&&u.pathname===base+'/loans/preview'){
    if(control.previewPending)await control.previewPending;
    if(control.previewFail)throw new TypeError('Failed to fetch');
    const p=JSON.parse(options.body);data={borrower_id:p.borrower_id,borrower_name:borrowers.find(b=>b.id===p.borrower_id).full_name,currency:'DOP',principal_amount:p.principal_amount,total_interest:'100.00',total_due:'1100.00',installments:Array.from({length:p.installment_count},(_,i)=>({sequence_number:i+1,due_date:'2026-11-10',principal_due:'500.00',interest_due:'50.00',total_due:'550.00'}))};
  }
  else if(options.method==='POST'&&u.pathname===base+'/loans'){
    if(control.loanPending)await control.loanPending;
    if(control.loanMode==='network')throw new TypeError('Failed to fetch');
    if(control.loanMode===422){status=422;data={detail:[]};}
    else if(control.loanMode===500){status=500;data={detail:'server error'};}
    else if(control.loanMode===409){status=409;data={detail:'Loan request key was used with different details'};}
    else data=detail(loans[0]);
  }
  else if(options.method==='PATCH'&&u.pathname.endsWith('/contact')){
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
 for(const link of w.document.querySelectorAll('link[href$=".css"]')){const style=w.document.createElement('style');style.textContent=fs.readFileSync(path.join(root,'app',link.getAttribute('href')),'utf8');w.document.head.append(style);}
 await flush();return {w,dom,calls,borrowers,control,prompts:()=>prompts};
}
(async()=>{
 for (const standalone of [true,false]) for (const role of ['owner','administrator','member']) {
  const s=await setup(role,standalone),w=s.w,d=w.document;
  const q=id=>d.getElementById(id),click=sel=>d.querySelector(sel).click();
  const visible=id=>!q(id).hidden&&w.getComputedStyle(q(id)).display!=='none';
  assert.equal(q('workspace').dataset.loanTask,'loans');assert(visible('compactLoans'));
  assert(!visible('compactBorrowers'));assert(!visible('compactApplications'));assert(!visible('compactSettings'));assert(!visible('compactLoanForm'));assert(!visible('compactBorrowerForm'));
  if(role==='owner')fs.writeFileSync('/tmp/pd-compact-'+(standalone?'standalone':'workspace')+'.html',d.documentElement.outerHTML);
  const before=s.calls.length;
  if(role==='member') {for(const b of d.querySelectorAll('[data-loan-manager]'))assert(b.hidden);click('[data-loan-tab="borrowers"]');assert.equal(q('workspace').dataset.loanTask,'loans');assert(!visible('compactLoanForm'));}
  else {
   click('[data-loan-form="compactLoanForm"]');assert(visible('compactLoanForm'));q('loanPrincipal').value='1234';
   click('[data-loan-close="compactLoanForm"]');assert(!visible('compactLoanForm'));assert.equal(q('loanPrincipal').value,'1234');
   click('[data-loan-form="compactLoanForm"]');assert.equal(q('loanPrincipal').value,'1234');
   click('[data-loan-form="compactBorrowerForm"]');assert(visible('compactBorrowerForm'));assert(!visible('compactLoanForm'));q('borrowerName').value='Draft borrower';
   click('[data-loan-tab="borrowers"]');assert(visible('compactBorrowers'));assert(!visible('compactLoans'));
   click('[data-loan-tab="applications"]');assert(visible('compactApplications'));assert(visible('compactProspects'));assert(!visible('compactBorrowers'));
   click('[data-loan-tab="settings"]');assert(visible('compactSettings'));click('[data-loan-tab="settings"]');assert.equal(q('workspace').dataset.loanTask,'loans');
   assert.equal(q('borrowerName').value,'Draft borrower');assert.equal(q('loanPrincipal').value,'1234');
   assert.equal(s.calls.length,before);
   click('[data-loan-tab="borrowers"]');q('borrowerList').querySelector('button').click();await flush();q('borrowerNewLoan').click();assert(visible('compactLoanForm'));assert.equal(q('loanBorrower').value,'7');
   click('[data-loan-tab="loans"]');
   for(const [id,value] of Object.entries({loanBorrower:'7',loanPrincipal:'1000',loanRate:'10',loanInstallments:'2',loanFrequency:'monthly',loanStartDate:'2026-10-10',loanFirstPaymentDate:'2026-11-10'}))q(id).value=value;
   s.control.loanMode='network';q('loanForm').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await flush();assert(visible('compactLoanForm'));
   click('[data-loan-form="compactBorrowerForm"]');assert(visible('compactLoanForm'));assert(!visible('compactBorrowerForm'));click('[data-loan-close="compactLoanForm"]');assert(visible('compactLoanForm'));click('[data-loan-tab="borrowers"]');assert.equal(q('workspace').dataset.loanTask,'loans');assert(!q('loanCreationRetry').hidden);
  }
  s.dom.window.close();
 }
 for(const standalone of [true,false]) {const s=await setup('owner',standalone,'not-json');assert.equal(s.w.document.getElementById('workspace').dataset.activeForm,'compactLoanForm');s.dom.window.close();}
 console.log('Compact loans checks passed: standalone/workspace, three roles, task visibility, retained drafts, borrower shortcut, no navigation requests and pending recovery guards.');
})().catch(e=>{console.error(e);process.exit(1);});
