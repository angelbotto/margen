/* Shared, dependency-free interface primitives. Decorative SVG never carries the accessible name. */
(() => {
  "use strict";
  if (window.BottifactUI) return;
  const paths = {
    chart: "M4 3v18h17M8 16v-5M13 16V6M18 16v-8",
    refresh: "M20 7V3l-3 3a8 8 0 1 0 3 9M20 3v5h-5",
    appearance: "M4 5h16M4 12h16M4 19h16M8 3v4M16 10v4M10 17v4",
    comment:
      "M8 18H5l-3 3V6a3 3 0 0 1 3-3h14a3 3 0 0 1 3 3v9a3 3 0 0 1-3 3H8M7 8h10M7 12h6",
    note: "M14 3H5v18h14V8l-5-5Zm0 0v5h5M8 12h8M8 16h5",
    review: "M8 5h13M8 12h13M8 19h13M3 5h.01M3 12h.01M3 19h.01",
    share: "M12 15V3m-4 4 4-4 4 4M5 12v8h14v-8",
    more: "M5 12h.01M12 12h.01M19 12h.01",
    search: "M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14M15 15l6 6",
    filter: "M4 6h16M7 12h10M10 18h4",
    columns: "M3 4h18v16H3ZM10 4v16M16 4v16",
    bookmark: "M6 3h12v18l-6-4-6 4Z",
    table: "M3 4h18v16H3ZM3 10h18M10 4v16",
    cards: "M4 3h16v7H4ZM4 14h16v7H4Z",
    download: "M12 3v12m-4-4 4 4 4-4M4 16v5h16v-5",
    copy: "M8 8h12v13H8ZM16 8V3H3v13h5",
    close: "M6 6l12 12M6 18 18 6",
    plus: "M12 4v16M4 12h16",
    check: "m5 12 4 4L19 6",
    arrow: "M5 12h14m-5-5 5 5-5 5",
    back: "M19 12H5m5-5-5 5 5 5",
    expand: "M9 3H3v6M15 3h6v6M3 15v6h6M21 15v6h-6",
    graph:
      "M7 7l10 5M7 7l3 12M10 19l7-7M7 4a3 3 0 1 0 0 6 3 3 0 0 0 0-6M19 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6M10 16a3 3 0 1 0 0 6 3 3 0 0 0 0-6",
    folder: "M3 6h7l2 3h9v11H3Z",
    clock: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18M12 7v5l3 2",
    globe:
      "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18M3 12h18M12 3c-5 5-5 13 0 18M12 3c5 5 5 13 0 18",
    archive: "M3 3h18v5H3ZM5 8v13h14V8M9 12h6",
    bell: "M5 16h14l-2-3V8a5 5 0 0 0-10 0v5ZM10 20h4",
    agent: "M8 4H4v16h4M16 4h4v16h-4M10 9l-3 3 3 3M14 9l3 3-3 3",
    settings: "M4 5h16M4 12h16M4 19h16M8 3v4M16 10v4M10 17v4",
    logout: "M9 4H4v16h5M10 12h11m-4-4 4 4-4 4",
    up: "M12 20V4m-5 5 5-5 5 5",
    print: "M6 8V3h12v5M6 17H3V9h18v8h-3M6 14h12v7H6Z",
    star: "m12 3 3 6 6 1-4 5 1 6-6-3-6 3 1-6-4-5 6-1Z",
  };
  function icon(name) {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("width", "16");
    svg.setAttribute("height", "16");
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "1.65");
    svg.setAttribute("stroke-linecap", "round");
    svg.setAttribute("stroke-linejoin", "round");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("focusable", "false");
    svg.classList.add("bf-ui-icon");
    const path = document.createElementNS(svg.namespaceURI, "path");
    path.setAttribute("d", paths[name] || paths.more);
    svg.append(path);
    return svg;
  }
  function decorate(node, name, iconOnly = false) {
    if (!node || node.querySelector(":scope > .bf-ui-icon")) return node;
    const label = node.getAttribute("aria-label") || node.textContent.trim();
    const text = document.createElement("span");
    text.className = "bf-control-label";
    text.append(...node.childNodes);
    node.append(icon(name), text);
    node.classList.add("bf-control");
    if (iconOnly) {
      node.classList.add("bf-icon-button");
      node.setAttribute("aria-label", label);
      node.title = label;
    }
    return node;
  }
  // IDENTITY START
  const identityMarkup = "<svg class=\"margen-mark\" width=\"30\" height=\"30\" aria-hidden=\"true\" focusable=\"false\" xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\"><g stroke=\"currentColor\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M16 3 28 10v13l-12 7L4 23V10Z\" stroke-dasharray=\".6 3.2\"/><path d=\"m4 10 12 7 12-7M16 17v13\"/><path d=\"M16 3v13M4 23l12-7 12 7\" opacity=\".35\" stroke-dasharray=\".6 3.2\"/></g></svg>";
  const faviconMarkup = "<link rel=\"icon\" type=\"image/svg+xml\" href=\"data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAzMiAzMiIgZmlsbD0ibm9uZSI+PHN0eWxlPnN2Z3tjb2xvcjojMjgyNzMzfUBtZWRpYShwcmVmZXJzLWNvbG9yLXNjaGVtZTpkYXJrKXtzdmd7Y29sb3I6I2VjZWJmM319PC9zdHlsZT48ZyBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIxLjYiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTE2IDMgMjggMTB2MTNsLTEyIDdMNCAyM1YxMFoiIHN0cm9rZS1kYXNoYXJyYXk9Ii42IDMuMiIvPjxwYXRoIGQ9Im00IDEwIDEyIDcgMTItN00xNiAxN3YxMyIvPjxwYXRoIGQ9Ik0xNiAzdjEzTTQgMjNsMTItNyAxMiA3IiBvcGFjaXR5PSIuMzUiIHN0cm9rZS1kYXNoYXJyYXk9Ii42IDMuMiIvPjwvZz48L3N2Zz4K\">";
  // IDENTITY END
  function mount() {
    for (const brand of document.querySelectorAll('.firma-editorial')) {
      if (!brand.querySelector('.marca-firma,img') && /^Margen(?:Cuadernos)?$/.test(brand.textContent.trim())) {
        brand.innerHTML = identityMarkup;
        brand.setAttribute('aria-label', 'Margen · Inicio');
        brand.title = 'Margen';
      }
    }
    if (!document.querySelector('link[rel="icon"]')) document.head.insertAdjacentHTML('beforeend', faviconMarkup);
    if (document.querySelector("[data-bottifact-interface]")) return;
    const style = document.createElement("style");
    style.dataset.bottifactInterface = "";
    style.textContent = `
    .bf-ui-icon{width:16px;height:16px;flex:none;fill:none;stroke:currentColor;stroke-width:1.65;stroke-linecap:round;stroke-linejoin:round;vertical-align:middle}
    .bf-control{display:inline-flex!important;align-items:center;justify-content:center;gap:7px;font-family:var(--sans,system-ui);font-weight:500;letter-spacing:0}
    .bf-control[hidden]{display:none!important}.bf-control-label{min-width:0}.bf-icon-button .bf-control-label{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}
    .bf-icon-button{width:34px;min-width:34px;padding:0!important}.bf-control:disabled{opacity:.45;cursor:not-allowed;box-shadow:none}
    .bf-control:focus-visible{outline:2px solid var(--foco,var(--accent,#6765cc));outline-offset:3px}
    @media(prefers-reduced-motion:no-preference){.bf-control{transition:background-color 120ms ease-out,border-color 120ms ease-out,color 120ms ease-out,box-shadow 120ms ease-out}.bf-control:active:not(:disabled){transform:translateY(.5px)}}
    @media(pointer:coarse){.bf-control{min-height:44px}.bf-icon-button{min-width:44px}}
    `;
    document.head.append(style);
  }
  window.BottifactUI = { icon, decorate, paths };
  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", mount, { once: true });
  else mount();
})();
