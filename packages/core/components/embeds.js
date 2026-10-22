/* Margen · publicaciones de X, YouTube e Instagram como tarjetas propias.
   Sin script ni HTML del proveedor. Nada se conecta al proveedor antes del clic del lector.
   Dentro del portal, el documento sólo pide «proveedor + ID»; el portal construye y monta el reproductor. */
(() => {
  'use strict';
  const instances = new WeakMap();
  const NAMES = {x: 'X', youtube: 'YouTube', instagram: 'Instagram'};
  const ORIGINS = {youtube: 'https://www.youtube-nocookie.com', instagram: 'https://www.instagram.com'};
  const REFERRER = {youtube: 'strict-origin', instagram: 'no-referrer'};
  const SANDBOX = 'allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox allow-presentation';
  const ALLOW = 'autoplay; encrypted-media; picture-in-picture; fullscreen';
  const WAIT = 8000;
  const YT_ERRORS = {2: 'El video no tiene un identificador válido.', 5: 'Este navegador no puede reproducir el video aquí.', 100: 'El video no existe o es privado.', 101: 'Quien lo publicó no permite verlo insertado.', 150: 'Quien lo publicó no permite verlo insertado.', 153: 'YouTube no aceptó esta página como origen.'};

  // Única fuente de verdad de lo que se acepta: proveedor fijo, ID con forma exacta, nada más.
  function normalize(spec) {
    if (!spec || typeof spec !== 'object') return null;
    const {provider} = spec;
    if (provider === 'youtube')
      return typeof spec.id === 'string' && /^[A-Za-z0-9_-]{11}$/.test(spec.id) ? {provider, id: spec.id} : null;
    if (provider === 'instagram')
      return typeof spec.id === 'string' && /^[A-Za-z0-9_-]{5,40}$/.test(spec.id) && (spec.kind === 'p' || spec.kind === 'reel') ? {provider, id: spec.id, kind: spec.kind} : null;
    if (provider === 'x') {
      if (typeof spec.user !== 'string' || !/^[A-Za-z0-9_]{1,15}$/.test(spec.user)) return null;
      if (spec.status === undefined || spec.status === null || spec.status === '') return {provider, user: spec.user};
      return typeof spec.status === 'string' && /^[0-9]{1,20}$/.test(spec.status) ? {provider, user: spec.user, status: spec.status} : null;
    }
    return null;
  }
  function sourceURL(spec) {
    const s = normalize(spec);
    if (!s) return null;
    if (s.provider === 'youtube') return 'https://www.youtube.com/watch?v=' + s.id;
    if (s.provider === 'instagram') return 'https://www.instagram.com/' + s.kind + '/' + s.id + '/';
    return 'https://x.com/' + s.user + (s.status ? '/status/' + s.status : '');
  }
  function playerURL(spec, origin) {
    const s = normalize(spec);
    if (!s || s.provider === 'x') return null;
    if (s.provider === 'instagram') return ORIGINS.instagram + '/' + s.kind + '/' + s.id + '/embed/';
    const params = new URLSearchParams({autoplay: '1', mute: '1', playsinline: '1', rel: '0', enablejsapi: '1'});
    if (typeof origin === 'string' && /^https?:\/\/[^/?#\s]+$/.test(origin)) params.set('origin', origin);
    return ORIGINS.youtube + '/embed/' + s.id + '?' + params;
  }
  // Mensajes del reproductor: sólo de ese iframe y de ese origen exacto, texto JSON acotado.
  function signal(provider, data) {
    if (typeof data !== 'string' || data.length > 20000) return null;
    let m;
    try { m = JSON.parse(data); } catch { return null; }
    if (!m || typeof m !== 'object') return null;
    if (provider === 'youtube') {
      if (m.event === 'onError') return {type: 'error', code: Number.isInteger(m.info) ? m.info : null};
      if (m.event === 'infoDelivery' && m.info && m.info.playerState === 1) return {type: 'playing'};
      if (['onReady', 'initialDelivery', 'infoDelivery', 'onStateChange'].includes(m.event)) return {type: 'alive'};
      return null;
    }
    if (provider === 'instagram') {
      if (m.type === 'MEASURE') {
        const h = m.details && m.details.height;
        return typeof h === 'number' && h > 0 && h < 4000 ? {type: 'measure', height: Math.round(h)} : {type: 'alive'};
      }
      return m.type === 'MOUNTED' || m.type === 'LOADING' ? {type: 'alive'} : null;
    }
    return null;
  }
  function errorText(provider, code) {
    return (provider === 'youtube' && YT_ERRORS[code]) || NAMES[provider] + ' no pudo mostrar la publicación.';
  }

  function specOf(el) {
    const d = el.dataset;
    if (d.embed === 'x') return normalize({provider: 'x', user: d.embedUser, status: d.embedStatus});
    return normalize({provider: d.embed, id: d.embedId, kind: d.embedKind});
  }
  function host() {
    const bridge = window.BottifactReviewBridge;
    return parent !== self && bridge && typeof bridge.embed === 'function' ? bridge : null;
  }
  function context(provider) {
    if (host()) return 'host';
    if (location.protocol === 'file:') return provider === 'youtube' ? 'source' : 'local';
    return self.origin === 'null' ? 'source' : 'local';
  }
  const SOURCE_ONLY = {
    file: 'Abierto como archivo local, YouTube no permite reproducirlo aquí. El enlace abre el video.',
    sandbox: 'Este documento está aislado y no puede mostrar el reproductor. El enlace abre la publicación.',
  };

  class MargenEmbed {
    constructor(el) {
      if (instances.has(el)) throw new TypeError('Ya hay una publicación en este contenedor.');
      this.el = el; this.abort = new AbortController(); this.player = null; this.dead = false;
      this.provider = el.dataset.embed; this.spec = specOf(el);
      this.status = el.querySelector('[data-embed-status]');
      this.button = el.querySelector('[data-embed-load]');
      this.stage = el.querySelector('[data-embed-stage]');
      this.links = [...el.querySelectorAll('a[data-embed-source]')];
      // Una imagen remota conectaría con un tercero sin clic; sólo se conservan imágenes embebidas.
      el.querySelectorAll('img').forEach(img => { if (!/^data:image\/(?:png|jpeg|gif|webp|avif|svg\+xml)[;,]/i.test(img.getAttribute('src') || '')) img.remove(); });
      const synthetic = el.hasAttribute('data-embed-synthetic');
      const url = synthetic ? null : sourceURL(this.spec);
      // El enlace se regenera desde el ID: nunca se copia el href del autor.
      for (const a of this.links) {
        if (!url) { const span = document.createElement('span'); span.className = a.className; span.textContent = synthetic ? 'Ejemplo sintético · sin publicación original' : 'Fuente no válida'; a.replaceWith(span); continue; }
        a.href = url; a.target = '_blank'; a.rel = 'noopener noreferrer'; a.setAttribute('referrerpolicy', 'no-referrer');
        a.addEventListener('click', event => this.openSource(event), {signal: this.abort.signal});
      }
      if (!url) this.links = [];
      el.dataset.embedListo = '';
      if (this.provider === 'x' || !this.button) { instances.set(el, this); return; }
      if (!this.spec) { this.say('Esta publicación no tiene un identificador válido.'); instances.set(el, this); return; }
      const where = context(this.provider);
      if (where === 'source') {
        this.say(location.protocol === 'file:' ? SOURCE_ONLY.file : SOURCE_ONLY.sandbox);
      } else {
        this.button.hidden = false;
        this.button.addEventListener('click', event => this.load(event), {signal: this.abort.signal});
      }
      document.addEventListener('margen:embed-closed', () => { if (this.requested) { this.requested = false; this.button.focus(); } }, {signal: this.abort.signal});
      addEventListener('pagehide', () => this.unload(), {signal: this.abort.signal});
      instances.set(el, this);
    }
    say(text) { if (this.status) this.status.textContent = text; }
    async openSource(event) {
      const bridge = host();
      if (!bridge || typeof bridge.openSource !== 'function') return;
      event.preventDefault();
      try { await bridge.openSource(this.spec); } catch { this.say('No se pudo abrir la fuente. Copia el enlace: ' + sourceURL(this.spec)); }
    }
    async load(event) {
      if (this.dead || !event.isTrusted) return;
      if (navigator.onLine === false) { this.say('Sin conexión. El enlace abre la publicación cuando vuelva la red.'); return; }
      const bridge = host();
      if (bridge) {
        this.requested = true;
        this.say('Abriendo el reproductor…');
        try { await bridge.embed(this.spec); this.say('El reproductor está abierto en una ventana del portal.'); }
        catch { this.requested = false; this.say(NAMES[this.provider] + ' no está disponible aquí. El enlace abre la publicación.'); }
        return;
      }
      this.mount();
    }
    mount() {
      this.unload();
      const frame = document.createElement('iframe');
      frame.title = NAMES[this.provider] + ': publicación insertada';
      frame.setAttribute('sandbox', SANDBOX);
      frame.setAttribute('allow', ALLOW);
      frame.setAttribute('referrerpolicy', REFERRER[this.provider]);
      frame.className = 'embed-reproductor';
      frame.src = playerURL(this.spec, location.origin === 'null' ? null : location.origin);
      const target = this.stage || this.el;
      const close = document.createElement('button');
      close.type = 'button'; close.className = 'embed-quitar'; close.textContent = 'Quitar reproductor';
      const local = new AbortController();
      let alive = false, poke = 0;
      const timer = setTimeout(() => { if (!alive) this.say(NAMES[this.provider] + ' no respondió. El enlace abre la fuente original.'); }, WAIT);
      addEventListener('message', event => {
        if (event.source !== frame.contentWindow || event.origin !== ORIGINS[this.provider]) return;
        const s = signal(this.provider, event.data);
        if (!s) return;
        alive = true; clearInterval(poke);
        if (s.type === 'measure') frame.style.height = Math.min(s.height, 1200) + 'px';
        else if (s.type === 'error') this.say(errorText(this.provider, s.code) + ' El enlace abre la fuente original.');
        else if (s.type === 'playing') this.say('Reproduciendo sin sonido. El sonido se activa en el propio reproductor.');
      }, {signal: local.signal});
      if (this.provider === 'youtube') frame.addEventListener('load', () => {
        clearInterval(poke);
        let tries = 0;
        poke = setInterval(() => { if (++tries > 20 || alive) clearInterval(poke); else frame.contentWindow?.postMessage('{"event":"listening","id":1,"channel":"widget"}', ORIGINS.youtube); }, 400);
      }, {signal: local.signal});
      close.addEventListener('click', () => { this.unload(); this.say('Reproductor retirado.'); this.button.focus(); }, {signal: local.signal});
      this.player = {frame, close, stop: () => { clearTimeout(timer); clearInterval(poke); local.abort(); frame.src = 'about:blank'; frame.remove(); close.remove(); }};
      this.el.dataset.embedCargado = '';
      this.button.hidden = true;
      target.append(frame);
      this.button.after(close);
      this.say('Conectando con ' + NAMES[this.provider] + '…');
      close.focus();
    }
    unload() {
      if (!this.player) return;
      this.player.stop(); this.player = null;
      delete this.el.dataset.embedCargado;
      if (!this.dead && this.button) this.button.hidden = false;
    }
    destroy() {
      if (this.dead) return;
      this.unload(); this.dead = true; this.abort.abort();
      delete this.el.dataset.embedListo; instances.delete(this.el);
    }
  }

  // Construye una tarjeta de X con texto escapado (textContent), sin aceptar HTML.
  function card(data) {
    const make = (tag, cls, text) => { const n = document.createElement(tag); if (cls) n.className = cls; if (text !== undefined) n.textContent = String(text); return n; };
    const figure = make('figure', 'embed embed-x');
    figure.dataset.embed = 'x';
    if (data.synthetic) figure.dataset.embedSynthetic = '';
    if (data.user) figure.dataset.embedUser = String(data.user);
    if (data.status) figure.dataset.embedStatus = String(data.status);
    const head = make('header', 'embed-cabecera');
    const who = make('p', 'embed-autor');
    who.append(make('strong', '', data.name || ''), ' ', make('span', 'embed-handle', data.user ? '@' + data.user : ''));
    head.append(who, make('span', 'embed-proveedor', 'X'));
    const text = make('blockquote', 'embed-texto');
    String(data.text || '').split(/\n{2,}/).forEach(p => text.append(make('p', '', p)));
    figure.append(head, text);
    if (data.media && /^data:image\/(?:png|jpeg|gif|webp|avif);base64,[A-Za-z0-9+/=]+$/.test(data.media)) {
      const img = make('img', 'embed-media'); img.src = data.media; img.alt = String(data.alt || ''); figure.append(img);
    }
    const foot = make('figcaption', 'embed-pie');
    if (data.synthetic) foot.append(make('span', 'embed-sintetico', 'Ejemplo sintético'), ' · ');
    if (data.date) { const t = make('time', '', data.dateLabel || data.date); t.dateTime = String(data.date); foot.append(t, ' · '); }
    const a = make('a', '', 'Ver en X'); a.dataset.embedSource = ''; a.href = '#'; foot.append(a);
    figure.append(foot);
    return figure;
  }

  function init(root = document) {
    return [...(root.matches?.('[data-embed]') ? [root] : []), ...root.querySelectorAll('[data-embed]')].map(el => instances.get(el) || new MargenEmbed(el));
  }
  window.MargenEmbeds = {init, get: el => instances.get(el), destroy: el => instances.get(el)?.destroy(), normalize, sourceURL, playerURL, signal, card, SANDBOX, ALLOW, REFERRER, ORIGINS};
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => init(), {once: true});
  else init();
})();
