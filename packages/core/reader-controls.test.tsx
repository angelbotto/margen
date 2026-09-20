import { beforeEach, afterEach, expect, it, vi } from "vitest";
import { readFileSync } from "node:fs";
const source = readFileSync(
  process.cwd() + "/packages/core/components/reader-controls.js",
  "utf8",
);
beforeEach(() => {
  document.body.replaceChildren();
  document.documentElement.className = "";
  delete (window as any).BottifactReaderControls;
  delete (window as any).BottifactReviewBridge;
});
afterEach(() => {
  document
    .querySelectorAll("[data-bottifact-controls]")
    .forEach((e) => e.remove());
});
it("renders one toolbar for hosted legacy markup and routes sharing to the host", () => {
  const action = vi.fn().mockResolvedValue({ ok: true }),
    subscribe = vi.fn(),
    ready = vi.fn();
  (window as any).BottifactReviewBridge = {
    action,
    subscribe,
    controlsReady: ready,
  };
  window.eval(source);
  document.dispatchEvent(new Event("DOMContentLoaded"));
  window.eval(source);
  document.dispatchEvent(new Event("DOMContentLoaded"));
  expect(document.querySelectorAll(".bottifact-toolbar")).toHaveLength(1);
  (document.querySelector('summary[aria-label="Compartir"]') as HTMLElement).click();
  ([...document.querySelectorAll('.bf-menu button')].find(b=>b.getAttribute("aria-label") === 'Enlace y acceso') as HTMLElement).click();
  expect(action).toHaveBeenCalledWith("share");
  expect(ready).toHaveBeenCalledOnce();
});
it("keeps the existing appearance and review controls as the action owners", () => {
  document.body.innerHTML =
    '<details data-apariencia-menu><summary>Appearance</summary><div class="apariencia-panel"></div></details><div class="revision-barra"><button>Comment</button><button aria-label="Añadir nota privada">Note</button><button>List</button></div>';
  const appearance = document.querySelector("[data-apariencia-menu]"),
    note = document.querySelector('[aria-label="Añadir nota privada"]')!,
    click = vi.fn();
  note.addEventListener("click", click);
  window.eval(source);
  document.dispatchEvent(new Event("DOMContentLoaded"));
  expect(
    document.querySelector(".bottifact-toolbar [data-apariencia-menu]"),
  ).toBe(appearance);
  const addNote = [...document.querySelectorAll(".bf-menu button")].find(
    (b) => b.getAttribute("aria-label") === 'Añadir nota personal',
  ) as HTMLButtonElement;
  addNote.click();
  expect(click).toHaveBeenCalledOnce();
});
it("uses the actual comment icon for its badge and keeps exactly three named tools", () => {
 document.body.innerHTML='<details data-apariencia-menu><summary>Appearance</summary></details><div class="revision-barra"><button>Comment</button><button>9</button></div>';
 const icons:string[]=[];(window as any).BottifactUI={icon:(name:string)=>{icons.push(name);const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.dataset.icon=name;return svg;},decorate:()=>{}};
 window.eval(source);document.dispatchEvent(new Event('DOMContentLoaded'));
 const tools=[...document.querySelectorAll('.bottifact-toolbar>details>summary')];
 expect(tools.map(t=>t.querySelector('.bf-tool-label')?.textContent)).toEqual(['Comentarios','Compartir','Preferencias']);
 expect(tools[0].querySelector('svg')?.dataset.icon).toBe('comment');
 expect(tools[0].querySelector('.bf-review-count')?.textContent).toBe('9');
 expect(document.querySelector('.bottifact-toolbar>button')).toBeNull();
 document.dispatchEvent(new CustomEvent('bottifact:review-mode',{detail:{active:true}}));
 expect(tools[0].classList.contains('bf-tool-active')).toBe(true);
 delete (window as any).BottifactUI;
});
it("keeps private notes available to a verified read-only reader", () => {
 let receive:any;(window as any).BottifactReviewBridge={action:vi.fn(),subscribe:(fn:any)=>receive=fn,controlsReady:vi.fn()};
 window.eval(source);document.dispatchEvent(new Event('DOMContentLoaded'));
 receive({author:'Reader',verified:true,permissions:{comment:false,edit:false}});
 const buttons=[...document.querySelectorAll('.bf-menu button')] as HTMLButtonElement[];
 expect(buttons.find(b=>b.getAttribute("aria-label") === 'Añadir comentario')?.disabled).toBe(true);
 expect(buttons.find(b=>b.getAttribute("aria-label") === 'Añadir nota personal')?.disabled).toBe(false);
});
it("moves between tools with arrow keys and exposes keyboard tooltip text", async () => {
  vi.useFakeTimers();
  document.body.innerHTML =
    '<div class="revision-barra"><button>Comment</button><button>List</button></div>';
  window.eval(source);
  document.dispatchEvent(new Event("DOMContentLoaded"));
  const first = document.querySelector(
    ".bottifact-toolbar>details>summary",
  ) as HTMLButtonElement;
  first.focus();
  await vi.advanceTimersByTimeAsync(1);
  expect(document.querySelector('[role="tooltip"]')?.textContent).toBe(
    "Comentarios · 0 abiertos",
  );
  first.dispatchEvent(
    new KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true }),
  );
  expect(document.activeElement?.getAttribute("aria-label")).toBe(
    "Compartir",
  );
  vi.useRealTimers();
});

