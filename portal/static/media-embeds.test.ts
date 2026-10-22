import {afterEach, beforeAll, describe, expect, it, vi} from 'vitest';
import {readFileSync} from 'node:fs';

const M = () => (window as any).MargenMediaEmbeds;
const core = readFileSync('packages/core/components/embeds.js', 'utf8');

beforeAll(() => {
  // jsdom no implementa el modal; basta con abrir/cerrar y emitir «close» como tarea.
  const proto = HTMLDialogElement.prototype as any;
  if (!proto.showModal || !proto.__margen) {
    proto.__margen = true;
    proto.showModal = function () { this.setAttribute('open', ''); };
    proto.close = function () { if (!this.hasAttribute('open')) return; this.removeAttribute('open'); setTimeout(() => this.dispatchEvent(new Event('close'))); };
  }
  window.eval(readFileSync('portal/static/media-embeds.js', 'utf8'));
});
afterEach(() => { document.body.innerHTML = ''; vi.useRealTimers(); vi.restoreAllMocks(); });

function host(state: any = {artifact: 'a1', version: 'v1'}, activation: boolean | null = true) {
  const frame = document.createElement('iframe');
  document.body.append(frame);
  const posted: any[] = [];
  vi.spyOn(frame.contentWindow!, 'postMessage').mockImplementation((m: any) => { posted.push(m); });
  const media = M().create({frame: () => frame, mounted: () => state.current === undefined ? state : state.current, origin: 'https://artifacts.botto.is', userActivation: () => activation});
  return {media, frame, posted, state};
}
const yt = {provider: 'youtube', id: 'M7lc1UVf-VE', version: 'v1'};

describe('validación del mensaje', () => {
  it('acepta sólo el esquema exacto', () => {
    const {validate} = M();
    expect(validate(yt)).toEqual(yt);
    expect(validate({provider: 'instagram', id: 'fA9uwTtkSN', kind: 'reel', version: 'v1'})).toEqual({provider: 'instagram', id: 'fA9uwTtkSN', kind: 'reel', version: 'v1'});
    expect(validate({provider: 'x', user: 'margen', status: '12', version: 'v1'})).toEqual({provider: 'x', user: 'margen', status: '12', version: 'v1'});
    for (const bad of [
      {...yt, url: 'https://evil.example'}, {...yt, srcdoc: '<script>'}, {...yt, html: '<b>'}, {...yt, id: 'M7lc1UVf-V'},
      {...yt, id: ['M7lc1UVf-VE']}, {...yt, version: undefined}, {...yt, version: 'v'.repeat(81)}, {provider: 'vimeo', id: '1', version: 'v1'},
      {provider: 'toString', version: 'v1'}, {provider: 'instagram', id: 'fA9uwTtkSN', kind: 'tv', version: 'v1'},
      {provider: 'x', user: 'margen', status: 12, version: 'v1'}, {provider: 'x', user: 'a.b', version: 'v1'}, null, [], 'youtube',
    ]) expect(validate(bad)).toBeNull();
  });

  it('coincide con la tabla del componente del artefacto', () => {
    window.eval(core);
    const E = (window as any).MargenEmbeds;
    for (const spec of [{provider: 'youtube', id: 'M7lc1UVf-VE'}, {provider: 'instagram', id: 'fA9uwTtkSN', kind: 'p'}, {provider: 'instagram', id: 'fA9uwTtkSN', kind: 'reel'}]) {
      expect(M().playerURL(spec, 'https://artifacts.botto.is')).toBe(E.playerURL(spec, 'https://artifacts.botto.is'));
      expect(M().sourceURL(spec)).toBe(E.sourceURL(spec));
    }
    expect(M().SANDBOX).toBe(E.SANDBOX);
    expect(M().REFERRER).toEqual(E.REFERRER);
    expect(M().ORIGINS).toEqual(E.ORIGINS);
  });
});

