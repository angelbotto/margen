(async () => {
  const checks=[];
  const assert=(yes,message)=>{if(!yes)throw new Error(message);};
  const close=(x,y)=>assert(Math.abs(x-y)<1e-5,`${x} ≠ ${y}`);
  const test=async(name,fn)=>{try{await fn();checks.push({name,ok:true});}catch(e){checks.push({name,ok:false,error:e.message});}};
  function sample(key) {
    const template=document.createElement('template');template.innerHTML=document.getElementById('receta-fuente-'+key).textContent;
    const root=template.content.firstElementChild;root.removeAttribute('id');document.querySelector('main').append(root);return root;
  }
  async function fixture(key,fn) {const root=sample(key);try{await fn(root);}finally{NotaReportes.get(root)?.destroy();NotaVisores.get(root)?.destroy();root.remove();}}
  await test('71 fuentes copiables sin errores de inicialización',()=>{
    assert(document.querySelectorAll('.catalogo-indice a').length===71,'Índice incompleto');
    assert(document.querySelectorAll('.receta-copia code').length===71,'Código de recetas incompleto');
    assert(!document.querySelector('[data-error-reporte],[data-error-visor]'),'Error visible');
  });
  await test('Apariencia sincroniza radios y almacenamiento; Sistema retira data-theme',()=>{
    const all=[...document.querySelectorAll('[data-elegir-tema]')];
    for(const name of ['light','dark','sea','system']) {
      const chosen=all.find(e=>e.value===name);chosen.checked=true;chosen.dispatchEvent(new Event('change',{bubbles:true}));
      assert((document.documentElement.dataset.theme||'system')===name,'Tema incorrecto');
      assert(all.filter(e=>e.checked).every(e=>e.value===name),'Radios no sincronizados');
    }
  });
  await test('Lectura cómoda alterna 18/16px sin alterar el ancho de la columna',()=>{
    const before=document.querySelector('.seccion p').getBoundingClientRect().width;
    const button=document.querySelector('[data-comodidad]');if(document.documentElement.hasAttribute('data-lectura-comoda'))button.click();
    close(parseFloat(getComputedStyle(document.body).fontSize),16);button.click();
    close(parseFloat(getComputedStyle(document.body).fontSize),18);close(document.querySelector('.seccion p').getBoundingClientRect().width,before);
    assert([...document.querySelectorAll('[data-comodidad]')].every(b=>b.getAttribute('aria-pressed')==='true'),'Botones no sincronizados');button.click();
  });
  await test('Cascada: suma, dominio y longitudes desde la misma escala',()=>{
    const f=document.querySelector('[data-reporte="cascada"]'),s=f.querySelector('svg'),bars=[...s.querySelectorAll('[data-from]')];
    // Dominio redondeado 1-2-5 que contiene 0 y 120; ancho medido: la escala sale de dos ticks del propio eje.
    close(+s.dataset.xMin,0);assert(+s.dataset.xMax>=120,'Dominio corto');close(+s.querySelector('[data-total]').dataset.total,95);
    const t=[...s.querySelectorAll('[data-tick-x]')].map(l=>[+l.dataset.tickX,+l.getAttribute('x1')]),unit=(t[1][1]-t[0][1])/(t[1][0]-t[0][0]);
    bars.forEach(b=>close(+b.getAttribute('width'),Math.abs(+b.dataset.to- +b.dataset.from)*unit));
    assert(f.querySelector('tfoot').textContent.includes('95'),'Total incorrecto');
  });
  await test('Cascada negativa y cero: ningún valor fuera del dominio ni coordenadas NaN',()=>fixture('cascada',f=>{
    [...f.querySelectorAll('[data-valor]')].forEach((c,i)=>c.dataset.valor=[-10,0,3,-1][i]);
    assert(NotaReportes.init(f)[0],'No inicializa');const s=f.querySelector('svg');close(+s.dataset.xMin,-10);close(+s.dataset.xMax,0);
    close(+s.querySelector('[data-total]').dataset.total,-8);assert(!/NaN|Infinity/.test(s.outerHTML),'Geometría inválida');
  }));
  await test('Cascada minúscula conserva etiquetas distintas de cero',()=>fixture('cascada',f=>{
    [...f.querySelectorAll('[data-valor]')].forEach(c=>c.dataset.valor='0.00000001');NotaReportes.init(f);
    assert(f.querySelector('svg').textContent.includes('E'),'Rótulos minúsculos redondeados a cero');
  }));
  await test('Cascada con nombres extensos reserva altura para cada rótulo',()=>fixture('cascada',f=>{
    [...f.querySelectorAll('tbody th')].forEach(c=>c.textContent='Revisión de las solicitudes pendientes y confirmadas en cada área de la organización '.repeat(3));
    NotaReportes.init(f);const s=f.querySelector('svg'),labels=[...s.querySelectorAll('text')].filter(t=>t.querySelector('tspan'));
    const bars=[...s.querySelectorAll('[data-from]')];assert(labels.length===4,'Rótulos ausentes');
    const hit=(a,b)=>Math.min(a.x+a.width,b.x+b.width)-Math.max(a.x,b.x)>1&&Math.min(a.y+a.height,b.y+b.height)-Math.max(a.y,b.y)>1;
    labels.forEach((t,i)=>{const b=t.getBBox();assert(![...s.querySelectorAll('[data-from],[data-total]')].some(r=>hit(b,r.getBBox())),'Rótulo invade el eje');assert(b.y+b.height<(i+1<bars.length?+bars[i+1].getAttribute('y'):+s.querySelector('[data-total]').getAttribute('y')),'Rótulo invade la siguiente fila');});
  }));
  await test('Reporte inválido conserva tabla; reintento limpia error; destroy restaura DOM',()=>fixture('cascada',f=>{
    const cell=f.querySelector('[data-valor]');cell.dataset.valor='invalid';const original=f.querySelector('table').outerHTML;
    assert(NotaReportes.init(f)[0]===null,'Aceptó inválido');assert(f.querySelector('table').outerHTML===original,'Mutación parcial');
    cell.dataset.valor='120';const before=f.innerHTML.replace(f.querySelector('[data-error-reporte]').outerHTML,'');
    const a=NotaReportes.init(f)[0];assert(a===NotaReportes.init(f)[0],'Instancia duplicada');a.destroy();a.destroy();assert(f.innerHTML===before,'No restauró HTML');
  }));
  await test('Múltiples: dominio común y ausencia corta la línea',()=>{
    const panels=[...document.querySelectorAll('[data-reporte="multiples"] svg')];
    panels.forEach(s=>{close(+s.dataset.yMin,0);close(+s.dataset.yMax,80);});
    assert((panels[2].querySelector('path').getAttribute('d').match(/M/g)||[]).length===2,'Conecta datos ausentes');
  });
  await test('Conciliación calcula diferencias y totales; ausencia no es cero',()=>fixture('conciliacion',f=>{
    f.querySelector('tbody').rows[1].cells[2].dataset.valor='';NotaReportes.init(f);
    const footer=f.querySelector('tfoot');assert(footer.textContent.includes('Incompleto')&&footer.textContent.includes('Sin comparación'),'Total parcial aparenta ser completo');
    assert(f.querySelector('tbody').rows[1].cells[3].textContent==='Sin dato','Ausencia convertida a cero');
  }));
  await test('Conciliación rechaza negativos y decimales de conteo',()=>fixture('conciliacion',f=>{
    f.querySelector('[data-valor]').dataset.valor='-1';assert(!NotaReportes.init(f)[0],'Acepta negativo');
    f.querySelector('[data-valor]').dataset.valor='1.5';assert(!NotaReportes.init(f)[0],'Acepta fracción');
  }));
  await test('Escenario: cero, empeoramiento, vacío, límites y reset',()=>fixture('escenario',async f=>{
    NotaReportes.init(f);const form=f.querySelector('form'),out=f.querySelector('output');
    const set=(name,value)=>{form.elements.namedItem(name).value=value;form.dispatchEvent(new Event('input',{bubbles:true}));};
    assert(out.textContent==='60 h/mes liberadas','Resultado base incorrecto');set('volumen','0');assert(out.textContent.startsWith('0 '),'Cero incorrecto');
    set('volumen','1200');set('despues','10');assert(out.textContent==='40 h/mes adicionales','Dirección incorrecta');
    set('antes','');assert(out.textContent.includes('Completa'),'Vacío conserva resultado');set('antes','2000');assert(out.textContent.includes('Completa'),'Límite no aplicado');
    form.reset();await Promise.resolve();assert(out.textContent==='60 h/mes liberadas','Reset no recalcula');
  }));
  await test('Globo narrado empieza pausado; pasos cambian selección y límites',()=>{
    const f=document.querySelector('[data-reporte="recorrido"]'),r=NotaReportes.get(f);
    assert(r.globe.paused&&r.globe.frame===0,'Giro inicial activo');
    assert(f.querySelector('[data-paso="prev"]').disabled,'Prev inicial activo');
    f.querySelector('[data-paso="next"]').click();assert(r.globe.selected==='idea-mad-hnd','Ruta no cambia');
    f.querySelector('[data-paso="next"]').click();assert(f.querySelector('[data-paso="next"]').disabled,'Next final activo');
    f.querySelector('[data-paso="prev"]').click();f.querySelector('[data-paso="prev"]').click();
    f.querySelector('[data-route="idea-mad-hnd"]').click();assert(f.querySelector('[data-recorrido-estado]').textContent.startsWith('Etapa 2'),'Lista y relato no sincronizados');
    f.querySelector('[data-paso="prev"]').click();
  });
  await test('Recorrido sin Three conserva pasos y lista; destroy libera el contenedor',()=>fixture('recorrido',f=>{
    const saved=window.THREE;try{window.THREE=undefined;const r=NotaReportes.init(f)[0];assert(r&&!r.globe.renderer,'Fallback incorrecto');assert(f.querySelectorAll('[data-ruta]').length===3,'Relato ausente');r.destroy();assert(!f.querySelector('canvas'),'Canvas no retirado');}finally{window.THREE=saved;}
  }));
  await test('Visor: cada tamaño es ancho real; auto conserva el espacio disponible',()=>{
    const v=NotaVisores.get(document.querySelector('[data-visor]'));
    [320,390,768,1024].forEach(n=>{v.setWidth(String(n));close(v.host.getBoundingClientRect().width,n);});
    v.setWidth('auto');assert(v.host.getBoundingClientRect().width<=v.box.clientWidth,'Auto desborda');v.setWidth('390');
  });
  await test('Visor: consultas de contenedor, navegación y reset',()=>{
    const v=NotaVisores.get(document.querySelector('[data-visor]'));
    v.setWidth('320');const page=v.shadow.querySelector('[data-demo-pagina="vacio"]');assert(getComputedStyle(page).display==='block','Diseño móvil no aplica');
    v.setWidth('768');assert(getComputedStyle(page).display==='grid','Consulta de contenedor no responde');
    v.shadow.querySelector('[data-demo-ir="revision"]').click();assert(!v.shadow.querySelector('[data-demo-pagina="revision"]').hidden,'No cambia estado');
    v.reset();assert(v.shadow.querySelector('[data-demo-pagina="revision"]').hidden,'Reset mantiene estado anterior');v.setWidth('390');
  });
  await test('Visor destroy restaura alternativa y reinicialización no duplica lienzos',()=>fixture('visor',f=>{
    const a=NotaVisores.init(f)[0];assert(a===NotaVisores.init(f)[0],'Instancia duplicada');
    a.destroy();assert(!f.querySelector('.visor-lienzo'),'Lienzo sobrevivió');assert(getComputedStyle(f.querySelector('.visor-fuente')).display!=='none','Alternativa oculta');
    NotaVisores.init(f);assert(f.querySelectorAll('.visor-lienzo').length===1,'Lienzo duplicado');
  }));
  await test('Visor rechaza manejadores inline sin modificar su muestra',()=>fixture('visor',f=>{
    f.querySelector('template').content.querySelector('button').setAttribute('onclick','void 0');
    assert(NotaVisores.init(f)[0]===null&&!f.querySelector('.visor-lienzo'),'HTML con manejadores aceptado');
    assert(getComputedStyle(f.querySelector('.visor-fuente')).display!=='none','Sin alternativa');
  }));
  await test('Búsqueda tolera acentos y no oculta contenido del documento',()=>{
    const input=document.querySelector('[data-buscador-recetas] input'),items=[...document.querySelectorAll('.catalogo-indice li')];
    input.value='ARTICULO';input.dispatchEvent(new Event('input'));assert(items.some(e=>!e.hidden&&e.textContent.includes('artículo')),'No normaliza acento');
    assert(document.getElementById('cascada-ejemplo').getClientRects().length,'Ocultó piezas');
    input.value='inexistente-xyz';input.dispatchEvent(new Event('input'));assert(items.every(e=>e.hidden),'Sin resultados incorrecto');
    input.value='';input.dispatchEvent(new Event('input'));assert(items.every(e=>!e.hidden),'No restaura lista');
  });
  await test('Método se abre al imprimir y recupera su estado',()=>{
    const d=document.querySelector('.metodologia');d.open=false;dispatchEvent(new Event('beforeprint'));assert(d.open,'Método no visible en impresión');dispatchEvent(new Event('afterprint'));assert(!d.open,'Estado no restaurado');
  });
  await test('Referencias y retorno apuntan a elementos existentes',()=>{
    [...document.querySelectorAll('#referencias-ejemplo a')].forEach(a=>assert(document.getElementById(a.hash.slice(1)),'Referencia rota'));
  });
  return {checks,passed:checks.filter(c=>c.ok).length,failed:checks.filter(c=>!c.ok).length};
})()
