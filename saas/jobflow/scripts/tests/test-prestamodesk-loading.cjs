// Development dependency: jsdom. All requests are mocked; no real data changes.
const {JSDOM}=require('jsdom');const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..'),html=fs.readFileSync(path.join(root,'app/prestamodesk-workspace.html'),'utf8');
const tick=()=>new Promise(resolve=>setTimeout(resolve,15));
async function flush(){for(let i=0;i<12;i++)await tick();}
async function setup(role='owner',multi=false,standalone=false,scenario={}){
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
  if(scenario.request){const result=await scenario.request(pathname,options);if(result)return result;}
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
 let release;
 const held=new Promise(resolve=>release=resolve);
 const s=await setup('owner',false,false,{request:async p=>p.endsWith('/loans')?await held:undefined});
 const d=s.w.document;assert(!d.getElementById('pdReadState').hidden);assert.match(d.getElementById('pdReadState').textContent,/Cargando/);
 release(new Response('[]',{headers:{'content-type':'application/json'}}));await flush();
 assert(d.getElementById('pdReadState').hidden);assert.equal(d.querySelector('.pd-module #loanList').textContent.trim(),'No hay préstamos registrados.');
 assert(!s.calls.some(c=>['POST','PATCH','PUT','DELETE'].includes(c.options.method)));s.dom.window.close();
 for(const failure of ['network','server']){
  const s=await setup('owner',false,false,{request:async p=>{
   if(!p.endsWith('/loans'))return;
   if(failure==='network')throw new TypeError('NETWORK PRIVATE DETAIL');
   return new Response('{"detail":"SERVER PRIVATE DETAIL"}',{status:503,headers:{'content-type':'application/json'}});
  }});
  const status=s.w.document.getElementById('pdReadState');assert(!status.hidden);assert.match(status.textContent,/No se pudieron cargar/);assert(!status.textContent.includes('PRIVATE'));
  await s.click('administration');assert(status.hidden);s.dom.window.close();
 }
 let settle;
 const pending=new Promise(resolve=>settle=resolve);
 const stale=await setup('owner',false,false,{request:async p=>p.endsWith('/loans')?await pending:undefined});
 await stale.click('administration');assert(stale.w.document.getElementById('pdReadState').hidden);
 settle(new Response('{"detail":"failed"}',{status:503,headers:{'content-type':'application/json'}}));await flush();
 assert(stale.w.document.getElementById('pdReadState').hidden);stale.dom.window.close();
 console.log('Loading checks passed: delayed reads, valid empty results, expected missing policy, network/server failures, safe status text, no writes and stale-section isolation.');
})().catch(error=>{console.error(error);process.exitCode=1;});
