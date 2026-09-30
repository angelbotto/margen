"""Conservative, versioned block source. Unchanged HTML remains byte-for-byte intact.

Only whitelisted semantic data crosses into the account UI. Opaque components and
all original attributes stay server-side. Edits never accept executable HTML.
"""
import copy
import hashlib
import json
import re
import uuid
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlsplit

SCHEMA = 'margen-blocks/1'
KINDS = {'paragraph','heading','list','checklist','quote','code','divider','table','opaque'}
VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
INLINE = {'strong','b','em','i','code','a','br','span','s','del','u','mark'}

class Element:
    def __init__(self, tag, attrs, start, inner, parent=None):
        self.tag, self.attrs, self.start, self.inner, self.parent = tag, dict(attrs), start, inner, parent
        self.end = inner
        self.close = inner
        self.children = []

class Tree(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.html = html
        self.lines = [0]
        for m in re.finditer('\n',html): self.lines.append(m.end())
        self.root = Element('root',{},0,0)
        self.stack = [self.root]
        self.nodes = []
        self.feed(html)
        self.root.end = self.root.close = len(html)
        for node in self.stack[1:]: node.end = node.close = len(html)
    def pos(self):
        line, col = self.getpos()
        return self.lines[line-1]+col
    def handle_starttag(self, tag, attrs):
        start = self.pos()
        n = Element(tag,attrs,start,start+len(self.get_starttag_text()),self.stack[-1])
        n.parent.children.append(n); self.nodes.append(n)
        if tag not in VOID: self.stack.append(n)
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag,attrs)
        if tag not in VOID: self.stack.pop()
    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag == tag:
                n = self.stack[i]; n.close = self.pos(); n.end = self.html.find('>',n.close)+1
                self.stack = self.stack[:i]
                break

class Inline(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True); self.runs=[]; self.stack=[]; self.feed(html)
    def handle_starttag(self, tag, attrs):
        if tag == 'br': self.handle_data('\n'); return
        a=dict(attrs); self.stack.append((tag,a))
    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i][0]==tag:self.stack=self.stack[:i];break
    def handle_data(self, text):
        if any(t in ('script','style') for t,_ in self.stack):return
        marks=[];href=None
        for t,a in self.stack:
            mark={'strong':'bold','b':'bold','em':'italic','i':'italic','code':'code','s':'strike','del':'strike','u':'underline'}.get(t)
            if mark and mark not in marks:marks.append(mark)
            if t=='a' and safe_url(a.get('href','')):href=a['href']
        run={'text':text,'marks':marks}
        if href:run['href']=href
        if text:self.runs.append(run)

def safe_url(value):
    if not isinstance(value,str) or re.search(r'[\x00-\x20]',value):return False
    return value.startswith(('#','/')) and not value.startswith('//') or urlsplit(value).scheme.lower() in ('https','http','mailto')

def text_of(html):return ''.join(r['text'] for r in Inline(html).runs)
def key(seed):return 'b-'+hashlib.sha256(seed.encode()).hexdigest()[:24]
def inner(tree,n):return tree.html[n.inner:n.close]
def descendants(n):
    for c in n.children:
        yield c
        yield from descendants(c)

def parse_block(tree,n,seed):
    bid=n.attrs.get('data-margen-block') or key(seed+':'+str(n.start))
    block={'id':bid,'type':'opaque','label':text_of(inner(tree,n))[:120] or n.tag,'locked':True}
    nodes=list(descendants(n))
    # Nested anchors cannot be reassigned by positional text editing.
    anchored=any(c.attrs.get('id') for c in nodes)
    plain=not anchored and all(c.tag in INLINE for c in nodes)
    if n.tag in ('p','h2','h3','h4','blockquote') and plain:
        block={'id':bid,'type':{'p':'paragraph','blockquote':'quote'}.get(n.tag,'heading'),'runs':Inline(inner(tree,n)).runs}
        if block['type']=='heading':block['level']=int(n.tag[1])
    elif n.tag=='hr':block={'id':bid,'type':'divider'}
    elif n.tag=='pre' and all(c.tag=='code' for c in nodes):block={'id':bid,'type':'code','text':text_of(inner(tree,n))}
    elif n.tag in ('ul','ol') and not anchored and all(c.tag in INLINE|{'li'} for c in nodes) and all(c.tag=='li' for c in n.children):
        block={'id':bid,'type':'list','ordered':n.tag=='ol','items':[Inline(inner(tree,c)).runs for c in n.children]}
    elif n.tag=='table' and not anchored and all(c.tag in INLINE|{'thead','tbody','tr','th','td','caption','colgroup','col'} for c in nodes) and not any(c.attrs.get('rowspan') or c.attrs.get('colspan') or any(k.startswith('data-') and k!='data-margen-block' for k in c.attrs) for c in [n,*nodes]):
        rows=[c for c in nodes if c.tag=='tr']
        cells=[[c for c in row.children if c.tag in ('td','th')] for row in rows]
        if cells and len(cells)<=100 and len(cells[0])<=12 and all(len(row)==len(cells[0]) for row in cells):
            block={'id':bid,'type':'table','rows':[[text_of(inner(tree,c)) for c in row] for row in cells], 'header':all(c.tag=='th' for c in cells[0]),'caption':next((text_of(inner(tree,c)) for c in nodes if c.tag=='caption'),'')}
    return block

