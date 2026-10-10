// Synthetic data only. No real requests, users or payments.
const {JSDOM}=require('jsdom');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..'),base='/api/v1/products/prestamodesk';
const wait=()=>new Promise(r=>setTimeout(r,15));
async function flush(){for(let i=0;i<12;i++)await wait();}
async function setup(role,standalone=false,stored=null){
 const page=fs.readFileSync(path.join(root,'app',standalone?'prestamodesk-caja.html':'prestamodesk-workspace.html'),'utf8');
 const dom=new JSDOM(page,{url:'https://example.test/prestamodesk/workspace#cashier',runScripts:'outside-only'}),w=dom.window;
 w.Headers=Headers;w.Response=Response;w.AbortController=AbortController;w.CSS={escape:v=>v};w.HTMLElement.prototype.scrollIntoView=()=>{};w.print=()=>{};w.crypto.randomUUID=()=> '00000000-0000-4000-8000-000000000001';
 let prompts=0;w.confirm=()=>{prompts++;return false;};
 const OriginalDate=w.Date;w.Date=class extends OriginalDate{constructor(...args){super(...(args.length?args:['2026-10-10T01:00:00Z']));}static now(){return new OriginalDate('2026-10-10T01:00:00Z').getTime();}};
 if(standalone)w.localStorage.setItem('prestamodesk_cashier_tenant_id','4');
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
  else if(u.pathname===base+'/cashier/closings'&&options.method==='POST') {
   if(control.closingPending)await control.closingPending;
   if(control.closingFail)throw new TypeError('Synthetic network failure');
   data={id:1,closed_at:'2026-10-10T12:00:00Z',payment_count:0,total_collected:'0',cash_expected:'0',cash_counted:'10',cash_difference:'10',bank_transfer_total:'0',card_total:'0',other_total:'0',notes:'Synthetic'};
  }
  else if(u.pathname===base+'/payments'&&options.method==='POST') {if(control.paymentPending)await control.paymentPending;if(control.paymentFail)throw new TypeError('Synthetic network failure');data={receipt_number:'PM-SYNTHETIC',amount:'10',loan_balance:'490'};}
  else if(u.pathname.startsWith(base+'/cashier/loans/')) {data={...detail(loans[0]),borrower_full_name:'Ana Rodríguez',paid_amount:'0',ordinary_balance_due:'500',late_fee_balance_due:'0',balance_due:'500',projected_through:'2026-10-10'};data.installments=data.installments.map(x=>({...x,ordinary_balance_due:'500',late_fee_balance_due:'0',balance_due:'500'}));}
  else if(u.pathname===base+'/cashier/loans')data=loans.map(l=>({...l,borrower_full_name:borrowers.find(b=>b.id===l.borrower_id).full_name,borrower_document_number:borrowers.find(b=>b.id===l.borrower_id).document_number}));
  else if(u.pathname===base+'/borrowers')data=tenant===9?[{id:7,full_name:'Otro negocio',document_number:'SECOND-001',status:'active'}]:borrowers;
  else if(u.pathname===base+'/loans')data=tenant===9?[]:loans;
  else if(u.pathname.startsWith(base+'/loans/'))data=detail(loans.find(l=>l.id===Number(u.pathname.split('/').pop())));
  else if(u.pathname.endsWith('/late-fee-policy')){status=404;data={detail:'not configured'};}
  else if(u.pathname.endsWith('/public-page'))data={tenant_slug:'synthetic'};
  else if(u.pathname.endsWith('/closing-preview'))data={opened_at:'2026-10-10T12:00:00Z',payment_count:0,total_collected:'0',cash_expected:'0',bank_transfer_total:'0',card_total:'0',other_total:'0'};
  return new Response(JSON.stringify(data),{status,headers:{'content-type':'application/json'}});
 };
 for(const match of page.matchAll(/<script[^>]*src="([^"]+)"/g))w.eval(fs.readFileSync(path.join(root,'app',match[1]),'utf8'));
 for(const link of w.document.querySelectorAll('link[href$=".css"]')){const style=w.document.createElement('style');style.textContent=fs.readFileSync(path.join(root,'app',link.getAttribute('href')),'utf8');w.document.head.append(style);}
 await flush();return {w,dom,calls,borrowers,control,prompts:()=>prompts};
}
(async()=>{
 for(const standalone of [true,false]) for(const role of ['owner','administrator','member','cashier']) {
  const s=await setup(role,standalone),w=s.w,d=w.document,q=id=>d.getElementById(id),tab=name=>d.querySelector('button[data-cashier-task="'+name+'"]').click();
  const visible=id=>!q(id).hidden&&w.getComputedStyle(q(id)).display!=='none';
  assert(!q('cashierWorkspace').hidden);assert(visible('cashierSearchPanel'));assert(!visible('cashClosingPanel'));assert(!visible('cashClosingHistoryPanel'));
  if(role==='member')fs.writeFileSync('/tmp/pd-compact-caja-'+(standalone?'standalone':'workspace')+'.html',d.documentElement.outerHTML);
  const own=['member','cashier'].includes(role);assert.equal(d.querySelector('button[data-cashier-task="closing"]').hidden,!own);
  let calls=s.calls.length;
  if(!own) {tab('closing');assert.equal(q('cashierWorkspace').dataset.cashierTask,'collect');assert.equal(s.calls.length,calls);s.dom.window.close();continue;}
  q('loanSearchQuery').value='Ana';tab('closing');assert(visible('cashClosingPanel'));assert(!visible('cashierSearchPanel'));q('cashCounted').value='123';q('cashClosingNotes').value='Draft notes';
  tab('history');assert(visible('cashClosingHistoryPanel'));assert(!visible('cashClosingPanel'));tab('collect');assert.equal(q('loanSearchQuery').value,'Ana');tab('closing');assert.equal(q('cashCounted').value,'123');assert.equal(q('cashClosingNotes').value,'Draft notes');assert.equal(s.calls.length,calls);
  let release;s.control.closingPending=new Promise(r=>release=r);q('cashClosingForm').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await wait();q('cashClosingForm').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await wait();assert.equal(s.calls.filter(c=>c.options.method==='POST'&&c.url===base+'/cashier/closings').length,1);tab('history');assert.equal(q('cashierWorkspace').dataset.cashierTask,'closing');
  if(!standalone){d.querySelector('[data-pd-view="loans"]').click();await flush();assert.equal(w.location.hash,'#cashier');}
  release();await flush();assert(!q('cashClosingReceipt').hidden);assert(!q('cashClosingForm').querySelector('button').disabled);let printed=0;w.print=()=>printed++;q('printCashClosingButton').click();assert.equal(printed,1);
  tab('collect');q('cashierLoanList').querySelector('button').click();await flush();assert(visible('paymentPanel'));q('paymentAmount').value='10';q('paymentReference').value='Draft ref';tab('history');tab('collect');assert.equal(q('paymentAmount').value,'10');assert.equal(q('paymentReference').value,'Draft ref');
  let paid;s.control.paymentPending=new Promise(r=>paid=r);s.control.paymentFail=true;q('paymentForm').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await wait();tab('closing');assert.equal(q('cashierWorkspace').dataset.cashierTask,'collect');paid();await flush();tab('history');assert.equal(q('cashierWorkspace').dataset.cashierTask,'collect');assert(!q('errorMessage').hidden);
  s.dom.window.close();
 }
 for(const standalone of [true,false]) {
  const s=await setup('member',standalone),w=s.w,d=w.document;
  d.querySelector('button[data-cashier-task="closing"]').click();d.getElementById('cashCounted').value='88';d.getElementById('cashClosingNotes').value='Preserved after error';s.control.closingFail=true;
  d.getElementById('cashClosingForm').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await flush();assert.equal(d.getElementById('cashCounted').value,'88');assert.equal(d.getElementById('cashClosingNotes').value,'Preserved after error');assert(!d.getElementById('cashClosingForm').querySelector('button').disabled);assert(!d.getElementById('errorMessage').hidden);s.dom.window.close();
 }
 console.log('Compact Caja checks passed: standalone/workspace, four roles, task visibility, retained search/payment/closure drafts, no task requests, closure submit/navigation guards, printing and uncertain-payment guards.');
})().catch(e=>{console.error(e);process.exit(1);});
