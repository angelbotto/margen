import {afterEach,beforeEach,expect,it,vi} from 'vitest';
import {readFileSync} from 'node:fs';
const source=readFileSync('packages/core/components/reader-speech.js','utf8');
let speech:any, instance:any, bridge:any, events:any, spoken:any[], config:any;
const flush=async()=>{for(let i=0;i<8;i++)await Promise.resolve();};
beforeEach(async()=>{
 document.documentElement.lang='es';
 document.body.innerHTML='<main><h1>Documento</h1><section id="one"><h2>Primera sección</h2><p id="a">Una frase con <strong>énfasis</strong> editorial.</p><p id="b">Segundo párrafo.</p></section><section id="two"><h2>Segunda sección</h2><p>Final.</p></section></main><nav class="bottifact-toolbar"></nav>';
 spoken=[];config={enabled:true,provider:'Synthetic',voices:[{id:'test',label:'Test voice'}]};
 bridge={narration:vi.fn(async(data:any)=>{if(data.action==='config')return config;if(data.action==='start')spoken.push(...data.items);return {pending:true};}),subscribeNarration:(fn:any)=>{events=fn;return ()=>{};}};
 (window as any).BottifactReviewBridge=bridge;
 delete (window as any).MargenSpeech;window.eval(source);speech=(window as any).MargenSpeech;
 instance=speech.mount(document.querySelector('nav'));await flush();
});
afterEach(()=>{instance.destroy();window.getSelection()?.removeAllRanges();delete (window as any).BottifactReviewBridge;});
const click=(label:string)=>{const b=[...document.querySelectorAll('button')].find(b=>b.textContent===label)!;expect(b).toBeTruthy();b.click();};
const startRequest=()=>bridge.narration.mock.calls.findLast(([data]:any)=>data.action==='start')[0];
const emit=(state:string,index=0,message='')=>events({request:startRequest().request,state,index,message});
it('extracts in DOM order, without duplicate wrappers, controls or hidden content',()=>{
 document.querySelector('main')!.insertAdjacentHTML('beforeend','<nav>Skip nav</nav><p hidden>Hidden</p><div style="display:none"><p>CSS hidden</p></div><p aria-hidden="true">ARIA hidden</p><div inert>Inert</div><p>Text <button>Skip button</button>end.</p><div>Loose text <em>inline</em>.</div><table><caption>Values</caption><tr><th>Name</th><th>Count</th></tr><tr><td>A</td><td>2</td></tr></table><div data-revision>Private notes</div><div data-speech-skip>Skip</div>');
 const text=speech.extract().map((x:any)=>x.text);
 expect(text).toEqual(['Documento','Primera sección','Una frase con énfasis editorial.','Segundo párrafo.','Segunda sección','Final.','Text end.','Loose text inline.','Values','Name','Count','A','2']);
});
it('preserves native context menus for selected text, links, code and Shift',async()=>{
 await Promise.resolve();
 const send=(target:Element,shiftKey=false)=>{const e=new MouseEvent('contextmenu',{bubbles:true,cancelable:true,shiftKey});target.dispatchEvent(e);return e.defaultPrevented;};
 expect(send(document.querySelector('#a')!,true)).toBe(false);
 document.querySelector('#a')!.innerHTML='<a href="#">Link</a><code>Code</code>';
 expect(send(document.querySelector('a')!)).toBe(false);expect(send(document.querySelector('code')!)).toBe(false);
 const range=document.createRange();range.selectNodeContents(document.querySelector('#b')!);window.getSelection()!.addRange(range);expect(send(document.querySelector('#b')!)).toBe(false);
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
it('preserves exact selected offsets, bilingual inline text and selection',async()=>{
 const range=document.createRange();range.setStart(document.querySelector('#a')!.firstChild!,4);range.setEnd(document.querySelector('#b')!.firstChild!,7);
 window.getSelection()!.removeAllRanges();window.getSelection()!.addRange(range);document.dispatchEvent(new Event('selectionchange'));
 const selected=window.getSelection()!.toString();click('Leer selección');await flush();
 expect(spoken.map(x=>x.text)).toEqual(['frase con énfasis editorial.','Segundo']);expect(spoken[0].start).toBe(4);expect(spoken[1].start).toBe(0);expect(window.getSelection()!.toString()).toBe(selected);
});
it('does not autoplay and bounds chunks without breaking unicode',()=>{
 expect(spoken).toHaveLength(0);document.querySelector('#a')!.textContent='Palabras largas. '.repeat(200);
 click('Escuchar documento completo');expect(spoken.length).toBeGreaterThan(6);expect(spoken.every(x=>x.text.length<=1200)).toBe(true);expect(instance.state).toBe('pending');expect(document.querySelector('[data-speech-current]')).toBeNull();
 expect(speech.chunk('😀'.repeat(1000)).every((x:string)=>!/[\uD800-\uDBFF]$/.test(x))).toBe(true);
});
it('pauses, resumes, stops and ignores stale transport events',()=>{
 click('Escuchar documento completo');const request=startRequest().request;emit('playing');expect(document.querySelectorAll('[data-speech-current]')).toHaveLength(1);
 click('Pausar');expect(bridge.narration).toHaveBeenCalledWith({action:'pause',request});emit('paused');expect(instance.state).toBe('paused');
 click('Reanudar');expect(bridge.narration).toHaveBeenCalledWith({action:'resume',request});emit('playing');click('Detener');
 events({request,state:'playing',index:1});expect(instance.state).toBe('idle');expect(document.querySelector('[data-speech-current]')).toBeNull();
});
it('cancels on document and chapter change without restarting',()=>{
 click('Escuchar documento completo');window.dispatchEvent(new Event('pagehide'));expect(instance.state).toBe('idle');
 click('Escuchar documento completo');document.dispatchEvent(new CustomEvent('nota:pagina'));expect(instance.state).toBe('idle');
 expect(bridge.narration.mock.calls.filter(([x]:any)=>x.action==='stop')).toHaveLength(2);
});
it('shows missing provider and standalone explicitly; never invokes device speech',async()=>{
 instance.destroy();config={enabled:false,reason:'Proveedor sin configurar',voices:[]};instance=speech.mount(document.querySelector('nav'));await flush();click('Escuchar documento completo');await flush();
 expect(document.body.textContent).toContain('Proveedor sin configurar');expect(spoken).toHaveLength(0);
 instance.destroy();delete (window as any).BottifactReviewBridge;instance=speech.mount(document.querySelector('nav'));click('Escuchar documento completo');await flush();expect(document.body.textContent).toContain('Abre este documento en el portal');expect(source).not.toContain('speechSynthesis');
});
it('skips code in whole documents and reads only literal selected code',()=>{
 document.querySelector('main')!.innerHTML='<pre id="code"><code>const answer = 42;</code></pre>';click('Escuchar documento completo');expect(spoken).toHaveLength(0);
 const range=document.createRange();range.selectNodeContents(document.querySelector('code')!);window.getSelection()!.removeAllRanges();window.getSelection()!.addRange(range);document.dispatchEvent(new Event('selectionchange'));click('Leer selección');expect(spoken[0].text).toBe('const answer = 42;');
});
it('offers point and section reading by keyboard and restores tabindex',()=>{
 click('Elegir desde dónde leer');expect(document.querySelector('#a')!.getAttribute('tabindex')).toBe('0');document.querySelector('#a')!.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true,cancelable:true}));
 expect(document.querySelector('#a')!.hasAttribute('tabindex')).toBe(false);click('Leer esta sección');expect(spoken[0].text).toBe('Primera sección');expect(document.activeElement?.textContent).toBe('Detener');
 click('Detener');click('Elegir desde dónde leer');document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));expect(document.querySelector('#a')!.hasAttribute('tabindex')).toBe(false);
});
it('changes playback speed while voice and profile stay bound to consent',()=>{
 click('Escuchar documento completo');emit('playing');const speed=document.querySelector('select[aria-label=Velocidad]') as HTMLSelectElement;speed.value='1.5';speed.dispatchEvent(new Event('change'));expect(bridge.narration).toHaveBeenCalledWith({action:'rate',request:startRequest().request,rate:1.5});
 expect((document.querySelector('select[aria-label=Voz]') as HTMLSelectElement).disabled).toBe(true);click('Detener');expect((document.querySelector('select[aria-label=Voz]') as HTMLSelectElement).disabled).toBe(false);
});

it('preserves separate segments around nested blocks including selected trailing text',()=>{
 document.querySelector('main')!.innerHTML='<div id="outer">Intro<p id="inner">Middle</p>Trailing Outro</div>';
 click('Escuchar documento completo');expect(spoken.map(x=>x.text)).toEqual(['Intro','Middle','Trailing Outro']);click('Detener');spoken=[];
 const range=document.createRange();range.setStart(document.querySelector('#outer')!.lastChild!,9);range.setEnd(document.querySelector('#outer')!.lastChild!,14);window.getSelection()!.removeAllRanges();window.getSelection()!.addRange(range);document.dispatchEvent(new Event('selectionchange'));click('Leer selección');expect(spoken.map(x=>x.text)).toEqual(['Outro']);expect(spoken[0].start).toBe(9);
});

it('does not reopen narration after stopping during slow configuration',async()=>{
 instance.destroy();let resolve:any;bridge.narration.mockImplementation(()=>new Promise(r=>resolve=r));instance=speech.mount(document.querySelector('nav'));
 const pending=instance.start(speech.extract());instance.stop();resolve(config);await pending;await flush();expect(instance.state).toBe('idle');expect(spoken).toHaveLength(0);
});
