/* Shared neural narration controls. Audio and authorization live in the trusted host. */
(() => {
  'use strict';
  if (window.MargenSpeech) return;
  const excluded = 'script,style,noscript,template,nav,summary,button,input,textarea,select,option,dialog,[role=navigation],[role=button],[role=menu],[contenteditable],.revision-ui,[data-revision],.bottifact-toolbar,.barra,[data-apariencia-menu],[data-speech-ui],[data-speech-skip],.salto';
  const blocks = 'h1,h2,h3,h4,h5,h6,p,li,dt,dd,figcaption,caption,td,th,pre,blockquote,div,section,article,main';
  const root = () => document.querySelector('main') || document.body;
  const page = node => node.closest('main.multipagina > .pagina');
  function readable(node, allPages = false) {
    if (!root().contains(node) || node.closest(excluded)) return false;
    for (let el = node; el; el = el.parentElement) {
      // Known chapter pages are editorial content; other hidden content stays excluded.
      if(el.matches('details:not([open])'))return false;
      const chapter = allPages && el.matches('main.multipagina > .pagina');
      if (!chapter && (el.hidden || el.hasAttribute('inert') || el.getAttribute('aria-hidden') === 'true')) return false;
      const css = getComputedStyle(el);
      if ((!chapter && css.display === 'none') || css.visibility === 'hidden' || css.visibility === 'collapse' || css.contentVisibility === 'hidden') return false;
    }
    return true;
  }
  function extract({range, allPages = false} = {}) {
    const result = [], walker = document.createTreeWalker(root(), NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
    let node,lastElement=null,part=0;const parts=new Map();
    while ((node = walker.nextNode())) {
      const lineBreak=node.nodeType===Node.ELEMENT_NODE && node.tagName==='BR';
      if(node.nodeType!==Node.TEXT_NODE && !lineBreak)continue;
      const parent = node.parentElement;
      if (!parent || !readable(parent, allPages)) continue;
      const element = parent.closest(blocks) || parent;
      if(element!==lastElement){part=(parts.get(element)??-1)+1;parts.set(element,part);lastElement=element;}
      let text = lineBreak?' ':node.textContent;
      if (range) {
        if (!range.intersectsNode(node)) continue;
        const start = range.startContainer === node ? range.startOffset : 0;
        const end = range.endContainer === node ? range.endOffset : text.length;
        text = text.slice(start, end);
      }
      const last = result.at(-1);
      if (last?.element === element && last.part===part) last.text += text;
      else result.push({element, part, text});
    }
    return result.map(item => ({...item, text:item.text.replace(/\s+/g, ' ').trim()})).filter(item => item.text);
  }
  function chunk(text, limit = 1200) {
    const chunks = [];
    let rest = text.trim();
    while (rest.length > limit) {
      const prefix = rest.slice(0, limit + 1);
      const sentence = [...prefix.matchAll(/[.!?;:]\s/g)].at(-1);
      let at = sentence && sentence.index > limit / 3 ? sentence.index + 1 : prefix.lastIndexOf(' ');
      if (at < 1) at = limit;
      // Do not split a surrogate pair in long URLs/code.
      if (/[\uD800-\uDBFF]/.test(rest[at - 1])) at--;
      chunks.push(rest.slice(0, at).trim()); rest = rest.slice(at).trim();
    }
    if (rest) chunks.push(rest);
    return chunks;
  }
  let instance;
  window.MargenSpeech = {extract, chunk, mount, stop: () => instance?.stop(), context: (...args) => instance?.context(...args)};
  function mount(bar) {
    if (instance) return instance;
    const abort = new AbortController();
    const on = (target, type, fn, options = {}) => target.addEventListener(type, fn, {...options, signal:abort.signal});
    const make = (tag, text) => {const el = document.createElement(tag); if (text) el.textContent = text; return el;};
    const button = (text, fn) => {const el = make('button', text); el.type = 'button'; on(el, 'click', fn); return el;};
    const bridge = window.BottifactReviewBridge;
    const supported = !!bridge?.narration;
    const style = make('style');
    style.textContent = `
      [data-speech-current]{outline:2px solid var(--foco,#6865c8)!important;outline-offset:4px;background-color:color-mix(in srgb,var(--foco,#6865c8) 9%,transparent)}
      .bf-speech-player{position:fixed;z-index:129;bottom:90px;left:50%;transform:translateX(-50%);width:min(480px,calc(100vw - 24px));box-sizing:border-box;max-height:calc(100dvh - 110px);overflow:auto;padding:12px;border:1px solid var(--linea,#d8d5ce);border-radius:12px;background:var(--papel,#faf9f7);color:var(--tinta,#252322);box-shadow:0 6px 24px #0002;font:13px/1.4 var(--sans,system-ui)}
      .bf-speech-player[hidden],[data-speech-ui][hidden]{display:none!important}
      .bf-speech-player button:disabled{opacity:.45;cursor:not-allowed}.bf-speech-player summary{cursor:pointer;min-height:32px;display:list-item;padding:6px 0;font:inherit}.bf-speech-player details{margin:0;padding:0;border:0;background:transparent}.bf-speech-player p{margin:0 0 8px;font:inherit}.bf-speech-row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.bf-speech-player button,.bf-speech-player select{min-height:44px;max-width:100%;box-sizing:border-box;font:inherit;color:inherit;background:var(--panel,#edeae5);border:1px solid var(--linea,#d8d5ce);border-radius:7px;padding:6px 10px;margin:0}
      .bf-speech-player label{display:flex;align-items:center;gap:8px;font:inherit;margin:6px 0 0}.bf-speech-player select{min-width:0;flex:1}.bf-speech-player :focus-visible{outline:2px solid var(--foco,#6865c8);outline-offset:2px}
      .bf-speech-context{position:fixed;z-index:160;padding:5px;border:1px solid var(--linea,#ddd);border-radius:10px;background:var(--papel,#fff);color:var(--tinta,#222);box-shadow:0 8px 28px #0002;max-width:calc(100vw - 16px);font:13px/1.4 var(--sans,system-ui)}
      .bf-speech-context button{display:block;min-height:44px;width:100%;padding:8px 12px;border:0;border-radius:6px;background:transparent;color:inherit;text-align:left;font:inherit}.bf-speech-context button:focus-visible,.bf-speech-context button:hover{background:var(--panel,#eee);outline:2px solid var(--foco,#6865c8);outline-offset:-2px}
      @media(max-width:540px){.bottifact-toolbar:has([data-speech-tool])>details>summary{min-width:0;padding-inline:7px}.bottifact-toolbar:has([data-speech-tool])>details+details{margin-left:0;padding-left:0}.bf-speech-player{bottom:85px}}
      @media print{[data-speech-ui]{display:none!important}[data-speech-current]{outline:0!important;background:transparent!important}}
    `;
    document.head.append(style);
    const tool = make('details'), summary = make('summary'), menu = make('div');
    summary.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M11 5 6 9H3v6h3l5 4V5Zm4 3a6 6 0 0 1 0 8m3-11a10 10 0 0 1 0 14"/></svg>';
    const toolLabel=make('span','Escuchar');toolLabel.className='bf-tool-label';summary.append(toolLabel);
    tool.dataset.speechTool = ''; tool.dataset.speechUi = ''; summary.setAttribute('aria-label','Escuchar');
    summary.className = 'bf-speech-summary'; menu.className = 'bf-menu'; tool.append(summary,menu); bar.append(tool);
    const player = make('section'); player.className = 'bf-speech-player'; player.dataset.speechUi = ''; player.hidden = true; player.setAttribute('aria-label','Lector de voz');
    const status = make('p'); status.setAttribute('role','status');
    const row = make('div'); row.className = 'bf-speech-row';
    const pause = button('Pausar', () => togglePause());
    const stopButton = button('Detener', () => stop());
    const close = button('Cerrar', () => {stop();player.hidden = true;summary.focus();});
    row.append(pause,stopButton,close);
    const speed = make('select'); speed.setAttribute('aria-label','Velocidad');
    for (const value of [0.75,1,1.25,1.5,2]) {const option = make('option',value+'×');option.value = String(value);speed.append(option);} speed.value='1';
    const voice = make('select'); voice.setAttribute('aria-label','Voz');
    const speedLabel = make('label','Velocidad'), voiceLabel = make('label','Voz');speedLabel.append(speed);voiceLabel.append(voice);
    const profile=make('select');profile.setAttribute('aria-label','Estilo');
    for(const [value,label] of [['report','Informe'],['narrative','Narración'],['neutral','Lectura neutra']]){const option=make('option',label);option.value=value;profile.append(option);}
    const profileLabel=make('label','Estilo');profileLabel.append(profile);
    const privacy = make('p','Voz generada por IA. Antes de enviar texto se pedirá confirmación en el portal.');
    const settings=make('details');settings.append(make('summary','Velocidad, voz y estilo'),speedLabel,voiceLabel,profileLabel,privacy);
    player.append(status,row,settings);document.body.append(player);
    let queue = [], state = 'idle', highlight, selectionRange, picking, internalPage = false, request='', config=null,generation=0;
    const unavailable='La narración neuronal aún no está configurada. No se usará una voz del dispositivo.';
    const message = text => {status.textContent = text;};
    function clearHighlight() {highlight?.removeAttribute('data-speech-current');highlight = null;}
    function stop(text = 'Lectura detenida.') {
      generation++;const wasActive=state!=='idle';request='';queue=[];clearHighlight();state='idle';
      pause.disabled=stopButton.disabled=true;pause.textContent='Pausar';voice.disabled=profile.disabled=false;message(text);
      if(wasActive&&supported)bridge.narration({action:'stop'}).catch(()=>{});
    }
    async function refreshVoices() {
      if(!supported){message('Abre este documento en el portal de Margen para usar narración neuronal. No hay voz del dispositivo como alternativa.');return;}
      const token=generation;
      try{
        const result=await bridge.narration({action:'config'});if(abort.signal.aborted||token!==generation)return;config=result;voice.replaceChildren();
        for(const v of config.voices||[]){const option=make('option',v.label);option.value=v.id;voice.append(option);}
        if(!config.enabled){voice.append(make('option','Narración no configurada'));message(config.reason||unavailable);}
        else {privacy.textContent=`Voz generada por IA · ${config.provider}. El texto se procesa externamente, previa confirmación. Calidad ES/EN pendiente de evaluación auditiva.`;if(state==='idle')message('Listo para solicitar narración.');}
      }catch(error){if(abort.signal.aborted||token!==generation)return;config=null;message(error.message);}
    }
    const unsubscribe=bridge?.subscribeNarration?.(event=>{
      if(!request||event.request!==request)return;
      if(event.state==='ended'||event.state==='error'){stop(event.message);return;}
      state=event.state==='paused'?'paused':'playing';pause.disabled=false;pause.textContent=state==='paused'?'Reanudar':'Pausar';
      message(event.message||'Preparando audio…');
      const item=queue[event.index];if(!item)return;
      if(!item.element.isConnected){stop('El documento cambió. Inicia una nueva lectura.');return;}
      const chapter=page(item.element);
      if(chapter?.hidden){const trigger=[...document.querySelectorAll('[data-ir]')].find(el=>el.dataset.ir===chapter.id);if(trigger){internalPage=true;trigger.click();internalPage=false;}}
      clearHighlight();highlight=item.element;highlight.setAttribute('data-speech-current','');
    });
    async function start(items, includeCode = false) {
      const selection=getSelection(),savedRange=includeCode&&selectionRange?selectionRange.cloneRange():null;
      stop();cancelPick();dismissContext();tool.open=false;player.hidden=false;
      const startGeneration=generation;
      if(!config?.enabled){await refreshVoices();if(abort.signal.aborted||startGeneration!==generation)return;if(!config?.enabled){close.focus({preventScroll:true});return;}}
      const full=extract({allPages:true});
      let mismatch=false;
      queue=items.filter(item=>includeCode||!item.element.closest('pre')).flatMap(item=>{
        const source=full.find(x=>x.element===item.element&&x.part===item.part);if(!source){mismatch=true;return [];}
        let offset=0;
        if(savedRange&&item.element.contains(savedRange.startContainer)){
          const prefix=document.createRange();prefix.selectNodeContents(item.element);prefix.setEnd(savedRange.startContainer,savedRange.startOffset);
          offset=extract({range:prefix}).filter(x=>x.element===item.element&&x.part===item.part).map(x=>x.text).join(' ').length;
        }
        let cursor=source.text.indexOf(item.text,offset);if(cursor<0){mismatch=true;return [];}
        return chunk(item.text).map(text=>{const start=source.text.indexOf(text,cursor);cursor=start+text.length;return {...item,text,fullText:source.text,start,anchor:item.element.closest('[id]')?.id||''};});
      });
      if(mismatch){queue=[];message('El texto cambió. Selecciona de nuevo antes de escuchar.');close.focus({preventScroll:true});return;}
      if(!queue.length){message('No hay texto editorial para leer. El código se lee solo al seleccionarlo.');close.focus({preventScroll:true});return;}
      request=crypto.randomUUID();const token=request;state='pending';pause.disabled=true;stopButton.disabled=false;voice.disabled=profile.disabled=true;
      message('Revisa y confirma el envío del texto en el portal.');stopButton.focus({preventScroll:true});
      if(savedRange){selection.removeAllRanges();selection.addRange(savedRange);}
      try{await bridge.narration({action:'start',request:token,voice:voice.value,profile:profile.value,rate:Number(speed.value),items:queue.map(({element,...item})=>item)});}
      catch(error){if(request===token)stop(error.message);}
    }
    function togglePause(){
      if(state==='idle'||state==='pending')return;
      bridge.narration({action:state==='paused'?'resume':'pause',request}).catch(error=>stop(error.message));
    }
    const from = (target, sectionOnly=false) => {
      const items=extract({allPages:true});
      if(sectionOnly) {const section=target.closest('section,article') || root();return items.filter(item=>section.contains(item.element));}
      const first=items.findIndex(item=>item.element===target || item.element.contains(target) || target.contains(item.element));
      return first<0?[]:items.slice(first);
    };
    const full=button('Escuchar documento completo',()=>start(extract({allPages:true})));
    const selected=button('Leer selección',()=>start(selectionRange?extract({range:selectionRange}):[],true));
    const choose=button('Elegir desde dónde leer',()=>pick());
    const show=button('Mostrar reproductor',()=>{tool.open=false;player.hidden=false;});
    menu.append(full,selected,choose,show,make('p','Selecciona texto o elige un punto. El código se lee solo al seleccionarlo. Nada se reproduce automáticamente.'));
    function rememberSelection() {
      const selection=getSelection();
      if(selection?.rangeCount && !selection.isCollapsed && root().contains(selection.anchorNode) && root().contains(selection.focusNode) && !selection.anchorNode.parentElement?.closest(excluded)) selectionRange=selection.getRangeAt(0).cloneRange();
      else if(!document.activeElement?.closest('[data-speech-ui]')) selectionRange=null;
      selected.disabled=!selectionRange;
    }
    on(document,'selectionchange',rememberSelection);selected.disabled=true;
    on(tool,'toggle',()=>{if(tool.open){player.hidden=true;for(const other of bar.querySelectorAll('details[open]'))if(other!==tool)other.open=false;}});
    // Other menus take precedence over the compact player, without stopping speech.
    on(bar,'toggle',e=>{if(e.target!==tool&&e.target.open)player.hidden=true;},{capture:true});
    on(speed,'change',()=>{if(state!=='idle')bridge.narration({action:'rate',request,rate:Number(speed.value)}).catch(error=>stop(error.message));});
    function cancelPick() {picking?.();picking=null;}
    function pick() {
      cancelPick();document.dispatchEvent(new Event('bottifact:speech-pick'));tool.open=false;player.hidden=true;
      const targets=[...new Set(extract().map(item=>item.element))], saved=new Map(targets.map(el=>[el,el.getAttribute('tabindex')]));
      targets.forEach(el=>el.tabIndex=0);
      const hint=button('Elige un punto para leer · Cancelar',()=>{cancelPick();summary.focus();});hint.dataset.speechUi='';hint.className='bf-controls-status';document.body.append(hint);
      const controller=new AbortController();
      picking=()=>{controller.abort();hint.remove();saved.forEach((value,el)=>value===null?el.removeAttribute('tabindex'):el.setAttribute('tabindex',value));};
      const capture=e=>{const target=targets.find(el=>el===e.target||el.contains(e.target));if(!target)return;e.preventDefault();e.stopImmediatePropagation();cancelPick();context(e,null,target);};
      document.addEventListener('click',capture,{capture:true,signal:controller.signal});
      document.addEventListener('keydown',e=>{if(e.key==='Escape'){cancelPick();summary.focus();}else if(e.key==='Enter')capture(e);},{capture:true,signal:controller.signal});
      targets[0]?.focus({preventScroll:true});
    }
    const contextMenu=make('div');contextMenu.className='bf-speech-context';contextMenu.dataset.speechUi='';contextMenu.hidden=true;contextMenu.setAttribute('role','menu');contextMenu.setAttribute('aria-label','Acciones del punto');document.body.append(contextMenu);
    let returnFocus;
    function dismissContext(restore=false) {contextMenu.hidden=true;if(restore){const target=returnFocus?.isConnected && returnFocus.matches('button,a,summary,[tabindex]')?returnFocus:summary;target.focus({preventScroll:true});}}
    function context(e, comment, picked) {
      if(!picked && (e.defaultPrevented || (e.type==='contextmenu'&&e.shiftKey) || getSelection()?.toString().trim()))return;
      const target=picked || e.target.closest?.(blocks);
      if(!target || !readable(target) || (!picked && e.target.closest('a,button,input,textarea,select,summary,[contenteditable],pre,code')))return;
      e.preventDefault();returnFocus=picked || document.activeElement;contextMenu.replaceChildren();
      if(comment){const b=button(comment.label,()=>{dismissContext();comment.run();});b.setAttribute('role','menuitem');contextMenu.append(b);}
      for(const [label,section] of [['Leer desde aquí',false],['Leer esta sección',true]]){const b=button(label,()=>start(from(target,section)));b.setAttribute('role','menuitem');contextMenu.append(b);}
      const r=target.getBoundingClientRect(),keyboard=e.type==='keydown'||picked;
      contextMenu.hidden=false;const size=contextMenu.getBoundingClientRect();
      contextMenu.style.left=Math.max(8,Math.min(innerWidth-size.width-8,keyboard?r.left:e.clientX))+'px';
      contextMenu.style.top=Math.max(8,Math.min(innerHeight-size.height-8,keyboard?r.top:e.clientY))+'px';contextMenu.firstElementChild.focus();
    }
    // Review gets first refusal and can supply its permission-checked comment action.
    queueMicrotask(()=>{if(abort.signal.aborted)return;on(document,'contextmenu',e=>context(e));on(document,'keydown',e=>{if(e.key==='ContextMenu'||(e.shiftKey&&e.key==='F10'))context(e);});});
    on(document,'keydown',e=>{if(contextMenu.hidden)return;if(e.key==='Escape'){e.preventDefault();dismissContext(true);}if(e.key==='Tab')dismissContext();if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();const buttons=[...contextMenu.children],i=buttons.indexOf(document.activeElement);buttons[(i+(e.key==='ArrowDown'?1:-1)+buttons.length)%buttons.length].focus();}});
    on(document,'pointerdown',e=>{if(!contextMenu.contains(e.target))dismissContext();});on(window,'scroll',()=>dismissContext(),{capture:true,passive:true});on(window,'resize',()=>dismissContext());
    on(document,'bottifact:review-mode',e=>{if(e.detail.active){cancelPick();dismissContext();}});
    on(document,'nota:pagina',()=>{if(!internalPage){stop();cancelPick();selectionRange=null;selected.disabled=true;}});
    on(window,'pagehide',()=>stop());
    refreshVoices();
    instance={stop,context,start,get state(){return state;},destroy(){stop();unsubscribe?.();cancelPick();abort.abort();tool.remove();player.remove();contextMenu.remove();style.remove();instance=null;}};
    return instance;
  }
})();
