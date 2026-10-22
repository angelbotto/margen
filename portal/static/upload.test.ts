import {beforeEach, expect, it, vi} from 'vitest';
import {readFileSync} from 'node:fs';
beforeEach(() => {
  const source = readFileSync('portal/static/index.html','utf8');
  document.body.innerHTML = source.slice(source.indexOf('<dialog id="upload-dialog"'), source.indexOf('</dialog>',source.indexOf('<dialog id="upload-dialog"')) + 9);
  Object.assign(HTMLDialogElement.prototype,{showModal(){this.open=true;},close(){this.open=false;this.dispatchEvent(new Event('close'));}});
  window.eval(readFileSync('portal/static/upload.js','utf8'));
});
function setup() {
  const api = vi.fn().mockResolvedValue({kind:'html',title:'A document',files:[],warnings:[]}), navigate = vi.fn();
  const ui = (window as any).MargenUpload.create({api,navigate}); ui.open();
  return {api,navigate,ui};
}
function select(name='plain.html', text='<h1>Own HTML</h1>') {
  const input = document.querySelector('input[name=file]')!;
  Object.defineProperty(input,'files',{value:[new File([text],name)],configurable:true}); input.dispatchEvent(new Event('change'));
}
const submit = () => document.querySelector('form')!.dispatchEvent(new Event('submit',{cancelable:true}));
it('inspects before publishing and never inserts uploaded markup into account DOM',async () => {
  const {api,navigate} = setup(); select('plain.html','<img id="evil" src=x onerror=alert(1)>');
  await vi.waitFor(() => expect((document.querySelector('[type=submit]') as HTMLButtonElement).disabled).toBe(false));
  expect(api).toHaveBeenCalledTimes(1); expect(api.mock.calls[0][0]).toBe('/api/uploads/inspect'); expect(document.querySelector('#evil')).toBeNull();
  api.mockResolvedValueOnce({id:'artifact',version:'v',state:'published'}); submit();
  await vi.waitFor(() => expect(navigate).toHaveBeenCalledWith('/a/artifact'));
  const body=JSON.parse(api.mock.calls[1][1].body); expect(body.name).toBe('plain.html'); expect(body.visibility).toBeUndefined(); expect(body.data).toBeTruthy();
});
it('does not accept stale inspection after another file replaces it',async () => {
  const {api} = setup(); let done:any;
  api.mockImplementationOnce(() => new Promise(resolve => done=resolve)); select();
  await vi.waitFor(() => expect(api).toHaveBeenCalledOnce());
  select('script.exe'); done({kind:'html',title:'Old',files:[],warnings:[]}); await new Promise(resolve => setTimeout(resolve,20));
  expect((document.querySelector('[type=submit]') as HTMLButtonElement).disabled).toBe(true);
  expect(document.querySelector('[data-upload-report]')!.hasAttribute('hidden')).toBe(true); submit(); expect(api).toHaveBeenCalledOnce();
});
it('keeps revision identity and sends the current version as a conflict guard',async () => {
  const {api,ui,navigate}=setup(); ui.open({id:'existing',current_version:'base',title:'Original',space:'Team'}); select();
  await vi.waitFor(() => expect((document.querySelector('[type=submit]') as HTMLButtonElement).disabled).toBe(false));
  api.mockResolvedValueOnce({id:'existing',version:'draft1',state:'draft'}); submit();
  await vi.waitFor(() => expect(navigate).toHaveBeenCalledWith('/a/existing?version=draft1'));
  expect(JSON.parse(api.mock.calls[1][1].body)).toMatchObject({artifact:'existing',expected_current:'base',title:'Original',mode:'draft'});
});
it('uses text for filenames and inspection warnings and blocks double submission',async () => {
  const {api}=setup(); api.mockResolvedValueOnce({kind:'zip',title:'Page',files:[{path:'<img src=x>',size:1},{path:'style.css',size:1}],warnings:['<img id=warning src=x>']}); select('site.zip');
  await vi.waitFor(() => expect((document.querySelector('[type=submit]') as HTMLButtonElement).disabled).toBe(false));
  expect(document.querySelectorAll('.upload-report img').length).toBe(0);
  api.mockImplementationOnce(() => new Promise(()=>{})); submit(); submit(); expect(api).toHaveBeenCalledTimes(2);
});
it('closing clears an in-flight inspection and keyboard selection remains available',async () => {
  const {api}=setup(); let done:any; api.mockImplementationOnce(() => new Promise(resolve => done=resolve)); select();
  await vi.waitFor(() => expect(api).toHaveBeenCalledOnce()); (document.querySelector('dialog') as HTMLDialogElement).close();
  done({kind:'html',title:'Late',files:[],warnings:[]}); await Promise.resolve();
  expect(document.querySelector('[data-upload-report]')!.hasAttribute('hidden')).toBe(true);
  expect(document.querySelector('input[type=file]')!.getAttribute('aria-label')).toContain('HTML');
});
it('rejects a file and original whose encoded body exceeds the portal limit before sending',async () => {
  const {api}=setup(); select();
  await vi.waitFor(() => expect((document.querySelector('[type=submit]') as HTMLButtonElement).disabled).toBe(false));
  const original = document.querySelector('input[name=original]')!, big = new File(['%PDF-'],'original.pdf');
  Object.defineProperty(big,'size',{value:11.5 * 1024 * 1024});
  const file = document.querySelector('input[name=file]') as HTMLInputElement;
  Object.defineProperty(file.files![0],'size',{value:10 * 1024 * 1024});
  Object.defineProperty(original,'files',{value:[big],configurable:true}); original.dispatchEvent(new Event('change'));
  expect(document.querySelector('.form-error')!.textContent).toMatch(/juntos ocupan 21\.5 MB.*hasta 16\.5 MB.*Quita el original/);
  submit(); await new Promise(resolve => setTimeout(resolve,20));
  expect(api).toHaveBeenCalledOnce(); expect(document.querySelector('.form-error')!.textContent).toContain('Quita el original');
});
