import {beforeEach, afterEach, expect, it, vi} from 'vitest';
import {readFileSync} from 'node:fs';
const source=readFileSync('packages/core/components/review.js','utf8');
const markup=readFileSync('packages/core/recipes/review/example.html','utf8');
let instance:any;
beforeEach(()=>{
  localStorage.clear();
  document.body.innerHTML='<main><section id="evidence"><h2>Evidence</h2><p id="claim">Three deliveries need review.</p></section>'+markup+'</main>';
  Object.defineProperty(window,'visualViewport',{configurable:true,value:null});
  vi.stubGlobal('ResizeObserver',class {observe(){} disconnect(){}});
  HTMLElement.prototype.scrollIntoView=vi.fn();
  HTMLDialogElement.prototype.show=function(){this.open=true;};
  HTMLDialogElement.prototype.showModal=function(){this.open=true;};
  HTMLDialogElement.prototype.close=function(){this.open=false;};
  vi.spyOn(HTMLElement.prototype,'getClientRects').mockReturnValue([{x:0,y:0,left:0,right:100,top:0,bottom:20,width:100,height:20,toJSON(){return {};}}] as any);
  delete (window as any).BottifactReviewBridge;
});
afterEach(()=>{instance?.destroy();instance=null;vi.unstubAllGlobals();vi.restoreAllMocks();});
function mount(){window.eval(source);instance=(window as any).NotaRevision.get(document.querySelector('[data-revision]'));}
function open(){(document.querySelector('[data-revision-modo]') as HTMLElement).click();(document.querySelector('#claim') as HTMLElement).click();}
it('keeps metadata optional and preserves note type, session and source context when saving',async()=>{
  mount();open();
  const editor=document.querySelector('[data-revision-editor]') as HTMLDialogElement;
  expect(editor.open).toBe(true);
  expect((editor.querySelector('.review-composer-options') as HTMLDetailsElement).open).toBe(false);
  const type=editor.querySelector('select') as HTMLSelectElement;type.value='note';type.dispatchEvent(new Event('change'));
  const session=editor.querySelector('.revision-session input') as HTMLInputElement;session.value='session-42';
  const draft=editor.querySelector('textarea')!;draft.value='Check the exception source.';
  draft.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',ctrlKey:true,bubbles:true}));
  await vi.waitFor(()=>expect(editor.open).toBe(false));
  const event=instance.exportData().events[0];
  expect(event).toMatchObject({entry_type:'note',session:'session-42',text:'Check the exception source.',anchor:{reference:'claim',text:'Three deliveries need review.'}});
  (document.querySelector('.revision-marca') as HTMLElement).click();
  expect(type.disabled).toBe(true);expect(session.disabled).toBe(true);
  expect(draft.value).toBe('Check the exception source.');
});
it('retains a failed shared draft and its context for retry',async()=>{
  const commit=vi.fn().mockRejectedValue(new Error('Connection unavailable'));
  (window as any).BottifactReviewBridge={commit,subscribe:(fn:any)=>{fn({author:'Reviewer',actor:'r',verified:true,permissions:{comment:true,edit:true},snapshot:{format:'nota-revision',version:2,document:document.title+'@'+location.pathname,events:[]}});return ()=>{};}};
  mount();open();
  const editor=document.querySelector('[data-revision-editor]') as HTMLDialogElement;
  const draft=editor.querySelector('textarea')!;draft.value='Keep this draft.';
  draft.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',ctrlKey:true,bubbles:true}));
  await vi.waitFor(()=>expect(commit).toHaveBeenCalledOnce());
  expect(editor.open).toBe(true);expect(draft.value).toBe('Keep this draft.');
  expect(document.querySelector('[data-revision-estado]')?.textContent).toContain('Connection unavailable');
});
it('can be destroyed and mounted again without losing original controls or duplicating the composer',()=>{
  mount();instance.destroy();
  instance=(window as any).NotaRevision.init()[0];open();
  expect(document.querySelectorAll('.review-composer-header')).toHaveLength(1);
  expect(document.querySelectorAll('.review-composer-options')).toHaveLength(1);
  expect(document.querySelectorAll('[data-revision-cancelar]')).toHaveLength(1);
  expect((document.querySelector('[data-revision-editor]') as HTMLDialogElement).open).toBe(true);
});
it('groups overlapping pins without losing any thread and publishes the open count',async()=>{
 const counts:number[]=[];const receive=(e:any)=>counts.push(e.detail.open);document.addEventListener('bottifact:review-count',receive);
 mount();
 for(const text of ['First point','Second point']){
  open();const editor=document.querySelector('[data-revision-editor]') as HTMLDialogElement;
  const draft=editor.querySelector('textarea')!;draft.value=text;draft.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',ctrlKey:true,bubbles:true}));
  await vi.waitFor(()=>expect(editor.open).toBe(false));
 }
 // Position inside the visible page (jsdom otherwise has a zero-sized viewport rect).
 const claim=document.querySelector('#claim') as HTMLElement;
 claim.getBoundingClientRect=()=>({x:100,y:100,left:100,right:300,top:100,bottom:200,width:200,height:100,toJSON(){return {};}});
 window.dispatchEvent(new Event('resize'));
 const pins=[...document.querySelectorAll('.revision-marca')].filter(n=>!(n as HTMLElement).hidden);
 expect(pins).toHaveLength(1);expect(pins[0].textContent).toBe('2');
 (pins[0] as HTMLElement).click();expect(document.querySelectorAll('.revision-hilo')).toHaveLength(2);
 expect(counts.at(-1)).toBe(2);
 document.removeEventListener('bottifact:review-count',receive);
});

