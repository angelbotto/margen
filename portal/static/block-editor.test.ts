import {beforeEach,afterEach,expect,it,vi} from 'vitest';
import {readFileSync} from 'node:fs';
const source=readFileSync(process.cwd()+'/portal/static/block-editor.js','utf8');
const sample=()=>({schema:'margen-blocks/1',title:'Report',regions:[{id:'region',label:'Body',blocks:[{id:'b-one',type:'paragraph',runs:[{text:'Hello',marks:[]}]},{id:'b-empty',type:'paragraph',runs:[]}]}]});
let state:any,calls:any[],editor:any;
beforeEach(()=>{vi.useFakeTimers();document.body.innerHTML='';Object.assign(HTMLDialogElement.prototype,{showModal(){this.open=true;},close(){this.open=false;}});(globalThis as any).CSS={escape:(s:string)=>s};window.eval(source);state={revision:0,base_version:'v1',source_version:'v1',document:sample(),stale:false};calls=[];});
afterEach(()=>{vi.clearAllTimers();vi.useRealTimers();});
async function start(custom?:any){
 const api=custom||vi.fn(async(path:string,options:any)=>{calls.push([path,options]);if(options?.method==='PUT'){const b=JSON.parse(options.body);state={...state,revision:state.revision+1,document:b.document};}return JSON.parse(JSON.stringify(state));});
 editor=await (window as any).MargenBlockEditor.open({api,artifact:{id:'a'}});return api;
}
function type(el:Element,text:string){el.textContent=text;el.dispatchEvent(new Event('input',{bubbles:true}));}
it('inserts a table through slash search and Enter without publishing',async()=>{
 await start();const empty=document.querySelector('[data-block="b-empty"] [contenteditable]')!;type(empty,'/');const input=document.querySelector('.be-slash input') as HTMLInputElement;expect(document.activeElement).toBe(input);input.value='tabla';input.dispatchEvent(new Event('input'));input.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}));
 expect(document.querySelector('.be-table-scroll')).not.toBeNull();expect(editor.getDocument().regions[0].blocks[1].type).toBe('table');await editor.save();expect(calls.some(c=>c[0].includes('checkpoint'))).toBe(false);
});
it('serializes concurrent saves and preserves keystrokes made during a request',async()=>{
 let release:any;let writes=0;const api=vi.fn(async(path:string,options:any)=>{if(!options)return structuredClone(state);const sent=JSON.parse(options.body);writes++;if(writes===1)await new Promise(r=>release=r);state={...state,revision:state.revision+1,document:sent.document};return structuredClone(state);});await start(api);
 type(document.querySelector('[data-block="b-one"] [contenteditable]')!,'First');const saving=editor.save();await Promise.resolve();type(document.querySelector('[data-block="b-one"] [contenteditable]')!,'Second');release();await saving;await editor.save();expect(editor.getDocument().regions[0].blocks[0].runs[0].text).toBe('Second');expect(state.document.regions[0].blocks[0].runs[0].text).toBe('Second');expect(writes).toBe(2);
});
it('retains local text and a visible unsaved state after network failure',async()=>{
 const api=vi.fn(async(_p:string,o:any)=>{if(o)throw Error('Sin conexión');return structuredClone(state);});await start(api);type(document.querySelector('[data-block="b-one"] [contenteditable]')!,'Keep this');await expect(editor.save()).rejects.toThrow('Sin conexión');expect(editor.getDocument().regions[0].blocks[0].runs[0].text).toBe('Keep this');expect(document.querySelector('.be-status')!.textContent).toBe('No guardado');expect(document.querySelector('.be-alert')!.textContent).toContain('Tu texto sigue aquí');
});
it('undoes and redoes text changes without replacing block identity',async()=>{
 await start();type(document.querySelector('[data-block="b-one"] [contenteditable]')!,'Edited');[...document.querySelectorAll('button')].find(b=>b.textContent==='Deshacer')!.click();expect(editor.getDocument().regions[0].blocks[0].runs[0].text).toBe('Hello');[...document.querySelectorAll('button')].find(b=>b.textContent==='Rehacer')!.click();expect(editor.getDocument().regions[0].blocks[0].id).toBe('b-one');expect(editor.getDocument().regions[0].blocks[0].runs[0].text).toBe('Edited');
});
it('renders untrusted block labels as text and keeps preview sandboxed',async()=>{
 state.document.regions[0].blocks.push({id:'b-opaque',type:'opaque',locked:true,label:'<img src=x onerror=alert(1)>'});await start();expect(document.querySelector('img')).toBeNull();expect(document.body.textContent).toContain('<img');[...document.querySelectorAll('button')].find(b=>b.textContent==='Vista previa')!.click();await vi.advanceTimersByTimeAsync(1);expect(document.querySelector('iframe')!.getAttribute('sandbox')).toBe('allow-scripts allow-downloads');
});
it('keeps conflicting local work until an explicit draft replacement',async()=>{
 let writes=0;const api=vi.fn(async(path:string,o:any)=>{if(o?.method==='PUT'){writes++;throw Object.assign(Error('Otra pestaña guardó'),{status:409});}if(path.endsWith('/restore'))return {...structuredClone(state),revision:4};if(path.endsWith('/editor'))return structuredClone(state);return {current_version:'v1'};});
 await start(api);type(document.querySelector('[data-block="b-one"] [contenteditable]')!,'My unsaved work');await expect(editor.save()).rejects.toThrow();expect(editor.getDocument().regions[0].blocks[0].runs[0].text).toBe('My unsaved work');
 const button=(label:string)=>[...document.querySelectorAll('button')].find(b=>b.textContent===label)!;
 expect(button('Descargar mis cambios')).toBeTruthy();button('Continuar desde la versión publicada').click();expect(api.mock.calls.some(c=>c[0].endsWith('/restore'))).toBe(false);button('Reemplazar borrador').click();await vi.advanceTimersByTimeAsync(1);
 expect(editor.getDocument().regions[0].blocks[0].runs[0].text).toBe('Hello');expect(writes).toBe(1);
});
it('freezes edits while closing waits for the final save',async()=>{
 let release:any;const api=vi.fn(async(_p:string,o:any)=>{if(!o)return structuredClone(state);await new Promise(r=>release=r);return {...state,revision:1,document:JSON.parse(o.body).document};});await start(api);type(document.querySelector('[data-block="b-one"] [contenteditable]')!,'Final text');const closing=editor.close();await Promise.resolve();expect((document.querySelector('.be-content') as HTMLElement).inert).toBe(true);release();await closing;expect(document.querySelector('.block-editor')).toBeNull();
});
