/* NotaFlota: globo operativo local. Datos ficticios y reproducción explícita, sin GPS ni red. */
(()=>{
 'use strict';
  // Three.js se pide al acercarse a la vista, una vez por documento; sin red queda el respaldo legible.
  const tres=window.NotaTres||(window.NotaTres=(()=>{const src='https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.1/three.min.js',sri='sha512-vnmn/Qqn6aG0POAc9mIGzjq0IybrvxJXYDafNvp9JSnDGxeF3pbkSqLvf+YGd5ku63pT7sa/jxHn7/d0mU8+tA==';let pending=null;
   const load=()=>window.THREE?Promise.resolve(window.THREE):pending||(pending=new Promise((ok,fail)=>{const s=document.createElement('script');s.src=src;s.integrity=sri;s.crossOrigin='anonymous';s.async=true;s.onload=()=>window.THREE?ok(window.THREE):fail(new Error('Three.js no disponible'));s.onerror=()=>{pending=null;s.remove();fail(new Error('Three.js no disponible sin conexión'));};(document.head||document.documentElement).append(s);}));
   return el=>window.THREE?Promise.resolve(window.THREE):new Promise(near=>{if(!('IntersectionObserver' in window))return near();const io=new IntersectionObserver(es=>{if(es.some(e=>e.isIntersecting)){io.disconnect();near();}},{rootMargin:'400px 0px'});io.observe(el);}).then(load);})());
 const instances=new WeakMap(),node=(tag,cls,text)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e;};
 const vector=(lat,lon,r=1)=>{const a=lat*Math.PI/180,b=lon*Math.PI/180;return new THREE.Vector3(Math.cos(a)*Math.cos(b)*r,Math.sin(a)*r,-Math.cos(a)*Math.sin(b)*r);};
 const truck='<svg viewBox="0 0 36 26" aria-hidden="true"><path d="M3 5h18v14H3zM21 10h7l5 6v3H21z"/><path d="M24 12h3l3 4h-6z" class="flota-ventana"/><circle cx="10" cy="20" r="3"/><circle cx="27" cy="20" r="3"/></svg>';
 const fmt=n=>new Intl.NumberFormat('es-CO',{maximumFractionDigits:0}).format(n);
 function read(e){
  const table=e.querySelector('table'),rows=[...(table?.tBodies[0]?.rows||[])];
  if(!rows.length||rows.length>12)throw Error('Se esperan de 1 a 12 vehículos.');
  const ids=new Set(),cities=new Map();
  const data=rows.map(row=>{
   if(row.cells.length!==9)throw Error('Cada vehículo requiere nueve columnas.');
   const c=[...row.cells],id=c[0].textContent.trim(),point=cell=>{
    const lat=Number(cell.dataset.lat),lon=Number(cell.dataset.lon),name=cell.textContent.trim();
    if(!name||!cell.dataset.lat||!cell.dataset.lon||!Number.isFinite(lat)||!Number.isFinite(lon)||lat < -5||lat >14||lon < -80||lon >-66)throw Error('Ciudad y coordenadas válidas de Colombia requeridas.');
    const p={name,lat,lon};if(cities.has(name)&&(cities.get(name).lat!==lat||cities.get(name).lon!==lon))throw Error('Ciudad con coordenadas inconsistentes.');cities.set(name,p);return p;
   };
   if(!id||ids.has(id))throw Error('Identificadores de vehículo únicos.');ids.add(id);
   const from=point(c[1]),to=point(c[2]),progress=Number(c[3].dataset.valor),orders=Number(c[4].dataset.valor),status=c[5].textContent.trim(),time=c[6].querySelector('time')?.dateTime;
   if(!c[3].dataset.valor||!c[4].dataset.valor||!Number.isFinite(progress)||progress<0||progress>100||!Number.isInteger(orders)||orders<0||orders>10000||!['En ruta','Con novedad','Entregado'].includes(status)||!time||!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})$/.test(time)||!Number.isFinite(Date.parse(time)))throw Error('Avance, pedidos, estado u hora de corte inválidos.');
   if(from.lat===to.lat&&from.lon===to.lon)throw Error('Origen y destino deben ser distintos.');
   if(status==='Entregado'&&progress!==100)throw Error('Una entrega completada requiere avance 100.');
   return {id,from,to,progress,orders,status,time,note:c[7].textContent.trim(),next:c[8].textContent.trim()};
  });
  return {data,cities:[...cities.values()]};
 }
 class Fleet{
  constructor(element){
   this.model=read(element);this.element=element;this.abort=new AbortController();this.parts=[];this.dead=false;this.frame=0;this.frames=0;this.progress=0;this.playing=false;this.visible=false;this.world=false;this.focusRoute=false;this.selected=this.model.data[0].id;this.materials=[];this.geometries=[];
   this.motion=matchMedia('(prefers-reduced-motion: reduce)');this.longitude=-73.5;this.latitude=4.5;this.zoom=1;this.orbitX=0;this.orbitY=0;this.panX=0;this.panY=0;
   this.build();instances.set(element,this);
   this.listen(this.motion,'change',()=>{this.stop();if(this.motion.matches)this.playing=false;this.sync();this.render();});
   this.listen(document,'visibilitychange',()=>{this.stop();if(!document.hidden)this.start();});
   this.listen(document,'nota:tema',()=>this.theme());
   this.mutation=new MutationObserver(()=>this.theme());this.mutation.observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
   this.scheme=matchMedia('(prefers-color-scheme: dark)');this.listen(this.scheme,'change',()=>this.theme());
   this.observer=new IntersectionObserver(entries=>{this.visible=entries[0].isIntersecting;this.stop();if(this.visible)this.start();},{threshold:0});this.observer.observe(this.stage);
   if(window.THREE){try{this.init3D();}catch(error){this.fallback(error);}}
   else {
    element.dataset.tres='cargando';
    tres(this.stage).then(()=>{if(this.dead)return;delete element.dataset.tres;try{this.init3D();this.sync();this.render();this.start();}catch(error){this.fallback(error);}},error=>{if(!this.dead){delete element.dataset.tres;this.fallback(error);}});
   }
   this.sync();
  }
  listen(target,type,fn){target.addEventListener(type,fn,{signal:this.abort.signal});}
  build(){
   const e=this.element;e.classList.add('nota-flota');
   this.header=node('div','flota-cabecera');const title=node('div');title.append(node('p','ceja','Colombia / demostración interactiva'),node('h3','','Cada vehículo cuenta una historia.'));
   this.badge=node('span','flota-badge','SIMULACIÓN · sin GPS conectado');this.header.append(title,this.badge);
   this.toolbar=node('div','flota-herramientas');this.views=node('div','flota-vistas');this.views.setAttribute('role','group');this.views.setAttribute('aria-label','Vista geográfica');
   this.buttons={};for(const [key,label]of [['region','Colombia'],['world','Globo'],['route','Acercar ruta']]){const b=node('button','',label);b.type='button';b.setAttribute('aria-pressed',String(key==='region'));this.listen(b,'click',()=>{this.world=key==='world';this.focusRoute=key==='route';this.longitude=-73.5;this.latitude=4.5;this.zoom=1;this.orbitX=0;this.orbitY=0;this.panX=0;this.panY=0;this.resetView();this.sync();});this.buttons[key]=b;this.views.append(b);}
   this.play=node('button','','Reproducir demo');this.play.type='button';this.listen(this.play,'click',()=>{if(this.motion.matches)return;if(this.progress>=100)this.progress=0;this.playing=!this.playing;this.stop();this.sync();this.start();});
   const label=node('label','','Avance de la demo');this.slider=node('input');this.slider.type='range';this.slider.min=0;this.slider.max=100;this.slider.value=0;this.slider.step=1;this.slider.setAttribute('aria-label','Avance de la demostración');this.listen(this.slider,'input',()=>{this.playing=false;this.stop();this.seek(Number(this.slider.value));});label.append(this.slider);this.toolbar.append(this.views,this.play,label);
   this.navigation=node('div','flota-navegacion');this.navigation.setAttribute('role','group');this.navigation.setAttribute('aria-label','Mover el globo');
   for(const [action,label,path]of [['in','Acercar globo','M12 5v14M5 12h14'],['out','Alejar globo','M5 12h14'],['home','Restablecer vista','M3 10a9 9 0 1 1 2 8M3 4v6h6']]){const b=node('button','nota-icono');b.type='button';b.title=label;b.setAttribute('aria-label',label);b.dataset.flotaVista=action;b.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="'+path+'"/></svg>';this.listen(b,'click',()=>action==='home'?this.resetView():this.changeZoom(action==='in'?1.25:.8));this.navigation.append(b);}this.toolbar.append(this.navigation);
   this.layout=node('div','flota-layout');this.stage=node('div','flota-mapa-caja');this.stage.tabIndex=0;this.stage.setAttribute('role','region');this.stage.setAttribute('aria-label','Globo operativo de Colombia, desplazable horizontalmente');
   this.surface=node('div','flota-superficie');this.canvas=node('canvas');this.canvas.setAttribute('role','img');this.canvas.setAttribute('aria-label','Colombia resaltada en un globo. Las rutas, estados y valores están en la lista y la tabla.');this.overlay=node('div','flota-etiquetas');this.surface.append(this.canvas,this.overlay);this.stage.append(this.surface);this.gestures();
   this.country=node('span','flota-pais','Colombia');this.overlay.append(this.country);
   this.cityLabels=this.model.cities.map(city=>{const el=node('span','flota-ciudad',city.name);this.overlay.append(el);return {city,el};});
   this.trucks=this.model.data.map((r,i)=>{const b=node('button','flota-camion');b.type='button';b.innerHTML=truck;b.dataset.serie=i%4+1;b.setAttribute('aria-label','Seleccionar '+r.id+': '+r.from.name+' a '+r.to.name);this.listen(b,'click',()=>this.select(r.id));this.overlay.append(b);return b;});
   this.side=node('div','flota-despacho');this.side.append(node('p','ceja','Vehículos / datos de ejemplo'));this.list=node('div','flota-vehiculos');this.cards=this.model.data.map((r,i)=>{const b=node('button','flota-vehiculo');b.type='button';b.dataset.serie=i%4+1;const line=node('span','flota-identidad');line.append(node('strong','',r.id),node('span','',r.status));b.append(line,node('span','',r.from.name+' → '+r.to.name),node('small','',fmt(r.orders)+' pedidos · corte '+new Intl.DateTimeFormat('es-CO',{timeZone:'America/Bogota',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(new Date(r.time))+' COT'));this.listen(b,'click',()=>this.select(r.id));this.list.append(b);return b;});
   this.detail=node('div','flota-detalle');this.detail.setAttribute('role','status');this.side.append(this.list,this.detail);this.layout.append(this.stage,this.side);
   this.summary=node('p','flota-resumen');this.summary.setAttribute('role','status');this.gestureHelp=node('p','flota-ayuda','Arrastra para girar; Mayús + arrastre para mover. Haz clic en el mapa para usar la rueda. En táctil, pellizca para acercar. Teclado: flechas, +, − y Home.');this.note=node('p','flota-nota','Conexiones entre ciudades, no carreteras. Los camiones recorren arcos esquemáticos. Una demo completa dura 45 segundos; el avance no mide distancia, ETA ni puntualidad.');
   this.error=node('p','grafica-error');this.error.hidden=true;this.parts=[this.header,this.toolbar,this.error,this.layout,this.gestureHelp,this.summary,this.note];const before=e.firstChild;this.parts.forEach(p=>e.insertBefore(p,before));
   this.listen(this.canvas,'webglcontextlost',event=>{event.preventDefault();this.lost=true;this.stop();this.error.hidden=false;this.error.textContent='Vista 3D pausada. Selección y tabla siguen disponibles.';});
   this.listen(this.canvas,'webglcontextrestored',()=>queueMicrotask(()=>{if(this.dead)return;this.lost=false;this.error.hidden=true;this.theme();this.start();}));
  }
  material(options){const m=new THREE.MeshBasicMaterial(options);this.materials.push(m);return m;}
  mesh(geometry,material){this.geometries.push(geometry);const m=new THREE.Mesh(geometry,material);this.scene.add(m);return m;}
  init3D(){
   if(!window.THREE||!window.NotaGeografia||!window.NotaGlobo)throw Error('Faltan Three, packages/core/components/geography.js o packages/core/components/globe.js.');
   this.renderer=new THREE.WebGLRenderer({canvas:this.canvas,antialias:true,alpha:true});this.renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));this.scene=new THREE.Scene();this.camera=new THREE.OrthographicCamera();
   this.earth=this.mesh(new THREE.SphereGeometry(1,80,48),this.material({color:0xffffff}));
   const ring=NotaGeografia.colombia.coordinates[0].slice(0,-1),points=ring.map(([lon,lat])=>new THREE.Vector2(lon,lat)),indices=THREE.ShapeUtils.triangulateShape(points,[]),positions=[];
   const subdivide=(a,b,c,level)=>{if(!level){positions.push(...a.toArray(),...b.toArray(),...c.toArray());return;}const ab=a.clone().add(b).normalize().multiplyScalar(1.004),bc=b.clone().add(c).normalize().multiplyScalar(1.004),ca=c.clone().add(a).normalize().multiplyScalar(1.004);subdivide(a,ab,ca,level-1);subdivide(ab,b,bc,level-1);subdivide(ca,bc,c,level-1);subdivide(ab,bc,ca,level-1);};
   indices.forEach(triangle=>subdivide(...triangle.map(i=>vector(ring[i][1],ring[i][0],1.004)),3));const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));this.countryMesh=this.mesh(geo,this.material({side:THREE.DoubleSide}));
   const contour=ring.concat([ring[0]]).map(([lon,lat])=>vector(lat,lon,1.006));this.outline=new THREE.Line(new THREE.BufferGeometry().setFromPoints(contour),new THREE.LineBasicMaterial());this.geometries.push(this.outline.geometry);this.materials.push(this.outline.material);this.scene.add(this.outline);
   this.routes=this.model.data.map((r,i)=>{const a=vector(r.from.lat,r.from.lon,1.018),b=vector(r.to.lat,r.to.lon,1.018),control=a.clone().add(b).normalize().multiplyScalar(1.018+a.distanceTo(b)*.12);const curve=new THREE.QuadraticBezierCurve3(a,control,b);const route=this.mesh(new THREE.TubeGeometry(curve,80,.0017,6,false),this.material({depthTest:true}));return {curve,mesh:route};});
   this.pins=this.model.cities.map(city=>{const m=this.mesh(new THREE.SphereGeometry(.0048,14,10),this.material({depthTest:false}));m.position.copy(vector(city.lat,city.lon,1.02));m.renderOrder=5;return m;});
   // Reutiliza la máscara COBE incrustada del globo; nunca solicita una imagen externa.
   const image=new Image();this.landImage=image;image.onload=()=>{if(this.dead)return;const c=document.createElement('canvas');c.width=image.width;c.height=image.height;const ctx=c.getContext('2d');ctx.drawImage(image,0,0);const pixels=ctx.getImageData(0,0,c.width,c.height).data,positions=[];
    for(let i=0;i<16000;i++){const y=1-2*(i+.5)/16000,lat=Math.asin(y)*180/Math.PI,lon=((i*137.507764)%360)-180,x=Math.min(c.width-1,Math.floor((lon+180)/360*c.width)),v=Math.min(c.height-1,Math.floor((90-lat)/180*c.height));if(pixels[(v*c.width+x)*4]>100)positions.push(...vector(lat,lon,1.001).toArray());}
    const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));const material=new THREE.PointsMaterial({size:.008,sizeAttenuation:true});this.land=new THREE.Points(geometry,material);this.scene.add(this.land);this.geometries.push(geometry);this.materials.push(material);this.theme();};image.src=NotaGlobo.landTexture;
   this.resize=new ResizeObserver(()=>{this.fit();this.stage.scrollLeft=Math.max(0,(this.surface.clientWidth-this.stage.clientWidth)/2);});this.resize.observe(this.surface);this.resize.observe(this.stage);this.theme();this.resetView();
  }
  color(raw){const ctx=this.colorContext||(this.colorContext=document.createElement('canvas').getContext('2d'));ctx.clearRect(0,0,1,1);ctx.fillStyle=raw;ctx.fillRect(0,0,1,1);const [r,g,b]=ctx.getImageData(0,0,1,1).data;return new THREE.Color().setRGB(r/255,g/255,b/255,THREE.SRGBColorSpace);}
  theme(){if(!this.renderer||this.dead)return;const css=getComputedStyle(this.element),color=name=>this.color(css.getPropertyValue(name).trim());this.earth.material.color.copy(color('--flota-oceano'));this.countryMesh.material.color.copy(color('--flota-territorio'));this.outline.material.color.copy(color('--flota-borde'));this.land?.material.color.copy(color('--flota-tierra'));this.pins.forEach(p=>p.material.color.copy(color('--flota-punto')));this.routes.forEach((r,i)=>r.mesh.material.color.copy(color('--grafica-'+(i%4+1))));this.render();}
  fit(){if(!this.renderer||this.dead)return;const r=this.surface.getBoundingClientRect(),w=Math.max(1,r.width),h=Math.max(1,r.height);this.renderer.setSize(w,h,false);const row=this.model.data.find(r=>r.id===this.selected),a=vector(row.from.lat,row.from.lon),b=vector(row.to.lat,row.to.lon);const half=(this.world?1.16:this.focusRoute?Math.max(.065,a.distanceTo(b)*.7):.225)/this.zoom/Math.min(1,w/h);this.camera.left=-half*w/h;this.camera.right=half*w/h;this.camera.top=half;this.camera.bottom=-half;this.camera.near=.01;this.camera.far=10;const baseNormal=this.focusRoute?a.clone().add(b).normalize():vector(this.latitude,this.longitude),lat=Math.asin(baseNormal.y)*180/Math.PI+this.orbitY,lon=Math.atan2(-baseNormal.z,baseNormal.x)*180/Math.PI+this.orbitX,normal=vector(Math.max(-85,Math.min(85,lat)),lon);this.viewNormal=normal;const up=new THREE.Vector3(0,1,0),right=new THREE.Vector3().crossVectors(up,normal).normalize(),vertical=new THREE.Vector3().crossVectors(normal,right),shift=right.multiplyScalar(this.panX).add(vertical.multiplyScalar(this.panY));this.camera.position.copy(normal.clone().multiplyScalar(4).add(shift));this.camera.up.set(0,1,0);this.camera.lookAt((this.world?new THREE.Vector3():normal.clone()).add(shift));this.camera.updateProjectionMatrix();this.camera.updateMatrixWorld();
   // Grosor visual constante: acercarse no convierte un punto en un disco que tapa la ruta.
   const radius=half*(this.world?1.5:3.5)/h;
   if(this.routeRadius!==radius){this.routeRadius=radius;this.routes.forEach(route=>{const old=route.mesh.geometry;this.geometries.splice(this.geometries.indexOf(old),1);old.dispose();route.mesh.geometry=new THREE.TubeGeometry(route.curve,80,radius,6,false);this.geometries.push(route.mesh.geometry);});}
   this.pins.forEach(pin=>pin.scale.setScalar(half*(this.world?7:10)/h/.0048));
   this.render();}
  resetView(){this.zoom=1;this.orbitX=0;this.orbitY=0;this.panX=0;this.panY=0;this.fit();this.stage.scrollLeft=Math.max(0,(this.surface.clientWidth-this.stage.clientWidth)/2);}
  changeZoom(factor){if(!this.renderer||!Number.isFinite(factor)||factor<=0)return;this.zoom=Math.max(.5,Math.min(6,this.zoom*factor));this.fit();}
  move(dx,dy,pan=false){if(!this.renderer)return;const scale=2*this.camera.top/this.surface.clientHeight;if(pan){this.panX=Math.max(-2,Math.min(2,this.panX-dx*scale));this.panY=Math.max(-2,Math.min(2,this.panY+dy*scale));}else{this.orbitX=(this.orbitX-dx*scale*180/Math.PI)%360;this.orbitY=Math.max(-80,Math.min(80,this.orbitY+dy*scale*180/Math.PI));}this.fit();}
  gestures(){
   this.pointers=new Map();this.canvas.style.touchAction='none';this.stage.setAttribute('aria-keyshortcuts','ArrowLeft ArrowRight ArrowUp ArrowDown + - Home');
   this.listen(this.canvas,'pointerdown',e=>{if(e.button!==0||!this.renderer)return;this.stage.focus({preventScroll:true});this.pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});this.canvas.setPointerCapture(e.pointerId);this.canvas.classList.add('arrastrando');});
   this.listen(this.canvas,'pointermove',e=>{const prev=this.pointers.get(e.pointerId);if(!prev)return;const others=[...this.pointers.entries()].filter(([id])=>id!==e.pointerId),next={x:e.clientX,y:e.clientY};if(others.length){const other=others[0][1],before=Math.hypot(prev.x-other.x,prev.y-other.y),after=Math.hypot(next.x-other.x,next.y-other.y);if(before>2)this.changeZoom(after/before);}else this.move(next.x-prev.x,next.y-prev.y,e.shiftKey);this.pointers.set(e.pointerId,next);});
   const end=e=>{this.pointers.delete(e.pointerId);if(!this.pointers.size)this.canvas.classList.remove('arrastrando');};for(const event of ['pointerup','pointercancel','lostpointercapture'])this.listen(this.canvas,event,end);
   this.canvas.addEventListener('wheel',e=>{if(!this.renderer||!(e.ctrlKey||e.metaKey||document.activeElement===this.stage))return;e.preventDefault();this.changeZoom(Math.exp(-Math.max(-150,Math.min(150,e.deltaY))*.004));},{passive:false,signal:this.abort.signal});
   this.listen(this.stage,'keydown',e=>{if(e.target!==this.stage)return;const moves={ArrowLeft:[24,0],ArrowRight:[-24,0],ArrowUp:[0,24],ArrowDown:[0,-24]};if(moves[e.key]){e.preventDefault();this.move(...moves[e.key],e.shiftKey);}else if(['+','=','-','Home'].includes(e.key)){e.preventDefault();if(e.key==='Home')this.resetView();else this.changeZoom(e.key==='-' ? .8 : 1.25);}});
  }
  front(v){return !this.viewNormal||v.clone().normalize().dot(this.viewNormal)>.04;}
  point(v){const p=v.clone().project(this.camera),r=this.surface.getBoundingClientRect();return {x:(p.x+1)*r.width/2,y:(1-p.y)*r.height/2};}
  position(row){return Math.min(100,row.progress+(100-row.progress)*this.progress/100);}
  render(){
   if(!this.renderer||this.dead||this.lost)return;
   const row=this.model.data.find(r=>r.id===this.selected),activeCity=city=>!this.focusRoute||city.name===row.from.name||city.name===row.to.name;this.pins.forEach((pin,i)=>pin.visible=activeCity(this.model.cities[i])&&this.front(pin.position));this.routes.forEach((route,i)=>route.mesh.visible=!this.focusRoute||this.model.data[i].id===this.selected);
   const used=[];this.cityLabels.forEach(({city,el})=>{el.hidden=this.world||!activeCity(city)||!this.front(vector(city.lat,city.lon));if(el.hidden)return;const p=this.point(vector(city.lat,city.lon,1.025)),w=el.offsetWidth,h=el.offsetHeight;
    let chosen=null;const choices=city.lon < -75?[[-w-12,-h-8],[-w-12,9],[12,-h-8],[12,9]]:[[12,-h-8],[12,9],[-w-12,-h-8],[-w-12,9]];for(const [dx,dy]of choices){const rect={x:p.x+dx,y:p.y+dy,w,h};if(rect.x<4||rect.y<4||rect.x+w>this.surface.clientWidth-4||rect.y+h>this.surface.clientHeight-4)continue;if(!used.some(a=>rect.x<a.x+a.w+5&&rect.x+w>a.x-5&&rect.y<a.y+a.h+5&&rect.y+h>a.y-5)){chosen=rect;break;}}
    if(!chosen){el.hidden=true;return;}used.push(chosen);el.style.left=chosen.x+'px';el.style.top=chosen.y+'px';
   });
   this.country.hidden=!this.world||!this.front(vector(4.5,-73.5));const p=this.point(vector(4.5,-73.5,1.03));this.country.hidden ||= p.x<0||p.y<0||p.x>this.surface.clientWidth-90||p.y>this.surface.clientHeight-25;this.country.style.left=(p.x+14)+'px';this.country.style.top=(p.y-18)+'px';
   this.trucks.forEach((button,i)=>{button.hidden=this.world||(this.focusRoute&&this.model.data[i].id!==this.selected);const route=this.routes[i],t=this.position(this.model.data[i])/100,point=this.point(route.curve.getPoint(t));button.hidden ||= !this.front(route.curve.getPoint(t))||point.x<22||point.y<22||point.x>this.surface.clientWidth-22||point.y>this.surface.clientHeight-22;button.style.left=point.x+'px';button.style.top=point.y+'px';const next=this.point(route.curve.getPoint(Math.min(1,t+.01))),prev=this.point(route.curve.getPoint(Math.max(0,t-.01))),angle=Math.atan2(next.y-prev.y,next.x-prev.x);button.querySelector('svg').style.transform='rotate('+angle+'rad)';});
   this.renderer.render(this.scene,this.camera);this.frames++;
  }
  select(id){if(!this.model.data.some(r=>r.id===id))throw Error('Vehículo desconocido.');this.selected=id;this.focusRoute=true;this.world=false;this.sync();this.resetView();}
  sync(){
   const row=this.model.data.find(r=>r.id===this.selected);this.buttons.region.setAttribute('aria-pressed',String(!this.world&&!this.focusRoute));this.buttons.route.setAttribute('aria-pressed',String(this.focusRoute));this.buttons.world.setAttribute('aria-pressed',String(this.world));this.play.disabled=this.motion.matches||!this.renderer;this.play.textContent=this.motion.matches?'Movimiento reducido':this.playing?'Pausar demo':this.progress>=100?'Repetir demo':'Reproducir demo';this.play.setAttribute('aria-pressed',String(this.playing));this.slider.value=String(Math.round(this.progress));
   this.cards.forEach((c,i)=>{c.setAttribute('aria-pressed',String(this.model.data[i].id===this.selected));this.trucks[i].setAttribute('aria-pressed',String(this.model.data[i].id===this.selected));});
   this.detail.replaceChildren(node('strong','',row.id+' · '+row.status),node('p','',row.note),node('p','',row.next),node('small','','Avance inicial al corte: '+fmt(row.progress)+' %'));
   if(this.routes)this.routes.forEach((r,i)=>{r.mesh.material.transparent=true;r.mesh.material.opacity=1;});
   this.summary.textContent=this.progress>=100?'Fin de la demostración. Las posiciones llegaron al destino; esto no confirma entregas reales.':this.playing?'Reproduciendo posiciones simuladas. Los estados y pedidos pertenecen al corte de ejemplo.':'Demostración en pausa · '+this.model.data.length+' vehículos · '+fmt(this.model.data.reduce((a,r)=>a+r.orders,0))+' pedidos de ejemplo.';
  }
  seek(value){if(!Number.isFinite(value)||value<0||value>100)throw Error('Avance entre 0 y 100.');this.progress=value;if(value===100){this.playing=false;this.stop();}this.sync();this.render();}
  stop(){cancelAnimationFrame(this.frame);this.frame=0;this.last=0;}
  start(){if(this.frame||!this.playing||this.motion.matches||!this.visible||document.hidden||this.dead||!this.renderer||this.lost)return;this.frame=requestAnimationFrame(t=>{this.frame=0;const dt=this.last?Math.min((t-this.last)/1000,.1):0;this.last=t;this.progress=Math.min(100,this.progress+dt/45*100);this.render();if(this.progress>=100){this.playing=false;this.sync();this.last=0;}else{this.slider.value=String(Math.round(this.progress));this.start();}});}
  fallback(error){this.stop();this.renderer?.dispose();this.geometries.forEach(g=>g.dispose());this.materials.forEach(m=>m.dispose());this.renderer=null;this.stage.hidden=true;this.views.hidden=true;this.navigation.hidden=true;this.gestureHelp.hidden=true;this.error.hidden=false;this.error.textContent='Vista 3D no disponible. Puedes consultar cada vehículo y la tabla completa.';this.error.dataset.reason=error.message;this.play.disabled=true;this.slider.disabled=true;}
  destroy(){if(this.dead)return;this.dead=true;this.stop();for(const id of this.pointers.keys()){if(this.canvas.hasPointerCapture(id))this.canvas.releasePointerCapture(id);}this.pointers.clear();this.abort.abort();this.observer.disconnect();this.resize?.disconnect();this.mutation.disconnect();if(this.landImage)this.landImage.onload=null;this.geometries.forEach(g=>g.dispose());this.materials.forEach(m=>m.dispose());this.renderer?.dispose();this.parts.forEach(p=>p.remove());this.element.classList.remove('nota-flota');instances.delete(this.element);}
 }
 function init(root=document){return [...(root.matches?.('[data-flota]')?[root]:[]),...root.querySelectorAll('[data-flota]')].map(e=>{if(instances.has(e))return instances.get(e);e.querySelector('[data-error-flota]')?.remove();try{return new Fleet(e);}catch(error){const p=node('p','grafica-error','No se pudo construir la flota: '+error.message);p.dataset.errorFlota='';e.prepend(p);return null;}});}
 window.NotaFlota={init,get:e=>instances.get(e)};init();
})();
