(()=>{
 'use strict';const results=[],check=(name,ok,detail)=>{results.push({name,ok:!!ok,detail});};
 const root=kind=>document.querySelector('[data-evidencia="'+kind+'"]'),get=kind=>NotaEvidencia.get(root(kind));
 check('Ocho instancias sin errores',document.querySelectorAll('[data-evidencia]').length===8&&[...document.querySelectorAll('[data-evidencia]')].every(e=>NotaEvidencia.get(e)?.model&&!NotaEvidencia.get(e)?.error));
 check('Sankey conserva 120 entre conexiones',get('sankey').model.total===120);
 const paths=root('sankey').querySelectorAll('.ev-flujo');check('Sankey: grosor 65/5 = 13',Math.abs(Number(paths[0].getAttribute('stroke-width'))/Number(paths[5].getAttribute('stroke-width'))-13)<1e-8);
 check('Cohorte conserva base y pendiente',get('cohortes').model.data[1].base===100&&get('cohortes').model.data[1].values[3]===null&&get('cohortes').model.data[0].values[3]===72);
 get('cohortes').select(3);check('Porcentaje de cohorte sobre su base',root('cohortes').querySelector('.evidencia-detalle').textContent.match(/60\s?%/));
 check('Sensibilidad permite impacto inverso',get('sensibilidad').model.data.find(d=>d.name==='Combustible').a===106&&get('sensibilidad').model.base===100);
 check('Gantt conserva hito y dos dependencias',get('gantt').model.data[4].start===get('gantt').model.data[4].end&&get('gantt').model.data[4].deps.length===2);
 get('embudo').select(3);const funnel=root('embudo').querySelector('.evidencia-detalle').textContent;check('Embudo 450/1000 y 450/500',/45\s?%/.test(funnel)&&/90\s?%/.test(funnel)&&funnel.includes('50 pedidos'),funnel);
 check('Banda alcanza ambos extremos',get('incertidumbre').model.domain[0]<=80&&get('incertidumbre').model.domain[1]>=180);
 const snapshot=root('sensibilidad').querySelector('table').outerHTML;root('sensibilidad').querySelector('select').value='2';root('sensibilidad').querySelector('select').dispatchEvent(new Event('change'));check('Selección cambia detalle y conserva datos',get('sensibilidad').selected===2&&root('sensibilidad').querySelector('table').outerHTML===snapshot);
 root('sensibilidad').querySelector('button').click();check('Restablecer consulta',get('sensibilidad').selected===0);
 root('relato').querySelector('.relato-pasos li:nth-child(2) button').click();check('Paso manual detiene seguimiento',get('relato').selected===1&&root('relato').querySelector('input[type=checkbox]').checked);
 const image=root('imagen'),zoom=image.querySelector('[aria-label="Ampliar imagen"]');for(let i=0;i<10;i++)zoom.click();check('Zoom acotado a 400 %',get('imagen').model.zoom===4);get('imagen').select(1);check('Imagen selecciona una zona y desplaza localmente',get('imagen').selected===1&&image.querySelector('.ev-imagen-visor').scrollLeft>0);image.querySelector('[aria-label="Ajustar imagen"]').click();check('Ajustar vuelve a 100 %',get('imagen').model.zoom===1);
 function variant(kind,mutate,valid=false,extra){const copy=root(kind).cloneNode(true);copy.querySelector('.evidencia-ui').remove();copy.removeAttribute('id');copy.querySelectorAll('[id]').forEach(e=>e.removeAttribute('id'));copy.querySelector('[data-evidencia-imagen]')?.removeAttribute('hidden');mutate(copy);document.body.append(copy);const instance=NotaEvidencia.init(copy)[0];const ok=valid?!instance.error:!!instance.error;check('Validación '+kind+': '+(extra||mutate.name),ok,instance.error||null);if(valid){check('Geometría finita '+kind,!copy.querySelector('svg')?.outerHTML.match(/(?:NaN|Infinity)/));const bad=[...copy.querySelectorAll('.evidencia-visor svg')].flatMap(s=>[...s.querySelectorAll('text')].filter(t=>{const b=t.getBBox(),v=s.viewBox.baseVal;return b.x < -1||b.y < -1||b.x+b.width>v.width+1||b.y+b.height>v.height+1;}));check('Rótulos completos '+kind,bad.length===0,bad.map(t=>t.textContent));}instance.destroy();check('Destroy conserva fuente '+kind,!copy.querySelector('.evidencia-ui')&&!!copy.querySelector('table,[data-evidencia-zonas]')&&!NotaEvidencia.get(copy));copy.remove();}
 const set=(r,row,col,value)=>{const c=r.querySelectorAll('tbody tr')[row].cells[col];c.dataset.valor=value;c.textContent=value;};
 variant('sankey',r=>r.removeAttribute('data-unidad'),false,'unidad ausente');
 variant('sankey',r=>r.append(r.querySelector('table').cloneNode(true)),false,'tabla duplicada');
 variant('sankey',r=>{for(let i=0;i<6;i++)set(r,i,2,.000001);},true,'magnitudes pequeñas');
 const axisDates=[...root('gantt').querySelectorAll('svg text')].filter(t=>/^2026-/.test(t.textContent));const gd=get('gantt').model.domain;
 check('Fechas del eje coinciden con coordenadas UTC',axisDates.every(t=>Math.abs(Number(t.getAttribute('x'))-(300+(Date.parse(t.textContent+'T00:00:00Z')-gd[0])/(gd[1]-gd[0])*610))<.001));
 variant('sankey',r=>set(r,0,2,-1),false,'negativo');variant('sankey',r=>{for(let i=0;i<6;i++)set(r,i,2,0);},false,'total cero');variant('sankey',r=>set(r,5,2,0),true,'flujo cero');
 variant('cohortes',r=>set(r,0,1,0),false,'base cero');variant('cohortes',r=>set(r,0,3,121),false,'supera base');variant('cohortes',r=>{const c=r.querySelector('tbody tr').cells[3];c.dataset.estado='pendiente';},false,'observado tras pendiente');variant('cohortes',r=>set(r,0,5,0),true,'cero observado');
 variant('gantt',r=>{r.querySelector('tbody tr').cells[2].textContent='2026-02-30';},false,'fecha inexistente');variant('gantt',r=>{r.querySelector('tbody tr').cells[6].textContent='Z';},false,'dependencia ausente');variant('gantt',r=>{r.querySelector('tbody tr').cells[6].textContent='E';},false,'dependencia futura');
 variant('gantt',r=>{for(const row of r.querySelectorAll('tbody tr')){row.cells[2].textContent=row.cells[3].textContent='2026-09-01';}r.querySelector('tbody tr').cells[6].textContent='E';},false,'ciclo');
 variant('embudo',r=>set(r,1,1,1001),false,'etapa creciente');variant('embudo',r=>{set(r,1,1,0);set(r,2,1,0);set(r,3,1,0);},true,'ceros al final');
 variant('incertidumbre',r=>set(r,0,1,110),false,'intervalo invertido');variant('incertidumbre',r=>r.querySelector('[data-evidencia-metodo]').remove(),false,'sin metodología');variant('incertidumbre',r=>{r.querySelectorAll('tbody tr')[1].cells[0].textContent='2026-10-01';},false,'fecha duplicada');
 variant('imagen',r=>{r.querySelector('[data-evidencia-zonas] li').dataset.x=101;},false,'zona fuera de imagen');
 variant('sankey',r=>{r.querySelector('tbody tr').cells[0].textContent='Una categoría con un nombre bastante largo que necesita varias líneas para conservar el contexto';},true,'nombre largo');
 variant('cohortes',r=>{set(r,0,1,1e12);for(let i=2;i<6;i++)set(r,0,i,1e12);},true,'base grande');
 variant('gantt',r=>{r.querySelector('tbody tr').cells[1].textContent='Una tarea con un nombre bastante largo que debe conservarse completo al consultar el calendario';},true,'tarea larga');
 variant('incertidumbre',r=>{set(r,0,1,-1e12);set(r,0,2,0);set(r,0,3,1e12);},true,'extremos grandes y negativos');
 for(const el of document.querySelectorAll('[data-evidencia]')){const i=NotaEvidencia.get(el);NotaEvidencia.init(el);check('Init idempotente '+el.dataset.evidencia,NotaEvidencia.get(el)===i&&el.querySelectorAll('.evidencia-ui').length===1);}
 return {results,passed:results.filter(r=>r.ok).length,failed:results.filter(r=>!r.ok).length};
})()
