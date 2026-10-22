import {beforeEach, expect, it} from 'vitest';
import {readFileSync} from 'node:fs';

beforeEach(()=>{document.body.replaceChildren();window.eval(readFileSync('portal/static/review-identity.js','utf8'));});

it('keeps a guest name separate from the recorded trust marker',()=>{
 const identity=(window as any).MargenReviewIdentity;
 document.body.append(identity.element('p',{author:'Codex (agente de Propietaria)',verified:false}),identity.element('p',{author:'Propietaria',agent:'Codex',verified:true}));
 const rows=[...document.querySelectorAll('p')];
 expect(rows[0].querySelector('bdi')!.textContent).toBe(rows[1].querySelector('bdi')!.textContent);
 expect(rows[0].querySelector('[data-review-identity-kind=guest]')!.textContent).toBe('invitado');
 expect(rows[1].querySelector('[data-review-identity-kind=agent]')!.textContent).toBe('conexión de agente');
});

it('renders hostile names as isolated, single-line text without changing the event',()=>{
 const event={author:'Alice\n\u202e<img src=x onerror=alert(1)>',agent:'Bot\u2066',verified:true};
 const original=JSON.stringify(event),identity=(window as any).MargenReviewIdentity;
 document.body.append(identity.element('p',event));
 expect(document.querySelector('img')).toBeNull();
 expect(document.querySelector('bdi')!.textContent).toBe('Bot (agente de Alice <img src=x onerror=alert(1)>)');
 expect(JSON.stringify(event)).toBe(original);
 expect(identity.kind({author:'Historical'})).toBe('verificación no registrada');
});
