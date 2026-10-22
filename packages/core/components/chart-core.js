/* Margen · núcleo común de gráficas. Escalas 1-2-5, formato por idioma, paleta de 8 con patrones,
   tip accesible (puntero, teclado, táctil), redibujo por ancho real, leyenda que aísla y exportación.
   Sin dependencias. Debe cargarse antes de charts.js, analytics.js, reports.js, evidence.js y attention-map.js. */
(() => {
  'use strict';
  if (window.MargenGraficas) return;
  const NS = 'http://www.w3.org/2000/svg';
  let serial = 0;
  const uid = prefix => (prefix || 'mg') + '-' + (++serial);

  // ---------- Números y escalas ----------
  const clean = v => { const n = +v.toPrecision(12); return Object.is(n, -0) ? 0 : n; };
  function nice(min, max, count = 5) {
    if (!Number.isFinite(min) || !Number.isFinite(max)) throw new TypeError('Dominio no finito.');
    if (min > max) [min, max] = [max, min];
    if (min === max) { const pad = Math.abs(min) * .1 || 1; min -= pad; max += pad; }
    const span = max - min;
    if (!Number.isFinite(span)) throw new TypeError('El rango excede la precisión numérica.');
    const raw = span / Math.max(1, count), power = 10 ** Math.floor(Math.log10(raw)), error = raw / power;
    const step = clean(power * (error >= 7.07 ? 10 : error >= 3.16 ? 5 : error >= 1.41 ? 2 : 1));
    const lo = clean(Math.floor(min / step + 1e-9) * step), hi = clean(Math.ceil(max / step - 1e-9) * step);
    const ticks = [];
    for (let i = 0, v = lo; v <= hi + step * 1e-6 && i < 200; v = clean(lo + ++i * step)) ticks.push(v);
    return {min: lo, max: hi, step, ticks};
  }
  // Ticks de calendario UTC alineados (día, semana, mes, trimestre, año) con su formato.
  const DAY = 86400000;
  const TIME_STEPS = [[1, 'd'], [2, 'd'], [7, 'd'], [14, 'd'], [1, 'm'], [2, 'm'], [3, 'm'], [6, 'm'], [12, 'm'], [24, 'm'], [60, 'm'], [120, 'm']];
  function timeTicks(min, max, count = 5) {
    if (!Number.isFinite(min) || !Number.isFinite(max) || max < min) throw new TypeError('Rango de fechas inválido.');
    const span = Math.max(DAY, max - min);
    const [n, kind] = TIME_STEPS.find(([n, k]) => span / ((k === 'd' ? DAY : 30.44 * DAY) * n) <= count) || TIME_STEPS.at(-1);
    const ticks = [];
    if (kind === 'd') {
      for (let t = Math.ceil(min / DAY) * DAY; t <= max && ticks.length < 100; t += n * DAY) ticks.push(t);
    } else {
      const d = new Date(min);
      let y = d.getUTCFullYear(), m = Math.ceil((d.getUTCMonth() + (d.getUTCDate() > 1 ? 1 : 0)) / n) * n;
      for (let t = Date.UTC(y, m, 1); t <= max && ticks.length < 100; m += n, t = Date.UTC(y, m, 1)) if (t >= min) ticks.push(t);
    }
    if (!ticks.length) ticks.push(min);
    return {ticks, spec: kind === 'd' ? 'shortdate' : n >= 12 ? 'year' : 'month'};
  }
  // Para dominios que deben contener el cero (barras, áreas, cascadas).
  const niceZero = (values, count) => nice(Math.min(0, ...values), Math.max(0, ...values), count);
  function linear([d0, d1], [r0, r1]) {
    if (![d0, d1, r0, r1].every(Number.isFinite) || d0 === d1) throw new TypeError('Dominio inválido.');
    const f = v => r0 + (v - d0) / (d1 - d0) * (r1 - r0);
    f.domain = [d0, d1]; f.range = [r0, r1];
    return f;
  }

  // ---------- Idioma y formato ----------
  const LOCALES = {es: 'es-CO', en: 'en-US', pt: 'pt-BR'};
  function lang(node) {
    const own = node?.closest?.('[data-locale]')?.getAttribute('data-locale');
    if (own) return own;
    const raw = node?.closest?.('[lang]')?.getAttribute('lang') || document.documentElement.lang || 'es';
    return LOCALES[raw.toLowerCase()] || raw;
  }
  const words = locale => /^en/i.test(locale)
    ? {missing: 'No data', all: 'All series', only: 'Only', hint: 'Click or press Enter on a series to show it alone; again to show all.', csv: 'Download CSV', svg: 'Download SVG', others: 'Others', total: 'Total', source: 'Source', unit: 'Unit'}
    : {missing: 'Sin dato', all: 'Todas las series', only: 'Solo', hint: 'Clic o Enter en una serie para verla sola; otra vez para ver todas.', csv: 'Descargar CSV', svg: 'Descargar SVG', others: 'Otros', total: 'Total', source: 'Fuente', unit: 'Unidad'};
  const cache = new Map();
  const nf = (locale, options) => {
    const key = locale + JSON.stringify(options);
    if (!cache.has(key)) cache.set(key, new Intl.NumberFormat(locale, options));
    return cache.get(key);
  };
  const df = (locale, options) => {
    const key = 'd' + locale + JSON.stringify(options);
    if (!cache.has(key)) cache.set(key, new Intl.DateTimeFormat(locale, {timeZone: 'UTC', ...options}));
    return cache.get(key);
  };
  const CURRENCIES = {cop: 'COP', usd: 'USD', eur: 'EUR', mxn: 'MXN', brl: 'BRL'};
  const DATES = {date: {dateStyle: 'medium'}, shortdate: {day: 'numeric', month: 'short'}, month: {month: 'short', year: 'numeric'}, year: {year: 'numeric'}};
  // Spec con nombres tipo Evidence: num1, num0k, pct1, pts1, cop0m, usd2, date, month, duration[_min|_h].
  function parse(spec = 'auto') {
    const m = /^(num|pct|pts|cop|usd|eur|mxn|brl)(\d)?(k|m|b|c)?$/.exec(spec);
    if (m) return {kind: m[1], digits: m[2] === undefined ? null : +m[2], compact: !!m[3]};
    if (DATES[spec] || spec === 'iso') return {kind: 'date', spec};
    const d = /^duration(?:_(s|min|h))?(?::(long|short|min))?$/.exec(spec);
    if (d) return {kind: 'duration', base: d[1] || 's', level: d[2] || 'long'};
    return {kind: 'auto'};
  }
  const DURATION_UNITS = [['day', 86400], ['hour', 3600], ['minute', 60], ['second', 1]];
  function duration(seconds, locale, level = 'long') {
    const sign = seconds < 0 ? '−' : '';
    let rest = Math.round(Math.abs(seconds));
    const parts = [];
    for (const [unit, size] of DURATION_UNITS) {
      const n = Math.floor(rest / size);
      if (n || (unit === 'second' && !parts.length)) { parts.push([unit, n]); rest -= n * size; }
      if (parts.length === (level === 'min' ? 1 : 3)) break;
    }
    // Sin segundos sueltos si ya hay unidades mayores: «3 d, 10 h, 36 min».
    const shown = parts.length > 1 ? parts.filter(([u]) => u !== 'second' || parts.length === 1) : parts;
    return sign + shown.map(([unit, n]) => nf(locale, {style: 'unit', unit, unitDisplay: level === 'long' ? 'long' : 'narrow'}).format(n)).join(level === 'long' ? ', ' : ' ');
  }
  function format(value, spec = 'auto', options = {}) {
    const locale = options.lang || lang(options.node);
    if (value === null || value === undefined || value === '') return words(locale).missing;
    if (typeof value !== 'number' || !Number.isFinite(value)) throw new TypeError('Valor no finito.');
    const p = typeof spec === 'object' ? spec : parse(spec);
    let text;
    if (p.kind === 'date') text = p.spec === 'iso' ? new Date(value).toISOString().slice(0, 10) : df(locale, DATES[p.spec]).format(value);
    else if (p.kind === 'duration') text = duration(value * (p.base === 'h' ? 3600 : p.base === 'min' ? 60 : 1), locale, p.level);
    else if (p.kind === 'pct') text = nf(locale, {style: 'percent', maximumFractionDigits: p.digits ?? 1}).format(value);
    else if (p.kind === 'pts') text = nf(locale, {style: 'percent', maximumFractionDigits: p.digits ?? 1}).format(value / 100);
    else if (CURRENCIES[p.kind]) text = nf(locale, {style: 'currency', currency: CURRENCIES[p.kind], currencyDisplay: 'narrowSymbol', ...(p.compact ? {notation: 'compact', maximumFractionDigits: p.digits ?? 1} : {maximumFractionDigits: p.digits ?? 0, minimumFractionDigits: p.digits ?? 0})}).format(value);
    else if (p.kind === 'num') text = nf(locale, p.compact ? {notation: 'compact', maximumFractionDigits: p.digits ?? 1} : {maximumFractionDigits: p.digits ?? 0, minimumFractionDigits: p.digits ?? 0}).format(value);
    else {
      const a = Math.abs(value);
      text = nf(locale, a !== 0 && a < 1e-4 ? {notation: 'scientific', maximumSignificantDigits: 4} : {maximumSignificantDigits: Math.max(6, Math.ceil(Math.log10(a + 1)))}).format(value);
    }
    return options.unit && p.kind !== 'duration' && !CURRENCIES[p.kind] && p.kind !== 'pct' && p.kind !== 'pts' && p.kind !== 'date' ? text + ' ' + options.unit : text;
  }
  // Rótulos de ticks: los decimales salen del paso; se usa notación compacta para magnitudes grandes
  // y se añaden cifras hasta que todos los rótulos sean distintos.
  function tickFormat(ticks, spec = 'auto', options = {}) {
    const locale = options.lang || lang(options.node), p = typeof spec === 'object' ? spec : parse(spec);
    if (p.kind === 'date' || p.kind === 'duration') return v => format(v, p, {lang: locale});
    const step = ticks.length > 1 ? Math.abs(ticks[1] - ticks[0]) : 1;
    const scale = p.kind === 'pct' ? 100 : 1;
    const decimals = Math.max(0, Math.min(10, -Math.floor(Math.log10(step * scale) + 1e-9)));
    const big = Math.max(...ticks.map(Math.abs)) >= 1e5;
    const base = CURRENCIES[p.kind] ? {style: 'currency', currency: CURRENCIES[p.kind], currencyDisplay: 'narrowSymbol'} : p.kind === 'pct' ? {style: 'percent'} : {};
    for (let extra = 0; extra < 4; extra++) {
      const opts = big || p.compact ? {...base, notation: 'compact', maximumFractionDigits: extra} : {...base, maximumFractionDigits: decimals + extra, minimumFractionDigits: decimals};
      const f = nf(locale, opts), labels = ticks.map(v => f.format(v));
      if (new Set(labels).size === labels.length || extra === 3) return v => f.format(v);
    }
  }
  // Especificación de formato de una celda, columna o figura.
  function specOf(...nodes) {
    for (const n of nodes) { const s = n?.getAttribute?.('data-formato'); if (s) return s; }
    return 'auto';
  }
  function unitOf(...nodes) {
    for (const n of nodes) { const s = n?.getAttribute?.('data-unidad'); if (s) return s; }
    return '';
  }

  // ---------- Paleta, trazos, formas y patrones ----------
  const color = i => 'var(--grafica-' + ((i % 8) + 1) + ')';
  const DASHES = ['', '7 4', '2 4', '10 3 2 3', '12 4', '4 2 1 2', '1 3', '8 2 2 2 2 2'];
  const dash = i => DASHES[i % 8];
  function shape(i, x, y, r = 4) {
    const s = r * .9, t = r * 1.15;
    switch (i % 8) {
      case 0: return `M${x - r} ${y}a${r} ${r} 0 1 0 ${2 * r} 0a${r} ${r} 0 1 0 ${-2 * r} 0Z`;
      case 1: return `M${x - s} ${y - s}h${2 * s}v${2 * s}h${-2 * s}Z`;
      case 2: return `M${x} ${y - t}L${x + t} ${y + t * .8}H${x - t}Z`;
      case 3: return `M${x} ${y - t}L${x + t} ${y}L${x} ${y + t}L${x - t} ${y}Z`;
      case 4: return `M${x} ${y + t}L${x + t} ${y - t * .8}H${x - t}Z`;
      case 5: return `M${x - t} ${y - r / 3}h${t * 2}v${r * 2 / 3}h${-t * 2}ZM${x - r / 3} ${y - t}h${r * 2 / 3}v${t * 2}h${-r * 2 / 3}Z`;
      case 6: return `M${x - t} ${y - t / 2}h${2 * t}v${t}h${-2 * t}Z`;
      default: return `M${x - s} ${y - t}h${2 * s}L${x - s} ${y + t}h${2 * s}Z`;
    }
  }
  const TEXTURES = ['', 'M-1 1l2-2M0 6l6-6M5 7l2-2', 'M3 3m-1 0a1 1 0 1 0 2 0a1 1 0 1 0-2 0', 'M0 3h6', 'M3 0v6', 'M0 0l6 6M6 0l-6 6', 'M-1 5l2 2M0 0l6 6M5-1l2 2', 'M0 1.5h6M1.5 0v6'];
  function svgNode(tag, attrs = {}, text) {
    const n = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) if (v !== undefined && v !== null) n.setAttribute(k, String(v));
    if (text !== undefined) n.textContent = text;
    return n;
  }
  // Patrones por instancia: el id incluye un serial para no colisionar entre figuras.
  function patterns(svg, enabled = true) {
    const id = uid('mgp'), defs = svgNode('defs');
    for (let i = 0; i < 8; i++) {
      const p = svgNode('pattern', {id: id + '-' + i, patternUnits: 'userSpaceOnUse', width: 6, height: 6});
      p.append(svgNode('rect', {width: 6, height: 6, style: 'fill:' + color(i)}));
      if (TEXTURES[i]) p.append(svgNode('path', {d: TEXTURES[i], class: 'mg-textura', style: 'stroke:var(--grafica-papel);fill:' + (i === 2 ? 'var(--grafica-papel)' : 'none')}));
      defs.append(p);
    }
    svg.prepend(defs);
    return i => enabled ? 'url(#' + id + '-' + (i % 8) + ')' : color(i);
  }
  const patternsEnabled = node => node?.closest?.('[data-patrones]')?.getAttribute('data-patrones') !== 'no';

  // ---------- Texto ----------
  let ctx;
  const widths = new Map();
  function textWidth(text, font = '12px monospace') {
    const key = font + '\u0000' + text;
    if (widths.has(key)) return widths.get(key);
    ctx ??= (() => { try { return document.createElement('canvas').getContext('2d'); } catch { return null; } })();
    let w;
    if (ctx) { ctx.font = font; w = ctx.measureText(text).width; }
    else w = text.length * (parseFloat(font.match(/([\d.]+)px/)?.[1]) || 12) * .62;
    if (widths.size > 4000) widths.clear();
    widths.set(key, w);
    return w;
  }
  function fontOf(svg, cls) {
    const probe = svgNode('text', {class: cls || '', x: -9999, y: -9999}, 'x');
    svg.append(probe);
    const s = getComputedStyle(probe);
    const font = `${s.fontStyle || 'normal'} ${s.fontWeight || 400} ${s.fontSize || '12px'} ${s.fontFamily || 'monospace'}`;
    probe.remove();
    return font;
  }
  // Devuelve el texto completo si cabe, una abreviatura con «…» o '' si no cabe nada legible.
  function fit(text, max, font, min = 3) {
    if (textWidth(text, font) <= max) return text;
    let lo = 0, hi = text.length;
    while (lo < hi) { const mid = (lo + hi + 1) >> 1; if (textWidth(text.slice(0, mid).trimEnd() + '…', font) <= max) lo = mid; else hi = mid - 1; }
    return lo >= min ? text.slice(0, lo).trimEnd() + '…' : '';
  }
  // Partir por palabras al ancho disponible, sin cortar palabras salvo que una sola no quepa.
  function wrap(text, max, font, maxLines = 3) {
    const lines = [];
    let line = '';
    for (const word of String(text).split(/\s+/).filter(Boolean)) {
      const next = line ? line + ' ' + word : word;
      if (textWidth(next, font) <= max || !line) line = next;
      else { lines.push(line); line = word; }
    }
    if (line) lines.push(line);
    if (lines.length > maxLines) { const kept = lines.slice(0, maxLines); kept[maxLines - 1] = fit(lines.slice(maxLines - 1).join(' '), max, font, 1); return kept; }
    return lines.map(l => textWidth(l, font) > max ? fit(l, max, font, 1) : l);
  }

  // ---------- Ancho real y redibujo ----------
  function contentWidth(el) {
    const s = getComputedStyle(el);
    const inset = ['paddingLeft', 'paddingRight', 'borderLeftWidth', 'borderRightWidth'].reduce((a, k) => a + (parseFloat(s[k]) || 0), 0);
    return Math.max(0, Math.floor(el.getBoundingClientRect().width - inset));
  }
  // Redibuja solo cuando cambia el ancho entero o la tipografía; ancho 0 (página oculta) no dibuja.
  function responsive(el, render, options = {}) {
    let key = '', raf = 0, dead = false, recent = [];
    const fontKey = () => { const s = getComputedStyle(el); return s.fontFamily + s.fontSize; };
    const run = () => {
      raf = 0;
      if (dead) return;
      const width = (options.measure || contentWidth)(el);
      if (width <= 0) return;
      const next = width + '|' + fontKey();
      if (next === key) return;
      // Freno ante oscilaciones (p. ej. una barra de desplazamiento que aparece y desaparece).
      const now = performance.now();
      recent = recent.filter(t => now - t < 1000);
      if (recent.length >= 6) { setTimeout(() => { recent = []; schedule(); }, 250); return; }
      recent.push(now);
      key = next;
      render(width);
    };
    const schedule = () => { if (!raf && !dead) raf = requestAnimationFrame(run); };
    const ro = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(schedule) : null;
    ro?.observe(el);
    const abort = new AbortController();
    document.addEventListener('nota:tema', schedule, {signal: abort.signal});
    document.addEventListener('nota:pagina', schedule, {signal: abort.signal});
    el.closest('details')?.addEventListener('toggle', schedule, {signal: abort.signal});
    document.fonts?.ready?.then(() => { if (!dead) { key = ''; schedule(); } });
    run();
    return {
      refresh() { key = ''; run(); },
      disconnect() { dead = true; ro?.disconnect(); abort.abort(); if (raf) cancelAnimationFrame(raf); }
    };
  }

  // ---------- Tip ----------
  let tipNode = null, tipOwner = null, tipTarget = null;
  function tipElement() {
    if (tipNode?.isConnected) return tipNode;
    tipNode = document.createElement('div');
    tipNode.className = 'mg-tip';
    tipNode.id = uid('mg-tip');
    tipNode.setAttribute('role', 'tooltip');
    tipNode.hidden = true;
    document.body.append(tipNode);
    return tipNode;
  }
  function place(node, anchor) {
    const tip = node.getBoundingClientRect(), gap = 10, pad = 8, vw = innerWidth, vh = innerHeight;
    let x = anchor.x + gap, y = anchor.bottom + gap;
    if (x + tip.width > vw - pad) x = anchor.right - tip.width - gap;
    if (anchor.point) x = anchor.x + gap + tip.width > vw - pad ? anchor.x - gap - tip.width : anchor.x + gap;
    if (y + tip.height > vh - pad) y = anchor.top - gap - tip.height;
    node.style.left = Math.round(Math.max(pad, Math.min(vw - tip.width - pad, x))) + 'px';
    node.style.top = Math.round(Math.max(pad, Math.min(vh - tip.height - pad, y))) + 'px';
  }
  function showTip(owner, target, content, point) {
    const node = tipElement();
    if (tipTarget && tipTarget !== target) tipTarget.removeAttribute('aria-describedby');
    tipOwner = owner; tipTarget = target;
    const parts = (Array.isArray(content) ? content : [content]).filter(Boolean);
    node.replaceChildren(...parts.map((line, i) => {
      const e = document.createElement(i ? 'span' : 'strong');
      e.textContent = line;
      return e;
    }));
    node.hidden = false;
    target.setAttribute('aria-describedby', node.id);
    const r = target.getBoundingClientRect();
    place(node, point ? {x: point.x, y: point.y, right: point.x, top: point.y, bottom: point.y, point: true} : {x: r.left, right: r.right, top: r.top, bottom: r.bottom});
  }
  function hideTip(owner) {
    if (!tipNode || (owner && owner !== tipOwner)) return;
    tipNode.hidden = true;
    tipTarget?.removeAttribute('aria-describedby');
    tipOwner = tipTarget = null;
  }

  // ---------- Marcas navegables ----------
  // items: elementos SVG en orden de lectura. describe(i) → [título, ...líneas].
  function marks(host, svg, {items, describe, onSelect, status, label, columns = 0}) {
    const owner = {}, abort = new AbortController(), signal = abort.signal;
    let current = 0, pinned = null, hideTimer = 0;
    const list = [...items];
    list.forEach((el, i) => {
      el.dataset.mgI = i;
      el.setAttribute('tabindex', i === 0 ? '0' : '-1');
      el.setAttribute('role', 'img');
      el.setAttribute('aria-label', describe(i).join('. '));
      el.classList.add('mg-marca');
    });
    svg.setAttribute('role', 'group');
    if (label) svg.setAttribute('aria-label', label + '. ' + list.length + ' marcas: flechas para recorrer, Enter para fijar, Escape para cerrar.');
    const index = el => { const m = el?.closest?.('[data-mg-i]'); return m && svg.contains(m) ? +m.dataset.mgI : -1; };
    const focus = i => {
      if (!list.length) return;
      current = (i + list.length) % list.length;
      list.forEach((el, k) => el.setAttribute('tabindex', k === current ? '0' : '-1'));
      list[current].focus({preventScroll: false});
    };
    const select = i => {
      pinned = i;
      list.forEach((el, k) => el.classList.toggle('mg-elegida', k === i));
      if (status) status.textContent = i === null ? '' : describe(i).join('. ');
      onSelect?.(i);
    };
    const show = (i, point) => { clearTimeout(hideTimer); showTip(owner, list[i], describe(i), point); };
    const later = () => { clearTimeout(hideTimer); hideTimer = setTimeout(() => { if (pinned === null) hideTip(owner); }, 160); };
    svg.addEventListener('keydown', e => {
      const i = index(e.target);
      if (i < 0) return;
      const keys = columns ? {ArrowRight: 1, ArrowLeft: -1, ArrowDown: columns, ArrowUp: -columns} : {ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1};
      if (keys[e.key]) { e.preventDefault(); const next = i + keys[e.key]; focus(columns && (next < 0 || next >= list.length) ? i : next); }
      else if (e.key === 'Home') { e.preventDefault(); focus(0); }
      else if (e.key === 'End') { e.preventDefault(); focus(list.length - 1); }
      else if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); select(pinned === i ? null : i); show(i); }
      else if (e.key === 'Escape') { select(null); hideTip(owner); }
    }, {signal});
    svg.addEventListener('focusin', e => { const i = index(e.target); if (i >= 0) { current = i; show(i); } }, {signal});
    svg.addEventListener('focusout', () => { if (pinned === null) later(); }, {signal});
    svg.addEventListener('pointermove', e => {
      if (e.pointerType === 'touch') return;
      const i = index(e.target);
      if (i >= 0) show(i, {x: e.clientX, y: e.clientY});
      else if (pinned === null) later();
    }, {signal});
    svg.addEventListener('pointerleave', () => { if (pinned === null) later(); }, {signal});
    svg.addEventListener('click', e => {
      const i = index(e.target);
      if (i < 0) return;
      current = i;
      list.forEach((el, k) => el.setAttribute('tabindex', k === i ? '0' : '-1'));
      select(pinned === i && e.pointerType !== 'touch' ? null : i);
      show(i, e.pointerType === 'mouse' ? {x: e.clientX, y: e.clientY} : null);
    }, {signal});
    document.addEventListener('pointerdown', e => {
      if (!svg.contains(e.target) && !tipNode?.contains(e.target) && tipOwner === owner) { select(null); hideTip(owner); }
    }, {signal});
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && tipOwner === owner) { select(null); hideTip(owner); } }, {signal});
    document.addEventListener('scroll', e => {
      if (tipOwner !== owner || tipNode?.contains(e.target)) return;
      const i = index(document.activeElement);
      if (i >= 0) show(i); else hideTip(owner);
    }, {signal, capture: true, passive: true});
    document.addEventListener('nota:pagina', () => { select(null); hideTip(owner); }, {signal});
    addEventListener('resize', () => hideTip(owner), {signal});
    return {
      select(i) { select(i); if (i !== null) show(i); },
      get selected() { return pinned; },
      destroy() { clearTimeout(hideTimer); abort.abort(); hideTip(owner); }
    };
  }

  // ---------- Leyenda que resalta y aísla ----------
  // series: [{name, index}]; targets(i) → elementos de esa serie dentro del SVG.
  function legend(names, {targets, onChange, locale, shapes}) {
    const w = words(locale), list = document.createElement('ul'), live = document.createElement('p');
    list.className = 'mg-leyenda';
    live.className = 'mg-oculto';
    live.setAttribute('role', 'status');
    let isolated = null;
    const paint = highlight => names.forEach((_, i) => targets(i).forEach(el => {
      el.classList.toggle('mg-atenuada', (isolated !== null && i !== isolated) || (highlight !== null && highlight !== undefined && i !== highlight && isolated === null));
    }));
    const buttons = names.map((name, i) => {
      const li = document.createElement('li'), b = document.createElement('button'), swatch = document.createElement('span');
      b.type = 'button';
      b.setAttribute('aria-pressed', 'false');
      b.title = w.only + ': ' + name;
      swatch.className = 'mg-muestra serie-' + (i % 8);
      swatch.setAttribute('aria-hidden', 'true');
      if (shapes) {
        const icon = svgNode('svg', {width: 14, height: 14, class: 'mg-muestra-forma serie-' + (i % 8), 'aria-hidden': 'true'});
        icon.append(svgNode('path', {d: shape(i, 7, 7, 5), class: i ? 'grafica-barra' : 'grafica-punto mg-forma', style: i ? 'fill:var(--serie)' : ''}));
        b.append(icon, document.createTextNode(name));
      } else b.append(swatch, document.createTextNode(name));
      b.addEventListener('click', () => {
        isolated = isolated === i ? null : i;
        buttons.forEach((x, k) => x.setAttribute('aria-pressed', String(k === isolated)));
        paint(null);
        live.textContent = isolated === null ? w.all : w.only + ': ' + name;
        onChange?.(isolated);
      });
      for (const [type, value] of [['pointerenter', i], ['focus', i], ['pointerleave', null], ['blur', null]]) b.addEventListener(type, () => paint(value));
      li.append(b);
      list.append(li);
      return b;
    });
    const box = document.createElement('div');
    box.className = 'mg-leyenda-caja';
    const hint = document.createElement('p');
    hint.className = 'mg-leyenda-ayuda';
    hint.id = uid('mg-ayuda');
    hint.textContent = w.hint;
    list.setAttribute('aria-describedby', hint.id);
    box.append(list, hint, live);
    return {element: box, get isolated() { return isolated; }, repaint: () => paint(null)};
  }

  // ---------- Exportación ----------
  // Texto que empieza como fórmula (=, +, -, @, tab, CR) se neutraliza con «'»; los números fuente quedan intactos.
  const neutral = v => /^[=+\-@\t\r]/.test(v) && !(v.trim() !== '' && Number.isFinite(Number(v))) ? "'" + v : v;
  const csvCell = raw => { const v = neutral(raw); return /[",\n\r;]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
  function tableCsv(table) {
    const rows = [];
    for (const row of table.querySelectorAll(':scope > thead > tr, :scope > tbody > tr, :scope > tfoot > tr')) {
      rows.push([...row.cells].map(c => {
        if (c.hasAttribute('data-valor')) return c.getAttribute('data-valor').trim();
        const time = c.querySelector('time[datetime]');
        return (time ? time.getAttribute('datetime') : c.textContent).trim().replace(/\s+/g, ' ');
      }).map(csvCell).join(','));
    }
    return rows.join('\r\n') + '\r\n';
  }
  const STYLE_KEYS = ['fill', 'fill-opacity', 'stroke', 'stroke-width', 'stroke-dasharray', 'stroke-opacity', 'opacity', 'font-family', 'font-size', 'font-weight', 'text-anchor', 'dominant-baseline', 'paint-order', 'stroke-linecap', 'stroke-linejoin'];
  // Copia autónoma: estilos computados en línea (sin var() ni currentColor), sin clases ni foco.
  function inlineCopy(svg) {
    const copy = svg.cloneNode(true), originals = [svg, ...svg.querySelectorAll('*')], copies = [copy, ...copy.querySelectorAll('*')];
    originals.forEach((el, i) => {
      const s = getComputedStyle(el), target = copies[i];
      for (const name of ['class', 'tabindex', 'aria-describedby', 'role', 'data-mg-i']) target.removeAttribute(name);
      for (const attr of [...target.attributes]) if (/var\(|currentcolor/i.test(attr.value) && attr.name !== 'style') target.removeAttribute(attr.name);
      target.setAttribute('style', STYLE_KEYS.map(k => s.getPropertyValue(k) ? k + ':' + s.getPropertyValue(k) : '').filter(Boolean).join(';'));
    });
    const box = svg.getBoundingClientRect();
    copy.setAttribute('width', Math.round(box.width) || +svg.getAttribute('width') || 800);
    copy.setAttribute('height', Math.round(box.height) || +svg.getAttribute('height') || 400);
    return copy;
  }
  function standaloneSvg(input, {title, source, unit}) {
    const list = Array.isArray(input) ? input : [input], svg = list[0];
    let copy;
    if (list.length === 1) copy = inlineCopy(svg);
    else {
      // Varios paneles (múltiplos): uno debajo de otro dentro de un solo SVG.
      const parts = list.map(inlineCopy), width = Math.max(...parts.map(p => +p.getAttribute('width')));
      let y = 0;
      copy = svgNode('svg', {width, viewBox: '0 0 ' + width + ' 1'});
      parts.forEach(p => { p.setAttribute('y', y); y += +p.getAttribute('height') + 16; copy.append(p); });
      copy.setAttribute('height', y); copy.setAttribute('viewBox', `0 0 ${width} ${y}`);
    }
    copy.setAttribute('xmlns', NS);
    copy.querySelectorAll(':scope > title, :scope > desc').forEach(n => n.remove());
    const bg = svgNode('rect', {width: '100%', height: '100%', style: 'fill:' + getComputedStyle(svg.closest('figure,section,div') || svg).getPropertyValue('--grafica-papel')});
    const defs = copy.querySelector(':scope > defs');
    if (defs) defs.after(bg); else copy.prepend(bg);
    copy.prepend(svgNode('title', {}, title), svgNode('desc', {}, [unit && 'Unidad: ' + unit, source && 'Fuente: ' + source].filter(Boolean).join('. ')));
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + new XMLSerializer().serializeToString(copy);
  }
  function download(name, type, text) {
    const url = URL.createObjectURL(new Blob([text], {type}));
    const a = document.createElement('a');
    a.href = url; a.download = name; a.hidden = true;
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  const slug = s => (s || 'grafica').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 60) || 'grafica';
  // getSvg se llama al exportar: siempre la versión vigente tras un redibujo.
  function exporter(figure, {table, getSvg, title}) {
    const w = words(lang(figure)), box = document.createElement('div');
    box.className = 'mg-exportar';
    const source = figure.querySelector('[data-fuente],.fuente,figcaption')?.textContent.trim().replace(/\s+/g, ' ') || figure.getAttribute('data-fuente') || '';
    const unit = figure.getAttribute('data-unidad') || '';
    const make = (text, fn) => { const b = document.createElement('button'); b.type = 'button'; b.textContent = text; b.addEventListener('click', fn); box.append(b); return b; };
    if (table) make(w.csv, () => download(slug(title) + '.csv', 'text/csv;charset=utf-8', '﻿' + tableCsv(table)));
    make(w.svg, () => { const svg = getSvg(); if (svg && (!Array.isArray(svg) || svg.length)) download(slug(title) + '.svg', 'image/svg+xml', standaloneSvg(svg, {title, source, unit})); });
    return box;
  }

  // ---------- Treemap squarified (Bruls, Huizing y van Wijk) ----------
  function worst(row, side) {
    const sum = row.reduce((a, r) => a + r.area, 0), max = Math.max(...row.map(r => r.area)), min = Math.min(...row.map(r => r.area));
    return Math.max(side * side * max / (sum * sum), sum * sum / (side * side * min));
  }
  function squarify(items, {x = 0, y = 0, w, h}) {
    const total = items.reduce((a, r) => a + r.value, 0);
    if (!(total > 0) || !(w > 0) || !(h > 0)) return [];
    const queue = items.filter(r => r.value > 0).sort((a, b) => b.value - a.value).map(r => ({...r, area: r.value / total * w * h}));
    const out = [];
    let rect = {x, y, w, h};
    while (queue.length) {
      const side = Math.min(rect.w, rect.h), row = [queue.shift()];
      while (queue.length && worst([...row, queue[0]], side) <= worst(row, side)) row.push(queue.shift());
      const sum = row.reduce((a, r) => a + r.area, 0);
      if (rect.w >= rect.h) {
        const cw = sum / rect.h; let cy = rect.y;
        row.forEach((r, k) => { const ch = k === row.length - 1 ? rect.y + rect.h - cy : r.area / cw; out.push({...r, x: rect.x, y: cy, w: cw, h: ch}); cy += ch; });
        rect = {x: rect.x + cw, y: rect.y, w: Math.max(0, rect.w - cw), h: rect.h};
      } else {
        const ch = sum / rect.w; let cx = rect.x;
        row.forEach((r, k) => { const cw = k === row.length - 1 ? rect.x + rect.w - cx : r.area / ch; out.push({...r, x: cx, y: rect.y, w: cw, h: ch}); cx += cw; });
        rect = {x: rect.x, y: rect.y + ch, w: rect.w, h: Math.max(0, rect.h - ch)};
      }
    }
    return out.map(({area, ...r}) => r);
  }

  // ---------- Ejes ----------
  // Dibuja rejilla y rótulos de un eje numérico. orient: 'left' | 'bottom'.
  function axis(svg, {orient, scale, ticks, format, from, to, at, className = '', font}) {
    const g = svgNode('g', {class: 'mg-eje ' + className, 'aria-hidden': 'true'});
    ticks.forEach(v => {
      const p = scale(v);
      if (orient === 'left') {
        g.append(svgNode('line', {x1: from, x2: to, y1: p, y2: p, class: v === 0 ? 'grafica-eje' : 'grafica-rejilla', 'data-tick-y': v}));
        g.append(svgNode('text', {x: at, y: p, 'text-anchor': 'end', 'dominant-baseline': 'middle'}, format(v)));
      } else {
        g.append(svgNode('line', {x1: p, x2: p, y1: from, y2: to, class: v === 0 ? 'grafica-eje' : 'grafica-rejilla', 'data-tick-x': v}));
        g.append(edgeText(svg, p, at, format(v), {}, font));
      }
    });
    svg.append(g);
    return g;
  }
  // Texto centrado que no se sale del SVG: en los bordes se ancla al inicio o al final.
  function edgeText(svg, x, y, text, attrs = {}, font) {
    const width = +svg.getAttribute('width') || Infinity, w = textWidth(text, font || '12px monospace');
    const anchor = x - w / 2 < 0 ? 'start' : x + w / 2 > width ? 'end' : 'middle';
    return svgNode('text', {x: anchor === 'start' ? Math.max(0, x - 4) : anchor === 'end' ? Math.min(width, x + 4) : x, y, 'text-anchor': anchor, ...attrs}, text);
  }
  // Rótulos de ticks horizontales que no se pisan: reduce la lista hasta que haya hueco.
  // Usa la misma regla de anclaje que edgeText para medir cada rótulo donde de verdad se dibuja.
  function spacedTicks(ticks, scale, format, font, gap = 12, width = Infinity) {
    const box = v => {
      const x = scale(v), w = textWidth(format(v), font);
      const left = x - w / 2 < 0 ? Math.max(0, x - 4) : x + w / 2 > width ? Math.min(width, x + 4) - w : x - w / 2;
      return [left, left + w];
    };
    for (let step = 1; step < ticks.length; step++) {
      const kept = ticks.filter((_, i) => i % step === 0), boxes = kept.map(box);
      if (boxes.every((b, i) => !i || b[0] - boxes[i - 1][1] >= gap)) return kept;
    }
    return ticks.slice(0, 1);
  }

  window.MargenGraficas = {
    version: '1', NS, uid, nice, niceZero, linear, timeTicks, lang, words, parse, format, tickFormat, duration, specOf, unitOf,
    color, dash, shape, patterns, patternsEnabled, svg: svgNode, textWidth, fontOf, fit, wrap,
    contentWidth, responsive, marks, edgeText, showTip, hideTip, legend, tableCsv, standaloneSvg, exporter, squarify, axis, spacedTicks
  };
})();
