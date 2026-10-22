/* BOTTIFACT · multipágina · septiembre 2026
   Pegar DESPUÉS de packages/core/components/reader.js, dentro de su propio <script>.

   Reparte una nota larga en páginas con su propio temario, sin cargar nada remoto y sin
   romper el enlace directo: cada página tiene su id y queda en el hash.

   Espera este esqueleto —ver docs/components.md, «Multipágina»—:
     .barra con un <button data-ir="id"> por página
     main.hoja.multipagina  >  article.pagina[id]  (la primera con class="viva")
     .paginacion con [data-nav="prev"] y [data-nav="next"]

   Dos cosas que resuelve y que no son evidentes:

   1. El índice de packages/core/components/reader.js delega aquí cuando ve .multipagina. Se recalcula
      mirando sólo la página viva, con aria-current y las clases propias
      `aqui-visto` y `aqui-actual`. Nunca se miden páginas ocultas.
   2. Al cambiar de página cambia la altura del documento; se avisa para que la regla de
      lectura y el índice se recalculen. */
(function () {
  "use strict";
  var hoja = document.querySelector(".hoja.multipagina");
  if (!hoja) return;
  var botones = Array.prototype.slice.call(document.querySelectorAll(".barra [data-ir]"));
  var pags = botones.map(function (b) { return document.getElementById(b.dataset.ir); });
  if (!pags.length || pags.some(function (p) { return !p; })) return;
  var titulos = botones.map(function (b) {
    var n = b.querySelector(".n");
    return (n ? b.textContent.replace(n.textContent, "") : b.textContent).trim();
  });
  var nav = document.querySelector("[data-paginacion]");
  var prev = nav && nav.querySelector('[data-nav="prev"]');
  var next = nav && nav.querySelector('[data-nav="next"]');
  var actual = 0;
  var historial = hoja.hasAttribute('data-historial');
  var profundos = hoja.hasAttribute('data-enlaces-internos');
  function destinoHash() {
    var id;try{id=decodeURIComponent(location.hash.slice(1));}catch{return null;}
    var target=document.getElementById(id);
    return target && (pags.includes(target)||profundos&&pags.some(p=>p.contains(target))) ? target : null;
  }
  function revelar(target,conFoco) {
    // Los destinos dentro de details también deben ser alcanzables.
    for(var p=target.parentElement;p&&p!==hoja;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;
    if(conFoco){target.tabIndex=-1;target.focus({preventScroll:true});}
    target.scrollIntoView({behavior:'instant',block:'start'});
  }

  function pintarNav() {
    if (!nav || !prev || !next) return;
    prev.disabled = actual === 0;
    next.disabled = actual === pags.length - 1;
    var a = prev.querySelector(".tit"), b = next.querySelector(".tit");
    if (a) a.textContent = actual > 0 ? titulos[actual - 1] : "—";
    if (b) b.textContent = actual < pags.length - 1 ? titulos[actual + 1] : "—";
  }

  function ir(i, conFoco, desdeHistorial, destino) {
    if (i < 0 || i >= pags.length) return;
    actual = i;
    pags.forEach(function (p, k) { p.hidden = k !== i; p.classList.toggle("viva", k === i); });
    botones.forEach(function (b, k) {
      if (k === i) b.setAttribute("aria-current", "page"); else b.removeAttribute("aria-current");
    });
    pintarNav();
    if (!destino && location.hash.slice(1) !== pags[i].id) history[historial && conFoco && !desdeHistorial ? 'pushState' : 'replaceState'](null, "", "#" + pags[i].id);
    if(historial){
      var salto=document.querySelector('a.salto');if(salto)salto.setAttribute('href','#'+pags[i].id);
      pags[i].tabIndex=-1;
      var caja=botones[i].closest('[data-capitulos-scroll]')||botones[i].closest('.barra'),r=botones[i].getBoundingClientRect(),c=caja.getBoundingClientRect();
      if(r.left<c.left)caja.scrollLeft+=r.left-c.left-12;else if(r.right>c.right)caja.scrollLeft+=r.right-c.right+12;
    }
    var suave = conFoco && !destino && !matchMedia("(prefers-reduced-motion: reduce)").matches;
    scrollTo({ top: 0, behavior: suave ? "smooth" : "instant" });
    if (conFoco) {
      var h = pags[i].querySelector("h1");
      if (h) { h.setAttribute("tabindex", "-1"); h.focus({ preventScroll: true }); }
    }
    document.dispatchEvent(new CustomEvent("nota:pagina", { detail: { indice: i, id: pags[i].id } }));
    if(destino && destino!==pags[i])revelar(destino,conFoco);
  }

  // Para módulos que difieren trabajo hasta que su página se muestra; avisa con nota:pagina.
  window.NotaPaginas = {
    actual: function () { return pags[actual].id; },
    visible: function (el) { return !pags.some(function (p) { return p.hidden && p.contains(el); }); }
  };
  botones.forEach(function (b, k) { b.addEventListener("click", function () { ir(k, true); }); });
  if (prev) prev.addEventListener("click", function () { ir(actual - 1, true); });
  if (next) next.addEventListener("click", function () { ir(actual + 1, true); });
  function desdeHash() {
    var target=destinoHash(),i=pags.findIndex(p=>p===target||profundos&&p.contains(target));
    if(i>=0 && (i!==actual||profundos))ir(i,true,true,profundos?target:null);
  }
  if(profundos)document.addEventListener('click',function(e){
    var a=e.target.closest('a[href^="#"]');if(!a||e.defaultPrevented||e.button!==0||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey)return;
    var target;try{target=document.getElementById(decodeURIComponent(a.hash.slice(1)));}catch{return;}
    var i=pags.findIndex(p=>p===target||p.contains(target));if(i<0)return;
    e.preventDefault();if(location.hash!==a.hash)history.pushState(null,'',a.hash);ir(i,true,true,target);
  });
  addEventListener("hashchange", desdeHash);
  if(historial)addEventListener('popstate',desdeHash);

  /* El temario, mirando sólo la página viva. */
  function indiceVivo() {
    var pg = pags[actual];
    if (!pg) return;
    Array.prototype.forEach.call(document.querySelectorAll(".indice li"), function (li) {
      li.classList.remove("visto");
      if (!pg.contains(li)) { li.classList.remove("aqui-visto", "aqui-actual"); li.querySelector('a')?.removeAttribute('aria-current'); }
    });
    var links = Array.prototype.slice.call(pg.querySelectorAll('.indice a[href^="#"]'));
    var act = -1;
    var padding = parseFloat(getComputedStyle(document.scrollingElement || document.documentElement).scrollPaddingTop) || 0;
    links.forEach(function (a, i) {
      var s = document.getElementById(a.hash.slice(1));
      if (s && s.getBoundingClientRect().top <= padding + (parseFloat(getComputedStyle(s).scrollMarginTop) || 0) + 2) act = i;
    });
    if(hoja.hasAttribute('data-progreso-pagina')&&pg.getBoundingClientRect().bottom<=innerHeight)act=links.length-1;
    links.forEach(function (a, i) {
      var li = a.closest("li");
      if (!li) return;
      var changed=i===act&&!li.classList.contains('aqui-actual');
      li.classList.toggle("aqui-visto", i < act);
      li.classList.toggle("aqui-actual", i === act);
      if(i===act)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current');
      var index=a.closest('.indice');
      if(changed&&hoja.classList.contains('lectura-guiada')&&getComputedStyle(index).position==='fixed'){
        var linkRect=a.getBoundingClientRect(),indexRect=index.getBoundingClientRect();
        if(linkRect.top<indexRect.top)index.scrollTop+=linkRect.top-indexRect.top;
        else if(linkRect.bottom>indexRect.bottom)index.scrollTop+=linkRect.bottom-indexRect.bottom;
      }
    });
  }
  var pend = 0;
  var motion = matchMedia('(prefers-reduced-motion: reduce)');
  function programar() {
    if(motion.matches){if(pend)cancelAnimationFrame(pend);pend=0;indiceVivo();return;}
    if (!pend) pend = requestAnimationFrame(function () { pend = 0; indiceVivo(); });
  }
  motion.addEventListener('change',programar);
  addEventListener("scroll", programar, { passive: true });
  addEventListener("resize", programar);
  document.addEventListener("nota:pagina", programar);
  document.fonts?.ready.then(programar);

  var targetInicial=destinoHash();
  var inicial = pags.findIndex(p=>p===targetInicial||profundos&&p.contains(targetInicial));
  if (inicial > 0 || historial) ir(Math.max(0,inicial), false, false, profundos?targetInicial:null); else { pintarNav(); programar(); }
  // En la edición nueva, el fragmento identifica el capítulo, pero se abre con su cabecera común.
  if(historial&&document.readyState!=='complete')addEventListener('load',function(){if(profundos&&targetInicial&&!pags.includes(targetInicial))revelar(targetInicial,false);else scrollTo({top:0,behavior:'instant'});},{once:true});
})();
