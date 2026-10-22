"""Independent Chromium probe of the real review.js against a fake portal bridge (run_d4fd3704f129)."""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

root = Path(sys.argv[1]); source = (root / 'packages/core/components/review.js').read_text()
markup = (root / 'packages/core/recipes/review/example.html').read_text()
PAGE = '<!doctype html><html><head><meta charset="utf-8"><title>Doc</title></head><body><main><section id="evidence"><h2>Evidence</h2><p id="claim">Three deliveries need review.</p><p id="other">Second claim.</p></section>' + markup + '</main></body></html>'
anchor = {'reference': 'claim', 'tag': 'P', 'text': 'Three deliveries need review.', 'quote': 'Three', 'page': 'Doc', 'x': .3, 'y': .3}
anchor2 = {**anchor, 'reference': 'other', 'text': 'Second claim.', 'quote': 'Second', 'x': .7}
anchor3 = {**anchor, 'x': .9}
EVENTS = [
  {'id': 'a1', 'thread': 'a1', 'kind': 'create', 'author': 'Alice Ruiz', 'actor': 'alice', 'verified': True, 'time': 1, 'version': 'v', 'text': 'Alice point', 'entry_type': 'comment', 'anchor': anchor},
  {'id': 'b1', 'thread': 'a1', 'kind': 'reply', 'author': 'Bob Pérez', 'actor': 'bob', 'verified': True, 'time': 2, 'version': 'v', 'text': 'Bob reply'},
  {'id': 'g1', 'thread': 'g1', 'kind': 'create', 'author': 'Ángel Botto', 'actor': 'owner', 'verified': True, 'agent': '<img src=x onerror=window.__xss=1>', 'time': 3, 'version': 'v', 'text': 'Agent point', 'entry_type': 'comment', 'anchor': anchor2},
  {'id': 'o1', 'thread': 'o1', 'kind': 'create', 'author': 'Bob Pérez', 'actor': 'bob', 'verified': True, 'time': 4, 'version': 'v', 'text': 'Bob own point', 'entry_type': 'comment', 'anchor': anchor3},
  {'id': 'h1', 'thread': 'h1', 'kind': 'create', 'author': 'Ángel Botto', 'actor': 'owner', 'verified': True, 'time': 5, 'version': 'v', 'text': 'Historic token entry', 'entry_type': 'comment', 'anchor': anchor2},
]
BRIDGE = '''
window.__commits=[];const doc=document.title+'@'+location.pathname;let state=%s,fns=new Set();const me=%s;
const snap=()=>({...me,snapshot:{format:'nota-revision',version:2,document:doc,events:state}});
window.BottifactReviewBridge={commit:async d=>{window.__commits.push(d);const e={id:d.id||crypto.randomUUID(),thread:d.thread||d.id,kind:d.kind,author:me.author,actor:me.actor,verified:true,time:100+state.length,version:'v'};if(d.text)e.text=d.text;if(d.kind==='create'){e.anchor=d.anchor;e.entry_type=d.entry_type;e.thread=e.id;}state=[...state,e];return snap();},
 subscribe:fn=>{fns.add(fn);fn(snap());return()=>fns.delete(fn);},identify(){},exportPrompt(){}};
'''
results = []
def check(name, ok, detail=''): results.append({'check': name, 'ok': bool(ok), 'detail': detail})

def serve(page, html):
    page.unroute('**/*'); page.route('**/*', lambda route: route.fulfill(status=200, content_type='text/html', body=html))
    page.goto('http://localhost:8799/doc.html')

def load(page, me):
    html = PAGE.replace('<main>', '<script>' + BRIDGE % (json.dumps(EVENTS), json.dumps(me)) + '</script><main>').replace('</body>', '<script>' + source.replace('</script', '<\\/script') + '</script></body>')
    serve(page, html)
    page.wait_for_selector('.revision-marca', state='attached')

def rows(page):
    return page.eval_on_selector_all('[data-revision-notas] > li', 'ls=>ls.map(li=>({thread:li.dataset.thread,meta:li.querySelector(".revision-meta")?.textContent,replies:li.querySelector(".revision-respuestas")?.textContent||"",buttons:[...li.querySelectorAll(".acciones button")].map(b=>b.textContent),history:[...li.querySelectorAll("details:last-of-type p")].map(p=>p.textContent)}))')

def marker(page, i):
    page.eval_on_selector_all('.revision-marca', '(ms,i)=>ms[i].click()', i)

