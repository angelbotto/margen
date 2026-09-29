/* Editable semantic data only. Artifact HTML stays in its sandbox. */
(() => {
  'use strict';
  const clone = x => JSON.parse(JSON.stringify(x));
  const el = (tag, text, cls) => {const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
  const run = text => [{text, marks:[]}];
  const types = [
    ['paragraph','Texto','Un párrafo para continuar la idea'],['heading','Título','Una sección o subtítulo'],
    ['list','Lista','Ideas o pasos'],['checklist','Checklist','Pendientes que puedes marcar'],
    ['table','Tabla','Filas, columnas y encabezados'],['quote','Cita','Una frase destacada'],
    ['code','Código','Texto literal, sin ejecutar'],['divider','Separador','Una pausa entre secciones'],
  ];
  function block(type) {
    const b={id:'b-'+crypto.randomUUID(),type};
    if(['paragraph','heading','quote'].includes(type))b.runs=run('');
    if(type==='heading')b.level=2;
    if(type==='list'){b.items=[run('')];b.ordered=false;}
    if(type==='checklist'){b.items=[run('')];b.checked=[false];}
    if(type==='table'){b.rows=[['Columna 1','Columna 2'],['','']];b.header=true;b.caption='';}
    if(type==='code')b.text='';
    return b;
  }
  function drawRuns(node,runs) {
    for(const r of runs){let n=document.createTextNode(r.text);for(const m of r.marks||[]){const tag={bold:'strong',italic:'em',code:'code',strike:'s',underline:'u'}[m];if(!tag)continue;const wrap=el(tag);wrap.append(n);n=wrap;}if(r.href){const a=el('a');a.href=r.href;a.tabIndex=-1;a.append(n);n=a;}node.append(n);}
  }
  function readRuns(node) {
    const result=[];
    function walk(n,marks=[],href){
      if(n.nodeType===3){if(n.textContent)result.push({text:n.textContent,marks:[...marks],...(href?{href}:{})});return;}
      if(n.nodeType!==1)return;
      const mark={STRONG:'bold',B:'bold',EM:'italic',I:'italic',CODE:'code',S:'strike',DEL:'strike',U:'underline'}[n.tagName];
      if(n.tagName==='BR'){result.push({text:'\n',marks:[...marks]});return;}
      if(['SCRIPT','STYLE','IMG','IFRAME'].includes(n.tagName))return;
      for(const child of n.childNodes)walk(child,mark?[...new Set([...marks,mark])]:marks,n.tagName==='A'?n.getAttribute('href'):href);
    }
    for(const n of node.childNodes)walk(n);
    return result;
  }
  function plainPaste(event) {
    event.preventDefault();const text=event.clipboardData?.getData('text/plain')||'';
    const selection=window.getSelection();if(!selection?.rangeCount)return;
    const range=selection.getRangeAt(0);range.deleteContents();const node=document.createTextNode(text);range.insertNode(node);range.setStartAfter(node);range.collapse(true);selection.removeAllRanges();selection.addRange(range);
    event.currentTarget.dispatchEvent(new Event('input',{bubbles:true}));
  }
  function readable(value) {
    if(value===null||value===undefined)return '';
    if(typeof value==='string')return value;
    const text=runs=>(runs||[]).map(r=>r.text).join('');
    if(value.runs)return text(value.runs);
    if(value.rows)return [value.caption,...value.rows.map(row=>row.join(' | '))].filter(Boolean).join('\n');
    if(value.items)return value.items.map((runs,i)=>(value.type==='checklist'?(value.checked[i]?'☑ ':'☐ '):'• ')+text(runs)).join('\n');
    if(value.type==='divider')return 'Separador';
    return value.text||value.label||'Bloque';
  }
  async function open({api,artifact,onPublished=()=>{}}) {
    const path='/api/artifacts/'+artifact.id;let state=await api(path+'/editor');
    let doc=clone(state.document),saved=JSON.stringify(doc),timer,pending=null,closed=false,undo=[],redo=[],busy=false;
    const dialog=el('dialog',undefined,'block-editor');dialog.setAttribute('aria-label','Editar artefacto');
    const bar=el('header',undefined,'be-toolbar'),back=el('button','Volver al artefacto'),status=el('span','Guardado','be-status'),actions=el('div',undefined,'be-actions');status.setAttribute('role','status');status.setAttribute('aria-live','polite');
    const undoButton=el('button','Deshacer'),redoButton=el('button','Rehacer'),preview=el('button','Vista previa'),historyButton=el('button','Historial'),publish=el('button','Publicar cambios','primary');
    actions.append(undoButton,redoButton,historyButton,preview,publish);bar.append(back,status,actions);
    const alert=el('div',undefined,'be-alert');alert.hidden=true;alert.setAttribute('role','alert');
    const recovery=el('div',undefined,'be-recovery'),download=el('button','Descargar mis cambios'),restart=el('button','Continuar desde la versión publicada');recovery.hidden=true;recovery.append(download,restart);
    const page=el('div',undefined,'be-page'),intro=el('p','BORRADOR · SOLO TÚ','eyebrow'),title=el('textarea',undefined,'be-title');title.rows=2;title.maxLength=200;title.value=doc.title;title.setAttribute('aria-label','Título del documento');
    const hint=el('p','Escribe / en un bloque vacío para insertar. Tus lectores verán los cambios cuando publiques.','be-hint'),content=el('div',undefined,'be-content');page.append(intro,title,hint,content);dialog.append(bar,alert,recovery,page);document.body.append(dialog);dialog.showModal();
    const dirty=()=>JSON.stringify(doc)!==saved;
    function notice(message){alert.textContent=message;alert.hidden=false;recovery.hidden=false;}
    download.addEventListener('click',()=>{const markdown='# '+doc.title+'\n\n'+doc.regions.flatMap(r=>r.blocks.map(b=>readable(b))).join('\n\n');const url=URL.createObjectURL(new Blob([markdown],{type:'text/markdown;charset=utf-8'}));const link=el('a');link.href=url;link.download='mis-cambios.md';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
    restart.addEventListener('click',()=>{const question=el('div');question.append(el('p','Descarga primero los cambios que quieras conservar. Continuar reemplazará el borrador de trabajo, también si fue editado desde otra pestaña. El historial no cambia.'));const yes=el('button','Reemplazar borrador'),no=el('button','Cancelar');no.addEventListener('click',()=>question.remove());yes.addEventListener('click',async()=>{busy=true;controls();try{if(pending)await pending.catch(()=>{});const latest=await api(path),draft=await api(path+'/editor');state=await api(path+'/editor/restore',{method:'POST',body:JSON.stringify({version:latest.current_version,expected_current:latest.current_version,revision:draft.revision})});doc=clone(state.document);saved=JSON.stringify(doc);undo=[];redo=[];render();status.textContent='Borrador actualizado';alert.hidden=true;recovery.hidden=true;question.remove();}catch(error){notice(error.message);}finally{busy=false;controls();}});question.append(no,yes);recovery.append(question);yes.focus();});
    function controls(){content.inert=busy;title.disabled=busy;undoButton.disabled=!undo.length||busy;redoButton.disabled=!redo.length||busy;publish.disabled=busy||state.stale;preview.disabled=busy;}
    function remember(){undo.push(clone(doc));if(undo.length>50)undo.shift();redo=[];}
    function changed(){status.textContent='Cambios sin guardar';clearTimeout(timer);timer=setTimeout(()=>save().catch(()=>{}),900);controls();}
    async function save(){
      clearTimeout(timer);
      if(state.stale){notice('Hay una versión publicada más reciente. Tu borrador está conservado. Abre el historial para comparar y decidir qué restaurar.');throw Error('Conflicto de versión');}
      if(pending){await pending;if(dirty())return save();return;}
      if(!dirty()&&state.revision>0)return;
      const snapshot=clone(doc),sent=JSON.stringify(snapshot);status.textContent='Guardando…';
      pending=api(path+'/editor',{method:'PUT',body:JSON.stringify({revision:state.revision,base_version:state.base_version,document:snapshot})})
        .then(next=>{state=next;saved=sent;status.textContent=dirty()?'Cambios sin guardar':'Guardado';alert.hidden=true;recovery.hidden=true;})
        .catch(error=>{status.textContent='No guardado';if(error.status===409)state.stale=true;notice(error.message+' Tu texto sigue aquí.');throw error;})
        .finally(()=>{pending=null;controls();});
      await pending;
      if(dirty()&&!closed){clearTimeout(timer);timer=setTimeout(()=>save().catch(()=>{}),900);}
    }
    function mutate(fn,focusId){remember();fn();render(focusId);changed();}
    function editable(runs,label,onInput,b,region){
      const field=el('div',undefined,'be-writing');field.setAttribute('contenteditable','true');field.setAttribute('role','textbox');field.setAttribute('aria-label',label);field.setAttribute('aria-multiline','true');field.dataset.placeholder='Escribe algo, o / para insertar';drawRuns(field,runs);
      field.addEventListener('paste',plainPaste);
      field.addEventListener('input',()=>{const text=field.textContent;if(b?.type==='paragraph'&&text.startsWith('/')&&!text.includes('\n')){showSlash(region,b,text.slice(1),field);return;}remember();onInput(readRuns(field));changed();});
      field.addEventListener('keydown',e=>{if(e.isComposing)return;if(e.key==='Enter'&&!e.shiftKey&&region&&b?.type==='paragraph'){e.preventDefault();const fresh=block('paragraph');mutate(()=>region.blocks.splice(region.blocks.indexOf(b)+1,0,fresh),fresh.id);}});
      field.addEventListener('click',e=>{if(e.target.closest('a'))e.preventDefault();});return field;
    }
    let slash=null;
    function showSlash(region,after,query='',originField=null){
      if(slash){slash.input.value=query;slash.filter();return;}
      const panel=el('div',undefined,'be-slash');panel.setAttribute('role','dialog');panel.setAttribute('aria-label','Insertar bloque');
      const input=el('input');input.type='search';input.placeholder='Buscar bloque…';input.setAttribute('aria-label','Buscar bloque');input.setAttribute('aria-controls','be-slash-options');input.value=query;
      const list=el('div');list.id='be-slash-options';list.setAttribute('role','listbox');let selected=0,visible=[];
      const close=()=>{panel.remove();slash=null;originField?.focus();};
      function choose(type){const fresh=block(type);close();mutate(()=>{const i=region.blocks.indexOf(after);if(after?.type==='paragraph'&&(!after.runs.some(r=>r.text.trim())||originField?.textContent.startsWith('/')))region.blocks.splice(i,1,fresh);else region.blocks.splice(i+1,0,fresh);},fresh.id);}
      function filter(){const q=input.value.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();visible=types.filter(t=>t.join(' ').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().includes(q));selected=Math.min(selected,Math.max(0,visible.length-1));list.replaceChildren();visible.forEach(([type,name,desc],i)=>{const button=el('button');button.type='button';button.id='be-option-'+type;button.setAttribute('role','option');button.setAttribute('aria-selected',String(i===selected));button.append(el('strong',name),el('span',desc));button.addEventListener('click',()=>choose(type));list.append(button);});if(!visible.length)list.append(el('p','No hay bloques con ese nombre.'));input.setAttribute('aria-activedescendant',visible[selected]?'be-option-'+visible[selected][0]:'');}
      input.addEventListener('input',()=>{selected=0;filter();});input.addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();e.stopPropagation();close();}if(['ArrowDown','ArrowUp'].includes(e.key)){e.preventDefault();selected=(selected+(e.key==='ArrowDown'?1:-1)+visible.length)%Math.max(1,visible.length);filter();}if(e.key==='Enter'&&visible[selected]){e.preventDefault();choose(visible[selected][0]);}});
      const cancel=el('button','Cerrar');cancel.addEventListener('click',close);panel.append(input,list,cancel);dialog.append(panel);slash={input,filter,close};filter();input.focus();
    }
    function render(focusId){
      content.replaceChildren();title.value=doc.title;
      for(const region of doc.regions){const section=el('section',undefined,'be-region');section.setAttribute('aria-label',region.label||'Contenido');
        for(const b of region.blocks){const row=el('article',undefined,'be-block');row.dataset.block=b.id;row.dataset.type=b.type;
          const tools=el('div',undefined,'be-block-tools');const menu=el('details'),summary=el('summary','⋮');summary.setAttribute('aria-label','Acciones del bloque');menu.append(summary);
          if(b.type!=='opaque')for(const [label,fn] of [['Mover arriba',()=>{const i=region.blocks.indexOf(b);if(i>0)[region.blocks[i-1],region.blocks[i]]=[b,region.blocks[i-1]];}],['Mover abajo',()=>{const i=region.blocks.indexOf(b);if(i<region.blocks.length-1)[region.blocks[i+1],region.blocks[i]]=[b,region.blocks[i+1]];}],['Duplicar',()=>{const copy=clone(b);copy.id='b-'+crypto.randomUUID();region.blocks.splice(region.blocks.indexOf(b)+1,0,copy);}],['Eliminar',()=>region.blocks.splice(region.blocks.indexOf(b),1)]]){const button=el('button',label);button.addEventListener('click',()=>mutate(fn));menu.append(button);}
          const add=el('button','+');add.setAttribute('aria-label','Insertar después del bloque');add.addEventListener('click',()=>showSlash(region,b));tools.append(add,menu);row.append(tools);
          const body=el('div',undefined,'be-block-body');
          if(['paragraph','heading','quote'].includes(b.type)){
            if(b.type==='heading'){const level=el('select');level.setAttribute('aria-label','Nivel del título');[2,3,4].forEach(n=>{const o=new Option('Título '+(n-1),String(n));level.add(o);});level.value=String(b.level);level.addEventListener('change',()=>mutate(()=>b.level=Number(level.value)));body.append(level);}
            const field=editable(b.runs,b.type==='heading'?'Título de sección':b.type==='quote'?'Cita':'Texto',runs=>b.runs=runs,b,region);body.append(field);
          }else if(['list','checklist'].includes(b.type)){
            if(b.type==='list'){const order=el('button',b.ordered?'Lista numerada':'Lista con viñetas');order.addEventListener('click',()=>mutate(()=>b.ordered=!b.ordered));body.append(order);}
            b.items.forEach((runs,i)=>{const line=el('div',undefined,'be-list-item');if(b.type==='checklist'){const check=el('input');check.type='checkbox';check.checked=b.checked[i];check.setAttribute('aria-label','Marcar elemento '+(i+1));check.addEventListener('change',()=>{remember();b.checked[i]=check.checked;changed();});line.append(check);}else line.append(el('span',b.ordered?(i+1)+'.':'•'));
              line.append(editable(runs,'Elemento '+(i+1),r=>b.items[i]=r));const remove=el('button','−');remove.setAttribute('aria-label','Eliminar elemento '+(i+1));remove.disabled=b.items.length===1;remove.addEventListener('click',()=>mutate(()=>{b.items.splice(i,1);b.checked?.splice(i,1);}));line.append(remove);body.append(line);});
            const addItem=el('button','Añadir elemento');addItem.addEventListener('click',()=>mutate(()=>{b.items.push(run(''));b.checked?.push(false);}));body.append(addItem);
          }else if(b.type==='table'){
            const caption=el('input');caption.value=b.caption;caption.placeholder='Título de la tabla';caption.setAttribute('aria-label','Título de la tabla');caption.addEventListener('input',()=>{remember();b.caption=caption.value;changed();});body.append(caption);
            const box=el('div',undefined,'be-table-scroll');box.tabIndex=0;box.setAttribute('role','region');box.setAttribute('aria-label','Tabla editable, desplazable');const table=el('table');
            b.rows.forEach((values,i)=>{const tr=el('tr');values.forEach((value,j)=>{const td=el(i===0&&b.header?'th':'td'),field=el('textarea');field.rows=2;field.value=value;field.setAttribute('aria-label',`Fila ${i+1}, columna ${j+1}`);field.addEventListener('input',()=>{remember();b.rows[i][j]=field.value;changed();});td.append(field);tr.append(td);});table.append(tr);});box.append(table);body.append(box);
            const bar=el('div',undefined,'be-table-actions');for(const [text,fn,disabled] of [['Añadir fila',()=>b.rows.push(b.rows[0].map(()=>'')),b.rows.length>=100],['Añadir columna',()=>b.rows.forEach(r=>r.push('')),b.rows[0].length>=12],['Quitar última fila',()=>b.rows.pop(),b.rows.length<=1],['Quitar última columna',()=>b.rows.forEach(r=>r.pop()),b.rows[0].length<=1]]){const button=el('button',text);button.disabled=disabled;button.addEventListener('click',()=>mutate(fn));bar.append(button);}body.append(bar);
          }else if(b.type==='code'){const code=el('textarea');code.rows=5;code.value=b.text;code.setAttribute('aria-label','Código');code.spellcheck=false;code.addEventListener('input',()=>{remember();b.text=code.value;changed();});body.append(code);
          }else if(b.type==='divider')body.append(el('hr'));
          else{body.append(el('p','Componente conservado','be-preserved'),el('p',b.label),el('small','Su diseño y contenido se mantienen. Puedes verlo en Vista previa.'));}
          row.append(body);section.append(row);
        }
        const plus=el('button','+ Insertar bloque','be-insert');plus.addEventListener('click',()=>showSlash(region,region.blocks.at(-1)));section.append(plus);content.append(section);
      }
      controls();if(focusId)content.querySelector(`[data-block="${CSS.escape(focusId)}"] [contenteditable], [data-block="${CSS.escape(focusId)}"] textarea`)?.focus();
    }
    title.addEventListener('input',()=>{remember();doc.title=title.value;changed();});
    function travel(from,to){if(busy||!from.length)return;to.push(clone(doc));doc=from.pop();render();changed();}
    undoButton.addEventListener('click',()=>travel(undo,redo));redoButton.addEventListener('click',()=>travel(redo,undo));
    dialog.addEventListener('keydown',e=>{if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='z'){e.preventDefault();e.shiftKey?travel(redo,undo):travel(undo,redo);}if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='s'){e.preventDefault();save().catch(()=>{});}});
    const unload=e=>{if(dirty()||pending){e.preventDefault();e.returnValue='';}};window.addEventListener('beforeunload',unload);
    async function close(){if(busy)return;busy=true;controls();try{if(dirty()||pending)await save();while(dirty())await save();closed=true;clearTimeout(timer);window.removeEventListener('beforeunload',unload);dialog.close();dialog.remove();}catch{notice('No se pudo guardar. El editor sigue abierto para conservar tus cambios.');}finally{busy=false;controls();}}
    back.addEventListener('click',close);dialog.addEventListener('cancel',e=>{e.preventDefault();if(slash)slash.close();else close();});
    preview.addEventListener('click',async()=>{try{await save();const d=el('dialog',undefined,'be-preview');const button=el('button','Volver a editar');button.addEventListener('click',()=>{d.close();d.remove();});const frame=el('iframe');frame.title='Vista previa del borrador';frame.setAttribute('sandbox','allow-scripts allow-downloads');frame.src=path+'/editor/preview';d.append(button,frame);dialog.append(d);d.showModal();d.addEventListener('cancel',()=>d.remove());}catch{}});
    let checkpointRequest=null;
    publish.addEventListener('click',async()=>{if(busy)return;busy=true;controls();try{await save();const revision=state.revision;if(!checkpointRequest||checkpointRequest.revision!==revision)checkpointRequest={revision,request_id:crypto.randomUUID()};const result=await api(path+'/editor/checkpoint',{method:'POST',body:JSON.stringify(checkpointRequest)});await api(path+'/release',{method:'POST',body:JSON.stringify({version:result.version,expected_current:state.base_version})});state=await api(path+'/editor');status.textContent='Publicado · enlace actualizado';artifact.current_version=result.version;await onPublished(result);checkpointRequest=null;}catch(error){notice(error.message);status.textContent='Publicación pendiente';}finally{busy=false;controls();}});
    historyButton.addEventListener('click',()=>history({api,artifact,onRestore:async()=>{state=await api(path+'/editor');doc=clone(state.document);saved=JSON.stringify(doc);undo=[];redo=[];render();status.textContent='Versión restaurada como borrador';alert.hidden=true;},beforeRestore:async()=>{if(dirty()||pending)await save();return state.revision;}}).catch(e=>notice(e.message)));
    render();if(state.stale)notice('Tu borrador parte de una versión anterior. Se conserva completo; revisa el historial antes de continuar.');title.focus();
    return {dialog,save,getDocument:()=>clone(doc),close};
  }
  async function history({api,artifact,onRestore=()=>{},beforeRestore=async()=>null}) {
    const path='/api/artifacts/'+artifact.id,data=await api(path+'/history'),dialog=el('dialog',undefined,'be-history');dialog.setAttribute('aria-label','Historial de cambios');
    const heading=el('div',undefined,'dialog-head'),close=el('button','Cerrar');close.addEventListener('click',()=>{dialog.close();dialog.remove();});heading.append(el('h2','Historial de cambios'),close);dialog.append(heading,el('p','Cada versión conserva su contenido. Restaurar prepara un borrador; el enlace compartido no cambia.','muted'));
    const message=el('p');message.setAttribute('role','status');dialog.append(message);
    for(const version of data.versions){const row=el('section',undefined,'be-version');row.append(el('h3',version.title||artifact.title),el('p',`${version.id===data.current_version?'Publicada':version.state==='draft'?'Borrador':'Anterior'} · ${version.author} · ${new Date(version.created*1000).toLocaleString('es')}`));
      const link=el('a','Abrir esta versión','button');link.href='/a/'+artifact.id+'?version='+version.id;link.target='_blank';link.rel='noopener';row.append(link);
      if(version.changes.length){const details=el('details'),summary=el('summary',version.changes.length+' cambios por bloque');details.append(summary);for(const change of version.changes){const entry=el('div',undefined,'be-diff');entry.append(el('strong',({added:'Añadido',edited:'Editado',deleted:'Eliminado',moved:'Movido'})[change.kind]+' · '+(change.id==='document-title'?'Título del documento':({heading:'Título de sección',paragraph:'Texto',table:'Tabla',list:'Lista',checklist:'Checklist',quote:'Cita',code:'Código',divider:'Separador'})[(change.after||change.before)?.type]||'Bloque')));for(const [label,value] of [['Antes',change.before],['Después',change.after]])if(value!==null){entry.append(el('p',label),el('pre',readable(value)));}details.append(entry);}row.append(details);}
      const restore=el('button','Restaurar como borrador');restore.addEventListener('click',async()=>{restore.disabled=true;try{let revision=await beforeRestore();const draft=await api(path+'/editor');if(revision===null)revision=draft.revision;const confirmation=el('div',undefined,'be-restore-confirm');confirmation.append(el('p','Se reemplazará tu borrador de trabajo con esta versión. Las versiones del historial se conservan.'));const yes=el('button','Restaurar borrador','primary'),no=el('button','Cancelar');no.addEventListener('click',()=>{confirmation.remove();restore.disabled=false;});yes.addEventListener('click',async()=>{yes.disabled=true;try{await api(path+'/editor/restore',{method:'POST',body:JSON.stringify({version:version.id,expected_current:data.current_version,revision})});await onRestore();dialog.close();dialog.remove();}catch(e){message.textContent=e.message;yes.disabled=false;restore.disabled=false;}});confirmation.append(no,yes);row.append(confirmation);yes.focus();}catch(e){message.textContent=e.message;restore.disabled=false;}});row.append(restore);dialog.append(row);
    }
    document.body.append(dialog);dialog.showModal();dialog.addEventListener('cancel',()=>dialog.remove());
  }
  window.MargenBlockEditor={open,history,types,createBlock:block,readRuns};
})();
