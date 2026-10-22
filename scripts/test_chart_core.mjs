// Pruebas de unidad del núcleo de gráficas: node --test scripts/test_chart_core.mjs
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const source = readFileSync(new URL('../packages/core/components/chart-core.js', import.meta.url), 'utf8');
const context = {Intl, Math, Number, Object, Array, Set, Map, JSON, TypeError, Date, String, RegExp, performance, console};
context.window = context;
context.document = {documentElement: {lang: 'es'}, createElement: () => ({getContext: () => null})};
vm.createContext(context);
vm.runInContext(source, context);
const G = context.MargenGraficas;
const es = {lang: 'es-CO'}, en = {lang: 'en-US'};
const nb = s => s.replace(/[  ]/g, ' ');
const plain = v => JSON.parse(JSON.stringify(v));

test('nice: pasos 1-2-5, extremos redondos que contienen los datos', () => {
  const cases = [[0, 13.5], [-7, 42], [0.001, 0.0087], [3, 3], [0, 0], [-1e12, 1e12], [17, 1e12], [-5, -1], [0.1, 0.3]];
  for (const [min, max] of cases) {
    const r = G.nice(min, max);
    const mantissa = r.step / 10 ** Math.floor(Math.log10(r.step) + 1e-12);
    assert.ok([1, 2, 5, 10].some(m => Math.abs(mantissa - m) < 1e-9), `paso ${r.step} no es 1-2-5`);
    assert.ok(r.min <= Math.min(min, max) && r.max >= Math.max(min, max), `dominio ${r.min}..${r.max} no contiene ${min}..${max}`);
    assert.ok(r.ticks.length >= 2 && r.ticks.length <= 12, `ticks ${r.ticks.length}`);
    for (const t of r.ticks) assert.ok(Number.isFinite(t) && !Object.is(t, -0));
    assert.deepEqual([...r.ticks].sort((a, b) => a - b), [...r.ticks]);
  }
  assert.deepEqual([...G.nice(0, 13.5).ticks], [0, 2, 4, 6, 8, 10, 12, 14]);
  assert.deepEqual([...G.nice(0.1, 0.3).ticks], [0.1, 0.15, 0.2, 0.25, 0.3]);
  assert.deepEqual([...G.nice(-7, 42).ticks], [-10, 0, 10, 20, 30, 40, 50]);
  assert.equal(G.nice(0, 0).min, -1);
  assert.throws(() => G.nice(0, Infinity));
  assert.throws(() => G.nice(-Number.MAX_VALUE, Number.MAX_VALUE));
  assert.ok(G.niceZero([5, 9]).ticks.includes(0));
  assert.ok(G.niceZero([-3, -9]).ticks.includes(0));
});

test('linear: proporciones exactas y rechazo de dominios vacíos', () => {
  const s = G.linear([0, 60], [100, 700]);
  assert.equal(s(15) - s(0), (s(60) - s(0)) / 4);
  assert.throws(() => G.linear([2, 2], [0, 1]));
});

test('format: cero, negativos, 1e12, null y sin dato', () => {
  assert.equal(G.format(0, 'auto', es), '0');
  assert.equal(G.format(-1234.5, 'auto', es), '-1234,5'.replace('1234', '1.234'));
  assert.equal(G.format(1e12, 'auto', es), '1.000.000.000.000');
  assert.equal(G.format(1e12, 'num0k', es).replace(/\s/g, ' ').length < 10, true);
  assert.equal(G.format(null, 'auto', es), 'Sin dato');
  assert.equal(G.format(null, 'auto', en), 'No data');
  assert.equal(G.format(undefined, 'num1', es), 'Sin dato');
  assert.throws(() => G.format(NaN, 'auto', es));
  assert.equal(G.format(0.00001234, 'auto', es), '1,234E-5');
  assert.equal(G.format(1234.5, 'num1', en), '1,234.5');
  assert.equal(G.format(12, 'auto', {...es, unit: 'h'}), '12 h');
});

test('format: porcentajes, monedas y fechas por idioma', () => {
  assert.equal(nb(G.format(0.3333, 'pct1', es)).replace(' ', ''), '33,3%');
  assert.equal(G.format(0.3333, 'pct1', en), '33.3%');
  assert.equal(G.format(33.3, 'pts1', es), G.format(0.333, 'pct1', es));
  assert.equal(nb(G.format(1500000, 'cop0', es)), '$ 1.500.000');
  assert.equal(G.format(1234.5, 'usd2', en), '$1,234.50');
  assert.match(nb(G.format(2500000, 'cop1m', es)), /^\$ ?2,5 ?M/);
  assert.equal(G.format(-0.05, 'pct0', en), '-5%');
  const t = Date.UTC(2026, 9, 22);
  assert.equal(G.format(t, 'iso', es), '2026-10-22');
  assert.match(G.format(t, 'month', es), /oct/);
  assert.match(G.format(t, 'month', en), /Oct 2026/);
  assert.equal(G.format(t, 'year', es), '2026');
});

