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
for(const role of ['owner','administrator','member','cashier','supervisor','collector']){
 const s=await setup(role,true),d=s.w.document,actions=d.getElementById('pdSummaryActions');const summaryAllowed=['owner','administrator','member'].includes(role);assert.equal(actions.hidden,!summaryAllowed);
 if(!summaryAllowed){s.dom.window.close();continue;}
 const expected=role==='member'?['loans','cashier']:['loans','cashier','collections','administration'];
 assert.deepEqual([...actions.querySelectorAll('button')].filter(b=>!b.hidden).map(b=>b.dataset.pdSummaryView),expected);
 const count=s.calls.length;actions.querySelector('summary').click();assert.equal(s.calls.length,count);
 for(const view of expected){actions.querySelector('[data-pd-summary-view='+view+']').click();await flush();assert.equal(s.w.location.hash,'#'+view);assert(actions.hidden);await s.click('summary');assert(!actions.hidden);}
 assert(!s.calls.some(c=>['POST','PATCH','PUT','DELETE'].includes(c.options.method)));
 d.getElementById('pdClient').value='9';d.getElementById('pdClient').dispatchEvent(new s.w.Event('change'));await flush();assert(d.getElementById('pdContext').textContent.includes('SECOND'));actions.querySelector('[data-pd-summary-view=cashier]').click();await flush();assert(s.calls.filter(c=>c.url.includes('/cashier/')).every(c=>new Headers(c.options.headers).get('X-Tenant-ID')==='4'||new Headers(c.options.headers).get('X-Tenant-ID')==='9'));
 await s.click('summary');s.deny();d.getElementById('pdRefresh').click();await flush();assert(actions.hidden);assert(d.getElementById('pdWorkspace').hidden);s.dom.window.close();
}
console.log('Summary shortcuts passed: six roles, summary-only visibility, existing guarded navigation, no writes, tenant switching, explanatory disclosure and denied-session clearing.');
})().catch(e=>{console.error(e);process.exit(1);});
