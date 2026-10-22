import {afterEach, beforeAll, describe, expect, it, vi} from 'vitest';
import {readFileSync} from 'node:fs';

const source = readFileSync('packages/core/components/embeds.js', 'utf8');
const E = () => (window as any).MargenEmbeds;
const realParent = window.parent;

beforeAll(() => { window.eval(source); });
afterEach(() => {
  document.querySelectorAll('[data-embed]').forEach(el => E().destroy(el));
  document.body.innerHTML = '';
  Object.defineProperty(window, 'parent', {value: realParent, configurable: true});
  delete (window as any).BottifactReviewBridge;
  vi.useRealTimers();
});

const youtube = (extra = '') => `<figure class="embed embed-video embed-youtube" data-embed="youtube" data-embed-id="M7lc1UVf-VE" ${extra}>
  <div class="embed-lienzo" data-embed-stage></div>
  <figcaption><p class="embed-acciones"><button type="button" data-embed-load hidden>Cargar video</button>
  <a data-embed-source href="https://evil.example/phish">Abrir en YouTube</a></p><p class="embed-aviso" data-embed-notice hidden>Al cargarlo…</p><p class="embed-aviso" data-embed-status role="status"></p></figcaption></figure>`;

describe('validación', () => {
  it('acepta sólo proveedores e IDs con forma exacta', () => {
    const {normalize} = E();
    expect(normalize({provider: 'youtube', id: 'M7lc1UVf-VE'})).toEqual({provider: 'youtube', id: 'M7lc1UVf-VE'});
    for (const id of ['M7lc1UVf-V', 'M7lc1UVf-VEx', 'M7lc1UVf/VE', '../../../x', '', 42, null])
      expect(normalize({provider: 'youtube', id})).toBeNull();
    expect(normalize({provider: 'instagram', id: 'fA9uwTtkSN', kind: 'reel'})).toEqual({provider: 'instagram', id: 'fA9uwTtkSN', kind: 'reel'});
    expect(normalize({provider: 'instagram', id: 'fA9uwTtkSN', kind: 'stories'})).toBeNull();
    expect(normalize({provider: 'instagram', id: 'abcd', kind: 'p'})).toBeNull();
    expect(normalize({provider: 'instagram', id: 'a'.repeat(41), kind: 'p'})).toBeNull();
    expect(normalize({provider: 'x', user: 'margen_app', status: '1846'})).toEqual({provider: 'x', user: 'margen_app', status: '1846'});
    expect(normalize({provider: 'x', user: 'margen'})).toEqual({provider: 'x', user: 'margen'});
    for (const spec of [{provider: 'x', user: 'a'.repeat(16)}, {provider: 'x', user: 'a.b'}, {provider: 'x', user: 'a', status: '12a'}, {provider: 'vimeo', id: '1'}, {provider: 'constructor'}, null, 'youtube'])
      expect(normalize(spec)).toBeNull();
  });

  it('construye URLs de una tabla fija, sin ruta del documento', () => {
    const {sourceURL, playerURL} = E();
    expect(sourceURL({provider: 'youtube', id: 'M7lc1UVf-VE'})).toBe('https://www.youtube.com/watch?v=M7lc1UVf-VE');
    expect(sourceURL({provider: 'instagram', id: 'fA9uwTtkSN', kind: 'p'})).toBe('https://www.instagram.com/p/fA9uwTtkSN/');
    expect(sourceURL({provider: 'x', user: 'margen', status: '12'})).toBe('https://x.com/margen/status/12');
    expect(playerURL({provider: 'instagram', id: 'fA9uwTtkSN', kind: 'reel'})).toBe('https://www.instagram.com/reel/fA9uwTtkSN/embed/');
    const yt = new URL(playerURL({provider: 'youtube', id: 'M7lc1UVf-VE'}, 'https://artifacts.botto.is'));
    expect(yt.origin + yt.pathname).toBe('https://www.youtube-nocookie.com/embed/M7lc1UVf-VE');
    expect(Object.fromEntries(yt.searchParams)).toEqual({autoplay: '1', mute: '1', playsinline: '1', rel: '0', enablejsapi: '1', origin: 'https://artifacts.botto.is'});
    // Un origen con ruta (p. ej. el del artefacto) nunca viaja al proveedor.
    expect(playerURL({provider: 'youtube', id: 'M7lc1UVf-VE'}, 'https://artifacts.botto.is/a/abc').includes('/a/abc')).toBe(false);
    expect(playerURL({provider: 'x', user: 'margen'})).toBeNull();
    expect(playerURL({provider: 'youtube', id: 'bad'})).toBeNull();
  });

  it('lee señales del reproductor como texto JSON acotado', () => {
    const {signal} = E();
    expect(signal('youtube', '{"event":"onError","info":153}')).toEqual({type: 'error', code: 153});
    expect(signal('youtube', '{"event":"infoDelivery","info":{"playerState":1}}')).toEqual({type: 'playing'});
    expect(signal('youtube', '{"event":"onReady"}')).toEqual({type: 'alive'});
    expect(signal('instagram', '{"type":"MEASURE","details":{"height":812.4}}')).toEqual({type: 'measure', height: 812});
    expect(signal('instagram', '{"type":"MEASURE","details":{"height":99999}}')).toEqual({type: 'alive'});
    for (const data of [{event: 'onReady'}, 'not json', 'x'.repeat(20001), '{"event":"other"}', 'null'])
      expect(signal('youtube', data)).toBeNull();
  });
});