def import_document(html,version,title):
    tree=Tree(html)
    meta={n.attrs.get('name'):n.attrs.get('content') for n in tree.nodes if n.tag=='meta'}
    if meta.get('margen-format') in ('presentation','prototype') or any('data-presentation' in n.attrs for n in tree.nodes):
        raise ValueError('Este formato conserva su editor original; la edición por bloques admite documentos editoriales.')
    main=next((n for n in tree.nodes if n.tag=='main'),None)
    if not main:raise ValueError('El documento no tiene una región editorial main compatible.')
    regions=[]; originals={}; slots=[]
    def walk(parent):
        batch=[]
        def flush():
            if not batch:return
            rid=key(version+':region:'+str(batch[0].start))
            blocks=[]
            for n in batch:
                b=parse_block(tree,n,version);blocks.append(b)
                originals[b['id']]={'block':copy.deepcopy(b),'raw':html[n.start:n.end], 'open':html[n.start:n.inner], 'close':html[n.close:n.end], 'tag':n.tag, 'attrs':n.attrs}
            regions.append({'id':rid,'label':next((text_of(inner(tree,n))[:100] for n in batch if n.tag in ('h2','h3')),'Contenido'),'blocks':blocks})
            slots.append({'id':rid,'start':batch[0].start,'end':batch[-1].end});batch.clear()
        for n in parent.children:
            # Text and comments between elements belong to the original document.
            # Keep those gaps outside replaceable slots rather than dropping them.
            if batch and html[batch[-1].end:n.start].strip():flush()
            cls=set((n.attrs.get('class') or '').split())
            if n.tag in ('header','nav','footer','script','style'):
                flush();continue
            if n.tag in ('section','article','div','figure') and (not cls or cls <= {'prosa','seccion','pagina','viva','tabla-caja','pieza','ancho','amplio','tabla-editorial'} and (n.tag!='figure' or any(c.tag=='table' for c in descendants(n)))) and not any(k.startswith('data-') for k in n.attrs):
                flush();walk(n)
            else:batch.append(n)
        flush()
    walk(main)
    if not regions:
        rid=key(version+':empty');regions=[{'id':rid,'label':'Contenido','blocks':[]}];slots=[{'id':rid,'start':main.close,'end':main.close}]
    doc={'schema':SCHEMA,'title':title,'regions':regions}
    return doc,{'html':html,'slots':slots,'originals':originals}

def valid_text(value,limit=50000):
    if not isinstance(value,str) or len(value)>limit:raise ValueError('Texto inválido o demasiado largo.')
    return value

def clean_runs(runs):
    if not isinstance(runs,list) or len(runs)>1000:raise ValueError('Formato de texto inválido.')
    result=[]
    for r in runs:
        if not isinstance(r,dict) or set(r)-{'text','marks','href'}:raise ValueError('Formato de texto no admitido.')
        marks=r.get('marks',[])
        if not isinstance(marks,list) or len(marks)>5 or any(m not in ('bold','italic','code','strike','underline') for m in marks):raise ValueError('Estilo de texto inválido.')
        item={'text':valid_text(r.get('text')),'marks':list(dict.fromkeys(marks))}
        if r.get('href'):
            if not safe_url(r['href']) or len(r['href'])>2000:raise ValueError('Enlace inválido.')
            item['href']=r['href']
        result.append(item)
    if sum(len(r['text']) for r in result)>50000:raise ValueError('Bloque demasiado largo.')
    return result

