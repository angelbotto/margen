/* Bottifact · evidencia espacial. Requiere Three.js 0.160.1, incluido UNA sola vez.
   Tabla de datos permanente; una instancia por figura; sin texturas externas. */
(() => {
  'use strict';
  // Three.js se pide al acercarse a la vista, una vez por documento; sin red queda el respaldo legible.
  const tres=window.NotaTres||(window.NotaTres=(()=>{const src='https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.1/three.min.js',sri='sha512-vnmn/Qqn6aG0POAc9mIGzjq0IybrvxJXYDafNvp9JSnDGxeF3pbkSqLvf+YGd5ku63pT7sa/jxHn7/d0mU8+tA==';let pending=null;
   const load=()=>window.THREE?Promise.resolve(window.THREE):pending||(pending=new Promise((ok,fail)=>{const s=document.createElement('script');s.src=src;s.integrity=sri;s.crossOrigin='anonymous';s.async=true;s.onload=()=>window.THREE?ok(window.THREE):fail(new Error('Three.js no disponible'));s.onerror=()=>{pending=null;s.remove();fail(new Error('Three.js no disponible sin conexión'));};(document.head||document.documentElement).append(s);}));
   return el=>window.THREE?Promise.resolve(window.THREE):new Promise(near=>{if(!('IntersectionObserver' in window))return near();const io=new IntersectionObserver(es=>{if(es.some(e=>e.isIntersecting)){io.disconnect();near();}},{rootMargin:'400px 0px'});io.observe(el);}).then(load);})());
  const instances=new WeakMap();
  const node=(tag,cls,text)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e;};
  const format=n=>new Intl.NumberFormat('es-CO',{maximumSignificantDigits:4,notation:Math.abs(n)>=1e6||(n!==0&&Math.abs(n)<.001)?'scientific':'standard'}).format(n);
  const extent=values=>{let min=Math.min(...values),max=Math.max(...values);if(min===max){const p=Math.abs(min)*.1||1;min-=p;max+=p;}if(!Number.isFinite(max-min))throw new TypeError('Dominio fuera de precisión.');return [min,max];};
  function read(element){
    const type=element.dataset.escena,table=element.querySelector('table');
    if(!['xyz','etapas','columnas','arcos','almacen'].includes(type)||!table?.tHead||!table.tBodies[0])throw new TypeError('Se necesita una tabla y un tipo de escena válido.');
    const heads=[...table.tHead.rows[0].cells].map(c=>c.textContent.trim());
    const columns={xyz:4,etapas:3,columnas:4,arcos:6,almacen:5};
    if(heads.length!==columns[type])throw new TypeError('La escena '+type+' necesita '+columns[type]+' columnas, incluida la etiqueta.');
    const data=[...table.tBodies[0].rows].map(row=>{
      if(row.cells.length!==heads.length)throw new TypeError('Fila incompleta.');
      const values=[...row.cells].slice(1,type==='etapas'?2:columns[type]).map(c=>{
        const raw=c.getAttribute('data-valor'),n=Number(raw);
        if(raw===null||raw.trim()===''||!Number.isFinite(n))throw new TypeError('Coordenada o duración inválida.');return n;
      });
      if(type==='etapas'&&values[0]<0)throw new TypeError('La duración no puede ser negativa.');
      return {label:row.cells[0].textContent.trim(),values,detail:type==='etapas'?row.cells[2].textContent.trim():''};
    });
    if(['columnas','arcos'].includes(type)){
      if(!window.NotaGeografia)throw new TypeError('Incluye packages/core/components/geography.js antes de packages/core/components/scene.js.');
      data.forEach(r=>{NotaGeografia.check(r.values[0],r.values[1]);if(type==='arcos')NotaGeografia.check(r.values[2],r.values[3]);if(r.values.at(-1)<0)throw new TypeError('Volumen negativo.');});
    }
    if(type==='almacen'&&data.some(r=>r.values[2]<0||r.values[3]<=0||r.values[2]>r.values[3]))throw new TypeError('Ocupación entre cero y capacidad positiva.');
    if(!data.length||data.length>(type==='xyz'?100:12))throw new TypeError('XYZ admite 1–100 puntos; las demás escenas, 1–12 registros.');
    return {type,table,heads,data,title:table.caption?.textContent||'Vista espacial'};
  }
  class NotaEscena {
    constructor(element){
      if(instances.has(element))throw new TypeError('Ya existe una escena en esta figura.');
      this.model=read(element);this.element=element;this.parts=[];this.dead=false;this.visible=false;
      this.frame=0;this.frames=0;this.last=0;this.rotating=false;this.lost=false;
      this.phi=0;this.theta=0;this.selected=null;this.resources=new Set();this.abort=new AbortController();
      this.motion=matchMedia('(prefers-reduced-motion: reduce)');this.scheme=matchMedia('(prefers-color-scheme: dark)');
      this.buildDOM();
      this.listen(this.motion,'change',()=>{this.stop();this.sync();this.draw();this.start();});
      this.listen(this.scheme,'change',()=>this.theme());
      this.listen(document,'nota:tema',()=>this.theme());
      this.listen(document,'visibilitychange',()=>{this.stop();if(!document.hidden){this.draw();this.start();}});
      this.mutation=new MutationObserver(()=>this.theme());this.mutation.observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
      this.intersection=new IntersectionObserver(entries=>{this.visible=entries[0].isIntersecting;this.stop();if(this.visible){this.fit();this.start();}});this.intersection.observe(element);
      const unavailable=()=>{this.error.textContent='La vista 3D no está disponible. La tabla conserva todos los datos.';this.error.hidden=false;this.stage.hidden=true;this.controls.hidden=true;this.releaseRenderer();};
      if(window.THREE){try {this.init();} catch(error){unavailable();}}
      else {
        element.dataset.tres='cargando';
        tres(element).then(()=>{if(this.dead)return;delete element.dataset.tres;try{this.init();this.sync();this.draw();this.start();}catch(error){unavailable();}},()=>{if(!this.dead){delete element.dataset.tres;unavailable();}});
      }
      this.sync();instances.set(element,this);
      document.fonts?.ready.then(()=>{if(!this.dead)this.theme();});
    }
    listen(target,type,fn){target.addEventListener(type,fn,{signal:this.abort.signal});}
    buildDOM(){
      this.element.classList.add('nota-escena');
      const title=node('h3','grafica-titulo',this.model.title);
      this.error=node('p','grafica-error');this.error.hidden=true;
      this.stage=node('div','escena-caja');this.stage.tabIndex=0;this.stage.setAttribute('role','region');this.stage.setAttribute('aria-label',this.model.title+', vista 3D desplazable');
      this.canvas=node('canvas');this.canvas.setAttribute('role','img');this.canvas.setAttribute('aria-label',this.model.title+'. Los valores y las unidades están en la tabla; usa los botones para cambiar la vista.');this.stage.append(this.canvas);
      this.controls=node('div','escena-controles');
      const left=node('button','','← Girar'),right=node('button','','Girar →'),up=node('button','','Inclinar'),reset=node('button','','Vista inicial');
      this.pauseButton=node('button','','Activar giro');this.pauseButton.setAttribute('aria-pressed','false');
      [left,right,up,reset,this.pauseButton].forEach(b=>{b.type='button';this.controls.append(b);});
      this.listen(left,'click',()=>this.rotate(-.25,0));this.listen(right,'click',()=>this.rotate(.25,0));
      this.listen(up,'click',()=>{this.theta=this.theta>.8?.2:this.theta+.2;this.draw();});
      this.listen(reset,'click',()=>{this.phi=0;this.theta=0;this.draw();});
      this.listen(this.pauseButton,'click',()=>{this.rotating=!this.rotating;this.stop();this.sync();this.start();});
      this.status=node('p','',this.model.type==='xyz'?'Tres variables, tres ejes. La tabla permite consultar cada punto.':this.model.type==='etapas'?'La altura representa duración; el orden horizontal representa la secuencia.':'Elige una ubicación o conexión; sus valores completos aparecen aquí.');this.status.setAttribute('role','status');
      this.selection=node('div','escena-controles');this.selection.setAttribute('role','group');this.selection.setAttribute('aria-label','Seleccionar registro');
      this.model.data.forEach((row,i)=>{const b=node('button','',(['columnas','arcos','almacen'].includes(this.model.type)?(i+1)+'. ':'')+row.label);b.type='button';b.dataset.registro=i;b.setAttribute('aria-pressed','false');this.listen(b,'click',()=>this.select(this.selected===i?null:i));this.selection.append(b);});
      const axes=node('p','secundario',this.model.type==='xyz'?this.model.heads.slice(1).map((h,i)=>['X','Y','Z'][i]+': '+h).join(' · '):this.model.type==='etapas'?'Altura: '+this.model.heads[1]:this.model.type==='arcos'?'Arcos: conexión directa, no vía terrestre. Sección del tubo proporcional a viajes; elevación constante para separar rutas.':this.model.type==='columnas'?'X/Z: longitud/latitud. Altura: '+this.model.heads[3]+'. Contorno Natural Earth 1:110m.':'X/Z: posición en metros. Altura sólida: ocupación. Contorno: capacidad en la misma escala.');
      this.parts=[title,this.error,this.stage,axes,this.controls,this.status,this.selection];
      const before=this.element.firstChild;this.parts.forEach(e=>this.element.insertBefore(e,before));
      this.listen(this.canvas,'webglcontextlost',e=>{e.preventDefault();this.lost=true;this.stop();this.error.hidden=false;this.error.textContent='Vista 3D suspendida. Consulta la tabla.';});
      this.listen(this.canvas,'webglcontextrestored',()=>queueMicrotask(()=>{if(this.dead)return;this.lost=false;this.error.hidden=true;this.draw();this.start();}));
    }
    keep(resource){this.resources.add(resource);return resource;}
    init(){
      if(!window.THREE)throw new Error('Three.js no disponible');
      this.renderer=new THREE.WebGLRenderer({canvas:this.canvas,antialias:true,alpha:true,preserveDrawingBuffer:true});
      this.renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));this.renderer.setClearColor(0,0);
      this.scene=new THREE.Scene();this.camera=new THREE.OrthographicCamera(-4,4,3,-3,.1,100);
      this.camera.position.set(5,4,7);this.camera.lookAt(0,0,0);this.items=[];this.labels=[];this.lines=[];
      this.group=new THREE.Group();this.scene.add(this.group);
      this.buildGeometry();this.theme();
      this.resize=new ResizeObserver(()=>this.fit());this.resize.observe(this.stage);this.fit();
    }
    line(from,to){
      const geometry=this.keep(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(...from),new THREE.Vector3(...to)]));
      const material=this.keep(new THREE.LineBasicMaterial());const line=new THREE.Line(geometry,material);this.group.add(line);this.lines.push(line);
    }
    text(text,position,size=.3){
      const canvas=document.createElement('canvas');canvas.width=768;canvas.height=96;
      const texture=this.keep(new THREE.CanvasTexture(canvas)),material=this.keep(new THREE.SpriteMaterial({map:texture,transparent:true,depthTest:false}));
      texture.colorSpace=THREE.SRGBColorSpace;
      const sprite=new THREE.Sprite(material);sprite.scale.set(size*8,size,1);sprite.position.set(...position);
      this.group.add(sprite);this.labels.push({sprite,canvas,texture,text});
    }
    buildGeometry(){
      const {type,data,heads}=this.model;
      if(['columnas','arcos','almacen'].includes(type)){this.buildSpatial();return;}
      if(type==='xyz'){
        this.domains=[0,1,2].map(i=>extent(data.map(r=>r.values[i])));
        const map=(v,i)=>-1+(v-this.domains[i][0])/(this.domains[i][1]-this.domains[i][0])*2;
        for(let axis=0;axis<3;axis++){
          const from=axis===0?[-1,-1.15,1.15]:axis===1?[-1.15,-1,-1.15]:[1.15,-1.15,-1];
          const to=[...from];to[axis]=1.12;this.line(from,to);
          for(let tick=0;tick<=2;tick++){
            const value=this.domains[axis][0]+(this.domains[axis][1]-this.domains[axis][0])*tick/2;
            const p=[...from];p[axis]=map(value,axis);
            if(axis===0)p[2]+=.5;else if(axis===2)p[0]+=.5;else p[0]-=.28;
            this.text(format(value),p,.28);
          }
          const p=axis===0?[0,-1.9,1.15]:axis===1?[-1.15,1.45,-1.15]:[1.15,-1.9,0];
          this.text(['X','Y','Z'][axis],p,.32);
        }
        data.forEach((r,i)=>{
          const geometry=this.keep(new THREE.SphereGeometry(.045,12,8));
          const material=this.keep(new THREE.MeshBasicMaterial());const mesh=new THREE.Mesh(geometry,material);
          mesh.position.set(...r.values.map(map));mesh.userData.index=i;this.group.add(mesh);this.items.push(mesh);
        });
      }else{
        const max=Math.max(...data.map(r=>r.values[0]))||1;this.domains=[[0,data.length-1],[0,max],[0,1]];
        const sx=i=>data.length===1?0:-1.5+i/(data.length-1)*3,sy=value=>value/max*2;
        this.line([-1.85,-1,0],[-1.85,1.1,0]);
        for(let tick=0;tick<=4;tick++){const v=max*tick/4,y=-1+sy(v);this.text(format(v),[-2.08,y,0],.28);this.line([-1.85,y,0],[1.8,y,0]);}
        this.text('Duración',[-1.85,1.7,0],.32);
        data.forEach((r,i)=>{
          const height=sy(r.values[0]);
          const material=this.keep(new THREE.MeshBasicMaterial());
          // Cero produce altura cero: no se infla la caja para darle visibilidad falsa.
          const mesh=new THREE.Mesh(this.keep(new THREE.BoxGeometry(Math.min(.4,2.4/data.length),height,.22)),material);
          mesh.position.set(sx(i),-1+height/2,0);mesh.userData.index=i;this.group.add(mesh);this.items.push(mesh);
          this.text(String(i+1),[sx(i),-1.3,0],.28);this.text(format(r.values[0]),[sx(i),-1+height+.3,0],.28);
        });
        this.text('Etapas en orden →',[0,-1.8,0],.32);
      }
    }
    buildSpatial(){
      const {type,data,heads}=this.model;
      const max=Math.max(...data.map(r=>r.values.at(-1)))||1;
      this.domains=[[0,max]];
      const base=-1.1,sy=v=>v/max*1.8;
      const mesh=(geometry,position,i)=>{const m=new THREE.Mesh(this.keep(geometry),this.keep(new THREE.MeshBasicMaterial()));m.position.set(...position);m.userData.index=i;this.group.add(m);this.items.push(m);return m;};
      if(type!=='almacen'){
        NotaGeografia.colombia.coordinates.forEach(ring=>{const points=ring.map(([lon,lat])=>{const[x,z]=NotaGeografia.project(lat,lon);return new THREE.Vector3(x,base,z);});const l=new THREE.Line(this.keep(new THREE.BufferGeometry().setFromPoints(points)),this.keep(new THREE.LineBasicMaterial()));this.group.add(l);this.lines.push(l);});
        this.text('N',[1.35,base,-2.02],.25);
        this.line([1.35,base,-1.1],[1.35,base,-1.8]);
        this.line([1.23,base,-1.6],[1.35,base,-1.8]);this.line([1.47,base,-1.6],[1.35,base,-1.8]);
        data.forEach((r,i)=>{
          const [lat,lon]=r.values,[x,z]=NotaGeografia.project(lat,lon),value=r.values.at(-1);
          if(type==='columnas'){
            const h=sy(value);mesh(new THREE.BoxGeometry(.11,h,.11),[x,base+h/2,z],i);this.text(String(i+1),[x,base+h+.2,z],.24);
          }else{
            const [x2,z2]=NotaGeografia.project(r.values[2],r.values[3]);
            const curve=new THREE.QuadraticBezierCurve3(new THREE.Vector3(x,base,z),new THREE.Vector3((x+x2)/2,1,(z+z2)/2),new THREE.Vector3(x2,base,z2));
            mesh(new THREE.TubeGeometry(curve,40,Math.sqrt(value/max)*.035,8,false),[0,0,0],i);
            this.text(String(i+1),[x2,base+.2,z2],.24);
          }
        });
        if(type==='arcos'){this.text('Volumen máximo: '+format(max),[0,-1.9,0],.26);return;}
      }else{
        const xd=extent(data.map(r=>r.values[0])),zd=extent(data.map(r=>r.values[1]));
        this.positionDomains=[xd,zd];
        // X y Z comparten metros: conservar la proporción física de la planta.
        const span=Math.max(xd[1]-xd[0],zd[1]-zd[0]);
        const sx=v=>(v-(xd[0]+xd[1])/2)/span*2.4,sz=v=>(v-(zd[0]+zd[1])/2)/span*2.4;
        data.forEach((r,i)=>{
          const [x,z,used,capacity]=r.values,h=sy(used),ch=sy(capacity);
          mesh(new THREE.BoxGeometry(.28,h,.28),[sx(x),base+h/2,sz(z)],i);
          const box=this.keep(new THREE.BoxGeometry(.29,ch,.29)),edges=this.keep(new THREE.EdgesGeometry(box));
          const outline=new THREE.LineSegments(edges,this.keep(new THREE.LineBasicMaterial()));outline.position.set(sx(x),base+ch/2,sz(z));this.group.add(outline);this.lines.push(outline);
          this.text(String(i+1),[sx(x),base-.25,sz(z)],.24);
        });
        this.line([sx(xd[0]),base,sz(zd[1])+.5],[sx(xd[1]),base,sz(zd[1])+.5]);this.text('X '+format(xd[0])+'–'+format(xd[1])+' m',[0,base-.55,1.7],.23);
        this.line([sx(xd[1])+.5,base,sz(zd[0])],[sx(xd[1])+.5,base,sz(zd[1])]);this.text('Z '+format(zd[0])+'–'+format(zd[1])+' m',[1.7,base-.55,0],.23);
      }
      this.line([-1.9,base,0],[-1.9,base+1.8,0]);
      [0,.5,1].forEach(t=>this.text(format(t*max),[-2.15,base+t*1.8,0],.24));
      this.text(type==='columnas'?heads[3]:heads[4],[-1.6,1.25,0],.25);
    }
    color(raw){const c=document.createElement('canvas').getContext('2d');c.fillStyle=raw;c.fillRect(0,0,1,1);const [r,g,b]=c.getImageData(0,0,1,1).data;return new THREE.Color().setRGB(r/255,g/255,b/255,THREE.SRGBColorSpace);}
    theme(){
      if(!this.renderer||this.dead)return;
      const css=getComputedStyle(this.element);this.colors=[1,2,3].map(i=>this.color(css.getPropertyValue('--escena-'+i)));
      const ink=css.getPropertyValue('--escena-tinta').trim(),line=this.color(css.getPropertyValue('--escena-linea'));
      this.lines.forEach(l=>l.material.color.copy(line));
      this.labels.forEach(({canvas,texture,text})=>{const ctx=canvas.getContext('2d');ctx.clearRect(0,0,768,96);ctx.font='72px '+css.getPropertyValue('--mono');ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle=ink;ctx.fillText(text,384,48,750);texture.needsUpdate=true;});
      this.colorItems();this.draw();
    }
    colorItems(){if(!this.items)return;this.items.forEach((mesh,i)=>{mesh.material.color.copy(this.colors[this.model.type==='xyz'?0:i%3]);mesh.material.transparent=this.selected!==null&&i!==this.selected;mesh.material.opacity=this.selected===null||i===this.selected?1:.28;});}
    select(index){
      if(index!==null&&(!Number.isInteger(index)||index<0||index>=this.model.data.length))throw new TypeError('Registro desconocido.');
      this.selected=index;this.selection.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.registro)===index)));
      const r=this.model.data[index];this.status.textContent=r?r.label+': '+r.values.map((v,i)=>this.model.heads[i+1]+' '+format(v)).join(' · ')+(r.detail?' · '+r.detail:''):'Todos los registros.';
      this.colorItems();this.draw();
    }
    fit(){
      if(!this.renderer||this.dead)return;
      // Mantiene un lienzo legible de 600 px, desplazable en un teléfono.
      const width=Math.max(600,Math.round(this.stage.clientWidth)),height=440;
      this.renderer.setSize(width,height,false);this.canvas.style.aspectRatio=width+'/'+height;
      const aspect=width/height,extent=2.7;
      this.camera.left=-extent*aspect;this.camera.right=extent*aspect;this.camera.top=extent;this.camera.bottom=-extent;this.camera.updateProjectionMatrix();this.draw();
    }
    draw(){
      if(!this.renderer||this.dead||this.lost||!this.visible||document.hidden)return;
      this.group.rotation.set(this.theta,this.phi,0);this.renderer.render(this.scene,this.camera);this.frames++;
    }
    rotate(dx,dy=0){this.phi+=dx;this.theta=Math.max(-.7,Math.min(1.1,this.theta+dy));this.draw();}
    sync(){this.pauseButton.disabled=this.motion.matches;this.pauseButton.setAttribute('aria-pressed',String(this.rotating&&!this.motion.matches));this.pauseButton.textContent=this.motion.matches?'Giro desactivado por preferencia':this.rotating?'Pausar giro':'Activar giro';}
    pause(){this.rotating=false;this.stop();this.sync();}
    resume(){this.rotating=true;this.sync();this.start();}
    stop(){cancelAnimationFrame(this.frame);this.frame=0;this.last=0;}
    start(){if(this.frame||!this.renderer||!this.visible||this.dead||this.lost||this.motion.matches||!this.rotating||document.hidden)return;this.frame=requestAnimationFrame(t=>this.tick(t));}
    tick(time){this.frame=0;const dt=this.last?Math.min((time-this.last)/1000,.05):0;this.last=time;this.phi+=dt*.15;this.draw();this.start();}
    releaseRenderer(){this.stop();this.resources.forEach(r=>r.dispose());this.resources.clear();this.renderer?.dispose();this.renderer=null;}
    destroy(){if(this.dead)return;this.dead=true;this.stop();this.abort.abort();this.intersection.disconnect();this.mutation.disconnect();this.resize?.disconnect();this.releaseRenderer();this.parts.forEach(e=>e.remove());this.element.classList.remove('nota-escena');instances.delete(this.element);}
  }
  function init(root=document){return [...(root.matches?.('[data-escena]')?[root]:[]),...root.querySelectorAll('[data-escena]')].map(el=>{
    if(instances.has(el))return instances.get(el);
    try{return new NotaEscena(el);}catch(error){let p=el.querySelector('[data-error-escena]');if(!p){p=node('p','grafica-error');p.dataset.errorEscena='';el.prepend(p);}p.textContent='No se pudo construir la escena: '+error.message;return null;}
  });}
  window.NotaEscena=NotaEscena;NotaEscena.init=init;NotaEscena.get=e=>instances.get(e);init();
})();
