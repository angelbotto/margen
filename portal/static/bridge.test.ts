import {expect,it,vi} from 'vitest';
import {readFileSync} from 'node:fs';
it('waits for a point instead of attaching a legacy comment to the heading, and lets Escape cancel',()=>{
 vi.useFakeTimers();
 document.body.innerHTML='<main id="content"><h1>Document title</h1><p id="evidence">Actual evidence</p></main>';
 const post=vi.spyOn(window.parent,'postMessage').mockImplementation(()=>{});
 window.eval(readFileSync('portal/static/bridge.js','utf8'));
 const request=()=>window.dispatchEvent(new MessageEvent('message',{source:window.parent,data:{bottifact:1,op:'capture-context'}}));
 const contexts=()=>post.mock.calls.map(call=>call[0] as any).filter(message=>message.op==='context');
 request();expect(contexts()).toHaveLength(0);expect(document.querySelector('[data-host-point-picker]')).not.toBeNull();
 document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));
 document.querySelector('#evidence')!.dispatchEvent(new MouseEvent('click',{bubbles:true}));expect(contexts()).toHaveLength(0);
 request();document.querySelector('#evidence')!.dispatchEvent(new MouseEvent('click',{bubbles:true,clientX:24,clientY:42}));
 expect(contexts()).toHaveLength(1);expect(contexts()[0].data).toMatchObject({reference:'evidence',tag:'P',text:'Actual evidence'});
 expect(document.querySelector('[data-host-point-picker]')).toBeNull();
 const message=contexts()[0];window.dispatchEvent(new MessageEvent('message',{source:window.parent,data:{bottifact:1,id:message.id,data:{ok:true}}}));
 post.mockRestore();vi.clearAllTimers();vi.useRealTimers();
 // Only a marked message from the parent can stop speech.

 const stop=vi.fn();(window as any).MargenSpeech={stop};
 window.dispatchEvent(new MessageEvent('message',{source:null,data:{bottifact:1,op:'stop-speech'}}));
 window.dispatchEvent(new MessageEvent('message',{source:window.parent,data:{op:'stop-speech'}}));
 expect(stop).not.toHaveBeenCalled();
 window.dispatchEvent(new MessageEvent('message',{source:window.parent,data:{bottifact:1,op:'stop-speech'}}));
 expect(stop).toHaveBeenCalledOnce();delete (window as any).MargenSpeech;
});
