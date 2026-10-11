const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),{spawnSync}=require('node:child_process');
const root=path.resolve(__dirname,'../..');
if(!process.env.PD_FORMATTING_CHILD){
 for(const tz of ['UTC','America/Los_Angeles','Asia/Tokyo']){
  const result=spawnSync(process.execPath,[__filename],{env:{...process.env,TZ:tz,PD_FORMATTING_CHILD:'1'},encoding:'utf8'});
  assert.equal(result.status,0,result.stdout+result.stderr);
 }
 console.log('Formatting checks passed: Dominican date boundaries across three browser zones, UTC/offset/naive timestamps, safe missing/invalid dates, DOP amounts and compiled parity.');
}else{
 const compiled=fs.readFileSync(path.join(root,'app',fs.readFileSync(path.join(root,'app/prestamodesk-workspace.html'),'utf8').match(/src="\/assets\/(prestamodesk-workspace-screens-[a-f0-9]+\.js)"/)[1].replace(/^/,'assets/')),'utf8');
 for(const page of ['prestamodesk-app.html','prestamodesk-caja.html','prestamodesk-cobros.html','prestamodesk-cobros-supervision.html','prestamodesk-administracion.html']){
  const html=fs.readFileSync(path.join(root,'app',page),'utf8'),src=html.match(/<script[^>]*src="\/assets\/([^"]+)"/)[1],code=fs.readFileSync(path.join(root,'app/assets',src),'utf8');
  const ctx=vm.createContext({Intl,Date,Number,String});
  for(const name of ['pdBusinessDate','pdDateOnly','pdDateTime','formatMoney']){
   const match=code.match(new RegExp('function '+name+'\\([^]*?\\n\\}'));
   if(!match)continue;vm.runInContext(match[0],ctx);assert(compiled.includes(match[0]),page+' compiled helper differs');
  }
  if(ctx.pdBusinessDate){
   assert.equal(ctx.pdBusinessDate(new Date('2026-10-11T00:30:00Z')),'2026-10-10');
   assert.equal(ctx.pdBusinessDate(new Date('2026-10-11T04:00:00Z')),'2026-10-11');
   assert.equal(ctx.pdBusinessDate(new Date('2027-01-01T03:59:00Z')),'2026-12-31');
  }
  assert.equal(ctx.pdDateOnly('2026-01-05'),'05/01/2026'); assert.equal(ctx.pdDateOnly('2024-02-29'),'29/02/2024'); for(const value of ['2026-02-29','2026-13-01','bad',null])assert.equal(ctx.pdDateOnly(value),'—');
  if(ctx.pdDateTime){
   const expected='10/10/2026, '+new Intl.DateTimeFormat('es-DO',{timeZone:'America/Santo_Domingo',hour:'numeric',minute:'2-digit'}).format(new Date('2026-10-11T00:30:00Z'));
   for(const raw of ['2026-10-11T00:30:00Z','2026-10-11T00:30:00','2026-10-10T20:30:00-04:00','2026-10-11T02:30:00+02:00'])assert.equal(ctx.pdDateTime(raw),expected);
   assert.equal(ctx.pdDateTime(null),'—');assert.equal(ctx.pdDateTime('invalid'),'—');assert.equal(ctx.pdDateTime('invalid','Sin fecha'),'Sin fecha');
  }
  if(ctx.formatMoney)for(const value of ['0','196540.50','-10.25'])assert.equal(ctx.formatMoney(value),new Intl.NumberFormat('es-DO',{style:'currency',currency:'DOP'}).format(Number(value)));
 }
}
