(() => {
  "use strict";
  const $ = id => document.getElementById(id);
  const definitions = {
    summary: {label:"Resumen",screen:"loans",roles:["owner","administrator","member"]},
    loans: {label:"Préstamos",screen:"loans",roles:["owner","administrator","member"]},
    cashier: {label:"Caja",screen:"cashier",roles:["owner","administrator","cashier","member"]},
    collections: {label:"Cobros",screen:"collections",roles:["owner","administrator","supervisor","collector"]},
    supervision: {label:"Supervisión",screen:"supervision",roles:["owner","administrator","supervisor"]},
    administration: {label:"Administración",screen:"administration",roles:["owner","administrator"]}
  };
  const paths = {"/prestamodesk/app":"loans","/prestamodesk-app.html":"loans","/prestamodesk/caja":"cashier","/prestamodesk-caja.html":"cashier","/prestamodesk/cobros":"collections","/prestamodesk-cobros.html":"collections","/prestamodesk/cobros/supervision":"supervision","/prestamodesk-cobros-supervision.html":"supervision","/prestamodesk-administracion.html":"administration"};
  let clients=[], selected=null, mounted=null, current=null, generation=0, writes=0, loading=false, dirty=false;
  const storageKeys=["prestamodesk_tenant_id","prestamodesk_cashier_tenant_id","prestamodesk_collections_tenant_id","prestamodesk_supervision_tenant_id"];
  const roleNames={owner:"Propietario",administrator:"Administrador",supervisor:"Supervisor",collector:"Cobrador",cashier:"Cajero",member:"Miembro"};
  function note(text){$("pdMessage").textContent=text;$("pdMessage").hidden=!text;}
  function controls(){for(const node of document.querySelectorAll('[data-pd-view],#pdClient,#pdLogout,#pdRefresh'))node.disabled=loading||writes>0;}
  async function api(path,options={}) {
    const response=await fetch("/api/v1"+path,{credentials:"same-origin",...options,headers:{"Content-Type":"application/json",...(options.headers||{})}});
    const data=await response.json();if(!response.ok){const error=new Error(typeof data.detail==="string"?data.detail:"No se pudo completar la solicitud.");error.status=response.status;throw error;}return data;
  }
  function allowed(view){return Boolean(selected&&definitions[view]?.roles.includes(selected.role));}
  function defaultView(){return Object.keys(definitions).find(allowed);}
  function canLeave(){
    if(writes>0){note("Espere la confirmación de la operación antes de cambiar de sección.");return false;}
    if(mounted?.guard&&!mounted.guard.canLeave()){note("Revise el resultado del pago en Caja antes de cambiar de sección.");return false;}
    return !dirty||window.confirm("Hay datos sin guardar. ¿Desea cambiar de sección y descartarlos?");
  }
  function teardown(){generation++;mounted?.dispose();mounted=null;current=null;dirty=false;$("pdHost").replaceChildren();}
  function updateAccess(){
    for(const button of document.querySelectorAll('[data-pd-view]'))button.hidden=!allowed(button.dataset.pdView);
    $("pdRole").textContent=roleNames[selected?.role]||"";
    $("pdContext").textContent=selected?`Cliente #${selected.client_number} · ${selected.name}`:"";
    $("pdWorkspace").hidden=!selected;$("pdAuth").hidden=Boolean(selected);
  }
  function renderClients(){
    $("pdClient").replaceChildren();
    for(const client of clients){const option=document.createElement("option");option.value=String(client.tenant_id);option.textContent=`Cliente #${client.client_number} · ${client.name}`;$("pdClient").append(option);}
    if(selected)$("pdClient").value=String(selected.tenant_id);
  }
  async function access(){
    const data=await api('/auth/products/prestamodesk/access');clients=data.clients||[];
    const saved=selected?.tenant_id??localStorage.getItem("prestamodesk_tenant_id");
    selected=clients.find(client=>String(client.tenant_id)===String(saved))||clients[0]||null;
    renderClients();updateAccess();
    if(!selected)note("Su cuenta no tiene acceso activo a PréstamoDesk.");
  }
  function moduleContext(root,tenant,epoch){
    const controller=new AbortController(),events=new EventTarget(),timers=new Set(),local={};
    const scopedDocument=new Proxy(document,{get(target,key){
      if(key==='getElementById')return id=>root.querySelector('#'+CSS.escape(id));
      if(key==='querySelector')return selector=>root.querySelector(selector);
      if(key==='querySelectorAll')return selector=>root.querySelectorAll(selector);
      if(key==='body')return root;
      if(key==='addEventListener')return root.addEventListener.bind(root);
      if(key==='removeEventListener')return root.removeEventListener.bind(root);
      const value=Reflect.get(target,key,target);return typeof value==='function'?value.bind(target):value;
    }});
    const scopedLocation={replace(url){const path=new URL(url,location.origin);if(paths[path.pathname])navigate(paths[path.pathname]);},reload(){navigate(current||defaultView(),true);}};
    const delay=(callback,ms)=>{const timer=window.setTimeout(()=>{timers.delete(timer);if(epoch===generation)callback();},ms);timers.add(timer);return timer;};
    const scopedWindow=new Proxy(window,{get(target,key){
      if(key==='location')return scopedLocation;
      if(key==='addEventListener')return events.addEventListener.bind(events);
      if(key==='removeEventListener')return events.removeEventListener.bind(events);
      if(key==='dispatchEvent')return events.dispatchEvent.bind(events);
      if(key==='setTimeout')return delay;
      if(key in local)return local[key];
      const value=Reflect.get(target,key,target);return typeof value==='function'?value.bind(target):value;
    },set(target,key,value){local[key]=value;return true;}});
    const scopedStorage={getItem(key){return storageKeys.includes(key)?String(tenant.tenant_id):localStorage.getItem(key);},setItem(key,value){if(!storageKeys.includes(key))localStorage.setItem(key,value);},removeItem(key){if(!storageKeys.includes(key))localStorage.removeItem(key);}};
    async function scopedFetch(input,options={}){
      if(epoch!==generation)throw new DOMException("Sección cerrada","AbortError");
      const url=new URL(input,location.origin);if(url.origin!==location.origin||!url.pathname.startsWith('/api/v1/'))throw new Error("Destino no permitido.");
      if(url.pathname==='/api/v1/auth/products/prestamodesk/access'){
        const data=await api('/auth/products/prestamodesk/access',{signal:controller.signal});
        const client=data.clients.find(item=>String(item.tenant_id)===String(tenant.tenant_id));
        return new Response(JSON.stringify({...data,clients:client?[client]:[]}),{headers:{'Content-Type':'application/json'}});
      }
      const headers=new Headers(options.headers||{});
      if(url.pathname.startsWith('/api/v1/products/prestamodesk/'))headers.set('X-Tenant-ID',String(tenant.tenant_id));
      const mutating=!['GET','HEAD'].includes((options.method||'GET').toUpperCase());
      if(mutating){writes++;controls();}
      try{
        const response=await fetch(url,{...options,headers,credentials:'same-origin',signal:controller.signal});
        if(mutating && response.ok && epoch===generation)dirty=false;
        if(response.status===401&&epoch===generation){teardown();selected=null;updateAccess();note("Su sesión venció. Inicie sesión para continuar.");}
        else if(response.status===403&&epoch===generation)note("Revise sus permisos. Puede actualizar el acceso desde el menú.");
        return response;
      }finally{if(mutating){writes--;controls();}}
    }
    return {document:scopedDocument,window:scopedWindow,fetch:scopedFetch,storage:scopedStorage,location:scopedLocation,delay,
      dispose(){controller.abort();for(const timer of timers)clearTimeout(timer);events.dispatchEvent(new Event('pd-dispose'));}};
  }
  async function navigate(view,force=false){
    if(loading)return;
    if(!force&&!canLeave()){if(current)history.replaceState(null,'','#'+current);return;}
    loading=true;controls();note("");
    try{
      await access();if(!selected){teardown();return;}
      if(!allowed(view)){view=defaultView();note("Mostramos las secciones disponibles para su rol.");}
      if(!view){teardown();note("Su rol no tiene un espacio disponible.");return;}
      teardown();current=view;const epoch=generation;
      localStorage.setItem('prestamodesk_tenant_id',String(selected.tenant_id));
      const definition=definitions[view],screen=window.PrestamoDeskScreens[definition.screen],root=document.createElement('div');root.className='pd-module';root.dataset.mode=view;
      root.innerHTML=screen.html;$("pdHost").append(root);
      const context=moduleContext(root,{...selected},epoch);mounted={dispose:context.dispose,guard:null};
      mounted.guard=screen.start(context.document,context.window,context.fetch,context.storage,context.location,context.delay,clearTimeout);
      root.addEventListener('input',()=>{dirty=true;});root.addEventListener('change',()=>{dirty=true;});

      root.addEventListener('click',event=>{const link=event.target.closest('a[href]');if(!link)return;const target=new URL(link.href,location.origin);if(target.origin===location.origin&&paths[target.pathname]){event.preventDefault();navigate(paths[target.pathname]);}});
      for(const button of document.querySelectorAll('[data-pd-view]')){const active=button.dataset.pdView===view;button.setAttribute('aria-current',active?'page':'false');}
      $("pdTitle").textContent=definition.label;$("pdHint").textContent=view==='summary'?"Su negocio, de un vistazo.":"Trabaje en esta sección sin salir de PréstamoDesk.";
      history.replaceState(null,'','#'+view);$("pdTitle").focus();
    }catch(error){note(error.status===401?"Inicie sesión para continuar.":error.message);if([401,403].includes(error.status)){teardown();selected=null;updateAccess();}}
    finally{loading=false;controls();}
  }
  for(const button of document.querySelectorAll('[data-pd-view]'))button.addEventListener('click',()=>navigate(button.dataset.pdView));
  window.addEventListener('hashchange',()=>navigate(location.hash.slice(1)));
  window.addEventListener('beforeunload',event=>{if(dirty||writes>0||mounted?.guard&&!mounted.guard.canLeave()){event.preventDefault();event.returnValue='';}});
  $("pdClient").addEventListener('change',()=>{
    const previous=selected;if(!canLeave()){$("pdClient").value=String(previous.tenant_id);return;}
    selected=clients.find(client=>String(client.tenant_id)===$("pdClient").value);teardown();navigate(defaultView(),true);
  });
  $("pdRefresh").addEventListener('click',()=>navigate(current||defaultView()));
  $("pdLogin").addEventListener('submit',async event=>{
    event.preventDefault();$("pdLoginButton").disabled=true;note("");
    try{await api('/auth/login',{method:'POST',body:JSON.stringify({email:$("pdEmail").value,password:$("pdPassword").value})});$("pdLogin").reset();await navigate(location.hash.slice(1)||'summary',true);}
    catch(error){note(error.status===401?"Correo o contraseña incorrectos.":error.message);}finally{$("pdLoginButton").disabled=false;}
  });
  $("pdLogout").addEventListener('click',async()=>{
    if(!canLeave())return;loading=true;controls();
    try{await api('/auth/logout',{method:'POST'});teardown();selected=null;clients=[];for(const key of storageKeys)localStorage.removeItem(key);updateAccess();note("Sesión cerrada.");}
    catch(error){note("No se pudo cerrar la sesión. Intente nuevamente.");}finally{loading=false;controls();}
  });
  api('/health').then(data=>{$("pdHealth").textContent='API: '+data.status;}).catch(()=>{$("pdHealth").textContent='API no disponible';});
  navigate(location.hash.slice(1)||'summary',true);
})();
