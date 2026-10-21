/* Pruebas del runtime real: migración, preferencias y cambios del sistema. Sin DOM externo. */
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const registry=JSON.parse(fs.readFileSync('packages/core/themes/themes.json','utf8'));
const source=fs.readFileSync('packages/core/components/reader.js','utf8').split('  // Variante optativa:')[0]+'})();';
let assertions=0;
function equal(actual,expected){assert.deepEqual(actual,expected);assertions++;}
function load({initial,mode,style,dark=false,stored={},blocked=false}={}){
 const values=new Map(Object.entries(stored)),dataset={},listeners={},changes=[];
 const media={matches:dark,addEventListener:(name,fn)=>listeners.media=fn};
 const doc={documentElement:{dataset},querySelectorAll:()=>[],querySelector:selector=>{
  const value=selector.includes('nota-tema-inicial')?initial:selector.includes('nota-modo-inicial')?mode:style;return value?{content:value}:null;
 },addEventListener:(name,fn)=>listeners[name]=fn,dispatchEvent:event=>changes.push(event.detail)};
 const storage={getItem:key=>{if(blocked)throw Error('blocked');return values.get(key)||null},setItem:(key,value)=>{if(blocked)throw Error('blocked');values.set(key,value)}};
 const context={document:doc,window:{},localStorage:storage,matchMedia:()=>media,location:{pathname:'/fixture.html'},CustomEvent:class{constructor(name,props){Object.assign(this,{name},props)}}};
 vm.runInNewContext(source,context);
 return {api:context.window.NotaTemas,dataset,values,changes,changeSystem(value){media.matches=value;listeners.media()},choose(attr,value){listeners.change({target:{value,matches:selector=>selector===`[${attr}]`}})}};
}
let app=load();equal(app.dataset.themeFamily,'editorial');equal(app.dataset.themeMode,'system');equal(app.dataset.theme,'light');
for(const family of registry.familias){
 app.choose('data-elegir-tema',family.id);equal(app.dataset.themeMode,'system');
 app.changeSystem(true);equal(app.dataset.colorMode,'dark');equal(app.dataset.theme,typeof family.dark==='string'?family.dark:family.id+'-dark');
 app.choose('data-elegir-modo','light');app.changeSystem(false);app.changeSystem(true);equal(app.dataset.colorMode,'light');
 app.choose('data-elegir-modo','dark');app.changeSystem(false);equal(app.dataset.colorMode,'dark');
 app.choose('data-elegir-modo','system');equal(app.dataset.colorMode,'light');
}
for(const [alias,[family,mode]] of Object.entries(registry.alias_anteriores)){
 const old=load({stored:{'nota-tema':alias}});equal(old.dataset.themeFamily,family);equal(old.dataset.themeMode,mode);
 const scoped=load({initial:'editorial',mode:'system',stored:{'nota-tema:/fixture.html':alias}});equal(scoped.dataset.themeFamily,family);equal(scoped.dataset.themeMode,mode);
}
app=load({initial:'catppuccin',mode:'system',dark:true});app.api.set({family:'github',mode:'light'});
const restored=load({initial:'catppuccin',mode:'system',dark:true,stored:Object.fromEntries(app.values)});equal(restored.dataset.themeFamily,'github');equal(restored.dataset.themeMode,'light');
equal(restored.api.set({family:'invalid'}),false);equal(restored.api.set({mode:'invalid'}),false);equal(restored.dataset.themeFamily,'github');
const blocked=load({initial:'liftit',mode:'system',blocked:true});equal(blocked.api.set({mode:'dark'}),true);equal(blocked.dataset.theme,'liftit-dark');
const unscoped=load({stored:{'nota-apariencia-v2':'{"family":"sea","mode":"light"}','nota-tema':'dark'}});equal(unscoped.dataset.theme,'sea-light');
const corrupt=load({stored:{'nota-apariencia-v2':'broken'}});equal(corrupt.dataset.themeFamily,'editorial');
// Kaira is a color family, not a brand asset or a typography override.
const kaira=registry.familias.find(family=>family.id==='kaira');
assert.ok(kaira,'Kaira must be registered with complete light and dark palettes');assertions++;
const css=fs.readFileSync('packages/core/styles/artifact.css','utf8');
function luminance(hex){
 return hex.slice(1).match(/../g).map(value=>parseInt(value,16)/255)
  .map(value=>value<=.04045?value/12.92:((value+.055)/1.055)**2.4)
  .reduce((sum,value,index)=>sum+value*[.2126,.7152,.0722][index],0);
}
function contrast(a,b){const x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);}
for(const mode of ['light','dark']){
 const palette=kaira[mode];
 const rule=css.match(new RegExp(`:root\\[data-theme="kaira-${mode}"\\] \\{([^}]+)\\}`));
 assert.ok(rule,`Missing generated Kaira ${mode} CSS`);assertions++;
 const generated=Object.fromEntries([...rule[1].matchAll(/--([\w-]+):\s*([^;]+);/g)].map(match=>[match[1],match[2]]));
 for(const key of ['papel','panel','panel-2','tinta','tinta-2','tinta-3','naranja','verde','rojo','azul']){
  assert.match(palette[key],/^#[\da-f]{6}$/i);assertions++;
  equal(generated[key],palette[key]);
 }
 for(const ink of ['tinta','tinta-2','tinta-3','naranja','verde','rojo','azul'])for(const bg of ['papel','panel','panel-2']){
  const ratio=contrast(palette[ink],palette[bg]);
  assert.ok(ratio>=4.5,`Kaira ${mode}: ${ink}/${bg} contrast ${ratio} < 4.5`);assertions++;
 }
 for(let level=0;level<=4;level++){
  assert.ok(contrast(generated['calor-tinta'],generated[`calor-${level}`])>=4.5,`Kaira ${mode}: heatmap ${level}`);assertions++;
 }
 for(const bg of ['naranja-suave','tabla-total','tabla-elegida']){
  const resolved=generated[bg].replace(/^var\(--([\w-]+)\)$/,(_,key)=>generated[key]);
  assert.ok(contrast(palette.tinta,resolved)>=4.5,`Kaira ${mode}: selected/table text on ${bg}`);assertions++;
 }
 const initial=load({initial:'kaira',mode,dark:mode!=='dark'});
 equal(initial.dataset.theme,`kaira-${mode}`);
 equal(initial.dataset.themeFamily,'kaira');
 const restored=load({initial:'editorial',mode:'system',stored:Object.fromEntries(initial.values)});
 equal(restored.dataset.theme,`kaira-${mode}`);
}
console.log(`${assertions} comprobaciones: ${registry.familias.length} familias, modos independientes, cambio del SO, persistencia, alias, almacenamiento bloqueado y contraste Kaira AA.`);
