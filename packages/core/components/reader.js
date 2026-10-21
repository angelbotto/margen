/* Bottifact. Pegar una vez al final del fragmento, dentro de <script>. */
(() => {
  'use strict';
  const root = document.documentElement;
  const selectors = document.querySelectorAll('[data-tema]');
  /* REGISTRO TEMAS */ const themeRegistry = {"familias":[{"id":"editorial","nombre":"Editorial","grupo":"editorial","descripcion":"Papel cálido · cobre","light":"light","dark":"dark"},{"id":"sea","nombre":"Sea","grupo":"editorial","descripcion":"Azul oceánico · menta","light":"sea-light","dark":"sea"},{"id":"oliva","nombre":"Oliva","grupo":"editorial","descripcion":"Botánico · verde","light":"oliva","dark":"oliva-dark"},{"id":"arcilla","nombre":"Arcilla","grupo":"editorial","descripcion":"Terracota · arena","light":"arcilla","dark":"arcilla-dark"},{"id":"ciruela","nombre":"Ciruela","grupo":"editorial","descripcion":"Malva · tinta violeta","light":"ciruela-light","dark":"ciruela"},{"id":"liftit","nombre":"Liftit","grupo":"marca","descripcion":"LMS · Ribbon, Bay y coral","light":"liftit-light","dark":"liftit-dark"},{"id":"tikin","nombre":"Tikin","grupo":"marca","descripcion":"Blanco y negro · rojo Tikin","light":"tikin-light","dark":"tikin-dark"},{"id":"catabum","nombre":"Catabum","grupo":"marca","descripcion":"Comunidad · violeta y magenta","light":"catabum-light","dark":"catabum-dark"},{"id":"kaira","nombre":"Kaira","grupo":"marca","descripcion":"Warm paper · deep plum · antique gold","light":"kaira-light","dark":"kaira-dark"},{"id":"blueprint","nombre":"Blueprint","grupo":"tecnico","descripcion":"Plano · cuadrícula","light":"blueprint-light","dark":"blueprint"},{"id":"hacker","nombre":"Hacker","grupo":"tecnico","descripcion":"Terminal · verde","light":"hacker-light","dark":"hacker"},{"id":"linear","nombre":"Linear","grupo":"producto","descripcion":"Grafito · lavanda","light":"linear-light","dark":"linear-dark"},{"id":"modern","nombre":"Modern","grupo":"editor","descripcion":"VS Code · azul","light":"modern-light","dark":"modern-dark"},{"id":"github","nombre":"GitHub","grupo":"editor","descripcion":"Neutros · azul","light":"github-light","dark":"github-dark"},{"id":"catppuccin","nombre":"Catppuccin","grupo":"editor","descripcion":"Latte / Mocha · pastel","light":"catppuccin-light","dark":"catppuccin-dark"},{"id":"solarized","nombre":"Solarized","grupo":"editor","descripcion":"Marfil / petróleo · cian","light":"solarized-light","dark":"solarized-dark"}],"aliases":{"system":["editorial","system"],"light":["editorial","light"],"dark":["editorial","dark"],"linear-light":["linear","light"],"linear-dark":["linear","dark"],"sea":["sea","dark"],"oliva":["oliva","light"],"arcilla":["arcilla","light"],"ciruela":["ciruela","dark"],"liftit":["liftit","light"],"blueprint":["blueprint","dark"],"hacker":["hacker","dark"]}}; /* FIN REGISTRO TEMAS */
  const families=new Map(themeRegistry.familias.map(f=>[f.id,f]));
  const modes=['light','dark','system'];
  const initialTheme=document.querySelector('meta[name="nota-tema-inicial"]')?.content;
  const initialMode=document.querySelector('meta[name="nota-modo-inicial"]')?.content;
  const initialStyle=document.querySelector('meta[name="nota-estilo-inicial"]')?.content;
  const preferenceKey=key=>((initialTheme||initialMode||initialStyle)?key+':'+location.pathname:key);
  const scheme=matchMedia('(prefers-color-scheme: dark)');
  const legacy=value=>themeRegistry.aliases[value]||[families.has(value)?value:'editorial','system'];
  let [family,mode]=legacy(initialTheme);
  if(modes.includes(initialMode))mode=initialMode;
  try {
    const saved=JSON.parse(localStorage.getItem(preferenceKey('nota-apariencia-v2'))||'null');
    if(saved&&families.has(saved.family)&&modes.includes(saved.mode)){family=saved.family;mode=saved.mode;}
    else {
      const old=localStorage.getItem(preferenceKey('nota-tema'));
      if(old)[family,mode]=legacy(old);
    }
  } catch {}
  const modeNames={light:'Claro',dark:'Oscuro',system:'Sistema'};
  function syncAppearance(persist=false) {
    const effective=mode==='system'?(scheme.matches?'dark':'light'):mode;
    const selected=families.get(family);
    root.dataset.themeFamily=family;
    root.dataset.themeMode=mode;
    root.dataset.colorMode=effective;
    root.dataset.theme=selected[effective];
    selectors.forEach(selector=>{
      const value=root.dataset.theme;
      if(![...selector.options].some(option=>option.value===value))selector.add(new Option(selected.nombre+' · '+modeNames[effective],value));
      selector.value=value;
    });
    document.querySelectorAll('[data-elegir-tema]').forEach(input=>input.checked=input.value===family);
    document.querySelectorAll('[data-elegir-modo]').forEach(input=>input.checked=input.value===mode);
    document.querySelectorAll('[data-apariencia-menu]').forEach(menu=>{
      menu.dataset.oscuro=String(effective==='dark');
      const name=selected.nombre+' · '+modeNames[effective];
      menu.querySelector('summary').setAttribute('aria-label',(menu.closest('.bottifact-toolbar')?'Preferencias. ':'Apariencia. ')+name+(mode==='system'?', según el sistema':'')+'.');
      menu.querySelectorAll('[data-tema-actual]').forEach(label=>label.textContent=name);
      menu.querySelectorAll('[data-modo-estado]').forEach(label=>label.textContent=mode==='system'?'Ahora en '+modeNames[effective].toLowerCase()+', según tu dispositivo.':'Modo '+modeNames[effective].toLowerCase()+' para cualquier tema.');
    });
    if(persist)try{localStorage.setItem(preferenceKey('nota-apariencia-v2'),JSON.stringify({family,mode}));}catch{}
    document.dispatchEvent(new CustomEvent('nota:tema',{detail:{family,mode,effective,palette:root.dataset.theme}}));
  }
  function setAppearance(next={}) {
    if(next.family!==undefined&&!families.has(next.family))return false;
    if(next.mode!==undefined&&!modes.includes(next.mode))return false;
    family=next.family??family;mode=next.mode??mode;syncAppearance(true);return true;
  }
  // Mantiene tema y modo independientes. Los selectores antiguos aceptan sus IDs de paleta.
  selectors.forEach(selector=>selector.addEventListener('change',e=>{
    const value=e.target.value;
    const paired=themeRegistry.familias.flatMap(f=>['light','dark'].map(m=>({family:f.id,mode:m,palette:f[m]}))).find(p=>p.palette===value);
    if(paired)setAppearance(paired);else{const [f,m]=legacy(value);setAppearance({family:f,mode:m});}
  }));
  document.addEventListener('change',e=>{
    if(e.target.matches('[data-elegir-tema]'))setAppearance({family:e.target.value});
    if(e.target.matches('[data-elegir-modo]'))setAppearance({mode:e.target.value});
  });
  scheme.addEventListener('change',()=>{if(mode==='system')syncAppearance();});
  window.NotaTemas=Object.freeze({set:setAppearance,get:()=>({family,mode,effective:root.dataset.colorMode,palette:root.dataset.theme})});
  syncAppearance(true);
  // Variante optativa: las notas antiguas conservan su escala de lectura.
  function comfort(enabled) {
    root.toggleAttribute('data-lectura-comoda', enabled);
    document.querySelectorAll('[data-comodidad]').forEach(button => button.setAttribute('aria-pressed', String(enabled)));
    try { localStorage.setItem('nota-lectura-comoda', String(enabled)); } catch {}
  }
  let comfortable = false;
  try { comfortable = localStorage.getItem('nota-lectura-comoda') === 'true'; } catch {}
  if (document.querySelector('[data-comodidad]')) comfort(comfortable);
  document.addEventListener('click', e => {
    if (e.target.closest('[data-comodidad]')) comfort(!root.hasAttribute('data-lectura-comoda'));
  });

  // Tipografía y trama son ejes optativos, independientes de la paleta.
  function readingStyle(value) {
    if(!['editorial','sobrio','tecnico','libro','revista','bitacora'].includes(value))value='editorial';
    if(value==='editorial')delete root.dataset.estilo;else root.dataset.estilo=value;
    document.querySelectorAll('[data-elegir-estilo]').forEach(input=>input.checked=input.value===value);
    try{localStorage.setItem(preferenceKey('nota-estilo'),value);}catch{}
  }
  function paper(enabled) {
    root.toggleAttribute('data-trama',enabled);
    document.querySelectorAll('[data-papel-tramado]').forEach(b=>b.setAttribute('aria-pressed',String(enabled)));
    try{localStorage.setItem('nota-trama',String(enabled));}catch{}
  }
  let style=initialStyle||'editorial',texture=false;
  try{style=localStorage.getItem(preferenceKey('nota-estilo'))||style;texture=localStorage.getItem('nota-trama')==='true';}catch{}
  if(document.querySelector('[data-elegir-estilo]'))readingStyle(style);
  if(document.querySelector('[data-papel-tramado]'))paper(texture);
  document.addEventListener('change',e=>{if(e.target.matches('[data-elegir-estilo]'))readingStyle(e.target.value);});
  document.addEventListener('click',e=>{if(e.target.closest('[data-papel-tramado]'))paper(!root.hasAttribute('data-trama'));});

  // Disclosure nativo; el panel se superpone sólo cuando JS puede mantenerlo en pantalla.
  const menus=[...document.querySelectorAll('[data-apariencia-menu]')];
  function place(menu) {
    if(!menu.open)return;
    const panel=menu.querySelector('.apariencia-panel'),trigger=menu.querySelector('summary');
    const viewport=window.visualViewport,w=viewport?.width||innerWidth,h=viewport?.height||innerHeight;
    const ox=viewport?.offsetLeft||0,oy=viewport?.offsetTop||0,gap=12;
    panel.style.width=Math.max(1,Math.min(menu.querySelector('.apariencia-explorador')?380:324,w-gap*2))+'px';
    panel.style.maxHeight=Math.max(1,h-gap*2)+'px';
    const r=trigger.getBoundingClientRect(),height=panel.getBoundingClientRect().height;
    if(r.bottom<oy||r.top>oy+h){close(menu);return;}
    const below=Math.max(0,oy+h-gap-r.bottom-8),above=Math.max(0,r.top-oy-gap-8);
    const up=height>below&&above>below;
    panel.style.maxHeight=Math.max(1,up?above:below)+'px';
    const top=up?r.top-panel.getBoundingClientRect().height-8:r.bottom+8;
    panel.style.top=top+'px';
    panel.style.left=Math.max(ox+gap,Math.min(r.right-panel.getBoundingClientRect().width,ox+w-panel.getBoundingClientRect().width-gap))+'px';
  }
  function close(menu,returnFocus=false) {menu.open=false;if(returnFocus)menu.querySelector('summary').focus();}
  menus.forEach(menu=>{
    menu.dataset.menuListo='';
    // Los controles antiguos conservan el disclosure; la receta nueva añade exploración local.
    const tabs=[...menu.querySelectorAll('[data-preferencia-tab]')];
    const showTab=(tab,focus=false)=>{
      tabs.forEach(t=>{const active=t===tab;t.setAttribute('aria-selected',String(active));t.tabIndex=active?0:-1;});
      menu.querySelectorAll('[data-preferencia-panel]').forEach(p=>p.hidden=p.dataset.preferenciaPanel!==tab.dataset.preferenciaTab);
      if(focus)tab.focus();place(menu);
    };
    tabs.forEach((tab,index)=>{
      tab.addEventListener('click',()=>showTab(tab));
      tab.addEventListener('keydown',e=>{
        const next=e.key==='ArrowRight'?(index+1)%tabs.length:e.key==='ArrowLeft'?(index+tabs.length-1)%tabs.length:e.key==='Home'?0:e.key==='End'?tabs.length-1:null;
        if(next!==null){e.preventDefault();showTab(tabs[next],true);}
      });
    });
    const search=menu.querySelector('[data-buscar-tema]'),family=menu.querySelector('[data-familia-tema]');
    const normalize=s=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
    const filterThemes=()=>{
      const query=normalize(search?.value||''),group=family?.value||'';
      const labels=[...menu.querySelectorAll('[data-tema-familia]')];let count=0;
      labels.forEach(label=>{label.hidden=!!((group&&label.dataset.temaFamilia!==group)||(query&&!normalize(label.textContent).includes(query)));if(!label.hidden)count++;});
      const status=menu.querySelector('[data-temas-resultados]');if(status)status.textContent=count?count+' de '+labels.length+' temas':'No encontramos ese tema.';
      const clear=menu.querySelector('[data-limpiar-temas]');if(clear)clear.hidden=!query&&!group;
      place(menu);
    };
    search?.addEventListener('input',filterThemes);family?.addEventListener('change',filterThemes);
    menu.querySelector('[data-limpiar-temas]')?.addEventListener('click',()=>{search.value='';family.value='';filterThemes();search.focus();});
    if(tabs.length)filterThemes();

    menu.querySelector('summary').addEventListener('click',e=>{
      e.preventDefault();const opening=!menu.open;menus.forEach(other=>close(other));menu.open=opening;place(menu);
    });
    menu.addEventListener('toggle',()=>{if(menu.open){
      menus.forEach(other=>{if(other!==menu)close(other);});place(menu);
      const selected=menu.querySelector('[data-elegir-tema]:checked')?.closest('label'),grid=menu.querySelector('.apariencia-colores');
      if(selected&&grid&&selected.getClientRects().length){const r=selected.getBoundingClientRect(),g=grid.getBoundingClientRect();if(r.bottom>g.bottom)grid.scrollTop+=r.bottom-g.bottom+4;else if(r.top<g.top)grid.scrollTop+=r.top-g.top-4;}
    }});
    menu.addEventListener('change',()=>place(menu));
  });
  document.addEventListener('pointerdown',e=>menus.forEach(menu=>{if(menu.open&&!menu.contains(e.target))close(menu);}));
  document.addEventListener('focusin',e=>menus.forEach(menu=>{if(menu.open&&!menu.contains(e.target))close(menu);}));
  document.addEventListener('keydown',e=>{if(e.key==='Escape'){const open=menus.find(menu=>menu.open);if(open){e.preventDefault();close(open,true);}}});
  const placeMenus=()=>menus.forEach(place);
  addEventListener('resize',placeMenus);addEventListener('scroll',placeMenus,{passive:true});
  window.visualViewport?.addEventListener('resize',placeMenus);
  window.visualViewport?.addEventListener('scroll',placeMenus,{passive:true});

  // El progreso pertenece al artículo, no al footer del documento envolvente.
  const article = document.querySelector('[data-lectura]');
  const links = [...document.querySelectorAll('.indice a[href^="#"]')];
  const sections = links.map(a => document.getElementById(a.hash.slice(1)));
  const ruler = document.querySelector('.regla');
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  function readingMetrics() {
    const perPage=article.hasAttribute('data-progreso-pagina');
    const target=perPage?article.querySelector('.pagina.viva')||article:article;
    const rect=target.getBoundingClientRect();
    const offset=perPage?document.querySelector('.barra')?.getBoundingClientRect().height||0:0;
    return {target,rect,start:scrollY+rect.top-offset,distance:Math.max(0,rect.height-innerHeight+offset)};
  }
  function goToProgress(value) {
    if (!article) return;
    const {start,distance}=readingMetrics();
    const top=start+distance*Math.max(0,Math.min(100,value))/100;
    scrollTo({top,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});
  }
  ruler?.addEventListener('click',e=>{const r=ruler.getBoundingClientRect();goToProgress(ruler.getAttribute('aria-orientation')==='horizontal'?(e.clientX-r.left)/r.width*100:(e.clientY-r.top)/r.height*100);});
  ruler?.addEventListener('keydown',e=>{
    const current=Number(ruler.getAttribute('aria-valuenow'));
    const values={ArrowDown:current+1,ArrowRight:current+1,ArrowUp:current-1,ArrowLeft:current-1,PageDown:current+10,PageUp:current-10,Home:0,End:100};
    if(e.key in values){e.preventDefault();goToProgress(values[e.key]);}
  });
  let frame = 0;
  function update() {
    frame = 0;
    if (!article) return;
    // La barra aún no está pegada al borde al inicio: medir su fondo, no sólo su altura.
    const barBottom=Math.max(0,document.querySelector('.barra')?.getBoundingClientRect().bottom||0);
    root.style.setProperty('--lectura-cabecera',Math.ceil(barBottom+24)+'px');
    const {target,rect,start,distance}=readingMetrics();
    const progress=distance<=0?(rect.bottom<=innerHeight?1:0):Math.max(0,Math.min(1,(scrollY-start)/distance));
    if (ruler) {
      if(ruler.classList.contains('regla-guiada'))ruler.setAttribute('aria-orientation',matchMedia('(min-width:1200px)').matches?'vertical':'horizontal');
      if(article.hasAttribute('data-progreso-pagina')){
        ruler.setAttribute('aria-controls',target.id);
        ruler.setAttribute('aria-label','Progreso de lectura: '+(target.querySelector('h1')?.textContent||'esta página'));
      }
      ruler.style.setProperty('--lectura',progress);
      ruler.setAttribute('aria-valuenow',Math.round(progress * 100));
      const value = ruler.querySelector('.val');
      if (value) value.textContent = Math.round(progress * 100) + '%';
    }
    // En multipágina el índice pertenece a packages/core/components/chapters.js; no medir páginas ocultas.
    if (article.classList.contains('multipagina')) return;
    let active = -1;
    sections.forEach((section,index) => { if (section?.getBoundingClientRect().top <= 120) active = index; });
    if (progress === 1 && links.length) active = links.length - 1;
    links.forEach((a,index) => {
      a.closest('li')?.classList.toggle('visto',index < active);
      if (index === active) a.setAttribute('aria-current','location'); else a.removeAttribute('aria-current');
    });
  }
  const schedule = () => { if (motion.matches) { if(frame)cancelAnimationFrame(frame);update(); } else if (!frame) frame = requestAnimationFrame(update); };
  motion.addEventListener('change',schedule);
  addEventListener('scroll',schedule,{passive:true});
  addEventListener('resize',schedule);
  document.addEventListener('nota:pagina',schedule);
  if (article && window.ResizeObserver) new ResizeObserver(schedule).observe(article);
  document.fonts?.ready.then(schedule);
  update();

  document.querySelectorAll('[data-copiar]').forEach(button => {
    if(button.closest('.codigo,.terminal')){button.classList.add('nota-icono');button.setAttribute('aria-label',button.getAttribute('aria-label')||'Copiar código');button.title=button.getAttribute('aria-label');button.innerHTML='<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V3H4v13h4"/></svg>';
      const block=button.closest('.codigo,.terminal'),heading=block.querySelector('.cab > span:not(.copia-estado)');block.classList.add('codigo-compacto');if(heading&&/^(CSS|HTML|JavaScript|TypeScript|JSON|Python|SQL|Shell|Bash|Terminal)$/i.test(heading.textContent.trim()))block.classList.add('codigo-sin-titulo');
    }
    button.addEventListener('click',async () => {
      const code = document.getElementById(button.dataset.copiar);
      const status = button.closest('.codigo,.terminal')?.querySelector('[role="status"]');
      if (!code) return;
      try {
        if (!navigator.clipboard?.writeText) throw new Error('clipboard unavailable');
        await navigator.clipboard.writeText(code.textContent);
        if (status) status.textContent = 'Código copiado.';
        // Conservar hijos, icono y nombre accesible; el estado comunica el resultado.
      } catch {
        const range = document.createRange(); range.selectNodeContents(code);
        const selection = getSelection(); selection.removeAllRanges(); selection.addRange(range);
        if (status) status.textContent = 'Código seleccionado. Usa ⌘C o Ctrl+C para copiar.';
      }
    });
  });

  // Reproducir un sonido exige activación explícita; no se descargan MP3.
  if(!window.NotaAudio){
  const soundButton = document.querySelector('[data-sonido]');
  let soundEnabled = false, audio;
  soundButton?.addEventListener('click',() => {
    soundEnabled = !soundEnabled;
    soundButton.setAttribute('aria-pressed',String(soundEnabled));
    soundButton.textContent = soundEnabled ? 'Sonido activado' : 'Sonido apagado';
    if (!soundEnabled) audio?.suspend().catch(()=>{});
  });
  document.addEventListener('click',e => {
    if (!soundEnabled || !e.target.closest('button') || e.target.closest('[data-sonido],[data-canal-sonido]')) return;
    try {
      const Audio = window.AudioContext || window.webkitAudioContext;
      if (!Audio) return;
      audio ||= new Audio(); audio.resume().catch(()=>{});
      const oscillator = audio.createOscillator(), gain = audio.createGain(), t = audio.currentTime;
      oscillator.type = 'sine'; oscillator.frequency.setValueAtTime(680,t);
      oscillator.frequency.exponentialRampToValueAtTime(420,t+.04);
      gain.gain.setValueAtTime(.025,t); gain.gain.exponentialRampToValueAtTime(.0001,t+.055);
      oscillator.connect(gain); gain.connect(audio.destination);
      oscillator.start(t); oscillator.stop(t+.06);
      oscillator.onended = () => { oscillator.disconnect(); gain.disconnect(); };
    } catch {}
  });
  }
  const writingTarget=document.querySelector('[data-mano]')||document.querySelector('[data-escritura]');
  let writingObserver;
  document.querySelectorAll('[data-ver-escritura]').forEach(button=>{
    button.hidden=!writingTarget;
    button.addEventListener('click',()=>{
      if(!writingTarget)return;
      button.closest('details').open=false;
      const page=writingTarget.closest('.pagina');
      if(page?.hidden)document.querySelector('[data-ir="'+page.id+'"]').click();
      writingTarget.scrollIntoView({behavior:'instant',block:'center'});
      writingObserver?.disconnect();
      writingObserver=new IntersectionObserver(entries=>{
        if(entries[0].intersectionRatio>=.3){(window.NotaMano?.get(writingTarget)||window.NotaEscritura?.get(writingTarget))?.play();writingObserver.disconnect();}
      },{threshold:.3});
      writingObserver.observe(writingTarget.querySelector('.escritura-caja')||writingTarget);
    });
  });
  document.addEventListener('nota:pagina',()=>writingObserver?.disconnect());
  // Imprimir el contenido íntegro de los extractos incluso en motores sin ::details-content.
  let closedForPrint = [];
  addEventListener('beforeprint',() => { closedForPrint=[...document.querySelectorAll('.metodologia:not([open]),.extracto details:not([open]),[data-grafica] details:not([open]),[data-analitica] details:not([open]),[data-escena] details:not([open])')]; closedForPrint.forEach(e=>e.open=true); });
  addEventListener('afterprint',() => { closedForPrint.forEach(e=>e.open=false); closedForPrint=[]; });
})();
