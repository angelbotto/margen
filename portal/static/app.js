/* Portal de revisión: ningún HTML de un artefacto se inserta en el DOM de la cuenta. */
(() => {
  "use strict";
  const $ = (s) => document.querySelector(s),
    $$ = (s) => [...document.querySelectorAll(s)],
    make = (tag, text, cls) => {
      const el = document.createElement(tag);
      if (text !== undefined) el.textContent = text;
      if (cls) el.className = cls;
      return el;
    };
  let user = null,
    view = "mine",
    items = [],
    current = null,
    grants = [],
    uploadVersion = false,
    poll = null,
    noticePoll = null,
    toastTimer = null,
    sharing = null,
    layout = "grid",
    authOptions = { google: false, email: true },
    commentAnchor = null,
    contextRequested = false,
    editing = null,
    organizing = null,
    nextCursor = null,
    total = 0,
    loading = false,
    requestNumber = 0,
    searchTimer = null,
    listController = null;
  try {
    const saved = localStorage.getItem("bottifact-library-layout");
    if (["grid", "list", "table"].includes(saved)) layout = saved;
  } catch {}
  let advancedFilters = "";
  const selectedArtifacts = new Set();
  let graphInstance = null;
  let graphData = null,
    graphController = null,
    peekNumber = 0,
    lastPeekTrigger = null;
  const K = window.BottifactKnowledge;
  const previews = new ResizeObserver((entries) => {
    for (const e of entries)
      e.target.style.setProperty("--preview-scale", e.contentRect.width / 1000);
  });
  const covers = new IntersectionObserver(
    (entries) => {
      for (const { target, isIntersecting } of entries) {
        if (!isIntersecting) {
          target.querySelector("iframe")?.remove();
          continue;
        }
        if (target.querySelector("iframe")) continue;
        const frame = make("iframe");
        frame.title = "Vista previa de " + target.dataset.title;
        frame.setAttribute("sandbox", "");
        frame.tabIndex = -1;
        frame.setAttribute("aria-hidden", "true");
        frame.addEventListener("load", () => frame.classList.add("ready"), {
          once: true,
        });
        frame.src = target.dataset.src;
        target.prepend(frame);
      }
    },
    { rootMargin: "650px 0px" },
  );
  const more = new IntersectionObserver(
    (entries) => {
      if (
        entries.some((e) => e.isIntersecting) &&
        nextCursor &&
        !loading &&
        layout !== "graph" &&
        layout !== "table"
      )
        load(true).catch((error) => toast(error.message));
    },
    { rootMargin: "400px" },
  );
  more.observe($("#feed-end"));
  $("#load-more").addEventListener("click", () =>
    load(true).catch((error) => toast(error.message)),
  );
  const anchorLabels = {
    exact: "fragmento conservado",
    moved: "posible cambio de ubicación",
    changed: "fragmento modificado",
    missing: "fragmento no localizado",
    ambiguous: "varias coincidencias",
  };
  const labels = {
    private: "Privado",
    invited: "Invitados",
    unlisted: "Con enlace",
    public: "Público",
    external: "Sitio anterior",
  };
  function toast(text) {
    $("#toast").textContent = text;
    $("#toast").hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => ($("#toast").hidden = true), 6000);
  }
  async function api(path, options = {}) {
    const response = await fetch(path, {
      ...options,
      headers: { "Content-Type": "application/json", ...options.headers },
    });
    let data;
    try {
      data = await response.json();
    } catch {
      throw Error("No pudimos contactar al portal. Intenta de nuevo.");
    }
    if (!response.ok) {
      const error = Error(
        typeof data.detail === "string"
          ? data.detail
          : "No se pudo completar la acción.",
      );
      error.status = response.status;
      throw error;
    }
    return data;
  }
  const safe = (fn) => async (event) => {
    try {
      await fn(event);
    } catch (error) {
      toast(error.message);
    }
  };
  async function copy(text) {
    try {
      await navigator.clipboard.writeText(text);
      toast("Copiado con el contexto de la revisión.");
    } catch {
      $("#copy-text").value = text;
      $("#text-dialog").showModal();
    }
  }
  async function identity() {
    ({ user } = await api("/api/session"));
    $("#admin-tab").hidden = !user?.admin;
    $("#identity").textContent = user
      ? user.name +
        (user.admin ? " · administrador" : user.verified ? "" : " · invitado")
      : "Sin sesión";
    $("#logout").hidden = !user;
    $("#login").hidden = !!user?.verified;
    $("#publish").hidden = !user?.verified;
    if ($("#context-tools")) $("#context-tools").hidden = !user?.verified;
    $("#library-description").textContent = user?.verified
      ? "Encuentra una idea, conecta sus temas y retoma el trabajo."
      : "Entra con tu correo para ver tus documentos privados y los que compartieron contigo.";
  }
  const loginURL = () =>
    "/login?next=" + encodeURIComponent(location.pathname + location.search);
  function empty(title, text, login = false) {
    const box = make("div", undefined, "empty");
    box.append(make("h2", title), make("p", text));
    if (login) {
      const a = make("a", "Entrar con mi correo", "button");
      a.href = loginURL();
      box.append(a);
    }
    $("#results").append(box);
  }
  function cover(a) {
    const cover = make("button", undefined, "artifact-preview");
    cover.type = "button";
    cover.setAttribute("aria-label", "Vista previa de " + a.title);
    cover.dataset.src = "/api/artifacts/" + a.id + "/preview";
    cover.dataset.title = a.title;
    cover.append(
      make("span", a.title, "preview-fallback"),
      make("span", "Vista previa", "preview-open"),
    );
    cover.addEventListener("click", () => peek(a));
    previews.observe(cover);
    covers.observe(cover);
    return cover;
  }
  function renderCard(a) {
    const card = make("article", undefined, "card");
    card.dataset.artifact = a.id;
    if (!a.external) card.append(cover(a));
    const body = make("div", undefined, "card-body"),
      meta = make("div", undefined, "card-meta");
    meta.append(
      make("span", a.space),
      make("span", a.archived ? "Archivado" : labels[a.visibility]),
    );
    const heading = make("h2"),
      link = make("a", a.title);
    link.href = a.external ? a.url : "/a/" + a.id;
    heading.append(link);
    body.append(meta, heading);
    const description = a.excerpt || a.description;
    if (description) {
      const p = make("p", undefined, "search-excerpt");
      highlight(p, description);
      body.append(p);
    }
    const chips = make("div", undefined, "chips");
    chips.append(make("span", a.category || "Sin clasificar", "chip category"));
    for (const tag of [
      ...new Set([...(a.tags || []), ...(a.auto_tags || [])]),
    ].slice(0, 3)) {
      const b = make("button", tag, "chip");
      b.title =
        ((a.auto_tags || []).includes(tag) && !(a.tags || []).includes(tag)
          ? "Etiqueta automática. "
          : "") +
        "Filtrar por " +
        tag;
      b.addEventListener("click", () => {
        $("#tag-filter").value = tag;
        load().catch((e) => toast(e.message));
      });
      chips.append(b);
    }
    body.append(chips);
    const bottom = make("div", undefined, "bottom");
    bottom.append(
      make(
        "span",
        new Date(a.updated * 1000).toLocaleDateString("es", {
          day: "numeric",
          month: "short",
        }),
      ),
      make(
        "span",
        a.open_comments
          ? a.open_comments + " pendientes"
          : (a.reading_minutes || 1) + " min de lectura",
      ),
    );
    if (a.drafts)
      bottom.append(
        make(
          "span",
          a.drafts + " borrador" + (a.drafts === 1 ? "" : "es"),
          "draft-dot",
        ),
      );
    const detail = make("button", undefined, "card-edit");
    detail.append(K.icon("peek"));
    detail.title = "Vista previa y contexto";
    detail.setAttribute("aria-label", "Vista previa y contexto de " + a.title);
    detail.addEventListener("click", () => peek(a));
    bottom.append(detail);
    body.append(bottom);
    card.append(body);
    $("#results").append(card);
  }
  function highlight(root, text) {
    const query = $("#search").value.trim();
    if (!query) {
      root.textContent = text;
      return;
    }
    const terms = query
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 16)
      .map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
    const re = new RegExp("(" + terms.join("|") + ")", "gi");
    let last = 0;
    for (const m of text.matchAll(re)) {
      root.append(
        document.createTextNode(text.slice(last, m.index)),
        make("mark", m[0]),
      );
      last = m.index + m[0].length;
    }
    root.append(document.createTextNode(text.slice(last)));
  }
  const hiddenColumns = new Set();
  let tableDensity = "comfortable";
  try {
    const saved = JSON.parse(
      localStorage.getItem("bottifact-table-settings") || "{}",
    );
    for (const name of saved.hidden || []) hiddenColumns.add(name);
    tableDensity = saved.density === "compact" ? "compact" : "comfortable";
  } catch {}
  const columns = [
    ["Documento", "title"],
    ["Categoría", "category"],
    ["Empresa / espacio", "space"],
    ["Origen", "agent"],
    ["Actualizado", "recent"],
    ["Pendientes", "comments"],
    ["Acciones", null],
  ];
  function applyTablePreferences() {
    const table = $(".artifact-table");
    if (!table) return;
    table.dataset.density = tableDensity;
    for (const row of table.rows)
      [...row.cells].forEach(
        (cell, i) =>
          (cell.hidden = i > 0 && i < 6 && hiddenColumns.has(columns[i][0])),
      );
  }
  function renderBatch() {
    let bar = $("#batch-actions");
    if (!bar) {
      bar = make("div", undefined, "context-actions");
      bar.id = "batch-actions";
      $("#results").before(bar);
    }
    bar.replaceChildren();
    bar.hidden = !selectedArtifacts.size;
    if (!selectedArtifacts.size) return;
    bar.append(
      make("span", selectedArtifacts.size + " registros seleccionados por ID"),
    );
    const value = make("input");
    value.placeholder = "Etiqueta o colección";
    value.setAttribute("aria-label", "Etiqueta o colección del lote");
    bar.append(value);
    for (const [action, label] of [
      ["tag", "Añadir etiqueta"],
      ["collection", "Añadir a colección"],
      ["archive", "Archivar"],
      ["restore", "Restaurar"],
    ]) {
      const b = make("button", label);
      b.onclick = safe(async () => {
        const r = await api("/api/context/batch", {
          method: "POST",
          body: JSON.stringify({
            artifacts: [...selectedArtifacts],
            action,
            value: value.value,
          }),
        });
        selectedArtifacts.clear();
        renderBatch();
        toast(r.updated + " artefactos actualizados");
        await load();
      });
      bar.append(b);
    }
    const clear = make("button", "Limpiar selección");
    clear.onclick = () => {
      selectedArtifacts.clear();
      renderBatch();
      renderList();
    };
    bar.append(clear);
  }
  function renderTable() {
    renderBatch();
    const wrap = make("div", undefined, "table-scroll");
    wrap.tabIndex = 0;
    wrap.setAttribute("role", "region");
    wrap.setAttribute(
      "aria-label",
      "Tabla de artefactos, desplazamiento horizontal",
    );
    const table = make("table", undefined, "artifact-table"),
      head = make("thead"),
      tr = make("tr");
    for (const [label, sort] of columns) {
      const th = make("th");
      th.scope = "col";
      if (sort) {
        const b = make("button", label),
          active = $("#sort-order").value === sort,
          dir =
            $("#sort-direction").value ||
            (["recent", "comments"].includes(sort) ? "desc" : "asc");
        b.append(
          make(
            "span",
            active ? (dir === "asc" ? " ↑" : " ↓") : " ↕",
            "sort-indicator",
          ),
        );
        b.setAttribute("aria-label", "Ordenar por " + label);
        b.addEventListener("click", () => {
          $("#sort-direction").value = active
            ? dir === "asc"
              ? "desc"
              : "asc"
            : ["recent", "comments"].includes(sort)
              ? "desc"
              : "asc";
          $("#sort-order").value = sort;
          $("#sort-order").dispatchEvent(new Event("change"));
        });
        th.append(b);
        th.setAttribute(
          "aria-sort",
          active ? (dir === "asc" ? "ascending" : "descending") : "none",
        );
      } else th.textContent = label;
      tr.append(th);
    }
    head.append(tr);
    table.append(head);
    const tbody = make("tbody");
    for (const a of items) {
      const row = make("tr"),
        doc = make("td"),
        title = make("div"),
        link = make("a", a.title);
      if (a.owner === user?.id && !a.external) {
        const check = make("input");
        check.type = "checkbox";
        check.checked = selectedArtifacts.has(a.id);
        check.setAttribute("aria-label", "Seleccionar " + a.title);
        check.onchange = () => {
          check.checked
            ? selectedArtifacts.add(a.id)
            : selectedArtifacts.delete(a.id);
          renderBatch();
        };
        doc.append(check);
      }
      link.href = a.external ? a.url : "/a/" + a.id;
      title.append(
        link,
        make(
          "small",
          labels[a.visibility] +
            (a.drafts ? " · " + a.drafts + " borradores" : ""),
        ),
      );
      if (!a.external) doc.append(cover(a));
      doc.append(title);
      row.append(
        doc,
        make("td", a.category || "Sin clasificar"),
        make("td", a.space),
        make(
          "td",
          [a.source?.agent, a.source?.device].filter(Boolean).join(" · ") ||
            "Sin registrar",
        ),
        make("td", new Date(a.updated * 1000).toLocaleDateString("es")),
        make("td", String(a.open_comments)),
      );
      const action = make("td"),
        b = make("button", undefined, "card-edit");
      b.append(K.icon("peek"));
      b.setAttribute("aria-label", "Vista previa de " + a.title);
      b.addEventListener("click", () => peek(a));
      action.append(b);
      row.append(action);
      tbody.append(row);
    }
    table.append(tbody);
    wrap.append(table);
    wrap.addEventListener("scroll", () => {
      if (
        wrap.scrollTop + wrap.clientHeight >= wrap.scrollHeight - 250 &&
        nextCursor &&
        !loading
      )
        load(true).catch((e) => toast(e.message));
    });
    $("#results").append(wrap);
    applyTablePreferences();
  }
  function queryParams() {
    return new URLSearchParams({
      filters: advancedFilters,
      view,
      q: $("#search").value,
      space: $("#space-filter").value,
      access: $("#access-filter").value,
      sort: $("#sort-order").value,
      collection: $("#collection-filter").value,
      tag: $("#tag-filter").value,
      category: $("#category-filter").value,
      direction: $("#sort-direction").value,
      agent: $("#agent-filter").value,
      review: $("#pending-filter").value,
    });
  }
  async function renderGraph() {
    graphController?.abort();
    graphController = new AbortController();
    const root = $("#results");
    root.className = "graph";
    root.append(make("p", "Conectando tus ideas…", "loading-line"));
    const params = queryParams();
    params.set("graph", "1");
    try {
      const data = await api("/api/artifacts?" + params, {
        signal: graphController.signal,
      });
      if (layout !== "graph") return;
      graphData = data;
      root.replaceChildren();
      let saved = {};
      if (user?.verified) {
        const views = await api("/api/context/views");
        saved =
          views.items.find(
            (v) => v.kind === "graph" && v.name === "Mapa personal",
          )?.body.positions || {};
      }
      if (layout !== "graph") return;
      graphInstance = K.graph(root, data, peek, {
        positions: saved,
        related: (aid) => contextWorkbench.related(aid),
        save: (positions) =>
          api("/api/context/views/graph-" + user.id, {
            method: "PUT",
            body: JSON.stringify({
              kind: "graph",
              name: "Mapa personal",
              body: { positions, items: [] },
            }),
          }),
      });
    } catch (e) {
      if (e.name !== "AbortError") {
        root.replaceChildren(make("p", e.message));
      }
    }
  }
  async function peek(a) {
    if (a.external) {
      location.assign(a.url);
      return;
    }
    lastPeekTrigger = document.activeElement;
    const n = ++peekNumber,
      panel = $("#artifact-peek"),
      body = $("#peek-content");
    panel.hidden = false;
    document.body.classList.add("peeking");
    body.replaceChildren(make("p", "Cargando documento…"));
    $("#close-peek").focus();
    try {
      const detail = await api("/api/artifacts/" + a.id);
      if (n !== peekNumber) return;
      body.replaceChildren();
      const frame = make("iframe");
      frame.title = "Vista previa de " + detail.title;
      frame.setAttribute("sandbox", "");
      frame.src = "/api/artifacts/" + a.id + "/preview";
      const visual = make("div", undefined, "peek-visual");
      visual.append(frame);
      body.append(
        visual,
        make("p", detail.space + " / " + detail.category, "eyebrow"),
        make("h2", detail.title),
      );
      const actions = make("div", undefined, "peek-actions"),
        open = make("a", "Abrir artefacto", "primary button");
      open.href = "/a/" + detail.id;
      actions.append(open);
      if (user?.id === detail.owner) {
        for (const [label, fn] of [
          ["Organizar", () => organization(detail)],
          ["Renombrar", () => rename(detail)],
          ["Compartir", () => openShare(detail.id)],
        ]) {
          const b = make("button", label);
          b.addEventListener("click", safe(fn));
          actions.append(b);
        }
      }
      const contextButton = make("button", "Referencias y conexiones");
      contextButton.addEventListener(
        "click",
        safe(() => contextWorkbench.related(detail.id)),
      );
      actions.append(contextButton);
      body.append(actions);
      const chips = make("div", undefined, "chips");
      for (const t of [
        ...(detail.collections || []),
        ...(detail.tags || []),
        ...(detail.auto_tags || []),
      ])
        chips.append(make("span", t, "chip"));
      body.append(chips);
      if (user?.id === detail.owner) {
        const source = make("section", undefined, "provenance");
        source.append(make("h3", "Retomar el trabajo"));
        const dl = make("dl");
        for (const [label, key] of [
          ["Agente", "agent"],
          ["Sesión", "session"],
          ["Dispositivo", "device"],
        ])
          dl.append(
            make("dt", label),
            make("dd", detail.source?.[key] || "No registrado"),
          );
        source.append(dl);
        const copyButton = make("button", "Copiar contexto para IA");
        copyButton.addEventListener(
          "click",
          safe(() => readerWorkspace.bundle(detail.id)),
        );
        source.append(copyButton);
        body.append(source);
      }
      const related = make("section", undefined, "peek-related");
      related.append(
        make("h3", "Ideas relacionadas"),
        make("p", "Buscando temas compartidos…", "muted"),
      );
      body.append(related);
      const params = new URLSearchParams({ view: "all", graph: "1" }),
        data = await api("/api/artifacts?" + params);
      if (n !== peekNumber) return;
      related.replaceChildren(make("h3", "Ideas relacionadas"));
      const edges = data.edges.filter(
        (e) => e.source === detail.id || e.target === detail.id,
      );
      for (const e of edges) {
        const other = data.nodes.find(
          (x) => x.id === (e.source === detail.id ? e.target : e.source),
        );
        const b = make("button", undefined, "atlas-related");
        b.append(
          make("strong", other.title),
          make("span", e.reasons.join(" · ")),
        );
        b.addEventListener("click", () => peek(other));
        related.append(b);
      }
      if (!edges.length)
        related.append(
          make(
            "p",
            data.truncated
              ? "No hay relaciones en los 120 documentos más recientes. Usa el mapa y sus filtros para ampliar la exploración."
              : "Todavía no hay etiquetas o colecciones compartidas.",
            "muted",
          ),
        );
    } catch (e) {
      if (n === peekNumber) body.replaceChildren(make("p", e.message));
    }
  }
  function closePeek() {
    peekNumber++;
    $("#artifact-peek").hidden = true;
    $("#peek-content").replaceChildren();
    document.body.classList.remove("peeking");
    lastPeekTrigger?.focus();
  }
  $("#close-peek").addEventListener("click", closePeek);
  function feedStatus() {
    const shown = items.length;
    $("#feed-end").hidden =
      ["inbox", "connections", "notifications", "admin"].includes(view) ||
      layout === "graph" ||
      !total;
    $("#feed-status").textContent = loading
      ? "Cargando artefactos…"
      : nextCursor
        ? shown + " de " + total + " artefactos"
        : "Has visto los " + total + " artefactos";
    $("#load-more").hidden = !nextCursor;
    $("#load-more").disabled = loading;
  }
  function renderList() {
    const root = $("#results");
    graphController?.abort();
    graphInstance?.destroy();
    graphInstance = null;
    $("#table-preferences").hidden =
      layout !== "table" ||
      ["inbox", "connections", "notifications", "admin"].includes(view);
    previews.disconnect();
    covers.disconnect();
    root.replaceChildren();
    root.className = "";
    $("#feed-end").hidden = true;
    if (view === "connections") return renderConnections();
    if (view === "admin") return renderAdmin();
    if (view === "notifications") return renderNotifications();
    const filtered =
      view === "inbox"
        ? items.filter(
            (item) =>
              JSON.stringify(item)
                .toLocaleLowerCase()
                .includes($("#search").value.toLocaleLowerCase()) &&
              (!$("#review-kind").value ||
                (item.thread.entry_type || "comment") ===
                  $("#review-kind").value) &&
              (!$("#review-state").value ||
                ($("#review-state").value === "unread"
                  ? item.unread
                  : $("#review-state").value === "open"
                    ? !item.thread.resolved
                    : item.thread.resolved)),
          )
        : items;
    $("#count").textContent =
      (view === "inbox" ? filtered.length : total) +
      " " +
      (view === "inbox" ? "hilos" : "artefactos");
    if (!filtered.length) {
      if (!user?.verified && view !== "public")
        empty(
          "Tu biblioteca empieza aquí.",
          "Entra con tu correo para encontrar tus artefactos, los que compartieron contigo y sus comentarios.",
          true,
        );
      else
        empty(
          view === "inbox"
            ? "La conversación está al día."
            : "No encontramos artefactos.",
          $("#search").value
            ? "Prueba otras palabras o ajusta los filtros."
            : view === "inbox"
              ? "Las revisiones aparecerán aquí, con su contexto."
              : "Publica tu primer documento para empezar.",
        );
      return;
    }
    if (view === "inbox") {
      filtered.forEach(renderThread);
      return;
    }
    root.className = layout;
    for (const name of ["grid", "list", "table", "graph"])
      $("#" + name + "-view").setAttribute(
        "aria-pressed",
        String(name === layout),
      );
    if (layout === "graph") {
      renderGraph();
      return;
    }
    if (layout === "table") renderTable();
    else filtered.forEach(renderCard);
    feedStatus();
  }
  function renderThread(item) {
    const n = item.thread,
      article = make("article", undefined, "thread"),
      origin = make("div"),
      link = make("a", item.title);
    link.href = item.context.url;
    origin.append(
      make("p", item.space, "eyebrow"),
      link,
      make(
        "p",
        (n.entry_type === "note" ? "Nota privada" : "Comentario") +
          " · " +
          (item.unread ? "Sin leer" : "Leído"),
        "meta",
      ),
    );
    const body = make("div");
    body.append(
      make(
        "p",
        n.author + " · " + (n.resolved ? "Resuelto" : "Pendiente"),
        "meta",
      ),
      make("p", n.text),
      make("blockquote", n.anchor.quote),
      make(
        "p",
        (n.anchor.section || n.anchor.page) + " / #" + n.anchor.reference,
        "meta",
      ),
    );
    if (item.context.anchor_status !== "exact")
      body.append(
        make(
          "p",
          "Revisar referencia: " + anchorLabels[item.context.anchor_status],
          "anchor-warning",
        ),
      );
    if (n.session) body.append(make("p", "Sesión: " + n.session, "meta"));
    for (const r of n.replies)
      body.append(make("p", r.author + ": " + r.text, "muted"));
    const ownNote = n.entry_type === "note",
      canReply = item.permissions.comment || ownNote;
    if (canReply) {
      const response = make("form", undefined, "reply"),
        input = make("input"),
        send = make("button", "Responder");
      input.required = true;
      input.maxLength = 4000;
      input.placeholder = ownNote
        ? "Añadir seguimiento…"
        : "Responder · @correo@empresa.com";
      input.setAttribute("aria-label", "Respuesta a " + n.author);
      response.append(input, send);
      response.addEventListener(
        "submit",
        safe(async (e) => {
          e.preventDefault();
          send.disabled = true;
          try {
            await writeReview(item, { kind: "reply", text: input.value });
            await load();
          } finally {
            send.disabled = false;
          }
        }),
      );
      body.append(response);
    }
    const actions = make("div", undefined, "thread-actions"),
      copyOne = make("button", "Copiar para IA"),
      read = make("button", "Marcar leído");
    if (item.permissions.edit || ownNote) {
      const resolve = make("button", n.resolved ? "Reabrir" : "Resolver");
      resolve.addEventListener(
        "click",
        safe(async () => {
          await writeReview(item, { kind: "resolve", resolved: !n.resolved });
          await load();
        }),
      );
      actions.append(resolve);
    }
    copyOne.addEventListener(
      "click",
      safe(async () =>
        copy(
          (
            await api(
              "/api/review/export?artifact=" +
                item.artifact +
                "&thread=" +
                encodeURIComponent(n.thread),
            )
          ).text,
        ),
      ),
    );
    read.addEventListener(
      "click",
      safe(async () => {
        await api("/api/artifacts/" + item.artifact + "/seen", {
          method: "POST",
          body: JSON.stringify({ thread: n.thread }),
        });
        await load();
      }),
    );
    actions.append(copyOne, read);
    article.append(origin, body, actions);
    $("#results").append(article);
  }
  function writeReview(item, data) {
    return api("/api/artifacts/" + item.artifact + "/review", {
      method: "POST",
      body: JSON.stringify({
        id: crypto.randomUUID(),
        thread: item.thread.thread,
        version: item.thread.version,
        ...data,
      }),
    });
  }
  async function load(append = false) {
    if (["brain", "insights", "work"].includes(view)) {
      listController?.abort();
      graphController?.abort();
      graphInstance?.destroy();
      previews.disconnect();
      covers.disconnect();
      for (const id of [
        "feed-end",
        "table-preferences",
        "context-tools",
        "browse-bar",
        "library-filters",
        "overview",
      ])
        $("#" + id).hidden = true;
      $(".tools").hidden = true;
      return workspace.render($("#results"), view);
    }
    workspace.destroy();
    $(".tools").hidden = false;
    $("#context-tools").hidden =
      !user?.verified ||
      ["admin", "connections", "notifications"].includes(view);
    const tableScroll = append ? $(".table-scroll")?.scrollTop || 0 : 0;
    if (["connections", "notifications", "admin"].includes(view)) {
      listController?.abort();
      return renderList();
    }
    if (append && (!nextCursor || loading)) return;
    if (!append) {
      listController?.abort();
      listController = new AbortController();
      requestNumber++;
      nextCursor = null;
    }
    const number = requestNumber;
    loading = true;
    feedStatus();
    $("#results").setAttribute("aria-busy", "true");
    try {
      if (view === "inbox") {
        items = user?.verified
          ? (await api("/api/inbox", { signal: listController.signal })).items
          : [];
        if (number !== requestNumber) return;
        total = items.length;
        $("#inbox-count").textContent =
          items.filter((i) => !i.thread.resolved).length || "";
        renderList();
        return;
      }
      const params = queryParams();
      params.set("limit", "12");
      if (append) params.set("cursor", nextCursor);
      const data = await api("/api/artifacts?" + params, {
        signal: listController.signal,
      });
      if (number !== requestNumber) return;
      const ids = new Set(items.map((a) => a.id)),
        added = append
          ? data.artifacts.filter((a) => !ids.has(a.id))
          : data.artifacts;
      items = append ? [...items, ...added] : added;
      nextCursor = data.next_cursor;
      total = data.total;
      $("#overview").hidden = view !== "mine" || !user?.verified;
      $("#legacy-note").hidden = true;
      if (view === "mine") {
        const summary = data.summary;
        $("#total-artifacts").textContent = summary.total;
        $("#total-pending").textContent = summary.open_comments;
        $("#inbox-count").textContent = summary.open_comments || "";
        $("#total-shared").textContent = summary.shared;
        if (!append)
          api("/api/creator/analytics/summary?days=30")
            .then((d) => {
              $("#total-visits").textContent = Number(d.total).toLocaleString(
                "es",
              );
            })
            .catch(() => {
              $("#total-visits").textContent = "—";
            });
      }
      const filter = $("#space-filter"),
        selected = filter.value;
      filter.replaceChildren();
      const all = make("option", "Todos los espacios");
      all.value = "";
      filter.append(all);
      data.spaces.forEach((space) => {
        const option = make("option", space);
        option.value = space;
        filter.append(option);
      });
      filter.value = [...filter.options].some((o) => o.value === selected)
        ? selected
        : "";
      for (const [id, values] of [
        ["collection-filter", data.collections],
        ["tag-filter", data.tags],
        ["category-filter", data.categories],
        ["agent-filter", data.agents],
      ]) {
        const select = $("#" + id),
          value = select.value;
        select.replaceChildren(new Option("Todas", ""));
        for (const name of values || []) select.append(new Option(name, name));
        select.value = value;
      }
      updateBrowse();
      updateCategories(data.categories || []);
      updateCompanies(data.spaces || []);
      if ((append && layout === "grid") || (append && layout === "list")) {
        added.forEach(renderCard);
        $("#count").textContent = total + " artefactos";
      } else {
        renderList();
        if (append && $(".table-scroll"))
          $(".table-scroll").scrollTop = tableScroll;
      }
    } catch (error) {
      if (error.name !== "AbortError") throw error;
    } finally {
      if (number === requestNumber) {
        loading = false;
        $("#results").setAttribute("aria-busy", "false");
        feedStatus();
      }
    }
  }
  $$("[data-view]").forEach((button) =>
    button.addEventListener(
      "click",
      safe(async () => {
        advancedFilters = "";
        selectedArtifacts.clear();
        renderBatch();
        view = button.dataset.view;
        if (innerWidth <= 850)
          button.scrollIntoView({
            block: "nearest",
            inline: "center",
            behavior: "instant",
          });
        document.body.dataset.view = view;
        history.replaceState(
          null,
          "",
          view === "mine"
            ? "/"
            : "/?view=" +
                view +
                (view === "work" &&
                new URLSearchParams(location.search).has("section")
                  ? "&section=" +
                    encodeURIComponent(
                      new URLSearchParams(location.search).get("section"),
                    )
                  : ""),
        );
        $("#library-title").textContent = {
          brain: "Grafo de conocimiento",
          insights: "Visitas",
          work: "Mi trabajo",
          mine: "Biblioteca",
          shared: "Compartidos con tu equipo.",
          inbox: "Conversaciones en contexto.",
          notifications: "Lo que necesita tu atención.",
          admin: "Tu biblioteca, bajo control.",
          archived: "Archivo de artefactos.",
          public: "Biblioteca pública.",
          connections: "La misma cuenta, cualquier agente.",
        }[view];
        $("#library-description").textContent =
          {
            brain: "Una memoria de ideas, fuentes y decisiones.",
            insights: "Entiende qué se lee cuando compartes tu trabajo.",
            work: "Revisa evidencia, retoma sesiones y decide el siguiente paso.",
          }[view] ||
          "Documentos, decisiones y conversaciones en un mismo lugar.";
        clearTimeout(searchTimer);
        $$("[data-view]").forEach(
          (b) => (
            b.classList.toggle("active", b === button),
            b.setAttribute("aria-current", b === button ? "page" : "false")
          ),
        );
        $("#copy-tools").hidden = view !== "inbox" || !user?.verified;
        $("#search").value = "";
        $("#search").placeholder =
          view === "inbox"
            ? "Buscar en comentarios y contexto…"
            : "Buscar en títulos y contenido…";
        $("#search").closest("label").hidden = [
          "connections",
          "notifications",
          "admin",
        ].includes(view);
        $("#review-filters").hidden = view !== "inbox";
        $("#library-filters").hidden = true;
        $("#toggle-filters").hidden = [
          "inbox",
          "connections",
          "notifications",
          "admin",
        ].includes(view);
        $("#browse-bar").hidden = $("#toggle-filters").hidden;
        $("#toggle-filters").setAttribute("aria-expanded", "false");
        $("#overview").hidden = view !== "mine";
        $("#legacy-note").hidden = true;
        $("#space-filter").value = "";
        $("#access-filter").value = "";
        $("#collection-filter").value = "";
        $("#tag-filter").value = "";
        $("#category-filter").value = "";
        $("#agent-filter").value = "";
        $("#pending-filter").value = "";
        closePeek();
        await load();
      }),
    ),
  );
  $("#search").addEventListener("input", () => {
    clearTimeout(searchTimer);
    if (view === "inbox") {
      renderList();
      return;
    }
    if ($("#search").value.trim() && $("#sort-order").value === "recent") {
      $("#sort-order").value = "relevance";
      $("#sort-direction").value = "";
    } else if (
      !$("#search").value.trim() &&
      $("#sort-order").value === "relevance"
    )
      $("#sort-order").value = "recent";
    searchTimer = setTimeout(
      () => load().catch((error) => toast(error.message)),
      250,
    );
  });
  for (const id of [
    "space-filter",
    "access-filter",
    "sort-order",
    "collection-filter",
    "tag-filter",
    "category-filter",
    "sort-direction",
    "agent-filter",
    "pending-filter",
  ])
    $("#" + id).addEventListener(
      "change",
      safe(() => load()),
    );
  for (const name of ["grid", "list", "table", "graph"])
    $("#" + name + "-view").addEventListener("click", () => {
      if (name === "graph") {
        $('[data-view="brain"]').click();
        return;
      }
      layout = name;
      try {
        localStorage.setItem("bottifact-library-layout", name);
      } catch {}
      renderList();
    });
  for (const id of ["review-kind", "review-state"])
    $("#" + id).addEventListener("change", renderList);
  $$("[data-copy]").forEach((b) =>
    b.addEventListener(
      "click",
      safe(async () =>
        copy((await api("/api/review/export?scope=" + b.dataset.copy)).text),
      ),
    ),
  );

  $("#view-controls").append($(".view-switch"));
  $("#search-icon").append(K.icon("search"));
  const decorate = window.BottifactUI?.decorate;
  document
    .querySelectorAll("button[data-close],#close-peek")
    .forEach((b) => decorate?.(b, "close", true));
  for (const [selector, icon, only] of [
    ["#theme", "appearance", true],
    ["#publish", "plus", false],
    ["#toggle-filters", "filter", false],
    ["#logout", "logout", false],
  ])
    decorate?.($(selector), icon, only);
  for (const [view, icon] of Object.entries({
    brain: "graph",
    insights: "chart",
    work: "note",
    mine: "folder",
    shared: "share",
    inbox: "comment",
    public: "globe",
    notifications: "bell",
    archived: "archive",
    admin: "settings",
    connections: "agent",
  }))
    decorate?.($('[data-view="' + view + '"]'), icon);
  for (const name of ["grid", "list", "table", "graph"])
    $("#" + name + "-view").replaceChildren(K.icon(name));
  $("#toggle-filters").addEventListener("click", () => {
    const hidden = !$("#library-filters").hidden;
    $("#library-filters").hidden = hidden;
    $("#toggle-filters").setAttribute("aria-expanded", String(!hidden));
  });
  function updateCompanies(spaces) {
    let section = $("#company-nav");
    if (!section) {
      section = make("section", undefined, "category-nav company-nav");
      section.id = "company-nav";
      $(".tabs").append(section);
    }
    section.replaceChildren(make("h2", "Tus espacios"));
    for (const space of spaces) {
      const b = make("button", space);
      b.classList.toggle("chosen", $("#space-filter").value === space);
      const initial = make("span", space.slice(0, 2), "company-initial");
      b.prepend(initial);
      b.onclick = () => {
        $("#space-filter").value = space;
        load().catch((e) => toast(e.message));
      };
      section.append(b);
    }
  }
  function updateCategories(categories) {
    let section = $("#category-nav");
    if (!section) {
      section = make("section", undefined, "category-nav");
      section.id = "category-nav";
      $(".tabs").append(section);
    }
    section.replaceChildren(make("h2", "Temas de tu biblioteca"));
    for (const category of categories) {
      const b = make("button", category);
      b.classList.toggle("chosen", $("#category-filter").value === category);
      b.addEventListener("click", () => {
        $("#category-filter").value =
          $("#category-filter").value === category ? "" : category;
        load().catch((e) => toast(e.message));
      });
      section.append(b);
    }
  }
  function restoreBrowse() {
    try {
      const saved = JSON.parse(
        sessionStorage.getItem("bottifact-browse:" + user.id) || "null",
      );
      if (!saved || saved.view !== "mine") return;
      $("#search").value = saved.q || "";
      for (const [key, id] of [
        ["space", "space-filter"],
        ["collection", "collection-filter"],
        ["tag", "tag-filter"],
        ["access", "access-filter"],
        ["sort", "sort-order"],
        ["category", "category-filter"],
        ["direction", "sort-direction"],
        ["agent", "agent-filter"],
        ["review", "pending-filter"],
      ]) {
        const select = $("#" + id);
        if (
          saved[key] &&
          ![...select.options].some((o) => o.value === saved[key])
        )
          select.append(new Option(saved[key], saved[key]));
        select.value = saved[key] || "";
      }
    } catch {}
  }
  function updateBrowse() {
    for (const select of $("#library-filters").querySelectorAll("select"))
      select.dispatchEvent(new Event("bottifact-sync"));
    const root = $("#active-filters");
    root.replaceChildren();
    try {
      sessionStorage.setItem(
        "bottifact-browse:" + user.id,
        JSON.stringify(Object.fromEntries(queryParams())),
      );
    } catch {}
    for (const id of [
      "category-filter",
      "space-filter",
      "collection-filter",
      "tag-filter",
      "access-filter",
      "agent-filter",
      "pending-filter",
    ]) {
      const select = $("#" + id);
      if (!select.value) continue;
      const b = make(
        "button",
        select.options[select.selectedIndex]?.text + " ×",
        "filter-chip",
      );
      b.setAttribute("aria-label", "Quitar filtro " + select.value);
      b.addEventListener("click", () => {
        select.value = "";
        select.dispatchEvent(new Event("change"));
      });
      root.append(b);
    }
    if (!root.children.length)
      root.append(make("span", "Explorar artefactos", "muted"));
  }
  document.addEventListener("keydown", (e) => {
    if (
      e.key === "Escape" &&
      !$("#artifact-peek").hidden &&
      !document.querySelector("dialog[open]")
    )
      closePeek();
  });

  window.BottifactLibraryControls.init($("#library-filters"));
  $("#clear-library-filters").addEventListener(
    "click",
    safe(async () => {
      for (const id of [
        "space-filter",
        "category-filter",
        "collection-filter",
        "tag-filter",
        "access-filter",
        "agent-filter",
        "pending-filter",
      ])
        $("#" + id).value = "";
      $("#search").value = "";
      $("#sort-order").value = "recent";
      $("#sort-direction").value = "";
      await load();
    }),
  );
  for (let i = 1; i < 6; i++) {
    const name = columns[i][0],
      label = make("label"),
      check = make("input");
    check.type = "checkbox";
    check.checked = !hiddenColumns.has(name);
    label.append(check, document.createTextNode(name));
    check.addEventListener("change", () => {
      check.checked ? hiddenColumns.delete(name) : hiddenColumns.add(name);
      saveTablePreferences();
      applyTablePreferences();
    });
    $("#table-columns").append(label);
  }
  function saveTablePreferences() {
    try {
      localStorage.setItem(
        "bottifact-table-settings",
        JSON.stringify({ hidden: [...hiddenColumns], density: tableDensity }),
      );
    } catch {}
  }
  $("#table-density").value = tableDensity;
  $("#table-density").addEventListener("change", () => {
    tableDensity = $("#table-density").value;
    saveTablePreferences();
    applyTablePreferences();
  });
  $("#logout").addEventListener(
    "click",
    safe(async () => {
      await api("/api/logout", { method: "POST", body: "{}" });
      location.reload();
    }),
  );
  $$("[data-close]").forEach((b) =>
    b.addEventListener("click", () => b.closest("dialog").close()),
  );
  $("#select-copy").addEventListener("click", () => {
    $("#copy-text").focus();
    $("#copy-text").select();
  });
  $("#theme").addEventListener("click", () => {
    const dark = !document.documentElement.hasAttribute("data-dark");
    document.documentElement.toggleAttribute("data-dark", dark);
    try {
      localStorage.setItem("bottifact-portal-dark", String(dark));
    } catch {}
  });
  try {
    document.documentElement.toggleAttribute(
      "data-dark",
      localStorage.getItem("bottifact-portal-dark") === "true" ||
        (!localStorage.getItem("bottifact-portal-dark") &&
          matchMedia("(prefers-color-scheme:dark)").matches),
    );
  } catch {}
  function upload(revision = false) {
    uploadVersion = revision;
    $("#upload-heading").textContent = revision
      ? "Subir una revisión"
      : "Publicar artefacto";
    const form = $("#upload-form");
    form.reset();
    form.elements.title.value = revision ? current.title : "";
    form.elements.space.value = revision ? current.space : "Personal";
    form.querySelector(".form-error").textContent = "";
    $("#upload-dialog").showModal();
  }
  function rename(a) {
    editing = a;
    const form = $("#rename-form");
    form.elements.title.value = a.title;
    form.elements.space.value = a.space;
    form.querySelector(".form-error").textContent = "";
    $("#rename-dialog").showModal();
    form.elements.title.focus();
    form.elements.title.select();
  }
  $("#rename-document").addEventListener("click", () => rename(current));
  $("#rename-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget,
      button =
        form.querySelector("[type=submit]") || form.querySelector(".primary");
    button.disabled = true;
    try {
      const result = await api("/api/artifacts/" + editing.id, {
        method: "PATCH",
        body: JSON.stringify({
          title: form.elements.title.value,
          space: form.elements.space.value,
        }),
      });
      if (current?.id === editing.id) {
        Object.assign(current, result);
        $("#doc-title").textContent = current.title;
        $("#doc-meta").textContent =
          current.space + " · " + labels[current.visibility];
        document.title = current.title + " · Margen";
      } else await load();
      form.closest("dialog").close();
      toast("Nombre actualizado. El enlace sigue siendo el mismo.");
    } catch (error) {
      form.querySelector(".form-error").textContent = error.message;
    } finally {
      button.disabled = false;
    }
  });
  $("#publish").addEventListener("click", () => upload());
  $("#new-version").addEventListener("click", () => upload(true));
  $("#upload-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.currentTarget,
      button = form.querySelector("[type=submit]");
    button.disabled = true;
    form.querySelector(".form-error").textContent = "";
    try {
      const file = form.elements.file.files[0];
      if (!file || file.size > 20 * 1024 * 1024)
        throw Error("Selecciona un HTML de hasta 20 MB.");
      const original = form.elements.original?.files[0];
      let attachments = [];
      if (original) {
        if (original.size > 12 * 1024 * 1024)
          throw Error("El original debe ocupar menos de 12 MB.");
        const data = await new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve(String(reader.result).split(",")[1]);
          reader.onerror = reject;
          reader.readAsDataURL(original);
        });
        attachments = [
          {
            name: "original." + original.name.split(".").pop().toLowerCase(),
            data,
          },
        ];
      }
      const payload = {
          attachments,
          title: form.elements.title.value,
          space: form.elements.space.value,
          html: await file.text(),
          mode: uploadVersion ? "draft" : "published",
          source: {
            agent: form.elements.agent.value,
            session: form.elements.session.value,
            device: form.elements.device.value,
          },
        },
        result = await api(
          uploadVersion
            ? "/api/artifacts/" + current.id + "/versions"
            : "/api/artifacts",
          { method: "POST", body: JSON.stringify(payload) },
        );
      location.assign(
        "/a/" +
          result.id +
          (result.state === "draft" ? "?version=" + result.version : ""),
      );
    } catch (error) {
      form.querySelector(".form-error").textContent = error.message;
    } finally {
      button.disabled = false;
    }
  });
  function shareSummary() {
    const form = $("#share-form"),
      mode = form.elements.visibility.value;
    $("#access-summary").textContent = {
      private:
        "Tu cuenta y la administración del portal pueden abrirlo. Guardar este modo retira los accesos de invitados.",
      invited:
        "Tu cuenta, estos correos y la administración del portal pueden abrirlo. Reenviar el enlace no concede acceso.",
      unlisted:
        "Cualquiera con el enlace puede abrirlo. No aparece en la biblioteca pública.",
      public:
        "Cualquiera puede abrirlo y encontrarlo en la biblioteca pública.",
    }[mode];
    const allowed =
      ["public", "unlisted"].includes(mode) &&
      form.elements.comments.value === "readers";
    form.elements.guests.disabled = !allowed;
    if (!allowed) form.elements.guests.checked = false;
  }
  function showGrants() {
    const root = $("#grants");
    root.replaceChildren();
    grants.forEach((g, index) => {
      const row = make("div", undefined, "grant"),
        remove = make("button", "Quitar"),
        select = make("select");
      remove.type = "button";
      remove.setAttribute("aria-label", "Quitar acceso de " + g.email);
      remove.addEventListener("click", () => {
        grants.splice(index, 1);
        showGrants();
      });
      for (const [value, title] of [
        ["viewer", "Ver"],
        ["commenter", "Comentar"],
        ["editor", "Editar"],
      ]) {
        const option = make("option", title);
        option.value = value;
        select.append(option);
      }
      select.value = g.role;
      select.setAttribute("aria-label", "Permiso de " + g.email);
      select.addEventListener("change", () => (g.role = select.value));
      row.append(make("span", g.email), select, remove);
      root.append(row);
    });
  }
  $("#share-form").elements.visibility.addEventListener("change", shareSummary);
  $("#share-form").elements.comments.addEventListener("change", shareSummary);
  $("#add-invite").addEventListener("click", () => {
    const input = $("#invite-email");
    if (!input.value || !input.reportValidity()) return;
    const email = input.value.trim().toLowerCase();
    grants = grants.filter((g) => g.email !== email);
    grants.push({ email, role: $("#invite-role").value });
    input.value = "";
    if ($("#share-form").elements.visibility.value === "private")
      $("#share-form").elements.visibility.value = "invited";
    shareSummary();
    showGrants();
  });
  async function openShare(id) {
    sharing = await api("/api/artifacts/" + id);
    const form = $("#share-form");
    form.elements.visibility.value = sharing.visibility;
    form.elements.comments.value = sharing.comments;
    form.elements.guests.checked = !!sharing.guests;
    form.querySelector(".form-error").textContent = "";
    grants = sharing.grants.map((g) => ({ ...g }));
    showGrants();
    shareSummary();
    $("#share-dialog").showModal();
  }
  $("#share").addEventListener(
    "click",
    safe(() => openShare(current.id)),
  );
  $("#share-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const f = e.currentTarget,
      b = f.querySelector("button.primary");
    b.disabled = true;
    try {
      await api("/api/artifacts/" + sharing.id + "/access", {
        method: "PUT",
        body: JSON.stringify({
          visibility: f.elements.visibility.value,
          comments: f.elements.comments.value,
          guests: f.elements.guests.checked,
          grants,
        }),
      });
      if (current?.id === sharing.id) {
        current = await api("/api/artifacts/" + current.id);
        $("#doc-meta").textContent =
          current.space + " · " + labels[current.visibility];
        await refreshReview();
      } else await load();
      f.closest("dialog").close();
      toast("Permisos actualizados.");
    } catch (error) {
      f.querySelector(".form-error").textContent = error.message;
    } finally {
      b.disabled = false;
    }
  });
  $("#copy-link").textContent = "Copiar enlace actual";
  $("#copy-link").addEventListener("click", () => {
    copy(location.origin + "/a/" + sharing.id);
    $("#access-summary").textContent =
      "Enlace copiado con los permisos guardados. Los cambios de este formulario requieren Guardar permisos.";
  });
  const prepareContext = make("button", "Preparar contexto");
  prepareContext.addEventListener(
    "click",
    safe(() => readerWorkspace.bundle(null)),
  );
  $("#copy-tools").append(prepareContext);
  $("#copy-document").addEventListener(
    "click",
    safe(async () =>
      copy((await api("/api/review/export?artifact=" + current.id)).text),
    ),
  );
  function identify() {
    if (user?.verified) return;
    if (current.guests && current.comments === "readers") {
      $("#guest-login").href = loginURL();
      $("#guest-google").hidden = !authOptions.google;
      $("#guest-google").href =
        "/auth/google?next=" +
        encodeURIComponent(location.pathname + location.search);
      if (!$("#guest-dialog").open) $("#guest-dialog").showModal();
    } else location.assign(loginURL());
  }

  $("#guest-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const f = e.currentTarget;
    try {
      await api("/api/guest", {
        method: "POST",
        body: JSON.stringify({
          artifact: current.id,
          name: f.elements.name.value,
        }),
      });
      await identity();
      current = await api("/api/artifacts/" + current.id);
      f.closest("dialog").close();
      await refreshReview();
      toast("Listo. Elige un punto del artefacto para comentar.");
    } catch (error) {
      f.querySelector(".form-error").textContent = error.message;
    }
  });
  async function refreshReview() {
    if (!current) return;
    try {
      const data = await api("/api/artifacts/" + current.id + "/review");
      data.reader = readerWorkspace.settings();
      $("#artifact-frame").contentWindow.postMessage(
        { bottifact: 1, op: "snapshot", data },
        "*",
      );
      $("#review-status").textContent = data.permissions.review
        ? data.permissions.comment
          ? "Revisión compartida"
          : "Puedes leer la revisión."
        : "La conversación de revisión es privada.";
      return data;
    } catch (error) {
      if (error.status === 404 || error.status === 401) {
        $("#artifact-frame").src = "about:blank";
        clearInterval(poll);
      }
      $("#review-status").textContent =
        "No se pudo sincronizar: " + error.message;
      throw error;
    }
  }
  let requestedEntryType = null;
  const contextWorkbench = window.BottifactContextWorkbench.create({
    api,
    user: () => user,
    current: () => current,
    peek,
    load,
    params: () => {
      const p = queryParams();
      p.set("_columns", JSON.stringify([...hiddenColumns]));
      p.set("_density", tableDensity);
      p.set("_layout", layout);
      return p;
    },
    bundle: (aid) => readerWorkspace.bundle(aid),
    applyParams: (p) => {
      if (p._columns) {
        try {
          const values = JSON.parse(p._columns);
          if (Array.isArray(values)) {
            hiddenColumns.clear();
            values
              .filter((v) => typeof v === "string")
              .forEach((v) => hiddenColumns.add(v));
          }
        } catch {}
      }
      if (["compact", "comfortable"].includes(p._density))
        tableDensity = p._density;
      if (["grid", "list", "table", "graph"].includes(p._layout))
        layout = p._layout;
      if (p.view && ["mine", "shared", "public", "archived"].includes(p.view)) {
        view = p.view;
        document.body.dataset.view = view;
        $$("[data-view]").forEach((b) => {
          b.classList.toggle("active", b.dataset.view === view);
          b.setAttribute(
            "aria-current",
            b.dataset.view === view ? "page" : "false",
          );
        });
      }
      advancedFilters = p.filters || "";
      for (const [key, id] of Object.entries({
        q: "search",
        space: "space-filter",
        access: "access-filter",
        sort: "sort-order",
        collection: "collection-filter",
        tag: "tag-filter",
        category: "category-filter",
        direction: "sort-direction",
        agent: "agent-filter",
        review: "pending-filter",
      }))
        if (p[key] !== undefined) $("#" + id).value = p[key];
      load();
    },
  });
  const creatorWorkspace = window.MargenCreator.create({
    api,
    copy,
    peek,
    bundle: (aid) => readerWorkspace.bundle(aid),
  });
  const workspace = window.MargenWorkspace.create({
    api,
    peek,
    copy,
    creator: creatorWorkspace,
    related: contextWorkbench.related,
    user: () => user,
  });
  const workbenchTools = make("div", undefined, "context-actions");
  workbenchTools.id = "context-tools";
  for (const [label, fn, icon] of [
    ["Condiciones", contextWorkbench.filters, "filter"],
    ["Mesas y vistas", contextWorkbench.views, "table"],
    ["Organizar conocimiento", contextWorkbench.entities, "graph"],
  ]) {
    const b = make("button", label);
    b.type = "button";
    b.addEventListener("click", safe(fn));
    window.BottifactUI?.decorate(b, icon);
    workbenchTools.append(b);
  }
  $("#results").before(workbenchTools);
  const readerWorkspace = window.BottifactReaderWorkspace.create({
    api,
    current: () => current,
    user: () => user,
    copy,
    related: contextWorkbench.related,
    search: contextWorkbench.search,
    share: openShare,
    manage: () => $("#owner-panel").showPopover(),
    comment: (kind) => {
      requestedEntryType = kind;
      $("#comment-document").click();
    },
    refresh: refreshReview,
  });
  addEventListener("message", async (event) => {
    if (
      !current ||
      event.source !== $("#artifact-frame").contentWindow ||
      event.origin !== "null" ||
      event.data?.bottifact !== 1
    )
      return;
    const { id, op, data } = event.data;
    if (
      typeof id !== "string" ||
      id.length > 80 ||
      ![
        "ready",
        "commit",
        "identify",
        "context",
        "navigate",
        "export",
        "action",
        "preferences",
        "controls-ready",
      ].includes(op)
    )
      return;
    const source = event.source;
    try {
      let result;
      if (["action", "preferences", "controls-ready"].includes(op)) {
        result = await readerWorkspace.handle(op, data);
      } else if (op === "export") {
        const exported = await api(
          "/api/review/export?artifact=" +
            current.id +
            "&scope=" +
            (data?.scope === "open" ? "open" : "all"),
        );
        await copy(exported.text);
        result = { ok: true };
      } else if (op === "navigate") {
        if (
          typeof data?.path !== "string" ||
          !(
            /^\/a\/[a-f0-9]{32}(?:#[^\s]*)?$/.test(data.path) ||
            (new RegExp(
              "^/api/artifacts/" +
                current.id +
                "/attachments/[a-f0-9]{32}/[^?#\\\\]+$",
            ).test(data.path) &&
              !decodeURIComponent(data.path).split("/").includes(".."))
          )
        )
          throw Error("Destino no permitido.");
        location.assign(data.path);
        result = { ok: true };
      } else if (op === "context") {
        if (!contextRequested) throw Error("Solicitud de contexto vencida.");
        contextRequested = false;
        commentAnchor = data;
        $("#document-comment-context").textContent =
          data.quote || current.title;
        $("#document-comment-text").value = "";
        $("#document-comment-form .form-error").textContent = "";
        $("#document-comment-kind").value =
          requestedEntryType ||
          (current.permissions.comment ? "comment" : "note");
        requestedEntryType = null;
        $("#document-comment-kind").querySelector("[value=comment]").disabled =
          !current.permissions.comment;
        $("#document-comment-dialog").showModal();
        $("#document-comment-text").focus();
        result = { ok: true };
      } else if (op === "identify") {
        identify();
        result = { ok: true };
      } else if (op === "ready") {
        $("#comment-document").hidden =
          !!data?.pins || !current.permissions.review || false;
        $("#reader-dock").classList.toggle("with-pins", !!data?.pins);
        result = await refreshReview();
        const thread = new URLSearchParams(location.search).get("thread");
        if (thread) {
          source.postMessage({ bottifact: 1, op: "focus-thread", thread }, "*");
          if (user?.verified)
            api("/api/artifacts/" + current.id + "/seen", {
              method: "POST",
              body: JSON.stringify({ thread }),
            }).catch(() => {});
        }
      } else {
        if (!user) {
          identify();
          throw Error(
            "Indica tu nombre para guardar. El comentario sigue en el editor.",
          );
        }
        const allowed = {};
        for (const k of [
          "id",
          "kind",
          "thread",
          "text",
          "resolved",
          "assignee",
          "anchor",
          "entry_type",
          "session",
        ])
          if (Object.hasOwn(data || {}, k)) allowed[k] = data[k];
        result = await api("/api/artifacts/" + current.id + "/review", {
          method: "POST",
          body: JSON.stringify({ ...allowed, version: $("#version").value }),
        });
        $("#review-status").textContent = "Comentario guardado.";
      }
      source.postMessage({ bottifact: 1, id, data: result }, "*");
    } catch (error) {
      source.postMessage({ bottifact: 1, id, error: error.message }, "*");
      toast(error.message);
    }
  });
  $("#comment-document").addEventListener("click", () => {
    if (!user) {
      identify();
      return;
    }
    if (!current.permissions.comment && !user?.verified) {
      toast("Tu acceso es de lectura.");
      return;
    }
    contextRequested = true;
    $("#artifact-frame").contentWindow.postMessage(
      { bottifact: 1, op: "capture-context" },
      "*",
    );
  });
  $("#document-comment-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget,
      button = form.querySelector("[type=submit]");
    button.disabled = true;
    try {
      await api("/api/artifacts/" + current.id + "/review", {
        method: "POST",
        body: JSON.stringify({
          id: crypto.randomUUID(),
          kind: "create",
          version: $("#version").value,
          text: $("#document-comment-text").value,
          anchor: commentAnchor,
          entry_type: $("#document-comment-kind").value,
          session: $("#document-comment-session").value,
        }),
      });
      form.closest("dialog").close();
      await refreshReview();
      toast("Comentario guardado.");
    } catch (error) {
      form.querySelector(".form-error").textContent = error.message;
    } finally {
      button.disabled = false;
    }
  });
  async function reader(aid) {
    document.body.classList.add("reading");
    $("#library").hidden = true;
    $("#reader").hidden = false;
    try {
      current = await api("/api/artifacts/" + aid);
    } catch (error) {
      $("#reader").replaceChildren();
      const box = make("div", undefined, "empty reader-gate");
      box.append(
        make("h2", "Este artefacto necesita acceso."),
        make(
          "p",
          user?.verified
            ? "Entra con el correo al que compartieron el documento o pide acceso al creador."
            : "Entra para abrir el documento.",
        ),
      );
      if (user?.verified) {
        const change = make("button", "Entrar con otra cuenta", "button");
        change.addEventListener(
          "click",
          safe(async () => {
            await api("/api/logout", { method: "POST", body: "{}" });
            location.assign(loginURL());
          }),
        );
        box.append(change);
      } else {
        if (authOptions.google) {
          const google = make("a", "Continuar con Google", "button");
          google.href =
            "/auth/google?next=" +
            encodeURIComponent(location.pathname + location.search);
          box.append(google);
        }
        const email = make("a", "Entrar con correo", "button primary");
        email.href = loginURL();
        box.append(email);
      }
      $("#reader").append(box);
      return;
    }
    const owner = user?.id === current.owner;
    $("#owner-tools").hidden = !owner;
    $("#owner-panel").hidden = !owner;
    $("#doc-title").textContent = current.title;
    document.title = current.title + " · Margen";
    $("#doc-meta").textContent =
      current.space + " · " + labels[current.visibility];
    const select = $("#version");
    select.replaceChildren();
    current.versions.forEach((v, i) => {
      const option = make(
        "option",
        (v.state === "draft"
          ? "Borrador · "
          : v.id === current.current_version
            ? "Publicada · "
            : "Anterior · ") + new Date(v.created * 1000).toLocaleString("es"),
      );
      option.value = v.id;
      select.append(option);
    });
    const requested = new URLSearchParams(location.search).get("version");
    select.value = current.versions.some((v) => v.id === requested)
      ? requested
      : current.current_version;
    const mount = () => {
      $("#reader-dock").hidden = false;
      versionControls();
      contextRequested = false;
      $("#artifact-frame").src =
        "/api/artifacts/" +
        current.id +
        "/render?version=" +
        select.value +
        location.hash;
    };
    select.addEventListener("change", mount);
    $("#artifact-frame").addEventListener(
      "load",
      () => {
        window.MargenAnalytics?.visit(api, current, user, select.value).catch(
          () => {},
        );
      },
      { once: true },
    );
    mount();
    poll = setInterval(() => {
      if (!document.hidden) refreshReview().catch(() => {});
    }, 12000);
  }
  async function renderConnections() {
    const root = $("#results");
    root.replaceChildren();
    $("#count").textContent = "";
    if (!user?.verified) {
      empty(
        "Conecta tu cuenta.",
        "Entra con tu correo para autorizar a Claude, Codex o Hermes.",
        true,
      );
      return;
    }
    const section = make("section", undefined, "connection");
    section.append(
      make("h2", "La misma cuenta, cualquier agente."),
      make(
        "p",
        "Crea una conexión personal y guárdala en el equipo del agente. Puede publicar documentos y consultar tus revisiones. Cada publicación es privada salvo que indiques --visibilidad public o unlisted. Revoca la conexión cuando quieras.",
      ),
    );
    const list = make("ol");
    [
      "Instala o actualiza el skill con el comando de abajo. Funciona con Claude Code, Codex y Hermes.",
      "Crea una conexión y guarda el token fuera del documento y del repositorio.",
      "Usa margen connect y margen publish para enviar el HTML.",
    ].forEach((t) => list.append(make("li", t)));
    section.append(list);
    const install = make(
      "pre",
      "curl -fsSL " + location.origin + "/install.sh | bash",
    );
    section.append(
      install,
      make(
        "p",
        "El mismo comando actualiza la biblioteca, conserva un respaldo y no cambia tu token. Generar archivos localmente no requiere una cuenta.",
        "muted",
      ),
    );
    const label = make("input");
    label.placeholder = "Nombre: Hermes MacBook";
    label.maxLength = 80;
    label.setAttribute("aria-label", "Nombre de la conexión");
    const create = make("button", "Crear conexión", "primary"),
      output = make("pre");
    create.addEventListener(
      "click",
      safe(async () => {
        const result = await api("/api/tokens", {
          method: "POST",
          body: JSON.stringify({ label: label.value || "Agente" }),
        });
        output.textContent =
          "Token personal (se muestra una sola vez):\n" +
          result.token +
          "\n\nmargen connect --servidor " +
          location.origin +
          "\nPega el token cuando el comando lo pida.";
        create.disabled = true;
      }),
    );
    section.append(label, create, output);
    root.append(section);
    const tokens = (await api("/api/tokens")).tokens;
    for (const token of tokens) {
      const row = make("div", undefined, "token-row"),
        remove = make("button", "Revocar");
      remove.addEventListener(
        "click",
        safe(async () => {
          await api("/api/tokens/" + token.hash, {
            method: "DELETE",
            body: "{}",
          });
          await renderConnections();
        }),
      );
      row.append(
        make(
          "span",
          token.label +
            " · " +
            new Date(token.created * 1000).toLocaleDateString("es"),
        ),
        remove,
      );
      section.append(row);
    }
  }
  function organization(a) {
    organizing = a;
    const f = $("#organization-form");
    f.elements.category.value = a.category_manual ? a.category : "";
    f.elements.automatic.checked = a.automatic !== false;
    const evidence = $("#classification-evidence");
    evidence.replaceChildren();
    for (const rule of a.classification || [])
      evidence.append(
        make("p", rule.tag + " ← " + rule.evidence.join(", "), "meta"),
      );
    f.elements.tags.value = (a.tags || []).join(", ");
    f.elements.collections.value = (a.collections || []).join(", ");
    f.elements.archived.checked = !!a.archived;
    f.querySelector(".form-error").textContent = "";
    $("#organization-title").textContent = a.title;
    $("#organization-dialog").showModal();
  }
  $("#organize-document").addEventListener("click", () =>
    organization(current),
  );
  $("#organization-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const f = event.currentTarget,
      b = f.querySelector(".primary");
    b.disabled = true;
    try {
      const split = (value) =>
        value
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean);
      const result = await api(
        "/api/artifacts/" + organizing.id + "/organization",
        {
          method: "PATCH",
          body: JSON.stringify({
            category: f.elements.category.value,
            automatic: f.elements.automatic.checked,
            tags: split(f.elements.tags.value),
            collections: split(f.elements.collections.value),
            archived: f.elements.archived.checked,
          }),
        },
      );
      if (current?.id === organizing.id)
        Object.assign(current, await api("/api/artifacts/" + organizing.id));
      else {
        await load();
        if (!$("#artifact-peek").hidden) await peek(organizing);
      }
      f.closest("dialog").close();
      toast("Organización guardada. El enlace se conserva.");
    } catch (error) {
      f.querySelector(".form-error").textContent = error.message;
    } finally {
      b.disabled = false;
    }
  });
  function versionControls() {
    const v = current.versions.find((v) => v.id === $("#version").value);
    let source = {};
    try {
      source = JSON.parse(v?.source || "{}");
    } catch {}
    $("#version-provenance").textContent =
      [
        source.agent,
        source.device,
        source.session ? "Sesión: " + source.session : "",
      ]
        .filter(Boolean)
        .join(" · ") || "Origen de esta versión sin registrar";
    $("#version-state").textContent =
      v?.state === "draft"
        ? "Borrador privado. Los lectores siguen viendo la versión publicada."
        : v?.id === current.current_version
          ? "Versión que abre el enlace compartido."
          : "Versión anterior. El enlace compartido no cambia al consultarla.";
    $("#release-version").hidden = v?.state !== "draft";
    $("#compare-version").disabled = current.versions.length < 2;
  }
  $("#compare-version").addEventListener(
    "click",
    safe(async () => {
      for (const name of ["from", "to"]) {
        const select = $("#compare-" + name);
        select.replaceChildren();
        current.versions.forEach((v) =>
          select.append(
            new Option(
              (v.state === "draft"
                ? "Borrador · "
                : v.id === current.current_version
                  ? "Publicada · "
                  : "Anterior · ") +
                new Date(v.created * 1000).toLocaleString("es"),
              v.id,
            ),
          ),
        );
      }
      const selected = $("#version").value,
        other = current.versions.find((v) => v.id !== current.current_version),
        draft = current.versions.find((v) => v.state === "draft");
      $("#compare-from").value =
        selected !== current.current_version || draft
          ? current.current_version
          : other.id;
      $("#compare-to").value =
        selected !== current.current_version
          ? selected
          : draft
            ? draft.id
            : current.current_version;
      $("#compare-dialog").showModal();
      await runCompare();
    }),
  );
  async function runCompare() {
    const button = $("#run-compare");
    button.disabled = true;
    $("#compare-status").textContent = "Comparando texto y referencias…";
    try {
      const result = await api(
          "/api/artifacts/" +
            current.id +
            "/compare?from=" +
            $("#compare-from").value +
            "&to=" +
            $("#compare-to").value,
        ),
        root = $("#comparison");
      root.replaceChildren();
      $("#compare-status").textContent =
        result.scope +
        (result.truncated
          ? " Se muestra una comparación parcial por tamaño."
          : "");
      if (!result.changes.length)
        root.append(
          make(
            "p",
            result.html_changed
              ? "El HTML cambió, pero no el texto comparado. Revisa la apariencia en cada versión."
              : "Estas versiones tienen el mismo contenido.",
          ),
        );
      for (const change of result.changes) {
        const pair = make("section", undefined, "diff-pair");
        for (const key of ["before", "after"]) {
          const block = make("div", undefined, "diff-" + key);
          block.append(make("h3", key === "before" ? "Antes" : "Después"));
          for (const line of change[key]) block.append(make("p", line));
          pair.append(block);
        }
        if (change.omitted)
          pair.append(
            make("p", change.omitted + " bloques adicionales omitidos."),
          );
        root.append(pair);
      }
      const anchors = make("section", undefined, "anchor-report");
      anchors.append(make("h3", "Contexto de comentarios y notas"));
      for (const a of result.anchors)
        anchors.append(
          make(
            "p",
            anchorLabels[a.status] + " · " + a.text,
            a.status === "exact" ? "muted" : "anchor-warning",
          ),
        );
      if (!result.anchors.length)
        anchors.append(make("p", "Todavía no hay referencias que comprobar."));
      root.append(anchors);
    } catch (error) {
      $("#compare-status").textContent = error.message;
    } finally {
      button.disabled = false;
    }
  }
  $("#run-compare").addEventListener("click", runCompare);
  $("#release-version").addEventListener("click", () => {
    $("#release-form .form-error").textContent = "";
    $("#release-dialog").showModal();
  });
  $("#release-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const b = event.currentTarget.querySelector(".primary");
    b.disabled = true;
    try {
      await api("/api/artifacts/" + current.id + "/release", {
        method: "POST",
        body: JSON.stringify({
          version: $("#version").value,
          expected_current: current.current_version,
        }),
      });
      location.assign("/a/" + current.id);
    } catch (error) {
      $("#release-form .form-error").textContent = error.message;
    } finally {
      b.disabled = false;
    }
  });
  async function noticeBadge() {
    if (!user?.verified) return;
    const data = await api("/api/notifications");
    $("#notification-count").textContent =
      data.items.filter((n) => !n.seen).length || "";
  }
  async function renderNotifications() {
    const root = $("#results");
    $("#count").textContent = "";
    root.className = "workspace-view";
    const data = await api("/api/notifications");
    if (view !== "notifications") return;
    root.replaceChildren();
    const header = make("section", undefined, "workspace-intro");
    header.append(
      make("p", "Bandeja de avisos", "eyebrow"),
      make("h2", "Lo que necesita tu atención."),
      make(
        "p",
        "Comentarios nuevos, respuestas y menciones. Tus notas privadas no avisan a otras personas.",
        "muted",
      ),
    );
    const settings = make("div", undefined, "notification-settings"),
      label = make("label", "Resumen por correo"),
      frequency = make("select");
    frequency.append(
      new Option("Apagado", "off"),
      new Option("Diario · sólo pendientes", "daily"),
    );
    frequency.value = data.frequency;
    label.append(frequency);
    frequency.addEventListener(
      "change",
      safe(async () => {
        await api("/api/notifications/settings", {
          method: "PUT",
          body: JSON.stringify({ frequency: frequency.value }),
        });
        toast(
          frequency.value === "daily"
            ? "Resumen diario activado para tu correo verificado."
            : "Resumen por correo desactivado.",
        );
      }),
    );
    const read = make("button", "Marcar todos leídos");
    read.addEventListener(
      "click",
      safe(async () => {
        await api("/api/notifications/read", {
          method: "POST",
          body: JSON.stringify({ all: true }),
        });
        await renderNotifications();
      }),
    );
    settings.append(label, read);
    header.append(settings);
    root.append(header);
    $("#notification-count").textContent =
      data.items.filter((n) => !n.seen).length || "";
    for (const n of data.items) {
      const row = make(
          "article",
          undefined,
          "notification" + (n.seen ? "" : " unread"),
        ),
        link = make("a", n.title);
      link.href =
        "/a/" + n.artifact + "?thread=" + encodeURIComponent(n.thread);
      link.addEventListener("click", () => {
        fetch("/api/notifications/read", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id: n.id }),
          keepalive: true,
        }).catch(() => {});
      });
      row.append(
        make(
          "span",
          {
            mention: "Te mencionaron",
            create: "Nuevo comentario",
            reply: "Nueva respuesta",
            assign: "Seguimiento asignado",
          }[n.kind] || "Actualización",
          "eyebrow",
        ),
        link,
        make("time", new Date(n.created).toLocaleString("es"), "muted"),
      );
      root.append(row);
    }
    if (!data.items.length)
      root.append(make("p", "No tienes avisos pendientes.", "empty"));
  }
  async function renderAdmin() {
    const root = $("#results");
    root.className = "workspace-view";
    $("#count").textContent = "";
    const data = await api("/api/admin");
    if (view !== "admin") return;
    root.replaceChildren();
    const intro = make("section", undefined, "workspace-intro");
    intro.append(
      make("p", "Operación / visión general", "eyebrow"),
      make("h2", "Tu biblioteca, bajo control."),
      make(
        "p",
        "Publicaciones, revisiones y continuidad del servicio. Las notas personales conservan su privacidad incluso en administración.",
        "muted",
      ),
    );
    root.append(intro);
    const metrics = make("div", undefined, "admin-metrics");
    for (const [key, label] of [
      ["artifacts", "Artefactos"],
      ["drafts", "Borradores"],
      ["archived", "Archivados"],
      ["versions", "Versiones"],
    ]) {
      const card = make("div");
      card.append(
        make("span", label),
        make("strong", String(data.counts[key])),
      );
      metrics.append(card);
    }
    root.append(metrics);
    const performance = make("details", undefined, "operation-card");
    performance.append(make("summary", "Rendimiento del servicio"));
    performance.addEventListener("toggle", async () => {
      if (!performance.open || performance.dataset.loaded) return;
      try {
        const sample = await api("/api/operations/performance");
        const table = make("table"),
          head = make("tr");
        for (const label of [
          "Ruta",
          "Muestras",
          "p50 (ms)",
          "p95 (ms)",
          "Errores 5xx",
        ])
          head.append(make("th", label));
        const thead = make("thead");
        thead.append(head);
        table.append(thead);
        const tbody = make("tbody");
        for (const r of sample.routes) {
          const row = make("tr");
          for (const value of [
            r.route,
            r.samples,
            r.p50_ms,
            r.p95_ms,
            r.server_errors,
          ])
            row.append(make("td", String(value)));
          tbody.append(row);
        }
        table.append(tbody);
        const scroll = make("div", undefined, "tabla-caja");
        scroll.tabIndex = 0;
        scroll.setAttribute("aria-label", "Tiempos del servicio");
        scroll.append(table);
        performance.append(
          make(
            "p",
            "Últimas 2000 solicitudes de este proceso. La ventana se reinicia al desplegar. No incluye tiempos de red ni de dibujo del navegador.",
            "muted",
          ),
          scroll,
        );
        performance.dataset.loaded = "1";
      } catch (e) {
        toast(e.message);
      }
    });
    root.append(performance);
    const operations = make("div", undefined, "operations-grid");
    for (const [key, title] of [
      ["backup", "Respaldo automático"],
      ["restore", "Restauración ensayada"],
      ["external", "Copia fuera del NAS"],
      ["worker", "Procesos programados"],
    ]) {
      const state = data.operations[key],
        fresh =
          state?.ok &&
          Date.now() / 1000 - state.at < (key === "worker" ? 300 : 172800),
        card = make("section", undefined, "operation-card");
      card.append(
        make("h3", title),
        make(
          "span",
          fresh ? "Verificado" : state ? "Requiere atención" : "Sin registro",
          fresh ? "status-good" : "status-pending",
        ),
        make(
          "p",
          state?.at
            ? new Date(state.at * 1000).toLocaleString("es")
            : "Aún no se ha registrado una ejecución.",
          "muted",
        ),
      );
      if (state?.detail) card.append(make("p", state.detail));
      operations.append(card);
    }
    root.append(operations);
    const stats = make(
      "p",
      data.counts.users +
        " identidades · " +
        data.counts.tokens +
        " conexiones de agentes · " +
        Math.round(data.file_bytes / 1024 / 1024) +
        " MB de archivos",
      "meta",
    );
    root.append(stats);
    const activity = make("section", undefined, "admin-activity");
    activity.append(make("h3", "Actividad reciente"));
    const actions = {
      organize: "Organización actualizada",
      rename: "Nombre actualizado",
      publish: "Versión guardada",
    };
    for (const event of data.activity) {
      const row = make("div", undefined, "activity-row");
      row.append(
        make("time", new Date(event.at * 1000).toLocaleString("es")),
        make(
          "span",
          actions[event.action] ||
            (event.action.startsWith("release:")
              ? "Versión publicada"
              : event.action.startsWith("access:")
                ? "Acceso actualizado"
                : event.action),
        ),
        make("span", event.title || "Cuenta"),
        make("span", event.name || "Sistema", "muted"),
      );
      activity.append(row);
    }
    root.append(activity);
  }

  addEventListener("beforeunload", () => {
    clearInterval(poll);
    clearInterval(noticePoll);
    listController?.abort();
    graphController?.abort();
    covers.disconnect();
    previews.disconnect();
    more.disconnect();
  });
  Promise.all([
    identity(),
    api("/api/auth/options").then((options) => (authOptions = options)),
  ])
    .then(() => {
      const match = location.pathname.match(/^\/a\/([a-f0-9]{32})$/);
      if (!match && !user?.verified) {
        location.replace("/login");
        return;
      }
      if (match) return reader(match[1]);
      noticeBadge().catch(() => {});
      noticePoll = setInterval(() => {
        if (!document.hidden) noticeBadge().catch(() => {});
      }, 60000);
      const requested = new URLSearchParams(location.search).get("view"),
        tab = $$("[data-view]").find(
          (b) => b.dataset.view === requested && !b.hidden,
        );
      if (tab) {
        tab.click();
        return;
      }
      restoreBrowse();
      return load();
    })
    .catch((error) => {
      toast(error.message);
      empty(
        "No pudimos abrir la biblioteca.",
        "Recarga la página para volver a intentar.",
      );
    });
})();
