import {afterEach, beforeAll, describe, expect, it, vi} from 'vitest';
import {readFileSync} from 'node:fs';

const R = () => (window as any).MargenReaderActions;

beforeAll(() => {
  const proto = HTMLDialogElement.prototype as any;
  if (!proto.showModal || !proto.__margen) {
    proto.__margen = true;
    proto.showModal = function () { this.setAttribute('open', ''); };
    proto.close = function () { if (!this.hasAttribute('open')) return; this.removeAttribute('open'); setTimeout(() => this.dispatchEvent(new Event('close'))); };
  }
  window.eval(readFileSync('portal/static/reader-actions.js', 'utf8'));
});
afterEach(() => { document.body.innerHTML = ''; vi.useRealTimers(); vi.restoreAllMocks(); });

const STATE = {artifact: 'a1', saved: false, liked: false, likes: 2, signed_in: true, can_act: true, saved_path: '/?view=saved'};

function host(state: any = STATE) {
  const dockHost = document.createElement('div');
  const frame = document.createElement('iframe');
  document.body.append(dockHost, frame);
  vi.spyOn(frame, 'getBoundingClientRect').mockReturnValue({left: 0, top: 0, right: 1000, bottom: 800, width: 1000, height: 800, x: 0, y: 0, toJSON() {}} as DOMRect);
  const posted: any[] = [];
  vi.spyOn(frame.contentWindow!, 'postMessage').mockImplementation((m: any) => { posted.push(m); });
  const calls: any[] = [];
  vi.stubGlobal('fetch', vi.fn(async (url: string, init: any = {}) => {
    calls.push({url, init});
    return new Response(JSON.stringify(state), {status: 200, headers: {'content-type': 'application/json'}});
  }));
  const actions = R().create({frame: () => frame, dock: () => dockHost});
  return {actions, frame, dockHost, posted, calls};
}
const anchor = {visible: true, x: 40, y: 120, width: 220, height: 44, vw: 1000, vh: 800};
const mutations = (calls: any[]) => calls.filter(c => c.init.method === 'PUT');

describe('validación del ancla', () => {
  it('acepta sólo geometría acotada y finita', () => {
    const {validateAnchor} = R();
    expect(validateAnchor(anchor)).toEqual(anchor);
    expect(validateAnchor({visible: false})).toEqual({visible: false, slot: false});
    expect(validateAnchor({visible: false, slot: true})).toEqual({visible: false, slot: true});
    for (const bad of [
      {...anchor, x: NaN}, {...anchor, y: Infinity}, {...anchor, width: 5000}, {...anchor, height: 400}, {...anchor, x: 900},
      {...anchor, op: 'save'}, {...anchor, saved: true}, {...anchor, slot: true}, {...anchor, vw: 0}, {...anchor, width: '220'},
      {visible: 'yes'}, {visible: false, liked: true}, {visible: false, slot: false}, null, [], 'save',
    ]) expect(validateAnchor(bad)).toBeNull();
  });
});

describe('frontera de confianza', () => {
  it('un mensaje forjado sólo mueve el ancla y nunca muta', async () => {
    const {actions, calls, posted} = host();
    await actions.load({id: 'a1', title: 'Informe'});
    expect(posted.at(-1)).toEqual({bottifact: 1, op: 'reader-actions-slot', height: 44});
    for (const forged of [{op: 'save'}, {saved: true}, {...anchor, liked: true}, {visible: true}])
      expect(actions.anchor(forged)).toEqual({ok: false});
    expect(actions.anchor(anchor)).toEqual({ok: true});
    const overlay = actions.nodes.overlay as HTMLElement;
    expect(overlay.hidden).toBe(false);
    expect([overlay.style.left, overlay.style.top, overlay.style.width]).toEqual(['40px', '120px', '220px']);
    expect(mutations(calls)).toEqual([]);
  });

  it('un ancla fuera de la caja visible del iframe se oculta', async () => {
    const {actions} = host();
    await actions.load({id: 'a1', title: 'Informe'});
    actions.anchor({...anchor, y: -20});
    expect((actions.nodes.overlay as HTMLElement).hidden).toBe(true);
    actions.anchor({visible: false});
    expect((actions.nodes.overlay as HTMLElement).hidden).toBe(true);
  });

  it('clics sintéticos (no isTrusted) no abren ni mutan', async () => {
    const {actions, calls} = host();
    await actions.load({id: 'a1', title: 'Informe'});
    actions.anchor(anchor);
    const overlay = actions.nodes.overlay as HTMLElement, dialog = actions.nodes.dialog as HTMLDialogElement;
    overlay.querySelectorAll('button').forEach(b => b.click());
    expect(dialog.open).toBe(false);
    dialog.querySelectorAll<HTMLButtonElement>('.reader-actions-choices button').forEach(b => { b.disabled = false; b.click(); });
    (actions.nodes.dock as HTMLElement).querySelectorAll('button').forEach(b => b.click());
    expect(mutations(calls)).toEqual([]);
  });

  it('sin ancla usa el dock fijo; con ancla no hay botones duplicados', async () => {
    vi.useFakeTimers();
    const {actions, dockHost} = host();
    await actions.load({id: 'a1', title: 'Informe'});
    const dock = actions.nodes.dock as HTMLElement;
    expect(dock.parentElement).toBe(dockHost);
    expect(dock.hidden).toBe(true);
    vi.advanceTimersByTime(1300);
    expect(dock.hidden).toBe(false);
    expect(dock.querySelector('[data-action=liked]')!.getAttribute('aria-label')).toBe('Me gusta. 2 cuentas lo marcaron');
    actions.anchor(anchor);
    expect(dock.hidden).toBe(true);
  });

  it('cambiar de documento descarta el estado y el ancla previos', async () => {
    const {actions} = host();
    await actions.load({id: 'a1', title: 'Informe'});
    actions.anchor(anchor);
    actions.reset();
    expect(actions.anchor(anchor)).toEqual({ok: false});
    expect((actions.nodes.overlay as HTMLElement).hidden).toBe(true);
  });
});
