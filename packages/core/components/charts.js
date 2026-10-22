/* Margen · gráficas SVG desde tablas semánticas. Requiere chart-core.js (MargenGraficas).
   La tabla es la única fuente de cifras. Se dibuja al ancho real de la figura; NotaGraficas.init(raíz)
   para contenido insertado después. */
(() => {
  'use strict';
  const G = window.MargenGraficas;
  const instances = new WeakMap();
  const TYPES = ['barras', 'lineas', 'temporal', 'dispersion', 'distribucion', 'calor', 'columnas', 'cambio', 'meta'];
  const element = (tag, cls, text) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  };
  function number(raw, missing = false) {
    if (raw === null || raw.trim() === '') {
      if (missing) return null;
      throw new TypeError('Falta un data-valor numérico.');
    }
    const n = Number(raw);
    if (!Number.isFinite(n)) throw new TypeError('El valor debe ser finito.');
    return n;
  }
  // Compatibilidad con la API anterior: una única función coloca valores y ticks.
  function scale(min, max, start, end) {
    if (![min, max, start, end, max - min, end - start].every(Number.isFinite) || min >= max) throw new TypeError('Dominio inválido.');
    return v => start + (v - min) / (max - min) * (end - start);
  }
  function domain(values, zero = false) {
    if (!values.length) return [0, 1];
    const r = zero ? G.niceZero(values) : G.nice(Math.min(...values), Math.max(...values));
    return [r.min, r.max];
  }
  function delta(current, previous, spec = 'auto', lang) {
    if (current === null || previous === null) return 'Sin comparación · dato ausente';
    const change = current - previous, sign = change > 0 ? '+' : '';
    const absolute = sign + G.format(change, spec, {lang});
    if (previous === 0) return absolute + ' · porcentaje no definido (base 0)';
    return absolute + ' · ' + sign + G.format(change / Math.abs(previous), 'pct1', {lang});
  }
  function read(figure) {
    const type = figure.dataset.grafica;
    if (!TYPES.includes(type)) throw new TypeError('Tipo de gráfica desconocido.');
    const table = figure.querySelector('table');
    const headCells = [...(table?.tHead?.rows[0]?.cells || [])];
    const heads = headCells.map(e => e.textContent.trim());
    const rows = [...(table?.tBodies[0]?.rows || [])];
    if (heads.length < 2 || rows.length > 500) throw new TypeError('Se necesitan cabeceras y hasta 500 filas.');
    if (type === 'calor' && (heads.length > 32 || rows.length > 31)) throw new TypeError('El mapa admite hasta 31 × 31 celdas.');
    if (['barras', 'lineas', 'temporal'].includes(type) && heads.length > 5) throw new TypeError('Hasta cuatro series por figura.');
    if (type === 'columnas' && (heads.length > 9 || rows.length > 40)) throw new TypeError('Columnas: hasta ocho series y 40 categorías.');
    if (['dispersion', 'distribucion', 'cambio'].includes(type) && heads.length !== 3) throw new TypeError('Se necesitan tres columnas.');
    if (type === 'cambio' && rows.length > 30) throw new TypeError('Antes y después: hasta 30 filas.');
    if (type === 'meta' && (heads.length < 3 || heads.length > 6 || rows.length > 12)) throw new TypeError('Meta: etiqueta, valor, meta y hasta tres umbrales; hasta 12 filas.');
    const data = rows.map(row => {
      if (row.cells.length !== heads.length) throw new TypeError('Todas las filas deben tener las mismas columnas.');
      const label = row.cells[0].textContent.trim();
      const values = [...row.cells].slice(1).map(c => number(c.getAttribute('data-valor'), true));
      let x = null, end = null;
      if (type === 'temporal') {
        const date = row.cells[0].querySelector('time')?.getAttribute('datetime');
        x = Date.parse(date + 'T00:00:00Z');
        if (!/^\d{4}-\d{2}-\d{2}$/.test(date || '') || !Number.isFinite(x) || new Date(x).toISOString().slice(0, 10) !== date) throw new TypeError('Fecha ISO YYYY-MM-DD inválida.');
      }
      if (type === 'distribucion') {
        x = number(row.cells[0].getAttribute('data-desde'));
        end = number(row.cells[0].getAttribute('data-hasta'));
        if (x >= end || values[0] === null || values[0] < 0 || !Number.isInteger(values[0])) throw new TypeError('Intervalos crecientes y frecuencias enteras no negativas.');
        // Columna de densidad se calcula, no es una segunda fuente manual.
        values[1] = values[0] / (end - x);
        if (!Number.isFinite(values[1])) throw new TypeError('La densidad excede la precisión numérica.');
      }
      if (type === 'dispersion' && values.some(v => v === null)) throw new TypeError('Cada punto necesita X e Y.');
      if (type === 'meta') {
        if (values[0] === null || values[1] === null) throw new TypeError('Cada fila de meta necesita valor y meta.');
        const bands = values.slice(2);
        if (bands.some(v => v === null || v < 0) || bands.some((v, i) => i && v <= bands[i - 1])) throw new TypeError('Umbrales de meta no negativos y crecientes.');
      }
      if (type === 'columnas' && figure.dataset.apilado === 'si' && values.some(v => v !== null && v < 0)) throw new TypeError('Las columnas apiladas no admiten negativos.');
      return {label, values, x, end, row};
    });
    if (type === 'temporal' && data.some((r, i) => i && r.x <= data[i - 1].x)) throw new TypeError('Fechas estrictamente crecientes; no se reordenan ni agregan datos.');
    if (type === 'distribucion' && data.some((r, i) => i && r.x < data[i - 1].end)) throw new TypeError('Intervalos ordenados, sin solapamiento.');
    const model = {type, table, heads, data, title: table.caption?.textContent.trim() || 'Gráfica',
      columns: headCells.slice(1).map(th => ({name: th.textContent.trim(), spec: G.specOf(th, figure), unit: G.unitOf(th) || figure.dataset.unidad || ''}))};
    if (type === 'calor') model.heat = heatScale(figure, data);
    return model;
  }
  // Escala de calor: umbrales declarados o cuantiles de los datos; con data-centro, divergente.
  function heatScale(figure, data) {
    const values = data.flatMap(r => r.values).filter(v => v !== null);
    const raw = figure.dataset.umbrales, centre = figure.dataset.centro;
    let limits;
    if (raw) {
      limits = raw.split(',').map(v => number(v));
      if (limits.length < 3 || limits.length > 6 || limits.some((v, i) => i && v <= limits[i - 1])) throw new TypeError('De tres a seis límites estrictamente crecientes.');
      if (values.some(v => v < limits[0] || v > limits.at(-1))) throw new TypeError('Un valor está fuera de la escala de calor.');
    } else if (centre !== undefined) {
      const c = number(centre), d = Math.max(...values.map(v => Math.abs(v - c))) || 1;
      limits = [c - d, c - .6 * d, c - .2 * d, c + .2 * d, c + .6 * d, c + d];
    } else {
      // Cuantiles: cada nivel agrupa una parte similar de los datos; no se inventan valores.
      const sorted = [...values].sort((a, b) => a - b), q = p => sorted[Math.min(sorted.length - 1, Math.floor(p * (sorted.length - 1) + 1e-9))];
      limits = [...new Set([0, .2, .4, .6, .8, 1].map(q))];
      // Dos cortes: el máximo forma su propio nivel para que el resto no se pinte como máximo.
      if (limits.length === 2) limits = [limits[0], limits[1], limits[1]];
    }
    // Todos los valores iguales: un solo nivel neutro, sin rango inventado ni intensidad máxima.
    const constant = limits.length === 1;
    const levels = constant ? 1 : limits.length - 1, diverging = centre !== undefined;
    const level = v => { const k = limits.slice(1).findIndex(l => v < l); return k === -1 ? levels - 1 : k; };
    const index = k => constant ? (limits[0] === 0 ? 0 : 2) : Math.round(k * 4 / Math.max(1, levels - 1));
    const fill = k => diverging
      ? (k === (levels - 1) / 2 ? 'var(--panel)' : 'color-mix(in oklab, ' + (k < levels / 2 ? 'var(--grafica-2)' : 'var(--grafica-1)') + ' ' + Math.round(20 + 50 * Math.abs(k - (levels - 1) / 2) / ((levels - 1) / 2)) + '%, var(--grafica-papel))')
      : 'var(--calor-' + index(k) + ')';
    return {limits, levels, level, fill, index, constant, diverging, quantile: !raw && !diverging && !constant};
  }

  class NotaGrafica {
    constructor(figure) {
      if (instances.has(figure)) throw new TypeError('Ya existe una gráfica en este contenedor.');
      if (!G) throw new TypeError('Incluye packages/core/components/chart-core.js antes de charts.js.');
      this.figure = figure; this.parts = []; this.original = [];
      this.details = figure.querySelector('details'); this.wasOpen = this.details?.open;
      this.model = read(figure);
      this.lang = G.lang(figure); this.words = G.words(this.lang);
      try { this.build(); instances.set(figure, this); } catch (error) { this.destroy(); throw error; }
    }
    add(e) { this.parts.push(e); this.figure.insertBefore(e, this.anchor); return e; }
    build() {
      const {type, heads, data, title, columns} = this.model;
      this.figure.classList.add('nota-grafica');
      this.anchor = this.figure.firstChild;
      this.add(element('h3', 'grafica-titulo', title));
      if (!data.length || data.every(r => r.values.every(v => v === null))) { this.add(element('p', 'grafica-vacia', 'Sin datos disponibles.')); return; }
      this.region = this.add(element('div', 'grafica-caja'));
      if (['barras', 'lineas', 'temporal', 'columnas'].includes(type) && heads.length > 2 || type === 'cambio') {
        this.legend = G.legend(type === 'cambio' ? heads.slice(1) : columns.map(c => c.name), {locale: this.lang, shapes: type === 'cambio', targets: i => [...(this.svg?.querySelectorAll(`[data-mg-serie="${i}"]`) || [])]});
        this.add(this.legend.element);
      }
      if (type === 'calor') this.heatLegend();
      if (type === 'temporal') this.comparison();
      this.status = this.add(element('p', 'grafica-estado'));
      this.status.setAttribute('role', 'status');
      this.add(G.exporter(this.figure, {table: this.model.table, title, getSvg: () => this.svg}));
      if (type === 'distribucion') data.forEach((r, i) => {
        const cell = r.row.cells[2]; this.original.push([cell, cell.textContent]);
        cell.textContent = G.format(r.values[1], 'auto', {lang: this.lang});
      });
      if (type === 'calor') data.forEach((r, j) => [...r.row.cells].slice(1).forEach((cell, i) => {
        const v = r.values[i];
        this.original.push([cell, null, cell.getAttribute('data-nivel')]);
        cell.dataset.nivel = v === null ? 'ausente' : this.model.heat.index(this.model.heat.level(v));
      }));
      if (type === 'calor') { this.tableClass = this.model.table.getAttribute('class'); this.model.table.classList.add('tabla-calor'); }
      // La figura es la vista principal: la tabla queda a un clic. El estado que elija el lector se respeta.
      if (this.details) this.details.open = false;
      this.watch = G.responsive(this.figure, width => this.draw(width));
    }
    draw(width) {
      const {type, title} = this.model;
      this.marks?.destroy();
      const svg = G.svg('svg', {class: 'mg-svg', width, height: 10, viewBox: `0 0 ${width} 10`, 'aria-label': title});
      svg.append(G.svg('title', {}, title), G.svg('desc', {}, 'Los valores exactos y las unidades están en la tabla de datos de esta figura.'));
      this.region.replaceChildren(svg);
      this.svg = svg; this.width = width;
      this.font = G.fontOf(svg);
      this.fill = G.patterns(svg, G.patternsEnabled(this.figure));
      const result = this[type === 'distribucion' ? 'histogram' : type === 'dispersion' ? 'scatter' : type === 'lineas' || type === 'temporal' ? 'lines' : type === 'calor' ? 'heatmap' : type === 'columnas' ? 'columns' : type === 'cambio' ? 'dumbbell' : type === 'meta' ? 'bullet' : 'bars'](svg, width);
      svg.setAttribute('height', result.height);
      svg.setAttribute('viewBox', `0 0 ${result.width || width} ${result.height}`);
      this.marks = G.marks(this.figure, svg, {items: result.items, describe: result.describe, status: this.status, label: title, columns: result.columns});
      this.legend?.repaint();
    }
    fmt(v, col = 0) { const c = this.model.columns[col] || this.model.columns[0]; return G.format(v, c.spec, {lang: this.lang}); }
    fmtUnit(v, col = 0) { const c = this.model.columns[col] || this.model.columns[0]; return v === null ? this.words.missing : G.format(v, c.spec, {lang: this.lang, unit: c.unit}); }
    unit() { return this.figure.dataset.unidad || this.model.columns.map(c => c.name).join(' / '); }
    text(x, y, value, attrs = {}) { const t = G.svg('text', {x, y, ...attrs}, value); this.svg.append(t); return t; }
    // Rejilla vertical numérica (eje Y) con título arriba a la izquierda. Devuelve márgenes y escala.
    yFrame(svg, width, height, range, {title, spec, xTitle, bottom = 30, pad = 0}) {
      const extra = (range[1] - range[0]) * pad;
      const n = G.nice(range[0] - extra, range[1] + extra, Math.max(3, Math.min(8, Math.floor((height - 60) / 44))));
      const f = G.tickFormat(n.ticks, spec || this.model.columns[0]?.spec, {lang: this.lang});
      const left = Math.ceil(Math.max(...n.ticks.map(v => G.textWidth(f(v), this.font)))) + 10;
      const top = 30, plotBottom = height - bottom - (xTitle ? 18 : 0);
      const y = G.linear([n.min, n.max], [plotBottom, top]);
      G.axis(svg, {orient: 'left', scale: y, ticks: n.ticks, format: f, from: left, to: width - 8, at: left - 6});
      if (title) this.text(0, 14, G.fit(title, width, this.font, 1), {class: 'grafica-unidad'});
      if (xTitle) this.text(width - 8, height - 4, G.fit(xTitle, width - 16, this.font, 1), {'text-anchor': 'end', class: 'grafica-unidad'});
      svg.dataset.yMin = n.min; svg.dataset.yMax = n.max;
      return {y, left, right: width - 12, top, bottom: plotBottom, ticks: n.ticks};
    }
    xNumeric(svg, range, {left, right, bottom, spec, top, pad = 0}) {
      const count = Math.max(2, Math.min(10, Math.floor((right - left) / 70))), extra = (range[1] - range[0]) * pad;
      const n = G.nice(range[0] - extra, range[1] + extra, count), f = G.tickFormat(n.ticks, spec, {lang: this.lang});
      const x = G.linear([n.min, n.max], [left, right]);
      const ticks = G.spacedTicks(n.ticks, x, f, this.font, 12, this.width);
      G.axis(svg, {orient: 'bottom', scale: x, ticks, format: f, from: top, to: bottom, at: bottom + 18, font: this.font});
      svg.dataset.xMin = n.min; svg.dataset.xMax = n.max;
      return x;
    }
    // Rótulos de categoría: completos si caben; si no, abreviados y cada k posiciones. Nunca fuera del SVG.
    categoryLabels(labels, x, space, y, width) {
      const room = (i, k) => Math.min(k * space - 8, 2 * Math.min(x(i), width - x(i)) - 2);
      const pick = k => labels.map((l, i) => i % k ? null : G.fit(l, room(i, k), this.font, Math.min(3, l.length)));
      let k = 1, shown = pick(1);
      while (k < labels.length && shown.some(t => t === '')) shown = pick(++k);
      shown.forEach((t, i) => { if (t) this.text(x(i), y, t, {'text-anchor': 'middle', 'data-label-index': i}); });
    }
    // ---------- Barras horizontales ----------
    bars(svg, width) {
      const {heads, data, columns} = this.model, narrow = width < 480, series = heads.length - 1;
      const values = data.flatMap(r => r.values).filter(v => v !== null);
      const valueWidth = Math.ceil(Math.max(...data.flatMap(r => r.values.map((v, i) => G.textWidth(this.fmt(v, i), this.font))))) + 12;
      const labelWidth = narrow ? width : Math.min(Math.round(width * .32), Math.ceil(Math.max(...data.map(r => G.textWidth(r.label, this.font)))) + 16);
      const left = narrow ? 4 : labelWidth, right = width - valueWidth, bar = 20, gap = 4;
      const top = 30;
      const labels = data.map(r => G.wrap(r.label, (narrow ? width : labelWidth) - 12, this.font, 2));
      const rowHeight = data.map((r, j) => narrow ? labels[j].length * 15 + 6 + series * (bar + gap) + 14 : Math.max(series * (bar + gap), labels[j].length * 15 + 6) + 14);
      const height = top + rowHeight.reduce((a, b) => a + b, 0) + 34;
      const x = this.xNumeric(svg, [Math.min(0, ...values), Math.max(0, ...values)], {left, right, top: top - 8, bottom: height - 30, spec: columns[0].spec});
      this.text(0, 14, G.fit(this.unit(), width, this.font, 1), {class: 'grafica-unidad'});
      const items = [], info = [];
      let rowTop = top;
      data.forEach((r, j) => {
        const t = this.text(narrow ? 4 : 0, rowTop + 12, '', {class: 'mg-texto-fuerte' + (narrow ? ' mg-halo' : '')});
        labels[j].forEach((line, k) => t.append(G.svg('tspan', {x: narrow ? 4 : 0, dy: k ? 15 : 0}, line)));
        let y = rowTop + (narrow ? labels[j].length * 15 + 2 : 0);
        r.values.forEach((v, i) => {
          const g = G.svg('g', {'data-mg-serie': i});
          if (v === null) g.append(G.svg('text', {x: x(0) + 4, y: y + 14, class: 'mg-texto-suave'}, this.words.missing));
          else {
            g.append(G.svg('rect', {x: Math.min(x(0), x(v)), y, width: Math.max(Math.abs(x(v) - x(0)), .5), height: bar, class: 'grafica-barra serie-' + i, style: 'fill:' + this.fill(i), 'data-value': v}));
            g.append(G.svg('text', {x: right + 8, y: y + 14, class: 'mg-texto-fuerte'}, this.fmt(v, i)));
          }
          svg.append(g); items.push(g); info.push([r.label, (series > 1 ? heads[i + 1] + ': ' : '') + this.fmtUnit(v, i)]);
          y += bar + gap;
        });
        rowTop += rowHeight[j];
      });
      return {height, items, describe: i => info[i]};
    }
    // ---------- Columnas agrupadas o apiladas ----------
    columns(svg, width) {
      const {heads, data, columns} = this.model, stacked = this.figure.dataset.apilado === 'si', series = heads.length - 1;
      const height = Math.round(Math.max(260, Math.min(380, width * .55)));
      const totals = data.map(r => r.values.reduce((a, v) => a + (v || 0), 0));
      const values = stacked ? totals : data.flatMap(r => r.values).filter(v => v !== null);
      const frame = this.yFrame(svg, width, height, [Math.min(0, ...values), Math.max(0, ...values)], {title: this.unit(), xTitle: heads[0]});
      const band = (frame.right - frame.left) / data.length, inner = band * .72, x0 = j => frame.left + band * j + (band - inner) / 2;
      const items = [], info = [];
      data.forEach((r, j) => {
        let base = 0;
        r.values.forEach((v, i) => {
          const g = G.svg('g', {'data-mg-serie': i});
          const w = stacked ? inner : inner / series, x = stacked ? x0(j) : x0(j) + w * i;
          // Sin dato: un marcador discontinuo donde empezaría el tramo, nunca una barra de cero.
          if (v === null) g.append(G.svg('rect', {x: x + 1, y: frame.y(stacked ? base : 0) - 10, width: Math.max(w - 3, 1), height: 9, class: 'mg-sin-dato'}));
          else {
            const a = stacked ? base : 0, b = stacked ? base + v : v;
            g.append(G.svg('rect', {x, y: Math.min(frame.y(a), frame.y(b)), width: Math.max(w - (stacked ? 0 : 1), 1), height: Math.max(Math.abs(frame.y(a) - frame.y(b)), .5), class: 'grafica-barra serie-' + i, style: 'fill:' + this.fill(i), 'data-value': v}));
            if (stacked) base += v;
          }
          svg.append(g); items.push(g);
          const complete = !r.values.some(x => x === null);
          info.push([r.label + (series > 1 ? ' · ' + heads[i + 1] : ''), this.fmtUnit(v, i), ...(stacked && series > 1 ? [this.words.total + ': ' + (complete ? this.fmtUnit(totals[j], 0) : 'incompleto (falta un dato)')] : [])]);
        });
        if (stacked && !r.values.some(v => v === null) && inner >= G.textWidth(this.fmt(totals[j]), this.font)) this.text(x0(j) + inner / 2, frame.y(totals[j]) - 6, this.fmt(totals[j]), {'text-anchor': 'middle', class: 'mg-texto-fuerte'});
      });
      this.categoryLabels(data.map(r => r.label), j => frame.left + band * (j + .5), band, frame.bottom + 18, width);
      return {height, items, describe: i => info[i]};
    }
    // ---------- Líneas por categoría o por fecha ----------
    lines(svg, width) {
      const {data, heads, type} = this.model, series = heads.length - 1;
      const height = Math.round(Math.max(240, Math.min(360, width * .55)));
      const all = data.flatMap(r => r.values).filter(v => v !== null), lo = Math.min(...all), hi = Math.max(...all);
      const range = lo === hi && lo >= 0 ? [0, hi || 1] : [lo, hi];
      const frame = this.yFrame(svg, width, height, range, {title: this.unit(), xTitle: heads[0], pad: lo === hi ? 0 : .05});
      const pad = type === 'temporal' ? 6 : Math.min(40, (frame.right - frame.left) / Math.max(2, data.length) / 2);
      let x, labelAt;
      if (type === 'temporal') {
        const lo = data[0].x, hi = data.at(-1).x === lo ? lo + 86400000 : data.at(-1).x;
        x = G.linear([lo, hi], [frame.left + pad, frame.right - pad]);
        const t = G.timeTicks(lo, hi, Math.max(2, Math.min(8, Math.floor((frame.right - frame.left) / 100)))), f = v => G.format(v, t.spec, {lang: this.lang});
        G.spacedTicks(t.ticks, x, f, this.font, 12, this.width).forEach(v => {
          svg.append(G.svg('line', {x1: x(v), x2: x(v), y1: frame.bottom, y2: frame.bottom + 4, class: 'grafica-eje', 'data-tick-x': v}));
          svg.append(G.edgeText(svg, x(v), frame.bottom + 18, f(v), {}, this.font));
        });
        svg.dataset.xMin = lo; svg.dataset.xMax = hi;
      } else {
        x = data.length > 1 ? G.linear([0, data.length - 1], [frame.left + pad, frame.right - pad]) : () => (frame.left + frame.right) / 2;
        const space = data.length > 1 ? (frame.right - frame.left - 2 * pad) / (data.length - 1) : frame.right - frame.left;
        this.categoryLabels(data.map(r => r.label), x, space, frame.bottom + 18, width);
      }
      const pos = j => x(type === 'temporal' ? data[j].x : j);
      const items = [], info = [];
      for (let i = 0; i < series; i++) {
        let d = '', pen = false;
        data.forEach((r, j) => {
          const v = r.values[i];
          if (v === null) { pen = false; return; }
          d += (pen ? 'L' : 'M') + pos(j).toFixed(2) + ' ' + frame.y(v).toFixed(2); pen = true;
        });
        svg.append(G.svg('path', {d, class: 'grafica-trazo serie-' + i, 'data-mg-serie': i}));
      }
      // Puntos (y ausencias) en orden de lectura: fila por fila, serie por serie.
      data.forEach((r, j) => r.values.forEach((v, i) => {
        const cx = pos(j), cy = v === null ? frame.bottom : frame.y(v), label = type === 'temporal' ? G.format(r.x, 'date', {lang: this.lang}) : r.label;
        const g = G.svg('g', {'data-mg-serie': i, 'data-value': v ?? '', 'data-cx': cx, 'data-cy': cy, 'data-index': j});
        if (v === null) g.append(G.svg('path', {d: `M${cx - 4} ${cy - 4}l8 8M${cx + 4} ${cy - 4}l-8 8`, class: 'grafica-eje'}));
        else g.append(G.svg('path', {d: G.shape(i, cx, cy, i ? 4 : 3.5), class: 'grafica-punto mg-forma serie-' + i}));
        svg.append(g); items.push(g); info.push([label, (series > 1 ? heads[i + 1] + ': ' : '') + this.fmtUnit(v, i)]);
      }));
      return {height, items, describe: i => info[i]};
    }
    scatter(svg, width) {
      const {data, heads, columns} = this.model;
      const height = Math.round(Math.max(260, Math.min(380, width * .6)));
      const frame = this.yFrame(svg, width, height, [Math.min(...data.map(r => r.values[1])), Math.max(...data.map(r => r.values[1]))], {title: heads[2] + (columns[1].unit ? ' · ' + columns[1].unit : ''), xTitle: heads[1] + (columns[0].unit ? ' · ' + columns[0].unit : ''), spec: columns[1].spec, pad: .06});
      const x = this.xNumeric(svg, [Math.min(...data.map(r => r.values[0])), Math.max(...data.map(r => r.values[0]))], {left: frame.left, right: frame.right, top: frame.top, bottom: frame.bottom, spec: columns[0].spec, pad: .06});
      const items = data.map(r => {
        const g = G.svg('g', {'data-x': r.values[0], 'data-y': r.values[1]});
        g.append(G.svg('circle', {cx: x(r.values[0]), cy: frame.y(r.values[1]), r: 5, class: 'grafica-serie serie-0'}));
        svg.append(g); return g;
      });
      return {height, items, describe: i => [data[i].label, heads[1] + ': ' + this.fmtUnit(data[i].values[0], 0), heads[2] + ': ' + this.fmtUnit(data[i].values[1], 1)]};
    }
    histogram(svg, width) {
      const {data, heads, columns} = this.model;
      const height = Math.round(Math.max(240, Math.min(340, width * .5)));
      const frame = this.yFrame(svg, width, height, [0, Math.max(...data.map(r => r.values[1])) || 1], {title: heads[2], xTitle: heads[0] + (this.figure.dataset.unidad ? ' · ' + this.figure.dataset.unidad : '')});
      const x = this.xNumeric(svg, [data[0].x, data.at(-1).end], {left: frame.left, right: frame.right, top: frame.top, bottom: frame.bottom, spec: columns[0].spec});
      const items = data.map(r => {
        const g = G.svg('g', {});
        g.append(G.svg('rect', {x: x(r.x), y: frame.y(r.values[1]), width: Math.max(.5, x(r.end) - x(r.x)), height: frame.y(0) - frame.y(r.values[1]), class: 'grafica-barra serie-0', 'data-desde': r.x, 'data-hasta': r.end, 'data-count': r.values[0], 'data-density': r.values[1]}));
        svg.append(g); return g;
      });
      return {height, items, describe: i => [data[i].label, heads[1] + ': ' + G.format(data[i].values[0], 'auto', {lang: this.lang}), heads[2] + ': ' + G.format(data[i].values[1], 'auto', {lang: this.lang})]};
    }
    // ---------- Antes y después (dumbbell) ----------
    dumbbell(svg, width) {
      const {data, heads, columns} = this.model, narrow = width < 480;
      const deltas = data.map(r => delta(r.values[1], r.values[0], columns[1].spec, this.lang));
      const valueWidth = narrow ? 0 : Math.min(width * .28, Math.ceil(Math.max(...deltas.map(d => G.textWidth(d.split(' · ')[0], this.font)))) + 16);
      const labelWidth = narrow ? width : Math.min(Math.round(width * .3), Math.ceil(Math.max(...data.map(r => G.textWidth(r.label, this.font)))) + 16);
      const left = narrow ? 10 : labelWidth, right = width - valueWidth - 10, top = 30;
      const labels = data.map(r => G.wrap(r.label + (narrow ? ' · ' + deltas[data.indexOf(r)].split(' · ')[0] : ''), (narrow ? width : labelWidth) - 12, this.font, 2));
      const rowHeight = labels.map(l => narrow ? l.length * 15 + 30 : Math.max(32, l.length * 15 + 12));
      const height = top + rowHeight.reduce((a, b) => a + b, 0) + 34;
      const all = data.flatMap(r => r.values).filter(v => v !== null);
      const x = this.xNumeric(svg, [Math.min(...all), Math.max(...all)], {left, right, top: top - 8, bottom: height - 30, spec: columns[0].spec});
      this.text(0, 14, G.fit(this.unit(), width, this.font, 1), {class: 'grafica-unidad'});
      if (!narrow) this.text(width, 14, 'Cambio', {'text-anchor': 'end', class: 'grafica-unidad'});
      const items = [], info = [];
      let y0 = top;
      data.forEach((r, j) => {
        const t = this.text(narrow ? 4 : 0, y0 + 12, '', {class: 'mg-texto-fuerte' + (narrow ? ' mg-halo' : '')});
        labels[j].forEach((line, k) => t.append(G.svg('tspan', {x: narrow ? 4 : 0, dy: k ? 15 : 0}, line)));
        const cy = narrow ? y0 + labels[j].length * 15 + 8 : y0 + 10;
        const [a, b] = r.values;
        if (a !== null && b !== null) svg.append(G.svg('line', {x1: x(a), x2: x(b), y1: cy, y2: cy, class: 'mg-conector' + (b > a ? ' mg-sube' : '')}));
        r.values.forEach((v, i) => {
          const g = G.svg('g', {'data-mg-serie': i, 'data-value': v ?? ''});
          const other = r.values[1 - i];
          if (v === null) g.append(G.svg('text', {x: other === null ? left : x(other) + 12, y: cy + 4, class: 'mg-texto-suave'}, G.fit(heads[i + 1] + ': ' + this.words.missing, Math.max(40, right - (other === null ? left : x(other) + 12)), this.font, 3)));
          else g.append(G.svg('path', {d: G.shape(i, x(v), cy, 6), class: 'serie-' + i + (i ? ' grafica-barra' : ' grafica-punto mg-forma'), style: i ? 'fill:var(--serie)' : ''}));
          svg.append(g); items.push(g);
          info.push([r.label, heads[i + 1] + ': ' + this.fmtUnit(v, i), 'Cambio: ' + deltas[j]]);
        });
        if (!narrow) this.text(width, cy + 4, deltas[j].split(' · ')[0], {'text-anchor': 'end', class: 'mg-texto-fuerte'});
        y0 += rowHeight[j];
      });
      return {height, items, describe: i => info[i]};
    }
    // ---------- Meta (bullet): valor frente a meta y bandas cualitativas ----------
    bullet(svg, width) {
      const {data, heads, columns} = this.model, narrow = width < 480;
      const summary = r => this.fmt(r.values[0], 0) + ' / ' + this.fmt(r.values[1], 1);
      const valueWidth = narrow ? 0 : Math.ceil(Math.max(...data.map(r => G.textWidth(summary(r), this.font)))) + 16;
      const labelWidth = narrow ? width : Math.min(Math.round(width * .3), Math.ceil(Math.max(...data.map(r => G.textWidth(r.label, this.font)))) + 16);
      const left = narrow ? 4 : labelWidth, right = width - valueWidth, top = 30, bar = 22;
      const labels = data.map(r => G.wrap(r.label + (narrow ? ' · ' + summary(r) : ''), (narrow ? width : labelWidth) - 12, this.font, 2));
      const rowHeight = labels.map(l => narrow ? l.length * 15 + bar + 18 : Math.max(bar + 18, l.length * 15 + 10));
      const height = top + rowHeight.reduce((a, b) => a + b, 0) + 34;
      const all = data.flatMap(r => r.values);
      const x = this.xNumeric(svg, [Math.min(0, ...all), Math.max(0, ...all)], {left, right, top: top - 8, bottom: height - 30, spec: columns[0].spec});
      this.text(0, 14, G.fit(this.unit(), width, this.font, 1), {class: 'grafica-unidad'});
      const items = [], info = [];
      let y0 = top;
      data.forEach((r, j) => {
        const t = this.text(narrow ? 4 : 0, y0 + 12, '', {class: 'mg-texto-fuerte' + (narrow ? ' mg-halo' : '')});
        labels[j].forEach((line, k) => t.append(G.svg('tspan', {x: narrow ? 4 : 0, dy: k ? 15 : 0}, line)));
        const y = narrow ? y0 + labels[j].length * 15 + 2 : y0;
        const [value, goal, ...bands] = r.values;
        let from = 0;
        bands.forEach((b, k) => { svg.append(G.svg('rect', {x: x(from), y, width: Math.max(0, x(b) - x(from)), height: bar, class: 'mg-bullet-banda mg-b' + k})); from = b; });
        const g = G.svg('g', {'data-value': value});
        g.append(G.svg('rect', {x: Math.min(x(0), x(value)), y: y + bar * .3, width: Math.max(.5, Math.abs(x(value) - x(0))), height: bar * .4, class: 'grafica-barra serie-0'}));
        g.append(G.svg('line', {x1: x(goal), x2: x(goal), y1: y + 2, y2: y + bar - 2, class: 'mg-bullet-meta'}));
        svg.append(g); items.push(g);
        if (!narrow) this.text(width, y + 15, summary(r), {'text-anchor': 'end', class: 'mg-texto-fuerte'});
        const ratio = goal === 0 ? 'no definido (meta 0)' : G.format(value / goal, 'pct0', {lang: this.lang});
        info.push([r.label, heads[1] + ': ' + this.fmtUnit(value, 0), heads[2] + ': ' + this.fmtUnit(goal, 1) + ' · ' + ratio + ' de la meta', ...bands.map((b, k) => heads[k + 3] + ': ' + this.fmtUnit(b, k + 2))]);
        y0 += rowHeight[j];
      });
      return {height, items, describe: i => info[i]};
    }
    // ---------- Mapa de calor con ejes ----------
    heatmap(svg, width) {
      const {data, heads, columns, heat} = this.model, cols = heads.length - 1;
      const natural = Math.min(Math.round(width * .3), Math.ceil(Math.max(...data.map(r => G.textWidth(r.label, this.font)))) + 12);
      const rowLabel = natural + cols * 8 + 4 <= width ? natural : Math.max(Math.min(40, natural), width - cols * 8 - 4);
      const cell = Math.max(8, Math.min(64, (width - rowLabel - 4) / cols)), cellH = Math.max(14, Math.min(40, cell * .75));
      const top = 34, height = top + cellH * data.length + 8, full = Math.max(width, Math.ceil(rowLabel + cols * cell + 4));
      this.scrollable(svg, full > width, full);
      const x = i => rowLabel + i * cell, y = j => top + j * cellH;
      const idx = heads.slice(1).map((_, i) => i);
      const shown = G.spacedTicks(idx, i => x(i) + cell / 2, i => G.fit(heads[i + 1], 80, this.font, 2) || heads[i + 1].slice(0, 2), this.font, 6, full);
      const span = shown.length > 1 ? (shown[1] - shown[0]) * cell : cell;
      shown.forEach(i => svg.append(G.edgeText(svg, x(i) + cell / 2, top - 8, G.fit(heads[i + 1], span - 4, this.font, 1) || heads[i + 1].slice(0, 1), {}, this.font)));
      // Filas bajas: un rótulo cada k filas para que no se pisen; el tip y la tabla nombran todas.
      const every = Math.ceil(16 / cellH);
      const hatch = G.uid('mg-aus'), defs = G.svg('defs'), pattern = G.svg('pattern', {id: hatch, patternUnits: 'userSpaceOnUse', width: 6, height: 6});
      pattern.append(G.svg('rect', {width: 6, height: 6, style: 'fill:var(--calor-ausente)'}), G.svg('path', {d: 'M-1 1l2-2M0 6l6-6M5 7l2-2', style: 'stroke:var(--grafica-tinta);stroke-width:.8;stroke-opacity:.6'}));
      defs.append(pattern); svg.append(defs);
      const items = [], info = [];
      data.forEach((r, j) => {
        if (j % every === 0) this.text(rowLabel - 8, y(j) + cellH / 2, G.fit(r.label, rowLabel - 10, this.font, 1), {'text-anchor': 'end', 'dominant-baseline': 'middle', class: 'mg-texto-fuerte'});
        r.values.forEach((v, i) => {
          const g = G.svg('g', {'data-value': v ?? '', 'data-fila': j, 'data-columna': i});
          g.append(G.svg('rect', {x: x(i), y: y(j), width: cell, height: cellH, class: 'mg-calor-celda', style: 'fill:' + (v === null ? 'url(#' + hatch + ')' : heat.fill(heat.level(v)))}));
          const label = v === null ? '—' : this.fmt(v, i);
          if (cell - 6 >= G.textWidth(label, this.font) && cellH >= 16) g.append(G.svg('text', {x: x(i) + cell / 2, y: y(j) + cellH / 2, 'text-anchor': 'middle', 'dominant-baseline': 'middle', class: 'ev-calor-texto'}, label));
          svg.append(g); items.push(g);
          info.push([r.label + ' · ' + heads[i + 1], this.fmtUnit(v, i) + (v === null ? ' (≠ 0)' : ''), v === null ? '' : heat.constant ? 'Sin variación: todas las celdas valen lo mismo' : 'Nivel ' + (heat.level(v) + 1) + ' de ' + heat.levels]);
        });
      });
      return {height, width: full, items, describe: i => info[i].filter(Boolean), columns: cols};
    }
    // Mínimo legible que no cabe: el SVG conserva su ancho y la caja se desplaza, declarada y etiquetada.
    scrollable(svg, on, full) {
      svg.classList.toggle('mg-desplazable', on);
      if (on) {
        svg.setAttribute('width', full);
        this.region.tabIndex = 0; this.region.setAttribute('role', 'region'); this.region.setAttribute('aria-label', this.model.title + ', desplazable horizontalmente');
      } else ['tabindex', 'role', 'aria-label'].forEach(a => this.region.removeAttribute(a));
    }
    heatLegend() {
      const {heat, columns} = this.model, f = v => G.format(v, columns[0].spec, {lang: this.lang});
      const legend = element('ul', 'calor-leyenda');
      legend.setAttribute('aria-label', 'Escala de intensidad: ' + (this.figure.dataset.unidad || this.model.heads[0]) + (heat.quantile ? ' · cortes por cuantiles de los datos' : heat.diverging ? ' · divergente desde ' + f(+this.figure.dataset.centro) : ''));
      for (let i = 0; i < heat.levels; i++) {
        const lo = heat.limits[i], hi = heat.limits[i + 1];
        const li = element('li', '', heat.constant ? `Todas las celdas: ${f(lo)} · sin variación` : lo === hi ? f(lo) : `${f(lo)} ${i === heat.levels - 1 ? 'a' : 'a menos de'} ${f(hi)}`);
        const swatch = element('span'); swatch.style.background = heat.fill(i); swatch.className = 'mg-calor-muestra'; swatch.setAttribute('aria-hidden', 'true');
        li.prepend(swatch); legend.append(li);
      }
      const missing = element('li', '', 'Sin dato ≠ 0'), swatch = element('span', 'mg-calor-muestra mg-calor-ausente-muestra');
      swatch.setAttribute('aria-hidden', 'true'); missing.prepend(swatch); legend.append(missing);
      this.add(legend);
    }
    comparison() {
      const {data, heads, columns} = this.model;
      const dl = element('dl', 'grafica-variacion');
      const now = data.at(-1), before = data.at(-2);
      heads.slice(1).forEach((h, i) => {
        const row = element('div');
        row.append(element('dt', '', h + ' · ' + now.label + (before ? ' frente a ' + before.label : '')), element('dd', '', before ? delta(now.values[i], before.values[i], columns[i].spec, this.lang) : 'Sin período anterior'));
        dl.append(row);
      });
      this.add(dl);
    }
    destroy() {
      this.watch?.disconnect();
      this.marks?.destroy();
      this.parts.forEach(e => e.remove());
      this.original.forEach(([cell, text, level]) => {
        if (text !== null) cell.textContent = text;
        if (level === null) delete cell.dataset.nivel; else if (level !== undefined) cell.setAttribute('data-nivel', level);
      });
      if (this.tableClass !== undefined) { if (this.tableClass === null) this.model.table.removeAttribute('class'); else this.model.table.setAttribute('class', this.tableClass); }
      this.figure.classList.remove('nota-grafica');
      if (this.details) this.details.open = this.wasOpen;
      instances.delete(this.figure);
    }
  }
  function init(root = document) {
    const figures = [...(root.matches?.('[data-grafica]') ? [root] : []), ...root.querySelectorAll('[data-grafica]')];
    return figures.map(f => {
      if (instances.has(f)) return instances.get(f);
      try { const chart = new NotaGrafica(f); f.querySelector('[data-error-grafica]')?.remove(); return chart; }
      catch (error) {
        let message = f.querySelector('[data-error-grafica]');
        if (!message) { message = element('p', 'grafica-error'); message.dataset.errorGrafica = ''; f.prepend(message); }
        message.textContent = 'No se pudo dibujar: ' + error.message + ' Los datos siguen disponibles.';
        const details = f.querySelector('details'); if (details) details.open = true; return null;
      }
    });
  }
  window.NotaGraficas = {init, get: el => instances.get(el), scale, domain, delta, format: v => G ? G.format(v, 'auto', {lang: G.lang(document.documentElement)}) : String(v)};
  init();
})();
