import { beforeEach, expect, it, vi } from 'vitest';
import { readFileSync } from 'node:fs';
let nav: HTMLElement;
beforeEach(() => {
  document.body.innerHTML = '<nav class="tabs"><button data-view="mine">Mine</button><button data-view="shared">Shared</button><button data-view="brain">Graph</button><button data-view="admin" hidden>Admin</button></nav>';
  nav = document.querySelector('nav')!;
  window.eval(readFileSync('portal/static/sidebar.js', 'utf8'));
});
it('moves existing destinations without dropping handlers or revealing admin', () => {
  const shared = nav.querySelector<HTMLButtonElement>('[data-view=shared]')!;
  const click = vi.fn(); shared.addEventListener('click', click);
  (window as any).MargenSidebar.init(nav);
  (window as any).MargenSidebar.init(nav);
  expect(nav.querySelectorAll('.nav-group')).toHaveLength(3);
  expect(nav.querySelector('.nav-library [data-view=shared]')).toBe(shared);
  shared.click(); expect(click).toHaveBeenCalledOnce();
  expect(nav.querySelector<HTMLButtonElement>('[data-view=admin]')!.hidden).toBe(true);
});
it('searches all spaces, preserves focus and uses selected rows as toggles', () => {
  const sidebar = (window as any).MargenSidebar;
  sidebar.init(nav);
  const onSelect = vi.fn();
  const props = {id:'company-nav', label:'Espacios', values:['Ágora','B','C','D','E','F','G','<img src=x>'], selected:'Ágora', onSelect, open:true};
  sidebar.facets(nav, props);
  const input = nav.querySelector<HTMLInputElement>('input')!;
  input.focus(); input.value = 'agora'; input.dispatchEvent(new Event('input'));
  const rows = [...nav.querySelectorAll<HTMLButtonElement>('[data-value]')];
  expect(rows.filter(b => !b.hidden)).toHaveLength(1);
  rows[0].click(); expect(onSelect).toHaveBeenLastCalledWith('');
  sidebar.facets(nav, {...props, selected:''});
  expect(document.activeElement).toBe(input);
  expect(rows[0].getAttribute('aria-pressed')).toBe('false');
  expect(nav.querySelector('img')).toBeNull();
  input.value = 'missing'; input.dispatchEvent(new Event('input'));
  expect(nav.querySelector<HTMLElement>('[role=status]')!.hidden).toBe(false);
});
