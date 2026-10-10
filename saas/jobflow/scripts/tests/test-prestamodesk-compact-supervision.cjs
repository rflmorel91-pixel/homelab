const {JSDOM}=require('jsdom'),fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..'),flush=()=>new Promise(r=>setTimeout(r,80));
(async()=>{for(const standalone of [true,false])for(const role of ['owner','administrator','supervisor','collector','cashier','member']){
const page=fs.readFileSync(path.join(root,'app',standalone?'prestamodesk-cobros-supervision.html':'prestamodesk-workspace.html'),'utf8'),dom=new JSDOM(page,{url:'https://example.test/prestamodesk/workspace#supervision',runScripts:'outside-only'}),w=dom.window,d=w.document;
w.Headers=Headers;w.Response=Response;w.AbortController=AbortController;w.CSS={escape:x=>x};w.HTMLElement.prototype.scrollIntoView=()=>{};w.localStorage.setItem('prestamodesk_collections_tenant_id','4');let calls=[];
w.URL.createObjectURL=()=> 'blob:synthetic';w.URL.revokeObjectURL=()=>{};w.HTMLAnchorElement.prototype.click=()=>{};
w.fetch=async(input,options={})=>{const u=new URL(input,'https://example.test');calls.push({u,options});let data=[];
if(u.pathname.endsWith('/access'))data={clients:[{tenant_id:4,client_number:1,name:'Synthetic',role}]};
else if(u.pathname.endsWith('/health'))data={status:'healthy'};
else if(u.pathname.endsWith('/export.csv'))return new Response('Synthetic CSV',{status:200});
else if(u.pathname.endsWith('/supervision'))data={aging_buckets:[{label:'1–30 días',loan_count:1,balance:'100'}],collectors:[],overdue_loan_count:1,overdue_balance:'100',total_recovered:'50'};
return new Response(JSON.stringify(data),{status:200,headers:{'content-type':'application/json'}});};
for(const m of page.matchAll(/<script[^>]*src="([^"]+)"/g))w.eval(fs.readFileSync(path.join(root,'app',m[1]),'utf8'));
for(const l of d.querySelectorAll('link[href$=".css"]')){const s=d.createElement('style');s.textContent=fs.readFileSync(path.join(root,'app',l.getAttribute('href')),'utf8');d.head.append(s);}await flush();
const allowed=['owner','administrator','supervisor'].includes(role),q=id=>d.getElementById(id);if(!allowed){assert(standalone?q('supervisionWorkspace').hidden:!q('supervisionWorkspace'));assert(!calls.some(c=>c.u.pathname.endsWith('/supervision')));dom.window.close();continue;}
assert(!q('supervisionWorkspace').hidden);assert.equal(q('supervisionWorkspace').dataset.supervisionTask,'overview');q('supervisionAsOf').value='2027-01-01';let count=calls.length;
for(const task of ['aging','promises','team','overview']){d.querySelector('button[data-supervision-task="'+task+'"]').click();for(const p of d.querySelectorAll('[data-supervision-panel]'))assert.equal(w.getComputedStyle(p).display==='none',p.dataset.supervisionPanel!==task);assert.equal(q('supervisionAsOf').value,'2027-01-01');assert.equal(calls.length,count);}
q('supervisionFilterForm').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await flush();assert.equal(calls.at(-1).u.searchParams.get('as_of'),'2027-01-01');assert.equal(new Headers(calls.at(-1).options.headers).get('X-Tenant-ID'),'4');
q('exportSupervisionButton').click();await flush();assert.equal(calls.at(-1).u.pathname.endsWith('/export.csv'),true);assert.equal(calls.at(-1).u.searchParams.get('as_of'),'2027-01-01');assert(!q('exportSupervisionButton').disabled);assert.equal(q('supervisionWorkspace').dataset.supervisionTask,'overview');dom.window.close();
}console.log('Compact Supervision checks passed: standalone/workspace, six roles, report visibility, retained cutoff, no tab requests, filtered refresh and tenant-bound CSV export.');})().catch(e=>{console.error(e);process.exit(1);});