describe('diálogo del portal', () => {
  it('rechaza sin documento montado, de otra versión o con X como reproductor', () => {
    const {media, state} = host();
    expect(() => media.handle('embed', {...yt, version: 'v0'})).toThrow(/otra versión/);
    expect(() => media.handle('embed', {provider: 'x', user: 'margen', version: 'v1'})).toThrow(/X no se inserta/);
    expect(() => media.handle('navigate', yt)).toThrow(/no permitida/);
    state.current = null;
    expect(() => media.handle('embed', yt)).toThrow(/No hay un documento/);
    expect(document.querySelector('.media-player')).toBeNull();
  });

  it('no monta YouTube hasta una acción real del portal, incluso con activación heredada', () => {
    const {media} = host();
    expect(media.handle('embed', yt)).toEqual({ok:true, confirm:true});
    expect(media.dialog.open).toBe(true);
    expect(document.querySelector('.media-player')).toBeNull();
    expect(media.dialog.querySelector('a')!.getAttribute('href')).toBe('https://www.youtube.com/watch?v=M7lc1UVf-VE');
    const load=media.dialog.querySelector<HTMLButtonElement>('.media-play')!;
    expect(load.textContent).toBe('Reproducir aquí');
    load.click();
    window.dispatchEvent(new MessageEvent('message', {source:window,origin:'https://www.youtube-nocookie.com',data:'{"event":"onReady"}'}));
    expect(document.querySelector('.media-player')).toBeNull();
  });


  it('Instagram muestra la fuente exacta sin montar ni aceptar clics sintéticos', () => {
    const {media} = host();
    media.handle('embed', {provider:'instagram',id:'fA9uwTtkSN',kind:'p',version:'v1'});
    expect(document.querySelector('.media-player')).toBeNull();
    expect(media.dialog.querySelector('a')!.getAttribute('href')).toBe('https://www.instagram.com/p/fA9uwTtkSN/');
    media.dialog.querySelector<HTMLButtonElement>('.media-play')!.click();
    expect(document.querySelector('.media-player')).toBeNull();
  });


  it('al cerrar limpia y devuelve el foco sólo al mismo documento', async () => {
    vi.useFakeTimers();
    const {media, posted, state} = host();
    media.handle('embed', yt);
    media.dialog.close();
    vi.runOnlyPendingTimers();
    expect(document.querySelector('.media-player')).toBeNull();
    expect(posted).toEqual([{bottifact: 1, op: 'embed-closed'}]);
    media.handle('embed', yt);
    state.current = {artifact: 'a1', version: 'v2'};
    media.dialog.close();
    vi.runOnlyPendingTimers();
    expect(posted).toHaveLength(1);
  });

  it('cambiar de documento cierra sin avisar al nuevo y reabrir no pierde la sesión nueva', () => {
    vi.useFakeTimers();
    const {media, posted} = host();
    media.handle('embed', yt);
    media.reset();
    vi.runOnlyPendingTimers();
    expect(media.dialog.open).toBe(false);
    expect(document.querySelector('.media-player')).toBeNull();
    expect(posted).toHaveLength(0);
    media.handle('embed', yt);
    media.handle('embed', {provider: 'instagram', id: 'fA9uwTtkSN', kind: 'p', version: 'v1'});
    vi.runOnlyPendingTimers();
    expect(media.dialog.open).toBe(true);
    expect(document.querySelectorAll('.media-player')).toHaveLength(0);
    expect(media.dialog.querySelector('a')!.href).toContain('instagram.com');
  });

  it('sin clic del lector no abre nada ni muestra diálogos', () => {
    const {media} = host(undefined, false);
    const open = vi.spyOn(window, 'open');
    for (const [op, data] of [['embed', yt], ['open-source', yt], ['external', {href: 'https://example.org/', version: 'v1'}]] as const)
      expect(() => media.handle(op, data)).toThrow(/clic del lector/);
    expect(open).not.toHaveBeenCalled();
    expect(media.dialog.open).toBe(false);
    expect(document.querySelector('.media-player')).toBeNull();
  });

  it('sin API de activación, el portal pide confirmación con su propio botón', () => {
    const {media} = host(undefined, null);
    expect(media.handle('embed', yt)).toEqual({ok: true, confirm: true});
    expect(document.querySelector('.media-player')).toBeNull();
    const load = media.dialog.querySelector<HTMLButtonElement>('button.primary')!;
    load.click();
    expect(document.querySelector('.media-player')).toBeNull();
    load.dispatchEvent(Object.assign(new MouseEvent('click'), {}));
    expect(document.querySelector('.media-player')).toBeNull();
  });

  it('una solicitud de fuente muestra el enlace exacto del portal sin abrir pestañas', () => {
    const open = vi.spyOn(window, 'open');
    const {media} = host();
    expect(media.handle('open-source', {provider:'instagram',id:'fA9uwTtkSN',kind:'reel',version:'v1'})).toEqual({ok:true,confirm:true});
    expect(open).not.toHaveBeenCalled();
    expect(media.dialog.open).toBe(true);
    const a=media.dialog.querySelector('a')!;
    expect(a.getAttribute('href')).toBe('https://www.instagram.com/reel/fA9uwTtkSN/');
    expect(a.getAttribute('target')).toBe('_blank');
    expect(a.getAttribute('rel')).toBe('noopener noreferrer');
    expect(media.dialog.querySelector('iframe')).toBeNull();
  });


  it('los destinos externos válidos se presentan sin navegar; credenciales y relativos se explican', () => {
    const {external}=M();
    expect(external({href:'https://example.org/a?b=1#c',version:'v1'})).toMatchObject({kind:'https',href:'https://example.org/a?b=1#c',version:'v1'});
    expect(external({href:'mailto:ana@example.org',version:'v1'})).toMatchObject({kind:'mailto',href:'mailto:ana@example.org'});
    expect(external({href:'http://example.org/',version:'v1'})).toMatchObject({kind:'http'});
    expect(external({href:'tel:+123456',version:'v1'})).toMatchObject({kind:'tel'});
    expect(external({href:'https://user:pw@example.org/',version:'v1'})).toEqual({kind:'credentials',shown:'example.org',version:'v1'});
    expect(external({href:'../otra',version:'v1'})).toMatchObject({kind:'relative'});
    for(const href of ['https://exa mple.org/','https://example.org/\n','HTTPS:','https://'+'a'.repeat(2050)])
      expect(external({href,version:'v1'})).toBeNull();
    expect(external({href:'https://example.org/',version:'v1',target:'_top'})).toBeNull();
    expect(external({href:'https://example.org/'})).toBeNull();
    const open=vi.spyOn(window,'open'),{media}=host();
    expect(()=>media.handle('external',{href:'https://example.org/',version:'v0'})).toThrow(/otra versión/);
    expect(media.handle('external',{href:'https://example.org/perfil',version:'v1'})).toEqual({ok:true,confirm:true});
    const a=media.dialog.querySelector('a')!;
    expect(a.getAttribute('href')).toBe('https://example.org/perfil');
    expect(a.getAttribute('rel')).toBe('noopener noreferrer');
    expect(open).not.toHaveBeenCalled();
    media.handle('external',{href:'https://user:pw@example.org/',version:'v1'});
    expect(a.hidden).toBe(true);expect(a.hasAttribute('href')).toBe(false);
  });

});

describe('cableado del portal', () => {
  const app = readFileSync('portal/static/app.js', 'utf8');
  const html = readFileSync('portal/static/index.html', 'utf8');
  const bridge = readFileSync('portal/static/bridge.js', 'utf8');
  it('el artefacto sigue opaco y las operaciones pasan por el canal correlacionado', () => {
    expect(html).toContain('<iframe id="artifact-frame" title="Artefacto y comentarios" sandbox="allow-scripts allow-downloads" allow="clipboard-write"></iframe>');
    expect(html.indexOf('/static/media-embeds.js')).toBeLessThan(html.indexOf('/static/app.js'));
    expect(app).toMatch(/event\.source !== \$\("#artifact-frame"\)\.contentWindow \|\|\s+event\.origin !== "null"/);
    expect(app).toContain('result = media.handle(op, data);');
    expect(app).toMatch(/media\.reset\(\);\s+mounted = \{ artifact: current\.id/);
    expect(bridge).toContain("embed:spec=>send('embed',{...spec,version:embedVersion})");
    expect(bridge).toContain("if(event.isTrusted)send('external'");
  });
});
