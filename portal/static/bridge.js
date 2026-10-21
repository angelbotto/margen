/* Scoped review bridge. No credentials, cookies or direct network access. */
(()=>{'use strict';
  const pending=new Map(),listeners=new Set();let latest=null;const retries=new Map();
  const send=(op,data={})=>new Promise((resolve,reject)=>{
    const id=crypto.randomUUID(),timer=setTimeout(()=>{pending.delete(id);reject(Error('No se pudo guardar. El texto permanece aquí; intenta de nuevo.'));},20000);
    pending.set(id,{resolve,reject,timer});parent.postMessage({bottifact:1,id,op,data},'*');
  });
  let picking=null;
  function captureContext(){
    picking?.();document.querySelector('[data-host-point-picker]')?.remove();
    const abort=new AbortController();picking=()=>stop();const focusBefore=document.activeElement;
    const excluded='.revision-ui,[data-revision],.bottifact-toolbar,.barra,[data-apariencia-menu],dialog';
    const selector='img,svg,canvas,video,audio,iframe,td,th,p,h1,h2,h3,h4,li,figure,pre,article,section,div,main';
    const root=document.querySelector('main')||document.body;
    const targetAt=node=>{const el=node?.nodeType===1?node:node?.parentElement;return el&&root.contains(el)&&!el.closest(excluded)?el.closest('svg')||el.closest(selector)||el:null;};
    const stop=()=>{abort.abort();picking=null;hint.remove();document.documentElement.removeAttribute('data-revisando');for(const [node,old] of focused)old===null?node.removeAttribute('tabindex'):node.setAttribute('tabindex',old);document.dispatchEvent(new CustomEvent('bottifact:review-mode',{detail:{active:false}}));};
    const hint=document.createElement('button');hint.type='button';hint.dataset.hostPointPicker='';hint.className='bf-controls-status revision-ui';hint.textContent='Elige dónde comentar · Cancelar';hint.addEventListener('click',()=>{stop();focusBefore?.focus?.();});
    const focused=new Map();
    function capture(target,selection='',coords){const r=target.getBoundingClientRect(),text=(target.textContent?.trim()||target.getAttribute('alt')||target.getAttribute('aria-label')||target.getAttribute('title')||'').replace(/\s+/g,' ').slice(0,4000);stop();send('context',{reference:target.closest('[id]')?.id||'documento',tag:target.tagName,text,quote:(selection||text||target.tagName).slice(0,1200),page:document.title.slice(0,300),section:target.closest('section')?.querySelector('h2,h3')?.textContent?.slice(0,300)||'',x:coords&&r.width?Math.max(0,Math.min(1,(coords.x-r.left)/r.width)):.5,y:coords&&r.height?Math.max(0,Math.min(1,(coords.y-r.top)/r.height)):.5}).catch(()=>{});}
    const selection=getSelection(),text=selection?.toString().trim(),selected=targetAt(selection?.anchorNode);
    if(text&&selected){capture(selected,text);return;}
    document.body.append(hint);document.documentElement.setAttribute('data-revisando','');document.dispatchEvent(new CustomEvent('bottifact:review-mode',{detail:{active:true}}));
    root.querySelectorAll(selector).forEach(node=>{if(node.closest(excluded)||!node.getClientRects().length)return;focused.set(node,node.getAttribute('tabindex'));node.tabIndex=0;});
    document.addEventListener('click',event=>{const target=targetAt(event.target);if(!target)return;event.preventDefault();event.stopImmediatePropagation();capture(target,'',{x:event.clientX,y:event.clientY});},{capture:true,signal:abort.signal});
    document.addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();stop();focusBefore?.focus?.();}else if(event.key==='Enter'&&focused.has(event.target)){event.preventDefault();capture(event.target);}},{signal:abort.signal});
  }
  document.addEventListener('bottifact:speech-pick',()=>picking?.());
  addEventListener('message',event=>{
    if(event.source!==parent||!event.data||event.data.bottifact!==1)return;
    const message=event.data;
    if(message.op==='stop-speech'){window.MargenSpeech?.stop();return;}
    if(message.op==='capture-context'){
      captureContext();return;
    }
    if(message.op==='focus-thread'){document.dispatchEvent(new CustomEvent('bottifact:focus-thread',{detail:message.thread}));return;}
    if(message.op==='snapshot'){latest=message.data;listeners.forEach(fn=>fn(latest));return;}
    const request=pending.get(message.id);if(!request)return;
    clearTimeout(request.timer);pending.delete(message.id);
    if(message.error)request.reject(Error(message.error));else request.resolve(message.data);
  });
  window.BottifactReviewBridge={
    action:name=>send('action',{name}),
    preferences:value=>send('preferences',value),
    controlsReady:()=>send('controls-ready').catch(()=>{}),
    commit:async data=>{const key=JSON.stringify(data),id=retries.get(key)||crypto.randomUUID();retries.set(key,id);const result=await send('commit',{...data,id});retries.delete(key);latest=result;listeners.forEach(fn=>fn(result));return result;},
    subscribe:fn=>{listeners.add(fn);if(latest)fn(latest);return()=>listeners.delete(fn);},
    identify:()=>send('identify').catch(()=>{}),
    exportPrompt:scope=>send('export',{scope}),
  };
  document.addEventListener('click',event=>{
    const a=event.target.closest?.('a');if(!a)return;
    const href=a.getAttribute('href')||'',base=href.split('#')[0].split('?')[0];
    const mapped=window.BottifactArchiveLinks?.[base]||window.BottifactArchiveLinks?.[base.replace(/^\.\//,'')];
    const path=mapped?(mapped+(href.includes('#')?('#'+href.split('#').slice(1).join('#')):'')):(a.hasAttribute('data-bottifact-link')?href:null);
    if(!path)return;event.preventDefault();send('navigate',{path}).catch(()=>{});
  },true);
  addEventListener('DOMContentLoaded',()=>send('ready',{pins:!!document.querySelector('script[data-nota-modulo="packages/core/components/review.js"]')}).then(value=>{latest=value;listeners.forEach(fn=>fn(value));}).catch(()=>{}),{once:true});
})();
