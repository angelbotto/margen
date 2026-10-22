(async () => {
  const checks=[];
  const assert=(condition,message)=>{if(!condition)throw new Error(message);};
  const near=(actual,expected)=>assert(Math.abs(actual-expected)<1e-6,actual+' ≠ '+expected);
  async function test(name,fn){try{await fn();checks.push({name,ok:true});}catch(e){checks.push({name,ok:false,error:e.message});}}
  const make=(type,heads,rows,attrs={})=>{
    const f=document.createElement('figure');f.dataset.grafica=type;Object.assign(f.dataset,attrs);
    const details=document.createElement('details');details.open=true;
    const summary=document.createElement('summary');summary.textContent='Datos de prueba';details.append(summary);
    const table=document.createElement('table');table.createCaption().textContent='Prueba '+type;
    const h=table.createTHead().insertRow();heads.forEach(text=>{const c=document.createElement('th');c.textContent=text;h.append(c);});
    const body=table.createTBody();rows.forEach(row=>{const tr=body.insertRow();row.forEach((v,i)=>{const c=document.createElement(i?'td':'th');if(i){c.dataset.valor=v===null?'':v;c.textContent=v===null?'Sin dato':v;}else if(typeof v==='object'){Object.assign(c.dataset,v);c.textContent=v.label||'Intervalo';if(v.date){const time=document.createElement('time');time.dateTime=v.date;time.textContent=v.date;c.replaceChildren(time);}}else c.textContent=v;tr.append(c);});});
    details.append(table);f.append(details);document.querySelector('main').append(f);return f;
  };
  const dispose=f=>{NotaGraficas.get(f)?.destroy();f.remove();};
  await test('Cinco gráficas SVG, calor y dos escenas inicializados',()=>{
    // Cada figura dibuja un único SVG (el mapa de calor también; su tabla coloreada sigue como modo accesible).
    const figures=[...document.querySelectorAll('[data-grafica]')];
    assert(figures.length>=6&&figures.every(f=>f.querySelectorAll('.grafica-caja svg').length===1),'Número de gráficas');
    assert(document.querySelectorAll('.tabla-calor').length===1,'Mapa ausente');
    document.querySelectorAll('[data-escena]').forEach(e=>assert(NotaEscena.get(e)?.renderer,'WebGL no disponible'));
  });
  await test('Barras: extremos, cero y longitudes proporcionales',()=>{
    const f=document.querySelector('[data-grafica="barras"]'),svg=f.querySelector('svg'),bars=[...svg.querySelectorAll('[data-value]')];
    near(+svg.dataset.xMin,-10);near(+svg.dataset.xMax,60);
    const b60=bars.find(e=>e.dataset.value==='60'),b15=bars.find(e=>e.dataset.value==='15');near(+b60.getAttribute('width')/+b15.getAttribute('width'),4);
    const negative=bars.find(e=>e.dataset.value==='-10');near(+negative.getAttribute('x') + +negative.getAttribute('width'),+b60.getAttribute('x'));
  });
  await test('Temporal: distancia real, extremos y delta',()=>{
    const f=document.querySelector('[data-grafica="temporal"]'),p=[...f.querySelectorAll('[data-cx]')];
    near((+p[1].dataset.cx- +p[0].dataset.cx)/(+p[3].dataset.cx- +p[0].dataset.cx),2/12);
    assert(/\+30 · \+33,3\s?%/.test(f.querySelector('.grafica-variacion').textContent),'Delta incorrecto');
    assert(NotaGraficas.delta(5,0).includes('no definido'),'Porcentaje con base cero');
    assert(NotaGraficas.delta(null,2).includes('ausente'),'Ausencia interpretada como cero');
  });
  await test('Líneas: ausencia corta el segmento; no conecta observaciones a través del hueco',()=>{
    const path=document.querySelector('[data-grafica="lineas"] .grafica-trazo.serie-0');assert((path.getAttribute('d').match(/M/g)||[]).length===2,'Se interpola un dato ausente');
  });
  await test('Histograma: áreas proporcionales a frecuencia con intervalos desiguales',()=>{
    const bars=[...document.querySelectorAll('[data-grafica="distribucion"] rect[data-count]')];
    const ratios=bars.filter(b=>+b.dataset.count).map(b=>(+b.getAttribute('width') * +b.getAttribute('height'))/+b.dataset.count);
    ratios.forEach(r=>near(r,ratios[0]));assert(new Set(bars.map(b=>+b.dataset.hasta- +b.dataset.desde)).size>1,'Fixture sin intervalos desiguales');
  });
  await test('Calor: todos los niveles alcanzados; cero distinto de ausencia',()=>{
    const f=document.querySelector('[data-grafica="calor"]'),cells=[...f.querySelectorAll('td[data-nivel]')];
    assert(['0','1','2','3','4','ausente'].every(n=>cells.some(c=>c.dataset.nivel===n)),'Escala incompleta');
    assert(cells.find(c=>c.dataset.valor==='0').dataset.nivel==='0','Cero confundido');
  });
  await test('Vacío, cero constante, datos inválidos y reintento sin DOM parcial',()=>{
    for(const rows of [[],[['A',null]],[['A',0],['B',0]]]){const f=make('barras',['Grupo','Valor'],rows);assert(NotaGraficas.init(f)[0],'Caso válido rechazado');assert(!/NaN|Infinity/.test(f.innerHTML),'Coordenada no finita');dispose(f);}
    const f=make('calor',['Grupo','Valor'],[['A',200]],{umbrales:'0,30,60,90,120,150'});
    assert(NotaGraficas.init(f)[0]===null&&f.querySelector('details').open,'Fuera de escala debe quedar en tabla');
    f.querySelector('[data-valor]').dataset.valor='30';assert(NotaGraficas.init(f)[0]&&!f.querySelector('[data-error-grafica]'),'No se recupera');dispose(f);
  });
  await test('Fechas inválidas rechazadas; fechas cercanas no superponen sus rótulos',()=>{
    let f=make('temporal',['Día','Valor'],[[{date:'2026-02-30'},4]]);assert(NotaGraficas.init(f)[0]===null,'Fecha inexistente aceptada');dispose(f);
    f=make('temporal',['Día','Valor'],[[{date:'2026-01-01'},1],[{date:'2026-01-02'},2],[{date:'2026-12-31'},3]]);
    NotaGraficas.init(f);const texts=[...f.querySelectorAll('svg text')].filter(t=>t.textContent.trim()).map(t=>t.getBoundingClientRect());
    assert(texts.length&&texts.every((a,i)=>texts.every((b,j)=>i>=j||Math.min(a.right,b.right)-Math.max(a.left,b.left)<=1||Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)<=1)),'Fechas cercanas sin separación');dispose(f);
  });
  await test('Inicialización idempotente y destroy recupera datos',()=>{
    const f=make('barras',['Grupo','Valor'],[['A',4],['B',9]]),before=f.innerHTML;
    const a=NotaGraficas.init(f)[0],b=NotaGraficas.init(f)[0];assert(a===b,'Instancia duplicada');a.destroy();assert(f.innerHTML===before,'DOM no restaurado');f.remove();
  });
  await test('Tabla: ordenar, ausencias al final, totales fijos y reversión',()=>{
    const t=document.querySelector('table[data-tabla="ordenable"]')||document.querySelector('.tabla-totales'),body=t.tBodies[0];
    const initial=[...body.rows],foot=t.tFoot.textContent,button=t.querySelector('[data-ordenar="numero"]');
    const c=body.insertRow();c.insertCell().textContent='Ausente';c.insertCell().dataset.valor='';while(c.cells.length<t.tHead.rows[0].cells.length)c.insertCell();
    button.click();assert(body.rows[body.rows.length-1]===c,'Ausencia ascendente');button.click();assert(body.rows[body.rows.length-1]===c,'Ausencia descendente');
    assert(t.tFoot.textContent===foot,'Total movido');c.remove();NotaTablas.get(t).destroy();assert([...body.rows].every((r,i)=>r===initial[i]),'Orden inicial perdido');NotaTablas.init(t);
  });
  await test('Sparklines: misma escala para todas las filas y valores completos',()=>{
    const t=document.querySelector('table[data-min][data-max]'),cells=[...t.querySelectorAll('[data-sparkline]')];
    assert(cells.every(c=>c.querySelector('svg')&&c.querySelector('.sparkline-datos')),'Falta dibujo o serie escrita');
    const min=+t.dataset.min,max=+t.dataset.max;
    cells.forEach(c=>{const raw=[...c.querySelectorAll('[data-valor]')].map(e=>e.dataset.valor).filter(v=>v!=='');near(+c.querySelector('circle').getAttribute('cy'),40-(+raw.at(-1)-min)/(max-min)*36);});
  });
  await test('Three: dominios reales y alturas relativas; sin inflación del tamaño por perspectiva',()=>{
    const xyz=NotaEscena.get(document.querySelector('[data-escena="xyz"]'));assert(xyz.camera.isOrthographicCamera,'Perspectiva no prevista');
    assert(JSON.stringify(xyz.domains)==='[[10,50],[80,170],[100,210]]','Dominios XYZ');
    xyz.items.forEach((mesh,i)=>xyz.model.data[i].values.forEach((v,a)=>near(mesh.position.getComponent(a),-1+2*(v-xyz.domains[a][0])/(xyz.domains[a][1]-xyz.domains[a][0]))));
    const e=NotaEscena.get(document.querySelector('[data-escena="etapas"]'));near(e.items[2].geometry.parameters.height/e.items[0].geometry.parameters.height,6);
    assert(xyz.labels.every(l=>l.texture.colorSpace===THREE.SRGBColorSpace),'Texto canvas sin espacio sRGB');
  });
  await test('Three: pérdida de contexto cancela RAF y conserva tabla; recuperación y destroy',async()=>{
    const f=document.querySelector('[data-escena="xyz"]'),e=NotaEscena.get(f);e.select(1);assert(e.status.textContent.includes('95'),'Selección sin valores');
    e.canvas.dispatchEvent(new Event('webglcontextlost',{cancelable:true}));assert(e.lost&&e.frame===0&&!e.error.hidden&&f.querySelector('table'),'No suspende');
    e.canvas.dispatchEvent(new Event('webglcontextrestored'));await Promise.resolve();assert(!e.lost,'No recupera');e.select(null);
    const table=f.querySelector('table').outerHTML;e.destroy();e.destroy();assert(!f.querySelector('canvas')&&f.querySelector('table').outerHTML===table&&!NotaEscena.get(f),'No libera/restaura');NotaEscena.init(f);
  });
  await test('Three ausente: tabla permanente e información accesible',()=>{
    const original=window.THREE,source=document.querySelector('[data-escena="etapas"]'),f=document.createElement('figure');f.dataset.escena='etapas';f.append(source.querySelector('.tabla-caja').cloneNode(true));document.querySelector('main').append(f);
    try{window.THREE=undefined;const e=NotaEscena.init(f)[0];assert(e&&!e.renderer&&!e.error.hidden&&f.querySelector('table'),'Fallback ausente');e.select(0);assert(e.status.textContent.includes('20'),'Selección sin WebGL falla');e.destroy();}finally{window.THREE=original;f.remove();}
  });
  await test('Audio: apagado y sin contexto; foco, scroll y clic sintético no lo activan',()=>{
    const f=document.querySelector('[data-canal-sonido]'),e=NotaSonido.get(f);assert(!e.enabled&&!e.audio,'Audio activo al cargar');
    f.querySelector('[data-audio-activar]').focus();dispatchEvent(new Event('scroll'));f.querySelector('[data-audio-activar]').click();f.querySelector('[data-audio]').click();assert(!e.enabled&&!e.audio&&e.plays===0,'Activación sin gesto real');
  });
  return {checks,passed:checks.filter(c=>c.ok).length,failed:checks.filter(c=>!c.ok).length};
})()
