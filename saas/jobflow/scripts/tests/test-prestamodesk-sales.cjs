const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..');
const html=fs.readFileSync(path.join(root,'app/prestamodesk.html'),'utf8');
const filename=html.match(/src="\/assets\/(prestamodesk-sales-[a-f0-9]+\.js)"/)[1];
const source=fs.readFileSync(path.join(root,'app/assets',filename),'utf8');
function setup(fetch){
 const button={disabled:false};const status={};const screen={};const steps=Array.from({length:4},(_,i)=>({dataset:{demoStep:String(i)},setAttribute(k,v){this[k]=v},addEventListener(_,fn){this.click=fn}}));
 const form={reportValidity:()=>true,querySelector:()=>button,reset(){this.resetCalled=true},addEventListener(_,fn){this.submit=fn}};
 const values={business_name:' Demo firm ',contact_name:' Rafael ',email:'demo@example.test',phone:'',business_type:'Préstamos personales',portfolio_size:'1–50',message:'Cuotas',consent:'on'};
 const ctx={document:{getElementById:id=>({demoScreen:screen,demoRequestForm:form,requestStatus:status})[id],querySelectorAll:()=>steps},FormData:class{*[Symbol.iterator](){yield* Object.entries(values)}},fetch};
 vm.createContext(ctx);vm.runInContext(source,ctx);return{form,status,screen,steps,button,submit:()=>form.submit({preventDefault(){}})};
}
(async()=>{
 let calls=0,resolve;
 const a=setup((url,opts)=>{calls++;assert.equal(url,'/api/v1/public/products/prestamodesk/leads');const p=JSON.parse(opts.body);assert.equal(p.business_name,'Demo firm');assert.match(p.message,/Autorizó contacto/);return new Promise(r=>resolve=r)});
 a.steps[3].click();assert.match(a.screen.innerHTML,/DEMO-001/);
 const first=a.submit();await a.submit();assert.equal(calls,1);resolve({ok:true,json:async()=>({lead_id:12})});await first;assert.match(a.status.textContent,/#12/);assert.equal(a.button.disabled,true);
 const b=setup(async()=>({ok:false,status:429}));await b.submit();assert.match(b.status.textContent,/demasiadas/);assert.equal(b.button.disabled,false);
 const c=setup(async()=>{throw Error('offline')});await c.submit();assert.match(c.status.textContent,/podría haberse recibido/);
 const d=setup(async()=>({ok:true,json:async()=>{throw Error('malformed')}}));await d.submit();assert.match(d.status.textContent,/Solicitud recibida/);
 assert(!/style=|<style|onclick=/.test(html));
 console.log('5 sales-page scenarios passed; no real requests sent.');
})().catch(e=>{console.error(e);process.exitCode=1});