try:
 with sync_playwright() as pw:
     b = pw.chromium.launch(); page = b.new_page()
     owner = {'author': 'Ángel Botto', 'actor': 'owner', 'verified': True, 'permissions': {'comment': True, 'edit': True}}
     load(page, owner)
     r = {x['thread']: x for x in rows(page)}
     check('owner sees Alice as author', r['a1']['meta'].startswith('Alice Ruiz · correo verificado'), r['a1']['meta'])
     check('reply shows Bob', r['a1']['replies'] == 'Bob Pérez: Bob reply', r['a1']['replies'])
     check('agent label rendered as text with account + agent marker', r['g1']['meta'].startswith('<img src=x onerror=window.__xss=1> (agente de Ángel Botto) · conexión de agente'), r['g1']['meta'])
     check('historic token entry without agent shown as human (by design)', r['h1']['meta'].startswith('Ángel Botto · correo verificado'), r['h1']['meta'])
     check('no XSS', page.evaluate('window.__xss') is None and page.locator('main img').count() == 0)
     marker(page, 0)
     check('owner clicking foreign pin opens thread, not composer', page.evaluate("document.querySelector('[data-revision-panel]').open && !document.querySelector('[data-revision-editor]').open"))
     page.evaluate("[...document.querySelector('[data-revision-notas] > li[data-thread=a1]').querySelectorAll('button')].find(b=>b.textContent==='Editar').click()")
     check('owner explicit edit shows original author in composer', page.text_content('.review-composer-name') == 'Alice Ruiz', page.text_content('.review-composer-name'))
     page.fill('[data-revision-texto]', 'Alice point (fixed by owner)'); page.click('[data-revision-guardar]')
     page.wait_for_timeout(300); check("composer closed after save", not page.evaluate("document.querySelector('[data-revision-editor]').open"), page.evaluate("({open:document.querySelector('[data-revision-editor]').open,err:document.querySelector('[data-revision-editor]').innerText.slice(0,300),commits:window.__commits})"))
     c = page.evaluate('window.__commits')
     check('edit commit carries no author field', c and c[-1]['kind'] == 'edit' and 'author' not in c[-1], c[-1] if c else None)
     r = {x['thread']: x for x in rows(page)}
     check('after edit, thread still by Alice; activity names editor', r['a1']['meta'].startswith('Alice Ruiz') and any(h.startswith('Ángel Botto · edit') for h in r['a1']['history']), r['a1'])
     page.click('[data-revision-modo]'); page.click('#other')
     check('new entry after foreign edit shows viewer', page.text_content('.review-composer-name') == 'Ángel Botto', page.text_content('.review-composer-name'))
     page.keyboard.press('Escape')
     prompt = page.text_content('[data-revision-prompt]') or ''
     check('copied context names recorded authors', 'Autor: Alice Ruiz' in prompt and 'Autor: <img src=x onerror=window.__xss=1> (agente de Ángel Botto)' in prompt, prompt[:300])
     # reload: identical render from server state
     before = rows(page); load(page, owner)
     check('reload deterministic for authorship', [x['meta'].split(' · ')[0] for x in rows(page)] == [x['meta'].split(' · ')[0] for x in before])
     # commenter Bob
     bob = {'author': 'Bob Pérez', 'actor': 'bob', 'verified': True, 'permissions': {'comment': True, 'edit': False}}
     load(page, bob)
     r = {x['thread']: x for x in rows(page)}
     check('commenter sees no Editar on foreign thread', 'Editar' not in r['a1']['buttons'], r['a1']['buttons'])
     check('commenter sees Editar on own thread only', r['o1']['buttons'] == ['Editar'], r['o1']['buttons'])
     marker(page, 0)
     check('commenter clicking foreign pin opens thread', page.evaluate("!document.querySelector('[data-revision-editor]').open"))
     page.evaluate("document.querySelector('[data-revision-panel]').close()")
     idx = page.evaluate("[...document.querySelectorAll('.revision-marca')].findIndex(m=>m.getAttribute('aria-label').includes('Bob own'))")
     marker(page, idx)
     check('commenter own pin opens composer as self', page.evaluate("document.querySelector('[data-revision-editor]').open") and page.text_content('.review-composer-name') == 'Bob Pérez', page.text_content('.review-composer-name'))
     # reader without comment permission
     load(page, {'author': 'Lectora', 'actor': 'r', 'verified': True, 'permissions': {'comment': False, 'edit': False}})
     check('read-only viewer has no actions', all(not x['buttons'] for x in rows(page)), [x['buttons'] for x in rows(page)])
     # local mode (no bridge): composer label for editing local entry
     serve(page, PAGE.replace('</body>', '<script>' + source + '</script></body>'))
     page.fill('[data-revision-editor] input, .revision-autor input', 'Local A') if page.locator('.revision-autor input').count() else None
     check('local mode loads', page.locator('[data-revision]').count() == 1)
     b.close()
except Exception as exc:
    results.append({'check':'probe aborted','ok':False,'detail':str(exc)[:600]})
json.dump(results, sys.stdout, ensure_ascii=False, indent=1)
