const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const root = path.resolve(__dirname, '../..');
const html = fs.readFileSync(path.join(root, 'app/prestamodesk-caja.html'), 'utf8');
const asset = html.match(/\/assets\/(prestamodesk-caja-[a-f0-9]+\.js)/)[1];
const source = fs.readFileSync(path.join(root, 'app/assets', asset), 'utf8');
const block = source.slice(source.indexOf('paymentForm.addEventListener('), source.indexOf('\n\ndocument.getElementById(\n  "printReceiptButton"'));
function setup(request, refresh = async () => {}) {
  const button = {disabled:false,textContent:'Registrar pago'};
  const installment = {value:'1',disabled:false,selectedOptions:[{dataset:{balance:'3400'}}]};
  const form = {querySelector:()=>button,addEventListener:(_,fn)=>{context.submit=fn;},reset:()=>{}};
  const errors=[];
  const context = {paymentSubmitting:false,paymentNeedsReview:false,paymentForm:form,
    selectedLoanId:3,selectedLoan:{borrower_full_name:'Carmen'},paymentDate:{value:'2026-10-08'},
    paymentInstallment:installment,paymentAmount:{value:'1000'},PRODUCT_BASE:'/products/prestamodesk',
    cashierWorkspace:{querySelectorAll:()=>[button,installment]},document:{getElementById:()=>({value:'cash'})},
    clearMessages:()=>{},apiRequest:request,receiptContent:{innerHTML:''},receiptPanel:{hidden:true},
    escapeHtml:String,formatMoney:String,formatPaymentMethod:String,setDefaultPaymentDate:()=>{},
    openLoan:refresh,searchLoans:async()=>{},loadCashClosing:async()=>{},loanSearchQuery:{value:''},
    showSuccess:()=>{},showError:message=>errors.push(message)};
  vm.createContext(context); vm.runInContext(block,context);
  return {context,button,errors,submit:()=>context.submit({preventDefault(){}})};
}
(async()=>{
  let resolve, calls=0;
  const pending=new Promise(r=>resolve=r);
  const a=setup(()=>{calls++;return pending;});
  const first=a.submit(); await a.submit(); assert.equal(calls,1); assert.equal(a.button.disabled,true);
  resolve({receipt_number:'PM-1',amount:'1000'}); await first;
  assert.equal(a.context.paymentSubmitting,false); assert.equal(a.button.disabled,false);
  const b=setup(async()=>({receipt_number:'PM-2'}),async()=>{throw Error('refresh');});
  await b.submit(); assert.match(b.errors[0],/Pago registrado/); assert.equal(b.context.receiptPanel.hidden,false);
  assert.equal(b.button.disabled,true); await b.submit(); assert.equal(b.errors.length,1);
  const c=setup(async()=>{throw new TypeError('Failed to fetch');});
  await c.submit(); assert.equal(c.context.paymentNeedsReview,true); assert.match(c.errors[0],/No lo repita/);
  const d=setup(async()=>{throw Object.assign(Error('Exceeds balance'),{status:409});});
  await d.submit(); assert.equal(d.button.disabled,false); assert.equal(d.errors[0],'Exceeds balance');
  console.log('4 payment submission scenarios passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
