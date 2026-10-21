import {afterEach,beforeEach,expect,it,vi} from 'vitest';
import {readFileSync} from 'node:fs';
const source=readFileSync('packages/core/components/reader-speech.js','utf8');
let speech:any, synth:any, spoken:any[], voices:any[], instance:any;
const local={voiceURI:'local',name:'Local test',lang:'es-CO',localService:true,default:false};
const remote={voiceURI:'remote',name:'Remote test',lang:'es-CO',localService:false,default:true};
beforeEach(()=>{
 vi.useFakeTimers();
 document.documentElement.lang='es';
 document.body.innerHTML='<main><h1>Documento</h1><section id="one"><h2>Primera sección</h2><p id="a">Una frase con <strong>énfasis</strong> editorial.</p><p id="b">Segundo párrafo.</p></section><section id="two"><h2>Segunda sección</h2><p>Final.</p></section></main><nav class="bottifact-toolbar"></nav>';
 spoken=[];voices=[remote,local];synth=new EventTarget();Object.assign(synth,{getVoices:()=>voices,speak:vi.fn(u=>spoken.push(u)),cancel:vi.fn(),pause:vi.fn(),resume:vi.fn()});
 Object.defineProperty(window,'speechSynthesis',{value:synth,configurable:true});
 (window as any).SpeechSynthesisUtterance=class{constructor(public text:string){}};
 delete (window as any).MargenSpeech;window.eval(source);speech=(window as any).MargenSpeech;
 instance=speech.mount(document.querySelector('nav'));
});
afterEach(()=>{instance.destroy();vi.clearAllTimers();vi.useRealTimers();window.getSelection()?.removeAllRanges();});
const click=(label:string)=>{const b=[...document.querySelectorAll('button')].find(b=>b.textContent===label)!;expect(b).toBeTruthy();b.click();};
it('extracts in DOM order, without duplicate wrappers, controls or hidden content',()=>{
 document.querySelector('main')!.insertAdjacentHTML('beforeend','<nav>Skip nav</nav><p hidden>Hidden</p><div style="display:none"><p>CSS hidden</p></div><p aria-hidden="true">ARIA hidden</p><div inert>Inert</div><p>Text <button>Skip button</button>end.</p><div>Loose text <em>inline</em>.</div><table><caption>Values</caption><tr><th>Name</th><th>Count</th></tr><tr><td>A</td><td>2</td></tr></table><div data-revision>Private notes</div><div data-speech-skip>Skip</div>');
 const text=speech.extract().map((x:any)=>x.text);
 expect(text).toEqual(['Documento','Primera sección','Una frase con énfasis editorial.','Segundo párrafo.','Segunda sección','Final.','Text end.','Loose text inline.','Values','Name','Count','A','2']);
});
it('reads exact multi-block selection excluding controls and preserves the selection',()=>{
 const range=document.createRange();range.setStart(document.querySelector('#a')!.firstChild!,4);range.setEnd(document.querySelector('#b')!.firstChild!,7);
 window.getSelection()!.addRange(range);document.dispatchEvent(new Event('selectionchange'));
 expect(speech.extract({range}).map((x:any)=>x.text)).toEqual(['frase con énfasis editorial.','Segundo']);
 const selected=window.getSelection()!.toString();click('Leer selección');expect(spoken[0].text).toBe('frase con énfasis editorial.');expect(window.getSelection()!.toString()).toBe(selected);
 spoken[0].onend();expect(spoken[1].text).toBe('Segundo');
});
it('does not autoplay; prefers local voices and queues one bounded chunk at a time',()=>{
 expect(spoken).toHaveLength(0);document.querySelector('#a')!.textContent='Palabras largas. '.repeat(100);
 click('Escuchar documento completo');expect(spoken).toHaveLength(1);expect(spoken[0].voice).toBe(local);
 for(let i=0;i<12;i++){expect(spoken[i].text.length).toBeLessThanOrEqual(220);spoken[i].onend();}
 expect(document.querySelectorAll('[data-speech-current]')).toHaveLength(1);
 expect(speech.chunk('x'.repeat(1000)).every((s:string)=>s.length<=220)).toBe(true);
});
it('pauses, resumes, stops and ignores stale end/error events',()=>{
 click('Escuchar documento completo');const first=spoken[0];first.onstart();click('Pausar');expect(synth.pause).toHaveBeenCalledOnce();expect(instance.state).toBe('paused');
 click('Reanudar');expect(synth.resume).toHaveBeenCalled();expect(instance.state).toBe('playing');click('Detener');expect(synth.cancel).toHaveBeenCalledOnce();
 first.onend();first.onerror({error:'canceled'});expect(spoken).toHaveLength(1);expect(document.querySelector('[data-speech-current]')).toBeNull();expect(instance.state).toBe('idle');
 click('Escuchar documento completo');first.onend();expect(spoken).toHaveLength(2);
});
it('handles end while paused without losing the next chunk',()=>{
 click('Escuchar documento completo');click('Pausar');spoken[0].onend();expect(spoken).toHaveLength(1);click('Reanudar');expect(spoken).toHaveLength(2);
});
it('cancels on pagehide and document/chapter changes, never restarts automatically',()=>{
 click('Escuchar documento completo');window.dispatchEvent(new Event('pagehide'));expect(instance.state).toBe('idle');
 click('Escuchar documento completo');document.dispatchEvent(new CustomEvent('nota:pagina'));expect(instance.state).toBe('idle');vi.advanceTimersByTime(20000);expect(spoken).toHaveLength(2);
});
it('reports missing voices/API and delayed voices without starting playback',()=>{
 voices=[];synth.dispatchEvent(new Event('voiceschanged'));click('Escuchar documento completo');expect(document.body.textContent).toContain('No hay voces disponibles');expect(spoken).toHaveLength(0);
 voices=[local];synth.dispatchEvent(new Event('voiceschanged'));expect(spoken).toHaveLength(0);click('Escuchar documento completo');expect(spoken).toHaveLength(1);
 instance.destroy();Object.defineProperty(window,'speechSynthesis',{value:undefined,configurable:true});instance=speech.mount(document.querySelector('nav'));click('Escuchar documento completo');expect(document.body.textContent).toContain('Este navegador no ofrece lectura por voz');
});
it('reports engine errors and stalled startup, without automatic retry',()=>{
 click('Escuchar documento completo');spoken[0].onerror({error:'not-allowed'});expect(document.body.textContent).toContain('El navegador bloqueó');
 click('Escuchar documento completo');vi.advanceTimersByTime(12001);expect(instance.state).toBe('idle');expect(document.body.textContent).toContain('La voz no respondió');expect(spoken).toHaveLength(2);
});
it('announces code blocks in full reading, reads code only when selected',()=>{
 document.querySelector('main')!.innerHTML='<pre><code>const answer = 42;</code></pre>';
 click('Escuchar documento completo');expect(spoken[0].text).toContain('Bloque de código');click('Detener');
 const range=document.createRange();range.selectNodeContents(document.querySelector('code')!);window.getSelection()!.removeAllRanges();window.getSelection()!.addRange(range);document.dispatchEvent(new Event('selectionchange'));click('Leer selección');expect(spoken[1].text).toBe('const answer = 42;');
});
it('preserves native context menus for selected text, links, code and Shift',async()=>{
 await Promise.resolve();
 const send=(target:Element,shiftKey=false)=>{const e=new MouseEvent('contextmenu',{bubbles:true,cancelable:true,shiftKey});target.dispatchEvent(e);return e.defaultPrevented;};
 expect(send(document.querySelector('#a')!,true)).toBe(false);
 document.querySelector('#a')!.innerHTML='<a href="#">Link</a><code>Code</code>';
 expect(send(document.querySelector('a')!)).toBe(false);expect(send(document.querySelector('code')!)).toBe(false);
 const range=document.createRange();range.selectNodeContents(document.querySelector('#b')!);window.getSelection()!.addRange(range);expect(send(document.querySelector('#b')!)).toBe(false);
});
it('offers point and section reading by keyboard, restores tabindex and permits cancellation',()=>{
 click('Elegir desde dónde leer');expect(document.querySelector('#a')!.getAttribute('tabindex')).toBe('0');
 document.querySelector('#a')!.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true,cancelable:true}));
 expect(document.querySelector('#a')!.hasAttribute('tabindex')).toBe(false);click('Leer esta sección');expect(spoken[0].text).toBe('Primera sección');
 click('Detener');click('Elegir desde dónde leer');document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));expect(document.querySelector('#a')!.hasAttribute('tabindex')).toBe(false);
});
it('keeps comment and speech actions in one contextual menu',()=>{
 const comment=vi.fn(),e=new MouseEvent('contextmenu',{cancelable:true});Object.defineProperty(e,'target',{value:document.querySelector('#a')});
 speech.context(e,{label:'Comentar aquí',run:comment});expect(document.querySelectorAll('[role=menuitem]')).toHaveLength(3);click('Comentar aquí');expect(comment).toHaveBeenCalledOnce();expect(spoken).toHaveLength(0);
});
it('reads known chapter pages but excludes unrelated hidden content',()=>{
 document.querySelector('main')!.className='multipagina';document.querySelector('main')!.innerHTML='<article id="p1" class="pagina"><p>First</p></article><article id="p2" class="pagina" hidden><p>Second</p><p hidden>Secret</p></article>';
 expect(speech.extract().map((x:any)=>x.text)).toEqual(['First']);expect(speech.extract({allPages:true}).map((x:any)=>x.text)).toEqual(['First','Second']);
});

