// Synthetic fixtures only; no real API requests.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
function fixture(file) {
 let code=fs.readFileSync(path.join(__dirname,file),'utf8').split('(async()=>{')[0];
 code=code.replace(' w.fetch=async(input,options={})=>{',' if(stored==="empty" || stored==="emptyloans")loans.length=0; if(stored==="empty")borrowers.length=0;\n w.fetch=async(input,options={})=>{');
 code=code.replace("if(stored!==null)w.sessionStorage", "if(stored!==null && !['empty','emptyloans'].includes(stored))w.sessionStorage");
 return new Function('require','__dirname',code+'\nreturn {setup,flush};')(require,__dirname);
}
(async()=>{
 const loan=fixture('test-prestamodesk-compact-loans.cjs');
 for(const standalone of [true,false])for(const role of ['owner','administrator','member']){
  let s=await loan.setup(role,standalone,'empty'),d=s.w.document;
  let count=s.calls.length,action=d.querySelector('#loanList [data-empty-action]');
  if(role==='member'){assert(!action);assert.match(d.getElementById('loanList').textContent,/propietario o administrador/);}
  else {assert.equal(action.textContent,'Crear prestatario');d.getElementById('borrowerName').value='Retained draft';action.click();assert.equal(d.getElementById('workspace').dataset.activeForm,'compactBorrowerForm');assert.equal(d.getElementById('borrowerName').value,'Retained draft');assert.equal(d.activeElement.id,'borrowerName');}
  assert.equal(s.calls.length,count);s.dom.window.close();
  s=await loan.setup(role,standalone);d=s.w.document;count=s.calls.length;
  d.getElementById('loanSearchQuery').value='no-match-<img src=x onerror=alert(1)>';d.getElementById('loanSearchQuery').dispatchEvent(new s.w.Event('input',{bubbles:true}));
  assert.equal(d.querySelectorAll('#loanList img').length,0);d.querySelector('#loanList [data-empty-action]').click();assert.equal(d.getElementById('loanSearchQuery').value,'');assert.equal(d.activeElement.id,'loanSearchQuery');assert(d.querySelector('#loanList .item-card'));
  if(role!=='member'){d.querySelector('[data-loan-tab="borrowers"]').click();d.getElementById('borrowerSearchQuery').value='missing';d.getElementById('borrowerSearchQuery').dispatchEvent(new s.w.Event('input',{bubbles:true}));d.querySelector('#borrowerList [data-empty-action]').click();assert.equal(d.getElementById('borrowerSearchQuery').value,'');assert.equal(d.activeElement.id,'borrowerSearchQuery');}
  assert.equal(s.calls.length,count);s.dom.window.close();
 }
 for(const standalone of [true,false]){
  const s=await loan.setup('owner',standalone,'emptyloans'),d=s.w.document,count=s.calls.length;
  d.getElementById('loanPrincipal').value='1234';const action=d.querySelector('#loanList [data-empty-action]');assert.equal(action.textContent,'Crear préstamo');action.click();assert.equal(d.getElementById('workspace').dataset.activeForm,'compactLoanForm');assert.equal(d.getElementById('loanPrincipal').value,'1234');assert.equal(s.calls.length,count);s.dom.window.close();
 }
 const caja=fixture('test-prestamodesk-compact-caja.cjs');
 for(const standalone of [true,false])for(const role of ['owner','administrator','member','cashier']){
  const s=await caja.setup(role,standalone,'empty'),d=s.w.document;
  assert(!d.querySelector('[data-empty-show-loans]'));
  d.getElementById('loanSearchQuery').value='missing';d.getElementById('loanSearchForm').dispatchEvent(new s.w.Event('submit',{bubbles:true,cancelable:true}));await caja.flush();
  const count=s.calls.length;d.querySelector('[data-empty-show-loans]').click();await caja.flush();assert.equal(d.getElementById('loanSearchQuery').value,'');assert.equal(d.activeElement.id,'loanSearchQuery');assert.equal(s.calls.length,count+1);assert(!s.calls.some(c=>['POST','PATCH','DELETE'].includes(c.options.method)));s.dom.window.close();
 }
 console.log('Empty-state checks passed: standalone/workspace, role-controlled creation, zero-data/filter distinctions, retained drafts, focus, safe text, no creation requests and Caja read-only recovery.');
})().catch(error=>{console.error(error);process.exit(1);});
