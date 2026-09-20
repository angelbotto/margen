import {beforeEach,afterEach,it,expect,vi} from 'vitest';
import {readFileSync} from 'node:fs';
const source=readFileSync('portal/static/reader-workspace.js','utf8');
beforeEach(()=>{HTMLDialogElement.prototype.showModal=function(){this.open=true;};window.eval(source);});
afterEach(()=>{document.body.replaceChildren();delete (HTMLDialogElement.prototype as any).showModal;vi.restoreAllMocks();});
it('never copies an in-flight prompt after feedback selection changes',async()=>{
 let resolve:any;
 const api=vi.fn(async(url:string)=>url.startsWith('/api/review/export')?{items:[{title:'Source',thread:{thread:'one',author:'Reviewer',text:'Check',anchor:{quote:'Original'},resolved:false}}]}:new Promise(r=>{resolve=r;}));
 const copy=vi.fn(),workspace=(window as any).BottifactReaderWorkspace.create({api,copy,user:()=>({verified:true,id:'owner'}),current:()=>null});
 await workspace.bundle(null);
 const button=[...document.querySelectorAll<HTMLButtonElement>('button')].find(b=>b.textContent==='Copiar para IA')!;
 button.click();await Promise.resolve();
 const checkbox=document.querySelector<HTMLInputElement>('.bundle-thread input')!;checkbox.checked=false;checkbox.dispatchEvent(new Event('change'));
 resolve({text:'Old selected feedback',count:1});await new Promise(r=>setTimeout(r,0));
 expect(copy).not.toHaveBeenCalled();
 expect(document.querySelector<HTMLTextAreaElement>('.bundle-preview textarea')!.value).toBe('');
 expect(document.querySelector('dialog>[role=status]')!.textContent).toContain('selección cambió');
});
