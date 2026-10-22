/* Margen · código. Fuente de packages/core/components/code.js (scripts/build_syntax.py la une con Prism).
   Prism solo tokeniza: el DOM se construye con nodos de texto, nunca con HTML del tokenizador.
   El texto de cada bloque (textContent) es la fuente; mark, .subra y otros envoltorios del autor se
   conservan como capas sobre los tokens. Los bloques ocultos se colorean al mostrarse. */
(function (Prism, STYLE) {
 'use strict';
 const VERSION = '2';
 if (window.NotaCodigo && window.NotaCodigo.version === VERSION) { window.NotaCodigo.init(); return; }
 const done = new WeakSet(), langs = new WeakMap(), owner = new WeakMap(), pending = new Set();
 const MAX_COLOR = 150000, MAX_LINES = 20000, SLICE_MS = 8, INIT_MS = 24, SMALL = 12000;
 const OVERLAY = 'mark,.subra,.tenue,a,abbr,b,strong,em,i,u,s,del,ins';
 const ALIAS = { js: 'javascript', mjs: 'javascript', cjs: 'javascript', ts: 'typescript', mts: 'typescript', py: 'python', python3: 'python',
  sh: 'bash', shell: 'bash', zsh: 'bash', console: 'bash', 'c++': 'cpp', cc: 'cpp', hpp: 'cpp', h: 'c', html: 'markup', xml: 'markup', svg: 'markup',
  htm: 'markup', yml: 'yaml', md: 'markdown', rs: 'rust', golang: 'go', pl: 'perl', pm: 'perl', patch: 'diff', jsonc: 'json', json5: 'json',
  text: 'salida', texto: 'salida', txt: 'salida', plaintext: 'salida', plain: 'salida', output: 'salida' };
 const LABEL = { javascript: 'JavaScript', typescript: 'TypeScript', jsx: 'JSX', tsx: 'TSX', python: 'Python', sql: 'SQL', bash: 'Shell', css: 'CSS',
  markup: 'HTML', json: 'JSON', cpp: 'C++', c: 'C', markdown: 'Markdown', yaml: 'YAML', diff: 'Diff', rust: 'Rust', go: 'Go', perl: 'Perl', salida: 'Texto' };
 const ORIGINAL_LABEL = { xml: 'XML', svg: 'SVG', shell: 'Shell', bash: 'Bash', sh: 'Shell' };
 const EXTENSION = [[/\.py\b|python/i, 'python'], [/\.tsx\b/i, 'tsx'], [/\.jsx\b/i, 'jsx'], [/\.ts\b|typescript/i, 'typescript'], [/\.m?jsx?\b|javascript/i, 'javascript'],
  [/\.s?css\b/i, 'css'], [/\.sql\b/i, 'sql'], [/\.(?:sh|bash|zsh)\b|shell|bash/i, 'bash'], [/\.jsonc?\b/i, 'json'], [/\.html?\b|\.svg\b|\.xml\b/i, 'markup'],
  [/\.ya?ml\b/i, 'yaml'], [/\.md\b/i, 'markdown'], [/\.rs\b/i, 'rust'], [/\.go\b/i, 'go'], [/\.(?:cpp|cc|hpp)\b/i, 'cpp'], [/\.[ch]\b/i, 'c'],
  [/\.p[lm]\b/i, 'perl'], [/\.(?:diff|patch)\b/i, 'diff']];
 // Salida de terminal: solo estados reconocibles y cifras; el resto queda como texto.
 Prism.languages.salida = { alerta: /\b(?:error|errors|failed|failure|fatal|warning|warn|fail)\b/i, ok: /\b(?:ok|success|passed|ready|done)\b/i,
  number: /\b\d+(?:[.,]\d+)*(?:\s?(?:ms|s|%|kb|mb|gb))?\b/i };
 // Tipo de Prism → clase estable. Las clases antiguas (kw, str, com, codigo-*) siguen siendo válidas
 // para temas y copias históricas; las nuevas agregan las categorías que faltaban.
 const KIND = { comment: 'com', prolog: 'com', doctype: 'com', cdata: 'com', shebang: 'com',
  string: 'str', char: 'str', 'attr-value': 'str', 'template-string': 'str', url: 'str', 'string-interpolation': 'str', 'triple-quoted-string': 'str', 'heredoc-string': 'str',
  keyword: 'kw', important: 'kw', atrule: 'kw', rule: 'kw', 'control-flow': 'kw', module: 'kw', directive: 'kw', 'macro': 'kw', ok: 'str',
  number: 'codigo-numero', boolean: 'codigo-numero', constant: 'codigo-numero', symbol: 'codigo-numero', unit: 'codigo-numero', hexcode: 'codigo-numero', color: 'codigo-numero', entity: 'codigo-numero',
  function: 'codigo-funcion', 'function-variable': 'codigo-funcion', 'class-name': 'codigo-funcion', builtin: 'codigo-funcion', method: 'codigo-funcion', decorator: 'codigo-funcion', annotation: 'codigo-funcion', 'maybe-class-name': 'codigo-funcion',
  property: 'codigo-atributo', 'attr-name': 'codigo-atributo', key: 'codigo-atributo', 'literal-property': 'codigo-atributo', parameter: 'codigo-atributo',
  tag: 'codigo-etiqueta', selector: 'codigo-etiqueta', title: 'codigo-etiqueta', 'table': 'codigo-etiqueta',
  punctuation: 'codigo-puntuacion', operator: 'codigo-puntuacion', 'interpolation-punctuation': 'kw', 'template-punctuation': 'str',
  regex: 'codigo-regex', escape: 'codigo-escape', variable: 'codigo-variable', environment: 'codigo-variable', 'assign-left': 'codigo-variable',
  inserted: 'codigo-insertado', deleted: 'codigo-eliminado', coord: 'com', alerta: 'codigo-alerta',
  // '' vuelve a texto normal (el código dentro de ${…} no es cadena); null hereda del padre.
  interpolation: '', 'plain-text': '', script: '', bold: null, italic: null };
 const ESCAPING = new Set(['javascript', 'typescript', 'jsx', 'tsx', 'json', 'python', 'c', 'cpp', 'rust', 'go', 'perl', 'bash', 'css']);
 const ESCAPE = /\\(?:x[0-9a-fA-F]{2}|u\{[0-9a-fA-F]+\}|u[0-9a-fA-F]{4}|[0-7]{1,3}|[\s\S])/g;

 function resolve(el, text) {
  const declared = (el.dataset.lenguaje || el.dataset.language || '').trim();
  if (declared) {
   const key = declared.toLowerCase(), id = ALIAS[key] || key;
   return { id: Prism.languages[id] ? id : 'plain', label: ORIGINAL_LABEL[key] || LABEL[id] || declared };
  }
  if (el.closest('.terminal')) return { id: 'salida', label: LABEL.salida };
  if (el.closest('.receta-copia')) return { id: 'markup', label: LABEL.markup };
  const name = el.dataset.nombreArchivo || el.closest('.codigo')?.querySelector('.cab')?.textContent || '';
  for (const [re, id] of EXTENSION) if (re.test(name)) return { id, label: LABEL[id] };
  if (text.trimStart().startsWith('<')) return { id: 'markup', label: LABEL.markup };
  try { JSON.parse(text); return { id: 'json', label: LABEL.json }; } catch { }
  return { id: 'salida', label: LABEL.salida };
 }

 // Lista plana de [inicio, fin, clase]; el token más interno con clase conocida decide el color.
 function tokens(source, id) {
  const grammar = Prism.languages[id], out = [];
  if (!grammar || !source) return source ? [[0, source.length, '']] : out;
  const env = { code: source, grammar, language: id };
  Prism.hooks.run('before-tokenize', env);
  env.tokens = Prism.tokenize(env.code, env.grammar);
  Prism.hooks.run('after-tokenize', env);
  let at = 0;
  const escaping = ESCAPING.has(id);
  const kindOf = token => {
   if (KIND[token.type] !== undefined) return KIND[token.type];
   for (const alias of [].concat(token.alias || [])) if (KIND[alias] !== undefined) return KIND[alias];
   return null;
  };
  const walk = (stream, inherited) => {
   for (const token of [].concat(stream)) {
    if (typeof token === 'string') { push(token, inherited); continue; }
    const own = kindOf(token);
    walk(token.content, own === null ? inherited : own);
   }
  };
  const push = (text, kind) => {
   if (!text) return;
   if (kind === 'str' && escaping && text.includes('\\') && !(id === 'python' && /^[a-z]*r/i.test(text))) {
    let last = 0;
    for (const m of text.matchAll(ESCAPE)) { add(text.slice(last, m.index), kind); add(m[0], 'codigo-escape'); last = m.index + m[0].length; }
    add(text.slice(last), kind);
   } else add(text, kind);
  };
  const add = (text, kind) => {
   if (!text) return;
   const prev = out[out.length - 1];
   if (prev && prev[2] === (kind || '')) prev[1] += text.length; else out.push([at, at + text.length, kind || '']);
   at += text.length;
  };
  walk(env.tokens, '');
  // Un tokenizador nunca puede alterar el texto: si algo no cuadra, se muestra sin color.
  return at === source.length ? out : [[0, source.length, '']];
 }

 // Envoltorios del autor (mark, .subra…) como rangos sobre el texto original.
 function overlays(el) {
  const ranges = [], walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
  let offset = 0;
  while (walker.nextNode()) {
   const node = walker.currentNode, end = offset + node.data.length;
   // Toda la cadena de envoltorios, de fuera hacia dentro: <mark><a>…</a></mark> y <a><mark>…</mark></a>.
   const chain = [];
   for (let p = node.parentElement; p && p !== el; p = p.parentElement) if (p.matches(OVERLAY)) chain.unshift(p);
   if (chain.length && end > offset) {
    const last = ranges[ranges.length - 1];
    if (last && last[1] === offset && last[2].length === chain.length && last[2].every((w, i) => w === chain[i])) last[1] = end;
    else ranges.push([offset, end, chain]);
   }
   offset = end;
  }
  return ranges;
 }

 function selectedLines(el) {
  const selected = new Set();
  for (const part of (el.dataset.destacar || '').split(',')) {
   const m = part.trim().match(/^(\d+)(?:-(\d+))?$/);
   if (!m) continue;
   const from = Number(m[1]), to = Math.min(Number(m[2] || m[1]), MAX_LINES);
   for (let i = from; i <= to; i++) selected.add(i);
  }
  return selected;
 }

 // Construye por tramos para no bloquear al lector; el texto visible no cambia hasta el reemplazo final.
 function* build(el, source, pieces, layers, numbered) {
  const frag = document.createDocumentFragment(), selected = selectedLines(el);
  let number = 1, line = null, stack = [], li = 0, count = 0;
  const target = () => stack.length ? stack[stack.length - 1][1] : line || frag;
  const newLine = () => {
   if (!numbered) return;
   line = document.createElement('span');
   line.className = 'codigo-linea' + (selected.has(number) ? ' destacada' : '');
   line.dataset.numero = String(number++);
   frag.append(line);
  };
  // Reutiliza los envoltorios abiertos que coinciden y clona el resto, anidados en el mismo orden.
  const wrap = chain => {
   let keep = 0;
   while (keep < stack.length && keep < chain.length && stack[keep][0] === chain[keep]) keep++;
   stack.length = keep;
   for (let i = keep; i < chain.length; i++) {
    const clone = chain[i].cloneNode(false);
    clone.removeAttribute('id');
    target().append(clone);
    stack.push([chain[i], clone]);
   }
  };
  const text = (start, end, kind, layer) => {
   wrap(layer >= 0 ? layers[layer][2] : []);
   const value = source.slice(start, end);
   if (!kind) { target().append(value); return; }
   const span = document.createElement('span');
   span.className = kind;
   span.textContent = value;
   target().append(span);
  };
  newLine();
  for (const [start, end, kind] of pieces) {
   let at = start;
   while (at < end) {
    while (li < layers.length && layers[li][1] <= at) li++;
    const inLayer = li < layers.length && layers[li][0] <= at ? li : -1;
    const limit = Math.min(end, inLayer >= 0 ? layers[inLayer][1] : li < layers.length ? layers[li][0] : end);
    const nl = source.indexOf('\n', at);
    const stop = nl >= 0 && nl < limit ? nl : limit;
    if (stop > at) text(at, stop, kind, inLayer);
    at = stop;
    if (nl === at && at < end) {
     // Cada línea cierra sus envoltorios; un salto final termina la última línea sin abrir otra vacía.
     stack = [];
     frag.append('\n');
     if (at + 1 < source.length) newLine();
     // Fila sin número: sin una caja tras el salto, Chromium lo omite al copiar una selección.
     else if (numbered) { const end = document.createElement('span'); end.className = 'codigo-linea codigo-linea-final'; frag.append(end); }
     at++;
     if (++count % 200 === 0) yield;
    }
   }
  }
  if (numbered) el.style.setProperty('--codigo-cifras', String(String(number - 1).length));
  return frag;
 }

 function header(el, lang) {
  const block = el.closest('.codigo');
  if (!block || el.closest('[data-ritmo="propio"],[data-presentation]')) return;
  block.classList.add('codigo-editorial'); block.classList.remove('codigo-sin-titulo');
  let head = block.querySelector('.cab');
  if (!head) { head = document.createElement('div'); head.className = 'cab'; block.prepend(head); }
  if (!head.querySelector('span:not(.copia-estado)')) {
   const name = document.createElement('span');
   name.className = 'codigo-lenguaje';
   name.textContent = el.dataset.nombreArchivo || lang.label;
   head.prepend(name);
  }
  if (!head.querySelector('[data-copiar]') && !head.querySelector('[data-codigo-copiar]')) {
   const button = document.createElement('button');
   button.type = 'button'; button.className = 'nota-icono'; button.dataset.codigoCopiar = '';
   button.setAttribute('aria-label', 'Copiar código'); button.title = 'Copiar código';
   button.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V3H4v13h4"/></svg>';
   const status = document.createElement('span');
   status.className = 'copia-estado'; status.setAttribute('role', 'status');
   head.append(button, status);
   button.addEventListener('click', async () => {
    try {
     if (!navigator.clipboard?.writeText) throw new Error('clipboard unavailable');
     await navigator.clipboard.writeText(el.textContent);
     status.textContent = 'Código copiado.';
    } catch {
     const range = document.createRange(); range.selectNodeContents(el);
     const selection = getSelection(); selection.removeAllRanges(); selection.addRange(range);
     status.textContent = 'Código seleccionado. Usa ⌘C o Ctrl+C para copiar.';
    }
   });
  }
  const pre = el.closest('pre');
  if (pre && !pre.hasAttribute('tabindex')) { pre.tabIndex = 0; pre.setAttribute('aria-label', 'Código: ' + (head.querySelector('span')?.textContent || lang.label)); }
  if (!el.hasAttribute('data-sin-lineas')) el.setAttribute('data-lineas', '');
 }

 // Preparación barata y síncrona para lo visible: clases, cabecera y lenguaje, sin tokenizar.
 function prepare(el) {
  if (langs.has(el)) return langs.get(el);
  const lang = resolve(el, el.textContent);
  langs.set(el, lang);
  el.dataset.coloreado = lang.id === 'plain' ? 'texto' : lang.id;
  header(el, lang);
  return lang;
 }

 function* color(el) {
  const lang = prepare(el), source = el.textContent;
  const numbered = el.hasAttribute('data-lineas');
  if (!numbered && lang.id === 'salida' && el.querySelector('*')) { el.dataset.codigoEstado = 'propio'; return; }
  let lines = 1;
  for (let i = source.indexOf('\n'); i >= 0 && lines <= MAX_LINES; i = source.indexOf('\n', i + 1)) lines++;
  if (lines > MAX_LINES) { el.dataset.codigoEstado = 'sin-lineas'; note(el, 'Bloque de más de ' + MAX_LINES.toLocaleString('es') + ' líneas: se muestra sin color ni numeración.'); return; }
  const plain = source.length > MAX_COLOR;
  const pieces = plain || lang.id === 'plain' ? (source ? [[0, source.length, '']] : []) : tokens(source, lang.id);
  yield;
  const frag = yield* build(el, source, pieces, overlays(el), numbered);
  if (el.textContent !== source) return; // Cambió mientras se preparaba; se vuelve a intentar al reiniciar.
  el.replaceChildren(frag);
  el.dataset.codigoEstado = plain ? 'sin-color' : 'listo';
  if (plain) note(el, 'Bloque muy extenso: se muestra sin color para no bloquear la lectura. La copia es exacta.');
  overflow(el.closest('pre'));
 }

 function note(el, message) {
  const head = el.closest('.codigo')?.querySelector('.cab');
  if (!head || head.querySelector('.codigo-aviso')) return;
  const p = document.createElement('span');
  p.className = 'codigo-aviso'; p.textContent = message;
  head.append(p);
 }

 // Atenúa los bordes según el desplazamiento lateral real, sin un oyente por bloque.
 function overflow(pre) {
  if (!pre) return;
  const max = pre.scrollWidth - pre.clientWidth;
  const state = max <= 1 ? '' : [pre.scrollLeft > 1 ? 'inicio' : '', pre.scrollLeft < max - 1 ? 'fin' : ''].filter(Boolean).join(' ');
  if (state) pre.dataset.desborde = state; else pre.removeAttribute('data-desborde');
 }

 // Un bloque está vivo si ninguna página, pestaña o detalle cerrado lo oculta.
 function active(el) {
  if (el.closest('[hidden],template')) return false;
  for (let d = el.closest('details'); d; d = d.parentElement?.closest('details')) {
   if (!d.open && !(d.querySelector(':scope > summary')?.contains(el))) return false;
  }
  return true;
 }

 const queue = [];
 let running = null, timer = 0;
 function pump() {
  timer = 0;
  const started = performance.now();
  while (queue.length || running) {
   if (!running) {
    const el = queue.shift();
    if (done.has(el) || !el.isConnected) continue;
    done.add(el);
    running = color(el);
   }
   try { if (running.next().done) running = null; } catch (error) { running = null; console.error(error); }
   if (performance.now() - started > SLICE_MS) break;
  }
  if (queue.length || running) schedule();
 }
 function schedule() { if (!timer) timer = setTimeout(pump, 0); }
 function finish(el) { const job = color(el); try { while (!job.next().done); } catch (error) { console.error(error); } }

 const near = 'IntersectionObserver' in window ? new IntersectionObserver(entries => {
  for (const entry of entries) {
   if (!entry.isIntersecting) continue;
   near.unobserve(entry.target);
   const el = owner.get(entry.target);
   if (el && !done.has(el) && active(el)) queue.push(el);
  }
  schedule();
 }, { rootMargin: '600px 0px' }) : null;

 function wake(el) {
  pending.delete(el);
  prepare(el);
  if (!near) { queue.push(el); schedule(); return; }
  const box = el.closest('pre') || el;
  owner.set(box, el);
  near.observe(box);
 }
 function revisit() {
  if (!pending.size) return;
  for (const el of [...pending]) if (!el.isConnected) pending.delete(el); else if (active(el)) wake(el);
 }
 let revisitPending = 0;
 function soon() { if (!revisitPending) revisitPending = requestAnimationFrame(() => { revisitPending = 0; revisit(); }); }

 function candidates(root) {
  const found = [...root.querySelectorAll('.codigo pre code,.terminal pre,[data-lenguaje]')];
  if (root.matches?.('.codigo pre code,.terminal pre,[data-lenguaje]')) found.unshift(root);
  return found;
 }

 // init(root) es idempotente. {inmediato:true} colorea ya, aunque esté oculto (pruebas, impresión).
 // Lo visible y pequeño se colorea durante init, dentro de un presupuesto; lo grande o lo que
 // excede el presupuesto espera a acercarse a la vista, y lo oculto a mostrarse.
 function init(root = document, options = {}) {
  const started = performance.now();
  for (const el of candidates(root)) {
   if (done.has(el)) continue;
   if (options.inmediato) { done.add(el); pending.delete(el); finish(el); continue; }
   if (!active(el)) { pending.add(el); continue; }
   if (performance.now() - started < INIT_MS && el.textContent.length < SMALL) { pending.delete(el); done.add(el); finish(el); } else wake(el);
  }
 }

 function style() {
  if (!STYLE || document.querySelector('style[data-margen-codigo="' + VERSION + '"]')) return;
  const s = document.createElement('style');
  s.dataset.margenCodigo = VERSION;
  s.textContent = STYLE;
  (document.body || document.head || document.documentElement).append(s);
 }

 style();
 new MutationObserver(records => {
  for (const r of records) if (r.type === 'attributes') { soon(); return; }
 }).observe(document.documentElement, { subtree: true, attributes: true, attributeFilter: ['hidden', 'open'] });
 document.addEventListener('toggle', soon, true);
 document.addEventListener('nota:pagina', soon);
 document.addEventListener('scroll', e => { if (e.target instanceof Element && e.target.matches('.codigo pre')) overflow(e.target); }, { capture: true, passive: true });
 let resized = 0;
 addEventListener('resize', () => { if (!resized) resized = requestAnimationFrame(() => { resized = 0; for (const code of document.querySelectorAll('.codigo pre > [data-codigo-estado]')) overflow(code.parentElement); }); }, { passive: true });
 // Print includes blocks still waiting for IntersectionObserver, not only hidden or queued ones.
 function printReady() {
  if (running) { try { while (!running.next().done); } catch (error) { console.error(error); } running = null; }
  queue.length = 0;
  init(document, { inmediato: true });
 }
 addEventListener('beforeprint', printReady);
 const printMedia = matchMedia('print');
 printMedia.addEventListener('change', event => { if (event.matches) printReady(); });
 if (printMedia.matches) printReady();

 window.NotaCodigo = { version: VERSION, init, lenguajes: Object.keys(LABEL).filter(id => Prism.languages[id]),
  tokens: (source, lang) => tokens(source, ALIAS[lang] || lang).map(([start, end, kind]) => [source.slice(start, end), kind]),
  // pendientes: coloreado en curso; esperando: bloques ocultos que se colorearán al mostrarse.
  activo: active, pendientes: () => queue.length + (running ? 1 : 0), esperando: () => pending.size };
 init();
})(MARGEN_PRISM, MARGEN_STYLE);
