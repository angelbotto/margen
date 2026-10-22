/* Margen · analítica local. La tabla es la única fuente de cifras. Requiere chart-core.js.
   Sin red ni animación automática; SVG al ancho real, marcas navegables y selector equivalente. */
(() => {
  'use strict';
  const G = window.MargenGraficas, instances = new WeakMap(), DAY = 86400000;
  const el = (tag, text) => { const e = document.createElement(tag); if (text !== undefined) e.textContent = text; return e; };
  const date = s => { if (!/^\d{4}-\d{2}-\d{2}$/.test(s)) throw Error('Fecha ISO requerida.'); const n = Date.parse(s + 'T00:00:00Z'); if (!Number.isFinite(n) || new Date(n).toISOString().slice(0, 10) !== s) throw Error('Fecha inválida.'); return n; };
  const iso = n => new Date(n).toISOString().slice(0, 10);
  const positive = values => { if (values.some(v => v < 0)) throw Error('No se admiten cantidades negativas.'); };
  function read(e) {
    const type = e.dataset.analitica, counts = {calendario: 2, torta: 2, areas: 4, caja: 6, velas: 5, rutas: 6, burbujas: 4};
    const table = e.querySelector('table'), headCells = [...(table?.tHead?.rows[0]?.cells || [])], heads = headCells.map(c => c.textContent.trim());
    if (!counts[type] || heads.length !== counts[type] || !table.tBodies[0]) throw Error('Tipo o cabecera incorrectos.');
    const rows = [...table.tBodies[0].rows].map(r => {
      if (r.cells.length !== heads.length) throw Error('Fila incompleta.');
      const label = r.cells[0].textContent.trim(), values = [...r.cells].slice(1).map(c => {
        const raw = c.getAttribute('data-valor'), v = Number(raw); if (raw === null || !raw.trim() || !Number.isFinite(v) || Math.abs(v) > 1e12) throw Error('Valor inválido o fuera de precisión.'); return v;
      }); return {label, values};
    });
    if (!rows.length || rows.length > (type === 'calendario' ? 366 : type === 'areas' || type === 'velas' ? 60 : 24)) throw Error('Cantidad de registros fuera de límite.');
    if (new Set(rows.map(r => r.label)).size !== rows.length) throw Error('Etiquetas duplicadas.');
    if (['calendario', 'areas', 'velas'].includes(type)) { rows.forEach(r => r.time = date(r.label)); rows.sort((a, b) => a.time - b.time); }
    if (['calendario', 'torta', 'areas'].includes(type)) positive(rows.flatMap(r => r.values));
    if (type === 'torta' && (rows.length > 8 || rows.reduce((s, r) => s + r.values[0], 0) <= 0)) throw Error('Torta: 1–8 categorías y total positivo.');
    if (type === 'calendario' && ((rows.at(-1).time - rows[0].time) / DAY > 365 || rows.some(r => !Number.isInteger(r.values[0])))) throw Error('Calendario: conteos enteros y hasta 366 días.');
    if (type === 'areas' && rows.length < 2) throw Error('Áreas requieren al menos dos fechas.');
    if (type === 'caja' && rows.some(r => r.values.some((v, i, a) => i && v < a[i - 1]))) throw Error('Orden esperado: mínimo ≤ Q1 ≤ mediana ≤ Q3 ≤ máximo.');
    if (type === 'velas' && rows.some(r => { const [o, h, l, c] = r.values; return l > Math.min(o, c) || h < Math.max(o, c) || l > h; })) throw Error('OHLC: mínimo ≤ apertura/cierre ≤ máximo.');
    if (['rutas', 'burbujas'].includes(type)) {
      if (!window.NotaGeografia) throw Error('Incluye packages/core/components/geography.js.');
      rows.forEach(r => { const v = r.values; NotaGeografia.check(v[0], v[1]); if (type === 'rutas') NotaGeografia.check(v[2], v[3]); positive([v.at(-1)]); });
    }
    return {type, table, heads, rows, title: table.caption?.textContent.trim() || 'Gráfica', unit: e.dataset.unidad || heads.at(-1), spec: G.specOf(headCells.at(-1), e)};
  }
  class Chart {
    constructor(element) {
      if (!G) throw Error('Incluye packages/core/components/chart-core.js antes de analytics.js.');
      this.model = read(element); this.element = element; this.abort = new AbortController(); this.parts = []; this.donut = true; this.selected = null;
      this.lang = G.lang(element); this.words = G.words(this.lang);
      this.heading = el('h3', this.model.title); this.heading.className = 'grafica-titulo';
      this.stage = el('div'); this.stage.className = 'grafica-caja analitica-caja';
      this.controls = el('div'); this.controls.className = 'analitica-controles';
      this.status = el('p', 'Elige un registro para consultar sus valores.'); this.status.className = 'analitica-estado'; this.status.setAttribute('role', 'status');
      const label = el('label', 'Consultar registro '); this.select = el('select'); this.select.setAttribute('aria-label', 'Registro de ' + this.model.title); this.select.append(new Option('Todos los registros', ''));
      this.model.rows.forEach((r, i) => this.select.append(new Option(r.label, String(i)))); label.append(this.select); this.controls.append(label);
      this.select.addEventListener('change', () => this.choose(this.select.value === '' ? null : Number(this.select.value), true), {signal: this.abort.signal});
      if (this.model.type === 'torta') {
        this.toggle = el('button', 'Ver como torta'); this.toggle.type = 'button'; this.toggle.setAttribute('aria-pressed', 'false');
        this.toggle.addEventListener('click', () => { this.donut = !this.donut; this.toggle.textContent = this.donut ? 'Ver como torta' : 'Ver como donut'; this.toggle.setAttribute('aria-pressed', String(!this.donut)); this.watch.refresh(); }, {signal: this.abort.signal}); this.controls.append(this.toggle);
      }
      this.legend = el('ul'); this.legend.className = 'analitica-leyenda';
      this.note = el('p'); this.note.className = 'mg-desplazar-nota'; this.note.hidden = true;
      this.parts = [this.heading, this.controls, this.stage, this.note, this.legend, this.status, G.exporter(element, {table: this.model.table, title: this.model.title, getSvg: () => this.chart})];
      const before = element.firstChild; this.parts.forEach(p => element.insertBefore(p, before)); element.classList.add('nota-analitica');
      try { this.watch = G.responsive(this.stage, w => this.draw(w)); } catch (error) { this.parts.forEach(p => p.remove()); element.classList.remove('nota-analitica'); this.abort.abort(); throw error; }
      instances.set(element, this);
    }
    add(tag, attrs, text) { const n = G.svg(tag, attrs, text); this.chart.append(n); return n; }
    text(x, y, text, anchor = 'start', cls) { return this.add('text', {x, y, 'text-anchor': anchor, class: cls}, text); }
    line(x1, y1, x2, y2, cls = 'grafica-rejilla') { return this.add('line', {x1, y1, x2, y2, class: cls}); }
    color(i) { return G.color(i); }
    f(v) { return G.format(v, this.model.spec, {lang: this.lang}); }
    fu(v) { return G.format(v, this.model.spec, {lang: this.lang, unit: this.model.unit}); }
    mark(n, i) { n.dataset.registro = i; this.items.push(n); return n; }
    describe(i) { const r = this.model.rows[i]; return [r.label, ...r.values.map((v, k) => this.model.heads[k + 1] + ': ' + this.f(v))]; }
    choose(i, fromSelect) {
      this.selected = i; this.select.value = i === null ? '' : String(i);
      this.status.textContent = i === null ? 'Todos los registros.' : this.describe(i).join(' · ');
      this.chart?.querySelectorAll('[data-registro]').forEach(n => n.classList.toggle('analitica-atenuada', i !== null && Number(n.dataset.registro) !== i));
      if (fromSelect && i !== null) { const k = this.items.findIndex(n => +n.dataset.registro === i); if (k >= 0) this.marks?.select(k); }
    }
    swatch(text, i, fill) {
      const li = el('li'), s = G.svg('svg', {width: 14, height: 14, class: 'analitica-muestra', 'aria-hidden': 'true'});
      s.append(G.svg('rect', {width: 14, height: 14, style: 'fill:' + (fill ?? this.fill(i))}));
      li.append(s, document.createTextNode(text)); this.legend.append(li);
    }
    // Eje Y numérico; devuelve escala y márgenes. Título de unidad arriba a la izquierda.
    yAxis(lo, hi, height, zero) {
      const n = zero ? G.niceZero([lo, hi], Math.max(3, Math.floor((height - 90) / 44))) : G.nice(lo - (hi - lo) * .05, hi + (hi - lo) * .05, Math.max(3, Math.floor((height - 90) / 44)));
      const fmt = G.tickFormat(n.ticks, this.model.spec, {lang: this.lang});
      const left = Math.ceil(Math.max(...n.ticks.map(v => G.textWidth(fmt(v), this.font)))) + 10, top = 30, bottom = height - 40;
      const y = G.linear([n.min, n.max], [bottom, top]);
      G.axis(this.chart, {orient: 'left', scale: y, ticks: n.ticks, format: fmt, from: left, to: this.width - 8, at: left - 6});
      this.text(0, 14, G.fit(this.model.unit, this.width, this.font, 1), 'start', 'grafica-unidad');
      this.domain = [n.min, n.max];
      return {y, left, top, bottom, right: this.width - 12};
    }
    timeAxis(x, lo, hi, bottom, left, right) {
      const t = G.timeTicks(lo, hi, Math.max(2, Math.min(8, Math.floor((right - left) / 100)))), f = v => G.format(v, t.spec, {lang: this.lang});
      G.spacedTicks(t.ticks, x, f, this.font, 12, this.width).forEach(v => { this.line(x(v), bottom, x(v), bottom + 4, 'grafica-eje'); this.chart.append(G.edgeText(this.chart, x(v), bottom + 18, f(v), {}, this.font)); });
      this.text(right, bottom + 34, 'Fecha UTC · distancia temporal real', 'end', 'mg-texto-suave');
    }
    draw(width) {
      this.marks?.destroy(); this.legend.replaceChildren(); this.items = []; this.width = width; this.note.hidden = true;
      this.chart = G.svg('svg', {class: 'mg-svg', width, height: 10, viewBox: `0 0 ${width} 10`, 'aria-label': this.model.title + '. Valores completos en la tabla.'});
      this.chart.append(G.svg('title', {}, this.model.title));
      this.stage.replaceChildren(this.chart);
      this.font = G.fontOf(this.chart);
      this.fill = G.patterns(this.chart, G.patternsEnabled(this.element));
      const height = this[this.model.type]();
      this.chart.setAttribute('height', height); this.chart.setAttribute('viewBox', `0 0 ${this.chart.getAttribute('width')} ${height}`);
      const order = this.items.map(n => +n.dataset.registro);
      this.marks = G.marks(this.element, this.chart, {items: this.items, label: this.model.title, describe: k => this.describe(order[k]), onSelect: k => this.choose(k === null ? null : order[k])});
      this.choose(this.selected);
    }
    calendario() {
      const {rows} = this.model, start = rows[0].time, end = rows.at(-1).time, max = Math.max(...rows.map(r => r.values[0]));
      const offset = (new Date(start).getUTCDay() + 6) % 7, weeks = Math.ceil(((end - start) / DAY + 1 + offset) / 7), x0 = 24;
      // Celda legible mínima de 12 px; si no cabe, desplazamiento horizontal declarado y etiquetado.
      const size = Math.max(12, Math.min(22, (this.width - x0 - 4) / weeks)), width = Math.max(this.width, Math.ceil(x0 + weeks * size + 4));
      if (width > this.width) {
        this.chart.setAttribute('width', width); this.chart.classList.add('mg-desplazable');
        this.stage.tabIndex = 0; this.stage.setAttribute('role', 'region'); this.stage.setAttribute('aria-label', this.model.title + ', desplazable horizontalmente');
        this.note.hidden = false; this.note.textContent = 'Desliza horizontalmente para ver las ' + weeks + ' semanas.';
      } else { this.stage.removeAttribute('tabindex'); this.stage.removeAttribute('role'); this.stage.removeAttribute('aria-label'); }
      // Iniciales de lunes a domingo según el idioma (en español «X» es miércoles).
      const weekday = new Intl.DateTimeFormat(this.lang, {weekday: 'narrow', timeZone: 'UTC'});
      for (let i = 0; i < 7; i++) if (i % 2 === 0 || size >= 16) { const t = this.text(x0 - 6, 36 + i * size + size / 2, weekday.format(Date.UTC(2024, 0, 1 + i)), 'end', 'mg-dia'); t.setAttribute('dominant-baseline', 'middle'); }
      const byDate = new Map(rows.map((r, i) => [r.time, {r, i}])); this.max = max;
      let lastLabel = -Infinity;
      for (let d = start; d <= end; d += DAY) {
        const index = (d - start) / DAY + offset, col = Math.floor(index / 7), day = index % 7, x = x0 + col * size, y = 36 + day * size, entry = byDate.get(d);
        if (new Date(d).getUTCDate() === 1 || d === start) {
          const label = G.format(d, 'month', {lang: this.lang}).replace(/ de \d{4}| \d{4}/, '');
          if (x - lastLabel >= G.textWidth(label, this.font) + 8) { this.text(x, 24, label); lastLabel = x; }
        }
        const v = entry?.r.values[0], level = v === undefined ? null : v === 0 ? 0 : Math.min(4, Math.ceil(v / Math.max(1, max) * 4));
        const cell = this.add('rect', {x, y, width: size - 2, height: size - 2, rx: 2, fill: `var(--calor-${level === null ? 'ausente' : level})`, stroke: 'var(--grafica-linea)', 'data-fecha': iso(d), 'data-valor': v ?? 'ausente'});
        if (entry) this.mark(cell, entry.i); else this.line(x + 3, y + size - 5, x + size - 5, y + 3, 'analitica-ausente');
      }
      const unit = this.model.unit;
      this.legend.append(el('li', `0 · ${[1, 2, 3, 4].map(i => this.f(max * i / 4)).join(' · ')} ${unit}. Intervalos (anterior, límite]; cero aparte. Diagonal: sin dato.`));
      for (let i = 0; i <= 4; i++) this.swatch(i === 0 ? '0' : `≤ ${this.f(max * i / 4)}`, i, `var(--calor-${i})`);
      return 36 + 7 * size + 12;
    }
    torta() {
      const {rows} = this.model, total = rows.reduce((s, r) => s + r.values[0], 0), r = Math.min(150, (this.width - 16) / 2), cx = this.width / 2, cy = r + 12, inner = this.donut ? r * .6 : 0; let a = -Math.PI / 2; this.total = total;
      rows.forEach((row, i) => {
        const fraction = row.values[0] / total, b = a + fraction * Math.PI * 2, p = t => [cx + r * Math.cos(t), cy + r * Math.sin(t)], q = t => [cx + inner * Math.cos(t), cy + inner * Math.sin(t)];
        if (fraction > 0) {
          let n;
          if (fraction === 1) n = this.add('circle', {cx, cy, r: (r + inner) / 2, fill: 'none', style: 'stroke:' + this.fill(i), 'stroke-width': r - inner});
          else n = this.add('path', {d: `M${p(a)} A${r},${r} 0 ${fraction > .5 ? 1 : 0},1 ${p(b)} L${q(b)} ${inner ? `A${inner},${inner} 0 ${fraction > .5 ? 1 : 0},0 ${q(a)}` : `L${cx},${cy}`} Z`, style: 'fill:' + this.fill(i), stroke: 'var(--grafica-papel)', 'stroke-width': 2});
          this.mark(n, i);
        }
        this.swatch(`${i + 1}. ${row.label} · ${this.f(row.values[0])} · ${G.format(fraction, 'pct1', {lang: this.lang})}`, i); a = b;
      });
      this.describe = i => [rows[i].label, this.fu(rows[i].values[0]), G.format(rows[i].values[0] / total, 'pct1', {lang: this.lang}) + ' de ' + this.fu(total)];
      if (this.donut) { this.text(cx, cy - 2, this.f(total), 'middle', 'mg-texto-fuerte'); this.text(cx, cy + 16, G.fit(this.model.unit, inner * 1.6, this.font, 1), 'middle'); return cy + r + 12; }
      this.text(cx, cy + r + 28, G.fit('Total: ' + this.fu(total), this.width, this.font, 1), 'middle'); return cy + r + 40;
    }
    areas() {
      const {rows, heads} = this.model, totals = rows.map(r => r.values.reduce((s, v) => s + v, 0)), height = Math.round(Math.max(260, Math.min(380, this.width * .55)));
      const {y, left, right, bottom} = this.yAxis(0, Math.max(...totals) || 1, height, true);
      const x = G.linear([rows[0].time, rows.at(-1).time], [left + 4, right]);
      for (let k = 2; k >= 0; k--) {
        const top = rows.map(r => [x(r.time), y(r.values.slice(0, k + 1).reduce((s, v) => s + v, 0))]), base = rows.map(r => [x(r.time), y(r.values.slice(0, k).reduce((s, v) => s + v, 0))]).reverse();
        this.add('path', {d: 'M' + [...top, ...base].map(p => p.join(',')).join(' L') + ' Z', style: 'fill:' + this.fill(k), 'fill-opacity': .55, stroke: this.color(k), 'stroke-width': 1.5});
      }
      heads.slice(1).forEach((h, i) => this.swatch(h, i));
      rows.forEach((r, i) => this.mark(this.add('circle', {cx: x(r.time), cy: y(totals[i]), r: 4, fill: 'var(--grafica-papel)', stroke: 'var(--grafica-tinta)', 'stroke-width': 2}), i));
      this.timeAxis(x, rows[0].time, rows.at(-1).time, bottom, left, right);
      // La suma de las tres series es el total de cada fecha (cantidades, no ratios).
      this.describe = i => [...this.describeBase(i), 'Total: ' + this.fu(totals[i])];
      return height;
    }
    describeBase(i) { const r = this.model.rows[i]; return [r.label, ...r.values.map((v, k) => this.model.heads[k + 1] + ': ' + this.fu(v))]; }
    caja() {
      const {rows} = this.model, narrow = this.width < 480, min = Math.min(...rows.map(r => r.values[0])), max = Math.max(...rows.map(r => r.values[4]));
      const labelWidth = narrow ? 0 : Math.min(this.width * .3, Math.ceil(Math.max(...rows.map(r => G.textWidth(r.label, this.font)))) + 16), left = labelWidth + 8, right = this.width - 16, rowH = narrow ? 64 : 48;
      const n = G.nice(min, max, Math.max(2, Math.floor((right - left) / 70))), f = G.tickFormat(n.ticks, this.model.spec, {lang: this.lang}), x = G.linear([n.min, n.max], [left, right]);
      this.domain = [n.min, n.max];
      const top = 44, height = top + rows.length * rowH + 30;
      G.spacedTicks(n.ticks, x, f, this.font, 12, this.width).forEach(v => { this.chart.append(G.edgeText(this.chart, x(v), 34, f(v), {}, this.font)); this.line(x(v), 40, x(v), height - 30); });
      rows.forEach((r, i) => {
        const [lo, q1, med, q3, hi] = r.values, y = top + i * rowH + (narrow ? 38 : 22), g = this.add('g', {}); this.mark(g, i);
        g.append(G.svg('line', {x1: x(lo), y1: y, x2: x(hi), y2: y, stroke: this.color(i), 'stroke-width': 2}), G.svg('rect', {x: x(q1), y: y - 12, width: Math.max(1, x(q3) - x(q1)), height: 24, style: 'fill:' + this.fill(i), 'fill-opacity': .35, stroke: this.color(i)}));
        [lo, med, hi].forEach((v, k) => g.append(G.svg('line', {x1: x(v), x2: x(v), y1: y - (k === 1 ? 12 : 7), y2: y + (k === 1 ? 12 : 7), stroke: this.color(i), 'stroke-width': k === 1 ? 3 : 2})));
        if (narrow) this.text(0, y - 18, G.fit(r.label, this.width, this.font, 1), 'start', 'mg-texto-fuerte'); else this.text(labelWidth, y + 4, G.fit(r.label, labelWidth - 8, this.font, 1), 'end', 'mg-texto-fuerte');
      });
      this.text(left, height - 8, G.fit(this.model.unit + ' · bigotes = mínimo y máximo · caja = Q1 a Q3', right - left, this.font, 1), 'start', 'mg-texto-suave');
      return height;
    }
    velas() {
      const {rows} = this.model, height = Math.round(Math.max(260, Math.min(380, this.width * .55))), min = Math.min(...rows.map(r => r.values[2])), max = Math.max(...rows.map(r => r.values[1]));
      const {y, left, right, bottom} = this.yAxis(min, max, height, false), span = rows.at(-1).time - rows[0].time;
      const x = span ? G.linear([rows[0].time, rows.at(-1).time], [left + 16, right - 16]) : () => (left + right) / 2;
      const gap = rows.length > 1 ? Math.min(...rows.slice(1).map((r, i) => x(r.time) - x(rows[i].time))) : 60, w = Math.max(1, Math.min(24, gap * .6));
      rows.forEach((r, i) => {
        const [o, h, l, c] = r.values, g = this.add('g', {}); this.mark(g, i); const color = this.color(c >= o ? 2 : 0);
        g.append(G.svg('line', {x1: x(r.time), x2: x(r.time), y1: y(h), y2: y(l), stroke: color, 'stroke-width': 2}), G.svg('rect', {x: x(r.time) - w / 2, y: y(Math.max(o, c)), width: w, height: Math.max(1, Math.abs(y(o) - y(c))), fill: c >= o ? 'var(--grafica-papel)' : color, stroke: color, 'stroke-width': 2}));
      });
      if (span) this.timeAxis(x, rows[0].time, rows.at(-1).time, bottom, left, right); else this.text((left + right) / 2, bottom + 18, rows[0].label, 'middle');
      this.swatch('Hueca: cierre ≥ apertura', 2, 'var(--grafica-papel);stroke:' + this.color(2)); this.swatch('Rellena: cierre < apertura', 0, this.color(0));
      return height;
    }
    // Encuadre del mapa: la caja de Colombia y de todos los puntos, escalada al ancho sin deformar.
    mapBase(points) {
      const base = ([lon, lat]) => [(lon + 80) * 21, (14 - lat) * 21], ring = NotaGeografia.colombia.coordinates[0].map(base), all = [...ring, ...points.map(base)];
      const x0 = Math.min(...all.map(p => p[0])) - 20, x1 = Math.max(...all.map(p => p[0])) + 20, y0 = Math.min(...all.map(p => p[1])) - 20, y1 = Math.max(...all.map(p => p[1])) + 20;
      const k = Math.min(this.width / (x1 - x0), 460 / (y1 - y0)), dx = (this.width - (x1 - x0) * k) / 2;
      const project = c => { const [px, py] = base(c); return [dx + (px - x0) * k, 24 + (py - y0) * k]; };
      for (const ring of NotaGeografia.colombia.coordinates) this.add('path', {d: 'M' + ring.map(project).map(p => p.join(',')).join(' L') + ' Z', fill: 'var(--calor-0)', stroke: 'var(--escena-linea)', 'stroke-width': 1.5});
      this.text(this.width - 4, 14, 'N ↑', 'end');
      this.mapHeight = 24 + (y1 - y0) * k + 24;
      this.text(0, this.mapHeight - 6, G.fit('Colombia · WGS84 · proyección equirectangular', this.width, this.font, 1), 'start', 'mg-texto-suave');
      this.k = k;
      return project;
    }
    rutas() {
      const rows = this.model.rows, project = this.mapBase(rows.flatMap(r => [[r.values[1], r.values[0]], [r.values[3], r.values[2]]])), max = Math.max(...rows.map(r => r.values[4])) || 1; this.max = max;
      const cities = new Map();
      rows.forEach((r, i) => {
        const [a, b, c, d, v] = r.values, p = project([b, a]), q = project([d, c]), dx = q[0] - p[0], dy = q[1] - p[1], distance = Math.hypot(dx, dy) || 1, bend = Math.min(22, distance * .2);
        if (v > 0) { const n = this.add('path', {d: `M${p} Q${(p[0] + q[0]) / 2 - dy / distance * bend},${(p[1] + q[1]) / 2 + dx / distance * bend} ${q}`, fill: 'none', stroke: this.color(i), 'stroke-dasharray': G.dash(i), 'stroke-width': Math.max(1.5, v / max * 8), 'stroke-linecap': 'round'}); this.mark(n, i); }
        const names = r.label.split(/\s*→\s*/); [[p, names[0]], [q, names[1]]].forEach(([pt, name]) => { const key = pt.join(','); if (!cities.has(key)) cities.set(key, {pt, name: name || 'Ciudad ' + (cities.size + 1)}); });
        this.swatch(`${i + 1}. ${r.label} · ${this.fu(v)}`, i, this.color(i));
      });
      // Nodos al final; rótulos solo si no pisan otro rótulo (el nombre sigue en la tabla y en el tip).
      const placed = [];
      cities.forEach(({pt, name}) => {
        this.add('circle', {cx: pt[0], cy: pt[1], r: 5, fill: 'var(--grafica-papel)', stroke: 'var(--grafica-tinta)', 'stroke-width': 2});
        const w = G.textWidth(name, this.font), x = pt[0] + 9 + w > this.width ? pt[0] - 9 - w : pt[0] + 9, box = [x, pt[1] - 20, w, 14];
        if (placed.some(b => b[0] < box[0] + box[2] && box[0] < b[0] + b[2] && b[1] < box[1] + box[3] && box[1] < b[1] + b[3])) return;
        placed.push(box); const label = this.text(x, pt[1] - 9, name); label.setAttribute('paint-order', 'stroke'); label.setAttribute('stroke', 'var(--grafica-papel)'); label.setAttribute('stroke-width', 4); label.setAttribute('stroke-linejoin', 'round');
      });
      this.legend.prepend(el('li', `Grosor proporcional · máximo ${this.fu(max)}`));
      this.describe = i => [rows[i].label, this.fu(rows[i].values[4])];
      return this.mapHeight;
    }
    burbujas() {
      const rows = this.model.rows, project = this.mapBase(rows.map(r => [r.values[1], r.values[0]])), max = Math.max(...rows.map(r => r.values[2])) || 1; this.max = max;
      const rmax = Math.max(10, 28 * this.k);
      rows.forEach((r, i) => { const [lat, lon, value] = r.values, p = project([lon, lat]), radius = Math.sqrt(value / max) * rmax; const n = this.add('circle', {cx: p[0], cy: p[1], r: Math.max(radius, 2), style: 'fill:' + this.fill(i), 'fill-opacity': .45, stroke: this.color(i), 'stroke-width': value ? 2 : 1}); this.mark(n, i); this.text(p[0] + radius + 5, p[1] + 4, String(i + 1)); this.swatch(`${i + 1}. ${r.label} · ${this.fu(value)}`, i); });
      this.legend.prepend(el('li', `Área proporcional al volumen · máximo ${this.fu(max)}`));
      this.describe = i => [rows[i].label, this.fu(rows[i].values[2]), 'Lat. ' + rows[i].values[0] + ', lon. ' + rows[i].values[1]];
      return this.mapHeight;
    }
    destroy() { this.watch?.disconnect(); this.marks?.destroy(); this.abort.abort(); this.parts.forEach(p => p.remove()); this.element.classList.remove('nota-analitica'); instances.delete(this.element); }
  }
  function init(root = document) { return [...(root.matches?.('[data-analitica]') ? [root] : []), ...root.querySelectorAll('[data-analitica]')].map(e => { if (instances.has(e)) return instances.get(e); e.querySelector('[data-error-analitica]')?.remove(); try { return new Chart(e); } catch (error) { const p = el('p', 'No se pudo construir la gráfica: ' + error.message); p.dataset.errorAnalitica = ''; p.className = 'grafica-error'; e.prepend(p); return null; } }); }
  window.NotaAnalitica = {init, get: e => instances.get(e)}; init();
})();
