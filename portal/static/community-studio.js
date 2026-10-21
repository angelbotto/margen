/* Visual creation is the primary path; source-package upload is optional. */
window.MargenStudio = (() => {
  const el = (tag, text, cls) => { const e = document.createElement(tag); if (text != null) e.textContent = text; if (cls) e.className = cls; return e; };
  const fonts = [["geist", "Geist · limpio"], ["instrument", "Instrument Serif · editorial"], ["literata", "Literata · lectura"], ["mono", "Geist Mono · técnico"], ["manrope", "Manrope · moderno"], ["source-serif", "Source Serif 4 · literario"]];
  function open({ root, api, kind = "theme", initial, onSaved }) {
    const seed = JSON.parse(JSON.stringify(initial || window.MargenDevelopers.template(kind)));
    kind = seed.kind;
    const dialog = el("dialog", null, "community-studio");
    const header = el("div", null, "dialog-head");
    const heading = el("h2", kind === "theme" ? "Crea tu tema" : "Crea un componente"); heading.id = "community-studio-title";
    const close = el("button", "Cerrar"); close.type = "button"; close.addEventListener("click", () => dialog.close()); header.append(heading, close); dialog.append(header); dialog.setAttribute("aria-labelledby", heading.id);
    dialog.append(el("p", "Diseña, prueba y comparte desde aquí. No necesitas programar ni abrir un PR.", "muted"));
    const layout = el("div", null, "studio-layout"), form = el("form", null, "studio-form"), sample = el("div", null, "studio-sample");
    const field = (label, input) => { const l = el("label", label); l.append(input); form.append(l); return input; };
    const title = el("input"); title.required = true; title.maxLength = 100; title.value = initial ? initial.title + " · mi versión" : ""; title.placeholder = kind === "theme" ? "Ej. Jardín nocturno" : "Ej. Pasos de una idea"; field("Nombre", title);
    const description = el("textarea"); description.maxLength = 3000; description.value = initial?.description || ""; description.placeholder = "Qué lo hace especial y cuándo usarlo"; field("Descripción", description);
    const mode = el("select"); for (const [value, name] of [["light", "Claro"], ["dark", "Oscuro"]]) { const o = el("option", name); o.value = value; mode.append(o); }
    const modeLabel = el("label", "Vista previa"); modeLabel.append(mode); sample.append(modeLabel);
    const preview = el("iframe", null, "studio-preview"); preview.title = "Vista previa de tu creación"; preview.setAttribute("sandbox", ""); sample.append(preview);
    const previewState = el("p", "Preparando vista previa…", "muted"); previewState.setAttribute("role", "status"); sample.append(previewState);
    let recipe, text, source;
    const type = {};
    if (kind === "theme") {
      form.append(el("p", "Cada modo tiene su propia paleta. Cambia Claro / Oscuro para editar ambos.", "muted"));
      const colors = el("div", null, "studio-colors");
      const names = { papel: "Fondo", panel: "Superficies", "panel-2": "Contraste de superficies", tinta: "Texto", "tinta-2": "Texto secundario", "tinta-3": "Texto tenue", naranja: "Acento y enlaces", verde: "Positivo", rojo: "Atención", azul: "Información" };
      for (const [key, name] of Object.entries(names)) {
        const l = el("label", name), input = el("input"); input.type = "color"; input.value = seed.content.light[key]; input.dataset.token = key;
        input.addEventListener("input", () => { seed.content[mode.value][key] = input.value; schedule(); }); l.append(input); colors.append(l);
      }
      form.append(colors);
      for (const [key, name] of [["heading", "Tipografía de títulos"], ["body", "Tipografía del texto"]]) {
        const select = el("select"); for (const [value, label] of fonts) { const option = el("option", label); option.value = value; select.append(option); }
        select.value = seed.typography?.[key] || (key === "heading" ? "instrument" : "geist"); type[key] = field(name, select);
      }
    } else if (initial && !initial.design) {
      source = el("textarea"); source.rows = 10; source.value = initial.content; source.maxLength = 100000; source.required = true;
      field("Fuente del componente · edición avanzada", source);
      form.append(el("p", "Este componente no fue creado con el editor visual. Conservamos su fuente; puedes editarla aquí o usarla tal como está.", "muted"));
    } else {
      recipe = el("select"); for (const [value, name] of [["card", "Tarjeta editorial"], ["steps", "Lista de pasos"], ["diagram", "Diagrama de flujo vertical"]]) { const o = el("option", name); o.value = value; recipe.append(o); }
      recipe.value = initial?.design?.kind || "card";
      field("Tipo de componente", recipe);
      text = el("textarea"); text.required = true; text.maxLength = 6000; text.rows = 7; text.placeholder = "Una idea por línea\nInvestigar\nProponer\nProbar\nDecidir"; text.value = initial?.design?.text || ""; field("Contenido · hasta 12 bloques", text);
      form.append(el("p", "El diagrama transforma cada línea en un paso. Las herramientas avanzadas admiten HTML/SVG estático; las interacciones nuevas requieren una contribución de código.", "muted"));
    }
    const rightsLabel = el("label", null, "developer-check"), rights = el("input"); rights.type = "checkbox";
    rightsLabel.append(rights, document.createTextNode("Puedo compartir esta creación bajo licencia " + (seed.license || "MIT") + " y acepto publicar mi nombre de perfil al compartirla.")); form.append(rightsLabel);
    const controls = el("div", null, "developer-actions");
    const actions = [["private", "Guardar para mí"], ["shared", "Compartir por enlace"], ["review", "Enviar al catálogo"]];
    const message = el("p", "", "developers-status"); message.setAttribute("role", "status");
    for (const [publication, name] of actions) {
      const b = el("button", name, publication === "shared" ? "primary" : ""); b.type = "button";
      b.addEventListener("click", async () => {
        if (!form.reportValidity()) return;
        if (publication !== "private" && !rights.checked) { message.textContent = "Confirma los derechos y la publicación de tu nombre antes de compartir."; rights.focus(); return; }
        controls.querySelectorAll("button").forEach(n => n.disabled = true);
        try {
          const pack = await packFor(true);
          if (!dialog.isConnected) return;
          const saved = await api("/api/developers/submissions", { method: "POST", body: JSON.stringify({ package: pack, publication, rights_accepted: rights.checked, public_listing_accepted: rights.checked }) });
          if (!dialog.isConnected) return;
          dialog.close(); onSaved(saved);
        } catch (error) { if (dialog.isConnected) message.textContent = error.message; }
        finally { controls.querySelectorAll("button").forEach(n => n.disabled = false); }
      }); controls.append(b);
    }
    form.append(controls, message); layout.append(form, sample); dialog.append(layout); root.append(dialog); dialog.showModal();
    let timer, revision = 0;
    const unique = crypto.randomUUID().slice(0, 6);
    async function packFor(save = false) {
      const name = title.value.trim() || "Mi creación";
      const slug = (name.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 44) || "creacion");
      const result = { schema: 1, kind, slug: "mi-" + slug + "-" + unique, version: "1.0.0", title: name, description: description.value.trim() || "Creado visualmente en Margen.", license: seed.license || "MIT", source_url: seed.source_url || "", credits: [seed.credits, initial?.author].filter(Boolean).join(" · "), content: seed.content };
      if (kind === "theme") result.typography = { heading: type.heading.value, body: type.body.value };
      else if (source) result.content = source.value;
      else {
        result.design = { kind: recipe.value, text: text.value.trim() || "Primer paso\nSiguiente paso" };
        const data = await api("/api/developers/visual-component", { method: "POST", body: JSON.stringify({ kind: recipe.value, title: name, text: text.value.trim() || "Primer paso\nSiguiente paso" }) }); result.content = data.content;
      }
      return result;
    }
    async function refresh() {
      const id = ++revision; previewState.textContent = "Actualizando vista previa…";
      try {
        const pack = await packFor(); if (!dialog.isConnected || id !== revision) return;
        const data = await api("/api/developers/preview?mode=" + mode.value, { method: "POST", body: JSON.stringify({ package: pack }) });
        if (!dialog.isConnected || id !== revision) return;
        preview.src = data.url; previewState.textContent = "Vista previa · " + (mode.value === "dark" ? "oscuro" : "claro");
      } catch (error) { if (dialog.isConnected && id === revision) previewState.textContent = error.message; }
    }
    function schedule() { revision++; clearTimeout(timer); timer = setTimeout(refresh, 700); }
    form.addEventListener("input", schedule); form.addEventListener("change", schedule);
    form.addEventListener("submit", event => event.preventDefault());
    mode.addEventListener("change", () => { if (kind === "theme") form.querySelectorAll("[data-token]").forEach(i => i.value = seed.content[mode.value][i.dataset.token]); schedule(); });
    dialog.addEventListener("close", () => { clearTimeout(timer); revision++; dialog.remove(); }, { once: true });
    refresh();
  }
  return { open };
})();