describe('tarjetas', () => {
  it('regenera el enlace desde el ID y no conecta antes del clic', () => {
    document.body.innerHTML = youtube() + '<figure class="embed" data-embed="x" data-embed-user="margen" data-embed-status="77"><img src="https://pbs.twimg.com/a.jpg" alt=""><img src="data:image/png;base64,AAAA" alt="ok"><figcaption><a data-embed-source href="javascript:alert(1)">Ver en X</a></figcaption></figure>';
    E().init();
    const links = [...document.querySelectorAll<HTMLAnchorElement>('a[data-embed-source]')];
    expect(links.map(a => a.getAttribute('href'))).toEqual(['https://www.youtube.com/watch?v=M7lc1UVf-VE', 'https://x.com/margen/status/77']);
    expect(links.every(a => a.rel === 'noopener noreferrer' && a.target === '_blank')).toBe(true);
    expect([...document.querySelectorAll('img')].map(i => i.getAttribute('src'))).toEqual(['data:image/png;base64,AAAA']);
    expect(document.querySelector('iframe')).toBeNull();
    expect(document.querySelector<HTMLButtonElement>('[data-embed-load]')!.hidden).toBe(false);
    expect(document.querySelector<HTMLElement>('[data-embed-notice]')!.hidden).toBe(false);
  });

  it('una tarjeta sintética no enlaza a una cuenta real', () => {
    document.body.innerHTML = '<figure class="embed" data-embed="x" data-embed-user="ejemplo" data-embed-synthetic><figcaption><a data-embed-source href="https://x.com/ejemplo">Ver en X</a></figcaption></figure>';
    E().init();
    expect(document.querySelector('a')).toBeNull();
    expect(document.querySelector('figcaption')!.textContent).toContain('Ejemplo sintético');
  });

  it('un ID inválido deja la tarjeta legible y sin botón de carga', () => {
    document.body.innerHTML = youtube().replace('M7lc1UVf-VE', 'nope');
    E().init();
    expect(document.querySelector<HTMLButtonElement>('[data-embed-load]')!.hidden).toBe(true);
    expect(document.querySelector<HTMLElement>('[data-embed-notice]')!.hidden).toBe(true);
    expect(document.querySelector('a')).toBeNull();
    expect(document.querySelector('[data-embed-status]')!.textContent).toMatch(/identificador válido/);
  });

  it('el clic sintético no carga; la carga local usa atributos medidos y se limpia', () => {
    vi.useFakeTimers();
    document.body.innerHTML = youtube();
    const [embed] = E().init();
    document.querySelector<HTMLButtonElement>('[data-embed-load]')!.click();
    expect(document.querySelector('iframe')).toBeNull();
    embed.mount();
    const frame = document.querySelector('iframe')!;
    expect(frame.getAttribute('sandbox')).toBe('allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox allow-presentation');
    expect(frame.getAttribute('referrerpolicy')).toBe('strict-origin');
    expect(frame.getAttribute('allow')).toBe('autoplay; encrypted-media; picture-in-picture; fullscreen');
    expect(frame.src.startsWith('https://www.youtube-nocookie.com/embed/M7lc1UVf-VE?')).toBe(true);
    const status = document.querySelector('[data-embed-status]')!;
    // Mensajes de otra ventana, del origen equivocado u opacos no cuentan como señal de vida.
    window.dispatchEvent(new MessageEvent('message', {source: window, origin: 'https://www.youtube-nocookie.com', data: '{"event":"onReady"}'}));
    window.dispatchEvent(new MessageEvent('message', {source: frame.contentWindow, origin: 'null', data: '{"event":"onReady"}'}));
    vi.advanceTimersByTime(8000);
    expect(status.textContent).toMatch(/no respondió/);
    window.dispatchEvent(new MessageEvent('message', {source: frame.contentWindow, origin: 'https://www.youtube-nocookie.com', data: '{"event":"onError","info":150}'}));
    expect(status.textContent).toMatch(/no permite verlo insertado/);
    document.querySelector<HTMLButtonElement>('.embed-quitar')!.click();
    expect(document.querySelector('iframe')).toBeNull();
    expect(document.querySelector('.embed-quitar')).toBeNull();
    // Tras retirar el reproductor no queda temporizador que escriba un estado tardío.
    vi.advanceTimersByTime(30000);
    expect(status.textContent).toBe('Reproductor retirado.');
  });

  it('Instagram usa no-referrer y acota la altura medida', () => {
    document.body.innerHTML = '<figure class="embed embed-instagram" data-embed="instagram" data-embed-id="fA9uwTtkSN" data-embed-kind="p"><div class="embed-lienzo" data-embed-stage></div><button type="button" data-embed-load hidden>Cargar</button><p data-embed-status></p></figure>';
    const [embed] = E().init();
    embed.mount();
    const frame = document.querySelector('iframe')!;
    expect(frame.getAttribute('referrerpolicy')).toBe('no-referrer');
    expect(frame.src).toBe('https://www.instagram.com/p/fA9uwTtkSN/embed/');
    window.dispatchEvent(new MessageEvent('message', {source: frame.contentWindow, origin: 'https://www.instagram.com', data: '{"type":"MEASURE","details":{"height":3500}}'}));
    expect(frame.style.height).toBe('1200px');
    E().destroy(embed.el);
    expect(document.querySelector('iframe')).toBeNull();
  });

  it('en el portal sólo pide proveedor + ID y devuelve el foco al cerrar', async () => {
    const embed = vi.fn(async () => ({ok: true})), openSource = vi.fn(async () => ({ok: true}));
    (window as any).BottifactReviewBridge = {embed, openSource};
    Object.defineProperty(window, 'parent', {value: {postMessage() {}}, configurable: true});
    document.body.innerHTML = youtube();
    const [card] = E().init();
    await card.load({isTrusted: true});
    expect(embed).toHaveBeenCalledWith({provider: 'youtube', id: 'M7lc1UVf-VE'});
    expect(document.querySelector('iframe')).toBeNull();
    document.dispatchEvent(new CustomEvent('margen:embed-closed'));
    expect(document.activeElement).toBe(document.querySelector('[data-embed-load]'));
    const link = document.querySelector('a')!;
    const click = new MouseEvent('click', {bubbles: true, cancelable: true});
    link.dispatchEvent(click);
    expect(click.defaultPrevented).toBe(true);
    expect(openSource).toHaveBeenCalledWith({provider: 'youtube', id: 'M7lc1UVf-VE'});
  });

  it('construye la tarjeta de X con texto, nunca con HTML', () => {
    const figure = E().card({name: '<b>Ana</b>', user: 'ana', text: '<img src=x onerror=alert(1)>\n\nSegundo', synthetic: true, media: 'https://x.com/a.png'});
    expect(figure.querySelector('img')).toBeNull();
    expect(figure.querySelector('b')).toBeNull();
    expect(figure.querySelectorAll('.embed-texto p')).toHaveLength(2);
    expect(figure.querySelector('.embed-texto p')!.textContent).toBe('<img src=x onerror=alert(1)>');
    expect(figure.dataset.embedSynthetic).toBe('');
  });
});
