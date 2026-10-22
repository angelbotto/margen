/* NotaGlobo — renderizador Three.js con geometría esférica y arcos de rutas.
 * La máscara terrestre y el shader Fibonacci derivan de COBE, de Shu Ding.
 * MIT License
 *
 * Copyright (c) 2021 Shu Ding
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 * No hay peticiones de imágenes ni fetch: la máscara es un data: URI.
 */
(() => {
  'use strict';
  // Three.js se pide al acercarse a la vista, una vez por documento; sin red queda el respaldo legible.
  const tres=window.NotaTres||(window.NotaTres=(()=>{const src='https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.1/three.min.js',sri='sha512-vnmn/Qqn6aG0POAc9mIGzjq0IybrvxJXYDafNvp9JSnDGxeF3pbkSqLvf+YGd5ku63pT7sa/jxHn7/d0mU8+tA==';let pending=null;
   const load=()=>window.THREE?Promise.resolve(window.THREE):pending||(pending=new Promise((ok,fail)=>{const s=document.createElement('script');s.src=src;s.integrity=sri;s.crossOrigin='anonymous';s.async=true;s.onload=()=>window.THREE?ok(window.THREE):fail(new Error('Three.js no disponible'));s.onerror=()=>{pending=null;s.remove();fail(new Error('Three.js no disponible sin conexión'));};(document.head||document.documentElement).append(s);}));
   return el=>window.THREE?Promise.resolve(window.THREE):new Promise(near=>{if(!('IntersectionObserver' in window))return near();const io=new IntersectionObserver(es=>{if(es.some(e=>e.isIntersecting)){io.disconnect();near();}},{rootMargin:'400px 0px'});io.observe(el);}).then(load);})());
  const LAND = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAQAAAACAAQAAAADMzoqnAAAECklEQVR42u3VsW4jRRzH8d94gzfF4Q0VQaC4vBLTRTp0mze4ggfAPAE5XQEFsGNAVIjwBrmW7h7gJE+giKjyABTZE4g06LKJETdRJvtD65kdz6yduKABiW+TVfzRf2bXYxtcE/59YJCz6YdbgQF6ACSRrwYKYImmh5PbwOewlV3wlQNbAN6SEExjUOO+BU0aCSnxReHABUlK4YFQeJeUT3da8IIkZ6NGoSnFY5KsMoVzMKfECUnqxgPYRArarmUCndHwzIEaQEpg5xVdBXROl8mpAQx5dUgPiHoYAAkg5w3JABR06byGAVgcRGAz5bznj6phBQNRFwyqgdxebH6gshJAesWoFhgYpApAFoG8BIZ/fEhSox5jDjQXmV0Ar5XJfAIrALi3URVs09gHIL4XJCkLC5LH9JWiArABFCSrQjdgkBzRJ0WJeUOSNyQAfJJwUSWUBRlJQ8oGHATACGlBynnzy2kEYLNjrxouigD8BZcgOeVPqh12RtufaCN5wCPVDpvQ9lsIrqndsJtDcWqBCpf4hWN7OdWHBw58FwIaNOU/n1TpMW2DFaD48cmr4185T8NHkpUFX749pQPVdgRKC/DGoQPVeAEKv+WHvY8OOWNTPRp5kHuwSf8wzXtVBKR7YwEH9H3lQUaypUfSATOALyVNu5vZJW31Bnx98nkLfDUWJaz6ixvm+RIQRdl3kmRxxiaDoGnZW4CpPfkaQadlcPim1xOSvETQo7Lv75enVAXJ3xGUlony4KQBBWUM1NiDc6qhyS8RgQs18OCMMtPDaAUIyg0PZkRWDqs+wnKJBTDI1Js6BolegOsKmUxNDBAAKqQyMQmidhegBlLZ+wwKYdv5M/8x1khkb1cgKqP2H+MKyV5vS+whrE8DQDgAlUAoRBX056EElJCjJVACeJBZgNfVp+iCCm4RBWCgKsRxASSA9KgDhDtCiTuMyfHsKXzhC6wNAIjjWb8LKAOA2ctk3FmCOlgKFy8f1N0JJtgsxinYnVAHt4t3gPzZXSCTyCWCQmBT91QE3B5yarSN40dNHYPka4TlDhTUI8zLvl0JSL3vZn6DsCFZOeB2yROEpR68sECQQA++xIGCR2X7DwlEoLRgUrZrqlUg50S1uy43YqDcN6UFBVkhAjWiCV2Q0jgQPdplMKxvBXodcOfAwJYvgdL+1etA1YJJfBcZlQV7sO1i2gHoNiyxtQ5sBsCgWyoxCHiFFd2L5nUTCqMAqGUgsQ9f5kCcCiZgRYkMgMTd5WsB1rTzj0Em14BE4r+QxN1lCEsVur2PoF5Wbg8RJXR4djgvBgauhLywoEZQrt1KKRdVS4CdlJ8qafyP+9KIj/nE/d7kKwH9jgS72e9DV+kvfTWgct4ZyP8Byb8BPG7MaaIIkAQAAAAASUVORK5CYII=';
  // Shader de COBE: t=viewport, s=ángulos, F=base, w=atmósfera,
  // n=(brillo,difusión,oscuro,opacidad), k=muestras, x=escala, y=brillo del océano.
  const PLANET = `precision highp float;uniform vec2 t,v,s;uniform vec3 paper;uniform float lightTheme;uniform vec3 F,w;uniform vec4 n;uniform float k,x,y;uniform sampler2D z;float u;mat3 A(float a,float b){float c=cos(a),d=cos(b),e=sin(a),f=sin(b);return mat3(d,f*e,-f*c,0,c,e,f,d*-e,d*c);}vec3 B(vec3 c,out float G){c=c.xzy;float q=max(2.,floor(log2(2.236068*k*3.141593*(1.-c.z*c.z))*.72021));vec2 g=floor(pow(1.618034,q)/2.236068*vec2(1,1.618034)+.5),d=fract((g+1.)*.618034)*6.283185-3.883222,e=-2.*g,f=vec2(atan(c.y,c.x),c.z-1.),r=floor(vec2(e.y*f.x-d.y*(f.y*k+1.),-e.x*f.x+d.x*(f.y*k+1.))/(d.x*e.y-e.x*d.y));float o=3.141593;vec3 C;for(float h=0.;h<4.;h+=1.){vec2 D=vec2(mod(h,2.),floor(h*.5));float j=dot(g,r+D);if(j>k)continue;float a=j,b=0.;a>=16384.?(a-=16384.,b+=.868872):0.,a>=8192.?(a-=8192.,b+=.934436):0.,a>=4096.?(a-=4096.,b+=.467218):0.,a>=2048.?(a-=2048.,b+=.733609):0.,a>=1024.?(a-=1024.,b+=.866804):0.,a>=512.?(a-=512.,b+=.433402):0.,a>=256.?(a-=256.,b+=.216701):0.,a>=128.?(a-=128.,b+=.108351):0.,a>=64.?(a-=64.,b+=.554175):0.,a>=32.?(a-=32.,b+=.777088):0.,a>=16.?(a-=16.,b+=.888544):0.,a>=8.?(a-=8.,b+=.944272):0.,a>=4.?(a-=4.,b+=.472136):0.,a>=2.?(a-=2.,b+=.236068):0.,a>=1.?(a-=1.,b+=.618034):0.;float l=fract(b)*6.283185,i=1.-2.*j*u,m=sqrt(1.-i*i);vec3 p=vec3(cos(l)*m,sin(l)*m,i);float E=length(c-p);if(E<o)o=E,C=p;}G=o;return C.xzy;}void main(){u=1./k;vec2 c=1./t,b=(gl_FragCoord.xy*c*2.-1.)/x-v*vec2(1,-1)*c;b.x*=t.x*c.y;float a=dot(b,b),f=0.,landShade=0.;vec4 l=vec4(0);if(a<=.64){float g;vec4 m=vec4(0);vec3 h=normalize(vec3(b,sqrt(.64-a)));mat3 o=A(s.y,s.x);float i=h.z;vec3 d=B(h*o,g);float j=asin(d.y),e=acos(-d.x/cos(j));e=d.z<0.?-e:e;float p=max(texture2D(z,vec2(e*.5/3.141593,-(j/3.141593+.5))).x,y),q=p*smoothstep(8e-3,0.,g)*pow(i,n.y)*n.x;landShade=q;m+=vec4(F*(mix((1.-q)*pow(i,.4),q,n.z)+.1)+pow(1.-i,4.)*w,1),l+=m*(1.+n.w)*.5,f=(1.-a)*(1.-a)*smoothstep(0.,1.,.2/(a-.64));}else{float r=sqrt(.2/(a-.64));f=smoothstep(.5,1.,r/(r+1.));}if(lightTheme>.5){if(a<=.64){float ink=clamp(.025+landShade*.30,0.,.50);gl_FragColor=vec4(mix(paper,F,ink),1.);}else{gl_FragColor=vec4(w,f*.15);}}else{gl_FragColor=l+vec4(f*w,f);}}`;
  const PROJECT = `
    uniform vec2 viewport, angles;
    uniform float scale;
    vec3 rotatePoint(vec3 p) {
      float cp=cos(angles.x), sp=sin(angles.x), ct=cos(angles.y), st=sin(angles.y);
      return vec3(cp*p.x+sp*p.z, sp*st*p.x+ct*p.y-cp*st*p.z, -sp*ct*p.x+st*p.y+cp*ct*p.z);
    }
    vec2 projectPoint(vec3 p) { return p.xy * vec2(viewport.y/viewport.x,1.) * scale; }
  `;
  const ARC_VERTEX = `
    attribute vec3 position;
    uniform vec3 fromPoint,toPoint,controlPoint;
    uniform float width;
    varying vec3 viewPoint;
    ${PROJECT}
    void main() {
      float t=position.x, u=1.-t;
      vec3 p=u*u*fromPoint+2.*u*t*controlPoint+t*t*toPoint;
      viewPoint=rotatePoint(p);
      vec3 tangent=rotatePoint(2.*u*(controlPoint-fromPoint)+2.*t*(toPoint-controlPoint));
      vec2 normal=normalize(vec2(-tangent.y,tangent.x)+vec2(.000001));
      vec2 clip=projectPoint(viewPoint)+normal*position.y*width*vec2(2./viewport.x,2./viewport.y);
      gl_Position=vec4(clip,0.,1.);
    }
  `;
  const ARC_FRAGMENT = `precision highp float;
    varying vec3 viewPoint;
    uniform vec3 color;
    void main() {
      if(viewPoint.z<0. && length(viewPoint.xy)<.8) discard;
      gl_FragColor=vec4(color,1.);
    }
  `;
  const MARKER_VERTEX = `
    attribute vec3 position;
    uniform vec3 location;
    uniform float size;
    varying vec2 uv;
    varying vec3 viewPoint;
    ${PROJECT}
    void main() {
      uv=position.xy;
      viewPoint=rotatePoint(location*.82);
      vec2 clip=projectPoint(viewPoint)+position.xy*size*vec2(viewport.y/viewport.x,1.)*scale;
      gl_Position=vec4(clip,0.,1.);
    }
  `;
  const MARKER_FRAGMENT = `precision highp float;
    varying vec2 uv; varying vec3 viewPoint; uniform vec3 color;
    void main() {
      if(viewPoint.z<0. && length(viewPoint.xy)<.8) discard;
      float alpha=1.-smoothstep(.4,.5,length(uv));
      if(alpha<=0.) discard;
      gl_FragColor=vec4(color,alpha);
    }
  `;
  const node = (tag,cls,text) => { const e=document.createElement(tag);if(cls)e.className=cls;if(text)e.textContent=text;return e; };
  const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
  const wrap=a=>((a+Math.PI)%(2*Math.PI)+2*Math.PI)%(2*Math.PI)-Math.PI;
  class NotaGlobo {
    constructor(element, data) {
      this.element=element; this.frame=0; this.frames=0; this.dead=false;
      this.visible=true; this.contextLost=false; this.paused=false;
      this.phi=4.6;this.theta=.18;this.scale=1;this.selected=null;
      this.motion=matchMedia('(prefers-reduced-motion: reduce)');
      this.scheme=matchMedia('(prefers-color-scheme: dark)');
      this.abort=new AbortController();this.cleanups=[];
      this.points=[];this.arcs=[];this.routeMeshes=[];this.markerMeshes=[];
      this.buildDOM();
      this.setData(data);
      this.listen(this.motion,'change',()=>{this.stop();this.syncPause();this.draw();this.start();});
      this.listen(this.scheme,'change',()=>this.theme());
      this.listen(document,'visibilitychange',()=>{this.stop();if(!document.hidden){this.draw();this.start();}});
      this.listen(document,'nota:tema',()=>this.theme());
      this.mutation=new MutationObserver(()=>this.theme());
      this.mutation.observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
      this.intersection=new IntersectionObserver(entries=>{this.visible=entries[0].isIntersecting;this.stop();if(this.visible){this.draw();this.start();}},{rootMargin:'80px'});
      this.intersection.observe(this.element);
      const unavailable=error=>{this.error.textContent='El globo 3D no está disponible. Las rutas completas están en la lista.';this.error.hidden=false;this.canvas.hidden=true;this.stage.hidden=true;this.layout.style.gridTemplateColumns='1fr';this.controls.hidden=true;this.error.dataset.reason=error.name;};
      if(window.THREE){try { this.init(); } catch(error) { unavailable(error); }}
      else {
        this.element.dataset.tres='cargando';
        tres(this.element).then(()=>{if(this.dead)return;delete this.element.dataset.tres;try{this.init();this.syncPause();this.draw();this.start();}catch(error){unavailable(error);}},
          error=>{if(!this.dead){delete this.element.dataset.tres;unavailable(error);}});
      }
      this.syncPause();
    }
    listen(target,type,handler,options={}) { target.addEventListener(type,handler,{...options,signal:this.abort.signal}); }
    buildDOM() {
      this.element.classList.add('globo');
      this.layout=node('div','globo-layout');
      this.stage=node('div','globo-escena');
      this.canvas=node('canvas');this.canvas.tabIndex=0;this.canvas.setAttribute('role','img');
      this.canvas.setAttribute('aria-label','Globo de rutas. Usa las flechas para girar; también puedes elegir una ruta en la lista.');
      this.stage.append(this.canvas);
      this.list=node('div','globo-rutas');this.list.setAttribute('aria-label','Rutas del globo');
      this.layout.append(this.stage,this.list);
      this.controls=node('div','globo-controles');
      this.pauseButton=node('button','','Pausar giro');
      this.pauseButton.type='button';this.pauseButton.setAttribute('aria-pressed','false');
      const left=node('button','','← Girar'),right=node('button','','Girar →'),reset=node('button','','Vista inicial');
      for(const button of [left,right,reset])button.type='button';
      this.controls.append(this.pauseButton,left,right,reset);
      this.status=node('p','globo-ayuda');this.status.setAttribute('role','status');this.status.setAttribute('aria-live','polite');
      this.status.textContent='Arrastra horizontalmente o usa las flechas. Selecciona una ruta para verla.';
      this.error=node('p','globo-error');this.error.hidden=true;
      this.element.append(this.error,this.layout,this.controls,this.status);
      this.listen(this.pauseButton,'click',()=>{this.paused=!this.paused;this.stop();this.syncPause();this.start();});
      this.listen(left,'click',()=>this.rotate(-.25,0));this.listen(right,'click',()=>this.rotate(.25,0));
      this.listen(reset,'click',()=>{this.select(null);this.phi=4.6;this.theta=.18;this.draw();});
      this.listen(this.canvas,'keydown',e=>{
        const directions={ArrowLeft:[-.15,0],ArrowRight:[.15,0],ArrowUp:[0,-.12],ArrowDown:[0,.12]};
        if(directions[e.key]){e.preventDefault();this.rotate(...directions[e.key]);}
        if(e.key==='Home'){e.preventDefault();this.select(null);this.phi=4.6;this.theta=.18;this.draw();}
      });
      this.listen(this.canvas,'pointerdown',e=>{
        if(e.button!==0)return;
        this.drag={id:e.pointerId,x:e.clientX,y:e.clientY,type:e.pointerType};
        this.canvas.setPointerCapture(e.pointerId);this.target=null;this.stop();
      });
      this.listen(this.canvas,'pointermove',e=>{
        if(!this.drag||this.drag.id!==e.pointerId)return;
        const dx=e.clientX-this.drag.x,dy=e.clientY-this.drag.y;
        this.phi+=dx*.005;
        // Un dedo conserva el scroll vertical de la página. Ratón permite inclinación.
        if(this.drag.type!=='touch')this.theta=clamp(this.theta+dy*.003,-1.2,1.2);
        this.drag.x=e.clientX;this.drag.y=e.clientY;this.draw();
      });
      const release=e=>{if(this.drag?.id===e.pointerId){this.drag=null;if(this.canvas.hasPointerCapture(e.pointerId))this.canvas.releasePointerCapture(e.pointerId);this.start();}};
      this.listen(this.canvas,'pointerup',release);this.listen(this.canvas,'pointercancel',release);
      this.listen(this.canvas,'lostpointercapture',()=>{this.drag=null;this.start();});
      this.listen(this.canvas,'webglcontextlost',e=>{e.preventDefault();this.contextLost=true;this.stop();this.error.textContent='La vista 3D está suspendida. Las rutas siguen disponibles.';this.error.hidden=false;});
      // Three reconstruye su estado en otro listener del mismo evento; dibujar después.
      this.listen(this.canvas,'webglcontextrestored',()=>queueMicrotask(()=>{if(this.dead)return;this.contextLost=false;this.error.hidden=true;this.draw();this.start();}));
    }
    setData(data) {
      if(!data||!Array.isArray(data.points)||!Array.isArray(data.arcs))throw new TypeError('Se esperan points y arcs.');
      const ids=new Set();
      const points=data.points.map(p=>{
        if(!p||typeof p.id!=='string'||!p.id||ids.has(p.id)||!Number.isFinite(p.lat)||!Number.isFinite(p.lon)||Math.abs(p.lat)>90||Math.abs(p.lon)>180)throw new TypeError('Punto inválido o id duplicado.');
        ids.add(p.id);return {id:p.id,label:String(p.label||p.id),lat:p.lat,lon:p.lon};
      });
      const routeIds=new Set();
      const arcs=data.arcs.map((a,i)=>{
        const id=String(a.id??'ruta-'+i);
        if(!ids.has(a.from)||!ids.has(a.to)||routeIds.has(id))throw new TypeError('Ruta inválida o id duplicado.');
        routeIds.add(id);return {id,from:a.from,to:a.to,label:String(a.label||a.from+' → '+a.to),detail:String(a.detail||'')};
      });
      this.points=points;this.arcs=arcs;this.selected=null;this.target=null;
      this.list.replaceChildren();
      if(!arcs.length)this.list.append(node('p','secundario','Sin rutas registradas.'));
      arcs.forEach(a=>{const b=node('button');b.type='button';b.dataset.route=a.id;b.setAttribute('aria-pressed','false');b.append(node('span','',a.label));if(a.detail)b.append(node('small','',a.detail));b.addEventListener('click',()=>this.select(this.selected===a.id?null:a.id));this.list.append(b);});
      if(this.scene){this.buildRoutes();this.draw();this.start();}
    }
    vector(point) {
      const lat=point.lat*Math.PI/180,lon=point.lon*Math.PI/180;
      return new THREE.Vector3(Math.cos(lat)*Math.cos(lon),Math.sin(lat),-Math.cos(lat)*Math.sin(lon));
    }
    rgb(css) {
      // El shader de referencia trabaja en sRGB; no convertir a espacio lineal aquí.
      const context=this.colorContext||(this.colorContext=document.createElement('canvas').getContext('2d'));
      context.fillStyle='#000';context.fillStyle=css;context.fillRect(0,0,1,1);
      const c=context.getImageData(0,0,1,1).data;
      return new THREE.Vector3(c[0]/255,c[1]/255,c[2]/255);
    }
    init() {
      if(!window.THREE)throw new Error('Three.js unavailable');
      this.renderer=new THREE.WebGLRenderer({canvas:this.canvas,alpha:true,antialias:true,preserveDrawingBuffer:true});
      this.renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));
      this.renderer.setClearColor(0,0);
      this.scene=new THREE.Scene();this.camera=new THREE.Camera();
      this.shared={viewport:{value:new THREE.Vector2(1,1)},angles:{value:new THREE.Vector2(this.phi,this.theta)},scale:{value:1}};
      this.planetUniforms={t:{value:new THREE.Vector2(1,1)},v:{value:new THREE.Vector2(0,0)},s:this.shared.angles,F:{value:new THREE.Vector3()},w:{value:new THREE.Vector3()},n:{value:new THREE.Vector4(10,2,.6,1)},k:{value:15000},x:this.shared.scale,y:{value:.05},z:{value:null},paper:{value:new THREE.Vector3()},lightTheme:{value:0}};
      const material=new THREE.RawShaderMaterial({uniforms:this.planetUniforms,vertexShader:'precision highp float; attribute vec3 position; void main(){gl_Position=vec4(position.xy,0.,1.);}',fragmentShader:PLANET,transparent:true,depthTest:false,depthWrite:false});
      const plane=new THREE.Mesh(new THREE.PlaneGeometry(2,2),material);plane.frustumCulled=false;plane.renderOrder=0;this.scene.add(plane);
      // Textura 256 × 128 de COBE, incrustada y con filtrado NEAREST como el original.
      this.texture=new THREE.TextureLoader().load(LAND,()=>{if(!this.dead){this.draw();this.start();}},undefined,()=>{this.error.textContent='No se pudo decodificar el mapa. Consulta la lista de rutas.';this.error.hidden=false;});
      this.texture.minFilter=THREE.NearestFilter;this.texture.magFilter=THREE.NearestFilter;
      // COBE usa UV negativos y los valores por defecto de WebGL: REPEAT y flipY=false.
      // Los defaults de Three (clamp/flip) borrarían o invertirían los continentes.
      this.texture.wrapS=THREE.RepeatWrapping;this.texture.wrapT=THREE.RepeatWrapping;this.texture.flipY=false;
      this.planetUniforms.z.value=this.texture;
      this.buildRoutes();this.theme();
      this.resize=new ResizeObserver(()=>this.fit());this.resize.observe(this.stage);
      this.fit();this.start();
    }
    disposeMeshes(list) { for(const mesh of list){this.scene.remove(mesh);mesh.geometry.dispose();mesh.material.dispose();}list.length=0; }
    buildRoutes() {
      this.disposeMeshes(this.routeMeshes);this.disposeMeshes(this.markerMeshes);
      const byId=new Map(this.points.map(p=>[p.id,p]));
      this.arcs.forEach(a=>{
        const from=this.vector(byId.get(a.from)),to=this.vector(byId.get(a.to));
        if(from.distanceTo(to)<.00001)return; // Una ruta a sí misma no produce una curva degenerada.
        const mid=from.clone().add(to);
        if(mid.length()<.0001)mid.crossVectors(from,new THREE.Vector3(Math.abs(from.y)<.9?0:1,Math.abs(from.y)<.9?1:0,0));
        mid.normalize();
        // Curva cuadrática elevada. Compensar la cuerda evita que rutas largas atraviesen la Tierra.
        const height=.1+.14*(1-from.dot(to))/2;
        const control=mid.multiplyScalar(2*(.82+height)-.82*Math.sqrt(Math.max(0,(1+from.dot(to))/2)));
        const vertices=[];
        for(let i=0;i<64;i++){const s=i/64,e=(i+1)/64;vertices.push(s,-1,0,e,-1,0,s,1,0,s,1,0,e,-1,0,e,1,0);}
        const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));
        const uniforms={...this.shared,fromPoint:{value:from.multiplyScalar(.82)},toPoint:{value:to.multiplyScalar(.82)},controlPoint:{value:control},width:{value:.65},color:{value:new THREE.Vector3()}};
        const material=new THREE.RawShaderMaterial({uniforms,vertexShader:'precision highp float;\n'+ARC_VERTEX,fragmentShader:ARC_FRAGMENT,transparent:true,depthTest:false,depthWrite:false});
        const mesh=new THREE.Mesh(geometry,material);mesh.frustumCulled=false;mesh.renderOrder=1;mesh.userData.id=a.id;this.scene.add(mesh);this.routeMeshes.push(mesh);
      });
      this.points.forEach(p=>{
        const geometry=new THREE.PlaneGeometry(1,1);
        const material=new THREE.RawShaderMaterial({uniforms:{...this.shared,location:{value:this.vector(p)},size:{value:.028},color:{value:new THREE.Vector3()}},vertexShader:'precision highp float;\n'+MARKER_VERTEX,fragmentShader:MARKER_FRAGMENT,transparent:true,depthTest:false,depthWrite:false});
        const mesh=new THREE.Mesh(geometry,material);mesh.frustumCulled=false;mesh.renderOrder=2;mesh.userData.id=p.id;this.scene.add(mesh);this.markerMeshes.push(mesh);
      });
      this.theme();
    }
    theme() {
      if(!this.renderer||this.dead)return;
      const css=getComputedStyle(this.element),get=name=>css.getPropertyValue(name).trim();
      this.colors={arc:this.rgb(get('--globo-arco')),point:this.rgb(get('--globo-punto')),selected:this.rgb(get('--marcador'))};
      const u=this.planetUniforms;
      u.F.value.copy(this.rgb(get('--globo-base')));u.w.value.copy(this.rgb(get('--globo-glow')));
      u.paper.value.copy(this.rgb(get('--papel')));u.n.value.x=parseFloat(get('--globo-brillo'))||10;
      u.n.value.z=parseFloat(get('--globo-dark'))||0;u.lightTheme.value=u.n.value.z===0?1:0;
      this.colorRoutes();this.draw();
    }
    colorRoutes() {
      if(!this.colors)return;
      const selected=this.arcs.find(a=>a.id===this.selected);
      this.routeMeshes.forEach(m=>{const on=m.userData.id===this.selected;m.material.uniforms.color.value.copy(on?this.colors.selected:this.colors.arc);m.material.uniforms.width.value=on?1.15:.65;});
      this.markerMeshes.forEach(m=>{const on=selected&&(m.userData.id===selected.from||m.userData.id===selected.to);m.material.uniforms.color.value.copy(on?this.colors.selected:this.colors.point);m.material.uniforms.size.value=on?.045:.028;});
    }
    select(id) {
      if(id!==null&&!this.arcs.some(a=>a.id===id))throw new TypeError('Ruta desconocida.');
      this.selected=id;this.target=null;
      for(const button of this.list.querySelectorAll('button'))button.setAttribute('aria-pressed',String(button.dataset.route===id));
      const arc=this.arcs.find(a=>a.id===id);
      this.status.textContent=arc?arc.label+(arc.detail?' · '+arc.detail:''):'Todas las rutas.';
      if(arc&&this.scene){
        const a=this.vector(this.points.find(p=>p.id===arc.from)),b=this.vector(this.points.find(p=>p.id===arc.to));
        const center=a.add(b);if(center.length()<.0001)center.copy(this.vector(this.points.find(p=>p.id===arc.from)));center.normalize();
        this.target={phi:Math.atan2(-center.x,center.z),theta:clamp(Math.asin(center.y),-1.2,1.2)};
        if(this.motion.matches||this.paused){this.phi=this.target.phi;this.theta=this.target.theta;this.target=null;}
      }
      this.colorRoutes();this.draw();this.start();
    }
    fit() {
      if(this.dead||!this.renderer)return;
      const rect=this.stage.getBoundingClientRect(),w=Math.max(1,Math.round(rect.width)),h=Math.max(1,Math.round(rect.height));
      this.renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));this.renderer.setSize(w,h,false);
      this.shared.viewport.value.set(w,h);
      this.planetUniforms.t.value.set(this.canvas.width,this.canvas.height);
      // La proyección reserva espacio para atmósfera y arcos incluso en un viewport vertical.
      this.scale=Math.min(1,w/h)*.92;this.shared.scale.value=this.scale;this.draw();
    }
    rotate(dx,dy) { this.target=null;this.phi+=dx;this.theta=clamp(this.theta+dy,-1.2,1.2);this.draw(); }
    syncPause() {
      this.pauseButton.disabled=this.motion.matches;
      this.pauseButton.setAttribute('aria-pressed',String(this.paused||this.motion.matches));
      this.pauseButton.textContent=this.motion.matches?'Giro desactivado por preferencia':this.paused?'Reanudar giro':'Pausar giro';
    }
    pause() {this.paused=true;this.stop();this.syncPause();}
    resume() {this.paused=false;this.syncPause();this.start();}
    draw() {
      if(!this.renderer||this.dead||this.contextLost)return;
      this.shared.angles.value.set(this.phi,this.theta);
      this.renderer.render(this.scene,this.camera);this.frames++;
    }
    stop() {cancelAnimationFrame(this.frame);this.frame=0;this.last=0;}
    start() {
      if(this.frame||!this.renderer||this.dead||this.contextLost||this.motion.matches||this.paused||this.drag||!this.visible||document.hidden)return;
      if(this.selected&&!this.target)return;
      this.frame=requestAnimationFrame(t=>this.tick(t));
    }
    tick(time) {
      this.frame=0;
      const dt=this.last?Math.min((time-this.last)/1000,.05):1/60;this.last=time;
      if(this.target){
        const factor=1-Math.pow(1-.09,dt*60),delta=wrap(this.target.phi-this.phi);
        this.phi+=delta*factor;this.theta+=(this.target.theta-this.theta)*factor;
        if(Math.abs(delta)<.0001&&Math.abs(this.target.theta-this.theta)<.0001)this.target=null;
      } else if(!this.selected)this.phi+=.072*dt; // .0012 rad/cuadro a 60 Hz, ahora independiente de FPS.
      this.draw();this.start();
    }
    destroy() {
      if(this.dead)return;this.dead=true;this.stop();this.abort.abort();
      this.resize?.disconnect();this.intersection?.disconnect();this.mutation?.disconnect();
      this.scene?.traverse(m=>{m.geometry?.dispose();m.material?.dispose();});
      this.texture?.dispose();this.renderer?.dispose();this.element.replaceChildren();
    }
  }
  Object.defineProperty(NotaGlobo,'landTexture',{value:LAND});
  window.NotaGlobo=NotaGlobo;
})();
