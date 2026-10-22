import {expect,it,vi} from 'vitest';
import {readFileSync} from 'node:fs';
it('reports the document surface to the host only as an opaque RGB triple',()=>{
 vi.useFakeTimers();
 document.body.innerHTML='<main><p>Texto</p></main>';
 const post=vi.spyOn(window.parent,'postMessage').mockImplementation(()=>{});
 window.eval(readFileSync('portal/static/bridge.js','utf8'));
 const surfaces=()=>post.mock.calls.map(call=>call[0] as any).filter(message=>message.op==='surface').map(message=>message.data.color);
 window.dispatchEvent(new Event('DOMContentLoaded'));
 expect(surfaces()).toEqual([null]);
 document.body.style.backgroundColor='rgb(19, 17, 15)';
 window.dispatchEvent(new Event('load'));
 expect(surfaces()).toEqual([null,[19,17,15]]);
 document.body.style.backgroundColor='rgba(19, 17, 15, 0.5)';
 document.dispatchEvent(new CustomEvent('nota:tema'));vi.runAllTimers();
 expect(surfaces()).toEqual([null,[19,17,15],null]);
 expect(document.documentElement.hasAttribute('data-margen-surface')).toBe(false);
 post.mockRestore();vi.clearAllTimers();vi.useRealTimers();
});
