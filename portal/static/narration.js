/* Neural audio lives in the trusted portal. The sandbox never sees a session URL or key. */
(()=>{'use strict';
  const unavailable='La narración neuronal aún no está configurada. No se usará una voz del dispositivo.';
  function references(items,manifest){
    if(!Array.isArray(items)||!items.length||items.length>500)throw Error('Elige entre 1 y 500 fragmentos.');
    let size=0;
    return items.map(item=>{
      if(typeof item.text!=='string'||typeof item.fullText!=='string'||item.fullText.length>100000||!Number.isInteger(item.start)||item.start<0)throw Error('Selección inválida.');
      size+=item.text.length;if(size>80000||[...item.text].length>1200)throw Error('Elige una sección más corta.');
      const exact=manifest.blocks.filter(b=>b.text===item.fullText);
      const anchored=item.anchor?exact.filter(b=>b.anchors.includes(item.anchor)):exact;
      // Review can add runtime-only IDs. A globally unique exact block is still safe.
      const candidates=anchored.length?anchored:exact;
      if(candidates.length!==1||item.fullText.slice(item.start,item.start+item.text.length)!==item.text)throw Error('No se puede vincular este texto a la versión guardada. Prueba una sección con identificador único.');
      return {id:candidates[0].id,start:[...item.fullText.slice(0,item.start)].length,end:[...item.fullText.slice(0,item.start+item.text.length)].length};
    });
  }
  function create({api,binding,emit,audioFactory=()=>new Audio()}){
    let epoch=0,active=null,dialog=null,timer=null;
    const bound=()=>{const b=binding();return b&&{...b};};
    const valid=(token,b)=>token===epoch&&binding()?.artifact===b.artifact&&binding()?.version===b.version;
    const path=b=>'/api/artifacts/'+b.artifact+'/narration';
    const post=(url,body)=>api(url,{method:'POST',body:JSON.stringify(body)});
    function stop(){
      epoch++;clearTimeout(timer);dialog?.close();dialog?.remove();dialog=null;
      const old=active;active=null;
      if(old){old.audio.onended=old.audio.onerror=old.audio.onplaying=null;old.audio.pause();old.audio.removeAttribute('src');old.audio.load();if(old.session)api(path(old.binding)+'/sessions/'+old.session,{method:'DELETE'}).catch(()=>{});}
    }
    function report(s,state,message){if(valid(s.token,s.binding)&&active===s)emit({request:s.request,state,index:s.index,message});}
    function fail(s,error){if(!valid(s.token,s.binding)||active!==s)return;if(s.paused&&error.name==='AbortError')return;report(s,'error',error.message||'No se pudo reproducir el audio.');stop();}
    async function next(s){
      if(!valid(s.token,s.binding)||active!==s)return;
      if(s.paused){s.pending=true;return;}
      if(s.index>=s.count){report(s,'ended','Lectura terminada.');stop();return;}
      try{
        report(s,'loading','Preparando audio…');
        s.audio.removeAttribute('src');s.audio.load();
        const clip=await post(path(s.binding)+'/sessions/'+s.session+'/blocks/'+s.index,{});
        if(!valid(s.token,s.binding)||active!==s)return;
        const prefix=path(s.binding)+'/sessions/'+s.session+'/audio/';
        if(typeof clip.url!=='string'||clip.url!==prefix+s.index)throw Error('Respuesta de audio inválida.');
        s.pauseMs=Math.min(1000,Math.max(0,clip.pause_ms||0));s.audio.preload='auto';s.audio.src=clip.url;s.audio.playbackRate=s.rate;s.audio.load();
        if(!s.paused)await s.audio.play();
      }catch(error){if(valid(s.token,s.binding))fail(s,error);}
    }
    function approve(b,token,request,config,manifest,refs,data){
      const d=document.createElement('dialog');dialog=d;d.className='narration-consent';
      const heading=document.createElement('h2');heading.id='narration-consent-title';heading.textContent='Escuchar con voz generada por IA';d.setAttribute('aria-labelledby',heading.id);
      const info=document.createElement('p');info.textContent=`Se enviará el texto mostrado a ${config.provider}. Voz: ${config.voices.find(v=>v.id===data.voice).label}. Estilo: ${config.profiles.find(p=>p.id===data.profile).label}. Se aplican los límites de uso configurados. Calidad ES/EN pendiente de evaluación auditiva.`;
      const preview=document.createElement('pre');preview.textContent=data.items.map(x=>x.text).join('\n\n');preview.tabIndex=0;preview.setAttribute('aria-label','Texto que se enviará');
      const cancel=document.createElement('button');cancel.textContent='Cancelar';cancel.type='button';
      const accept=document.createElement('button');accept.textContent='Enviar texto y escuchar';accept.type='button';
      const status=document.createElement('p');status.setAttribute('role','status');
      const cancelPending=()=>{if(valid(token,b)){emit({request,state:'error',message:'Lectura cancelada antes de enviar texto.'});stop();}};
      cancel.onclick=cancelPending;d.addEventListener('cancel',e=>{e.preventDefault();cancelPending();});
      accept.onclick=async()=>{
        if(!valid(token,b)||accept.disabled)return;accept.disabled=true;status.textContent='Preparando lectura…';
        const s={binding:b,token,request,audio:audioFactory(),index:0,count:refs.length,session:null,rate:Number(data.rate)||1,paused:false,pending:false};active=s;
        try{
          const session=await post(path(b)+'/sessions',{version:b.version,sha:manifest.sha,voice:data.voice,profile:data.profile,confirmed:true,blocks:refs});
          if(!valid(token,b)||active!==s){api(path(b)+'/sessions/'+session.id,{method:'DELETE'}).catch(()=>{});return;}
          s.session=session.id;d.close();d.remove();if(dialog===d)dialog=null;
          s.audio.onplaying=()=>{if(!s.paused)report(s,'playing',`Leyendo · ${s.index+1} de ${s.count}`);};
          s.audio.onerror=()=>fail(s,Error('No se pudo reproducir el audio. No se cambió a otra voz.'));
          s.audio.onended=async()=>{
            try{
              const completion=await api(path(b)+'/sessions/'+s.session+'/status/'+s.index);
              if(!valid(token,b)||active!==s)return;
              if(completion.state!=='complete')throw Error('La transmisión se interrumpió. Inicia la lectura de nuevo.');
              s.index++;s.pending=true;timer=setTimeout(()=>{if(!s.paused){s.pending=false;next(s);}},s.pauseMs);
            }catch(error){if(valid(token,b))fail(s,error);}
          };
          await next(s);
        }catch(error){if(valid(token,b)){d.close();d.remove();dialog=null;fail(s,error);}}
      };
      d.append(heading,info,preview,status,cancel,accept);document.body.append(d);d.showModal();cancel.focus();
    }
    async function handle(data){
      const b=bound();if(!b)throw Error('No hay documento abierto.');
      if(data?.action==='config')return api(path(b)+'?version='+b.version);
      if(data?.action==='stop'){stop();return {ok:true};}
      if(data?.action==='start'){
        stop();const token=epoch,request=data.request;
        if(typeof request!=='string'||request.length>80)throw Error('Lectura inválida.');
        const config=await api(path(b)+'?version='+b.version);
        if(!valid(token,b))return {cancelled:true};if(!config.enabled)throw Error(config.reason||unavailable);
        if(!config.voices.some(v=>v.id===data.voice)||!config.profiles.some(p=>p.id===data.profile))throw Error('Elige voz y estilo.');
        if(![.75,1,1.25,1.5,2].includes(Number(data.rate)))throw Error('Velocidad inválida.');
        const manifest=await api(path(b)+'/manifest?version='+b.version);
        if(!valid(token,b))return {cancelled:true};const refs=references(data.items,manifest);
        approve(b,token,request,config,manifest,refs,data);return {pending:true};
      }
      const s=active;if(!s||data?.request!==s.request) return {ok:false};
      if(data.action==='pause'){s.paused=true;s.audio.pause();report(s,'paused','Lectura pausada.');}
      else if(data.action==='resume'){
        s.paused=false;
        if(s.pending){clearTimeout(timer);s.pending=false;next(s);}
        else if(s.audio.getAttribute('src'))s.audio.play().catch(e=>fail(s,e));
      }else if(data.action==='rate'&&[.75,1,1.25,1.5,2].includes(Number(data.rate))){s.rate=Number(data.rate);s.audio.playbackRate=s.rate;}
      return {ok:true};
    }
    return {handle,stop};
  }
  window.MargenNarration={create,references};
})();