def validate_document(value,base,template):
    if not isinstance(value,dict) or value.get('schema')!=SCHEMA:raise ValueError('Fuente de bloques incompatible.')
    title=valid_text(value.get('title'),200).strip()
    if not title:raise ValueError('El título no puede estar vacío.')
    regions=value.get('regions')
    if not isinstance(regions,list) or [r.get('id') for r in regions if isinstance(r,dict)]!=[r['id'] for r in base['regions']]:raise ValueError('La estructura de secciones cambió; vuelve a abrir el documento.')
    out={'schema':SCHEMA,'title':title,'regions':[]};seen=set();count=0
    for region,prior in zip(regions,base['regions']):
        blocks=region.get('blocks')
        if not isinstance(blocks,list):raise ValueError('Bloques inválidos.')
        clean=[]
        oldlocked=[b for b in prior['blocks'] if b['type']=='opaque']
        for b in blocks:
            count+=1
            if count>1000:raise ValueError('Máximo 1000 bloques por documento.')
            if not isinstance(b,dict):raise ValueError('Bloque inválido.')
            bid=b.get('id');kind=b.get('type')
            if not isinstance(bid,str) or not re.fullmatch(r'b-[a-zA-Z0-9_-]{1,64}',bid) or bid in seen or kind not in KINDS:raise ValueError('Identidad o tipo de bloque inválido.')
            seen.add(bid);c={'id':bid,'type':kind}
            original=template['originals'].get(bid)
            if kind=='opaque':
                if b not in oldlocked:raise ValueError('Los componentes conservados no se pueden modificar.')
                clean.append(copy.deepcopy(b));continue
            if original and original['block']['type']=='opaque':raise ValueError('No se puede reemplazar un componente conservado.')
            if kind in ('paragraph','heading','quote'):
                c['runs']=clean_runs(b.get('runs',[]))
                if kind=='heading':
                    if b.get('level') not in (2,3,4):raise ValueError('Nivel de título inválido.')
                    c['level']=b['level']
            elif kind in ('list','checklist'):
                items=b.get('items')
                if not isinstance(items,list) or not 1<=len(items)<=100:raise ValueError('Lista inválida.')
                c['items']=[clean_runs(i) for i in items]
                if kind=='list':c['ordered']=bool(b.get('ordered',False))
                else:
                    checked=b.get('checked',[False]*len(items))
                    if not isinstance(checked,list) or len(checked)!=len(items) or any(type(v) is not bool for v in checked):raise ValueError('Checklist inválido.')
                    c['checked']=checked
            elif kind=='code':c['text']=valid_text(b.get('text',''))
            elif kind=='table':
                rows=b.get('rows')
                if not isinstance(rows,list) or not 1<=len(rows)<=100 or not isinstance(rows[0],list) or not 1<=len(rows[0])<=12 or any(not isinstance(r,list) or len(r)!=len(rows[0]) for r in rows):raise ValueError('La tabla admite 100 filas y 12 columnas como máximo.')
                c.update(rows=[[valid_text(v,4000) for v in row] for row in rows],header=bool(b.get('header',True)),caption=valid_text(b.get('caption',''),500))
            clean.append(c)
        if [b for b in clean if b['type']=='opaque']!=oldlocked:raise ValueError('Conserva los componentes que tienen su propio formato.')
        out['regions'].append({'id':prior['id'],'label':prior['label'],'blocks':clean})
    if len(json.dumps(out).encode())>2*1024*1024:raise ValueError('La fuente editable supera 2 MB.')
    return out

def render_runs(runs):
    out=''
    for r in runs:
        s=escape(r['text']).replace('\n','<br>')
        for mark in r.get('marks',[]):
            tag={'bold':'strong','italic':'em','code':'code','strike':'s','underline':'u'}[mark];s=f'<{tag}>{s}</{tag}>'
        if r.get('href'):s='<a href="'+escape(r['href'],quote=True)+'">'+s+'</a>'
        out+=s
    return out

