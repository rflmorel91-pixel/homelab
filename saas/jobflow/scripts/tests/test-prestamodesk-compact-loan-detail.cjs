// Synthetic schedules only; no real loans, payments or services.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
let code=fs.readFileSync(path.join(__dirname,'test-prestamodesk-compact-loans.cjs'),'utf8').split('(async()=>{')[0];
code=code.replace("else if(u.pathname.startsWith(base+'/loans/'))data=detail(loans.find(l=>l.id===Number(u.pathname.split('/').pop())));", "else if(u.pathname.startsWith(base+'/loans/')){if(control.schedulePending)await control.schedulePending;if(control.scheduleFail){status=500;data={detail:'Synthetic failure'};}else data=detail(loans.find(l=>l.id===Number(u.pathname.split('/').pop())));}");
code=code.replace("for(const match of page.matchAll(/<script[^>]*src=\"([^\"]+)\"/g))w.eval(fs.readFileSync(path.join(root,'app',match[1]),'utf8'));", "w.eval([...page.matchAll(/<script[^>]*src=\"([^\"]+)\"/g)].map(match=>fs.readFileSync(path.join(root,'app',match[1]),'utf8').replaceAll('window.prestamodeskSchedulePrint = {capture, clear};', 'window.prestamodeskSchedulePrint = {capture, clear}; document.getElementById(\"printLoanScheduleButton\").syntheticOpenLoan=openLoan;').replaceAll('let paymentNeedsReview = false;', 'let paymentNeedsReview = false; document.getElementById(\"printLoanScheduleButton\").syntheticSetPaymentState=(pending,uncertain)=>{paymentSubmitting=pending;paymentNeedsReview=uncertain;};')).join('\\n'));");
code=code.replace("else data=detail(loans.find(l=>l.id===Number(u.pathname.split('/').pop())));", "else {data=detail(loans.find(l=>l.id===Number(u.pathname.split('/').pop())));if(control.scheduleRows)data.installments=Array.from({length:control.scheduleRows},(_,i)=>({...data.installments[0],id:410+i,sequence_number:i+1}));}");
const {setup,flush}=new Function('require','__dirname',code+'\nreturn {setup,flush};')(require,__dirname);
(async()=>{
 for(const standalone of [true,false])for(const role of ['owner','administrator','member']){
 const s=await setup(role,standalone),w=s.w,d=w.document,q=id=>d.getElementById(id),root=standalone?d.body:d.querySelector('.pd-module');
 q('loanList').querySelector('button').click();await flush();
 const workspace=q('workspace'),tabs=[...q('loanDetailViews').querySelectorAll('button')];
 assert.equal(workspace.dataset.loanDetailView,'installments');
 assert.equal(tabs[2].hidden,role==='member');
 q('paymentAmount').value='123';q('paymentReference').value='draft';q('loanLateFeeSelected').checked=true;
 const before=s.calls.length;tabs[1].click();assert.equal(workspace.dataset.loanDetailView,'payments');
 assert.equal(w.getComputedStyle(q('paymentPanel')).display,'none');
 assert.equal(w.getComputedStyle(d.querySelector('[data-loan-detail-pane="installments"]')).display,'none');
 tabs[2].click();assert.equal(workspace.dataset.loanDetailView,role==='member'?'payments':'late-fee');
 tabs[0].click();assert.equal(workspace.dataset.loanDetailView,'installments');
 assert.equal(q('paymentAmount').value,'123');assert.equal(q('paymentReference').value,'draft');assert(q('loanLateFeeSelected').checked);assert.equal(s.calls.length,before);
 for(const state of [[true,false],[false,true]]){q('printLoanScheduleButton').syntheticSetPaymentState(...state);tabs[1].click();assert.equal(workspace.dataset.loanDetailView,'installments');q('closeLoanDetail').click();assert(!q('loanDetailPanel').hidden);}
 q('printLoanScheduleButton').syntheticSetPaymentState(false,false);
 tabs[1].click();await q('printLoanScheduleButton').syntheticOpenLoan(41);assert.equal(workspace.dataset.loanDetailView,'payments');
 q('closeLoanDetail').click();assert(q('loanDetailPanel').hidden);q('loanList').querySelector('button').click();await flush();assert.equal(workspace.dataset.loanDetailView,'installments');
 s.dom.window.close();
 }
 console.log('Compact loan detail checks passed: standalone/workspace, three roles, pane visibility, request-free switches, preserved drafts, pending/uncertain guards, refresh and reopen.');
})().catch(e=>{console.error(e);process.exit(1)});
