import {beforeEach,afterEach,it,expect,vi} from 'vitest';
import {readFileSync} from 'node:fs';
beforeEach(()=>{document.body.replaceChildren();HTMLDialogElement.prototype.showModal=function(){this.open=true;};HTMLDialogElement.prototype.close=function(){this.open=false;this.dispatchEvent(new Event('close'));};window.eval(readFileSync('portal/static/interface.js','utf8'));window.eval(readFileSync('portal/static/context-workbench.js','utf8'));});
afterEach(()=>vi.restoreAllMocks());
function setup(filters:any={join:'and',rules:[]}){
 const applyParams=vi.fn();const source=new URLSearchParams({view:'mine',space:'Atlas',filters:JSON.stringify(filters)});
 const tools=(window as any).BottifactContextWorkbench.create({params:()=>source,applyParams});
 return {tools,applyParams,source};
}
it('keeps filter edits local until apply, supports cancel and separated actions',async()=>{
 const {tools,applyParams,source}=setup({join:'and',rules:[{column:'space',operator:'contains',value:'Atlas'}]});await tools.filters();
 const field=document.querySelector<HTMLInputElement>('.filter-values input')!;field.value='North';field.dispatchEvent(new Event('input'));
 expect(applyParams).not.toHaveBeenCalled();expect(source.get('filters')).toContain('Atlas');
 expect(document.querySelectorAll('.filter-actions button')).toHaveLength(3);
 expect(document.querySelector('.filter-remove')!.classList.contains('bf-icon-button')).toBe(true);
 document.querySelector<HTMLButtonElement>('.filter-confirm button')!.click();
 expect(document.querySelector('dialog')).toBeNull();expect(applyParams).not.toHaveBeenCalled();
});
it('applies to the full query, preserves other facets and retains numeric zero',async()=>{
 const {tools,applyParams}=setup({join:'or',rules:[{column:'comments',operator:'eq',value:0}]});await tools.filters();
 expect(document.querySelector<HTMLInputElement>('.filter-values input')!.value).toBe('0');
 document.querySelector('form')!.dispatchEvent(new Event('submit',{cancelable:true}));await Promise.resolve();
 expect(applyParams.mock.calls[0][0].space).toBe('Atlas');
 expect(JSON.parse(applyParams.mock.calls[0][0].filters)).toEqual({join:'or',rules:[{column:'comments',operator:'eq',value:0}]});
});
it('clears draft conditions without changing the query until apply',async()=>{
 const {tools,applyParams}=setup({join:'and',rules:[{column:'title',operator:'contains',value:'Plan'}]});await tools.filters();
 document.querySelector<HTMLButtonElement>('.filter-reset')!.click();
 expect(applyParams).not.toHaveBeenCalled();expect(document.querySelectorAll('.context-rule')).toHaveLength(0);
 document.querySelector('form')!.dispatchEvent(new Event('submit',{cancelable:true}));await Promise.resolve();
 expect(applyParams.mock.calls[0][0].filters).toBe('');
});
it('rejects reversed ranges and offers typed comparisons after a field change',async()=>{
 const {tools,applyParams}=setup({join:'and',rules:[{column:'comments',operator:'between',value:9,upper:2}]});await tools.filters();
 document.querySelector('form')!.dispatchEvent(new Event('submit',{cancelable:true}));
 expect(applyParams).not.toHaveBeenCalled();expect(document.querySelectorAll<HTMLInputElement>('.filter-values input')[1].validationMessage).toContain('límite');
 const column=document.querySelector<HTMLSelectElement>('.context-rule select')!;column.value='title';column.dispatchEvent(new Event('change'));
 const operators=[...document.querySelectorAll<HTMLOptionElement>('.context-rule select')[1].options].map(o=>o.value);
 expect(operators).not.toContain('between');expect(document.activeElement).toBe(document.querySelector('.context-rule select'));
});
