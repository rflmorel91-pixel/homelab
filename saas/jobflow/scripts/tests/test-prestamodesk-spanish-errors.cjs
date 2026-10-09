const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..');
function readAsset(page,prefix){const html=fs.readFileSync(path.join(root,'app',page),'utf8');const name=html.match(new RegExp('/assets/('+prefix+'-[a-f0-9]+\\.js)'))[1];return fs.readFileSync(path.join(root,'app/assets',name),'utf8');}
const screens=[['prestamodesk-app.html','prestamodesk-app'],['prestamodesk-caja.html','prestamodesk-caja'],['prestamodesk-administracion.html','prestamodesk-administration']];
const compiled=readAsset('prestamodesk-workspace.html','prestamodesk-workspace-screens');
(async()=>{let checks=0;
for(const [page,prefix] of screens){
 const source=readAsset(page,prefix),admin=prefix.includes('administration');
 const start=source.indexOf(admin?'  async function request(':'async function apiRequest(');
 const end=source.indexOf(admin?'  function roleSelect(':'async function checkHealth(',start);
 const block=source.slice(start,end);assert(start>=0&&end>start);assert(compiled.includes(block),`${prefix} must be compiled without losing translations`);
 let reply,cleared=0;
 const context={API_BASE:'/api/v1',tenantId:'4',base:'/api/v1/products/prestamodesk/administration',client:{tenant_id:4},fetch:async(url,options)=>{assert.equal(options.headers['X-Tenant-ID'],'4');return reply;},clearActivation:()=>cleared++,clearMemberDetail:()=>{},panel:{hidden:false},document:{getElementById:()=>({hidden:false})}};
 vm.createContext(context);vm.runInContext(block,context);
 async function failure(status,detail,expected,malformed=false){reply={ok:false,status,json:async()=>{if(malformed)throw Error('bad json');return {detail};}};try{await (admin?context.request('/invitations','POST',{}):context.apiRequest('/loans'));assert.fail('request must reject');}catch(error){assert.equal(error.status,status);assert.match(error.message,expected);assert(!error.message.includes('private backend trace'));}checks++;}
 await failure(409,'Configure and enable the tenant late-fee policy first',/Configure y active la política de mora/);
 await failure(422,'First payment date cannot be before the loan start date',/primera cuota/);
 await failure(409,'Payment exceeds installment balance',/supera el saldo/);
 await failure(409,'Payment request key was used with different details',/Revise el historial antes de volver a cobrar/);
 await failure(409,'An active invitation already exists for this client and email',/revoque la invitación/);
 await failure(409,'Client must retain at least one active owner',/propietario activo/);
 await failure(401,'Authentication required',/Inicie sesión/);
 await failure(403,'Role does not permit this operation',/Su rol no permite/);
 await failure(422,[{loc:['body','amount'],msg:'Input should be greater than 0',input:'private'}],/campos obligatorios/);
 await failure(503,'private backend trace',/problema del servidor/);
 await failure(409,'private backend trace',/conflicto/);
 await failure(429,null,/demasiadas solicitudes/);
 await failure(502,null,/problema del servidor/,true);
 await failure(409,'toString',/conflicto/);
 reply={ok:true,status:200,json:async()=>({id:7})};assert.equal((await(admin?context.request('/team'):context.apiRequest('/loans'))).id,7);
 if(admin){assert.equal(cleared,2);assert.equal(context.panel.hidden,true);}else{reply={ok:true,status:204};assert.equal(await context.apiRequest('/loans'),null);}
 context.fetch=async()=>{throw new TypeError('Failed to fetch');};await assert.rejects(admin?context.request('/invitations'):context.apiRequest('/payments'),e=>e.status===undefined); // Uncertain payment handling must stay intact.
}
console.log(`${checks} Spanish API error checks passed across loans, Caja and Administration; compiled workspace matches.`);
})().catch(error=>{console.error(error);process.exitCode=1;});
