/* Working-memory surfaces share the creator workspace and preserve explicit actions. */
window.MargenMemory = {
  async render({api,root,mode,project,artifacts,copy,decisionForm,refresh}) {
    const el=(t,text,cls)=>{const n=document.createElement(t);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
    const status=el('p','', 'creator-status');status.setAttribute('role','status');root.append(status);
    const action=(text,fn,icon='arrow')=>{const b=el('button',text);b.type='button';window.BottifactUI?.decorate(b,icon);b.onclick=async()=>{b.disabled=true;try{await fn();}catch(e){status.textContent=e.message;}finally{b.disabled=false;}};return b;};
    const request=(url,data,method='POST')=>api(url,{method,body:JSON.stringify(data)});
    const link=(text,url)=>{const a=el('a',text);a.href=url;return a;};
    const row=(title,label)=>{const c=el('article',undefined,'creator-row memory-card');c.append(el('span',label,'creator-badge'),el('h3',title));root.append(c);return c;};
    const refs=(c,items)=>{for(const e of items){const d=el('details');d.append(el('summary',e.title+' · '+e.version.slice(0,8)),el('blockquote',e.quote),link('Abrir la fuente',e.url),el('small',({unchanged:'Versión conservada',presentation_only:'Cambió la presentación; el texto se conserva',quoted_text_preserved:'La cita se conserva; revisar su contexto',cited_text_changed:'Cambió la cita',unassessed:'Cambio pendiente de evaluar'})[e.materiality]||''));c.append(d);}};
    const form=(title,fields,onSave)=>{
      const dialog=el('dialog',undefined,'creator-form');dialog.setAttribute('aria-label',title);const body=el('form',undefined,'creator-form-body');const head=el('header');head.append(el('h2',title),action('Cerrar',()=>dialog.close(),'close'));dialog.append(head,body);document.body.append(dialog);dialog.onclose=()=>dialog.remove();
      const inputs={};for(const f of fields){const label=el('label',f.label);let input;if(f.options){input=el('select');f.options.forEach(([v,t])=>input.add(new Option(t,v)));}else{input=el(f.multiline?'textarea':'input');if(!f.multiline)input.type=f.type||'text';}input.value=f.value||'';input.required=!!f.required;inputs[f.key]=input;label.append(input);body.append(label);}
      const error=el('p');error.setAttribute('role','status');body.append(error);const save=el('button','Guardar');save.type='submit';save.className='primary';body.append(save);
      body.onsubmit=async e=>{e.preventDefault();save.disabled=true;try{await onSave(Object.fromEntries(Object.entries(inputs).map(([k,v])=>[k,v.value])));dialog.close();await refresh();}catch(err){error.textContent=err.message;}finally{save.disabled=false;}};
      dialog.showModal();Object.values(inputs)[0]?.focus();return {dialog,inputs,body};
    };
    if(mode==='analytics'){
      const d=await api('/api/creator/analytics?project='+encodeURIComponent(project));root.append(el('h2','Visitas a tus artefactos'),el('p','Aperturas registradas al leer una versión publicada. Excluye tus propias visitas. No equivale a personas únicas.'));
      root.append(action(d.enabled?'Desactivar medición':'Activar medición',async()=>{await request('/api/creator/analytics',{enabled:!d.enabled},'PUT');await refresh();},'settings'));
      if(d.umami)root.append(link('Abrir Umami',d.umami.origin+'/websites/'+d.umami.website));
      const total=d.rows.reduce((n,r)=>n+r.views,0);row(String(total)+' aperturas','Hasta '+d.limit+' registros diarios · últimos '+d.retention_days+' días');
      const groups=new Map();for(const r of d.rows){const a=groups.get(r.id)||{...r,views:0};a.views+=r.views;groups.set(r.id,a);}for(const a of [...groups.values()].sort((a,b)=>b.views-a.views)){const c=row(a.title,String(a.views)+' aperturas');c.append(link('Abrir artefacto','/a/'+a.id));}
      if(!d.rows.length)root.append(el('p','La medición comienza al activarla. Las visitas anteriores no pueden reconstruirse.','creator-empty'));
      try{const metrics=await api('/api/operations/performance');const block=row('Rendimiento persistente',metrics.samples+' peticiones');block.append(el('p','Hasta 50.000 peticiones de los últimos 30 días. Latencia del servidor; no incluye renderizado ni toda la red.'));
        const box=el('div',undefined,'memory-table');box.tabIndex=0;box.setAttribute('role','region');box.setAttribute('aria-label','Rendimiento por ruta');const table=el('table'),thead=el('thead'),tr=el('tr');['Ruta','Muestras','p95 · ms','Errores 5xx'].forEach(t=>{const th=el('th',t);th.scope='col';tr.append(th);});thead.append(tr);table.append(thead);const tbody=el('tbody');for(const r of metrics.routes){const tr=el('tr');[r.route,r.samples,r.p95_ms,r.server_errors].forEach(t=>tr.append(el('td',String(t))));tbody.append(tr);}table.append(tbody);box.append(table);block.append(box);
      }catch{}return;
    }
    if(mode==='evidence'){
      root.append(el('h2','Buscar con la fuente a la vista'),el('p','Texto completo en versiones publicadas propias. Los fragmentos son candidatos a evidencia; no una respuesta inferida.'));
      const f=el('form',undefined,'creator-projects'),label=el('label','Términos o frase'),input=el('input');input.type='search';input.required=true;input.placeholder='capacidad, decisiones, rendimiento';label.append(input);const go=el('button','Buscar');go.type='submit';f.append(label,go);root.append(f);const results=el('section');root.append(results);
      f.onsubmit=async e=>{e.preventDefault();go.disabled=true;try{const found=await api('/api/creator/evidence-search?project='+encodeURIComponent(project)+'&q='+encodeURIComponent(input.value));results.replaceChildren(el('p',found.answer));for(const hit of found.items){const c=el('article',undefined,'creator-row memory-card');c.append(link(hit.title,hit.url),el('small','Versión '+hit.version.slice(0,8)),el('blockquote',hit.quote),action('Copiar cita',()=>copy(hit.quote+'\nFuente: '+hit.url),'copy'));results.append(c);}}catch(e){status.textContent=e.message;}finally{go.disabled=false;}};return;
    }
    if(mode==='brief'){
      const d=await api('/api/creator/brief?project='+encodeURIComponent(project));root.append(el('h2','Retoma el hilo'),el('p','Decisiones, supuestos, conversaciones y salidas de sesiones con sus fuentes. Tus notas privadas quedan fuera.'));
      root.append(action('Copiar para continuar',()=>copy(d.text),'copy'));
      const preview=el('article',d.text,'memory-brief');root.append(preview);return;
    }
    const d=await api('/api/creator/memory?project='+encodeURIComponent(project));
    function editClaim(c={}){
      const first=c.evidence?.[0];form(c.id?'Revisar supuesto':'Nuevo supuesto con evidencia',[
        {key:'statement',label:'Qué afirmamos o suponemos',value:c.statement,multiline:true,required:true},
        {key:'project',label:'Proyecto',value:c.project||project||'Personal',required:true},
        {key:'subject',label:'Asunto comparable (misma unidad y alcance)',value:c.subject,required:true},
        {key:'period',label:'Periodo',value:c.period,required:true},
        {key:'value',label:'Valor o postura',value:c.value,required:true},
        {key:'state',label:'Estado',value:c.state||'open',options:[['open','Supuesto abierto'],['supported','Sustentado'],['discarded','Descartado']]},
        {key:'review_on',label:'Revisar el',value:c.review_on,type:'date'},
        {key:'artifact',label:'Artefacto fuente',value:first?.artifact,options:artifacts.map(a=>[a.id,a.title])},
        {key:'version',label:'Versión exacta (vacía usa la publicada)',value:first?.version},
        {key:'quote',label:'Cita exacta de la fuente',value:first?.quote,multiline:true,required:true}
      ],b=>request('/api/creator/claims',{...b,id:c.id,updated:c.updated,evidence:[{artifact:b.artifact,version:b.version,quote:b.quote},...(c.evidence||[]).slice(1)]}));
    }
    if(mode==='claims'){
      root.append(el('h2','Supuestos que podemos comprobar'),el('p','Registra alcance, periodo, valor y cita. Las fuentes nuevas no reescriben lo que sabíamos antes.'),action('Registrar supuesto',()=>editClaim(),'plus'));
      for(const c of d.claims){const card=row(c.statement,({open:'Abierto',supported:'Sustentado',discarded:'Descartado'})[c.state]+(c.needs_review?' · Revisar':''));card.append(el('p',[c.subject,c.period,c.value].filter(Boolean).join(' · ')),el('small',c.review_on?'Revisión: '+c.review_on:'Sin fecha de revisión'));refs(card,c.evidence);card.append(action('Revisar',()=>editClaim(c)),action('Ver historial',async()=>{const h=await api('/api/creator/claims/'+c.id+'/history');const detail=el('details');detail.open=true;detail.append(el('summary','Historial · '+h.items.length+' entradas'));for(const item of h.items){const record=JSON.parse(item.record);detail.append(el('p',new Date(item.at*1000).toLocaleString()+' · '+record.statement+' · '+record.state));}card.append(detail);},'history'));}
      if(!d.claims.length)root.append(el('p','Empieza por una afirmación que afecte una decisión. Necesita una cita exacta en uno de tus artefactos.','creator-empty'));return;
    }
    if(mode==='contradictions'){
      root.append(el('h2','Contrastar antes de concluir'),el('p','Candidatos por el mismo asunto y periodo declarados, con valores distintos. No es una comprobación automática de verdad.'));
      for(const c of d.contradictions){const card=row(c.left.subject,({suggested:'Por revisar',confirmed:'Confirmado por ti',dismissed:'Descartado por ti'})[c.state]);card.append(el('p',c.reason));for(const claim of [c.left,c.right]){const side=el('section');side.append(el('h4',claim.statement),el('p',claim.period+' · '+claim.value));refs(side,claim.evidence);card.append(side);}card.append(action('Registrar criterio',()=>form('Explicar el contraste',[{key:'state',label:'Resultado',value:c.state,options:[['suggested','Seguir investigando'],['confirmed','Confirmar contradicción'],['dismissed','Descartar coincidencia']]},{key:'reason',label:'Por qué, con qué alcance',value:c.reason,multiline:true,required:true}],b=>request('/api/creator/contradictions',{...b,left:c.left.id,right:c.right.id}))));}
      if(!d.contradictions.length)root.append(el('p','No hay candidatos en este alcance. Esto no demuestra que todas las fuentes sean consistentes.','creator-empty'));return;
    }
    if(mode==='sessions'){
      root.append(el('h2','Dónde quedó el trabajo'),el('p','Sesiones registradas por los agentes en tus versiones. Añade contexto de continuidad; no se importan conversaciones completas.'));
      for(const s of d.sessions){const card=row(s.objective||s.session,s.agent+' · '+s.device);card.append(el('p',s.summary||'Estado aún no registrado'),el('p','Siguiente paso: '+(s.next_step||'Por definir')));for(const o of s.outputs){card.append(link(o.title+' · '+o.version.slice(0,8),o.url));}card.append(action('Completar continuidad',()=>form('Ficha de sesión',[{key:'objective',label:'Objetivo',value:s.objective,multiline:true},{key:'summary',label:'Dónde quedó',value:s.summary,multiline:true},{key:'next_step',label:'Siguiente paso',value:s.next_step,multiline:true}],b=>request('/api/creator/sessions',{...b,agent:s.agent,device:s.device,session:s.session,project}))));}
      if(!d.sessions.length)root.append(el('p','No hay sesiones registradas en este alcance. Se conservarán cuando el agente publique una referencia real.','creator-empty'));return;
    }
    if(mode==='outcomes'){
      root.append(el('h2','De lo esperado a lo observado'),el('p','Revisa el resultado sin borrar la decisión original. Un resultado distinto no demuestra por sí solo que la decisión fuera incorrecta.'));
      for(const x of d.outcomes){const c=row(x.title,x.state+(x.needs_review?' · Revisar':''));c.append(el('h4','Esperábamos'),el('p',x.expected||'Resultado esperado pendiente'),el('h4','Observamos'),el('p',x.outcome||'Todavía sin observación'),el('p','Incertidumbre: '+(x.uncertainty||'No registrada')));refs(c,x.evidence);c.append(action('Registrar resultado',()=>decisionForm(x)));}
      if(!d.outcomes.length)root.append(el('p','Registra una decisión con resultado esperado y una fecha de revisión.','creator-empty'));
    }
  }
};
