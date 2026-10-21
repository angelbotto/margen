/* Bound live document frames; off-screen previews never retain a browsing context. */
window.MargenPreviews = {
  create({limit = 8} = {}) {
    const visible = new Set(), observed = new Set(), live = new Set();
    let scheduled = false, generation = 0;
    const reconcile = () => {
      scheduled = false;
      const candidates = [...visible].filter(node => node.isConnected);
      candidates.sort((a,b) => Math.abs(a.getBoundingClientRect().top-innerHeight/2)-Math.abs(b.getBoundingClientRect().top-innerHeight/2));
      const active = new Set(candidates.slice(0,limit));
      for (const target of live) if (!active.has(target)) { target.querySelector('iframe')?.remove(); live.delete(target); }
      for (const target of active) {
        if (target.querySelector('iframe')) continue;
        const frame=document.createElement('iframe');frame.title='Vista previa de '+target.dataset.title;
        frame.setAttribute('sandbox','');frame.tabIndex=-1;frame.setAttribute('aria-hidden','true');
        frame.addEventListener('load',()=>frame.classList.add('ready'),{once:true});
        frame.src=target.dataset.src;target.prepend(frame);live.add(target);
      }
    };
    const schedule=()=>{if(scheduled)return;scheduled=true;const at=generation;requestAnimationFrame(()=>{if(at===generation)reconcile();});};
    const observer=new IntersectionObserver(entries=>{for(const e of entries){if(!observed.has(e.target))continue;e.isIntersecting?visible.add(e.target):visible.delete(e.target);}schedule();},{rootMargin:'120px 0px'});
    return {
      observe(target){observed.add(target);observer.observe(target);},
      disconnect(){generation++;scheduled=false;observer.disconnect();for(const target of live)target.querySelector('iframe')?.remove();observed.clear();visible.clear();live.clear();},
    };
  }
};
