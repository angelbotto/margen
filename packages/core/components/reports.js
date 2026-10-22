/* Margen · piezas de reportes. Tablas como fuente, sin red ni animaciones. Cascada y múltiples
   requieren chart-core.js; incluir tras packages/core/components/globe.js si se usa recorrido. */
(() => {
  'use strict';
  const G = window.MargenGraficas;
  const instances = new WeakMap();
  const fmt = n => G ? G.format(n, 'auto', {lang: G.lang(document.documentElement)}) : new Intl.NumberFormat('es-CO', {maximumSignificantDigits: 12}).format(n);
  const el = (tag, cls, text) => {
    const node = document.createElement(tag); if(cls) node.className = cls;
    if(text !== undefined) node.textContent = text; return node;
  };
  const svg = (tag, attrs = {}, text) => {
    const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
    Object.entries(attrs).forEach(([k,v]) => node.setAttribute(k, String(v)));
    if(text !== undefined) node.textContent = text; return node;
  };
  function finite(raw, missing = false) {
    if(raw === null || raw.trim() === '') { if(missing) return null; throw new TypeError('Falta un valor.'); }
    const n = Number(raw);
    if(!Number.isFinite(n) || Math.abs(n) > 1e9) throw new TypeError('Se admiten valores finitos de hasta mil millones en magnitud.');
    return n;
  }
  function tableData(root, min, max) {
    const table = root.querySelector('table');
    const heads = [...(table?.tHead?.rows[0]?.cells || [])].map(c => c.textContent.trim());
    const rows = [...(table?.tBodies[0]?.rows || [])];
    if(heads.length < min || heads.length > max || !rows.length || rows.length > 60) throw new TypeError('Revisa cabeceras; se admiten de 1 a 60 filas.');
    if(rows.some(r => r.cells.length !== heads.length)) throw new TypeError('Las filas deben tener las mismas columnas.');
    return {table, heads, rows};
  }
  // Caja de la figura: el SVG se dibuja al ancho medido y sin desplazamiento.
  function region(title) {
    const box = el('div','grafica-caja');
    return box;
  }
  function drawing(box, title, width) {
    const s = svg('svg',{class:'mg-svg',width,height:10,viewBox:`0 0 ${width} 10`,'aria-label':title});
    s.append(svg('title',{},title)); box.replaceChildren(s); return s;
  }
  function text(root,x,y,value,attrs={}) { const t = svg('text',{x,y,...attrs},value); root.append(t); return t; }
  class Reporte {
    constructor(root) {
      this.root=root; this.parts=[]; this.restore=[]; this.abort=new AbortController(); this.dead=false;
      try {
        switch(root.dataset.reporte) {
          case 'cascada': this.waterfall(); break;
          case 'multiples': this.multiples(); break;
          case 'conciliacion': this.reconcile(); break;
          case 'escenario': this.scenario(); break;
          case 'recorrido': this.journey(); break;
          default: throw new TypeError('Tipo de reporte desconocido.');
        }
        instances.set(root,this);
      } catch(error) {this.destroy();throw error;}
    }
    add(node,before=this.root.querySelector('.tabla-caja')) {this.root.insertBefore(node,before);this.parts.push(node);return node;}
    change(node,value) {if(!node)throw new TypeError('Falta una celda de resultado.');const children=[...node.childNodes];this.restore.push(()=>node.replaceChildren(...children));node.textContent=value;}
    on(node,type,fn) {node.addEventListener(type,fn,{signal:this.abort.signal});}
    // Cascada: cada tramo empieza donde termina el anterior. El acumulado se calcula, no se suma a mano.
    waterfall() {
      if(!G)throw new TypeError('Incluye packages/core/components/chart-core.js.');
      const {table,rows,heads}=tableData(this.root,3,3);
      const head=table.tHead.rows[0].cells[1],spec=G.specOf(head,this.root),lang=G.lang(this.root),f=v=>G.format(v,spec,{lang});
      let total=0;
      const data=rows.map(r=>{
        const value=finite(r.cells[1].getAttribute('data-valor'));
        const from=total; total+=value;
        if(Math.abs(total)>1e9)throw new TypeError('El acumulado excede mil millones.');
        return {row:r,label:r.cells[0].textContent.trim(),value,from,to:total};
      });
      const title=table.caption?.textContent||'Cascada',unit=this.root.dataset.unidad||heads[1];
      const box=region(title),status=el('p','grafica-estado');status.setAttribute('role','status');
      this.add(box);this.add(status);this.add(G.exporter(this.root,{table,title,getSvg:()=>this.svg}));
      const draw=width=>{
        this.marks?.destroy();
        const s=this.svg=drawing(box,title,width),font=G.fontOf(s),narrow=width<480,sign=v=>(v>0?'+':'')+f(v);
        const valueWidth=Math.ceil(Math.max(...data.map(r=>G.textWidth(sign(r.value),font)),G.textWidth(f(total),font)))+14;
        const labelWidth=narrow?width:Math.min(Math.round(width*.32),Math.ceil(Math.max(...data.map(r=>G.textWidth(r.label,font)),G.textWidth('Resultado',font)))+16);
        const left=narrow?4:labelWidth,right=width-valueWidth,bar=24;
        const labels=[...data.map(r=>G.wrap(r.label,(narrow?width:labelWidth)-12,font,2)),['Resultado']];
        const layout=labels.map(l=>narrow?l.length*15+bar+16:Math.max(bar+18,l.length*15+10));
        const top=34,height=top+layout.reduce((a,b)=>a+b,0)+34;
        const n=G.niceZero(data.flatMap(r=>[r.from,r.to]),Math.max(2,Math.floor((right-left)/70))),tf=G.tickFormat(n.ticks,spec,{lang}),x=G.linear([n.min,n.max],[left,right]);
        s.dataset.xMin=n.min;s.dataset.xMax=n.max;
        G.axis(s,{orient:'bottom',scale:x,ticks:G.spacedTicks(n.ticks,x,tf,font),format:tf,from:top-8,to:height-30,at:height-12,font});
        text(s,0,14,G.fit(unit,width,font,1),{class:'grafica-unidad'});
        const items=[],info=[];let y=top;
        data.forEach((r,i)=>{
          const t=text(s,narrow?4:0,y+12,'',{class:'mg-texto-fuerte'+(narrow?' mg-halo':'')});labels[i].forEach((line,k)=>t.append(svg('tspan',{x:narrow?4:0,dy:k?15:0},line)));
          const by=narrow?y+labels[i].length*15+2:y;
          const g=svg('g',{});g.append(svg('rect',{x:Math.min(x(r.from),x(r.to)),y:by,width:Math.max(.5,Math.abs(x(r.to)-x(r.from))),height:bar,class:r.value<0?'cascada-baja':'cascada-sube','data-from':r.from,'data-to':r.to}));
          s.append(g);items.push(g);info.push([r.label,heads[1]+': '+sign(r.value),'Acumulado: '+f(r.to)]);
          text(s,width,by+16,sign(r.value),{'text-anchor':'end',class:'mg-texto-fuerte'});
          if(i<data.length-1)s.append(svg('path',{d:`M${x(r.to)} ${by+bar}V${by+layout[i]+(narrow?labels[i+1].length*15+2:0)}`,class:'cascada-enlace'}));
          y+=layout[i];
        });
        text(s,narrow?4:0,y+12,'Resultado',{class:'mg-texto-fuerte'+(narrow?' mg-halo':'')});
        const ty=narrow?y+17:y,g=svg('g',{});g.append(svg('rect',{x:Math.min(x(0),x(total)),y:ty,width:Math.max(.5,Math.abs(x(total)-x(0))),height:bar,class:'cascada-total','data-total':total}));
        s.append(g);items.push(g);info.push(['Resultado',f(total)]);text(s,width,ty+16,f(total),{'text-anchor':'end',class:'mg-texto-fuerte'});
        s.setAttribute('height',height);s.setAttribute('viewBox',`0 0 ${width} ${height}`);
        this.marks=G.marks(this.root,s,{items,describe:i=>info[i],status,label:title});
      };
      this.watch=G.responsive(box,draw);
      data.forEach(r=>this.change(r.row.cells[2],f(r.to)));
      if(table.tFoot)this.change(table.tFoot.rows[0].cells[2],f(total));
    }
    // Múltiplos pequeños: mismo eje Y para todos los paneles; el eje X es el orden de la tabla.
    multiples() {
      if(!G)throw new TypeError('Incluye packages/core/components/chart-core.js.');
      const {table,rows,heads}=tableData(this.root,2,5);
      if(rows.length<2)throw new TypeError('Los múltiples necesitan al menos dos períodos.');
      const lang=G.lang(this.root),labels=rows.map(r=>r.cells[0].textContent.trim());
      const specs=[...table.tHead.rows[0].cells].slice(1).map(th=>G.specOf(th,this.root));
      const values=rows.map(r=>[...r.cells].slice(1).map(c=>finite(c.getAttribute('data-valor'),true)));
      const n=G.niceZero(values.flat().filter(v=>v!==null),4);
      const group=el('div','multiples-rejilla'),status=el('p','grafica-estado');status.setAttribute('role','status');
      this.panels=[];
      heads.slice(1).forEach((head,index)=>{
        const panel=el('div');panel.append(el('h4','',head));
        const title=head+' · '+(table.caption?.textContent||'Serie'),box=region(title);panel.append(box);group.append(panel);
        const state={};this.panels.push(state);
        const f=v=>G.format(v,specs[index],{lang}),tf=G.tickFormat(n.ticks,specs[index],{lang});
        state.watch=G.responsive(box,width=>{
          state.marks?.destroy();
          const s=drawing(box,title,width),font=G.fontOf(s);
          const left=Math.ceil(Math.max(...n.ticks.map(v=>G.textWidth(tf(v),font))))+10,right=width-12,top=12,bottom=170,height=212;
          s.dataset.yMin=n.min;s.dataset.yMax=n.max;
          const x=G.linear([0,rows.length-1],[left+8,right-8]),y=G.linear([n.min,n.max],[bottom,top]);
          G.axis(s,{orient:'left',scale:y,ticks:n.ticks,format:tf,from:left,to:right,at:left-6});
          let path='',pen=false;const items=[],info=[];
          values.forEach((row,i)=>{
            const v=row[index];
            const g=svg('g',{'data-value':v??''});
            if(v===null){pen=false;g.append(svg('path',{d:`M${x(i)-4} ${bottom-4}l8 8M${x(i)+4} ${bottom-4}l-8 8`,class:'grafica-eje'}));}
            else{path+=(pen?'L':'M')+x(i)+' '+y(v);pen=true;g.append(svg('circle',{cx:x(i),cy:y(v),r:4,class:'grafica-punto serie-0','data-value':v}));}
            s.append(g);items.push(g);info.push([labels[i],head+': '+(v===null?G.words(lang).missing:f(v))]);
          });
          s.prepend(svg('path',{d:path,class:'grafica-trazo serie-0'}));
          // Extremos con su nombre de período (abreviado si no cabe); la tabla nombra todos.
          const room=(right-left)/2-8;
          text(s,left+8,bottom+18,G.fit(labels[0],room,font,1),{'text-anchor':'start'});
          text(s,right-8,bottom+18,G.fit(labels.at(-1),room,font,1),{'text-anchor':'end'});
          text(s,(left+right)/2,bottom+36,G.fit(heads[0]+' · orden de la tabla',right-left,font,1),{'text-anchor':'middle',class:'mg-texto-suave'});
          s.setAttribute('height',height);s.setAttribute('viewBox',`0 0 ${width} ${height}`);
          state.marks=G.marks(this.root,s,{items,describe:i=>info[i],status,label:title});
        });
      });
      this.add(group);this.add(status);
    }
    reconcile() {
      const {table,rows}=tableData(this.root,5,5);
      const data=rows.map(row=>{
        const a=finite(row.cells[1].getAttribute('data-valor')), b=finite(row.cells[2].getAttribute('data-valor'),true);
        if(!Number.isSafeInteger(a)||a<0||(b!==null&&(!Number.isSafeInteger(b)||b<0))) throw new TypeError('Conciliación requiere conteos enteros no negativos.');
        return {row,a,b};
      });
      let expected=0,observed=0,complete=true;
      data.forEach(({row,a,b})=>{expected+=a; if(b===null)complete=false;else observed+=b;
        this.change(row.cells[3],b===null?'Sin dato':(b-a>0?'+':'')+fmt(b-a));});
      if(table.tFoot) {
        const cells=table.tFoot.rows[0].cells;
        this.change(cells[1],fmt(expected));this.change(cells[2],complete?fmt(observed):'Incompleto');
        this.change(cells[3],complete?fmt(observed-expected):'Sin comparación');
      }
    }
    scenario() {
      const form=this.root.querySelector('form');
      const fields=['volumen','antes','despues'].map(n=>form?.elements.namedItem(n));
      const result=this.root.querySelector('[data-resultado]');const detail=this.root.querySelector('[data-formula]');
      if(fields.some(f=>!f)||!result||!detail)throw new TypeError('Faltan campos o resultados del escenario.');
      this.change(result,result.textContent);this.change(detail,detail.textContent);
      const update=()=>{
        if(fields.some(f=>!f.validity.valid||f.value==='')) {result.textContent='Completa los tres valores dentro de sus límites.';detail.textContent='No hay una estimación válida.';return;}
        const [volume,before,after]=fields.map(f=>Number(f.value));
        const hours=volume*(before-after)/60;
        result.textContent=fmt(Math.abs(hours))+' h/mes '+(hours>=0?'liberadas':'adicionales');
        detail.textContent=`${fmt(volume)} operaciones × (${fmt(before)} − ${fmt(after)}) min ÷ 60 = ${fmt(hours)} h/mes. Es capacidad estimada, no ahorro monetario ni una predicción.`;
      };
      this.on(form,'submit',e=>e.preventDefault());this.on(form,'input',update);
      this.on(form,'reset',()=>queueMicrotask(()=>{if(!this.dead)update();}));update();
    }
    journey() {
      const stage=this.root.querySelector('[data-recorrido-globo]');
      const steps=[...this.root.querySelectorAll('[data-ruta]')];
      const status=this.root.querySelector('[data-recorrido-estado]');
      const prev=this.root.querySelector('[data-paso="prev"]'),next=this.root.querySelector('[data-paso="next"]');
      if(!stage||!steps.length||!status||!prev||!next||!window.NotaGlobo)throw new TypeError('El recorrido necesita pasos, controles y NotaGlobo.');
      const points=new Map(),ids=new Set();
      const arcs=steps.map(step=>{
        const places=[...step.querySelectorAll('[data-lugar]')];const id=step.dataset.ruta;
        if(!id||ids.has(id)||places.length!==2)throw new TypeError('Cada paso necesita una ruta única y dos lugares.');ids.add(id);
        places.forEach(place=>{
          const p={id:place.dataset.lugar,label:place.textContent.trim(),lat:finite(place.getAttribute('data-lat')),lon:finite(place.getAttribute('data-lon'))};
          if(!p.id || Math.abs(p.lat)>90 || Math.abs(p.lon)>180)throw new TypeError('Coordenada geográfica inválida.');
          if(points.has(p.id)&&JSON.stringify(points.get(p.id))!==JSON.stringify(p))throw new TypeError('Coordenadas o nombre inconsistentes para el mismo lugar.');
          points.set(p.id,p);
        });
        return {id,from:places[0].dataset.lugar,to:places[1].dataset.lugar,label:places.map(p=>p.textContent.trim()).join(' → '),detail:step.querySelector('p')?.textContent.trim()||''};
      });
      this.globe=new NotaGlobo(stage,{points:[...points.values()],arcs});this.globe.pause();
      this.change(status,status.textContent);const prior=[prev.disabled,next.disabled];
      this.restore.push(()=>{prev.disabled=prior[0];next.disabled=prior[1];});
      steps.forEach(step=>{const current=step.getAttribute('aria-current');this.restore.push(()=>{if(current===null)step.removeAttribute('aria-current');else step.setAttribute('aria-current',current);});});
      let index=0;
      const go=i=>{
        index=Math.max(0,Math.min(steps.length-1,i));this.globe.select(arcs[index].id);
        steps.forEach((step,k)=>{if(k===index)step.setAttribute('aria-current','step');else step.removeAttribute('aria-current');});
        prev.disabled=index===0;next.disabled=index===steps.length-1;
        status.textContent=`Etapa ${index+1} de ${steps.length}: ${arcs[index].label}. ${arcs[index].detail}`;
      };
      this.on(prev,'click',()=>go(index-1));this.on(next,'click',()=>go(index+1));
      // La lista nativa del globo y los botones del relato comparten la etapa.
      this.on(stage,'click',event=>{
        const button=event.target.closest('[data-route]');if(!button)return;
        const i=arcs.findIndex(arc=>arc.id===button.dataset.route);if(i>=0)go(i);
      });
      go(0);
    }
    destroy() {
      if(this.dead)return;this.dead=true;this.abort.abort();this.globe?.destroy();
      this.watch?.disconnect();this.marks?.destroy();this.panels?.forEach(p=>{p.watch?.disconnect();p.marks?.destroy();});
      this.parts.forEach(p=>p.remove());this.restore.reverse().forEach(fn=>fn());instances.delete(this.root);
    }
  }
  function init(root=document) {
    return [...(root.matches?.('[data-reporte]')?[root]:[]),...root.querySelectorAll('[data-reporte]')].map(e=>{
      if(instances.has(e))return instances.get(e);
      e.querySelector('[data-error-reporte]')?.remove();
      try {return new Reporte(e);}catch(error){const p=el('p','nota-vacio','No se pudo preparar esta pieza: '+error.message+' El contenido original sigue disponible.');p.dataset.errorReporte='';e.prepend(p);return null;}
    });
  }
  window.NotaReportes={init,get:e=>instances.get(e)};init();
})();
