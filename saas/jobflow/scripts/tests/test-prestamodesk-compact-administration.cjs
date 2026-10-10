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
for(const standalone of [true,false])for(const role of ['owner','administrator']){
 const s=await setup(role,standalone),d=s.w.document,q=id=>d.getElementById(id),composer=q('administrationInviteComposer');
 assert(!composer.open);const count=s.calls.length;q('inviteMemberButton').click();assert(composer.open);assert(!q('invitationsSection').hidden);assert.equal(d.activeElement.name,'display_name');assert.equal(s.calls.length,count);
 q('administrationInvite').elements.display_name.value='Draft';q('administrationInvite').elements.email.value='draft@example.test';composer.open=false;q('teamTab').click();q('invitationsTab').click();assert.equal(q('administrationInvite').elements.display_name.value,'Draft');assert.equal(q('administrationInvite').elements.email.value,'draft@example.test');assert.equal(s.calls.length,count);
 q('inviteMemberButton').click();await s.create();composer.open=false;assert(!s.card().hidden);assert(!composer.contains(s.card()));assert(unload(s));noStoredToken(s);
 q('teamTab').focus();q('teamTab').dispatchEvent(new s.w.KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true}));assert.equal(q('invitationsTab').getAttribute('aria-selected'),'true');assert.equal(d.activeElement,q('invitationsTab'));s.dom.window.close();
}
console.log('Compact Administration checks passed: standalone/workspace, owner/administrator, collapsed invitation composer, direct-open focus, retained drafts, keyboard tabs and unsaved-link guards.');
})().catch(e=>{console.error(e);process.exit(1);});