def render_block(b,template):
    old=template['originals'].get(b['id'])
    if old and b==old['block']:
        if b['type']=='opaque' or 'data-margen-block' in old['attrs']:return old['raw']
        opening=old['open'].rstrip()
        end='/>' if opening.endswith('/>') else '>'
        return opening[:-len(end)]+' data-margen-block="'+b['id']+'"'+end+old['raw'][len(old['open']):]
    kind=b['type'];bid=b['id']
    tag={'paragraph':'p','heading':'h'+str(b.get('level',2)),'quote':'blockquote','code':'pre','divider':'hr','list':'ol' if b.get('ordered') else 'ul','checklist':'ul','table':'table'}.get(kind)
    if not tag:raise ValueError('No se puede reconstruir el bloque.')
    attrs=' data-margen-block="'+bid+'"'
    if old:
        for k,v in old['attrs'].items():
            if k in ('id','class','style','lang','dir') or k.startswith('aria-'):
                attrs+=' '+k+'="'+escape(v or '',quote=True)+'"'
    else:attrs+=' id="'+bid+'"'
    content=''
    if kind in ('paragraph','heading','quote'):content=render_runs(b['runs'])
    elif kind=='code':content='<code>'+escape(b['text'])+'</code>'
    elif kind in ('list','checklist'):
        content=''.join('<li>'+('<span aria-label="'+('Hecho' if b['checked'][i] else 'Pendiente')+'">'+('☑' if b['checked'][i] else '☐')+'</span> ' if kind=='checklist' else '')+render_runs(r)+'</li>' for i,r in enumerate(b['items']))
    elif kind=='table':
        content='<caption>'+escape(b['caption'])+'</caption>'
        for i,row in enumerate(b['rows']):
            cell='th' if i==0 and b['header'] else 'td'
            content+=('<thead>' if i==0 and b['header'] else '<tbody>' if i==(1 if b['header'] else 0) else '')+'<tr>'+''.join('<'+cell+(' scope="col"' if cell=='th' else '')+'>'+escape(v)+'</'+cell+'>' for v in row)+'</tr>'+('</thead>' if i==0 and b['header'] else '')
        if len(b['rows'])>int(b['header']):content+='</tbody>'
    result='<'+tag+attrs+'>'+content+('' if tag in VOID else '</'+tag+'>')
    if kind=='table' and not old:result='<div class="tabla-caja" tabindex="0" role="region" aria-label="Tabla, desplazable">'+result+'</div>'
    return result

def render_document(doc,template):
    source=template['html'];regions={r['id']:r for r in doc['regions']}
    for slot in sorted(template['slots'],key=lambda s:s['start'],reverse=True):
        body='\n'.join(render_block(b,template) for b in regions[slot['id']]['blocks'])
        source=source[:slot['start']]+body+source[slot['end']:]
    # Title is source data; update only title and the canonical document masthead.
    source=re.sub(r'(<title\b[^>]*>).*?(</title>)',lambda m:m[1]+escape(doc['title'])+m[2],source,count=1,flags=re.S|re.I)
    source=re.sub(r'(<header\b[^>]*class="[^"]*\bcabecera\b[^"]*"[^>]*>\s*<h1\b[^>]*>).*?(</h1>)',lambda m:m[1]+escape(doc['title'])+m[2],source,count=1,flags=re.S)
    parsed=Tree(source)
    headings=[n for n in parsed.nodes if n.tag=='h2' and (n.attrs.get('id') or n.parent.attrs.get('id'))]
    for nav in reversed([n for n in parsed.nodes if n.tag=='nav' and 'indice' in (n.attrs.get('class') or '').split()]):
        listing=next((n for n in nav.children if n.tag=='ol'),None)
        if listing:
            links=''.join('<li><a href="#'+escape(n.attrs.get('id') or n.parent.attrs['id'],quote=True)+'">'+escape(text_of(inner(parsed,n)))+'</a></li>' for n in headings)
            source=source[:listing.inner]+links+source[listing.close:]
    return source

def changes(before,after):
    def flatten(doc):return {b['id']:(r['id'],i,b) for r in doc['regions'] for i,b in enumerate(r['blocks'])}
    left,right=flatten(before),flatten(after);out=[]
    if before['title']!=after['title']:out.append({'id':'document-title','kind':'edited','before':before['title'],'after':after['title']})
    for bid in dict.fromkeys([*left,*right]):
        a,b=left.get(bid),right.get(bid)
        if not a:kind='added'
        elif not b:kind='deleted'
        elif a[2]!=b[2]:kind='edited'
        elif a[:2]!=b[:2]:kind='moved'
        else:continue
        out.append({'id':bid,'kind':kind,'before':a[2] if a else None,'after':b[2] if b else None})
    return out
