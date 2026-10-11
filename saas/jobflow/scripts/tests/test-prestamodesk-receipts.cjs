// Synthetic receipts only. Never contact a live API or create real payments.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const receipt={receipt_number:'PM-SYNTHETIC',loan_id:41,amount:'10.00',late_fee_amount:'1.00',interest_amount:'2.00',principal_amount:'7.00',installment_ordinary_balance:'440.00',installment_late_fee_balance:'3.00',installment_balance:'443.00',loan_balance:'993.00',recorded_by_user_id:1,paid_at:'2026-10-11T00:30:00Z',payment_method:'bank_transfer',reference:'<img src=x onerror=alert(1)>'};
function fixture(cashier){
 let code=fs.readFileSync(path.join(__dirname,cashier?'test-prestamodesk-compact-caja.cjs':'test-prestamodesk-compact-loans.cjs'),'utf8').split('(async()=>{')[0];
 const marker="  if(options.method==='POST'&&u.pathname===base+'/loans/preview'){";
 code=code.replace(marker,"  if(options.method==='POST'&&u.pathname===base+'/payments'){data="+JSON.stringify(receipt)+";}\n  else if(options.method==='POST'&&u.pathname===base+'/loans/preview'){");
 return new Function('require','__dirname',code+'\nreturn {setup,flush};')(require,__dirname);
}
(async()=>{
 for(const cashier of [false,true])for(const standalone of [true,false]){
  const f=fixture(cashier),s=await f.setup('owner',standalone),w=s.w,d=w.document;
  d.getElementById(cashier?'cashierLoanList':'loanList').querySelector('button').click();await f.flush();
  d.getElementById('paymentAmount').value='10';d.getElementById('paymentForm').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await f.flush();
  const panel=d.getElementById('receiptPanel'),content=d.getElementById('receiptContent');assert(!panel.hidden);assert(content.querySelector('.pd-receipt-details'));assert(!content.querySelector('img'));assert.match(content.textContent,/PM-SYNTHETIC/);assert.match(content.textContent,/10\/10\/2026/);assert.match(content.textContent,/Transferencia bancaria/);assert.match(content.textContent,/<img src=x onerror=alert\(1\)>/);assert.match(content.textContent,/Saldos al registrar este pago/);
  const values=[...content.querySelectorAll('dd')].map(x=>x.textContent);for(const amount of [1,2,7,440,3,443,993])assert(values.includes(new Intl.NumberFormat('es-DO',{style:'currency',currency:'DOP'}).format(amount)));
  assert.equal(s.calls.filter(c=>c.url.endsWith('/payments')&&c.options.method==='POST').length,1);
  const count=s.calls.length;let prints=0,sawMode=false;const printRoot=standalone?d.body:d.querySelector('.pd-module');
  w.print=()=>{prints++;sawMode=printRoot.classList.contains('pd-payment-receipt-print');};
  d.getElementById('printReceiptButton').click();assert.equal(prints,1);assert(sawMode);assert(!printRoot.classList.contains('pd-payment-receipt-print'));assert.equal(s.calls.length,count);
  w.print=()=>{throw new Error('Synthetic unavailable printer');};d.getElementById('printReceiptButton').click();assert(!printRoot.classList.contains('pd-payment-receipt-print'));assert.match(d.getElementById('errorMessage').textContent,/pago ya está registrado/);assert(!panel.hidden);assert.equal(s.calls.length,count);
  panel.hidden=true;w.print=()=>{prints++;};d.getElementById('printReceiptButton').click();assert.equal(prints,1);
  s.dom.window.close();
 }
 console.log('Receipt checks passed: both screens, standalone/workspace, backend amount breakdown, DD/MM/YYYY timezone, safe text, single payment, isolated print mode, printer failure recovery and no print requests.');
})().catch(error=>{console.error(error);process.exit(1);});
