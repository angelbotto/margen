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

  async function render({ root, api, user }) {
    const ticket = ++generation;
    const current = () => ticket === generation && root.isConnected;
    root.className = "developers-view";
    root.replaceChildren();
    const intro = el("section", null, "developers-intro");
    const heading = el("div");
    heading.append(el("p", "Hecho para construir juntos", "eyebrow"), el("h2", "Dale tu forma a Margen."), el("p", "Encuentra temas, componentes y diagramas. Guarda los que te sirven y comparte lo que crees.", "lede"));
    const open = el("aside", null, "developers-open");
    open.append(el("strong", "Open source · MIT"), el("p", "Puedes estudiar el código, modificarlo y contribuir. No necesitas aportar código: ejemplos, traducciones y mejoras de accesibilidad también cuentan."), link("Ver código y contribuir ↗", REPO));
    intro.append(heading, open); root.append(intro);
    const status = el("p", "Cargando catálogo…", "developers-status"); status.setAttribute("role", "status"); root.append(status);
    let catalog;
    try { catalog = await api("/api/developers/catalog"); }
    catch (error) { if (current()) { status.textContent = error.message; root.append(button("Reintentar", () => render({ root, api, user }))); } return; }
    if (!current()) return;
    function saved(result) {
      history.replaceState(null, "", result.url);
      render({ root, api, user });
    }
    if (catalog.can_submit) {
      const create = el("div", null, "developer-actions studio-entry");
      create.append(button("Crear un tema", () => window.MargenStudio.open({ root, api, kind: "theme", onSaved: saved }), "primary"), button("Crear un componente", () => window.MargenStudio.open({ root, api, kind: "component", onSaved: saved })));
      intro.firstElementChild.append(create);
    }
    const all = catalog.items;
    const themeCount = all.filter(item => item.kind === "theme").length;
    status.textContent = `${themeCount} temas · ${all.length - themeCount} componentes y recetas${catalog.community_truncated ? " · Se muestran los 200 aportes más recientes de la comunidad" : ""}`;
    const toolbar = el("div", null, "developers-toolbar");
    const searchLabel = el("label", "Buscar en el catálogo");
    const search = el("input"); search.type = "search"; search.placeholder = "Un tema, un diagrama, una idea…"; searchLabel.append(search);
    const nav = el("div", null, "developers-tabs"); nav.setAttribute("role", "group"); nav.setAttribute("aria-label", "Filtrar catálogo");
    toolbar.append(searchLabel, nav); root.append(toolbar);
    const results = el("section", null, "developers-grid"); results.setAttribute("aria-label", "Catálogo de temas y componentes");
    const resultStatus = el("p", "", "muted"); resultStatus.setAttribute("role", "status");
    root.append(resultStatus, results);
    let selected = "all", rows = all, limit = 12, queryRevision = 0;
    const more = button("Mostrar más", () => { limit += 12; draw(); }, "developers-more"); root.append(more);
    const filters = [["all", "Todos"], ["theme", "Temas"], ["component", "Componentes y diagramas"], ["favorite", "Favoritos"]];
    if (catalog.can_submit) filters.push(["mine", "Mis aportes"]);
    if (catalog.admin) filters.push(["review", "Revisar aportes"]);
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
            rows = data.items; draw();
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
      more.hidden = filtered.length <= limit;
      if (!filtered.length) results.append(el("p", selected === "favorite" ? "Guarda un tema o componente para encontrarlo aquí." : "No hay aportes para esta búsqueda.", "developers-empty"));
      for (const item of filtered.slice(0, limit)) {
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
    async function inspect(item) {
      const dialog = el("dialog", null, "developer-dialog");
      const header = el("div", null, "dialog-head"); const title = el("h2", item.title); title.id = "developer-detail-title";
      const close = button("Cerrar", () => dialog.close()); header.append(title, close); dialog.append(header); dialog.setAttribute("aria-labelledby", title.id);
      const state = el("p", "Cargando aporte…"); state.setAttribute("role", "status"); dialog.append(state);
      root.append(dialog); dialog.addEventListener("close", () => dialog.remove(), { once: true }); dialog.showModal();
      try {
        const detail = await api("/api/developers/items/" + encodeURIComponent(item.id));
        if (!current() || !dialog.isConnected) return;
        title.textContent = detail.title;
        state.textContent = `${detail.author} · ${detail.license} · ${detail.version} · ${labels[detail.status]}`;
        dialog.append(el("p", detail.description));
        if (detail.credits) dialog.append(el("p", "Créditos: " + detail.credits, "muted"));
        const frame = el("iframe", null, "developer-detail-preview"); frame.title = "Vista estática del aporte"; frame.setAttribute("sandbox", "");
        frame.src = `/api/developers/items/${item.id}/preview`; dialog.append(frame);
        if (detail.kind === "theme") {
          const modes = el("div", null, "developer-actions");
          for (const [value, name] of [["light", "Claro"], ["dark", "Oscuro"]]) modes.append(button(name, () => { frame.src = `/api/developers/items/${item.id}/preview?mode=${value}`; }));
          dialog.append(modes);
        }
        dialog.append(el("p", detail.kind === "theme" ? "Prueba este tema en un artefacto nuevo o prepara una revisión de uno existente." : "Se reutiliza la versión estática: texto, tablas y SVG compatibles. Gráficas generadas por código, controles e interacciones no se incluyen. Para la receta completa, usa la fuente con tu agente.", "muted"));
        if (catalog.can_submit) {
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
                dialog.close(); await render({ root, api, user });
              } catch (error) { if (dialog.isConnected) state.textContent = error.message; }
              finally { controls.querySelectorAll("button").forEach(b => b.disabled = false); }
            }));
          }
          review.append(controls); dialog.append(review);
        }
      } catch (error) { if (dialog.isConnected) state.textContent = error.message; }
    }
    draw();
    const contribute = el("details", null, "developers-contribute");
    contribute.append(el("summary", "Developers · código, extensiones y aportes avanzados"));
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
    root.append(contribute);
    const requestedItem = new URLSearchParams(location.search).get("item");
    if (requestedItem && /^[a-zA-Z0-9_-]{1,120}$/.test(requestedItem)) inspect({ id: requestedItem, title: "Creación compartida" });
  }
  return { render, destroy, template };
})();
