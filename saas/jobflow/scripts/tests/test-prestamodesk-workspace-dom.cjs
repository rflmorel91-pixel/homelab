// Development dependency: jsdom. All requests are mocked; no real data changes.
const {JSDOM}=require('jsdom');const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..'),html=fs.readFileSync(path.join(root,'app/prestamodesk-workspace.html'),'utf8');
const tick=()=>new Promise(resolve=>setTimeout(resolve,15));
async function flush(){for(let i=0;i<12;i++)await tick();}
async function setup(role='owner',multi=false,standalone=false){
 const page=standalone?fs.readFileSync(path.join(root,'app/prestamodesk-app.html'),'utf8'):html;
 const dom=new JSDOM(page,{url:'https://example.test/prestamodesk/workspace',runScripts:'outside-only'});const w=dom.window;
 w.Headers=Headers;w.Response=Response;w.AbortController=AbortController;w.CSS={escape:value=>value};w.confirm=()=>true;w.print=()=>{};w.HTMLElement.prototype.scrollIntoView=()=>{};
 if(standalone)w.localStorage.setItem("prestamodesk_tenant_id","4");
 const calls=[];let denied=false;
 const loan={id:1,borrower_id:7,loan_type:'personal',status:'active',currency:'DOP',principal_amount:'1000',total_interest:'100',total_due:'1100',installment_count:2,late_fee_enabled:false,installments:[{id:1,sequence_number:1,due_date:'2026-11-09',principal_due:'500',interest_due:'50',total_due:'550',paid_amount:'0',status:'pending'}]};
 const restricted=['/borrowers','/prospects','/applications','/prospects/public-page','/late-fee-policy'];
 const clients=[{tenant_id:4,client_number:1,name:'TEST Demo',role}];if(multi)clients.push({tenant_id:9,client_number:2,name:'SECOND Demo',role});
 w.fetch=async(input,options={})=>{
  const url=new URL(input,'https://example.test'),pathname=url.pathname;calls.push({url:pathname,options});
  let data=[],status=200;
  if(pathname.endsWith('/health'))data={status:'healthy'};
  else if(pathname.endsWith('/access')){data=denied?{detail:'Authentication required'}:{clients};if(denied)status=401;}
  else if(pathname.endsWith('/logout'))data={status:'signed_out'};
  else if(role==='member'&&restricted.some(p=>pathname.endsWith(p))){status=403;data={detail:'Tenant owner access required'};}
  else if(role==='member'&&pathname.endsWith('/cashier/loans'))data=[{...loan,borrower_full_name:'TEST Member Borrower',balance_due:'1100',ordinary_balance_due:'1100',late_fee_balance_due:'0'}];
  else if(role==='member'&&pathname.endsWith('/loans/1'))data=loan;
  else if(role==='member'&&pathname.endsWith('/loans'))data=[loan];
  else if(pathname.endsWith('/public-page'))data={tenant_slug:'test-demo'};
  else if(pathname.endsWith('/late-fee-policy')){status=404;data={detail:'not configured'};}
  else if(pathname.endsWith('/supervision'))data={aging_buckets:[],collectors:[],overdue_balance:'0',assigned_overdue_balance:'0',unassigned_overdue_balance:'0',total_recovered:'0',total_promised:'0',total_fulfilled:'0',promise_completion_rate:'0'};
  else if(pathname.endsWith('/team'))data={members:[],assignable_roles:['collector'],roles:[]};
  else if(pathname.endsWith('/invitations'))data={invitations:[]};
  else if(pathname.endsWith('/closing-preview'))data={payment_count:0,total_collected:'0.00',cash_expected:'0.00',bank_transfer_total:'0.00',card_total:'0.00',other_total:'0.00'};
  return new Response(JSON.stringify(data),{status,headers:{'content-type':'application/json'}});
 };
 for(const src of page.matchAll(/<script src="([^"]+)"/g))w.eval(fs.readFileSync(path.join(root,'app',src[1]),'utf8'));
 await flush();return{w,dom,calls,deny(){denied=true;},button(view){return w.document.querySelector(`[data-pd-view=${view}]`);},async click(view){this.button(view).click();await flush();}};
}
(async()=>{
 const a=await setup();assert.equal(a.w.document.getElementById('pdWorkspace').hidden,false);assert.equal(a.w.location.hash,'#summary');
 const mountHost=a.w.document.getElementById("pdHost"), originalAppend=mountHost.append.bind(mountHost);
 mountHost.append=(section)=>{assert.equal(section.querySelector("#authPanel").hidden,true,"login must be hidden before mounting");originalAppend(section);};
 for(const view of ['loans','cashier','collections','supervision','administration','summary']){
  await a.click(view);assert.equal(a.w.location.hash,'#'+view);assert.equal(a.button(view).getAttribute('aria-current'),'page');
  const ids=[...a.w.document.querySelectorAll('[id]')].map(x=>x.id);assert.equal(new Set(ids).size,ids.length,'duplicate IDs in '+view);
  const host=a.w.document.getElementById('pdHost');assert(host.children.length===1);assert.equal(host.querySelector('#authPanel').hidden,true,'screen failed to initialize: '+view);
 }
 assert(a.calls.filter(x=>x.url.startsWith('/api/v1/products/')).every(x=>new Headers(x.options.headers).get('X-Tenant-ID')==='4'));
 let readOnlyPrompts=0;a.w.confirm=()=>{readOnlyPrompts++;return false;};
 for(const [view,formId,next] of [['cashier','loanSearchForm','collections'],['collections','portfolioFilterForm','supervision'],['supervision','supervisionFilterForm','summary']]){
  await a.click(view);const field=a.w.document.querySelector('#'+formId+' input, #'+formId+' select');assert(field);field.dispatchEvent(new a.w.Event('input',{bubbles:true}));field.dispatchEvent(new a.w.Event('change',{bubbles:true}));await a.click(next);assert.equal(a.w.location.hash,'#'+next);
 }
 assert.equal(readOnlyPrompts,0,'read-only filters must not warn about unsaved data');a.w.confirm=()=>true;

 const loan=a.w.document.getElementById('pdHost');await a.click('loans');const input=a.w.document.querySelector('#borrowerName');input.value='Unsubmitted';input.dispatchEvent(new a.w.Event('input',{bubbles:true}));a.w.confirm=()=>false;await a.click('cashier');assert.equal(a.w.location.hash,'#loans');a.w.confirm=()=>true;await a.click('cashier');assert.equal(a.w.location.hash,'#cashier');
 a.deny();await a.click('loans');assert.equal(a.w.document.getElementById('pdWorkspace').hidden,true);assert.equal(a.w.document.getElementById('pdHost').children.length,0);a.dom.window.close();
 for(const [role,views] of Object.entries({owner:['summary','loans','cashier','collections','supervision','administration'],administrator:['summary','loans','cashier','collections','supervision','administration'],collector:['collections'],supervisor:['collections','supervision'],cashier:['cashier'],member:['summary','loans','cashier']})){
  const s=await setup(role);const visible=[...s.w.document.querySelectorAll('[data-pd-view]')].filter(n=>!n.hidden).map(n=>n.dataset.pdView);assert.deepEqual(visible,views);
  s.w.location.hash='#administration';await flush();assert(views.includes(s.w.location.hash.slice(1)),'role route bypass');s.dom.window.close();
 }
 for(const standalone of [false,true]){
  const member=await setup('member',false,standalone),d=member.w.document;
  const check=()=>{
   assert.equal(d.getElementById('authPanel').hidden,true,'member must stay authenticated');
   assert.equal(d.getElementById('workspace').hidden,false);
   for(const id of ['borrowerForm','loanForm','applicationList','prospectList','borrowerList','lateFeePolicyForm'])assert.equal(d.getElementById(id).closest('section').hidden,true,'management panel exposed: '+id);
   assert.equal(d.getElementById('loanLateFeeForm').hidden,true);
   assert.equal(d.getElementById('borrowerCount').closest('article').hidden,true,'restricted count must not show a misleading zero');
   assert.equal(d.getElementById('activeLoanCount').textContent,'1');
   assert.match(d.getElementById('loanList').textContent,/TEST Member Borrower/);
   assert(!member.calls.some(c=>restrictedForMember(c.url)),'member requested a management endpoint');
  };
  function restrictedForMember(url){return ['/borrowers','/prospects','/applications','/prospects/public-page','/late-fee-policy'].some(p=>url.endsWith(p));}
  check();
  if(!standalone){await member.click('loans');check();}
  d.querySelector('[data-view-loan="1"]').click();await flush();
  assert.equal(d.getElementById('loanDetailPanel').hidden,false);
  assert.match(d.getElementById('loanDetailTitle').textContent,/TEST Member Borrower/);
  assert.equal(d.getElementById('paymentPanel').hidden,false,'member payment form unavailable');
  assert.equal(d.getElementById('paymentCorrectionPanel').hidden,true);
  if(!standalone){await member.click('cashier');await member.click('summary');check();}
  member.dom.window.close();
 }
 const m=await setup('owner',true);assert.equal(m.w.document.getElementById('pdClient').options.length,2);const select=m.w.document.getElementById('pdClient');select.value='9';select.dispatchEvent(new m.w.Event('change'));await flush();assert.match(m.w.document.getElementById('pdContext').textContent,/SECOND Demo/);assert(m.calls.some(x=>new Headers(x.options.headers).get('X-Tenant-ID')==='9'));
 m.w.document.getElementById('pdLogout').click();await flush();assert.equal(m.w.document.getElementById('pdHost').children.length,0);assert.equal(m.w.document.getElementById('pdWorkspace').hidden,true);m.dom.window.close();
 console.log('Workspace DOM scenarios passed: six sections, scoped IDs, tenant binding, six roles, denied-session clearing, unsaved form guard, multi-client switching and logout.');
})().catch(error=>{console.error(error);process.exitCode=1;});
