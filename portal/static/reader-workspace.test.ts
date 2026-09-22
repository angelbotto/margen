import {beforeEach,expect,it,vi} from 'vitest';
import {readFileSync} from 'node:fs';
beforeEach(()=>{document.body.innerHTML='<div id="reader-dock"></div>';localStorage.clear();window.eval(readFileSync(process.cwd()+'/portal/static/reader-workspace.js','utf8'));Object.assign(HTMLDialogElement.prototype,{showModal(){this.open=true;},close(){this.open=false;this.dispatchEvent(new Event('close'));}});});
function setup(owner=false){const share=vi.fn(),copy=vi.fn().mockResolvedValue(true),manage=vi.fn(),current={id:'a',owner:'owner',permissions:{manage:owner}};const api=vi.fn().mockResolvedValue({items:[]});const instance=(window as any).BottifactReaderWorkspace.create({api,current:()=>current,user:()=>({id:owner?'owner':'reader',verified:true}),share,copy,manage,comment:vi.fn(),refresh:vi.fn()});return {instance,share,copy,manage,api};}
it('gives readers copy-link sharing without permission management',async()=>{const {instance,share,copy}=setup();await instance.handle('action',{name:'share'});expect(share).not.toHaveBeenCalled();const b=[...document.querySelectorAll('button')].find(b=>b.textContent==='Copiar enlace')!;b.click();await Promise.resolve();expect(copy).toHaveBeenCalled();await expect(instance.handle('action',{name:'manage'})).rejects.toThrow();});
it('uses owner sharing and stores validated preferences in the account/document scope',async()=>{const {instance,share}=setup(true);await instance.handle('action',{name:'share'});expect(share).toHaveBeenCalledWith('a');await instance.handle('preferences',{theme:'linear',mode:'dark',sound:true,volume:.4,token:'not-a-preference'});expect(JSON.parse(localStorage.getItem('bottifact-reader:owner:a')!)).toEqual({theme:'linear',mode:'dark',sound:true,volume:.4});});
it('renders reader activity without inventing missing uniques or interpreting names as HTML',async()=>{
  const {instance,api}=setup(true);
  api.mockResolvedValue({visible:true,owner:true,shared:false,enabled:true,views:12,visitors:null,source:'margen',since:'2026-09-01',until:'2026-09-30',comments:1,messages:2,participant_count:1,participants:[{name:'<img src=x onerror=alert(1)>',verified:false}]});
  await instance.handle('action',{name:'activity'});
  expect(document.querySelectorAll('.activity-metrics dd')[1].textContent).toBe('—');
  expect(document.querySelector('.activity-people img')).toBeNull();
  expect(document.querySelector('.activity-people')!.textContent).toContain('<img');
  expect(document.querySelector('input[type=checkbox]')).not.toBeNull();
});
it('does not show owner controls or hidden activity to readers',async()=>{
  const {instance,api}=setup(); api.mockResolvedValue({visible:false});
  await instance.handle('action',{name:'activity'});
  expect(document.querySelector('.activity-metrics')).toBeNull();
  expect(document.querySelector('input[type=checkbox]')).toBeNull();
  expect(document.body.textContent).toContain('no ha compartido');
});
