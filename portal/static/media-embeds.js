/* Margen · reproductores de YouTube e Instagram montados por el portal, nunca por el artefacto.
   El artefacto sólo pide proveedor + ID; la URL sale de una tabla fija. El artefacto conserva su sandbox opaco. */
(() => {
  'use strict';
  const NAMES = {x: 'X', youtube: 'YouTube', instagram: 'Instagram'};
  const ORIGINS = {youtube: 'https://www.youtube-nocookie.com', instagram: 'https://www.instagram.com'};
  const REFERRER = {youtube: 'strict-origin', instagram: 'no-referrer'};
  const SANDBOX = 'allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox allow-presentation';
  const ALLOW = 'autoplay; encrypted-media; picture-in-picture; fullscreen';
  const WAIT = 8000;
  const YT_ERRORS = {2: 'El video no tiene un identificador válido.', 5: 'Este navegador no puede reproducir el video aquí.', 100: 'El video no existe o es privado.', 101: 'Quien lo publicó no permite verlo insertado.', 150: 'Quien lo publicó no permite verlo insertado.', 153: 'YouTube no aceptó esta página como origen.'};
  const KEYS = {youtube: ['provider', 'id', 'version'], instagram: ['provider', 'id', 'kind', 'version'], x: ['provider', 'user', 'status', 'version']};

  // Esquema exacto: proveedor conocido, sólo sus campos, tipos y longitudes fijos.
  function validate(data) {
    if (!data || typeof data !== 'object' || Array.isArray(data) || !Object.hasOwn(KEYS, data.provider)) return null;
    const keys = Object.keys(data);
    if (keys.some(k => !KEYS[data.provider].includes(k))) return null;
    if (typeof data.version !== 'string' || !/^[A-Za-z0-9_-]{1,80}$/.test(data.version)) return null;
    const {provider, version} = data;
    if (provider === 'youtube')
      return typeof data.id === 'string' && /^[A-Za-z0-9_-]{11}$/.test(data.id) ? {provider, id: data.id, version} : null;
    if (provider === 'instagram')
      return typeof data.id === 'string' && /^[A-Za-z0-9_-]{5,40}$/.test(data.id) && (data.kind === 'p' || data.kind === 'reel') ? {provider, id: data.id, kind: data.kind, version} : null;
    if (typeof data.user !== 'string' || !/^[A-Za-z0-9_]{1,15}$/.test(data.user)) return null;
    if (data.status === undefined) return {provider, user: data.user, version};
    return typeof data.status === 'string' && /^[0-9]{1,20}$/.test(data.status) ? {provider, user: data.user, status: data.status, version} : null;
  }
  function sourceURL(s) {
    if (s.provider === 'youtube') return 'https://www.youtube.com/watch?v=' + s.id;
    if (s.provider === 'instagram') return 'https://www.instagram.com/' + s.kind + '/' + s.id + '/';
    return 'https://x.com/' + s.user + (s.status ? '/status/' + s.status : '');
  }
  // Enlaces generales del documento (p. ej. el pie): https sin credenciales o mailto con dirección, sin controles.
  function external(data) {
    if (!data || typeof data !== 'object' || Array.isArray(data) || Object.keys(data).some(k => k !== 'href' && k !== 'version')) return null;
    const {href, version} = data;
    if (typeof version !== 'string' || !/^[A-Za-z0-9_-]{1,80}$/.test(version)) return null;
    if (typeof href !== 'string' || href.length > 2048 || /[\s<>"'`\\\x00-\x1f\x7f]/.test(href)) return null;
    if (/^mailto:[^@/?#:]+@[^@/?#:]+\.[^@/?#:]+(?:\?[^#]*)?$/.test(href)) return {href, version};
    if (!/^https:\/\//i.test(href)) return null;
    let url;
    try { url = new URL(href); } catch { return null; }
    if (url.protocol !== 'https:' || !url.hostname || url.username || url.password) return null;
    return {href: url.href, version};
  }
  function playerURL(s, origin) {
    if (s.provider === 'instagram') return ORIGINS.instagram + '/' + s.kind + '/' + s.id + '/embed/';
    if (s.provider !== 'youtube') return null;
    const params = new URLSearchParams({autoplay: '1', mute: '1', playsinline: '1', rel: '0', enablejsapi: '1', origin});
    return ORIGINS.youtube + '/embed/' + s.id + '?' + params;
  }
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
    if (m.type === 'MEASURE') {
      const h = m.details && m.details.height;
      return typeof h === 'number' && h > 0 && h < 4000 ? {type: 'measure', height: Math.round(h)} : {type: 'alive'};
    }
    return m.type === 'MOUNTED' || m.type === 'LOADING' ? {type: 'alive'} : null;
  }

  function make(tag, attrs = {}, text) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
    if (text !== undefined) node.textContent = text;
    return node;
  }

  /* options: frame() → iframe del artefacto; mounted() → {artifact, version} vigente; origin; userActivation() opcional. */
  function create(options) {
    const dialog = make('dialog', {class: 'media-dialog', 'aria-labelledby': 'media-dialog-title'});
    const title = make('h2', {id: 'media-dialog-title'});
    const close = make('button', {type: 'button', class: 'icon', 'aria-label': 'Cerrar'}, '×');
    const head = make('div', {class: 'dialog-head'});
    head.append(title, close);
    const notice = make('p', {class: 'media-notice'});
    const stage = make('div', {class: 'media-stage'});
    const status = make('p', {class: 'media-status', role: 'status'});
    const link = make('a', {target: '_blank', rel: 'noopener noreferrer', referrerpolicy: 'no-referrer', class: 'media-source'});
    dialog.append(head, notice, stage, status, link);
    document.body.append(dialog);
    let session = null;

    function teardown() {
      if (!session) return;
      const s = session; session = null;
      clearTimeout(s.timer); clearInterval(s.poke); s.abort.abort();
      if (s.player) { s.player.src = 'about:blank'; s.player.remove(); }
      stage.replaceChildren(); status.textContent = ''; dialog.dataset.provider = '';
      return s;
    }
    close.addEventListener('click', () => dialog.close());
    dialog.addEventListener('close', () => {
      // Un cierre previo a reabrir llega tarde: no debe desmontar la sesión nueva.
      if (dialog.open) return;
      const s = teardown();
      // Devuelve el foco al documento que lo pidió, sólo si sigue montado; el artefacto lo pasa a su botón.
      const frame = options.frame(), now = options.mounted();
      if (s && now && now.artifact === s.artifact && now.version === s.version && frame?.contentWindow) {
        frame.focus();
        frame.contentWindow.postMessage({bottifact: 1, op: 'embed-closed'}, '*');
      }
    });

    function begin(provider, href, label) {
      if (dialog.open) dialog.close();
      teardown();
      const now = options.mounted();
      session = {artifact: now.artifact, version: now.version, abort: new AbortController(), timer: 0, poke: 0, player: null, alive: false};
      dialog.dataset.provider = provider;
      link.href = href;
      link.textContent = label;
      return session;
    }

    function play(spec, s = begin(spec.provider, sourceURL(spec), 'Abrir en ' + NAMES[spec.provider])) {
      title.textContent = (spec.provider === 'youtube' ? 'Video de ' : 'Publicación de ') + NAMES[spec.provider];
      notice.textContent = 'Al cargarlo, tu navegador se conecta con ' + NAMES[spec.provider] + '.';
      const player = make('iframe', {
        title: NAMES[spec.provider] + ': publicación insertada', sandbox: SANDBOX, allow: ALLOW,
        referrerpolicy: REFERRER[spec.provider], class: 'media-player', src: playerURL(spec, options.origin),
      });
      s.player = player;
      const say = text => { if (session === s) status.textContent = text; };
      addEventListener('message', event => {
        if (session !== s || event.source !== player.contentWindow || event.origin !== ORIGINS[spec.provider]) return;
        const sig = signal(spec.provider, event.data);
        if (!sig) return;
        if (!s.alive && sig.type !== 'error' && sig.type !== 'playing') say('');
        s.alive = true; clearInterval(s.poke);
        if (sig.type === 'measure') player.style.height = Math.min(Math.max(sig.height, 200), 3000) + 'px';
        else if (sig.type === 'error') say(((spec.provider === 'youtube' && YT_ERRORS[sig.code]) || NAMES[spec.provider] + ' no pudo mostrar la publicación.') + ' El enlace abre la fuente original.');
        else if (sig.type === 'playing') say('Reproduciendo sin sonido. Actívalo en el propio reproductor.');
      }, {signal: s.abort.signal});
      if (spec.provider === 'youtube') player.addEventListener('load', () => {
        clearInterval(s.poke);
        let tries = 0;
        s.poke = setInterval(() => {
          if (session !== s || s.alive || ++tries > 20) clearInterval(s.poke);
          else player.contentWindow?.postMessage('{"event":"listening","id":1,"channel":"widget"}', ORIGINS.youtube);
        }, 400);
      }, {signal: s.abort.signal});
      // Que el iframe cargue no prueba nada: sin señal del reproductor se dice con honestidad.
      s.timer = setTimeout(() => { if (!s.alive) say(NAMES[spec.provider] + ' no respondió. El enlace abre la fuente original.'); }, WAIT);
      stage.replaceChildren(player);
      status.textContent = 'Conectando con ' + NAMES[spec.provider] + '…';
      if (!dialog.open) dialog.showModal();
      close.focus();
      return {ok: true};
    }

    // Sin API de activación no hay prueba del clic: el lector confirma con un botón del propio portal.
    function confirmPlay(spec) {
      const s = begin(spec.provider, sourceURL(spec), 'Abrir en ' + NAMES[spec.provider]);
      title.textContent = (spec.provider === 'youtube' ? 'Video de ' : 'Publicación de ') + NAMES[spec.provider];
      notice.textContent = 'Al cargarlo, tu navegador se conecta con ' + NAMES[spec.provider] + '.';
      const load = make('button', {type: 'button', class: 'primary'}, 'Cargar aquí');
      load.addEventListener('click', event => { if (event.isTrusted && session === s) play(spec, s); }, {signal: s.abort.signal});
      stage.replaceChildren(load);
      dialog.showModal();
      load.focus();
      return {ok: true, confirm: true};
    }

    function fallback(provider, href, label, heading, text) {
      begin(provider, href, label);
      title.textContent = heading;
      notice.textContent = text;
      dialog.showModal();
      link.focus();
      return {ok: true, opened: false};
    }

    function activation() {
      if (options.userActivation) return options.userActivation();
      return navigator.userActivation ? navigator.userActivation.isActive : null;
    }

    // Abre sólo con un clic real del lector; window.open consume esa activación, así que un clic abre como mucho una pestaña.
    function open(href) {
      if (href.startsWith('mailto:')) {
        const a = make('a', {href});
        a.click();
        return true;
      }
      // Sin noopener para poder detectar el bloqueo; el vínculo se corta antes de navegar.
      const opened = window.open('', '_blank');
      if (!opened) return false;
      opened.opener = null;
      opened.location.replace(href);
      return true;
    }

    function handle(op, data) {
      const now = options.mounted();
      if (!now) throw Error('No hay un documento abierto.');
      const active = activation();
      // Un mensaje sin clic del lector no abre diálogos ni pestañas: así el documento no puede insistir.
      if (active === false) throw Error('Hace falta un clic del lector.');
      if (op === 'external') {
        const target = external(data);
        if (!target) throw Error('Enlace no permitido.');
        if (target.version !== now.version) throw Error('Enlace de otra versión.');
        if (active && open(target.href)) return {ok: true, opened: true};
        const shown = target.href.startsWith('mailto:') ? target.href.slice(7) : target.href;
        return fallback('link', target.href, shown, 'Abrir enlace', 'Este enlace sale de Margen y se abre en una pestaña nueva.');
      }
      const spec = validate(data);
      if (!spec) throw Error('Publicación no válida.');
      if (spec.version !== now.version) throw Error('Publicación de otra versión.');
      if (op === 'embed') {
        if (spec.provider === 'x') throw Error('X no se inserta; abre la fuente.');
        return active ? play(spec) : confirmPlay(spec);
      }
      if (op === 'open-source') {
        if (active && open(sourceURL(spec))) return {ok: true, opened: true};
        return fallback(spec.provider, sourceURL(spec), 'Abrir en ' + NAMES[spec.provider], 'Abrir la fuente', 'La publicación original se abre en ' + NAMES[spec.provider] + ', en una pestaña nueva.');
      }
      throw Error('Operación no permitida.');
    }

    function reset() { if (dialog.open) dialog.close(); teardown(); }
    addEventListener('pagehide', reset);
    addEventListener('popstate', reset);
    return {handle, reset, dialog};
  }

  window.MargenMediaEmbeds = {create, validate, external, sourceURL, playerURL, signal, SANDBOX, ALLOW, REFERRER, ORIGINS};
})();
