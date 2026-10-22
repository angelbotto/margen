/* Contratos de revisión: convergencia, importación, historial y errores de almacenamiento. */
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),{webcrypto}=require('node:crypto');
const source=fs.readFileSync(require('node:path').join(__dirname,'../packages/core/components/review.js'),'utf8').split('/* Comentarios locales:')[0];const context={crypto:webcrypto};vm.createContext(context);vm.runInContext(source,context);const Store=context.NotaRevisionStore;
const memory=()=>{const m=new Map();return {get length(){return m.size},key:i=>[...m.keys()][i],getItem:k=>m.get(k)??null,setItem:(k,v)=>m.set(k,v),removeItem:k=>m.delete(k)};};
const anchor={reference:'intro',tag:'P',text:'Texto estable',quote:'estable',page:'Inicio',x:.5,y:.5};
const db=memory(),a=Store.create('doc',db),b=Store.create('doc',db),c=a.append('create',null,'Ana',{text:'Revisar cifra',anchor});
b.append('reply',c.thread,'Luis',{text:'Fuente añadida'});a.append('reply',c.thread,'Ana',{text:'Revisada'});assert.equal(a.state()[0].replies.length,2);assert.equal(b.state()[0].replies.length,2);
b.append('resolve',c.thread,'Luis',{resolved:true});assert.equal(a.state()[0].resolved,true);a.append('edit',c.thread,'Ana',{text:'Cifra confirmada'});assert.equal(a.state()[0].history.length,5);
const portable=a.exportData(),other=Store.create('doc',memory());assert.equal(other.importData(JSON.parse(JSON.stringify(portable))),5);assert.equal(other.importData(JSON.parse(JSON.stringify(portable))),0);assert.equal(other.state()[0].text,'Cifra confirmada');
assert.throws(()=>other.importData({...portable,document:'otro'}));const bad=JSON.parse(JSON.stringify(portable));bad.events[0].text='Colisión';assert.throws(()=>other.importData(bad));assert.equal(other.state()[0].text,'Cifra confirmada');
assert.throws(()=>Store.validate({...portable.events[0],anchor:{...anchor,x:2}}));assert.equal(other.importData({...portable,events:[portable.events[1]]}),0);
const fresh=Store.create('doc',memory());assert.throws(()=>fresh.importData({...portable,events:[portable.events[1]]}));assert.equal(fresh.state().length,0);
const noSpace=memory();noSpace.setItem=()=>{throw Error('quota')};const volatile=Store.create('v',noSpace);volatile.append('create',null,'Ana',{text:'Pendiente',anchor});assert.equal(volatile.persistent,false);assert.equal(volatile.state().length,1);
const quota=memory(),quotaStore=Store.create('doc',quota);let writes=0;const set=quota.setItem;quota.setItem=(k,v)=>{if(++writes>2)throw Error('quota');set(k,v)};assert.throws(()=>quotaStore.importData(portable));assert.equal(quota.length,0);assert.equal(quotaStore.state().length,0);
a.append('delete',c.thread,'Ana');assert.equal(a.state().length,0);assert.equal(a.exportData().events.length,6);
console.log('Revisión: convergencia entre instancias, importación idempotente, errores atómicos, resolución e historial correctos.');

// Server-origin snapshots can contain edits allowed by an older API. Preserve
// that history without projecting another actor's words over the author's text.
const shared=Store.create('shared'),original=shared.append('create',null,'Ana',{actor:'a',text:'Original de Ana',anchor});
shared.append('edit',original.thread,'Luis',{actor:'b',text:'Palabras ajenas'});
assert.equal(shared.state()[0].text,'Original de Ana');
shared.append('edit',original.thread,'Ana',{actor:'a',text:'Corrección de Ana'});
assert.equal(shared.state()[0].text,'Corrección de Ana');
assert.equal(shared.state()[0].history.length,3);
assert.equal(shared.exportData().events[1].text,'Palabras ajenas');
const imported=Store.create('shared');imported.importData(shared.exportData());
assert.equal(imported.state()[0].text,'Corrección de Ana');
