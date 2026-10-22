#!/usr/bin/env python3
"""Code runtime edge cases on a contract-built fixture. Usage: probe_code.py fixture.html chromium|webkit"""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from probe_common import serve, offline

def main(html, engine):
    blocked, errors, out = [], [], {}
    with serve(Path(html)) as url, sync_playwright() as pw:
        b = getattr(pw, engine).launch()
        ctx = b.new_context(viewport={'width': 1440, 'height': 900}, permissions=['clipboard-read', 'clipboard-write'] if engine == 'chromium' else [])
        offline(ctx, blocked)
        p = ctx.new_page(); p.on('pageerror', lambda e: errors.append(str(e)))
        p.goto(url + '#uno'); p.wait_for_timeout(500)
        out['state'] = p.evaluate("""[...document.querySelectorAll('code[id^=c]')].map(c=>({id:c.id,estado:c.dataset.codigoEstado||null,lineas:c.querySelectorAll('.codigo-linea').length,
            ultima:(c.querySelector('.codigo-linea:last-child')||{}).textContent??null, marks:c.querySelectorAll('mark').length, links:c.querySelectorAll('a').length,hrefs:[...c.querySelectorAll('a')].map(a=>a.getAttribute('href')),
            label:c.closest('.codigo').querySelector('.cab').textContent}))""")
        # selection serialization of whole block vs source text
        out['selection'] = p.evaluate("""['c1','c2','c3'].map(id=>{const c=document.getElementById(id),r=document.createRange();r.selectNodeContents(c);const s=getSelection();s.removeAllRanges();s.addRange(r);return {id,same:s.toString()===c.textContent,sel:JSON.stringify(s.toString()),src:JSON.stringify(c.textContent)};})""")
        # CR handling and tokenizer through public API
        out['cr'] = p.evaluate("""(()=>{const w=document.createElement('div');w.className='codigo';w.innerHTML='<pre><code data-lenguaje="js" data-lineas></code></pre>';const c=w.querySelector('code');c.textContent='a\\r\\nb\\rc';document.getElementById('s1').append(w);NotaCodigo.init(w,{inmediato:true});return {same:c.textContent==='a\\r\\nb\\rc',lines:c.querySelectorAll('.codigo-linea').length};})()""")
        # Theme switch must not touch token DOM
        out['theme'] = p.evaluate("""(async()=>{let n=0;const mo=new MutationObserver(r=>n+=r.length);document.querySelectorAll('code[id^=c]').forEach(c=>mo.observe(c,{subtree:true,childList:true,characterData:true}));
            const root=document.documentElement;const before=getComputedStyle(document.querySelector('#c1 .kw')).color;document.querySelector('[data-elegir-modo][value=light]').click();
            await new Promise(r=>setTimeout(r,200));return {mutations:n,before,after:getComputedStyle(document.querySelector('#c1 .kw')).color,attrs:[...root.attributes].map(a=>a.name+'='+a.value).join(' ')};})()""")
        out['hidden_before'] = p.evaluate("""['c20','c30'].map(id=>({id,estado:document.getElementById(id).dataset.codigoEstado||null}))""")
        p.click('#det > summary'); p.wait_for_timeout(400)
        p.goto(url + '#dos'); p.wait_for_timeout(600)
        out['hidden_after'] = p.evaluate("""['c20','c30'].map(id=>({id,estado:document.getElementById(id).dataset.codigoEstado||null}))""")
        # Re-including runtime script and double init must not duplicate headers/buttons
        out['remount'] = p.evaluate("""(()=>{NotaCodigo.init();NotaCodigo.init();return [...document.querySelectorAll('.codigo .cab')].map(h=>h.querySelectorAll('button').length+'/'+h.querySelectorAll('.codigo-lenguaje').length)})()""")
        if engine == 'chromium':
            p.goto(url + '#uno'); p.wait_for_timeout(300)
            p.locator('#c2').scroll_into_view_if_needed()
            btn = p.locator('#c2').locator('xpath=ancestor::div[contains(@class,"codigo")]//button').first
            box = btn.bounding_box(); p.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2); p.wait_for_timeout(200)
            out['clipboard_c2'] = p.evaluate('navigator.clipboard.readText().then(t=>t===document.getElementById("c2").textContent)')
            # real keyboard copy of a mouse drag selection over 2 numbered lines
            first = p.locator('#c1 .codigo-linea').nth(0).bounding_box(); last = p.locator('#c1 .codigo-linea').nth(1).bounding_box()
            p.mouse.move(first['x'] + 40, first['y'] + 4); p.mouse.down(); p.mouse.move(last['x'] + last['width'] - 2, last['y'] + last['height'] - 3, steps=8); p.mouse.up()
            p.keyboard.press('ControlOrMeta+c'); p.wait_for_timeout(150)
            out['drag_copy'] = p.evaluate('navigator.clipboard.readText()')
        b.close()
    out['errors'], out['blocked'] = errors, blocked
    print(json.dumps(out, ensure_ascii=False, indent=1))

if __name__ == '__main__':
    main(*sys.argv[1:3])
