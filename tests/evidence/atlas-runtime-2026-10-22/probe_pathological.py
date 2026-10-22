import json,sys
sys.path.insert(0,'/Users/angelbotto/orca/workspaces/margen/margen-atlas-runtime/scripts')
from contract_artifact import build
from playwright.sync_api import sync_playwright
html=build('P',[{'id':'p','titulo':'P','html':'<section class="prosa" id="s"><h2>P</h2><p>x</p></section>'}])
CASES={
 'js_one_line_149k':"'const a=[' + Array.from({length:14900},(_, i)=>i+',').join('').slice(0,148000) + '];'",
 'js_strings_149k':"Array.from({length:3000},(_, i)=>'s'+i+' = \"'+'\\\\\\\\n'.repeat(20)+'\";').join('\\n').slice(0,149000)",
 'html_nested_149k':"'<div class=\"a\">'.repeat(9000).slice(0,149000)",
 'unclosed_template_149k':"'`' + '${a}x'.repeat(29000).slice(0,148000)",
 'markdown_149k':"('# t\\n*a* **b** `c` [d](e)\\n').repeat(5000).slice(0,149000)",
}
with sync_playwright() as pw:
 for eng in ('chromium','webkit'):
  b=getattr(pw,eng).launch();p=b.new_page();p.route('**/*',lambda r:r.fulfill(status=200,content_type='text/html',body=html) if r.request.url.startswith('https://m.test/') else r.abort());p.goto('https://m.test/')
  out={}
  for k,expr in CASES.items():
   lang='markdown' if 'markdown' in k else 'markup' if 'html' in k else 'javascript'
   out[k]=p.evaluate(f"""()=>{{const src={expr};const t0=performance.now();const toks=NotaCodigo.tokens(src,'{lang}');const t1=performance.now();
     const box=document.createElement('div');box.className='codigo';box.innerHTML='<pre tabindex="0" aria-label="x"><code data-lenguaje="{lang}" data-lineas></code></pre>';const c=box.querySelector('code');c.textContent=src;document.querySelector('#s').append(box);
     const t2=performance.now();NotaCodigo.init(box,{{inmediato:true}});const t3=performance.now();const same=c.textContent===src;box.remove();
     return {{chars:src.length,tokenizeMs:Math.round(t1-t0),fullSyncMs:Math.round(t3-t2),tokens:toks.length,exact:same,state:c.dataset.codigoEstado}}}}""")
  print(eng,json.dumps(out));b.close()
