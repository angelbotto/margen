/* Resaltado local conservador. Nueve lenguajes; todos los tokens son nodos de texto. */
(()=>{'use strict';const done=new WeakSet();
 const sets={cpp:'include define ifdef endif int char void bool double float auto const unsigned signed long short return if else for while break continue class struct public private protected virtual namespace using new delete nullptr true false template typename sizeof static switch case default',javascript:'async await break case catch class const continue debugger default delete do else export extends false finally for from function if import in instanceof let new null of return static super switch this throw true try typeof undefined var void while yield',typescript:'abstract any as boolean declare enum implements interface keyof namespace never number private protected public readonly string type unknown',python:'and as assert async await break class continue def del elif else except False finally for from global if import in is lambda None nonlocal not or pass raise return True try while with yield',sql:'SELECT FROM WHERE JOIN LEFT RIGHT INNER OUTER ON GROUP BY ORDER ASC DESC INSERT INTO VALUES UPDATE SET DELETE CREATE TABLE AS AND OR NOT NULL LIMIT COUNT SUM AVG HAVING DISTINCT',shell:'if then else fi for in do done case esac function echo printf cd pwd export source return exit set',css:'important media supports container keyframes root hover focus display grid flex block none minmax repeat var calc color background padding margin width height'};
 function language(el,text){const declared=el.dataset.lenguaje||el.dataset.language;if(declared)return ({js:'javascript',ts:'typescript',bash:'shell','c++':'cpp',c:'cpp'})[declared.toLowerCase()]||declared.toLowerCase();if(el.closest('.terminal'))return 'salida';if(el.closest('.receta-copia'))return 'html';const title=el.closest('.codigo')?.querySelector('.cab')?.textContent||'';for(const [re,lang] of [[/\.py\b|python/i,'python'],[/\.tsx?\b|typescript/i,'typescript'],[/\.jsx?\b|javascript/i,'javascript'],[/\.css\b/i,'css'],[/\.sql\b/i,'sql'],[/\.sh\b|shell|bash/i,'shell'],[/\.json\b/i,'json']])if(re.test(title))return lang;if(text.trim().startsWith('<'))return 'html';try{JSON.parse(text);return 'json';}catch{}return 'salida';}
 function tokens(source,lang){const out=[],add=(text,kind)=>out.push({text,kind});if(lang==='html'){
   const re=/<!--[\s\S]*?-->|<\/?[A-Za-z][^>]*>/g;let end=0;for(const m of source.matchAll(re)){add(source.slice(end,m.index));const token=m[0];if(token.startsWith('<!--'))add(token,'com');else{let pos=0;for(const p of token.matchAll(/(<\/?[\w:-]+)|("[^"]*"|'[^']*')|([\w:-]+)(?=\s*=)/g)){add(token.slice(pos,p.index));add(p[0],p[1]?'kw':p[2]?'str':'codigo-atributo');pos=p.index+p[0].length;}add(token.slice(pos));}end=m.index+token.length;}add(source.slice(end));return out;
  }
  const comments={cpp:/\/\*[\s\S]*?\*\/|\/\/[^\n]*/.source,javascript:/\/\*[\s\S]*?\*\/|\/\/[^\n]*/.source,typescript:/\/\*[\s\S]*?\*\/|\/\/[^\n]*/.source,css:/\/\*[\s\S]*?\*\//.source,python:/#[^\n]*/.source,shell:/#[^\n]*/.source,sql:/--[^\n]*|\/\*[\s\S]*?\*\//.source};
  const pattern=new RegExp('('+(comments[lang]||'(?!)')+')|'+/("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`)|(\b(?:0x[\da-fA-F]+|\d+(?:[.,]\d+)*(?:e[+-]?\d+)?))|([A-Za-z_$][\w$-]*)/.source,'g');let end=0;const words=new Set(((sets[lang]||'')+' '+(lang==='typescript'?sets.javascript:'')).split(' '));
  for(const m of source.matchAll(pattern)){add(source.slice(end,m.index));let kind;
   if(m[1])kind='com';
   else if(m[2])kind=lang==='json'&&/^\s*:/.test(source.slice(m.index+m[0].length))?'codigo-atributo':'str';else if(m[3])kind='codigo-numero';else if(words.has(m[4])||lang==='sql'&&words.has(m[4].toUpperCase())||lang==='json'&&['true','false','null'].includes(m[4]))kind='kw';else if(/^(error|failed|warning|warn|fail)$/i.test(m[4]))kind='codigo-alerta';else if(/^(ok|success|passed|ready)$/i.test(m[4]))kind='str';else if(/^[\s]*\(/.test(source.slice(m.index+m[0].length))&&['javascript','typescript','python','shell'].includes(lang))kind='codigo-atributo';
   add(m[0],kind);end=m.index+m[0].length;
  }add(source.slice(end));return out;
 }
 function init(root=document){root.querySelectorAll('.codigo pre code,.terminal pre,[data-lenguaje]').forEach(el=>{if(done.has(el))return;done.add(el);const lang=language(el,el.textContent);el.dataset.coloreado=lang;
  const block=el.closest('.codigo');
  if(block){
   block.classList.add('codigo-editorial');block.classList.remove('codigo-sin-titulo');
   let header=block.querySelector('.cab');if(!header){header=document.createElement('div');header.className='cab';block.prepend(header);}
   const label=header.querySelector('span:not(.copia-estado)');
   if(!label){const name=document.createElement('span');name.className='codigo-lenguaje';name.textContent=({javascript:'JavaScript',typescript:'TypeScript',python:'Python',sql:'SQL',shell:'Shell',css:'CSS',html:'HTML',json:'JSON',cpp:'C++',salida:'Texto'})[lang]||lang;header.prepend(name);}
   if(!header.querySelector('[data-copiar]')){
    const button=document.createElement('button');button.type='button';button.className='nota-icono';button.setAttribute('aria-label','Copiar código');button.title='Copiar código';
    button.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V3H4v13h4"/></svg>';
    const status=document.createElement('span');status.className='copia-estado';status.setAttribute('role','status');header.append(button,status);
    button.addEventListener('click',async()=>{try{if(!navigator.clipboard?.writeText)throw new Error('clipboard unavailable');await navigator.clipboard.writeText(el.textContent);status.textContent='Código copiado.';}catch{const range=document.createRange();range.selectNodeContents(el);const selection=getSelection();selection.removeAllRanges();selection.addRange(range);status.textContent='Código seleccionado. Usa ⌘C o Ctrl+C para copiar.';}});
   }
   const pre=el.closest('pre');if(pre&&!pre.hasAttribute('tabindex')){pre.tabIndex=0;pre.setAttribute('aria-label','Código: '+(header.querySelector('span')?.textContent||lang));}
   if(!el.hasAttribute('data-sin-lineas'))el.setAttribute('data-lineas','');
  }
  if(el.hasAttribute('data-lineas')){
   const source=el.textContent,selected=new Set(),marks=[];
   const walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);let offset=0;
   while(walker.nextNode()){const node=walker.currentNode,end=offset+node.textContent.length;if(node.parentElement.closest('mark,.subra'))marks.push([offset,end]);offset=end;}
   let sourceOffset=0;
   const append=(parent,text)=>{let at=0;for(const [start,end] of marks){const left=Math.max(0,start-sourceOffset),right=Math.min(text.length,end-sourceOffset);if(right<=left)continue;if(left>at)parent.append(document.createTextNode(text.slice(at,left)));const mark=document.createElement('mark');mark.textContent=text.slice(left,right);parent.append(mark);at=right;}if(at<text.length)parent.append(document.createTextNode(text.slice(at)));sourceOffset+=text.length;};
   for(const part of (el.dataset.destacar||'').split(',')){const m=part.trim().match(/^(\d+)(?:-(\d+))?$/);if(!m)continue;const from=Number(m[1]),to=Number(m[2]||m[1]);for(let i=from;i<=Math.min(to,10000);i++)selected.add(i);}
   const frag=document.createDocumentFragment();let number=1,line;
   const next=()=>{line=document.createElement('span');line.className='codigo-linea'+(selected.has(number)?' destacada':'');line.dataset.numero=String(number++);frag.append(line);};next();
   tokens(source,lang).forEach(({text,kind})=>text.split('\n').forEach((part,i)=>{if(i){frag.append(document.createTextNode('\n'));sourceOffset++;next();}if(!part)return;const span=document.createElement('span');if(kind)span.className=kind;append(span,part);line.append(span);}));
   el.replaceChildren(frag);return;
  }
  const walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT),nodes=[];while(walker.nextNode())nodes.push(walker.currentNode);
  for(const node of nodes){if(node.parentElement.closest('.kw,.str,.com,.subra,.tenue'))continue;const frag=document.createDocumentFragment();tokens(node.textContent,lang).forEach(({text,kind})=>{if(!text)return;if(!kind){frag.append(document.createTextNode(text));return;}const span=document.createElement('span');span.className=kind;span.textContent=text;frag.append(span);});node.replaceWith(frag);}
 });}window.NotaCodigo={init};init();})();