it.each([
 ['image','<img id="surface" alt="Delivery exception evidence" src="data:image/svg+xml,%3Csvg/%3E">','IMG','Delivery exception evidence'],
 ['cell','<table><tbody><tr><td id="surface">Delivered · 12 packages</td></tr></tbody></table>','TD','Delivered · 12 packages'],
 ['chart','<svg id="surface" aria-label="Volume by week"><path d="M0 0h10"/></svg>','svg','Volume by week'],
 ['card','<div id="surface">Nested detail card</div>','DIV','Nested detail card'],
 ['canvas','<canvas id="surface" aria-label="Fleet positions"></canvas>','CANVAS','Fleet positions'],
])('anchors a comment to the %s itself and restores it after remount',async(_name,html,tag,text)=>{
 document.querySelector('#evidence')!.insertAdjacentHTML('beforeend',html);mount();
 (document.querySelector('[data-revision-modo]') as HTMLElement).click();
 const surface=document.querySelector('#surface')!;
 surface.getClientRects=()=>[{width:100,height:100}] as any;
 surface.getBoundingClientRect=()=>({left:20,top:30,width:100,height:100,right:120,bottom:130,x:20,y:30,toJSON(){return {};}});
 (surface.querySelector('path')||surface).dispatchEvent(new MouseEvent('click',{bubbles:true,clientX:45,clientY:105}));
 const editor=document.querySelector('[data-revision-editor]') as HTMLDialogElement;expect(editor.open).toBe(true);
 const draft=editor.querySelector('textarea')!;draft.value='Review this exact surface.';
 draft.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',ctrlKey:true,bubbles:true}));await vi.waitFor(()=>expect(editor.open).toBe(false));
 expect(instance.exportData().events[0].anchor).toMatchObject({reference:'surface',tag,text,quote:text,x:.25,y:.75});
 instance.destroy();instance=(window as any).NotaRevision.init()[0];
 expect(document.querySelector('.revision-hilo')?.textContent).not.toContain('El bloque cambió');
 expect(document.querySelector('.revision-hilo a')?.getAttribute('href')).toBe('#surface');
});
it('offers a contextual action on content while keeping native link, selection and form menus',()=>{
 document.querySelector('#evidence')!.insertAdjacentHTML('beforeend','<a id="link" href="#">Link</a><input id="field">');mount();
 const event=new MouseEvent('contextmenu',{bubbles:true,cancelable:true,clientX:30,clientY:40});document.querySelector('#claim')!.dispatchEvent(event);
 expect(event.defaultPrevented).toBe(true);expect((document.querySelector('.review-context-menu') as HTMLElement).hidden).toBe(false);
 (document.querySelector('.review-context-menu button') as HTMLElement).click();expect((document.querySelector('[data-revision-editor]') as HTMLDialogElement).open).toBe(true);
 for(const id of ['link','field']){const native=new MouseEvent('contextmenu',{bubbles:true,cancelable:true});document.getElementById(id)!.dispatchEvent(native);expect(native.defaultPrevented).toBe(false);}
 const shifted=new MouseEvent('contextmenu',{bubbles:true,cancelable:true,shiftKey:true});document.querySelector('#claim')!.dispatchEvent(shifted);expect(shifted.defaultPrevented).toBe(false);
});
it('does not offer context creation before permissions arrive or to an unverified read-only reader',()=>{
 let receive:any;(window as any).BottifactReviewBridge={subscribe:(fn:any)=>{receive=fn;return ()=>{};},identify:vi.fn()};mount();
 function check(){const event=new MouseEvent('contextmenu',{bubbles:true,cancelable:true});document.querySelector('#claim')!.dispatchEvent(event);expect(event.defaultPrevented).toBe(false);}
 check();receive({author:'Guest',verified:false,permissions:{comment:false},snapshot:instance.exportData()});check();
});
it('supports the keyboard context menu and restores focus on Escape',()=>{
 mount();const target=document.querySelector('#claim') as HTMLElement;target.tabIndex=0;target.focus();
 target.dispatchEvent(new KeyboardEvent('keydown',{key:'F10',shiftKey:true,bubbles:true,cancelable:true}));
 expect(document.activeElement).toBe(document.querySelector('.review-context-menu button'));
 document.activeElement!.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));
 expect((document.querySelector('.review-context-menu') as HTMLElement).hidden).toBe(true);expect(document.activeElement).toBe(target);
});
it('names the recorded author, not the viewer, on shared threads and agent entries',()=>{
  const doc=document.title+'@'+location.pathname,anchor={reference:'claim',tag:'P',text:'Three deliveries need review.',quote:'Three',page:'Doc',x:.5,y:.5};
  const events=[{id:'a1',thread:'a1',kind:'create',author:'Alice Ruiz',actor:'alice',verified:true,time:1,version:'v',text:'Alice point',entry_type:'comment',anchor},
    {id:'b1',thread:'a1',kind:'reply',author:'Bob Pérez',actor:'bob',verified:true,time:2,version:'v',text:'Bob reply'},
    {id:'g1',thread:'g1',kind:'create',author:'Ángel Botto',actor:'owner',verified:true,agent:'Codex',time:3,version:'v',text:'Agent point',entry_type:'comment',anchor:{...anchor,x:.9}}];
  (window as any).BottifactReviewBridge={commit:vi.fn(),subscribe:(fn:any)=>{fn({author:'Ángel Botto',actor:'owner',verified:true,permissions:{comment:true,edit:true},snapshot:{format:'nota-revision',version:2,document:doc,events}});return ()=>{};}};
  mount();
  const editor=document.querySelector('[data-revision-editor]') as HTMLDialogElement,panel=document.querySelector('[data-revision-panel]') as HTMLDialogElement;
  (document.querySelector('.revision-marca') as HTMLElement).click();
  expect(editor.open).toBe(false);expect(panel.open).toBe(true);
  const rows=[...document.querySelectorAll('[data-revision-notas] > li')];
  const alice=rows.find(li=>li.textContent!.includes('Alice point'))!,agent=rows.find(li=>li.textContent!.includes('Agent point'))!;
  expect(alice.querySelector('.revision-meta')!.textContent).toMatch(/^Alice Ruiz · correo verificado/);
  expect(alice.querySelector('.revision-respuestas')!.textContent).toBe('Bob Pérez · correo verificado: Bob reply');
  expect(agent.querySelector('.revision-meta')!.textContent).toMatch(/^Codex \(agente de Ángel Botto\) · conexión de agente/);
  expect([...alice.querySelectorAll('button')].find(b=>b.textContent==='Editar')).toBeUndefined();
  ([...agent.querySelectorAll('button')].find(b=>b.textContent==='Editar') as HTMLElement).click();
  expect(editor.open).toBe(true);
  expect(document.querySelector('.review-composer-name')!.textContent).toBe('Ángel Botto');
  editor.close();open();
  expect(document.querySelector('.review-composer-name')!.textContent).toBe('Ángel Botto');
  expect(document.querySelector('[data-revision-prompt]')!.textContent).toContain('Autor: Codex (agente de Ángel Botto)');
});

