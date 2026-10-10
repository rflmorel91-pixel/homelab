const {JSDOM}=require('jsdom'),fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..');const flush=()=>new Promise(r=>setTimeout(r,100));
(async()=>{for(const standalone of [true,false])for(const role of ['owner','administrator','supervisor','collector']){
const page=fs.readFileSync(path.join(root,'app',standalone?'prestamodesk-cobros.html':'prestamodesk-workspace.html'),'utf8');
const dom=new JSDOM(page,{url:'https://example.test/prestamodesk/workspace#collections',runScripts:'outside-only'}),w=dom.window,d=w.document;
w.Headers=Headers;w.Response=Response;w.AbortController=AbortController;w.CSS={escape:x=>x};w.HTMLElement.prototype.scrollIntoView=()=>{};w.confirm=()=>false;
w.localStorage.setItem('prestamodesk_collections_tenant_id','4');let calls=0,release,pending=null;
w.fetch=async(input,options={})=>{calls++;const u=new URL(input,'https://example.test');let data=[];
if(options.method==='POST'&&u.pathname.endsWith('/activities')){if(pending)await pending;data={};}
else if(u.pathname.endsWith('/access'))data={clients:[{tenant_id:4,client_number:1,name:'Synthetic',role}]};
else if(u.pathname.endsWith('/health'))data={status:'healthy'};
else if(u.pathname.includes('/portfolio'))data=[{loan_id:1,borrower_full_name:'Synthetic',borrower_document_number:'TEST',total_balance_due:'100',overdue_installment_count:1,days_overdue:1}];
return new Response(JSON.stringify(data),{status:200,headers:{'content-type':'application/json'}});};
for(const match of page.matchAll(/<script[^>]*src="([^"]+)"/g))w.eval(fs.readFileSync(path.join(root,'app',match[1]),'utf8'));
for(const link of d.querySelectorAll('link[href$=".css"]')){const s=d.createElement('style');s.textContent=fs.readFileSync(path.join(root,'app',link.getAttribute('href')),'utf8');d.head.append(s);}await flush();
const q=id=>d.getElementById(id),tab=x=>d.querySelector('button[data-collection-task="'+x+'"]').click(),detail=x=>d.querySelector('button[data-collection-detail="'+x+'"]').click();
assert(!q('collectionsWorkspace').hidden);assert.equal(q('collectionsWorkspace').dataset.collectionTask,'portfolio');
assert.equal(q('collectionAssignmentTab').hidden,role==='collector');let count=calls;tab('overdue');assert.equal(w.getComputedStyle(q('collectionPortfolioPanel')).display,'none');tab('portfolio');assert.equal(calls,count);
const button=q('portfolioList').querySelector('button');assert(button);button.click();await flush();assert(!q('collectionDetailPanel').hidden);q('activityOutcome').value='Draft';q('promiseAmount').value='25';count=calls;
detail('promise');assert.equal(w.getComputedStyle(q('collectionActivityPanel')).display,'none');detail('history');detail('assignment');assert.equal(q('collectionDetailPanel').dataset.collectionDetail,role==='collector'?'history':'assignment');detail('activity');tab('overdue');tab('portfolio');assert.equal(q('activityOutcome').value,'Draft');assert.equal(q('promiseAmount').value,'25');assert.equal(calls,count);
pending=new Promise(r=>release=r);q('activityForm').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await flush();tab('overdue');detail('promise');q('closeCollectionDetail').click();assert.equal(q('collectionsWorkspace').dataset.collectionTask,'portfolio');assert.equal(q('collectionDetailPanel').dataset.collectionDetail,'activity');assert(!q('collectionDetailPanel').hidden);
if(!standalone){d.querySelector('[data-pd-view="loans"]').click();await flush();assert.equal(w.location.hash,'#collections');}
release();await flush();detail('promise');assert.equal(q('collectionDetailPanel').dataset.collectionDetail,'promise');dom.window.close();
}console.log('Compact Cobros checks passed: standalone/workspace, four roles, task visibility, retained drafts, no tab requests and pending-write navigation guards.');})().catch(e=>{console.error(e);process.exit(1);});
