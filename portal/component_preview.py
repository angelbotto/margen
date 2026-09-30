"""Read-only block visuals. HTML stays in an opaque, network-restricted frame."""
import base64
import hashlib
import json
import re
from html import escape
from html.parser import HTMLParser
from portal.block_source import Tree


MEASURE = """(()=>{'use strict';let last=0;const send=()=>{const root=document.getElementById('margen-component-root');if(!root)return;const height=Math.ceil(root.getBoundingClientRect().height);if(height!==last){last=height;parent.postMessage({type:'margen-component-size',height},'*');}};new ResizeObserver(send).observe(document.getElementById('margen-component-root'));document.fonts.ready.then(send);addEventListener('load',send);send();})();"""
CSP = ("sandbox allow-scripts; default-src 'none'; script-src 'sha256-" +
       base64.b64encode(hashlib.sha256(MEASURE.encode()).digest()).decode() +
       "'; style-src 'unsafe-inline'; img-src data: blob:; font-src data:; "
       "connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'")


class StaticMarkup(HTMLParser):
    """Preserve inline SVG, large embedded images and fonts, remove active elements."""
    blocked = {'script', 'iframe', 'object', 'template'}
    def __init__(self, markup):
        super().__init__(convert_charrefs=False)
        self.parts=[];self.depth=0;self.feed(markup)
    def handle_starttag(self, tag, attrs):
        if tag in self.blocked:self.depth+=1;return
        if self.depth or tag in {'embed','base','meta','link'}:return
        safe=[]
        for key,value in attrs:
            if key.startswith('on') or key in {'href','xlink:href','srcdoc','action','formaction','autofocus','contenteditable','tabindex'}:
                # SVG local symbol references are safe and needed by some diagrams.
                if key not in {'href','xlink:href'} or not (value or '').startswith('#'):continue
            safe.append(key if value is None else key+'="'+escape(value,quote=True)+'"')
        if tag in {'input','button','select','textarea'}:safe.append('disabled')
        self.parts.append('<'+tag+(' '+' '.join(safe) if safe else '')+'>')
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag,attrs)
        if tag in self.blocked:self.depth=max(0,self.depth-1)
        elif tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:
            # SVG shapes must close before the next sibling; HTMLParser otherwise
            # turns <rect/> into a parent and the browser hides nested labels.
            self.handle_endtag(tag)
    def handle_endtag(self, tag):
        if tag in self.blocked:self.depth=max(0,self.depth-1);return
        if not self.depth:self.parts.append('</'+tag+'>')
    def handle_data(self, data):
        if not self.depth:self.parts.append(data)
    def handle_entityref(self, name):
        if not self.depth:self.parts.append('&'+name+';')
    def handle_charref(self, name):
        if not self.depth:self.parts.append('&#'+name+';')


def render_component(document,template,block_id):
    region=next((r for r in document['regions'] if any(b['id']==block_id and b['type']=='opaque' for b in r['blocks'])),None)
    original=template['originals'].get(block_id)
    if not region or not original:raise ValueError('Componente no disponible.')
    source=template['html'];tree=Tree(source)
    slot=next(s for s in template['slots'] if s['id']==region['id'])
    node=next((n for n in tree.nodes if slot['start']<=n.start<n.end<=slot['end'] and source[n.start:n.end]==original['raw']),None)
    if node is None:raise ValueError('Componente no disponible.')
    styles=''.join(source[n.start:n.end] for n in tree.nodes if n.tag=='style')
    meta={n.attrs.get('name'):n.attrs.get('content') for n in tree.nodes if n.tag=='meta'}
    family=meta.get('nota-tema-inicial','editorial');mode='dark' if meta.get('nota-modo-inicial')=='dark' else 'light'
    theme={'editorial':mode,'linear':'linear-'+mode}.get(family,family)
    match=re.search(r'\{[^{}]*"id"\s*:\s*"'+re.escape(family)+r'"[^{}]*\}',source)
    if match:
        try:theme=json.loads(match[0]).get(mode,theme)
        except ValueError:pass
    if not isinstance(theme,str):theme=family
    ancestors=[];parent=node.parent
    while parent and parent.tag not in {'body','html','root'}:
        ancestors.append(parent);parent=parent.parent
    markup=''.join(source[n.start:n.inner] for n in reversed(ancestors))+original['raw']+''.join('</'+n.tag+'>' for n in ancestors)
    static=''.join(StaticMarkup(styles+markup).parts)
    override="""<style>
html,body{margin:0!important;padding:0!important;min-height:0!important;height:auto!important;scroll-behavior:auto!important}
body{overflow-x:auto}#margen-component-root{display:flow-root;min-height:1px;pointer-events:none}
#margen-component-root :is(main,.hoja,.pagina){display:block!important;max-width:none!important;width:100%!important;min-height:0!important;margin:0!important;padding:0!important;border:0!important}
#margen-component-root :is(figure,.pieza,.ancho,.amplio){max-width:100%!important;margin-inline:0!important}
#margen-component-root img{max-width:100%;height:auto}#margen-component-root *{animation:none!important;transition:none!important;caret-color:transparent!important}
#margen-component-root :is(.reveal,[data-reveal],.animar){opacity:1!important;transform:none!important}
</style>"""
    return '<!doctype html><html data-theme="'+escape(theme,quote=True)+'" data-estilo="'+escape(meta.get('nota-estilo-inicial','editorial'),quote=True)+'"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head><body><div id="margen-component-root">'+static+'</div>'+override+'<script>'+MEASURE+'</script></body></html>'
