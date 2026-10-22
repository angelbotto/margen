/* Margen · Guardar y «Me gusta» del lector, siempre en el DOM del portal.
   El artefacto (iframe opaco) sólo puede pedir dónde dibujar el ancla bajo «En esta página»; nunca muta.
   El ancla abre un diálogo del portal con retardo de intención; el dock fijo actúa con un clic real. */
(() => {
  'use strict';
  const HEADER = 'X-Margen-Reader-Action';
  const INTENT_DELAY = 650;
  const SLOT_HEIGHT = 44;
  const DOCK_WAIT = 1200;
  const ANCHOR_KEYS = ['visible', 'slot', 'x', 'y', 'width', 'height', 'vw', 'vh'];

  const make = (tag, attrs = {}, text) => {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const ICONS = {saved: '<path d="M7 4h10v16l-5-4-5 4Z"/>', liked: '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10Z"/>'};
  const icon = (node, key, count) => {
    node.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true">' + ICONS[key] + '</svg>';
    if (count) node.append(make('span', {class: 'reader-action-count', 'aria-hidden': 'true'}, String(count)));
  };
  const finite = (v, min, max) => typeof v === 'number' && Number.isFinite(v) && v >= min && v <= max;

  // Esquema exacto del ancla: sólo geometría acotada dentro del viewport del iframe.
  function validateAnchor(data) {
    if (!data || typeof data !== 'object' || Array.isArray(data)) return null;
    const keys = Object.keys(data);
    if (keys.some(k => !ANCHOR_KEYS.includes(k)) || typeof data.visible !== 'boolean') return null;
    if (data.slot !== undefined && data.slot !== true) return null;
    if (!data.visible) return keys.length === 1 + (data.slot ? 1 : 0) ? {visible: false, slot: !!data.slot} : null;
    if (data.slot !== undefined) return null;
    const {x, y, width, height, vw, vh} = data;
    if (!finite(vw, 1, 10000) || !finite(vh, 1, 10000)) return null;
    if (!finite(width, 40, Math.min(vw, 640)) || !finite(height, 24, 96)) return null;
    if (!finite(x, 0, vw - width) || !finite(y, -height, vh)) return null;
    return {visible: true, x, y, width, height, vw, vh};
  }

  async function request(url, init) {
    const response = await fetch(url, {credentials: 'same-origin', ...init});
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw Object.assign(Error(body.detail || 'No se pudo completar.'), {status: response.status});
    return body;
  }

  function create(options) {
    const frame = () => options.frame();
    let current = null, state = null, anchored = false, dockTimer = 0, busy = false, geometry = null;

    // Dock fijo: sin ancla (presentaciones, HTML propio) los botones viven aquí y actúan directo.
    const dock = make('div', {class: 'reader-actions-dock', role: 'group', 'aria-label': 'Acciones de lectura', hidden: ''});
    const dockSave = make('button', {type: 'button', class: 'dock-button reader-action', 'data-action': 'saved', 'aria-pressed': 'false'});
    const dockLike = make('button', {type: 'button', class: 'dock-button reader-action', 'data-action': 'liked', 'aria-pressed': 'false'});
    dock.append(dockSave, dockLike);

    // Ancla: botones del portal superpuestos al hueco del documento; sólo abren el diálogo.
    const overlay = make('div', {class: 'reader-actions-anchor', role: 'group', 'aria-label': 'Acciones de lectura de este documento', hidden: ''});
    const anchorSave = make('button', {type: 'button', class: 'reader-action', 'data-action': 'saved', 'aria-haspopup': 'dialog'});
    const anchorLike = make('button', {type: 'button', class: 'reader-action', 'data-action': 'liked', 'aria-haspopup': 'dialog'});
    overlay.append(anchorSave, anchorLike);

    const dialog = make('dialog', {class: 'reader-actions-dialog', 'aria-labelledby': 'reader-actions-heading'});
    const head = make('div', {class: 'dialog-head'});
    const heading = make('h2', {id: 'reader-actions-heading'}, 'Guardar o marcar');
    const close = make('button', {type: 'button', class: 'icon', 'aria-label': 'Cerrar'}, '×');
    head.append(heading, close);
    const subject = make('p', {class: 'reader-actions-title'});
    const choices = make('div', {class: 'reader-actions-choices'});
    const save = make('button', {type: 'button', class: 'reader-action', 'data-action': 'saved', 'aria-pressed': 'false'});
    const like = make('button', {type: 'button', class: 'reader-action', 'data-action': 'liked', 'aria-pressed': 'false'});
    choices.append(save, like);
    const status = make('p', {class: 'reader-actions-status', role: 'status'});
    const savedLink = make('a', {class: 'reader-actions-saved', hidden: ''}, 'Ver mis guardados');
    const login = make('a', {class: 'button primary reader-actions-login', hidden: ''}, 'Entrar para guardar');
    dialog.append(head, subject, choices, status, savedLink, login);
    const announce = make('p', {class: 'reader-actions-live', role: 'status'});

    let session = null;
    function paint() {
      const s = state || {saved: false, liked: false, likes: 0, can_act: false};
      const likes = s.likes ? ' · ' + s.likes : '';
      for (const b of [anchorSave, save]) b.textContent = s.saved ? 'Guardado' : 'Guardar';
      for (const b of [anchorLike, like]) b.textContent = 'Me gusta' + likes;
      icon(dockSave, 'saved'); icon(dockLike, 'liked', s.likes);
      for (const b of [dockSave, anchorSave, save]) {
        b.setAttribute('aria-label', s.saved ? 'Guardado en tu lista. Quitar de guardados' : 'Guardar en tu lista');
      }
      for (const b of [dockLike, anchorLike, like]) {
        b.setAttribute('aria-label', (s.liked ? 'Te gusta. Quitar me gusta' : 'Me gusta') + (s.likes ? '. ' + s.likes + (s.likes === 1 ? ' cuenta lo marcó' : ' cuentas lo marcaron') : ''));
      }
      for (const b of [dockSave, save]) b.setAttribute('aria-pressed', String(!!s.saved));
      for (const b of [dockLike, like]) b.setAttribute('aria-pressed', String(!!s.liked));
      anchorSave.dataset.on = String(!!s.saved); anchorLike.dataset.on = String(!!s.liked);
      // Sin cuenta verificada se ve el total, pero sólo el diálogo explica cómo entrar.
      for (const b of [dockSave, dockLike]) b.disabled = busy;
      save.hidden = like.hidden = !s.can_act;
      login.hidden = s.can_act;
      if (current) login.href = '/login?next=' + encodeURIComponent('/a/' + current.id);
      savedLink.href = s.saved_path || '/?view=saved';
      savedLink.hidden = !(s.can_act && s.saved);
    }

    async function apply(key, value) {
      if (!current || busy) return;
      const artifact = current.id;
      busy = true; paint();
      try {
        const next = await request('/api/artifacts/' + encodeURIComponent(artifact) + '/reader-actions', {
          method: 'PUT', headers: {'Content-Type': 'application/json', [HEADER]: '1'}, body: JSON.stringify({[key]: value}),
        });
        if (current?.id !== artifact) return;
        state = next;
        const said = key === 'saved' ? (value ? 'Guardado en tu lista.' : 'Quitado de guardados.') : (value ? 'Marcaste me gusta.' : 'Quitaste me gusta.');
        status.textContent = announce.textContent = said;
        options.toast?.(said, key === 'saved' && value ? {href: next.saved_path, label: 'Ver guardados'} : null);
      } catch (error) {
        status.textContent = announce.textContent = error.status === 401 ? 'Inicia sesión con tu correo para guardar.' : error.message;
      } finally {
        busy = false; paint();
      }
    }

    // Repetición de tecla o doble clic heredados del documento no cruzan al diálogo.
    for (const control of [save, like]) {
      control.addEventListener('pointerdown', event => {
        if (session) session.pointer = event.isTrusted && performance.now() >= session.readyAt ? control : null;
      });
      control.addEventListener('keydown', event => {
        if (!['Enter', ' '].includes(event.key)) return;
        if (session) session.repeatedKey = event.repeat;
        if (event.repeat || !session || performance.now() < session.readyAt) event.preventDefault();
      });
      control.addEventListener('keyup', event => {
        if (session?.repeatedKey && ['Enter', ' '].includes(event.key)) event.preventDefault();
      });
      control.addEventListener('click', event => {
        const s = session;
        const ok = event.isTrusted && s && !control.disabled && performance.now() >= s.readyAt && event.detail <= 1 &&
          (event.detail === 0 ? !s.repeatedKey : s.pointer === control) && s.artifact === current?.id;
        if (s) s.pointer = null;
        if (!ok) { event.preventDefault(); return; }
        apply(control.dataset.action, !state?.[control.dataset.action]);
      });
    }
    for (const control of [dockSave, dockLike]) {
      control.addEventListener('click', event => {
        if (!event.isTrusted || event.detail > 1 || !state) return;
        if (!state.can_act) { open(control); return; }
        apply(control.dataset.action, !state[control.dataset.action]);
      });
    }
    for (const control of [anchorSave, anchorLike]) control.addEventListener('click', event => { if (event.isTrusted) open(control); });
    close.addEventListener('click', () => dialog.close());
    dialog.addEventListener('close', () => {
      if (dialog.open) return;
      const s = session; session = null;
      if (s) clearTimeout(s.timer);
      place();
      if (s?.opener?.isConnected && !s.opener.closest('[hidden]')) s.opener.focus();
      else frame()?.focus();
    });

    function open(opener) {
      if (!current) return;
      if (session) clearTimeout(session.timer);
      const s = session = {artifact: current.id, readyAt: performance.now() + INTENT_DELAY, pointer: null, repeatedKey: false, timer: 0, opener};
      subject.textContent = current.title || 'Este documento';
      status.textContent = state?.can_act ? '' : 'Guardar y marcar requieren una cuenta con correo verificado. El total es visible para quien puede leerlo.';
      save.disabled = like.disabled = true;
      paint();
      if (!dialog.open) dialog.showModal();
      close.focus();
      s.timer = setTimeout(() => { if (session === s) { save.disabled = like.disabled = false; } }, INTENT_DELAY);
    }

    function place() {
      const f = frame();
      if (!anchored || !geometry?.visible || !f || dialog.open) { overlay.hidden = true; return; }
      const box = f.getBoundingClientRect();
      if (!box.width || !box.height) { overlay.hidden = true; return; }
      const scale = box.width / geometry.vw;
      const left = box.left + geometry.x * scale, top = box.top + geometry.y * scale;
      const width = geometry.width * scale, height = geometry.height * scale;
      // Recorte estricto: un ancla fuera de la caja visible del iframe no se dibuja.
      if (top < box.top || top + height > box.bottom || left < box.left || left + width > box.right) { overlay.hidden = true; return; }
      Object.assign(overlay.style, {left: left + 'px', top: top + 'px', width: width + 'px', height: height + 'px'});
      overlay.hidden = false;
    }
    addEventListener('resize', place, {passive: true});

    function showDock() {
      clearTimeout(dockTimer);
      dock.hidden = !current || anchored || !state;
    }

    function offer() {
      frame()?.contentWindow?.postMessage({bottifact: 1, op: 'reader-actions-slot', height: SLOT_HEIGHT}, '*');
    }

    function mountNodes() {
      const host = options.dock?.();
      if (host && dock.parentElement !== host) host.append(dock);
      const f = frame();
      if (f?.parentElement && overlay.nextElementSibling !== f) f.before(overlay);
      if (!dialog.isConnected) document.body.append(dialog, announce);
    }

    return {
      surface(color) {
        const valid = Array.isArray(color) && color.length === 3 && color.every(c => Number.isInteger(c) && c >= 0 && c <= 255);
        const channels = valid ? color.map(c => c / 255).map(c => c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4) : [];
        const dark = valid && channels[0] * .2126 + channels[1] * .7152 + channels[2] * .0722 < .179;
        for (const node of [dock, overlay, dialog]) {
          if (!valid) { for (const key of ['--bg', '--ink', '--line', '--muted']) node.style.removeProperty(key); continue; }
          node.style.setProperty('--bg', 'rgb(' + color.join(',') + ')');
          node.style.setProperty('--ink', dark ? '#fff' : '#000');
          node.style.setProperty('--line', 'color-mix(in srgb,var(--ink) 24%,var(--bg))');
          node.style.setProperty('--muted', 'color-mix(in srgb,var(--ink) 75%,var(--bg))');
        }
      },
      async load(artifact) {
        mountNodes();
        current = artifact && typeof artifact.id === 'string' ? {id: artifact.id, title: String(artifact.title || '')} : null;
        state = null; anchored = false; geometry = null; overlay.hidden = true; dock.hidden = true;
        if (dialog.open) dialog.close();
        if (!current) return null;
        const id = current.id;
        try {
          const next = await request('/api/artifacts/' + encodeURIComponent(id) + '/reader-actions');
          if (current?.id !== id) return null;
          state = next;
        } catch { return null; }
        paint();
        dockTimer = setTimeout(showDock, DOCK_WAIT);
        offer();
        return state;
      },
      // Lo único que acepta del artefacto: geometría validada. Nunca cambia estado ni dispara acciones.
      anchor(data) {
        const value = validateAnchor(data);
        if (!value || !current || !state) return {ok: false};
        if (value.slot) { offer(); return {ok: true}; }
        if (!anchored) { anchored = true; clearTimeout(dockTimer); dock.hidden = true; }
        geometry = value; place();
        return {ok: true};
      },
      reset() { current = null; state = null; anchored = false; geometry = null; clearTimeout(dockTimer); overlay.hidden = dock.hidden = true; if (dialog.open) dialog.close(); },
      get state() { return state; },
      nodes: {dock, overlay, dialog},
    };
  }

  // Lista privada de guardados; el servidor ya excluye lo que hoy no se puede leer.
  async function renderSaved(container) {
    container.replaceChildren(make('p', {class: 'muted', role: 'status'}, 'Cargando guardados…'));
    let result;
    try { result = await request('/api/reader/saved'); }
    catch (error) {
      container.replaceChildren(make('p', {class: 'form-error', role: 'alert'}, error.status === 401 ? 'Inicia sesión para ver tus guardados.' : error.message));
      return null;
    }
    const heading = make('h2', {class: 'reader-saved-heading', tabindex: '-1'}, 'Guardados');
    if (!result.artifacts.length) {
      const empty = make('div', {class: 'reader-saved-empty'});
      empty.append(make('p', {}, 'Aquí vuelves a lo que quieres seguir leyendo.'),
        make('p', {class: 'muted'}, 'Abre un documento y toca «Guardar» bajo «En esta página», o en la barra del lector. Sólo tú ves esta lista.'));
      container.replaceChildren(heading, empty);
      return result;
    }
    const list = make('ol', {class: 'reader-saved-list'});
    for (const a of result.artifacts) {
      const item = make('li');
      const link = make('a', {href: a.url}, a.title);
      const when = new Date(a.saved * 1000);
      const meta = make('span', {class: 'muted'}, a.space + ' · guardado ' + when.toLocaleDateString('es', {day: 'numeric', month: 'short', year: 'numeric'}));
      item.append(link, meta);
      list.append(item);
    }
    container.replaceChildren(heading, list);
    return result;
  }

  window.MargenReaderActions = {create, validateAnchor, renderSaved};
})();
