"""Editorial text and language runs. Content never becomes provider instructions."""
import hashlib
import re
from html.parser import HTMLParser

BLOCKS = set('h1 h2 h3 h4 h5 h6 p li dt dd figcaption caption td th pre blockquote div section article main'.split())
SKIP_TAGS = set('script style noscript template nav summary button input textarea select option dialog head title'.split())
SKIP_CLASSES = set('revision-ui bottifact-toolbar barra salto'.split())
VOID = set('area base br col embed hr img input link meta param source track wbr'.split())


def language(value):
    return value if isinstance(value, str) and re.fullmatch(r'(?:es|en)(?:-[A-Za-z]{2,8})?', value) else ''


class Editorial(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.stack = []; self.items = []; self.serial = 0
        self.has_main = bool(re.search(r'<main(?:\s|>)', source, re.I))
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs); self.serial += 1
        classes = set(a.get('class', '').split())
        chapter = 'pagina' in classes and any(n['tag'] == 'main' and 'multipagina' in n['classes'] for n in self.stack)
        hidden = ('hidden' in a and not chapter) or 'inert' in a or a.get('aria-hidden') == 'true'
        hidden |= bool(re.search(r'(?:display\s*:\s*none|visibility\s*:\s*(?:hidden|collapse)|content-visibility\s*:\s*hidden)', a.get('style', ''), re.I)) and not chapter
        skip = tag in SKIP_TAGS or bool(classes & SKIP_CLASSES) or hidden or (tag == 'details' and 'open' not in a)
        skip |= any(k in a for k in ('data-revision','data-speech-skip','data-speech-ui','data-apariencia-menu','contenteditable'))
        skip |= a.get('role') in ('navigation','button','menu')
        node = {'tag':tag, 'id':a.get('id',''), 'classes':classes, 'skip':skip, 'serial':self.serial,
                'lang':language(a.get('lang')) or (self.stack[-1]['lang'] if self.stack else '')}
        if tag == 'br': self.handle_data(' ')
        if tag not in VOID: self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag,attrs)
        if tag not in VOID:self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i]['tag'] == tag:
                self.stack = self.stack[:i]; break

    def handle_data(self, text):
        if not self.stack or any(n['skip'] for n in self.stack):return
        if self.has_main and not any(n['tag']=='main' for n in self.stack):return
        block = next((n for n in reversed(self.stack) if n['tag'] in BLOCKS), self.stack[-1])
        if not self.items or self.items[-1]['serial'] != block['serial']:
            self.items.append({'serial':block['serial'], 'kind':block['tag'], 'anchors':[n['id'] for n in self.stack if n['id']], 'parts':[]})
        self.items[-1]['parts'].append((text,self.stack[-1]['lang']))


def editorial_blocks(source):
    result = []
    for item in Editorial(source).items:
        chars=[]; langs=[]
        for text, lang in item.pop('parts'):
            for ch in text:
                if ch.isspace():
                    if chars and chars[-1]!=' ':chars.append(' ');langs.append(lang)
                else:chars.append(ch);langs.append(lang)
        if chars and chars[-1]==' ':chars.pop();langs.pop()
        text=''.join(chars)
        if text:result.append({**item, 'text':text, 'languages':langs})
    return result


def manifest(source):
    result=[]
    for block in editorial_blocks(source):
        token=hashlib.sha256((str(block['serial'])+':'+block['text']).encode()).hexdigest()
        result.append({**block,'id':token})
    return result


def select_blocks(source, requested):
    if not isinstance(requested,list) or not 1<=len(requested)<=500:raise ValueError('Elige entre 1 y 500 fragmentos.')
    available={b['id']:b for b in manifest(source)}; result=[];total=0
    for raw in requested:
        if not isinstance(raw,dict) or set(raw)!={'id','start','end'}:raise ValueError('Referencia de lectura inválida.')
        b=available.get(raw['id']);start=raw['start'];end=raw['end']
        if not b or type(start)!=int or type(end)!=int or not 0<=start<end<=len(b['text']) or end-start>1200:raise ValueError('La selección no corresponde a esta versión.')
        text=b['text'][start:end];total+=len(text)
        if total>80000:raise ValueError('Elige una sección de menos de 80.000 caracteres.')
        runs=[]
        for ch,lang in zip(text,b['languages'][start:end]):
            if runs and runs[-1]['lang']==lang:runs[-1]['text']+=ch
            else:runs.append({'lang':lang,'text':ch})
        result.append({'text':text,'runs':runs,'kind':b['kind'],'block':b['id'],'start':start,'end':end})
    return result
