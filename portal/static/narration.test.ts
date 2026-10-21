import {afterEach,beforeEach,expect,it,vi} from 'vitest';
import {readFileSync} from 'node:fs';
const source=readFileSync('portal/static/narration.js','utf8');
let api:any,controller:any,events:any[],audio:any,binding:any;
const config={enabled:true,provider:'Synthetic',voices:[{id:'test',label:'Synthetic voice'}],profiles:[{id:'report',label:'Informe'}]};
const manifest={sha:'sha',blocks:[{id:'b1',text:'Texto 😀 bilingüe.',anchors:['first']}]};
const input=()=>({action:'start',request:'request-1',voice:'test',profile:'report',rate:1,items:[{fullText:'Texto 😀 bilingüe.',text:'😀 bilingüe.',start:6,anchor:'first'}]});
const flush=async()=>{for(let i=0;i<30;i++)await Promise.resolve();};
const approve=async()=>{(document.querySelector('.narration-consent button:last-child') as HTMLButtonElement).click();await flush();};
beforeEach(()=>{
 vi.useFakeTimers();window.eval(source);events=[];binding={artifact:'a',version:'v'};
 HTMLDialogElement.prototype.showModal=function(){this.setAttribute('open','');};HTMLDialogElement.prototype.close=function(){this.removeAttribute('open');};
 audio=document.createElement('audio');audio.play=vi.fn(async()=>audio.onplaying?.());audio.pause=vi.fn();audio.load=vi.fn();
 api=vi.fn(async(path:string,options:any)=>{
  if(path.includes('/status/'))return {state:'complete'};
  if(path.endsWith('/blocks/0'))return {url:'/api/artifacts/a/narration/sessions/s/audio/0',pause_ms:300};
  if(path.endsWith('/sessions')&&options?.method==='POST')return {id:'s'};
  if(path.includes('/manifest?'))return manifest;
  if(path.includes('?version='))return config;
  return {ok:true};
 });
 controller=(window as any).MargenNarration.create({api,binding:()=>binding,emit:(x:any)=>events.push(x),audioFactory:()=>audio});
});
afterEach(()=>{controller.stop();document.body.replaceChildren();vi.clearAllTimers();vi.useRealTimers();});
it('requires trusted portal confirmation before session/provider work and exact unicode offsets',async()=>{
 await controller.handle(input());expect(api.mock.calls.some(([p]:any)=>p.endsWith('/sessions'))).toBe(false);expect(audio.play).not.toHaveBeenCalled();expect(document.querySelector('pre')?.textContent).toBe('😀 bilingüe.');
 await approve();const body=JSON.parse(api.mock.calls.find(([p]:any)=>p.endsWith('/sessions'))[1].body);expect(body.blocks).toEqual([{id:'b1',start:6,end:17}]);expect(body.sha).toBe('sha');expect(audio.play).toHaveBeenCalledOnce();expect(events.at(-1).state).toBe('playing');
});
it('rejects injected or ambiguous text without creating a session',async()=>{
 const bad=input();bad.items[0].text='Invented';await expect(controller.handle(bad)).rejects.toThrow('vincular');expect(document.querySelector('dialog')).toBeNull();
 const map=(window as any).MargenNarration.references;expect(()=>map(input().items,{blocks:[manifest.blocks[0],manifest.blocks[0]]})).toThrow('vincular');
});
it('cancels a pending consent on navigation and ignores stale manifest',async()=>{
 let resolve:any;api.mockImplementation((p:string)=>p.includes('/manifest?')?new Promise(r=>resolve=r):Promise.resolve(config));
 const start=controller.handle(input());await flush();controller.stop();binding.version='new';resolve(manifest);await start;expect(document.querySelector('dialog')).toBeNull();expect(audio.play).not.toHaveBeenCalled();
});
it('deletes a session that finishes opening after navigation',async()=>{
 await controller.handle(input());let resolve:any;const original=api.getMockImplementation();api.mockImplementation((p:string,o:any)=>p.endsWith('/sessions')?new Promise(r=>resolve=r):original(p,o));
 const pending=approve();await flush();controller.stop();binding.version='new';resolve({id:'late'});await pending;
 expect(api).toHaveBeenCalledWith('/api/artifacts/a/narration/sessions/late',{method:'DELETE'});expect(audio.play).not.toHaveBeenCalled();
});
it('pauses/resumes, changes speed, cancels and ignores stale audio events',async()=>{
 await controller.handle(input());await approve();await controller.handle({action:'pause',request:'request-1'});expect(events.at(-1).state).toBe('paused');expect(audio.pause).toHaveBeenCalled();
 await controller.handle({action:'resume',request:'request-1'});await controller.handle({action:'rate',request:'request-1',rate:1.5});expect(audio.playbackRate).toBe(1.5);
 const stale=audio.onplaying;controller.stop();stale();expect(api).toHaveBeenCalledWith('/api/artifacts/a/narration/sessions/s',{method:'DELETE'});expect(audio.getAttribute('src')).toBeNull();
});
it('refuses to advance when media ended after an incomplete stream',async()=>{
 await controller.handle(input());await approve();const original=api.getMockImplementation();api.mockImplementation((p:string,o:any)=>p.includes('/status/')?Promise.resolve({state:'failed'}):original(p,o));
 await audio.onended();await flush();expect(events.at(-1).state).toBe('error');expect(events.at(-1).message).toContain('interrumpió');expect(audio.getAttribute('src')).toBeNull();
});
it('ends only after backend confirms integrity and respects pause between blocks',async()=>{
 await controller.handle(input());await approve();await audio.onended();await controller.handle({action:'pause',request:'request-1'});await vi.advanceTimersByTimeAsync(400);expect(events.at(-1).state).toBe('paused');
 await controller.handle({action:'resume',request:'request-1'});await flush();expect(events.at(-1).state).toBe('ended');
});
it('missing configuration reports explicitly without dialog or local fallback',async()=>{
 api.mockResolvedValue({enabled:false,reason:'Falta proveedor'});await expect(controller.handle(input())).rejects.toThrow('Falta proveedor');expect(document.querySelector('dialog')).toBeNull();expect(audio.play).not.toHaveBeenCalled();
});

it('ignores a stale play rejection without cancelling a later consent',async()=>{
 await controller.handle(input());await approve();let reject:any;audio.play=vi.fn(()=>new Promise((_,r)=>reject=r));await controller.handle({action:'resume',request:'request-1'});controller.stop();await controller.handle({...input(),request:'request-2'});
 reject(new DOMException('stopped','AbortError'));await flush();expect(document.querySelector('dialog[open]')).not.toBeNull();
});
it('keeps a pause during pending play recoverable',async()=>{
 let reject:any;audio.play=vi.fn(()=>new Promise((_,r)=>reject=r));await controller.handle(input());await approve();await controller.handle({action:'pause',request:'request-1'});
 reject(new DOMException('paused','AbortError'));await flush();expect(events.at(-1).state).toBe('paused');expect(audio.getAttribute('src')).not.toBeNull();
 audio.play=vi.fn(async()=>audio.onplaying());await controller.handle({action:'resume',request:'request-1'});expect(events.at(-1).state).toBe('playing');
});

it('accepts a unique persisted block after review assigns a runtime-only anchor',()=>{
 const items=input().items;items[0].anchor='nota-revision-bloque-1';const refs=(window as any).MargenNarration.references(items,manifest);expect(refs[0].id).toBe('b1');
});
