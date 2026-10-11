// Synthetic saved receipts only; no payment writes or live services.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const payment={id:3,loan_id:41,amount:'10',interest_amount:'10',principal_amount:'0',late_fee_amount:'0',paid_at:'2026-10-11T00:30:00Z',recorded_by_user_id:1,payment_method:'cash',correction_supported:true};
const envelope={receipt:{...payment,receipt_number:'PM-00000003',loan_balance:'1090',installment_balance:'540',installment_ordinary_balance:'540',installment_late_fee_balance:'0'},snapshot_available:true,borrower_name:'<img src=x onerror=alert(1)>',business_name:'Synthetic'};
function fixture(cashier){
 let code=fs.readFileSync(path.join(__dirname,cashier?'test-prestamodesk-compact-caja.cjs':'test-prestamodesk-compact-loans.cjs'),'utf8').split('(async()=>{')[0];
 const marker="  if(options.method==='POST'&&u.pathname===base+'/loans/preview'){";
 code=code.replace(marker,`  if(u.pathname===base+'/payments/loan/41')data=[${JSON.stringify(payment)}];
  else if(u.pathname===base+'/payments/3/receipt'){
   if(control.receiptPending)await control.receiptPending;
   if(control.receiptFail){status=500;data={detail:'Synthetic failure'};}
   else data=control.receiptData||${JSON.stringify(envelope)};
  }
  else if(options.method==='POST'&&u.pathname===base+'/loans/preview'){ `);
 code=code.replace("for(const match of page.matchAll(/<script[^>]*src=\"([^\"]+)\"/g))w.eval(fs.readFileSync(path.join(root,'app',match[1]),'utf8'));", "w.eval([...page.matchAll(/<script[^>]*src=\"([^\"]+)\"/g)].map(match=>fs.readFileSync(path.join(root,'app',match[1]),'utf8')).join('\\n'));");
 return new Function('require' ,'__dirname',code+'\nreturn {setup,flush};')(require,__dirname);
}
(async()=>{
 for(const cashier of [false,true])for(const standalone of [true,false]){
  const f=fixture(cashier),s=await f.setup('owner',standalone),d=s.w.document;
  d.getElementById(cashier?'cashierLoanList':'loanList').querySelector('button').click();await f.flush();
  const button=()=>[...d.querySelectorAll('#paymentCorrectionList button')].find(x=>x.textContent==='Ver recibo');assert(button(),JSON.stringify({cashier,standalone,message:d.getElementById("paymentCorrectionMessage").textContent,calls:s.calls.map(c=>c.url)}));
  d.getElementById('paymentAmount').value='27';button().click();await f.flush();
  const content=d.getElementById('receiptContent');assert(!d.getElementById('receiptPanel').hidden);assert(!content.querySelector('img'));assert.match(content.textContent,/1090|1,090/);assert.match(content.textContent,/10\/10\/2026/);assert.match(content.textContent,/Nombre del prestatario y negocio actuales/);assert.equal(d.getElementById('paymentAmount').value,'27');
  assert(!s.calls.some(c=>c.options.method==='POST'));
  const before=s.calls.length;s.w.print=()=>{};d.getElementById('printReceiptButton').click();assert.equal(s.calls.length,before);
  s.control.receiptData={...envelope,receipt:{...payment,voided_at:'2026-10-12T12:00:00Z',void_reason:'<script>bad</script>',voided_by_user_id:1},snapshot_available:false};button().click();await f.flush();assert.match(content.textContent,/ANULADO/);assert.match(content.textContent,/no conserva los saldos originales/);assert(!content.querySelector('script'));
  s.control.receiptFail=true;button().click();await f.flush();assert.match(d.getElementById('paymentCorrectionMessage').textContent,/No se pudo recuperar/);s.control.receiptFail=false;
  let release;s.control.receiptPending=new Promise(r=>release=r);button().click();await f.flush();d.getElementById('closeLoanDetail').click();const previous=content.innerHTML;release();await f.flush();assert.equal(content.innerHTML,previous);
  assert(!s.calls.some(c=>c.options.method==='POST'));s.dom.window.close();
 }
 for(const role of ['member','cashier']){const f=fixture(false),s=await f.setup(role,true);s.w.document.getElementById('loanList').querySelector('button').click();await f.flush();assert(s.w.document.getElementById('paymentCorrectionPanel').hidden);s.dom.window.close();}
 console.log('Receipt history checks passed: both screens and modes, saved/legacy/voided copies, escaped text, unchanged drafts, no payment writes, print without requests, failed reads and stale responses.');
})().catch(e=>{console.error(e);process.exit(1);});
