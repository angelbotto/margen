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
  // Cualquier enlace del documento. El portal decide qué ofrece; nada se abre sin un clic en su propio diálogo.
  // https/http/mailto/tel llevan destino; credenciales, relativos y otros esquemas sólo se explican.
  function external(data) {
    if (!data || typeof data !== 'object' || Array.isArray(data) || Object.keys(data).some(k => k !== 'href' && k !== 'version')) return null;
    const {href, version} = data;
    if (typeof version !== 'string' || !/^[A-Za-z0-9_-]{1,80}$/.test(version)) return null;
    if (typeof href !== 'string' || !href || href.length > 2048 || /[\s<>"'`\\\x00-\x1f\x7f]/.test(href)) return null;
    if (/^mailto:[^@/?#:]+@[^@/?#:]+\.[^@/?#:]+(?:\?[^#]*)?$/i.test(href)) return {kind: 'mailto', href, shown: href.slice(7).split('?')[0], version};
    if (/^tel:\+?[0-9().-]{3,30}$/i.test(href)) return {kind: 'tel', href, shown: href.slice(4), version};
    if (/^https?:/i.test(href)) {
      let url;
      try { url = new URL(href); } catch { return null; }
      if (!url.hostname || !/^https?:$/.test(url.protocol) || !/^https?:\/\//i.test(href)) return null;
      if (url.username || url.password) return {kind: 'credentials', shown: url.hostname, version};
      return {kind: url.protocol === 'https:' ? 'https' : 'http', href: url.href, shown: url.hostname, version};
    }
    if (/^[A-Za-z][A-Za-z0-9+.-]*:/.test(href)) return {kind: 'scheme', shown: href.split(':')[0].slice(0, 20) + ':', version};
    return {kind: 'relative', shown: href.slice(0, 120), version};
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

  /* options: frame() → iframe del artefacto; mounted() → {artifact, version} vigente; origin; userActivation() opcional.
     El iframe es opaco y no es de fiar: su activación puede venir de cualquier clic del documento. Por eso nada sale
     del portal (pestaña, correo, proveedor) hasta un clic en un control de este diálogo, que el artefacto no alcanza. */
  function create(options) {
    const dialog = make('dialog', {class: 'media-dialog', 'aria-labelledby': 'media-dialog-title', 'aria-describedby': 'media-dialog-notice'});
    const title = make('h2', {id: 'media-dialog-title'});
    const close = make('button', {type: 'button', class: 'icon', 'aria-label': 'Cerrar'}, '×');
    const head = make('div', {class: 'dialog-head'});
    head.append(title, close);
    const preview = make('div', {class: 'media-preview'});
    const tag = make('span', {class: 'media-tag'});
    const place = make('strong', {class: 'media-place'});
    const address = make('span', {class: 'media-address'});
    preview.append(tag, place, address);
    const notice = make('p', {class: 'media-notice', id: 'media-dialog-notice'});
    const stage = make('div', {class: 'media-stage'});
    const status = make('p', {class: 'media-status', role: 'status'});
    const start = make('button', {type: 'button', class: 'primary media-play'});
    const link = make('a', {class: 'media-source button', referrerpolicy: 'no-referrer'});
    const actions = make('div', {class: 'media-actions'});
    actions.append(start, link);
    dialog.append(head, preview, notice, stage, status, actions);
    document.body.append(dialog);
    let session = null;

    function teardown() {
      if (!session) return;
      const s = session; session = null;
      clearTimeout(s.timer); clearInterval(s.poke); s.abort.abort();
      if (s.player) { s.player.src = 'about:blank'; s.player.remove(); }
      stage.replaceChildren(); status.textContent = ''; dialog.dataset.provider = ''; dialog.dataset.intent = '';
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
    // El único camino al proveedor: un clic real en el botón del portal, ligado a la sesión que lo mostró.
    start.addEventListener('click', event => {
      if (event.isTrusted && session?.spec && !session.player) play(session.spec, session);
    });
    // El enlace del portal navega por sí mismo (pestaña nueva sin opener ni referrer, o mailto/tel); luego el diálogo sobra.
    link.addEventListener('click', event => { if (event.isTrusted && session) setTimeout(() => dialog.close()); });

    function begin(provider, intent) {
      if (dialog.open) dialog.close();
      teardown();
      const now = options.mounted();
      session = {artifact: now.artifact, version: now.version, abort: new AbortController(), timer: 0, poke: 0, player: null, alive: false, spec: null};
      dialog.dataset.provider = provider;
      dialog.dataset.intent = intent;
      preview.hidden = false; start.hidden = true;
      return session;
    }
    function show(heading, kind, where, full, text) {
      title.textContent = heading; tag.textContent = kind; place.textContent = where; address.textContent = full || '';
      notice.textContent = text;
      dialog.showModal();
    }
    function target(href, label, tab) {
      link.hidden = !href;
      if (!href) { link.removeAttribute('href'); return; }
      link.href = href; link.textContent = label;
      link.classList.toggle('primary', dialog.dataset.intent === 'link');
      if (tab) { link.target = '_blank'; link.rel = 'noopener noreferrer'; }
      else { link.removeAttribute('target'); link.rel = 'noreferrer'; }
    }

    function play(spec, s) {
      const player = make('iframe', {
        title: NAMES[spec.provider] + ': publicación insertada', sandbox: SANDBOX, allow: ALLOW,
        referrerpolicy: REFERRER[spec.provider], class: 'media-player', src: playerURL(spec, options.origin),
      });
      s.player = player;
      dialog.dataset.intent = 'player'; preview.hidden = true; start.hidden = true;
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
      close.focus();
      return {ok: true};
    }

    // Vista previa sin red: proveedor y fuente exacta. El reproductor se monta sólo con «Reproducir aquí».
    function confirmPlay(spec) {
      const s = begin(spec.provider, 'confirm');
      s.spec = spec;
      const video = spec.provider === 'youtube';
      target(sourceURL(spec), 'Abrir en ' + NAMES[spec.provider], true);
      start.textContent = video ? 'Reproducir aquí' : 'Cargar aquí';
      start.hidden = false;
      show((video ? 'Video de ' : 'Publicación de ') + NAMES[spec.provider], NAMES[spec.provider] + (video ? ' · video' : ' · publicación'),
        new URL(sourceURL(spec)).hostname.replace(/^www\./, ''), sourceURL(spec),
        'Al reproducirlo, tu navegador se conecta con ' + NAMES[spec.provider] + '. Hasta entonces no se le pide nada.');
      start.focus();
      return {ok: true, confirm: true};
    }

    const KINDS = {https: 'Enlace externo', http: 'Enlace http · sin cifrar', mailto: 'Correo', tel: 'Teléfono'};
    const ACTIONS = {https: 'Abrir en pestaña nueva', http: 'Abrir en pestaña nueva', mailto: 'Escribir correo', tel: 'Llamar'};
    // El destino se muestra entero antes de salir; el clic en el enlace del portal es la intención.
    function leave(kind, href, shown, heading = 'Abrir enlace', label = ACTIONS[kind]) {
      begin('link', 'link');
      const tab = kind === 'https' || kind === 'http';
      target(href, label, tab);
      show(heading, KINDS[kind], shown, href.replace(/^(?:mailto|tel):/, ''), tab ? 'Sale de Margen y se abre en una pestaña nueva, sin datos de esta página.' : 'Se abre con la aplicación de tu equipo.');
      link.focus();
      return {ok: true, confirm: true};
    }
    const WHY = {
      credentials: 'Lleva usuario y contraseña dentro de la dirección. Margen no lo abre para no exponerlos.',
      relative: 'Apunta a un archivo que acompañaba al documento original y no está publicado en Margen.',
      scheme: 'Margen abre enlaces web, de correo y de teléfono. Éste usa otro tipo de dirección.',
    };
    function explain(kind, shown) {
      begin('link', 'info');
      target(null);
      show('Este enlace no se abre aquí', 'Enlace no disponible', shown, '', WHY[kind]);
      close.focus();
      return {ok: true, opened: false};
    }

    function activation() {
      if (options.userActivation) return options.userActivation();
      return navigator.userActivation ? navigator.userActivation.isActive : null;
    }

    function handle(op, data) {
      const now = options.mounted();
      if (!now) throw Error('No hay un documento abierto.');
      // Sin clic reciente del lector no se muestra ni el diálogo: así el documento no puede insistir.
      if (activation() === false) throw Error('Hace falta un clic del lector.');
      if (op === 'external') {
        const link = external(data);
        if (!link) throw Error('Enlace no permitido.');
        if (link.version !== now.version) throw Error('Enlace de otra versión.');
        return link.href ? leave(link.kind, link.href, link.shown) : explain(link.kind, link.shown);
      }
      const spec = validate(data);
      if (!spec) throw Error('Publicación no válida.');
      if (spec.version !== now.version) throw Error('Publicación de otra versión.');
      if (op === 'embed') {
        if (spec.provider === 'x') throw Error('X no se inserta; abre la fuente.');
        return confirmPlay(spec);
      }
      if (op === 'open-source') {
        const href = sourceURL(spec);
        return leave('https', href, new URL(href).hostname.replace(/^www\./, ''), 'Abrir la fuente', 'Abrir en ' + NAMES[spec.provider]);
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
