// Synthetic invitation tokens; all API and clipboard calls mocked.
const {JSDOM}=require('jsdom'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..'),base='/api/v1/products/prestamodesk/administration';
const tick=()=>new Promise(r=>setTimeout(r,15));async function flush(){for(let i=0;i<12;i++)await tick();}
async function setup(role='owner',standalone=false){
 const html=fs.readFileSync(path.join(root,'app',standalone?'prestamodesk-administracion.html':'prestamodesk-workspace.html'),'utf8');
 const dom=new JSDOM(html,{url:'https://example.test/prestamodesk/workspace#administration',runScripts:'outside-only'}),w=dom.window;
 w.Headers=Headers;w.Response=Response;w.AbortController=AbortController;w.CSS={escape:v=>v};w.HTMLElement.prototype.scrollIntoView=()=>{};w.print=()=>{};w.localStorage.setItem('prestamodesk_tenant_id','4');
 let approve=false,failCopy=false,pendingCopy=null,failRefresh=false,created=0;const calls=[],copied=[],prompts=[],invitations=[];
 w.confirm=text=>{prompts.push(text);return approve;};
 Object.defineProperty(w.navigator,'clipboard',{configurable:true,value:{writeText:async text=>{if(pendingCopy)await pendingCopy;if(failCopy)throw new Error('denied');copied.push(text);}}});
 w.fetch=async(input,options={})=>{
  const u=new URL(input,'https://example.test'),method=options.method||'GET';calls.push({path:u.pathname,method});let data=[],status=200;
  if(u.pathname.endsWith('/health'))data={status:'healthy'};
  else if(u.pathname.endsWith('/access'))data={clients:[{tenant_id:4,client_number:1,name:'TEST First',role},{tenant_id:9,client_number:2,name:'TEST Second',role}].slice(0,standalone?1:2)};
  else if(u.pathname.endsWith('/logout'))data={status:'signed_out'};
  else if(u.pathname===base+'/team'){if(failRefresh){status=500;data={detail:'failed'};}else data={members:[],assignable_roles:['member'],roles:[]};}
  else if(u.pathname===base+'/invitations'&&method==='POST'){
   const body=JSON.parse(options.body);created++;const record={id:created,...body,status:'pending'};invitations.push(record);
   data={...record,activation_path:'/accept-invitation#token=SYNTHETIC-TOKEN-'+created,expires_at:'2026-10-12T20:00:00Z'};
  }
  else if(u.pathname===base+'/invitations')data={invitations};
  else if(u.pathname.endsWith('/revoke')){invitations.find(x=>x.id===Number(u.pathname.split('/').at(-2))).status='revoked';data={status:'revoked'};}
  else if(u.pathname.endsWith('/late-fee-policy')){status=404;data={detail:'not configured'};}
  else if(u.pathname.endsWith('/public-page'))data={tenant_slug:'test'};
  else if(u.pathname.endsWith('/closing-preview'))data={payment_count:0,total_collected:'0',cash_expected:'0',bank_transfer_total:'0',card_total:'0',other_total:'0'};
  return new Response(JSON.stringify(data),{status,headers:{'content-type':'application/json'}});
 };
 for(const match of html.matchAll(/<script[^>]*src="([^"]+)"/g))w.eval(fs.readFileSync(path.join(root,'app',match[1]),'utf8'));
 await flush();return {w,dom,calls,copied,prompts,approve:v=>approve=v,fail:v=>failCopy=v,pending:p=>pendingCopy=p,refreshFail:v=>failRefresh=v,created:()=>created,
  async create(){const f=w.document.getElementById('administrationInvite');f.elements.display_name.value='SYNTHETIC Member';f.elements.email.value='synthetic@example.test';f.elements.role.value='member';f.dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await flush();},
  card(){return w.document.getElementById('administrationActivation');},button(text){return [...this.card().querySelectorAll('button')].find(x=>x.textContent===text);},async clickView(view){w.document.querySelector('[data-pd-view='+view+']').click();await flush();}};
}
function unload(s){const e=new s.w.Event('beforeunload',{cancelable:true});s.w.dispatchEvent(e);return e.defaultPrevented;}
function noStoredToken(s){for(const storage of [s.w.localStorage,s.w.sessionStorage])for(let i=0;i<storage.length;i++)assert(!storage.getItem(storage.key(i)).includes('SYNTHETIC-TOKEN'),'token persisted in browser storage');}
(async()=>{
 for(const role of ['owner','administrator'])for(const standalone of [false,true]){
  const s=await setup(role,standalone),d=s.w.document;await s.create();
  assert.equal(s.card().hidden,false);assert.match(s.card().textContent,/correo no se envía automáticamente/);
  const link=s.card().querySelector('a');assert.equal(link.target,'_blank');assert.equal(link.rel,'noopener noreferrer');
  assert.equal(s.card().querySelector('input').value,'https://example.test/accept-invitation#token=SYNTHETIC-TOKEN-1');
  assert(unload(s),'unsaved invitation must protect unload');noStoredToken(s);
  d.getElementById('administrationRefresh').click();await flush();assert.equal(s.card().hidden,false,'refresh lost link');
  d.getElementById('teamTab').click();d.getElementById('invitationsTab').click();assert.equal(s.card().hidden,false,'admin tabs lost link');
  await s.create();assert.equal(s.created(),1,'replacement must require confirmation');
  const logoutId=standalone?'logoutButton':'pdLogout';d.getElementById(logoutId).click();await flush();assert(!s.calls.some(c=>c.path.endsWith('/logout')),'logout bypassed invitation guard');
  if(!standalone){await s.clickView('cashier');assert.equal(s.w.location.hash,'#administration');assert.match(d.getElementById('pdMessage').textContent,/enlace de invitación/);}
  s.button('Copiar enlace').click();await flush();assert.deepEqual(s.copied,['https://example.test/accept-invitation#token=SYNTHETIC-TOKEN-1']);assert(!unload(s),'successful copy must release guard');
  noStoredToken(s);if(!standalone){await s.clickView('cashier');assert.equal(s.w.location.hash,'#cashier');assert.equal(d.querySelector('#administrationActivation'),null);}else{d.getElementById(logoutId).click();await flush();assert.equal(s.card().hidden,true);}
  s.dom.window.close();
 }
 const fallback=await setup();await fallback.create();fallback.fail(true);fallback.button('Copiar enlace').click();await flush();assert(unload(fallback));assert.match(fallback.card().textContent,/No se pudo copiar/);assert.equal(fallback.copied.length,0);
 fallback.button('Ya guardé o compartí el enlace').click();assert(!unload(fallback));fallback.dom.window.close();
 const busy=await setup();await busy.create();busy.button('Copiar enlace').click();await flush();assert(!unload(busy));let resolve;busy.pending(new Promise(r=>resolve=r));busy.button('Copiar enlace').click();busy.approve(true);await busy.clickView('cashier');assert.equal(busy.w.location.hash,'#administration','pending copy must block leaving even after prior save');resolve();await flush();assert(!unload(busy));busy.dom.window.close();
 const refresh=await setup();refresh.refreshFail(true);await refresh.create();assert.equal(refresh.card().hidden,false,'post-create refresh failure lost token');assert.match(refresh.w.document.getElementById('administrationMessage').textContent,/Guarde el enlace/);refresh.dom.window.close();
 const switcher=await setup();await switcher.create();let select=switcher.w.document.getElementById('pdClient');select.value='9';select.dispatchEvent(new switcher.w.Event('change'));await flush();assert.equal(select.value,'4');assert.equal(switcher.card().hidden,false);
 switcher.approve(true);select.value='9';select.dispatchEvent(new switcher.w.Event('change'));await flush();assert(!switcher.card() || switcher.card().hidden);assert.equal(switcher.w.document.querySelector('#administrationActivation input'),null);assert.match(switcher.w.document.getElementById('pdContext').textContent,/SECOND|Second/);noStoredToken(switcher);switcher.dom.window.close();
 const revoked=await setup();await revoked.create();revoked.approve(true);[...revoked.w.document.querySelectorAll('#administrationInvitations button')].find(x=>x.textContent==='Revocar').click();await flush();assert.equal(revoked.card().hidden,true);assert(!unload(revoked));revoked.dom.window.close();
 console.log('Invitation-sharing scenarios passed: owner/administrator standalone/workspace, absolute copy, manual fallback, refresh/tab retention, replacement/logout/navigation/unload guards, pending copy, refresh failure, business switching, revocation and no token storage.');
})().catch(error=>{console.error(error);process.exitCode=1;});
