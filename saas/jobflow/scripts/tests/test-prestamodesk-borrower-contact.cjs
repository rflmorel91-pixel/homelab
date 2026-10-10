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
 function detail(loan){return {...loan,installments:[{id:loan.id*10,sequence_number:1,due_date:loan.due,total_due:'550',principal_due:'500',interest_due:'50',paid_amount:loan.paid,status:loan.paid==='550'?'paid':'pending'}]};}
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
  if(role==='member'){assert(d.getElementById('borrowerDetailPanel').hidden);assert(!d.querySelector('[data-view-borrower]'));s.dom.window.close();continue;}
  d.querySelector('[data-view-borrower="7"]').click();d.getElementById('editBorrowerContact').click();await flush();
  const form=d.getElementById('borrowerContactForm'),phone=d.getElementById('borrowerContactPhone'),email=d.getElementById('borrowerContactEmail');
  const submit=()=>form.dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));
  const edit=v=>{phone.value=v;phone.dispatchEvent(new w.Event('input',{bubbles:true}));};
  const patches=()=>s.calls.filter(c=>c.options.method==='PATCH');
  assert.equal(form.hidden,false);edit('809-555-0101');
  d.getElementById('closeBorrowerDetail').click();assert.equal(d.getElementById('borrowerDetailPanel').hidden,false);assert.equal(phone.value,'809-555-0101');
  d.querySelector('[data-view-borrower="8"]').click();assert.equal(d.getElementById('borrowerDetailTitle').textContent,'Ana Rodríguez');
  const unload=new w.Event('beforeunload',{cancelable:true});w.dispatchEvent(unload);assert(unload.defaultPrevented);
  if(!standalone){d.querySelector('[data-pd-view="cashier"]').click();await flush();assert.equal(w.location.hash,'#loans');const t=d.getElementById('pdClient');t.value='9';t.dispatchEvent(new w.Event('change'));await flush();assert.equal(t.value,'4');}
  email.value='invalid';submit();await flush();assert.equal(patches().length,0);email.value=' test@example.test ';
  // Native email fields trim outer whitespace.
  edit(' 809-555-0101 ');submit();submit();await flush();assert.equal(patches().length,1);
  const payload=JSON.parse(patches()[0].options.body);assert.equal(payload.phone,'809-555-0101');assert.equal(payload.email,'test@example.test');assert.equal(payload.expected_updated_at,'2026-10-10T12:00:00.000000');assert(!('full_name' in payload));assert(!('status' in payload));assert.equal(new Headers(patches()[0].options.headers).get('X-Tenant-ID'),'4');
  assert.equal(form.hidden,true);assert.match(d.getElementById('borrowerContactDetails').textContent,/809-555-0101/);assert.match(d.getElementById('borrowerContactMessage').textContent,/guardado/);
  d.getElementById('editBorrowerContact').click();await flush();edit('809-555-0102');s.control.fail=409;submit();await flush();assert.equal(form.hidden,false);assert.equal(phone.value,'809-555-0102');assert.match(d.getElementById('borrowerContactMessage').textContent,/cambió/);
  s.control.fail=422;submit();await flush();assert.equal(phone.value,'809-555-0102');assert.equal(d.getElementById('borrowerContactMessage').getAttribute('role'),'alert');
  s.control.fail='network';submit();await flush();assert.match(d.getElementById('borrowerContactMessage').textContent,/No se pudo confirmar/);assert.equal(phone.value,'809-555-0102');
  s.control.fail=null;w.confirm=()=>true;d.getElementById('refreshBorrowerContact').click();await flush();assert.equal(phone.value,'809-555-0101');
  edit('809-555-0103');let release;s.control.pending=new Promise(r=>release=r);submit();await wait();assert(d.getElementById('saveBorrowerContact').disabled);d.getElementById('closeBorrowerDetail').click();assert(!d.getElementById('borrowerDetailPanel').hidden);
  if(!standalone){d.querySelector('[data-pd-view="cashier"]').click();await wait();assert.equal(w.location.hash,'#loans');}
  release();await flush();assert(form.hidden);
  d.getElementById('editBorrowerContact').click();await flush();edit('');submit();await flush();assert.equal(JSON.parse(patches().at(-1).options.body).phone,null);
  d.getElementById('editBorrowerContact').click();await flush();edit('discard');d.getElementById('cancelBorrowerContact').click();assert(form.hidden);
  if(!standalone){d.getElementById('editBorrowerContact').click();await flush();edit('unsaved');const t=d.getElementById('pdClient');t.value='9';t.dispatchEvent(new w.Event('change'));await flush();assert(d.getElementById('borrowerContactForm').hidden);assert.equal(d.getElementById('borrowerContactPhone').value,'');}
  assert(!s.calls.some(c=>c.options.method==='PUT'));s.dom.window.close();
 }
 console.log('6 borrower-contact scenarios passed: role gates, fields-only PATCH, validation, trimming/clearing, duplicate-submit prevention, success/conflict/network failure, preserved drafts, pending writes, discard/navigation/business guards and tenant headers.');
})().catch(error=>{console.error(error);process.exitCode=1;});
