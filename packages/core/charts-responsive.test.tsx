import {beforeEach, afterEach, expect, it, vi} from 'vitest';
import {readFileSync} from 'node:fs';
const source=readFileSync('packages/core/components/charts.js','utf8');
const fixture=readFileSync('packages/core/recipes/bar-chart/example.html','utf8');
let resize: () => void;
let width=0;
const disconnected=vi.fn();
const api=()=> (window as any).NotaGraficas;
const host=()=>document.querySelector('figure')!;
beforeEach(()=>{
  width=0; disconnected.mockClear();
  vi.stubGlobal('ResizeObserver',class {constructor(fn:()=>void){resize=fn;} observe(){} disconnect(){disconnected();}});
  document.body.innerHTML=fixture;
  vi.spyOn(host(),'getBoundingClientRect').mockImplementation(()=>({width}) as DOMRect);
  window.eval(source);
});
afterEach(()=>{api().get(host())?.destroy();vi.restoreAllMocks();vi.unstubAllGlobals();document.body.replaceChildren();});
it('reveals bars when a hidden chapter opens on mobile and preserves exact source values',()=>{
  const table=host().querySelector('table')!.outerHTML;
  width=284;resize();
  const svg=host().querySelector('svg')!;
  expect(svg.getAttribute('viewBox')).toMatch(/^0 0 284 /);
  for(const bar of svg.querySelectorAll('rect')){
    const x=Number(bar.getAttribute('x')), w=Number(bar.getAttribute('width'));
    expect(x).toBeGreaterThanOrEqual(0);
    expect(x+w).toBeLessThan(width);
  }
  expect([...svg.querySelectorAll('rect')].map(r=>r.getAttribute('data-value'))).toEqual(['60','25','15','-10']);
  expect(host().querySelector('table')!.outerHTML).toBe(table);
  expect(svg.outerHTML).not.toMatch(/NaN|Infinity/);
});
it('keeps one chart, user disclosure state and a correct negative baseline after resizing',()=>{
  const details=host().querySelector('details')!;details.open=true;
  width=320;resize();width=900;resize();
  expect(details.open).toBe(true);
  expect(host().querySelectorAll('svg')).toHaveLength(1);
  expect(host().querySelectorAll('.grafica-leyenda')).toHaveLength(1);
  const svg=host().querySelector('svg')!, bars=[...svg.querySelectorAll('rect')];
  const zero=Number(svg.querySelector('.grafica-eje')!.getAttribute('x1'));
  const negative=bars.at(-1)!;
  expect(Number(negative.getAttribute('x'))+Number(negative.getAttribute('width'))).toBeCloseTo(zero);
  expect(Number(bars[0].getAttribute('width'))/Number(negative.getAttribute('width'))).toBeCloseTo(6);
  api().get(host()).destroy();expect(disconnected).toHaveBeenCalledOnce();
  expect(host().querySelector('svg')).toBeNull();
});