test('format: duraciones largas, cortas y mínimas', () => {
  const s = 3 * 86400 + 10 * 3600 + 36 * 60;
  assert.equal(G.format(s, 'duration', en), '3 days, 10 hours, 36 minutes');
  assert.equal(nb(G.format(s, 'duration:short', en)), '3d 10h 36m');
  assert.equal(G.format(s, 'duration:min', en).replace(/\s/g, ''), '3d');
  assert.equal(G.format(90, 'duration_min', es), '1 hora, 30 minutos');
  assert.equal(G.format(0, 'duration', en), '0 seconds');
});

test('tickFormat: decimales según paso, compacto y rótulos únicos', () => {
  const a = G.nice(0, 1).ticks, fa = G.tickFormat(a, 'auto', es);
  assert.deepEqual(plain(a.map(fa)), ['0,0', '0,2', '0,4', '0,6', '0,8', '1,0']);
  const b = G.nice(0, 1e12).ticks, fb = G.tickFormat(b, 'auto', en);
  const labels = b.map(fb);
  assert.equal(new Set(labels).size, labels.length);
  assert.ok(labels.every(l => l.length <= 6), labels.join('|'));
  const c = G.nice(0, 0.3).ticks, fc = G.tickFormat(c, 'pct0', en);
  assert.deepEqual(plain(c.map(fc)), ['0%', '5%', '10%', '15%', '20%', '25%', '30%']);
  const d = G.nice(-200000, 1500000).ticks, fd = G.tickFormat(d, 'cop0', es);
  assert.equal(new Set(d.map(fd)).size, d.length);
  const e = G.nice(9.98, 10.02).ticks, fe = G.tickFormat(e, 'auto', en);
  assert.equal(new Set(e.map(fe)).size, e.length);
});

test('squarify: áreas exactas, sin solapes, cubre el rectángulo y mejora la relación de aspecto', () => {
  const values = [6, 6, 4, 3, 2, 2, 1];
  const tiles = G.squarify(values.map((value, i) => ({value, i})), {w: 600, h: 400});
  const total = values.reduce((a, b) => a + b, 0);
  for (const t of tiles) assert.ok(Math.abs(t.w * t.h - t.value / total * 240000) < 1e-6);
  const area = tiles.reduce((a, t) => a + t.w * t.h, 0);
  assert.ok(Math.abs(area - 240000) < 1e-6);
  for (const a of tiles) for (const b of tiles) if (a !== b) {
    const ox = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x), oy = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
    assert.ok(ox <= 1e-6 || oy <= 1e-6, 'solape');
  }
  const ratio = tiles.reduce((a, t) => a + Math.max(t.w / t.h, t.h / t.w), 0) / tiles.length;
  assert.ok(ratio < 3, 'relación media ' + ratio);
});

test('squarify: 26 categorías, cola extrema y ceros', () => {
  const values = Array.from({length: 26}, (_, i) => i < 3 ? 1e6 / (i + 1) : i % 5 === 0 ? 0 : 7 + i);
  const tiles = G.squarify(values.map((value, i) => ({value, i})), {w: 1008, h: 380});
  assert.equal(tiles.length, values.filter(v => v > 0).length, 'los ceros no se pintan');
  const total = values.reduce((a, b) => a + b, 0);
  const area = tiles.reduce((a, t) => a + t.w * t.h, 0);
  assert.ok(Math.abs(area - 1008 * 380) < 1e-3);
  for (const t of tiles) {
    assert.ok(t.x >= -1e-9 && t.y >= -1e-9 && t.x + t.w <= 1008 + 1e-6 && t.y + t.h <= 380 + 1e-6);
    assert.ok(Math.abs(t.w * t.h / (1008 * 380) - t.value / total) < 1e-9);
  }
  assert.deepEqual([...G.squarify([{value: 0}], {w: 10, h: 10})], []);
});

test('paleta y formas: ocho slots distintos y estables', () => {
  const colors = Array.from({length: 8}, (_, i) => G.color(i));
  assert.equal(new Set(colors).size, 8);
  assert.equal(G.color(8), G.color(0));
  const shapes = Array.from({length: 8}, (_, i) => G.shape(i, 10, 10, 4));
  assert.equal(new Set(shapes).size, 8);
  assert.ok(shapes.every(d => !/NaN|undefined/.test(d)));
  assert.equal(new Set(Array.from({length: 8}, (_, i) => G.dash(i))).size, 8);
});

test('fit y wrap: nunca superan el ancho y abrevian con elipsis', () => {
  const font = '12px monospace';
  assert.equal(G.fit('Arc', 200, font), 'Arc');
  const short = G.fit('Spotify Premium', 40, font);
  assert.ok(short.endsWith('…') && G.textWidth(short, font) <= 40);
  assert.equal(G.fit('Spotify', 8, font), '');
  const lines = G.wrap('Ingresos operacionales netos del trimestre', 90, font, 2);
  assert.equal(lines.length, 2);
  for (const l of lines) assert.ok(G.textWidth(l, font) <= 90, l);
});
