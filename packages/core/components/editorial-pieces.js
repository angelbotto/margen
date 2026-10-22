/* Actividad, avisos, galería y reacciones: mejoras locales, sin red ni reproducción automática. */
(()=>{'use strict';
 const instances=new WeakMap(),selector='[data-actividad],[data-aviso-animado],[data-galeria],[data-editorial-web],[data-reacciones],.lectura-guiada:not([data-presentation]) .indice';
 const indexJobs=new Map();let indexFrame=0,indexRedraw=false;
 const indexUpdate=()=>{indexFrame=0;const redraw=indexRedraw;indexRedraw=false;
  for(const [el,job] of indexJobs){if(!el.isConnected){instances.get(el)?.destroy();continue;}if(!el.getClientRects().length)continue;job.mask();if(redraw)job.draw();}
 };
 const scheduleIndex=(redraw=false)=>{indexRedraw=indexRedraw||redraw;if(!indexFrame)indexFrame=requestAnimationFrame(indexUpdate);};
 addEventListener('scroll',()=>scheduleIndex(),{passive:true});
 addEventListener('resize',()=>scheduleIndex(true),{passive:true});
 document.addEventListener('nota:pagina',()=>scheduleIndex(true));
 document.addEventListener('nota:tema',()=>scheduleIndex(true));
 document.fonts?.ready.then(()=>scheduleIndex(true));
 function mount(el){
  if(instances.has(el))return;
  const clean=[],motion=matchMedia('(prefers-reduced-motion: reduce)');
  const on=(node,type,fn,opts)=>{node.addEventListener(type,fn,opts);clean.push(()=>node.removeEventListener(type,fn,opts));};
  let api={motion,destroy(){clean.splice(0).forEach(fn=>fn());instances.delete(el);}};
  if(el.classList.contains('indice')){
   const links=[...el.querySelectorAll('a')],NS='http://www.w3.org/2000/svg';
   const decorated=links.map(a=>{
    const label=document.createElement('span');label.className='indice-rotulo';label.append(...a.childNodes);a.append(label);
    const svg=document.createElementNS(NS,'svg');svg.classList.add('indice-tachado');svg.setAttribute('aria-hidden','true');svg.setAttribute('focusable','false');a.append(svg);
    return {a,label,svg};
   });
   const draw=()=>{if(getComputedStyle(el).position!=='fixed')return;
    for(const {a,label,svg} of decorated){const box=a.getBoundingClientRect();if(!box.width)continue;
     svg.setAttribute('viewBox',`0 0 ${box.width} ${box.height}`);
     const range=document.createRange();range.selectNodeContents(label);const paths=[];
     [...range.getClientRects()].filter(r=>r.width>0).forEach((r,i)=>{
      const x=i?Math.max(0,r.left-box.left):0,end=Math.min(box.width,r.right-box.left+2),y=r.top-box.top+r.height*.57,w=end-x;
      const path=document.createElementNS(NS,'path');path.setAttribute('d',`M${x} ${y+.6} C${x+w*.28} ${y-1.1} ${x+w*.65} ${y+1.3} ${end} ${y-.5}`);path.setAttribute('pathLength','1');paths.push(path);
     });svg.replaceChildren(...paths);
    }
   };
   const mask=()=>{const chapter=el.closest('.pagina')||el.closest('.hoja'),fixed=getComputedStyle(el).position==='fixed';
    const enabled=fixed&&chapter&&chapter.offsetHeight>innerHeight+768;el.toggleAttribute('data-indice-mascara',!!enabled);
    if(enabled){const y=Math.round(chapter.getBoundingClientRect().top-el.getBoundingClientRect().top);el.style.setProperty('--indice-fade-y',y+'px');}
   };
   el.setAttribute('data-indice-trazo','');indexJobs.set(el,{draw,mask});
   const observer=new ResizeObserver(()=>scheduleIndex(true));observer.observe(el);scheduleIndex(true);
   clean.push(()=>{observer.disconnect();indexJobs.delete(el);el.removeAttribute('data-indice-trazo');el.removeAttribute('data-indice-mascara');el.style.removeProperty('--indice-fade-y');for(const {label,svg} of decorated){svg.remove();label.replaceWith(...label.childNodes);}});
  }
  if(el.hasAttribute('data-editorial-web')){
   const navigation=el.querySelector(':scope > .web-navegacion'),footer=el.querySelector(':scope > .web-pie');if(!navigation||!footer)return;
   const full=el===document.body,scrollNode=full?window:el,position=()=>full?scrollY:el.scrollTop;
   let previous=position(),distance=0,direction=0,frame=0;
   const show=()=>el.classList.remove('web-nav-oculta');
   const update=()=>{frame=0;const current=position(),delta=current-previous;previous=current;
    if(motion.matches||current<64||navigation.contains(document.activeElement)){show();distance=0;return;}
    const nextDirection=Math.sign(delta);if(nextDirection!==direction){direction=nextDirection;distance=0;}distance+=Math.abs(delta);
    if(distance>=12){el.classList.toggle('web-nav-oculta',direction>0);distance=0;}
   };
   on(scrollNode,'scroll',()=>{if(!frame)frame=requestAnimationFrame(update);},{passive:true});
   on(navigation,'focusin',show);on(motion,'change',()=>{show();previous=position();distance=0;});
   on(footer,'focusin',()=>{show();footer.scrollIntoView({block:'end',behavior:'instant'});});
   // Native hash links keep their destinations without JS. Focus follows an
   // in-page selection so keyboard users land in the content, not a hidden bar.
   on(el,'click',event=>{const link=event.target.closest('a[href^="#"]');if(!link||!el.contains(link))return;let target;try{target=document.getElementById(decodeURIComponent(link.hash.slice(1)));}catch{return;}if(!target||!el.contains(target))return;
    const hadTabindex=target.hasAttribute('tabindex');if(!hadTabindex)target.tabIndex=-1;target.focus({preventScroll:true});if(!hadTabindex)target.addEventListener('blur',()=>target.removeAttribute('tabindex'),{once:true});show();
   });
   clean.push(()=>{if(frame)cancelAnimationFrame(frame);show();});
  }
  if(el.hasAttribute('data-actividad')){
   const map=el.querySelector('[data-actividad-mapa]'),legend=el.querySelector('[data-actividad-escala]'),status=el.querySelector('[data-actividad-estado]');if(!map||!legend||!status)return;
   const original=[map.innerHTML,legend.innerHTML,status.textContent];
   const source=el.hasAttribute('data-actividad-tabla')?document.getElementById(el.dataset.actividadTabla):el;
   const rows=[...(source?.querySelectorAll('tbody tr')||[])].map(tr=>({label:tr.querySelector('th')?.textContent.trim(),raw:tr.querySelector('[data-valor]')?.getAttribute('data-valor')}));
   if(!rows.length||rows.length>52||rows.some(r=>!r.label||r.raw===null||r.raw===undefined||r.raw.trim()===''||!Number.isInteger(Number(r.raw))||Number(r.raw)<0||Number(r.raw)>1e6)){
    status.textContent='No se puede dibujar la actividad: revisa los conteos enteros no negativos de la tabla.';
   }else{
    const values=rows.map(r=>Number(r.raw)),maximum=Math.max(...values),step=Math.max(1,Math.ceil(maximum/4)),total=values.reduce((a,b)=>a+b,0);
    const labels=[{label:'0',level:0},...Array.from({length:4},(_,i)=>({from:i*step+1,to:Math.min(maximum,(i+1)*step),level:i+1})).filter(r=>r.from<=r.to).map(r=>({...r,label:r.from===r.to?String(r.from):r.from+'–'+r.to}))];
    legend.replaceChildren();labels.forEach(({label,level})=>{const span=document.createElement('span'),swatch=document.createElement('i');swatch.className='actividad-nivel-'+level;swatch.setAttribute('aria-hidden','true');span.append(swatch,document.createTextNode(label));legend.append(span);});
    map.replaceChildren();rows.forEach((row,i)=>{const value=values[i],b=document.createElement('button');b.type='button';b.className='actividad-celda actividad-nivel-'+(value?Math.min(4,Math.ceil(value/step)):0);b.setAttribute('aria-label',row.label+': '+value+' acciones de '+total+' en total.');b.textContent=String(value);b.title=row.label+': '+value+' acciones';const select=()=>{status.textContent=row.label+': '+value+' acciones. '+(total?(100*value/total).toFixed(1):'0')+' % de las '+total+' del período.';};on(b,'click',select);on(b,'focus',select);on(b,'pointerenter',select);map.append(b);});
    status.textContent=total+' acciones en '+rows.length+' períodos. Consulta una celda para ver su contexto.';
   }
   clean.push(()=>{map.innerHTML=original[0];legend.innerHTML=original[1];status.textContent=original[2];});
  }
  if(el.hasAttribute('data-aviso-animado')){
   const icon=el.querySelector('.num');if(!icon)return;
   const halo=document.createElement('span');halo.className='aviso-pulso';halo.setAttribute('aria-hidden','true');icon.append(halo);
   let animation=null,visible=false,played=false;
   const stop=()=>{animation?.cancel();animation=null;};
   const play=()=>{stop();if(!visible||motion.matches||document.hidden)return;animation=halo.animate([{transform:'scale(1)',opacity:.55},{transform:'scale(1.65)',opacity:0}],{duration:1000,iterations:2,easing:'cubic-bezier(0,0,.2,1)'});animation.onfinish=stop;};
   const observer=new IntersectionObserver(entries=>{visible=entries[0].isIntersecting&&entries[0].intersectionRatio>=.25;if(!visible)stop();else if(!played){played=true;play();}},{threshold:.25});observer.observe(el);
   on(el,'pointerenter',play);on(el,'focusin',play);on(motion,'change',stop);on(document,'visibilitychange',()=>{if(document.hidden)stop();});
   clean.push(()=>{observer.disconnect();stop();halo.remove();});api.play=play;Object.defineProperty(api,'animating',{get:()=>!!animation});
  }
  if(el.hasAttribute('data-galeria')){
   const track=el.querySelector('[data-galeria-pista]'),prev=el.querySelector('[data-galeria-anterior]'),next=el.querySelector('[data-galeria-siguiente]'),status=el.querySelector('[data-galeria-estado]');if(!track||!status)return;
   // Arrastre directo sólo con ratón; tacto y teclado conservan el desplazamiento nativo.
   if(el.classList.contains('galeria-fotografica')){
    let drag=null;
    const end=()=>{if(!drag)return;const id=drag.id;drag=null;track.classList.remove('arrastrando');if(track.hasPointerCapture(id))track.releasePointerCapture(id);};
    on(track,'pointerdown',e=>{if(e.pointerType!=='mouse'||e.button!==0||e.target.closest('a,button,input,textarea,select'))return;drag={id:e.pointerId,x:e.clientX,left:track.scrollLeft};track.setPointerCapture(e.pointerId);});
    on(track,'pointermove',e=>{if(!drag||e.pointerId!==drag.id||Math.abs(e.clientX-drag.x)<4)return;e.preventDefault();track.classList.add('arrastrando');track.scrollLeft=drag.left-(e.clientX-drag.x);});
    on(track,'pointerup',end);on(track,'pointercancel',end);on(track,'lostpointercapture',end);on(track,'dragstart',e=>e.preventDefault());clean.push(end);
   }
   const items=[...track.children],original={prev:prev?.disabled,next:next?.disabled,text:status.textContent,fadeStart:track.style.getPropertyValue('--galeria-fade-inicio'),fadeEnd:track.style.getPropertyValue('--galeria-fade-fin')};let timer,fadeFrame=0;
   // Edge fades follow the scroll every frame; the status text waits for rest.
   const fade=()=>{fadeFrame=0;if(!el.classList.contains('galeria-fotografica'))return;const left=track.scrollLeft,room=track.scrollWidth-track.clientWidth,edge=Math.min(track.clientWidth*.12,40);track.style.setProperty('--galeria-fade-inicio',Math.min(edge,Math.max(0,left))+'px');track.style.setProperty('--galeria-fade-fin',Math.min(edge,Math.max(0,room-left))+'px');};
   const update=()=>{fade();const r=track.getBoundingClientRect(),index=items.reduce((best,e,i)=>Math.abs(e.getBoundingClientRect().left-r.left)<Math.abs(items[best].getBoundingClientRect().left-r.left)?i:best,0);if(prev)prev.disabled=track.scrollLeft<=1;if(next)next.disabled=track.scrollLeft>=track.scrollWidth-track.clientWidth-1;status.textContent=items.length?'Vista '+(index+1)+' de '+items.length+'. Desliza para recorrer.':'No hay imágenes en esta galería.';};
   const move=direction=>{const r=track.getBoundingClientRect(),current=track.scrollLeft,positions=items.map(e=>current+e.getBoundingClientRect().left-r.left),target=direction>0?positions.find(x=>x>current+2):positions.reverse().find(x=>x<current-2);track.scrollTo({left:target??(direction>0?track.scrollWidth:0),behavior:motion.matches?'instant':'smooth'});};
   if(prev)on(prev,'click',()=>move(-1));if(next)on(next,'click',()=>move(1));on(track,'scroll',()=>{if(!fadeFrame)fadeFrame=requestAnimationFrame(fade);clearTimeout(timer);timer=setTimeout(update,90);},{passive:true});
   on(motion,'change',()=>{if(motion.matches)track.scrollTo({left:track.scrollLeft,behavior:'instant'});update();});
   const observer=new ResizeObserver(update);observer.observe(track);update();
   clean.push(()=>{clearTimeout(timer);cancelAnimationFrame(fadeFrame);observer.disconnect();track.scrollTo({left:track.scrollLeft,behavior:'instant'});if(prev)prev.disabled=original.prev;if(next)next.disabled=original.next;status.textContent=original.text;for(const [name,value] of [['--galeria-fade-inicio',original.fadeStart],['--galeria-fade-fin',original.fadeEnd]]){if(value)track.style.setProperty(name,value);else track.style.removeProperty(name);}});
  }
  if(el.hasAttribute('data-reacciones')){
   // Solo este navegador: sin conteos compartidos ni red. Sin almacenamiento, siguen funcionando en la sesión.
   const buttons=[...el.querySelectorAll('[data-reaccion]')];if(!buttons.length)return;
   const key='margen-reacciones:'+(document.querySelector('meta[name="nota-documento"]')?.content||location.pathname)+':'+(el.dataset.reacciones||'documento');
   let chosen=new Set();const temporary=()=>{const note=el.querySelector('.reacciones-nota');if(note)note.textContent='La selección se conserva mientras esta página siga abierta. No hay conteos compartidos.';};
   try{const saved=JSON.parse(localStorage.getItem(key)||'[]');if(Array.isArray(saved))chosen=new Set(saved.filter(v=>buttons.some(b=>b.dataset.reaccion===v)));}catch{temporary();}
   const paint=()=>buttons.forEach(b=>b.setAttribute('aria-pressed',String(chosen.has(b.dataset.reaccion))));
   buttons.forEach(b=>on(b,'click',()=>{const v=b.dataset.reaccion;chosen.has(v)?chosen.delete(v):chosen.add(v);paint();try{localStorage.setItem(key,JSON.stringify([...chosen]));}catch{temporary();}}));
   paint();clean.push(()=>buttons.forEach(b=>b.setAttribute('aria-pressed','false')));
  }
  instances.set(el,api);
 }
 function init(root=document){
  const framed='.marcos-editoriales :is(.ancho,.amplio):not(.marco-difuso),.marco-punteado';
  [...(root.matches?.(framed)?[root]:[]),...root.querySelectorAll(framed)].forEach(el=>{
   // Una composición tiene un marco exterior; sus piezas no crean otra rejilla.
   const existing=el.querySelector(':scope > .marco-lineas');
   if(el.parentElement?.closest('.marco-difuso,.marco-punteado,.marcos-editoriales :is(.ancho,.amplio)')){existing?.remove();return;}
   if(existing)return;const lines=document.createElement('span');lines.className='marco-lineas';lines.setAttribute('aria-hidden','true');el.append(lines);
  });
  [...(root.matches?.(selector)?[root]:[]),...root.querySelectorAll(selector)].forEach(mount);}
 window.NotaPiezasEditoriales={init,get:el=>instances.get(el)};init();
 // Bordes de lectura: capas decorativas fuera del flujo, una sola vez por documento.
 if(document.querySelector('.hoja.lectura-guiada:not([data-presentation])')&&!document.querySelector('.lectura-bordes')){const edges=document.createElement('div');edges.className='lectura-bordes';edges.setAttribute('aria-hidden','true');edges.innerHTML='<span></span>'.repeat(8);document.body.append(edges);}
})();
