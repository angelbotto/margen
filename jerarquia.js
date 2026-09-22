/* Bottifact · tabla jerárquica: filas de resumen que despliegan su detalle.
   La tabla sigue siendo la fuente: sin JS todo queda visible y legible. */
(() => {
  'use strict';
  const instances=new WeakMap(), NS='http://www.w3.org/2000/svg';
  const chevron=()=>{
    const svg=document.createElementNS(NS,'svg');
    svg.setAttribute('viewBox','0 0 24 24');svg.setAttribute('width','14');svg.setAttribute('height','14');
    svg.setAttribute('aria-hidden','true');svg.setAttribute('class','jerarquia-flecha');
    const p=document.createElementNS(NS,'path');
    p.setAttribute('d','m9 6 6 6-6 6');p.setAttribute('fill','none');
    p.setAttribute('stroke','currentColor');p.setAttribute('stroke-width','2');
    p.setAttribute('stroke-linecap','round');p.setAttribute('stroke-linejoin','round');
    svg.append(p);return svg;
  };
  function init(root=document) {
    const tables=[...(root.matches?.('[data-jerarquia]')?[root]:[]),...root.querySelectorAll('[data-jerarquia]')]
      .map(n=>n.matches('table')?n:n.querySelector('table')).filter(Boolean);
    return tables.map(table=>{
      if(instances.has(table))return instances.get(table);
      const abort=new AbortController(),grupos=new Map();
      table.classList.add('tabla-jerarquica');
      [...table.querySelectorAll('tr[data-de]')].forEach(row=>{
        const id=row.getAttribute('data-de');
        if(!grupos.has(id))grupos.set(id,[]);
        grupos.get(id).push(row);
        row.classList.add('fila-hija');
      });
      const cabezas=[...table.querySelectorAll('tr[data-grupo]')];
      cabezas.forEach(row=>{
        const id=row.getAttribute('data-grupo'),hijas=grupos.get(id)||[];
        if(!hijas.length)return;
        row.classList.add('fila-grupo');
        const celda=row.cells[0];if(!celda)return;
        const btn=document.createElement('button');
        btn.type='button';btn.className='jerarquia-toggle';
        btn.setAttribute('aria-expanded','false');
        // El nombre accesible dice qué se abre, no sólo «abrir».
        btn.setAttribute('aria-label','Ver el detalle de '+celda.textContent.trim());
        btn.append(chevron());
        const texto=document.createElement('span');
        texto.className='jerarquia-titulo';
        while(celda.firstChild)texto.append(celda.firstChild);
        btn.append(texto);celda.append(btn);
        const pintar=abierto=>{
          btn.setAttribute('aria-expanded',String(abierto));
          row.classList.toggle('abierta',abierto);
          hijas.forEach(h=>{h.hidden=!abierto;});
        };
        pintar(false);
        btn.addEventListener('click',()=>pintar(btn.getAttribute('aria-expanded')!=='true'),{signal:abort.signal});
      });
      // Filtro optativo: pastillas declaradas fuera de la tabla que dejan ver sólo un estado.
      // Al filtrar, los grupos con coincidencias se abren solos y los que no tienen desaparecen:
      // buscar «sin registrar» no debería obligar a abrir 35 fechas a mano.
      const caja=table.closest('[data-jerarquia]')||table.parentElement;
      const barra=caja?.querySelector('[data-jerarquia-filtros]');
      const cuenta=caja?.querySelector('[data-jerarquia-cuenta]');
      const col=Number(table.getAttribute('data-columna-filtro')??-1);
      const textoDe=row=>{const c=col>=0?row.cells[col]:row.cells[row.cells.length-1];return (c?.textContent||'').trim();};
      let filtro='';
      const aplicar=()=>{
        let visibles=0,gruposVisibles=0;
        cabezas.forEach(row=>{
          const hijas=grupos.get(row.getAttribute('data-grupo'))||[];
          const coinciden=filtro?hijas.filter(h=>textoDe(h)===filtro):hijas;
          const btn=row.querySelector('.jerarquia-toggle');
          row.hidden=filtro?coinciden.length===0:false;
          if(!row.hidden){gruposVisibles++;visibles+=coinciden.length;}
          hijas.forEach(h=>{h.hidden=row.hidden||(filtro?textoDe(h)!==filtro:btn?.getAttribute('aria-expanded')!=='true');});
          if(filtro&&btn&&!row.hidden){btn.setAttribute('aria-expanded','true');row.classList.add('abierta');}
        });
        if(cuenta)cuenta.textContent=filtro
          ? visibles+' de '+[...grupos.values()].flat().length+' · en '+gruposVisibles+' de '+cabezas.length+' grupos'
          : [...grupos.values()].flat().length+' registros en '+cabezas.length+' grupos';
      };
      if(barra){
        barra.querySelectorAll('[data-filtro]').forEach(btn=>{
          btn.addEventListener('click',()=>{
            filtro=btn.getAttribute('data-filtro')||'';
            barra.querySelectorAll('[data-filtro]').forEach(b=>b.setAttribute('aria-pressed',String(b===btn)));
            if(!filtro)cabezas.forEach(row=>{
              const btn2=row.querySelector('.jerarquia-toggle');
              if(btn2){btn2.setAttribute('aria-expanded','false');row.classList.remove('abierta');}
            });
            aplicar();
          },{signal:abort.signal});
        });
        aplicar();
      }
      const api={
        raiz:table, grupos:grupos.size, filtrar(v){filtro=v||'';aplicar();},
        abrirTodo:()=>table.querySelectorAll('.jerarquia-toggle[aria-expanded="false"]').forEach(b=>b.click()),
        cerrarTodo:()=>table.querySelectorAll('.jerarquia-toggle[aria-expanded="true"]').forEach(b=>b.click()),
        destroy(){
          abort.abort();
          table.querySelectorAll('tr[data-de]').forEach(r=>{r.hidden=false;r.classList.remove('fila-hija');});
          table.querySelectorAll('.jerarquia-toggle').forEach(b=>{
            const celda=b.parentElement,texto=b.querySelector('.jerarquia-titulo');
            if(texto)while(texto.firstChild)celda.insertBefore(texto.firstChild,b);
            b.remove();
          });
          table.querySelectorAll('tr[data-grupo]').forEach(r=>r.classList.remove('fila-grupo','abierta'));
          table.classList.remove('tabla-jerarquica');
          instances.delete(table);
        }
      };
      instances.set(table,api);return api;
    });
  }
  const get=node=>instances.get(node);
  window.NotaJerarquia={init,get};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>init());
  else init();
})();
