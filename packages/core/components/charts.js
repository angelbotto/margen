/* Bottifact · gráficas SVG desde tablas semánticas. Sin dependencias.
   Pegar una vez; NotaGraficas.init(raíz) para contenido insertado posteriormente. */
(() => {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';
  const instances = new WeakMap();
  const fmt = n => new Intl.NumberFormat('es-CO', {maximumSignificantDigits: 6,
    notation: Math.abs(n)>=1e7 || (n!==0 && Math.abs(n)<.001) ? 'scientific' : 'standard'}).format(n);
  const element = (tag, cls, text) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  };
  const svgNode = (tag, attrs = {}, text) => {
    const e = document.createElementNS(NS, tag);
    Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, String(v)));
    if (text !== undefined) e.textContent = text;
    return e;
  };
  function number(raw, missing = false) {
    if (raw === null || raw.trim() === '') {
      if (missing) return null;
      throw new TypeError('Falta un data-valor numérico.');
    }
    const n = Number(raw);
    if (!Number.isFinite(n)) throw new TypeError('El valor debe ser finito.');
    return n;
  }
  // Una única función coloca valores y ticks; nunca hay coordenadas con escala distinta.
  function scale(min, max, start, end) {
    if (![min,max,start,end,max-min,end-start].every(Number.isFinite) || min >= max) throw new TypeError('Dominio inválido.');
    return v => start + (v - min) / (max - min) * (end - start);
  }
  function domain(values, zero = false) {
    let min = Math.min(...values), max = Math.max(...values);
    if (!values.length) return [0, 1];
    if (zero) { min = Math.min(0, min); max = Math.max(0, max); }
    if (min === max) { const pad = Math.abs(min) * .1 || 1; min -= pad; max += pad; }
    if (!Number.isFinite(max - min)) throw new TypeError('El rango excede la precisión numérica.');
    return [min, max];
  }
  function delta(current, previous) {
    if (current === null || previous === null) return 'Sin comparación: dato ausente';
    const change = current - previous;
    const absolute = (change > 0 ? '+' : '') + fmt(change);
    if (previous === 0) return absolute + ' · porcentaje no definido (base 0)';
    return absolute + ' · ' + (change > 0 ? '+' : '') + fmt(change / Math.abs(previous) * 100) + ' %';
  }
  function read(figure) {
    const type = figure.dataset.grafica;
    if (!['barras','lineas','temporal','dispersion','distribucion','calor'].includes(type)) throw new TypeError('Tipo de gráfica desconocido.');
    const table = figure.querySelector('table');
    const heads = [...(table?.tHead?.rows[0]?.cells || [])].map(e => e.textContent.trim());
    const rows = [...(table?.tBodies[0]?.rows || [])];
    if (heads.length < 2 || rows.length > 500) throw new TypeError('Se necesitan cabeceras y hasta 500 filas.');
    if (type === 'calor' && (heads.length > 32 || rows.length > 31)) throw new TypeError('El mapa admite hasta 31 × 31 celdas.');
    if (['barras','lineas','temporal'].includes(type) && heads.length > 5) throw new TypeError('Hasta cuatro series por figura.');
    if (['dispersion','distribucion'].includes(type) && heads.length !== 3) throw new TypeError('Se necesitan tres columnas.');
    const data = rows.map(row => {
      if (row.cells.length !== heads.length) throw new TypeError('Todas las filas deben tener las mismas columnas.');
      const label = row.cells[0].textContent.trim();
      const values = [...row.cells].slice(1).map(c => number(c.getAttribute('data-valor'), true));
      let x = null, end = null;
      if (type === 'temporal') {
        const date = row.cells[0].querySelector('time')?.getAttribute('datetime');
        x = Date.parse(date + 'T00:00:00Z');
        if (!/^\d{4}-\d{2}-\d{2}$/.test(date || '') || !Number.isFinite(x) || new Date(x).toISOString().slice(0,10) !== date) throw new TypeError('Fecha ISO YYYY-MM-DD inválida.');
      }
      if (type === 'distribucion') {
        x = number(row.cells[0].getAttribute('data-desde'));
        end = number(row.cells[0].getAttribute('data-hasta'));
        if (x >= end || values[0] === null || values[0] < 0 || !Number.isInteger(values[0])) throw new TypeError('Intervalos crecientes y frecuencias enteras no negativas.');
        // Columna de densidad se calcula, no es una segunda fuente manual.
        values[1] = values[0] / (end - x);
        if(!Number.isFinite(values[1]))throw new TypeError('La densidad excede la precisión numérica.');
      }
      if (type === 'dispersion' && values.some(v => v === null)) throw new TypeError('Cada punto necesita X e Y.');
      return {label, values, x, end};
    });
    if (type === 'temporal' && data.some((r,i) => i && r.x <= data[i-1].x)) throw new TypeError('Fechas estrictamente crecientes; no se reordenan ni agregan datos.');
    if (type === 'distribucion' && data.some((r,i) => i && r.x < data[i-1].end)) throw new TypeError('Intervalos ordenados, sin solapamiento.');
    return {type, table, heads, data, title: table.caption?.textContent.trim() || 'Gráfica'};
  }
  function label(svg, x, y, text, attrs = {}) {
    const t = svgNode('text', {x, y, ...attrs}, text); svg.append(t); return t;
  }
  function axes(svg, xd, yd, bounds, xTitle, yTitle, xFormat = fmt) {
    const {left, right, top, bottom} = bounds;
    const sx = scale(...xd, left, right), sy = scale(...yd, bottom, top);
    for (let i = 0; i <= 4; i++) {
      const y = yd[0] + (yd[1]-yd[0])*i/4;
      svg.append(svgNode('line', {x1:left,x2:right,y1:sy(y),y2:sy(y),class:'grafica-rejilla','data-tick-y':y}));
      label(svg,left-12,sy(y)+4,fmt(y),{'text-anchor':'end'});
      if (xTitle) {
        const x = xd[0] + (xd[1]-xd[0])*i/4;
        label(svg,sx(x),bottom+26,xFormat(x),{'text-anchor':'middle','data-tick-x':x});
      }
    }
    svg.append(svgNode('path',{d:`M${left} ${top}V${bottom}H${right}`,class:'grafica-eje'}));
    // Unidades completas en HTML: el texto largo puede envolver sin salirse del viewBox.
    label(svg,left,top-18,'Y',{class:'grafica-unidad'});
    if(xTitle) label(svg,(left+right)/2,bottom+62,'X',{'text-anchor':'middle',class:'grafica-unidad'});
    return {sx,sy};
  }
  class NotaGrafica {
    constructor(figure) {
      if (instances.has(figure)) throw new TypeError('Ya existe una gráfica en este contenedor.');
      this.figure=figure; this.parts=[]; this.original=[];
      this.details=figure.querySelector('details'); this.wasOpen=this.details?.open;
      this.model=read(figure);
      try {this.render();instances.set(figure,this);} catch(error) {this.destroy();throw error;}
      if (this.model.type === 'barras' && typeof ResizeObserver !== 'undefined') {
        this.resizeObserver = new ResizeObserver(() => {
          const width = this.measureWidth();
          if (width <= 0 || Math.max(260, width) === this.renderWidth) return;
          const open = this.details?.open;
          this.parts.forEach(part => part.remove()); this.parts = [];
          this.render();
          if (this.details) this.details.open = open;
        });
        this.resizeObserver.observe(figure);
      }
    }
    measureWidth() {
      const style=getComputedStyle(this.figure);
      const inset=['paddingLeft','paddingRight','borderLeftWidth','borderRightWidth'].reduce((sum,key)=>sum+(parseFloat(style[key])||0),0);
      return Math.max(0,Math.round(this.figure.getBoundingClientRect().width-inset));
    }
    add(e) {this.parts.push(e);this.figure.insertBefore(e,this.figure.firstChild);return e;}
    render() {
      const {type,heads,data,title}=this.model;
      this.figure.classList.add('nota-grafica');
      if (!data.length || data.every(r=>r.values.every(v=>v===null))) {
        this.add(element('p','grafica-vacia','Sin datos disponibles.')); return;
      }
      if (type==='calor') {this.heatmap();this.add(element('h3','grafica-titulo',title));return;}
      const available = this.measureWidth();
      this.renderWidth = type === 'barras' ? Math.max(260, available || 800) : 800;
      this.labelLimit = Math.max(6, Math.min(26, Math.floor(this.renderWidth * .28 / 7)));
      this.labelParts = text => text.match(new RegExp('.{1,'+this.labelLimit+'}(?:\\s|$)|.{1,'+this.labelLimit+'}', 'g')) || [''];
      const lineCount = text => this.labelParts(text).length;
      this.rowSizes=data.map(r=>Math.max(r.values.length*42,lineCount(r.label)*16+16));
      const width=this.renderWidth, height=type==='barras'?Math.max(240,this.rowSizes.reduce((a,b)=>a+b,0)+112):400;
      const region=element('div','grafica-caja'); region.tabIndex=0;region.setAttribute('role','region');
      region.setAttribute('aria-label',title+'. Gráfica desplazable; datos completos a continuación.');
      const svg=svgNode('svg',{viewBox:`0 0 ${width} ${height}`,width,height,role:'img','aria-label':title});
      svg.append(svgNode('title',{},title),svgNode('desc',{},'Los valores exactos y las unidades están en la tabla de datos de esta figura.'));
      region.append(svg);this.add(region);this.svg=svg;
      const all=data.flatMap(r=>r.values).filter(v=>v!==null);
      if (type==='barras') this.bars(svg,width,height);
      else {
        const b={left:110,right:700,top:50,bottom:310};
        let xd,yd,xTitle=heads[0];
        if(type==='dispersion') {xd=domain(data.map(r=>r.values[0]));yd=domain(data.map(r=>r.values[1]));xTitle=heads[1];}
        else if(type==='distribucion') {xd=domain(data.flatMap(r=>[r.x,r.end]));yd=[0,Math.max(...data.map(r=>r.values[1]))||1];xTitle=heads[0];}
        else {xd=type==='temporal'?domain(data.map(r=>r.x)):domain(data.map((_,i)=>i));yd=domain(all);}
        // El dominio numérico está expuesto en SVG para verificar el contrato, no para controlarlo.
        svg.dataset.xMin=xd[0];svg.dataset.xMax=xd[1];svg.dataset.yMin=yd[0];svg.dataset.yMax=yd[1];
        const yTitle=type==='dispersion'?heads[2]:type==='distribucion'?heads[2]:(this.figure.dataset.unidad || heads.slice(1).join(' / '));
        const units=element('p','grafica-unidades','X: '+xTitle+' · Y: '+yTitle);region.before(units);this.parts.push(units);
        const {sx,sy}=axes(svg,xd,yd,b,['lineas','temporal'].includes(type)?null:xTitle,yTitle);
        if(type==='dispersion') data.forEach(r=>{
          const circle=svgNode('circle',{cx:sx(r.values[0]),cy:sy(r.values[1]),r:5,class:'grafica-serie serie-0','data-x':r.values[0],'data-y':r.values[1]});
          circle.append(svgNode('title',{},`${r.label}: ${fmt(r.values[0])}, ${fmt(r.values[1])}`));svg.append(circle);
        });
        else if(type==='distribucion') {
          data.forEach((r,i)=>{
            const bar=svgNode('rect',{x:sx(r.x),y:sy(r.values[1]),width:sx(r.end)-sx(r.x),height:sy(0)-sy(r.values[1]),class:'grafica-barra serie-0','data-desde':r.x,'data-hasta':r.end,'data-count':r.values[0],'data-density':r.values[1]});
            bar.append(svgNode('title',{},`${r.label}: ${fmt(r.values[0])} observaciones; densidad ${fmt(r.values[1])}`));svg.append(bar);
            const cell=this.model.table.tBodies[0].rows[i].cells[2];this.original.push([cell,cell.textContent]);cell.textContent=fmt(r.values[1]);
          });
        } else this.lines(svg,sx,sy,b);
      }
      if(['barras','lineas','temporal'].includes(type)) {
        const legend=element('ul','grafica-leyenda');legend.setAttribute('aria-label','Series');
        heads.slice(1).forEach((h,i)=>{const li=element('li','',h);li.prepend(element('span','grafica-muestra serie-'+i, String(i+1)));legend.append(li);});
        region.after(legend);this.parts.push(legend);
      }
      if(type==='temporal') this.comparison();
      this.add(element('h3','grafica-titulo',title));
      if(this.details) this.details.open=false;
    }
    bars(svg,width,height) {
      const {heads,data}=this.model;
      const values=data.flatMap(r=>r.values).filter(v=>v!==null),xd=domain(values,true);
      const longest = Math.max(...data.map(r => Math.min(this.labelLimit, r.label.length)));
      const left=Math.min(320,Math.max(64,longest*7+28)),right=width-80,top=60,bottom=height-52,sx=scale(...xd,left,right);
      svg.dataset.xMin=xd[0];svg.dataset.xMax=xd[1];
      const ticks = width < 480 ? 2 : 4;
      for(let i=0;i<=ticks;i++) {const x=xd[0]+(xd[1]-xd[0])*i/ticks;svg.append(svgNode('line',{x1:sx(x),x2:sx(x),y1:top-10,y2:bottom,class:'grafica-rejilla','data-tick-x':x}));label(svg,sx(x),bottom+26,fmt(x),{'text-anchor':'middle'});}
      svg.append(svgNode('line',{x1:sx(0),x2:sx(0),y1:top-10,y2:bottom,class:'grafica-eje'}));
      const units=element('p','grafica-unidades','X: '+(this.figure.dataset.unidad||heads.slice(1).join(' / ')));this.svg.parentElement.before(units);this.parts.push(units);
      label(svg,left,28,'X');
      let rowTop=top;
      data.forEach((r,j)=>r.values.forEach((v,i)=>{
        const y=rowTop+i*42;
        if(i===r.values.length-1)rowTop+=this.rowSizes[j];
        // Las etiquetas extensas se parten en líneas; la tabla conserva el texto íntegro.
        if(i===0) {
          const words=this.labelParts(r.label);
          const t=label(svg,12,y+16,'');
          words.forEach((w,k)=>t.append(svgNode('tspan',{x:12,dy:k?16:0},w.trim())));
        }
        if(v===null) {label(svg,left,y+16,'Sin dato');return;}
        const rect=svgNode('rect',{x:Math.min(sx(0),sx(v)),y,width:Math.abs(sx(v)-sx(0)),height:24,class:'grafica-barra serie-'+i,'data-value':v});
        rect.append(svgNode('title',{},`${r.label}, ${heads[i+1]}: ${fmt(v)}`));svg.append(rect);
        label(svg,right+8,y+16,fmt(v),{'text-anchor':'start'});
      }));
    }
    lines(svg,sx,sy,b) {
      const {data,heads,type}=this.model;
      heads.slice(1).forEach((_,i)=>{
        let d='',pen=false;
        data.forEach((r,j)=>{
          const v=r.values[i];if(v===null){pen=false;return;}
          const x=sx(type==='temporal'?r.x:j),y=sy(v);
          d+=(pen?'L':'M')+x+' '+y;pen=true;
          const point=svgNode('circle',{cx:x,cy:y,r:i===0?3.5:4.5,class:'grafica-punto serie-'+i,'data-value':v,'data-index':j});
          point.append(svgNode('title',{},r.label+', '+heads[i+1]+': '+fmt(v)));svg.append(point);
        });
        svg.prepend(svgNode('path',{d,class:'grafica-trazo serie-'+i}));
      });
      // Fechas irregulares: sólo rótulos separados por 115 px. Todos los puntos se dibujan.
      const candidates=Array.from({length:Math.min(5,data.length)},(_,i)=>Math.round(i*(data.length-1)/Math.max(1,Math.min(5,data.length)-1)));
      const ticks=new Set([0]);let last=sx(type==='temporal'?data[0].x:0);
      candidates.slice(1).forEach(i=>{const x=sx(type==='temporal'?data[i].x:i);if(x-last>=115){ticks.add(i);last=x;}});
      if(data.length>1){const end=data.length-1,x=sx(type==='temporal'?data[end].x:end);[...ticks].forEach(i=>{if(i!==0 && x-sx(type==='temporal'?data[i].x:i)<115)ticks.delete(i);});ticks.add(end);}
      // Etiquetas completas en varias líneas, con altura calculada según su contenido.
      let lines=1;
      data.forEach((r,j)=>{if(ticks.has(j)) {
        const text=type==='temporal'?new Date(r.x).toISOString().slice(0,10):r.label;
        const chunks=text.match(/.{1,14}(?:\s|$)|.{1,14}/g)||[''];lines=Math.max(lines,chunks.length);
        const x=sx(type==='temporal'?r.x:j),t=label(svg,x,b.bottom+26,'',{'text-anchor':'middle','data-label-index':j});
        chunks.forEach((chunk,i)=>t.append(svgNode('tspan',{x,dy:i?16:0},chunk.trim())));
      }});
      const height=Math.max(400,b.bottom+lines*16+86);
      svg.setAttribute('viewBox',`0 0 800 ${height}`);svg.setAttribute('height',height);
      label(svg,(b.left+b.right)/2,b.bottom+lines*16+50,'X',{'text-anchor':'middle'});
    }
    comparison() {
      const {data,heads}=this.model;
      const dl=element('dl','grafica-variacion');
      const now=data.at(-1),before=data.at(-2);
      heads.slice(1).forEach((h,i)=>{
        const row=element('div');row.append(element('dt','',h+' · '+now.label+(before?' frente a '+before.label:'')),element('dd','',before?delta(now.values[i],before.values[i]):'Sin período anterior'));dl.append(row);
      });
      this.svg.parentElement.after(dl);this.parts.push(dl);
    }
    heatmap() {
      const {table,heads,data}=this.model;
      const raw=this.figure.dataset.umbrales;
      if(!raw) throw new TypeError('Define data-umbrales: mínimo, cortes y máximo.');
      const limits=raw.split(',').map(v=>number(v));
      if(limits.length!==6 || limits.some((v,i)=>i&&v<=limits[i-1])) throw new TypeError('Seis límites estrictamente crecientes para cinco niveles.');
      const values=data.flatMap(r=>r.values).filter(v=>v!==null);
      if(values.some(v=>v<limits[0]||v>limits.at(-1))) throw new TypeError('Un valor está fuera de la escala de calor.');
      table.classList.add('tabla-calor');
      this.heatWidth=table.style.getPropertyValue('--calor-ancho');
      table.style.setProperty('--calor-ancho',Math.max(42,8+(heads.length-1)*6)+'rem');
      [...table.tBodies[0].rows].forEach((row,j)=>[...row.cells].slice(1).forEach((cell,i)=>{
        const value=data[j].values[i];
        const level=value===null?'ausente':Math.min(4,limits.slice(1).findIndex(v=>value<v)===-1?4:limits.slice(1).findIndex(v=>value<v));
        this.original.push([cell,cell.textContent,cell.getAttribute('data-nivel')]);cell.dataset.nivel=level;
        cell.textContent=value===null?'Sin dato':fmt(value);
      }));
      const legend=element('ul','calor-leyenda');legend.setAttribute('aria-label','Escala de intensidad: '+(this.figure.dataset.unidad||heads[0]));
      for(let i=0;i<5;i++) {const li=element('li','',`${fmt(limits[i])} ${i===4?'a':'a menos de'} ${fmt(limits[i+1])}`);const swatch=element('span');swatch.dataset.nivel=i;swatch.setAttribute('aria-hidden','true');li.prepend(swatch);legend.append(li);}
      legend.append(element('li','','Sin dato ≠ 0'));this.add(legend);
      // La propia tabla es la visualización: nunca esconderla detrás de un disclosure cerrado.
      if(this.details) this.details.open=true;
    }
    destroy() {
      this.resizeObserver?.disconnect();
      this.parts.forEach(e=>e.remove());
      this.original.forEach(([cell,text,level])=>{cell.textContent=text;if(level===null)delete cell.dataset.nivel;else if(level!==undefined)cell.setAttribute('data-nivel',level);});
      this.model.table.classList.remove('tabla-calor');this.figure.classList.remove('nota-grafica');
      if(this.heatWidth!==undefined){if(this.heatWidth)this.model.table.style.setProperty('--calor-ancho',this.heatWidth);else this.model.table.style.removeProperty('--calor-ancho');}
      if(this.details)this.details.open=this.wasOpen;
      instances.delete(this.figure);
    }
  }
  function init(root=document) {
    const figures=[...(root.matches?.('[data-grafica]')?[root]:[]),...root.querySelectorAll('[data-grafica]')];
    return figures.map(f=>{
      if(instances.has(f))return instances.get(f);
      try {const chart=new NotaGrafica(f);f.querySelector('[data-error-grafica]')?.remove();return chart;}
      catch(error){
        let message=f.querySelector('[data-error-grafica]');
        if(!message){message=element('p','grafica-error');message.dataset.errorGrafica='';f.prepend(message);}
        message.textContent='No se pudo dibujar: '+error.message+' Los datos siguen disponibles.';
        const details=f.querySelector('details');if(details)details.open=true;return null;
      }
    });
  }
  window.NotaGraficas={init,get:el=>instances.get(el),scale,domain,delta,format:fmt};
  init();
})();
