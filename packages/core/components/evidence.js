/* Margen · evidencia editorial. SVG local al ancho real, tablas como fuente; sin RAF ni red. Requiere chart-core.js. */
(()=>{'use strict';
 const G=window.MargenGraficas,instances=new WeakMap(),NS='http://www.w3.org/2000/svg',DAY=86400000;
 const fmt={format:v=>G?G.format(v,'auto',{lang:G.lang(document.documentElement)}):new Intl.NumberFormat('es-CO',{maximumSignificantDigits:8}).format(v)};
 const make=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;};
 const svg=(tag,attrs={},text)=>{const e=document.createElementNS(NS,tag);for(const [k,v] of Object.entries(attrs))if(v!==undefined)e.setAttribute(k,String(v));if(text!==undefined)e.textContent=text;return e;};
 const number=(cell)=>{const raw=cell?.dataset.valor??cell?.textContent?.trim();if(raw===undefined||raw===''||!Number.isFinite(Number(raw))||Math.abs(Number(raw))>1e12)throw Error('Cada valor requiere un número finito de hasta 10¹².');return Number(raw);};
 const label=cell=>{const s=cell?.textContent.trim();if(!s||s.length>100)throw Error('Usa nombres de 1 a 100 caracteres.');return s;};
 const day=cell=>{const s=cell?.querySelector('time')?.dateTime||cell?.textContent.trim();if(!/^\d{4}-\d{2}-\d{2}$/.test(s||''))throw Error('Las fechas deben ser YYYY-MM-DD.');const t=Date.parse(s+'T00:00:00Z');if(!Number.isFinite(t)||new Date(t).toISOString().slice(0,10)!==s)throw Error('Fecha inexistente.');return t;};
 const date=t=>new Date(t).toISOString().slice(0,10),pct=v=>G?G.format(v,'pct1',{lang:G.lang(document.documentElement)}):fmt.format(v*100)+' %',amount=(v,u)=>fmt.format(v)+(u?' '+u:'');
 function rows(root,min,max,columns){if(root.querySelectorAll('table[data-evidencia-datos]').length!==1)throw Error('Se requiere una sola tabla fuente.');const rs=[...root.querySelectorAll('table[data-evidencia-datos] > tbody > tr')];if(rs.length<min||rs.length>max)throw Error(`Se requieren ${min}–${max} filas.`);return rs.map(r=>{const cells=[...r.cells];if(columns&&cells.length!==columns)throw Error(`Se requieren ${columns} columnas por fila.`);return cells;});}
 function wrap(s,text,x,y,width,font,lines=3,attrs={}){const parts=G.wrap(text,width,font,lines),t=svg('text',{x,y,...attrs});parts.forEach((line,i)=>t.append(svg('tspan',{x,dy:i?15:0},line)));s.append(t);return parts.length;}
 // Eje horizontal con ticks 1-2-5 (o de calendario) que no se pisan ni salen del SVG.
 function axis(ctx,s,lo,hi,x0,x1,y,{unit='',dates=false,zero=false}={}){
  const count=Math.max(2,Math.min(8,Math.floor((x1-x0)/80)));let ticks,f,scale;
  if(dates){const t=G.timeTicks(lo,hi,count);scale=G.linear([lo,hi===lo?lo+DAY:hi],[x0,x1]);ticks=t.ticks;f=v=>G.format(v,t.spec,{lang:ctx.lang});}
  else{const n=zero?G.niceZero([lo,hi],count):G.nice(lo,hi,count);scale=G.linear([n.min,n.max],[x0,x1]);ticks=n.ticks;f=G.tickFormat(n.ticks,ctx.spec,{lang:ctx.lang});ctx.domain=[n.min,n.max];}
  s.append(svg('line',{x1:x0,y1:y,x2:x1,y2:y,class:'ev-eje'}));
  G.spacedTicks(ticks,scale,f,ctx.font,12,+s.getAttribute('width')).forEach(v=>{const xx=scale(v);s.append(svg('line',{x1:xx,y1:y,x2:xx,y2:y-6,class:'ev-eje'}),G.edgeText(s,xx,y+18,f(v),{},ctx.font));});
  if(unit)s.append(svg('text',{x:x0,y:y+36,class:'mg-texto-suave'},G.fit(unit,x1-x0,ctx.font,1)));
  return scale;
 }
 // Dibujo responsivo: draw(s,width) devuelve la altura (y opcionalmente un ancho mayor para desplazar).
 function mount(ctx,description,draw){
  ctx.watch=G.responsive(ctx.view,width=>{
   ctx.marks?.destroy();
   const s=svg('svg',{class:'mg-svg',width,height:10,viewBox:`0 0 ${width} 10`,'aria-label':description});s.append(svg('title',{},description));ctx.view.replaceChildren(s);ctx.svg=s;
   ctx.font=G.fontOf(s);ctx.fill=G.patterns(s,G.patternsEnabled(ctx.root));
   const r=draw(s,width),w=r.width||width;
   s.setAttribute('width',w);s.setAttribute('height',r.height);s.setAttribute('viewBox',`0 0 ${w} ${r.height}`);
   const scroll=w>width;s.classList.toggle('mg-desplazable',scroll);ctx.note.hidden=!scroll;
   if(scroll){ctx.view.tabIndex=0;ctx.view.setAttribute('role','region');ctx.view.setAttribute('aria-label',ctx.title+', desplazable horizontalmente');ctx.note.textContent='Desliza horizontalmente para ver toda la figura; la tabla tiene los mismos datos.';}
   else{ctx.view.removeAttribute('tabindex');ctx.view.removeAttribute('role');ctx.view.removeAttribute('aria-label');}
   const items=[...s.querySelectorAll('[data-ev-row]')].sort((a,b)=>a.dataset.evRow-b.dataset.evRow);
   ctx.marks=G.marks(ctx.root,s,{items,label:ctx.title,describe:k=>[ctx.descriptions[+items[k].dataset.evRow]],onSelect:k=>{if(k!==null)ctx.choose(+items[k].dataset.evRow);}});
   if(ctx.selected!==undefined)ctx.view.querySelectorAll('[data-ev-row]').forEach(n=>n.classList.toggle('ev-elegido',Number(n.dataset.evRow)===ctx.selected));
  });
  ctx.clean.push(()=>{ctx.watch.disconnect();ctx.marks?.destroy();});
 }
 function mark(s,node,index){node.classList.add('ev-marca');node.dataset.evRow=index;s.append(node);return node;}
 function selection(ctx,labels,descriptions,custom){ctx.descriptions=descriptions;const l=make('label','Consultar dato '),sel=make('select');sel.setAttribute('aria-label','Consultar dato de '+ctx.title);labels.forEach((name,i)=>{const o=make('option',name);o.value=i;sel.append(o);});l.append(sel);ctx.tools.append(l);ctx.choose=i=>{i=Math.max(0,Math.min(labels.length-1,Number(i)||0));sel.value=i;ctx.selected=i;ctx.detail.textContent=descriptions[i];ctx.view.querySelectorAll('[data-ev-row]').forEach(n=>n.classList.toggle('ev-elegido',Number(n.dataset.evRow)===i));custom?.(i);};ctx.on(sel,'change',()=>ctx.choose(sel.value));ctx.choose(0);return sel;}
 const labelColumn=(ctx,names,width,share=.32)=>Math.min(Math.round(width*share),Math.ceil(Math.max(...names.map(n=>G.textWidth(n,ctx.font))))+16);
 function sankey(ctx){
  const rs=rows(ctx.root,1,24,3),data=rs.map(c=>({a:label(c[0]),b:label(c[1]),v:number(c[2])}));if(data.some(d=>d.v<0))throw Error('Sankey requiere magnitudes no negativas.');
  const total=data.reduce((a,d)=>a+d.v,0);if(total<=0||total>1e12)throw Error('El total debe ser positivo y no superar 10¹².');
  const left=[...new Set(data.map(d=>d.a))],right=[...new Set(data.map(d=>d.b))];if(Math.max(left.length,right.length)>8)throw Error('Máximo ocho nodos por columna.');
  selection(ctx,data.map(d=>d.a+' → '+d.b),data.map(d=>`${d.a} → ${d.b}: ${amount(d.v,ctx.unit)}. ${pct(d.v/total)} del total ${amount(total,ctx.unit)}.`));
  mount(ctx,ctx.title+'; grosor proporcional; '+amount(total,ctx.unit)+' en total.',(s,width)=>{
   const amounts=[...left.map(n=>data.filter(d=>d.a===n)),...right.map(n=>data.filter(d=>d.b===n))].map(list=>amount(list.reduce((a,d)=>a+d.v,0),ctx.unit));
   const lw=Math.max(80,Math.min(Math.round(width*.3),labelColumn(ctx,[...left,...right,...amounts],width,.3))),xa=lw,xb=width-lw-14;
   const lines=name=>G.wrap(name,lw-12,ctx.font,3).length,n=Math.max(left.length,right.length);
   const gap=Math.max(40,...[...left,...right].map(name=>lines(name)*15+24)),h=Math.max(260,n*90),k=(h-(n-1)*gap)/total;
   const layout=(names,key)=>{let y=24;return new Map(names.map(name=>{const v=data.filter(d=>d[key]===name).reduce((a,d)=>a+d.v,0),node={y,v,offset:0};y+=v*k+gap;return [name,node];}));},a=layout(left,'a'),b=layout(right,'b');
   data.forEach((d,i)=>{const from=a.get(d.a),to=b.get(d.b),thick=d.v*k,y1=from.y+from.offset+thick/2,y2=to.y+to.offset+thick/2,mid=(xa+14+xb)/2;from.offset+=thick;to.offset+=thick;if(d.v)mark(s,svg('path',{d:`M${xa+14} ${y1} C${mid} ${y1} ${mid} ${y2} ${xb} ${y2}`,class:'ev-flujo ev-color-'+left.indexOf(d.a)%8,style:'stroke:'+G.color(left.indexOf(d.a)),'stroke-width':Math.max(1,thick),fill:'none'}),i);});
   for(const [map,x,tx,anchor] of [[a,xa,xa-8,'end'],[b,xb,xb+22,'start']])for(const [name,d] of map){s.append(svg('rect',{x,y:d.y,width:14,height:Math.max(1,d.v*k),class:'ev-nodo'}));const ln=wrap(s,name,tx,d.y+10,lw-12,ctx.font,3,{'text-anchor':anchor,class:'mg-texto-fuerte'});s.append(svg('text',{x:tx,y:d.y+12+ln*15,'text-anchor':anchor},G.fit(amount(d.v,ctx.unit),lw-12,ctx.font,1)));}
   ctx.model={total,scale:k,links:data};
   return {height:24+Math.max(...[...a.values(),...b.values()].map(d=>d.y+d.v*k))+gap};
  });
 }
 function cohorts(ctx){
  const rs=rows(ctx.root,1,20),cols=rs[0].length-2;if(cols<1||cols>12||rs.some(c=>c.length!==cols+2))throw Error('Cohortes requiere nombre, base y 1–12 períodos iguales.');
  const heads=[...ctx.root.querySelectorAll('table[data-evidencia-datos] thead th')].slice(2).map(label);if(heads.length!==cols||heads.some(h=>h.length>24))throw Error('Cada período necesita cabecera.');
  const data=rs.map(c=>{const base=number(c[1]);if(!Number.isInteger(base)||base<=0)throw Error('La base de cohorte debe ser un entero positivo.');let missing=false;const values=c.slice(2).map(v=>{if(v.dataset.estado==='pendiente'){missing=true;return null;}if(missing)throw Error('Los períodos pendientes deben quedar al final de la fila.');const x=number(v);if(!Number.isInteger(x)||x<0||x>base)throw Error('Recuentos de cohorte entre cero y su base.');return x;});return {name:label(c[0]),base,values};});
  const labels=[],descriptions=[];
  data.forEach(d=>d.values.forEach((v,c)=>{labels.push(d.name+' · '+heads[c]);descriptions.push(v===null?`${d.name}, ${heads[c]}: pendiente de observar; base ${d.base}.`:`${d.name}, ${heads[c]}: ${v} de ${d.base}; ${pct(v/d.base)}.`);}));
  const legend=make('p','Escala: 0–<20 %, 20–<40 %, 40–<60 %, 60–<80 %, 80–100 %. Contorno discontinuo: pendiente.');legend.className='evidencia-leyenda';ctx.view.after(legend);ctx.clean.push(()=>legend.remove());
  selection(ctx,labels,descriptions);
  mount(ctx,ctx.title+'; porcentaje respecto a la base de cada cohorte. Pendiente no equivale a cero.',(s,width)=>{
   const lw=Math.max(90,Math.min(Math.round(width*.28),labelColumn(ctx,data.map(d=>d.name),width,.28)));
   const need=Math.ceil(Math.max(G.textWidth('sin observar',ctx.font),...data.flatMap(d=>d.values.map(v=>v===null?0:G.textWidth(`${v} / ${d.base}`,ctx.font)))))+14;
   const cw=Math.max(need,Math.min(120,(width-lw)/cols)),rh=Math.max(52,...data.map(d=>G.wrap(d.name,lw-12,ctx.font,2).length*15+32)),total=Math.ceil(lw+cols*cw);
   heads.forEach((x,i)=>s.append(svg('text',{x:lw+i*cw+(cw-6)/2,y:18,'text-anchor':'middle'},G.fit(x,cw-6,ctx.font,1))));
   let index=0;
   data.forEach((d,r)=>{const y0=28+r*rh,ln=wrap(s,d.name,0,y0+16,lw-12,ctx.font,2,{class:'mg-texto-fuerte'});s.append(svg('text',{x:0,y:y0+18+ln*15,class:'mg-texto-suave'},'Base '+fmt.format(d.base)));
    d.values.forEach((v,c)=>{const x=lw+c*cw,ratio=v===null?null:v/d.base,g=svg('g');g.append(svg('rect',{x,y:y0,width:cw-6,height:rh-6,class:v===null?'ev-ausente':'ev-calor ev-nivel-'+Math.min(4,Math.floor(ratio*5))}),svg('text',{x:x+(cw-6)/2,y:y0+(rh-6)/2-2,'text-anchor':'middle',class:'ev-calor-texto'},v===null?'Pendiente':pct(ratio)),svg('text',{x:x+(cw-6)/2,y:y0+(rh-6)/2+14,'text-anchor':'middle',class:'ev-calor-texto'},v===null?'sin observar':`${v} / ${d.base}`));mark(s,g,index++);});});
   ctx.model={data,periods:heads};
   return {height:28+data.length*rh+4,width:Math.max(width,total)};
  });
 }
 function sensitivity(ctx){
  const baseCell=ctx.root.querySelector('[data-evidencia-base]');if(!baseCell)throw Error('Falta el resultado base visible.');const base=number(baseCell),rs=rows(ctx.root,1,16,5);
  const data=rs.map(c=>({name:label(c[0]),low:label(c[1]),a:number(c[2]),high:label(c[3]),b:number(c[4])}));
  data.sort((a,b)=>Math.abs(b.b-b.a)-Math.abs(a.b-a.a));
  const descriptions=data.map(v=>`${v.name}. A (${v.low}): ${amount(v.a,ctx.unit)}, cambio ${amount(v.a-base,ctx.unit)}. B (${v.high}): ${amount(v.b,ctx.unit)}, cambio ${amount(v.b-base,ctx.unit)}. Base ${amount(base,ctx.unit)}. No combina supuestos.`);
  selection(ctx,data.map(d=>d.name),descriptions);const reset=make('button','Restablecer consulta');reset.type='button';ctx.on(reset,'click',()=>ctx.choose(0));ctx.tools.append(reset);
  mount(ctx,ctx.title+'; un supuesto cambia a la vez; resultado base '+amount(base,ctx.unit),(s,width)=>{
   const narrow=width<480,lw=narrow?0:labelColumn(ctx,data.map(d=>d.name),width),x0=lw+8,x1=width-12,rh=narrow?72:58,h=48+data.length*rh;
   const all=[base,...data.flatMap(x=>[x.a,x.b])],pad=(Math.max(...all)-Math.min(...all))*.05||1,x=axis(ctx,s,Math.min(...all)-pad,Math.max(...all)+pad,x0,x1,h,{unit:ctx.unit});
   s.append(svg('line',{x1:x(base),x2:x(base),y1:30,y2:h,class:'ev-base'}),svg('text',{x:0,y:14},G.fit('Base: '+amount(base,ctx.unit)+' · ○ A / ■ B',width,ctx.font,1)));
   data.forEach((v,i)=>{const y=48+i*rh+(narrow?24:12);if(narrow)s.append(svg('text',{x:0,y:y-14,class:'mg-texto-fuerte'},G.fit(v.name,width,ctx.font,1)));else wrap(s,v.name,lw,y+4,lw-8,ctx.font,2,{'text-anchor':'end',class:'mg-texto-fuerte'});
    const g=svg('g');g.append(svg('line',{x1:x(v.a),x2:x(v.b),y1:y,y2:y,class:'ev-intervalo'}),svg('circle',{cx:x(v.a),cy:y,r:6,class:'ev-punto'}),svg('rect',{x:x(v.b)-6,y:y-6,width:12,height:12,class:'ev-punto ev-color-1'}));mark(s,g,i);
    s.append(svg('text',{x:x0,y:y+22,class:'mg-texto-suave'},G.fit('A: '+fmt.format(v.a)+' · B: '+fmt.format(v.b),x1-x0,ctx.font,1)));});
   ctx.model={base,domain:ctx.domain,data};return {height:h+44};
  });
 }
 function gantt(ctx){
  const rs=rows(ctx.root,1,24,7),data=rs.map(c=>({id:label(c[0]),name:label(c[1]),start:day(c[2]),end:day(c[3]),owner:label(c[4]),state:label(c[5]),deps:c[6].textContent.trim()==='—'?[]:c[6].textContent.trim().split(/\s*,\s*/)}));
  const map=new Map(data.map(d=>[d.id,d]));if(map.size!==data.length||data.some(d=>!/^[-\w]{1,12}$/.test(d.id)||d.end<d.start||!['Plan','En curso','Completada'].includes(d.state)))throw Error('IDs únicos, fin ≥ inicio y estados Plan / En curso / Completada.');
  const visiting=new Set(),done=new Set();function visit(d){if(visiting.has(d.id))throw Error('Las dependencias no pueden formar ciclos.');if(done.has(d.id))return;visiting.add(d.id);for(const id of d.deps){if(!map.has(id))throw Error('Dependencia inexistente: '+id);if(d.start<map.get(id).end)throw Error('Una dependencia fin→inicio no puede terminar después del inicio dependiente.');visit(map.get(id));}visiting.delete(d.id);done.add(d.id);}data.forEach(visit);
  let d=[Math.min(...data.map(v=>v.start)),Math.max(...data.map(v=>v.end))];if(d[0]===d[1])d[1]+=DAY;if(d[1]-d[0]>3660*DAY)throw Error('El Gantt admite hasta diez años.');
  selection(ctx,data.map(d=>d.id+' · '+d.name),data.map(v=>`${v.name}: ${date(v.start)} → ${date(v.end)} (${fmt.format((v.end-v.start)/DAY)} días transcurridos). ${v.owner}. ${v.state}. Depende de: ${v.deps.join(', ')||'ninguna'}.`));
  mount(ctx,ctx.title+'; fechas UTC, intervalos inicio a fin y dependencias fin a inicio.',(s,width)=>{
   // Línea de tiempo mínima legible de 320 px; si no cabe, el componente se desplaza (declarado).
   const lw=Math.max(110,Math.min(240,labelColumn(ctx,data.map(v=>v.id+' · '+v.name),width,.34))),span=Math.max(320,width-lw-16),total=lw+span+16;
   const rh=Math.max(52,...data.map(v=>G.wrap(v.id+' · '+v.name,lw-12,ctx.font,2).length*15+30)),h=24+data.length*rh;
   const x=axis(ctx,s,d[0],d[1],lw,lw+span,h,{unit:'Fechas UTC · ○ plan, ◐ en curso, ● completada',dates:true});
   data.forEach((v,i)=>v.deps.forEach(id=>{const j=data.findIndex(t=>t.id===id),from=data[j],a=x(from.end),b=x(v.start),yy=24+j*rh+rh/2-6,y=24+i*rh+rh/2-6;const elbow=Math.min(b,Math.max(lw,a+10));s.append(svg('path',{d:`M${a} ${yy} H${elbow} V${y} H${b}`,class:'ev-dependencia'}),svg('path',{d:`M${b-6} ${y-4} L${b} ${y} L${b-6} ${y+4}`,class:'ev-dependencia'}));}));
   data.forEach((v,i)=>{const y=24+i*rh+rh/2-6;const ln=wrap(s,v.id+' · '+v.name,0,y-6,lw-12,ctx.font,2,{class:'mg-texto-fuerte'});s.append(svg('text',{x:0,y:y-4+ln*15,class:'mg-texto-suave'},({'Plan':'○','En curso':'◐','Completada':'●'})[v.state]+' '+v.state));const g=svg('g');if(v.end===v.start)g.append(svg('path',{d:`M${x(v.start)} ${y-8} l8 8 -8 8 -8 -8 Z`,class:'ev-solido'}));else g.append(svg('rect',{x:x(v.start),y:y-9,width:Math.max(2,x(v.end)-x(v.start)),height:18,rx:2,class:'ev-solido'}));mark(s,g,i);});
   ctx.model={data,domain:d};return {height:h+44,width:Math.max(width,total)};
  });
 }
 function funnel(ctx){
  const data=rows(ctx.root,2,12,3).map(c=>({name:label(c[0]),v:number(c[1]),meaning:label(c[2])}));if(data[0].v<=0||data.some((d,i)=>!Number.isInteger(d.v)||d.v<0||(i&&d.v>data[i-1].v)))throw Error('El embudo exige recuentos enteros no crecientes y base positiva.');
  const max=data[0].v;
  const desc=data.map((v,i)=>`${v.name}: ${amount(v.v,ctx.unit)}; ${pct(v.v/max)} de la base.${i?' Conversión desde la anterior: '+(data[i-1].v?pct(v.v/data[i-1].v):'no definida (base cero)')+'; abandono '+amount(data[i-1].v-v.v,ctx.unit)+'.':''} ${v.meaning}`);
  selection(ctx,data.map(d=>d.name),desc);
  mount(ctx,ctx.title+'; ancho proporcional al recuento; cero común.',(s,width)=>{
   const narrow=width<480,lw=narrow?0:labelColumn(ctx,data.map(d=>d.name),width),x0=narrow?0:lw+8,x1=width-12,rh=narrow?70:56,h=12+data.length*rh,x=axis(ctx,s,0,max,x0,x1,h,{unit:ctx.unit,zero:true});
   data.forEach((v,i)=>{const y=12+i*rh+(narrow?18:0);if(narrow)s.append(svg('text',{x:0,y:y-6,class:'mg-texto-fuerte'},G.fit(v.name,width,ctx.font,1)));else wrap(s,v.name,lw,y+16,lw-8,ctx.font,2,{'text-anchor':'end',class:'mg-texto-fuerte'});mark(s,svg('rect',{x:x0,y,width:Math.max(.5,x(v.v)-x0),height:22,class:'ev-solido'}),i);s.append(svg('text',{x:x0,y:y+38,class:'mg-texto-suave'},G.fit(fmt.format(v.v)+' · '+pct(v.v/max)+' de la base',x1-x0,ctx.font,1)));});
   ctx.model={data,base:max};return {height:h+44};
  });
 }
 function uncertainty(ctx){
  if(!ctx.root.querySelector('[data-evidencia-metodo]')?.textContent.trim())throw Error('Explica cómo se construyó el intervalo.');
  const data=rows(ctx.root,2,48,4).map(c=>({t:day(c[0]),low:number(c[1]),v:number(c[2]),high:number(c[3])}));if(data.some((d,i)=>d.low>d.v||d.v>d.high||(i&&d.t<=data[i-1].t)))throw Error('Fechas estrictamente crecientes y límite inferior ≤ central ≤ superior.');
  const desc=data.map(d=>`${date(d.t)}: inferior ${amount(d.low,ctx.unit)}, central ${amount(d.v,ctx.unit)}, superior ${amount(d.high,ctx.unit)}.`);
  selection(ctx,data.map(d=>date(d.t)),desc);
  mount(ctx,ctx.title+'; banda de escenarios declarados, sin probabilidad implícita.',(s,width)=>{
   const h=Math.round(Math.max(240,Math.min(360,width*.5))),lo=Math.min(...data.map(d=>d.low)),hi=Math.max(...data.map(d=>d.high)),pad=(hi-lo)*.05||1;
   const n=G.nice(lo-pad,hi+pad,Math.max(3,Math.floor((h-80)/44))),tf=G.tickFormat(n.ticks,ctx.spec,{lang:ctx.lang}),x0=Math.ceil(Math.max(...n.ticks.map(v=>G.textWidth(tf(v),ctx.font))))+10,bottom=h-40;
   const y=G.linear([n.min,n.max],[bottom,24]);ctx.domain=[n.min,n.max];
   G.axis(s,{orient:'left',scale:y,ticks:n.ticks,format:tf,from:x0,to:width-8,at:x0-6});s.append(svg('text',{x:0,y:12,class:'grafica-unidad'},G.fit(ctx.unit,width,ctx.font,1)));
   const x=axis(ctx,s,data[0].t,data.at(-1).t,x0+6,width-14,bottom,{unit:'Fecha UTC',dates:true});
   s.append(svg('path',{d:'M'+data.map(d=>`${x(d.t)} ${y(d.high)}`).join(' L')+' L'+[...data].reverse().map(d=>`${x(d.t)} ${y(d.low)}`).join(' L')+' Z',class:'ev-banda'}));
   for(const key of ['low','high','v'])s.append(svg('path',{d:'M'+data.map(d=>`${x(d.t)} ${y(d[key])}`).join(' L'),class:key==='v'?'ev-central':'ev-limite'}));
   data.forEach((d,i)=>mark(s,svg('circle',{cx:x(d.t),cy:y(d.v),r:5,class:'ev-punto'}),i));
   ctx.model={data,domain:ctx.domain};return {height:h+14};
  });
 }
 function story(ctx){
  const data=rows(ctx.root,2,8,3).map(c=>({name:label(c[0]),v:number(c[1]),text:label(c[2])}));if(data.some(d=>d.v<0)||Math.max(...data.map(d=>d.v))===0)throw Error('El relato requiere magnitudes no negativas y algún valor positivo.');
  const steps=make('ol');steps.className='relato-pasos';ctx.ui.append(steps);const buttons=[];
  data.forEach((d,i)=>{const li=make('li'),b=make('button',d.name);b.type='button';const p=make('p',amount(d.v,ctx.unit)+'. '+d.text);li.append(b,p);steps.append(li);buttons.push(b);ctx.on(b,'click',()=>{manual.checked=true;ctx.choose(i);});});
  const control=make('label'),manual=make('input');manual.type='checkbox';control.append(manual,make('span',' Elegir pasos manualmente'));ctx.tools.append(control);
  const select=selection(ctx,data.map(d=>d.name),data.map(d=>`${d.name}: ${amount(d.v,ctx.unit)}. ${d.text}`),i=>{buttons.forEach((b,j)=>{b.setAttribute('aria-pressed',String(i===j));b.closest('li').classList.toggle('relato-actual',i===j);});});ctx.on(select,'change',()=>{manual.checked=true;});
  ctx.detail.setAttribute('aria-live','off');ctx.ui.classList.add('ev-relato');
  mount(ctx,ctx.title+'; todos los pasos comparten escala.',(s,width)=>{
   const narrow=width<360,lw=narrow?0:labelColumn(ctx,data.map(d=>d.name),width,.34),x0=narrow?0:lw+8,x1=width-12,rh=narrow?76:64,h=10+data.length*rh,x=axis(ctx,s,0,Math.max(...data.map(d=>d.v)),x0,x1,h,{unit:ctx.unit,zero:true});
   data.forEach((d,i)=>{const y=10+i*rh+(narrow?18:0);if(narrow)s.append(svg('text',{x:0,y:y-6,class:'mg-texto-fuerte'},G.fit(d.name,width,ctx.font,1)));else wrap(s,d.name,lw,y+16,lw-8,ctx.font,2,{'text-anchor':'end',class:'mg-texto-fuerte'});mark(s,svg('rect',{x:x0,y,width:Math.max(.5,x(d.v)-x0),height:22,class:'ev-solido'}),i);s.append(svg('text',{x:x0,y:y+38,class:'mg-texto-suave'},amount(d.v,ctx.unit)));});
   return {height:h+44};
  });
  const io=new IntersectionObserver(entries=>{if(manual.checked||document.hidden)return;const visible=entries.filter(e=>e.isIntersecting);if(visible.length){const near=visible.sort((a,b)=>Math.abs(a.boundingClientRect.top-innerHeight*.45)-Math.abs(b.boundingClientRect.top-innerHeight*.45))[0];ctx.choose([...steps.children].indexOf(near.target));}},{rootMargin:'-25% 0px -35% 0px',threshold:0});[...steps.children].forEach(li=>io.observe(li));ctx.clean.push(()=>io.disconnect());ctx.model={data};
 }
 function image(ctx){
  const source=ctx.root.querySelector('[data-evidencia-imagen] img'),list=ctx.root.querySelector('[data-evidencia-zonas]');if(!source||!/^data:image\//.test(source.getAttribute('src')||'')||!list)throw Error('Se requiere una imagen incrustada y lista de zonas.');
  const zones=[...list.children].map(li=>({x:Number(li.dataset.x),y:Number(li.dataset.y),text:label(li)}));if(zones.length<1||zones.length>12||zones.some(d=>!Number.isFinite(d.x)||!Number.isFinite(d.y)||d.x<0||d.x>100||d.y<0||d.y>100))throw Error('Usa 1–12 zonas, con coordenadas porcentuales de 0 a 100.');
  const holder=source.parentElement,oldHidden=holder.hidden;holder.hidden=true;ctx.clean.push(()=>{holder.hidden=oldHidden;});
  ctx.view.classList.add('ev-imagen-visor');const sheet=make('div'),img=source.cloneNode(true);img.removeAttribute('id');sheet.className='ev-lamina';sheet.append(img);ctx.view.append(sheet);let zoom=1;const read=make('output');read.setAttribute('aria-label','Ampliación de imagen');
  const setZoom=value=>{zoom=Math.max(1,Math.min(4,value));sheet.style.width=(100*zoom)+'%';read.textContent=Math.round(zoom*100)+' %';if(ctx.selected!==undefined)focusZone(ctx.selected);};
  function focusZone(i){const d=zones[i];ctx.view.scrollLeft=Math.max(0,sheet.clientWidth*d.x/100-ctx.view.clientWidth/2);ctx.view.scrollTop=Math.max(0,sheet.clientHeight*d.y/100-ctx.view.clientHeight/2);}
  for(const [name,fn] of [['Ampliar imagen',()=>setZoom(zoom+.5)],['Reducir imagen',()=>setZoom(zoom-.5)],['Ajustar imagen',()=>setZoom(1)]]){const b=make('button',name==='Ampliar imagen'?'+':name==='Reducir imagen'?'−':'↺');b.type='button';b.className='nota-icono';b.title=name;b.setAttribute('aria-label',name);ctx.tools.append(b);ctx.on(b,'click',fn);}ctx.tools.append(read);
  zones.forEach((d,i)=>{const b=make('button',String(i+1));b.type='button';b.className='ev-pin';b.style.left=d.x+'%';b.style.top=d.y+'%';b.dataset.evRow=i;b.setAttribute('aria-label',`Zona ${i+1}: ${d.text}`);sheet.append(b);ctx.on(b,'click',()=>ctx.choose(i));});
  selection(ctx,zones.map((d,i)=>`${i+1}. ${d.text}`),zones.map((d,i)=>`Zona ${i+1}: ${d.text}`),focusZone);ctx.on(img,'load',()=>focusZone(ctx.selected||0));setZoom(1);ctx.model={zones,get zoom(){return zoom;}};
 }
 const renderers={sankey,cohortes:cohorts,sensibilidad:sensitivity,gantt,embudo:funnel,incertidumbre:uncertainty,relato:story,imagen:image};
 function init(root=document){return [...(root.matches?.('[data-evidencia]')?[root]:[]),...root.querySelectorAll('[data-evidencia]')].map(el=>{if(instances.has(el))return instances.get(el);const abort=new AbortController(),clean=[],ui=make('div'),tools=make('div'),view=make('div'),detail=make('p');ui.className='evidencia-ui';tools.className='evidencia-controles';view.className='evidencia-visor';detail.className='evidencia-detalle';detail.setAttribute('role','status');detail.setAttribute('aria-live','polite');view.tabIndex=0;view.setAttribute('role','region');const title=el.querySelector('table caption,h3')?.textContent.trim()||'Evidencia';view.setAttribute('aria-label',title+', desplazable');const note=make('p');note.className='mg-desplazar-nota';note.hidden=true;ui.append(tools,view,note,detail);el.prepend(ui);
   const ctx={root:el,title,unit:el.dataset.unidad||'',ui,tools,view,note,detail,clean,selected:undefined,choose:()=>{},on:(node,type,fn,options={})=>node.addEventListener(type,fn,{...options,signal:abort.signal}),lang:G?G.lang(el):'es-CO',spec:G?G.specOf(el):'auto'};
   const instance={get model(){return ctx.model;},get selected(){return ctx.selected;},select:i=>ctx.choose(i),destroy(){abort.abort();clean.forEach(fn=>fn());ui.remove();instances.delete(el);}};instances.set(el,instance);
   try{if(el.dataset.evidencia!=='imagen'&&(!ctx.unit.trim()||ctx.unit.length>40))throw Error('Declara una unidad de 1 a 40 caracteres.');if(!renderers[el.dataset.evidencia])throw Error('Tipo de evidencia desconocido.');if(el.dataset.evidencia!=='imagen'&&!G)throw Error('Incluye packages/core/components/chart-core.js.');renderers[el.dataset.evidencia](ctx);if(el.dataset.evidencia!=='imagen')ui.append(G.exporter(el,{table:el.querySelector('table[data-evidencia-datos]'),title,getSvg:()=>ctx.svg}));}
   catch(error){abort.abort();clean.forEach(fn=>fn());ui.replaceChildren(make('p','No se dibujó esta vista: '+error.message+' Los datos originales siguen disponibles.'));ui.classList.add('evidencia-error');instance.error=error.message;}
   return instance;
  });}
 window.NotaEvidencia={init,get:el=>instances.get(el)};init();
})();
