/* Community source is data. It is never mounted into the portal DOM. */
window.MargenDevelopers = (() => {
  const REPO = "https://github.com/angelbotto/margen";
  const labels = { theme: "Tema", component: "Componente", bundled: "Incluido en Margen", approved: "Comunidad · revisado", pending: "Pendiente de revisión", changes_requested: "Cambios solicitados", withdrawn: "Retirado", draft: "Creación personal" };
  const el = (tag, text, cls) => {
    const node = document.createElement(tag);
    if (text != null) node.textContent = text;
    if (cls) node.className = cls;
    return node;
  };
  const button = (text, action, cls) => {
    const b = el("button", text, cls); b.type = "button";
    b.addEventListener("click", action); return b;
  };
  const link = (text, url) => {
    const a = el("a", text, "button"); a.href = url;
    if (url.startsWith("https://")) { a.target = "_blank"; a.rel = "noopener noreferrer"; }
    return a;
  };
  const normalize = value => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  let generation = 0;
  const destroy = () => { generation++; };
  function saveJSON(value, filename) {
    const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], { type: "application/json" }));
    const a = link("Descargar", url); a.download = filename; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function template(kind) {
    const palette = { papel: "#fbf4e9", panel: "#fffaf2", "panel-2": "#f3e7d6", tinta: "#2d1b28", "tinta-2": "#5a204c", "tinta-3": "#77636f", naranja: "#805b1f", verde: "#42643e", rojo: "#a53843", azul: "#3e6379" };
    return { schema: 1, slug: "mi-" + kind, version: "1.0.0", kind, title: "Mi aporte", description: "Explica cuándo usarlo, sus límites y cómo probarlo.", license: "MIT", source_url: "",
      content: kind === "theme" ? { light: palette, dark: { ...palette, papel: "#180611", panel: "#290c24", "panel-2": "#3b1233", tinta: "#fffaf2", "tinta-2": "#f0dfaa", "tinta-3": "#c9b5c2", naranja: "#d9bd77", verde: "#a8cc9b", rojo: "#f09caa", azul: "#a2c9db" } } : '<section class="prosa" id="mi-aporte"><h2>Una idea clara</h2><p>Contenido de ejemplo. Sustituye estos datos antes de compartir.</p></section>' };
  }

  async function render({ root, api, user, section = "developers" }) {
    if (!["components", "themes", "developers"].includes(section)) section = "developers";
    const ticket = ++generation;
    const current = () => ticket === generation && root.isConnected;
    root.className = "developers-view developers-" + section;
    root.replaceChildren();
    const intro = el("section", null, "developers-intro");
    const heading = el("div");
    const copy = {
      components: ["Biblioteca", "Componentes", "Explora un ejemplo, consulta cómo usarlo y copia el código para tu documento."],
      themes: ["Diseño", "Temas", "Paletas y tipografías para dar una voz propia a tus documentos. Explora un tema o crea tu versión."],
      developers: ["Open source · MIT", "Construye con Margen", "Contribuye a la biblioteca, comparte una receta o mejora el sistema. Aquí encontrarás las herramientas para trabajar con código."]
    }[section];
    heading.append(el("p", copy[0], "eyebrow"), el("h2", copy[1]), el("p", copy[2], "lede"));
    intro.append(heading); root.append(intro);
    const status = el("p", "Cargando catálogo…", "developers-status"); status.setAttribute("role", "status"); root.append(status);
    let catalog;
    try { catalog = await api("/api/developers/catalog"); }
    catch (error) { if (current()) { status.textContent = error.message; root.append(button("Reintentar", () => render({ root, api, user, section }))); } return; }
    if (!current()) return;
    function saved(result) {
      const next = new URL(result.url, location.origin);
      next.searchParams.set("view", section);
      history.replaceState(null, "", next.pathname + next.search);
      render({ root, api, user, section });
    }
    const create = el("div", null, "developer-actions studio-entry");
    if (section !== "developers") {
      const kind = section === "themes" ? "theme" : "component";
      if (catalog.can_submit) create.append(button(kind === "theme" ? "Crear un tema" : "Crear componente visual", () => window.MargenStudio.open({ root, api, kind, onSaved: saved }), kind === "theme" ? "primary" : ""));
      else create.append(link("Entrar para crear", "/login"));
      create.append(link("Contribuir con código ↗", "/?view=developers"));
      heading.append(create);
    } else heading.append(link("Código y guía de contribución ↗", REPO));
    const all = catalog.items.filter(item => section === "developers" || item.kind === (section === "themes" ? "theme" : "component"));
    status.textContent = section === "developers" ? "La biblioteca y sus fuentes están disponibles bajo licencia MIT." : `${all.length} ${section === "themes" ? "temas" : "componentes"}${catalog.community_truncated ? " · Se muestran los 200 aportes más recientes de la comunidad" : ""}`;
    const toolbar = el("div", null, "developers-toolbar");
    const searchLabel = el("label", section === "components" ? "Buscar componentes" : section === "themes" ? "Buscar temas" : "Buscar aportes");
    const search = el("input"); search.type = "search"; search.placeholder = section === "components" ? "Tablas, gráficas, diagramas…" : section === "themes" ? "Nombre, paleta o estilo…" : "Nombre o autor…"; searchLabel.append(search);
    const nav = el("div", null, "developers-tabs"); nav.setAttribute("role", "group"); nav.setAttribute("aria-label", "Filtrar catálogo");
    toolbar.append(searchLabel, nav);
    const results = el("section", null, section === "components" ? "component-index" : section === "themes" ? "developers-grid" : "developer-submissions");
    results.setAttribute("aria-label", section === "components" ? "Índice de componentes" : section === "themes" ? "Catálogo de temas" : "Aportes");
    const resultStatus = el("p", "", "muted"); resultStatus.setAttribute("role", "status");
    const docs = el("article", null, "component-documentation");
    let selected = section === "developers" ? "mine" : "all", rows = section === "developers" ? [] : all, limit = 12, queryRevision = 0, activeItem = "";
    const more = button("Mostrar más", () => { limit += 12; draw(); }, "developers-more");
    if (section === "components") {
      const layout = el("div", null, "component-docs-layout"), index = el("aside", null, "component-navigation");
      index.append(toolbar, resultStatus, results); layout.append(index, docs); root.append(layout);
    } else root.append(toolbar, resultStatus, results, more);
    const filters = section === "developers" ? [] : [["all", "Todos"], ["favorite", "Favoritos"]];
    if (catalog.can_submit) filters.push(["mine", "Mis aportes"]);
    if (section === "developers" && catalog.admin) filters.push(["review", "Revisar aportes"]);
    for (const [id, text] of filters) {
      const b = button(text, async () => {
        selected = id; limit = 12;
        const revision = ++queryRevision;
        nav.querySelectorAll("button").forEach(n => n.setAttribute("aria-pressed", String(n === b)));
        rows = []; draw();
        if (id === "mine" || id === "review") {
          resultStatus.textContent = "Consultando aportes…";
          try {
            const data = await api("/api/developers/submissions" + (id === "review" ? "?scope=review" : ""));
            if (!current() || queryRevision !== revision) return;
            rows = data.items.filter(item => section === "developers" || item.kind === (section === "themes" ? "theme" : "component")); draw();
            if (data.truncated) resultStatus.textContent += " · Se muestran los 200 más recientes.";
          } catch (error) { if (current() && revision === queryRevision) resultStatus.textContent = error.message; }
        } else { rows = all; draw(); }
      });
      b.dataset.filter = id; b.setAttribute("aria-pressed", String(id === selected)); nav.append(b);
    }
    search.addEventListener("input", () => { limit = 12; draw(); });
    function draw() {
      results.replaceChildren();
      const q = normalize(search.value.trim());
      const filtered = rows.filter(i => (selected === "theme" || selected === "component" ? i.kind === selected : selected === "favorite" ? i.favorite : true) && normalize([i.title, i.description, i.category, i.author].join(" ")).includes(q));
      resultStatus.textContent = `${filtered.length} resultados`;
      more.hidden = section === "components" || filtered.length <= limit;
      if (!filtered.length) results.append(el("p", selected === "favorite" ? "Guarda un tema o componente para encontrarlo aquí." : "No hay aportes para esta búsqueda.", "developers-empty"));
      const groups = new Map();
      for (const item of (section === "components" ? filtered : filtered.slice(0, limit))) {
        if (section === "components") {
          const category = item.category || "Comunidad";
          if (!groups.has(category)) {
            const group = el("div", null, "component-index-group");
            group.append(el("h3", category)); groups.set(category, group); results.append(group);
          }
          const entry = button(item.title, () => openComponent(item), "component-index-link");
          entry.dataset.item = item.id; entry.setAttribute("aria-current", item.id === activeItem ? "page" : "false");
          groups.get(category).append(entry); continue;
        }
        if (section === "developers") {
          const row = el("article", null, "developer-submission-row");
          row.append(el("div", item.title), el("span", `${labels[item.kind]} · ${labels[item.status] || item.status}`, "muted"), button(selected === "review" ? "Revisar aporte" : "Ver detalles", () => inspect(item)));
          results.append(row); continue;
        }
        const card = el("article", null, "developer-card");
        const visual = el("iframe", null, "developer-preview"); visual.title = "Vista estática de " + item.title;
        visual.setAttribute("sandbox", ""); visual.loading = "lazy"; visual.tabIndex = -1; visual.setAttribute("aria-hidden", "true");
        visual.src = "/api/developers/items/" + encodeURIComponent(item.id) + "/preview";
        const text = el("div", null, "developer-card-body");
        text.append(el("p", `${labels[item.kind]} · ${labels[item.status] || item.status}`, "eyebrow"), el("h3", item.title), el("p", item.description, "developer-description"), el("p", `${item.author} · ${item.license}`, "meta"));
        const actions = el("div", null, "developer-actions");
        actions.append(button(selected === "review" ? "Revisar aporte" : "Ver detalles", () => inspect(item)));
        if (item.status === "approved" || item.status === "bundled") {
          const fav = button(item.favorite ? "Guardado" : "Guardar", async () => {
            if (!catalog.can_submit) { location.href = "/login"; return; }
            fav.disabled = true;
            try {
              const updated = await api(`/api/developers/items/${item.id}/favorite`, { method: "PUT", body: JSON.stringify({ favorite: !item.favorite }) });
              if (!current()) return;
              Object.assign(item, updated); fav.textContent = item.favorite ? "Guardado" : "Guardar"; fav.setAttribute("aria-pressed", String(item.favorite));
              if (selected === "favorite") draw();
            } catch (error) { if (current()) resultStatus.textContent = error.message; }
            finally { fav.disabled = false; }
          });
          fav.setAttribute("aria-label", "Guardar " + item.title); fav.setAttribute("aria-pressed", String(!!item.favorite)); actions.append(fav);
        }
        text.append(actions); card.append(visual, text); results.append(card);
      }
    }
    function openComponent(item, updateURL = true) {
      activeItem = item.id;
      results.querySelectorAll("[data-item]").forEach(entry => entry.setAttribute("aria-current", entry.dataset.item === item.id ? "page" : "false"));
      if (updateURL) {
        const url = new URL(location.href); url.searchParams.set("view", "components"); url.searchParams.set("item", item.id);
        history.replaceState(null, "", url.pathname + url.search);
      }
      return inspect(item, true);
    }
    async function inspect(item, inline = false) {
      const dialog = el(inline ? "section" : "dialog", null, inline ? "component-detail" : "developer-dialog");
      const header = el("div", null, "dialog-head"); const title = el("h2", item.title); title.id = "developer-detail-title";
      header.append(title);
      if (!inline) header.append(button("Cerrar", () => dialog.close()));
      dialog.append(header); dialog.setAttribute("aria-labelledby", title.id);
      const state = el("p", "Cargando aporte…", "component-meta"); state.setAttribute("role", "status"); dialog.append(state);
      if (inline) { dialog.close = () => {}; docs.replaceChildren(dialog); }
      else { root.append(dialog); dialog.addEventListener("close", () => dialog.remove(), { once: true }); dialog.showModal(); }
      try {
        const detail = await api("/api/developers/items/" + encodeURIComponent(item.id));
        if (!current() || !dialog.isConnected) return;
        title.textContent = detail.title;
        state.textContent = `${detail.author} · ${detail.license} · ${detail.version} · ${labels[detail.status]}`;
        dialog.append(el("p", (detail.description || "").replace(/^\*\*Use and limits:\*\*\s*/, "Uso y límites: ")));
        if (detail.credits) dialog.append(el("p", "Créditos: " + detail.credits, "muted"));
        const frame = el("iframe", null, "developer-detail-preview"); frame.title = "Ejemplo de " + detail.title; frame.setAttribute("sandbox", detail.origin === "bundled" && detail.preview_runtime?.length ? "allow-scripts" : "");
        frame.src = `/api/developers/items/${item.id}/preview`;
        if (detail.kind === "component") {
          const example = el("section", null, "component-example");
          const tabs = el("div", null, "component-example-toolbar"); tabs.setAttribute("role", "group"); tabs.setAttribute("aria-label", "Vista del ejemplo");
          const code = el("pre", detail.content || "", "component-code"); code.tabIndex = 0; code.hidden = true;
          const previewTab = button("Vista previa", () => toggle(false)), codeTab = button("Código", () => toggle(true));
          function toggle(showCode) { code.hidden = !showCode; frame.hidden = showCode; previewTab.setAttribute("aria-pressed", String(!showCode)); codeTab.setAttribute("aria-pressed", String(showCode)); }
          toggle(false);
          const copy = button("Copiar HTML", async () => {
            try { await navigator.clipboard.writeText(detail.content || ""); copy.textContent = "Copiado"; }
            catch { toggle(true); state.textContent = "Selecciona el código para copiarlo. El navegador no permitió usar el portapapeles."; code.focus(); }
          });
          tabs.append(previewTab, codeTab, copy); example.append(tabs, frame, code); dialog.append(example);
          const usage = el("section", null, "component-usage");
          usage.append(el("h3", "Uso"), el("p", "Copia el HTML en el contenido de tu documento Margen y sustituye los datos de ejemplo. Conserva las clases, los atributos y el texto accesible de la receta."));
          if (detail.origin === "bundled") usage.append(el("p", "Con tu agente: pide usar «" + (detail.slug || detail.title) + "» de la biblioteca Margen. La fuente incluye su ejemplo y los límites de uso."));
          const deps = (detail.dependencies || []).filter(value => typeof value === "string");
          if (deps.length) { const list = el("ul", null, "component-dependencies"); deps.forEach(value => list.append(el("li", value))); usage.append(el("h3", "Dependencias"), list); }
          dialog.append(usage);
        } else dialog.append(frame);
        if (detail.kind === "theme") {
          const modes = el("div", null, "developer-actions");
          for (const [value, name] of [["light", "Claro"], ["dark", "Oscuro"]]) modes.append(button(name, () => { frame.src = `/api/developers/items/${item.id}/preview?mode=${value}`; }));
          dialog.append(modes);
        }
        dialog.append(el("p", detail.kind === "theme" ? "Prueba este tema en un artefacto nuevo o prepara una revisión de uno existente." : (detail.origin === "bundled" && detail.preview_runtime?.length ? "El ejemplo ejecuta los módulos incluidos de la biblioteca. Copia el HTML junto con sus dependencias para conservar este comportamiento." : "Esta vista muestra el HTML/SVG estático. Consulta las dependencias y la fuente para integrar la receta completa."), "muted"));
        if (catalog.can_submit && detail.kind === "theme") {
          const use = el("section", null, "community-use");
          const useActions = el("div", null, "developer-actions");
          useActions.append(button(detail.kind === "theme" ? "Crear artefacto con este tema" : "Crear artefacto estático", async event => {
            const b = event.currentTarget; b.disabled = true;
            try {
              const result = await api(`/api/developers/items/${detail.id}/use`, { method: "POST", body: JSON.stringify({ title: detail.title }) });
              if (dialog.isConnected) location.href = result.url;
            } catch (error) { if (dialog.isConnected) state.textContent = error.message; b.disabled = false; }
          }, "primary"));
          useActions.append(button("Crear mi versión", () => { dialog.close(); window.MargenStudio.open({ root, api, initial: detail, onSaved: saved }); }));
          use.append(useActions);
          use.append(el("p", "El nuevo artefacto será privado. Puedes editarlo y compartirlo desde el lector.", "muted"));
          if (detail.kind === "theme") {
            const targetLabel = el("label", "Aplicar a uno de mis artefactos"); const target = el("select");
            target.append(el("option", "Elige un artefacto…")); target.firstChild.value = ""; targetLabel.append(target);
            const apply = button("Preparar revisión con este tema", async () => {
              const option = target.selectedOptions[0]; if (!target.value) { target.focus(); return; }
              apply.disabled = true;
              try {
                const result = await api(`/api/developers/items/${detail.id}/use`, { method: "POST", body: JSON.stringify({ artifact: target.value, expected_current: option.dataset.version }) });
                if (dialog.isConnected) location.href = result.preview_url;
              } catch (error) { if (dialog.isConnected) state.textContent = error.message; apply.disabled = false; }
            });
            use.append(targetLabel, apply, el("p", "Abre la revisión y pulsa Publicar esta versión cuando quieras que la vean sus lectores. El enlace y los permisos se conservan.", "muted"));
            api("/api/developers/targets").then(data => {
              if (!dialog.isConnected) return;
              for (const item of data.items) { const option = el("option", item.title); option.value = item.id; option.dataset.version = item.current_version; target.append(option); }
              if (data.truncated) use.append(el("p", "Se muestran tus 200 artefactos más recientes.", "muted"));
            }).catch(error => { if (dialog.isConnected) state.textContent = error.message; });
          }
          dialog.append(use);
        }
        if (catalog.can_submit && detail.kind === "component") {
          const variants = el("div", null, "developer-actions");
          variants.append(button(detail.design ? "Crear una variante visual" : "Editar una copia del código", () => { dialog.close(); window.MargenStudio.open({ root, api, initial: detail, onSaved: saved }); }));
          dialog.append(variants);
        }
        if (detail.mine) {
          const sharing = el("fieldset"); sharing.append(el("legend", "Comparte tu creación"));
          const rightsLabel = el("label", null, "developer-check"), rights = el("input"); rights.type = "checkbox";
          rightsLabel.append(rights, document.createTextNode("Puedo compartir esta creación bajo su licencia y acepto publicar mi nombre de perfil.")); sharing.append(rightsLabel);
          const publication = el("div", null, "developer-actions");
          for (const [value, text] of [["shared", "Compartir por enlace"], ["review", "Solicitar inclusión en catálogo"], ["private", "Dejar privado"]]) {
            publication.append(button(text, async () => {
              if (value !== "private" && !rights.checked) { state.textContent = "Confirma los derechos antes de compartir."; rights.focus(); return; }
              publication.querySelectorAll("button").forEach(b => b.disabled = true);
              try {
                const result = await api(`/api/developers/submissions/${detail.id}/publication`, { method: "PUT", body: JSON.stringify({ publication: value, revision: detail.revision, rights_accepted: rights.checked, public_listing_accepted: rights.checked }) });
                if (dialog.isConnected) { dialog.close(); saved(result); }
              } catch (error) { if (dialog.isConnected) state.textContent = error.message; }
              finally { publication.querySelectorAll("button").forEach(b => b.disabled = false); }
            }));
          }
          sharing.append(publication); dialog.append(sharing);
        }
        if (detail.visibility === "unlisted" || detail.status === "approved") {
          const label = el("label", "Enlace para compartir"); const url = el("input"); url.readOnly = true; url.value = location.origin + "/?view=developers&item=" + detail.id; url.addEventListener("focus", () => url.select()); label.append(url); dialog.append(label);
        }
        const actions = el("div", null, "developer-actions");
        actions.append(link("Descargar fuente JSON", `/api/developers/items/${item.id}/download`));
        if (detail.source_url) actions.append(link("Ver origen ↗", detail.source_url));
        actions.append(link("Proponer una mejora ↗", REPO + "/issues/new?title=" + encodeURIComponent("Mejora: " + detail.title)));
        if (detail.kind === "component" && ["bundled", "approved"].includes(detail.status)) {
          const favorite = button(detail.favorite ? "Guardado" : "Guardar", async () => {
            if (!catalog.can_submit) { location.href = "/login"; return; }
            favorite.disabled = true;
            try {
              const updated = await api(`/api/developers/items/${detail.id}/favorite`, { method: "PUT", body: JSON.stringify({ favorite: !detail.favorite }) });
              if (!current() || !dialog.isConnected) return;
              detail.favorite = updated.favorite; const row = all.find(row => row.id === detail.id); if (row) row.favorite = updated.favorite;
              favorite.textContent = detail.favorite ? "Guardado" : "Guardar"; favorite.setAttribute("aria-pressed", String(detail.favorite));
              if (selected === "favorite") draw();
            } catch (error) { if (dialog.isConnected) state.textContent = error.message; }
            finally { favorite.disabled = false; }
          });
          favorite.setAttribute("aria-pressed", String(!!detail.favorite)); actions.append(favorite);
        }
        dialog.append(actions);
        const code = el("details", null, "developer-source"); code.append(el("summary", "Inspeccionar código y dependencias"));
        const pre = el("pre", JSON.stringify(detail, null, 2)); pre.tabIndex = 0; code.append(pre); dialog.append(code);
        dialog.append(el("p", detail.origin === "bundled" ? "Incluido en la biblioteca. Puedes pedirle a tu agente que lo use por su nombre o identificador: " + detail.slug + "." : "Creación de la comunidad. Puedes usarla desde el portal sin cambiar el código de Margen. La vista de componentes usa HTML/SVG estático; la lógica nueva se revisa como extensión del sistema.", "muted"));
        if (item.review) dialog.append(el("p", "Revisión: " + item.review));
        if (catalog.admin && detail.origin === "community" && ["pending", "approved"].includes(detail.status)) {
          const review = el("fieldset"); review.append(el("legend", "Revisión de la comunidad"));
          review.append(el("p", "Revisa autoría, licencia, legibilidad en ambos modos y comportamiento esperado. Publicar hace visible la fuente para todos los visitantes del catálogo."));
          const label = el("label", "Nota para el autor"); const note = el("textarea"); note.maxLength = 2000; label.append(note); review.append(label);
          const controls = el("div", null, "developer-actions");
          for (const [status, text] of [["approved", "Publicar en catálogo"], ["changes_requested", "Solicitar cambios"], ["withdrawn", "Retirar del catálogo"]]) {
            if (status === detail.status || (detail.status !== "pending" && status !== "withdrawn")) continue;
            controls.append(button(text, async () => {
              if (status !== "approved" && !note.value.trim()) { state.textContent = "Escribe una nota para el autor."; note.focus(); return; }
              controls.querySelectorAll("button").forEach(b => b.disabled = true);
              try {
                await api(`/api/developers/submissions/${item.id}/review`, { method: "PUT", body: JSON.stringify({ status, note: note.value, revision: detail.revision }) });
                if (!current() || !dialog.isConnected) return;
                dialog.close(); await render({ root, api, user, section });
              } catch (error) { if (dialog.isConnected) state.textContent = error.message; }
              finally { controls.querySelectorAll("button").forEach(b => b.disabled = false); }
            }));
          }
          review.append(controls); dialog.append(review);
        }
      } catch (error) { if (dialog.isConnected) state.textContent = error.message; }
    }
    draw();
    const contribute = el("section", null, "developers-contribute");
    contribute.append(el("p", "Con código", "eyebrow"));
    contribute.append(el("p", "Tu próximo aporte", "eyebrow"), el("h2", "Comparte una pieza. Mejora el sistema."), el("p", "Envía un tema con colores claros y oscuros, o una receta HTML/SVG. El equipo revisa el aporte antes de publicarlo. Las extensiones con lógica nueva se integran mediante un pull request."));
    const guides = el("div", null, "developer-actions");
    guides.append(button("Plantilla de tema ↓", () => saveJSON(template("theme"), "margen-theme.json")), button("Plantilla de componente ↓", () => saveJSON(template("component"), "margen-component.json")), link("Guía de contribución ↗", REPO + "/blob/main/docs/contributing-components.md"));
    contribute.append(guides);
    if (catalog.can_submit) {
      const form = el("form", null, "developer-submit");
      const fileLabel = el("label", "Tu paquete JSON · máximo 150 KB"); const file = el("input"); file.type = "file"; file.accept = ".json,application/json"; file.required = true; fileLabel.append(file); form.append(fileLabel);
      const rightsLabel = el("label", null, "developer-check"); const rights = el("input"); rights.type = "checkbox"; rights.required = true; rightsLabel.append(rights, document.createTextNode("Soy autor o tengo permiso para compartir este contenido bajo la licencia indicada."));
      const publicLabel = el("label", null, "developer-check"); const publicCheck = el("input"); publicCheck.type = "checkbox"; publicCheck.required = true; publicLabel.append(publicCheck, document.createTextNode("Acepto que mi nombre de perfil y la fuente del aporte sean públicos si se aprueba. No incluye datos privados."));
      const send = el("button", "Enviar a revisión", "primary"); send.type = "submit";
      const message = el("p", "", "developers-status"); message.setAttribute("role", "status");
      form.append(rightsLabel, publicLabel, send, message);
      form.addEventListener("submit", async event => {
        event.preventDefault(); if (!form.reportValidity()) return;
        const picked = file.files?.[0]; if (!picked) return;
        if (picked.size > 150000) { message.textContent = "El archivo supera los 150 KB."; return; }
        send.disabled = true;
        try {
          let value;
          try { value = JSON.parse(await picked.text()); }
          catch { throw new Error("El archivo no contiene JSON válido. Usa una de las plantillas."); }
          if (!current()) return;
          await api("/api/developers/submissions", { method: "POST", body: JSON.stringify({ package: value, rights_accepted: rights.checked, public_listing_accepted: publicCheck.checked }) });
          if (!current()) return;
          form.reset(); message.textContent = "Aporte enviado. Sigue su estado en Mis aportes; todavía no es público.";
        } catch (error) { if (current()) message.textContent = error.message; }
        finally { send.disabled = false; }
      });
      contribute.append(form);
    } else contribute.append(link("Entrar para aportar", "/login"));
    if (section === "developers") {
      const noCode = el("p", null, "developers-no-code"); noCode.append(document.createTextNode("¿Prefieres crear visualmente? "), link("Editor de temas", "/?view=themes"), document.createTextNode(" "), link("Componentes visuales", "/?view=components"));
      contribute.prepend(noCode); root.append(contribute);
      if (catalog.can_submit) nav.querySelector('[data-filter="mine"]')?.click();
      else { toolbar.hidden = true; resultStatus.hidden = true; }
    }
    const requestedItem = new URLSearchParams(location.search).get("item");
    if (requestedItem && /^[a-zA-Z0-9_-]{1,120}$/.test(requestedItem)) {
      const item = all.find(item => item.id === requestedItem) || { id: requestedItem, title: "Creación compartida" };
      if (section === "components") await openComponent(item, false); else await inspect(item);
    } else if (section === "components") {
      const first = all.find(item => item.slug === "bar-chart") || all[0];
      if (first) await openComponent(first, false); else docs.append(el("p", "Todavía no hay componentes disponibles.", "muted"));
    }
  }
  return { render, destroy, template };
})();
