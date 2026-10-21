/* A shared, data-only theme embedded in this document revision. No host credentials. */
(() => {
  const title = /* THEME TITLE */ "Tema compartido";
  function mount() {
    const root = document.documentElement;
    root.setAttribute("data-margen-community-theme", "");
    const key = "margen-community-theme:" + (document.querySelector('meta[name="nota-documento"]')?.content || location.pathname);
    try { if (localStorage.getItem(key) === "off") root.removeAttribute("data-margen-community-theme"); } catch {}
    if (!root.dataset.colorMode) root.dataset.colorMode = matchMedia("(prefers-color-scheme:dark)").matches ? "dark" : "light";
    const original = document.querySelector("[data-apariencia-menu]");
    const target = original?.querySelector(".apariencia-colores")?.parentElement || original?.querySelector(".apariencia-panel");
    const button = document.createElement("button");
    button.type = "button"; button.textContent = "Usar tema: " + title;
    button.className = "bf-theme-favorite";
    button.dataset.communityTheme = "";
    function sync() {
      const active = root.hasAttribute("data-margen-community-theme");
      button.setAttribute("aria-pressed", String(active));
      if (active) document.querySelectorAll("[data-tema-actual]").forEach(n => n.textContent = title);
    }
    button.addEventListener("click", () => {
      root.setAttribute("data-margen-community-theme", "");
      root.removeAttribute("data-community-typography-override");
      try { localStorage.setItem(key, "on"); } catch {}
      sync();
    });
    target?.append(button);
    document.addEventListener("change", event => {
      if (event.target.matches("[data-elegir-tema],[data-tema]")) {
        root.removeAttribute("data-margen-community-theme");
        try { localStorage.setItem(key, "off"); } catch {}
        if (window.NotaTemas) window.NotaTemas.set(window.NotaTemas.get());
      }
      if (event.target.matches("[data-elegir-estilo]")) root.setAttribute("data-community-typography-override", "");
      sync();
    });
    document.addEventListener("nota:tema", sync);
    sync();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount, { once: true }); else mount();
})();
