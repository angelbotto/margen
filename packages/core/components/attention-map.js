/* Margen · attention map: treemap squarified con área exactamente proporcional. Requiere chart-core.js.
   Lenguaje visual de la portada de cmrg.me (celdas planas, nombre serif y duración mono); conserva foco
   por celda, tooltip con el valor completo, controles por categoría y la tabla fuente. */
(()=>{'use strict';
 const G=window.MargenGraficas,instances=new WeakMap();
 // Partición binaria anterior, disponible con data-atencion-modo="particion".
 function partition(rows,x=0,y=0,w=1000,h=380){if(rows.length===1)return [{...rows[0],x,y,w,h}];const sum=rows.reduce((a,r)=>a+r.value,0);let acc=0,index=0;while(index<rows.length-1&&acc<sum/2){acc+=rows[index++].value;}const fraction=acc/sum,a=rows.slice(0,index),b=rows.slice(index);return w>=h?[...partition(a,x,y,w*fraction,h),...partition(b,x+w*fraction,y,w*(1-fraction),h)]:[...partition(a,x,y,w,h*fraction),...partition(b,x,y+h*fraction,w,h*(1-fraction))];}
 const MIN_SIDE=10,MIN_AREA=196;
 class AttentionMap{
  constructor(e){
   if(!G)throw Error('Incluye packages/core/components/chart-core.js antes de attention-map.js.');
   this.element=e;this.abort=new AbortController();const table=e.querySelector('table');
   if(!table?.tBodies[0]||table.tHead?.rows[0]?.cells.length!==2)throw Error('Falta tabla de áreas.');
   const th=table.tHead.rows[0].cells[1];
   this.rows=[...table.tBodies[0].rows].map((r,i)=>{const raw=r.cells[1]?.getAttribute('data-valor'),value=Number(raw);if(raw===null||!raw?.trim()||!Number.isFinite(value)||value<0||value>1e9)throw Error('Cantidad no negativa y finita requerida.');return {name:r.cells[0].textContent.trim(),value,index:i,context:r.querySelector('[data-contexto]')?.textContent.trim()||r.dataset.contexto||''};});
   this.total=this.rows.reduce((s,r)=>s+r.value,0);
   if(this.rows.some(r=>!r.name)||!this.total||this.rows.length>40||new Set(this.rows.map(r=>r.name)).size!==this.rows.length)throw Error('1–40 nombres únicos y total positivo.');
   this.lang=G.lang(e);this.words=G.words(this.lang);this.spec=G.specOf(th,e);this.unit=e.dataset.unidad||G.unitOf(th)||'';
   this.title=table.caption?.textContent.trim()||'Attention map';
   const make=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;};
   const title=make('h3','grafica-titulo',this.title);
   this.frame=make('div','atencion-marco');this.stage=make('div','grafica-caja atencion-caja atencion-v2');this.frame.append(this.stage);
   this.status=make('p','atencion-estado','Total: '+this.full(this.total)+'. Recorre las celdas con las flechas o elige una categoría.');this.status.setAttribute('role','status');
   this.controls=make('div','atencion-leyenda');this.controls.setAttribute('role','group');this.controls.setAttribute('aria-label','Consultar categorías del mapa');
   this.rows.forEach(r=>{const b=make('button','',(r.index+1)+'. '+r.name+' · '+this.full(r.value));b.type='button';b.dataset.categoria=r.index;b.dataset.audioHover='';b.setAttribute('aria-pressed','false');this.controls.append(b);});
   this.controls.addEventListener('click',event=>{const b=event.target.closest('[data-categoria]');if(b)this.select(+b.dataset.categoria);},{signal:this.abort.signal});
   const exporter=G.exporter(e,{table,title:this.title,getSvg:()=>this.chart});
   this.parts=[title,this.frame,this.controls,this.status,exporter];e.prepend(...this.parts);e.classList.add('nota-atencion');
   this.watch=G.responsive(this.frame,w=>this.draw(w));
   instances.set(e,this);
  }
  full(v){return G.format(v,this.spec,{lang:this.lang,unit:this.unit});}
  share(v){return G.format(v/this.total,'pct1',{lang:this.lang});}
  // Niveles de la etiqueta de valor, del más completo al más corto (como «3 days, 10 hours» → «3d 10h» → «3d»).
  levels(v){
   const p=G.parse(this.spec);
   if(p.kind==='duration')return ['long','short','min'].map(l=>G.format(v,{...p,level:l},{lang:this.lang}));
   return [this.full(v),G.format(v,'num1k',{lang:this.lang})+(this.unit?' '+this.unit:''),G.format(v,'num0k',{lang:this.lang})];
  }
  // Agrupa en «Otros» la cola mínima necesaria para que toda celda pintada sea visible e interactiva.
  layout(w,h){
   const positive=this.rows.filter(r=>r.value>0).sort((a,b)=>b.value-a.value||a.index-b.index);
   const narrow=w<640,rect=narrow?{w:h,h:w}:{w,h};
   const place=items=>this.element.dataset.atencionModo==='particion'?partition(items,0,0,rect.w,rect.h):G.squarify(items,rect);
   let grouped=[],tiles=place(positive);
   const tooSmall=t=>Math.min(t.w,t.h)<MIN_SIDE||t.w*t.h<MIN_AREA;
   // Solo se agrupa la cola que no se vería; «Otros» conserva su suma exacta aunque quede pequeño
   // (no se le inventa área) y una categoría visible nunca entra en él.
   if(tiles.filter(tooSmall).length>=2)for(let k=2;k<=positive.length;k++){
    const tail=positive.slice(-k),sum=tail.reduce((a,r)=>a+r.value,0);
    const name=this.rows.some(r=>r.name===this.words.others)?this.words.others+' agrupados':this.words.others;
    const next=place([...positive.slice(0,-k),{name:name+' ('+k+')',value:sum,index:-1,members:tail,context:''}]);
    if(next.filter(t=>!t.members).some(tooSmall))continue;
    grouped=tail;tiles=next;break;
   }
   if(narrow)tiles=tiles.map(t=>({...t,x:t.y,y:t.x,w:t.h,h:t.w}));
   this.grouped=new Set(grouped.map(r=>r.index));
   return tiles;
  }
  draw(width){
   const w=Math.min(1008,width),h=w<640?320:380;
   this.marks?.destroy();
   const svg=G.svg('svg',{class:'mg-svg',width:w,height:h,viewBox:`0 0 ${w} ${h}`,'aria-label':this.title+'. Cada área representa su parte del total de '+this.full(this.total)+'.'});
   svg.append(G.svg('title',{},this.title),G.svg('desc',{},'Treemap squarified; los valores exactos están en la tabla.'));
   this.stage.replaceChildren(svg);this.chart=svg;
   const nameFont=G.fontOf(svg,'atencion-nombre'),valueFont=G.fontOf(svg,'atencion-valor');
   this.tiles=this.layout(w,h);
   const items=this.tiles.map(t=>{
    const g=G.svg('g',{'data-categoria':t.index,'data-audio-hover':'',class:t.members?'atencion-otros':''});
    g.append(G.svg('rect',{x:t.x,y:t.y,width:t.w,height:t.h,class:'atencion-area','data-valor':t.value}));
    const pad=t.w<120||t.h<80?8:16,room=t.w-pad*2;
    // Nombre serif 18 y valor mono 11,5: completos, abreviados o ninguno; nunca fuera de la celda.
    if(t.h>=34&&room>=24){
     const name=G.fit(t.name,room,nameFont,3);
     if(name){
      g.append(G.svg('text',{x:t.x+pad,y:t.y+pad+16,class:'atencion-nombre'},name));
      const value=t.h>=pad+37?this.levels(t.value).find(v=>G.textWidth(v,valueFont)<=room):null;
      if(value)g.append(G.svg('text',{x:t.x+pad,y:t.y+pad+34,class:'atencion-valor'},value));
     }
    }
    svg.append(g);return g;
   });
   this.marks=G.marks(this.element,svg,{items,status:this.status,label:this.title,describe:i=>this.describe(this.tiles[i]),onSelect:i=>{if(i!==null)this.press(this.tiles[i].index);}});
   if(this.selected!==undefined)this.press(this.selected);
  }
  describe(t){
   if(t.members)return [t.name,this.full(t.value)+' · '+this.share(t.value)+' de '+this.full(this.total),...t.members.map(r=>r.name+': '+this.full(r.value))];
   return [t.name,this.full(t.value)+' · '+this.share(t.value)+' de '+this.full(this.total),t.context].filter(Boolean);
  }
  press(index){
   this.selected=index;
   this.controls.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(+b.dataset.categoria===index)));
   const target=this.grouped.has(index)?-1:index;
   this.chart.querySelectorAll('g[data-categoria]').forEach(g=>g.classList.toggle('atencion-elegida',+g.dataset.categoria===target));
  }
  select(index){
   const row=this.rows[index];if(!row)return;
   this.press(index);
   const where=row.value===0?' Sin área: su valor es 0.':this.grouped.has(index)?' Su área está dentro de «'+this.tiles.find(t=>t.members)?.name+'».':'';
   this.status.textContent=row.name+': '+this.full(row.value)+' · '+this.share(row.value)+' del total.'+where;
  }
  destroy(){this.watch.disconnect();this.marks?.destroy();this.abort.abort();this.parts.forEach(p=>p.remove());this.element.classList.remove('nota-atencion');instances.delete(this.element);}
 }
 function init(root=document){return [...(root.matches?.('[data-atencion]')?[root]:[]),...root.querySelectorAll('[data-atencion]')].map(e=>{if(instances.has(e))return instances.get(e);e.querySelector('[data-error-atencion]')?.remove();try{return new AttentionMap(e);}catch(error){const p=document.createElement('p');p.className='grafica-error';p.dataset.errorAtencion='';p.textContent='No se pudo construir el mapa: '+error.message;e.prepend(p);return null;}});}
 window.NotaAtencion={init,get:e=>instances.get(e),partition};init();
})();