it("shows the open-thread count and removes the duplicated note and generic more shortcuts",()=>{
 document.body.innerHTML='<div class="revision-barra"><button>Comment</button><button>3</button></div>';
 window.eval(source);document.dispatchEvent(new Event('DOMContentLoaded'));
 expect(document.querySelector('.bf-review-count')?.textContent).toBe('3');
 document.dispatchEvent(new CustomEvent('bottifact:review-count',{detail:{open:5,total:8}}));
 expect(document.querySelector('.bf-review-count')?.textContent).toBe('5');
 expect(document.querySelector('summary[aria-label="Más opciones"]')).toBeNull();
 expect(document.querySelector('.bottifact-toolbar>button[aria-label="Añadir nota privada"]')).toBeNull();
});
it('counts authorized host threads even when a legacy artifact has no embedded review module',()=>{
 let receive:any;(window as any).BottifactReviewBridge={subscribe:(fn:any)=>receive=fn,controlsReady:vi.fn()};
 window.eval(source);document.dispatchEvent(new Event('DOMContentLoaded'));
 const event=(kind:string,thread:string,time:number,extra={})=>({id:String(time),kind,thread,time,...extra});
 receive({author:'Reader',verified:true,permissions:{comment:true},snapshot:{events:[event('create','a',1),event('create','b',2),event('reply','a',3),event('create','c',4),event('resolve','b',5,{resolved:true}),event('delete','c',6)]}});
 expect(document.querySelector('.bf-review-count')?.textContent).toBe('1');
});

it("honors project appearance while retaining the company and other reader preferences",()=>{
 const meta=document.createElement('meta');meta.name='margen-theme-policy';meta.content='project';document.head.append(meta);
 let receive:any;const set=vi.fn(),configure=vi.fn();
 (window as any).NotaTemas={set,get:()=>({family:'liftit',mode:'light'})};(window as any).NotaAudio={configure};
 (window as any).BottifactReviewBridge={subscribe:(fn:any)=>receive=fn,controlsReady:vi.fn()};
 window.eval(source);document.dispatchEvent(new Event('DOMContentLoaded'));
 receive({verified:true,permissions:{comment:true},reader:{preferences:{theme:'hacker',mode:'dark',sound:false}}});
 expect(set).not.toHaveBeenCalled();expect(configure).toHaveBeenCalledWith({preferred:false,volume:undefined});
 meta.remove();delete (window as any).NotaTemas;delete (window as any).NotaAudio;
});
it("hides empty badges and prevents deck navigation while editing feedback", () => {
  document.body.innerHTML='<div class="revision-barra"><button>Comment</button><button>0</button></div><textarea></textarea>';
  window.eval(source);document.dispatchEvent(new Event('DOMContentLoaded'));
  expect((document.querySelector('.bf-review-count') as HTMLElement).hidden).toBe(true);
  const navigate=vi.fn();window.addEventListener('keydown',navigate);
  const event=new KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true,cancelable:true});
  document.querySelector('textarea')!.dispatchEvent(event);
  expect(navigate).not.toHaveBeenCalled();expect(event.defaultPrevented).toBe(false);
  window.removeEventListener('keydown',navigate);
  document.dispatchEvent(new CustomEvent('bottifact:review-count',{detail:{open:2}}));
  expect((document.querySelector('.bf-review-count') as HTMLElement).hidden).toBe(false);
});