it('preserves spaces between inline nodes',()=>{
 document.querySelector('#a')!.innerHTML='<strong>Uno</strong> <em>dos</em> <span>tres</span>';
 expect(speech.extract().find((x:any)=>x.element.id==='a').text).toBe('Uno dos tres');
});
it('reinstates startup timeout after pausing before the engine starts',()=>{
 click('Escuchar documento completo');click('Pausar');vi.advanceTimersByTime(13000);expect(instance.state).toBe('paused');
 click('Reanudar');vi.advanceTimersByTime(13000);expect(instance.state).toBe('idle');expect(document.body.textContent).toContain('La voz no respondió');
});
it('moves keyboard focus to the player when starting from context',()=>{
 const e=new MouseEvent('contextmenu',{cancelable:true});Object.defineProperty(e,'target',{value:document.querySelector('#a')});speech.context(e);
 click('Leer desde aquí');expect(document.activeElement?.textContent).toBe('Pausar');expect(document.activeElement?.closest('[hidden]')).toBeNull();
});
it('applies the chosen remote voice and speed only to the next fragment',()=>{
 click('Escuchar documento completo');const voice=document.querySelector('select[aria-label=Voz]') as HTMLSelectElement;
 voice.value=JSON.stringify([remote.voiceURI,remote.name,remote.lang,remote.localService]);voice.dispatchEvent(new Event('change'));
 const speed=document.querySelector('select[aria-label=Velocidad]') as HTMLSelectElement;speed.value='1.5';speed.dispatchEvent(new Event('change'));
 expect(spoken[0].voice).toBe(local);spoken[0].onend();expect(spoken[1].voice).toBe(remote);expect(spoken[1].rate).toBe(1.5);
 voices=[local];synth.dispatchEvent(new Event('voiceschanged'));expect(instance.state).toBe('idle');expect(document.body.textContent).toContain('La voz elegida ya no está disponible');
});
it('does not read script/control text in a range and excludes collapsed disclosure content',()=>{
 document.querySelector('#a')!.innerHTML='Editorial <button>Control</button><script>private()</script> final';
 const range=document.createRange();range.selectNodeContents(document.querySelector('#a')!);
 expect(speech.extract({range}).map((x:any)=>x.text)).toEqual(['Editorial final']);
 document.querySelector('main')!.insertAdjacentHTML('beforeend','<details><summary>Control</summary><p>Collapsed content</p></details><details open><summary>Control</summary><p>Expanded content</p></details>');
 const text=speech.extract().map((x:any)=>x.text).join(' ');expect(text).not.toContain('Collapsed content');expect(text).toContain('Expanded content');expect(text).not.toContain('Control');
});

it('keeps semantic line breaks as separators, including a partial selection',()=>{
 document.querySelector('#a')!.innerHTML='Primera línea<br>Segunda línea';
 expect(speech.extract().find((x:any)=>x.element.id==='a').text).toBe('Primera línea Segunda línea');
 const range=document.createRange();range.setStart(document.querySelector('#a')!.firstChild!,8);range.setEnd(document.querySelector('#a')!.lastChild!,7);
 expect(speech.extract({range}).map((x:any)=>x.text)).toEqual(['línea Segunda']);
});
