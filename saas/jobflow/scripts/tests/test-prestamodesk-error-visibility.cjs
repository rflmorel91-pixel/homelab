// DOM notification checks only; no real API requests, invitations or payments.
const {JSDOM}=require('jsdom'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..');
function asset(page,prefix){const html=fs.readFileSync(path.join(root,'app',page),'utf8'),name=html.match(new RegExp('/assets/('+prefix+'-[a-f0-9]+\\.js)'))[1];return {html,source:fs.readFileSync(path.join(root,'app/assets',name),'utf8')};}
const workspace=asset('prestamodesk-workspace.html','prestamodesk-workspace-screens');
const configs=[
 ['prestamodesk-app.html','prestamodesk-app','errorMessage','function showError(','function showSuccess(','showError'],
 ['prestamodesk-caja.html','prestamodesk-caja','errorMessage','function showError(','function showSuccess(','showError'],
 ['prestamodesk-administracion.html','prestamodesk-administration','administrationMessage','  function notify(','  async function request(','notify'],
 ['prestamodesk-administracion.html','prestamodesk-administration','administrationMemberMessage','  function detailNotify(','  function selectMemberTab(','detailNotify']
];
let count=0;
for(const [page,prefix,id,begin,end,fn] of configs){const {html,source}=asset(page,prefix),start=source.indexOf(begin),finish=source.indexOf(end,start),code=source.slice(start,finish);assert(start>=0&&finish>start);assert(workspace.source.includes(code),'workspace lost notification implementation');
 for(const compiled of [false,true]){
  // Render the real standalone markup or its compiled screen markup.
  let markup=html;if(compiled){const loader=new JSDOM('',{runScripts:'outside-only'});loader.window.eval(workspace.source);markup=loader.window.PrestamoDeskScreens[prefix==='prestamodesk-app'?'loans':prefix==='prestamodesk-caja'?'cashier':'administration'].html;loader.window.close();}
  const dom=new JSDOM(markup,{runScripts:'outside-only'}),w=dom.window,d=w.document,box=d.getElementById(id);assert(box);
  for(let parent=box.parentElement;parent;parent=parent.parentElement)parent.hidden=false;
  const field=d.querySelector('input:not([type=hidden])');field.value='Datos que deben conservarse';field.focus();const focus=d.activeElement;
  const scroll=[];box.scrollIntoView=options=>{assert.equal(box.hidden,false);assert.equal(box.getAttribute('role'),'alert');assert.equal(box.textContent,'<b>Error de prueba</b>');scroll.push(options);};
  w.eval(`const errorMessage=document.getElementById('errorMessage'); const successMessage=document.getElementById('successMessage'); const message=document.getElementById('administrationMessage');`+code);
  const show=()=>w[fn]('<b>Error de prueba</b>',true);show();assert.equal(scroll.length,1);assert.equal(scroll[0].behavior,'instant');assert.equal(scroll[0].block,'center');assert.equal(box.getAttribute('aria-atomic'),'true');assert.equal(box.querySelector('b'),null,'errors must use text, not HTML');assert.equal(field.value,'Datos que deben conservarse');assert.equal(d.activeElement,focus,'error must not move focus');show();assert.equal(scroll.length,2,'repeated error must remain visible');
  if(fn!=='showError'){w[fn]('Guardado',false);assert.equal(scroll.length,2,'success must not scroll');assert.equal(box.getAttribute('role'),'status');}
  const parent=box.parentElement;parent.hidden=true;show();assert.equal(scroll.length,2,'hidden section must not scroll');parent.hidden=false;box.remove();show();assert.equal(scroll.length,2,'disposed screen must not scroll');
  dom.window.close();count++;
 }
}
console.log(`${count} error-visibility DOM scenarios passed: standalone/workspace, loans/Caja/team/member errors, instant scrolling, alerts, repeated messages, preserved values/focus, polite success and hidden/disposed sections.`);