it('validates imported agent labels and keeps local identity explicitly declared',()=>{
 mount();open();
 const input=document.querySelector('[data-revision-texto]') as HTMLTextAreaElement;input.value='Local note';
 input.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',ctrlKey:true,bubbles:true}));
 const original=instance.exportData().events[0],validate=(window as any).NotaRevisionStore.validate;
 for(const agent of [4,{},'','x'.repeat(81)])expect(()=>validate({...original,agent})).toThrow('Identidad de agente inválida');
 expect(validate({...original,agent:'Analista ñ'}).agent).toBe('Analista ñ');
});

it('limits Edit to the thread author and displays the provenance of the current text',()=>{
 const doc=document.title+'@'+location.pathname,anchor={reference:'claim',tag:'P',text:'Three deliveries need review.',quote:'Three',page:'Doc',x:.5,y:.5};
 const events=[{id:'alice-note',thread:'alice-note',kind:'create',author:'Alice',actor:'alice',verified:true,time:1,text:'Original',anchor},
 {id:'agent-edit',thread:'alice-note',kind:'edit',author:'Alice',actor:'alice',agent:'Codex',verified:true,time:2,text:'Agent revision'}];
 (window as any).BottifactReviewBridge={subscribe:(fn:any)=>{fn({author:'Owner',actor:'owner',verified:true,permissions:{comment:true,edit:true},snapshot:{format:'nota-revision',version:2,document:doc,events}});return ()=>{};}};
 mount();
 const row=document.querySelector('.revision-hilo')!;
 expect(row.textContent).toContain('Última edición: Codex (agente de Alice)');
 expect(row.textContent).toContain('Agent revision');
 expect([...row.querySelectorAll('button')].some(b=>b.textContent==='Editar')).toBe(false);
 expect([...row.querySelectorAll('button')].some(b=>b.textContent==='Resolver')).toBe(true);
});
