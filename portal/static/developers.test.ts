import { beforeEach, afterEach, expect, it, vi } from 'vitest';
import { readFileSync } from 'node:fs';
let root: HTMLElement;
const tick = () => new Promise(resolve => setTimeout(resolve, 0));
const theme = {id:'theme-kaira', slug:'kaira', title:'Kaira', kind:'theme', origin:'bundled', status:'bundled', description:'Papel cálido', license:'MIT', version:'1', author:'Community', favorite:false};
const recipe = {id:'component-flow', title:'Diagrama <img src=x onerror=alert(1)>', kind:'component', status:'bundled', description:'Pasos', license:'MIT', author:'Community'};
beforeEach(() => {
  history.replaceState(null, '', '/?view=developers');
  document.body.innerHTML = '<section id="root"></section>';
  root = document.querySelector('#root')!;
  (HTMLDialogElement.prototype as any).showModal = function() { this.open = true; };
  (HTMLDialogElement.prototype as any).close = function() { this.open = false; this.dispatchEvent(new Event('close')); };
  window.eval(readFileSync('portal/static/developers.js', 'utf8'));
  window.eval(readFileSync('portal/static/community-studio.js', 'utf8'));
});
afterEach(() => { (window as any).MargenDevelopers.destroy(); vi.useRealTimers(); vi.restoreAllMocks(); });
const click = (text: string) => {
  const button = [...root.querySelectorAll<HTMLButtonElement>('button')].find(b => b.textContent === text);
  expect(button, text).toBeTruthy(); button!.click();
};
it('renders real items as text, filters accents and saves per-account favorites', async () => {
  const items = [structuredClone(theme), structuredClone(recipe)];
  const api = vi.fn(async (path, options) => path.endsWith('/favorite') ? {...theme, favorite:JSON.parse(options.body).favorite, favorites:1} : {items, can_submit:true, admin:false});
  await (window as any).MargenDevelopers.render({root, api, user:{}});
  expect(root.querySelector('img')).toBeNull();
  expect([...root.querySelectorAll('iframe')].every(f => f.getAttribute('sandbox') === '')).toBe(true);
  const search = root.querySelector<HTMLInputElement>('input[type=search]')!;
  search.value = 'calido'; search.dispatchEvent(new Event('input'));
  expect(root.querySelectorAll('.developer-card')).toHaveLength(1);
  click('Guardar'); await tick();
  expect(root.querySelector('[aria-label="Guardar Kaira"]')!.getAttribute('aria-pressed')).toBe('true');
  click('Favoritos'); await tick();
  expect(root.querySelectorAll('.developer-card')).toHaveLength(1);
  expect(root.textContent).not.toContain('Revisar aportes');
});
it('does not overwrite a new view when an old catalog request finishes', async () => {
  let finish: any;
  const api = () => new Promise(resolve => finish = resolve);
  const pending = (window as any).MargenDevelopers.render({root, api, user:null});
  (window as any).MargenDevelopers.destroy(); root.textContent = 'Another view';
  finish({items:[theme]}); await pending;
  expect(root.textContent).toBe('Another view');
});
it('distinguishes private creations, review queue and public catalog', async () => {
  const api = vi.fn(async path => path === '/api/developers/catalog' ? {items:[theme], can_submit:true, admin:true} : {items:[{...recipe, id:'pending', status:'pending'}]});
  await (window as any).MargenDevelopers.render({root, api, user:{}});
  click('Revisar aportes'); await tick();
  expect(api).toHaveBeenCalledWith('/api/developers/submissions?scope=review');
  expect(root.textContent).toContain('Pendiente de revisión');
  expect(root.querySelector('[aria-label^="Guardar"]')).toBeNull();
  click('Todos'); await tick();
  expect(root.textContent).toContain('Kaira');
  expect(root.textContent).not.toContain('Pendiente de revisión');
});
it('opens a shared item by URL even if it is not listed in the catalog', async () => {
  history.replaceState(null,'','/?view=developers&item=shared123');
  const api = vi.fn(async path => path.endsWith('/catalog') ? {items:[], can_submit:false, admin:false} : {...theme, id:'shared123', title:'Shared title', visibility:'unlisted', status:'draft', origin:'community'});
  await (window as any).MargenDevelopers.render({root, api, user:null}); await tick();
  expect(root.querySelector('dialog h2')!.textContent).toBe('Shared title');
  expect(root.querySelector<HTMLInputElement>('dialog input[readonly]')!.value).toContain('&item=shared123');
  expect(api).toHaveBeenCalledWith('/api/developers/items/shared123');
});
it('visual theme creation needs no JSON and sends selected fonts/colors', async () => {
  const onSaved = vi.fn();
  const api = vi.fn(async path => path.startsWith('/api/developers/preview') ? {html:'<p>Preview</p>'} : {id:'new', url:'/?view=developers&item=new'});
  (window as any).MargenStudio.open({root, api, kind:'theme', onSaved});
  const dialog = root.querySelector('dialog')!;
  const title = dialog.querySelector<HTMLInputElement>('input:not([type])')!; title.value = 'Jardín';
  const colors = dialog.querySelector<HTMLInputElement>('[data-token=papel]')!; colors.value = '#112233'; colors.dispatchEvent(new Event('input'));
  const selects = dialog.querySelectorAll<HTMLSelectElement>('.studio-form select'); selects[0].value = 'source-serif'; selects[1].value = 'manrope';
  click('Compartir por enlace'); await tick();
  expect(api.mock.calls.some(([path]) => path === '/api/developers/submissions')).toBe(false);
  dialog.querySelector<HTMLInputElement>('input[type=checkbox]')!.checked = true;
  click('Compartir por enlace'); await tick();
  const request = api.mock.calls.find(([path]) => path === '/api/developers/submissions')!;
  const body = JSON.parse((request[1] as any).body);
  expect(body.publication).toBe('shared');
  expect(body.package.content.light.papel).toBe('#112233');
  expect(body.package.typography).toEqual({heading:'source-serif', body:'manrope'});
  expect(body.package.title).toBe('Jardín');
  expect(onSaved).toHaveBeenCalledWith({id:'new', url:'/?view=developers&item=new'});
  expect(root.querySelector('dialog')).toBeNull();
});
it('keeps the visual draft when saving fails', async () => {
  const api = vi.fn(async path => { if (path.includes('/preview')) return {html:'<p>Preview</p>'}; throw Error('Try again'); });
  (window as any).MargenStudio.open({root, api, kind:'theme', onSaved:vi.fn()});
  const title = root.querySelector<HTMLInputElement>('input:not([type])')!; title.value = 'Keep me';
  click('Guardar para mí'); await tick();
  expect(root.querySelector('dialog')).not.toBeNull(); expect(title.value).toBe('Keep me');
  expect(root.textContent).toContain('Try again');
  click('Cerrar');
});

it.each([true, false])('preserves component content, license and provenance when forking (visual=%s)', async visual => {
  const initial = {...recipe, kind:'component', content:'<p>Original content</p>', source_url:'https://example.org/origin', license:'Apache-2.0', credits:'First author',
    ...(visual ? {design:{kind:'steps', text:'Original first step\nOriginal second step'}} : {})};
  const api = vi.fn(async path => path.endsWith('/visual-component') ? {content:'<ol><li>Generated</li></ol>'} : path.includes('/preview') ? {html:'Preview'} : {id:'new'});
  (window as any).MargenStudio.open({root, api, initial, onSaved:vi.fn()});
  click('Guardar para mí'); await tick(); await tick();
  const request = api.mock.calls.find(([path]) => path === '/api/developers/submissions')!;
  const saved = JSON.parse((request[1] as any).body).package;
  expect(saved.license).toBe(initial.license);
  expect(saved.source_url).toBe(initial.source_url);
  expect(saved.credits).toContain('First author');
  expect(saved.credits).toContain(initial.author);
  if (visual) expect(saved.design).toEqual((initial as any).design);
  else expect(saved.content).toBe(initial.content);
});
