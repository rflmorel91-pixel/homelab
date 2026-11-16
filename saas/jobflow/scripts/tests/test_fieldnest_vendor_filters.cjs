const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const app = path.resolve(__dirname, '../../app');
const html = fs.readFileSync(path.join(app, 'fieldnest-workspace.html'), 'utf8');
const source = fs.readFileSync(path.join(app, html.match(/assets\/fieldnest-workspace-[a-f0-9]+\.js/)[0]), 'utf8');
function block(start, end) {const a=source.indexOf(start), b=source.indexOf(end,a); assert.ok(a>=0 && b>a); return source.slice(a,b);}
class Clock extends Date {constructor(...args) {super(...(args.length ? args : ['2026-11-16T01:00:00Z']));}}
const vendors = [
  {id: 1, name: 'Acme Plumbing', trade: 'Plumbing', insurance_expires: '2026-11-15'},
  {id: 2, name: 'Acme Electrical', trade: 'Electrical', insurance_expires: '2026-11-16'},
  {id: 3, name: 'Roof Works', trade: 'Roofing', insurance_expires: '2026-12-16'},
  {id: 4, name: 'Later Works', trade: 'General', insurance_expires: '2026-12-17'},
  {id: 5, name: 'No Date', trade: 'General', insurance_expires: null},
  {id: 6, name: 'Bad Date', trade: 'General', insurance_expires: '2026-02-30'},
];
const state = {vendors, orders: []}; const original = JSON.stringify(state);
function list(rows) {return {rows, note:null, querySelectorAll() {return this.rows;}, querySelector() {return this.note;}, append(note) {this.note=note;}};}
const rows = vendors.map(v => ({dataset:{vendorId:String(v.id)}, textContent:v.name+' '+v.trade, hidden:false}));
const property = {dataset:{},textContent:'Building A',hidden:false};
const nodes={vendorExpiryFilter:{value:'all'},clearVendorFilters:{},vendorFilterCount:{},vendors:list(rows),properties:list([property])};
const search={value:'',dataset:{search:'vendors'}}, propertySearch={value:'',dataset:{search:'properties'}};
const context=vm.createContext({state,Date:Clock,$:id=>nodes[id],document:{
  querySelectorAll:()=>[search,propertySearch],createElement:()=>({}),querySelector:selector=>{assert.equal(selector,'[data-search="vendors"]');return search;}
}});
vm.runInContext(block('  const esc =','  const msg =')+block('  function vendorInsuranceStatus(','  function workOrderListMarkup(')+block('  function workOrderMatchesFilter(','  function orderedOpenWorkOrders('),context);
const shown=()=>rows.filter(row=>!row.hidden).map(row=>row.dataset.vendorId);
for(const [filter,expected] of [['all',['1','2','3','4','5','6']],['past',['1']],['soon',['2','3']],['missing',['5','6']],['unknown',['1','2','3','4','5','6']]]) {
  nodes.vendorExpiryFilter.value=filter; context.applySearch();assert.deepEqual(shown(),expected);assert.equal(nodes.vendorFilterCount.textContent,expected.length+' of 6 vendors shown');assert.equal(property.hidden,false);
}
nodes.vendorExpiryFilter.value='soon';search.value='  ACME  ';context.applySearch();assert.deepEqual(shown(),['2']);assert.equal(nodes.clearVendorFilters.disabled,false);
search.value='missing vendor';context.applySearch();assert.deepEqual(shown(),[]);assert.equal(nodes.vendors.note.hidden,false);assert.match(nodes.vendors.note.textContent,/expiry filter/);
context.clearVendorFilters();assert.equal(nodes.vendorExpiryFilter.value,'all');assert.equal(search.value,'');assert.equal(nodes.clearVendorFilters.disabled,true);assert.equal(nodes.vendors.note.hidden,true);assert.deepEqual(shown(),['1','2','3','4','5','6']);
search.value=' ';context.applySearch();assert.equal(nodes.clearVendorFilters.disabled,false);context.clearVendorFilters();
assert.equal(JSON.stringify(state),original,'filtering must not change records');
nodes.vendorExpiryFilter.value='past';state.vendors=vendors.map(v=>v.id===1?{...v,insurance_expires:'2026-12-20'}:v);context.applySearch();assert.deepEqual(shown(),[],'refreshed expiry must update the filtered set');
state.vendors=[];context.applySearch();assert.deepEqual(shown(),[],'old workspace rows must not remain visible');
nodes.vendors.rows=[];context.applySearch();assert.equal(nodes.vendorFilterCount.textContent,'0 of 0 vendors shown');assert.equal(nodes.vendors.note.hidden,true);
const renderLine=source.split('\n').find(line=>line.startsWith('    $("vendors").innerHTML ='));
assert.ok(renderLine);assert.match(renderLine,/data-vendor-id="\$\{esc\(v.id\)\}"/);
const renderNode={};const escapedContext=vm.createContext({state:{vendors:[{id:'1" onclick="x',name:'<Acme>',trade:'A&B',insurance_expires:null}]},$:()=>renderNode});
vm.runInContext(block('  const esc =','  const msg =')+block('  function vendorInsuranceStatus(','  function workOrderListMarkup(')+renderLine,escapedContext);
assert.match(renderNode.innerHTML,/data-vendor-id="1&quot; onclick=&quot;x"/);assert.doesNotMatch(renderNode.innerHTML,/<Acme>/);
const filter=html.match(/<select id="vendorExpiryFilter">([\s\S]*?)<\/select>/)[1];
for(const value of ['all','past','soon','missing']) assert.ok(filter.includes('value="'+value+'"'));
assert.match(html,/id="vendorFilterCount" role="status"/);
assert.ok(source.includes('$("vendorExpiryFilter")?.addEventListener("change", applySearch)'));
assert.ok(source.includes('$("clearVendorFilters")?.addEventListener("click", clearVendorFilters)'));
console.log('FieldNest vendor filters: UTC expiry groups, search intersection, counts, clear/empty state, refreshed dates, stale rows, escaping, and immutability passed');
