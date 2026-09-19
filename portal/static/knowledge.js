/* Atlas local: relaciones explicadas y alternativa navegable por teclado. */
window.BottifactKnowledge = (() => {
  const make = (tag, text, cls) => {
    const e = document.createElement(tag);
    if (text !== undefined) e.textContent = text;
    if (cls) e.className = cls;
    return e;
  };
  const paths = {
    grid: "M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z",
    list: "M3 5h4v4H3z M11 7h10 M3 15h4v4H3z M11 17h10",
    table: "M3 4h18v16H3z M3 9h18 M3 14h18 M9 4v16",
    graph:
      "M8 7l8 3 M7 9l4 8 M16 13l-3 4 M7 4a3 3 0 1 0 0 6 3 3 0 0 0 0-6 M18 8a3 3 0 1 0 0 6 3 3 0 0 0 0-6 M12 16a3 3 0 1 0 0 6 3 3 0 0 0 0-6",
    search: "M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14 M15 15l6 6",
    peek: "M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12 M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6",
    edit: "M4 16l12-12 4 4L8 20H4z M13 7l4 4",
    close: "M6 6l12 12 M6 18L18 6",
    arrow: "M5 12h14 M14 7l5 5-5 5",
    folder: "M3 6h7l2 3h9v11H3z",
    filter: "M4 6h16 M7 12h10 M10 18h4",
  };
  function icon(name) {
    if (window.BottifactUI?.paths[name]) return window.BottifactUI.icon(name);
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("aria-hidden", "true");
    const p = document.createElementNS(svg.namespaceURI, "path");
    p.setAttribute("d", paths[name] || paths.folder);
    svg.append(p);
    return svg;
  }
  function graph(root, data, peek, options = {}) {
    const network = data.network || {
      nodes: data.nodes.map((n) => ({
        ...n,
        kind: "artifact",
        artifact: n.id,
      })),
      edges: data.edges.map((e) => ({ ...e, reason: e.reasons.join(" · ") })),
    };
    const records = new Map(data.nodes.map((n) => [n.id, n])),
      nodes = new Map(network.nodes.map((n) => [n.id, n]));
    const kindNames = {
      artifact: "Artefacto",
      space: "Empresa / espacio",
      topic: "Tema",
      collection: "Colección",
      company: "Empresa",
      project: "Proyecto",
      decision: "Decisión",
      session: "Sesión de trabajo",
    };
    const abort = new AbortController(),
      listen = (el, event, fn) =>
        el.addEventListener(event, fn, { signal: abort.signal });
    const controls = make("div", undefined, "atlas-toolbar"),
      shell = make("div", undefined, "atlas"),
      canvas = make("div", undefined, "atlas-canvas"),
      sidebar = make("aside", undefined, "atlas-inspector");
    root.append(controls, shell);
    shell.append(canvas, sidebar);
    function button(text, fn, cls) {
      const b = make("button", text, cls);
      b.type = "button";
      listen(b, "click", fn);
      return b;
    }
    function select(label, options) {
      const wrap = make("label", label),
        input = make("select");
      for (const [v, t] of options) input.append(new Option(t, v));
      wrap.append(input);
      controls.append(wrap);
      return input;
    }
    const searchWrap = make("label", "Encontrar en este mapa"),
      search = make("input");
    search.type = "search";
    search.placeholder = "Empresa, tema o artefacto…";
    searchWrap.append(search);
    controls.append(searchWrap);
    const lens = select("Conectar por", [
      ["all", "Todas las conexiones"],
      ["space", "Empresas / espacios"],
      ["topic", "Temas"],
      ["collection", "Colecciones"],
      ["company", "Empresas explícitas"],
      ["project", "Proyectos"],
    ]);
    const relation = select("Relación", [
      ["all", "Todas"],
      ["membership", "Pertenencia"],
      ["cites", "Cita"],
      ["updates", "Actualiza"],
      ["contradicts", "Contradice"],
      ["depends_on", "Depende de"],
      ["resolves", "Resuelve"],
    ]);
    const scope = select("Alcance", [
      ["all", "Mapa completo"],
      ["1", "Una conexión"],
      ["2", "Dos conexiones"],
    ]);
    const labelsWrap = make("label", undefined, "atlas-check"),
      labels = make("input");
    labels.type = "checkbox";
    labels.checked = network.nodes.length <= 40;
    labelsWrap.append(labels, document.createTextNode("Mostrar nombres"));
    controls.append(labelsWrap);
    const back = button("← Volver", () => {
      if (history.length) {
        const previous = history.pop();
        selected = previous.id;
        scope.value = previous.scope;
        render();
      }
    });
    controls.append(back);
    const status = make("p", undefined, "atlas-status");
    status.setAttribute("role", "status");
    root.insertBefore(status, shell);
    const legend = make("div", undefined, "atlas-legend");
    for (const [kind, label] of Object.entries(kindNames))
      legend.append(make("span", label, "kind-" + kind));
    root.insertBefore(legend, shell);
    const matches = make("div", undefined, "atlas-search-results");
    root.insertBefore(matches, shell);
    const ns = "http://www.w3.org/2000/svg",
      svg = document.createElementNS(ns, "svg");
    svg.setAttribute("viewBox", "0 0 1000 680");
    svg.setAttribute("role", "group");
    svg.setAttribute(
      "aria-label",
      "Grafo de empresas, temas y artefactos; flechas del teclado para mover, más y menos para zoom.",
    );
    svg.setAttribute("tabindex", "0");
    canvas.append(svg);
    const layer = document.createElementNS(ns, "g");
    svg.append(layer);
    let savedPositions = options.positions || {},
      selected = null,
      history = [],
      zoom = 1,
      tx = 0,
      ty = 0,
      drag = null,
      shown = [],
      edges = [],
      positions = new Map(),
      renderAbort = new AbortController();
    function transform() {
      layer.setAttribute(
        "transform",
        `translate(${tx} ${ty}) translate(500 340) scale(${zoom}) translate(-500 -340)`,
      );
    }
    const zoomControls = make("div", undefined, "atlas-controls");
    function reset() {
      zoom = 1;
      tx = 0;
      ty = 0;
      transform();
    }
    for (const [text, label, fn] of [
      [
        "+",
        "Acercar",
        () => {
          zoom = Math.min(4, zoom * 1.25);
          transform();
        },
      ],
      [
        "−",
        "Alejar",
        () => {
          zoom = Math.max(0.4, zoom / 1.25);
          transform();
        },
      ],
      ["↺", "Centrar mapa", reset],
    ]) {
      const b = button(text, fn);
      b.setAttribute("aria-label", label);
      b.title = label;
      zoomControls.append(b);
    }
    canvas.append(
      zoomControls,
      make("p", "Arrastra el fondo o un nodo · rueda para zoom", "atlas-hint"),
    );
    function choose(id, local = false) {
      if (!nodes.has(id)) return;
      if (selected !== id || local)
        history.push({ id: selected, scope: scope.value });
      selected = id;
      if (local) scope.value = "1";
      render();
      sidebar.querySelector("h2")?.focus({ preventScroll: true });
    }
    function action(text, fn, cls) {
      const b = make("button", text, cls);
      b.type = "button";
      b.addEventListener("click", fn, { signal: renderAbort.signal });
      return b;
    }
    function render() {
      renderAbort.abort();
      renderAbort = new AbortController();
      back.disabled = !history.length;
      scope.options[1].disabled = scope.options[2].disabled = !selected;
      layer.replaceChildren();
      sidebar.replaceChildren();
      const allowed = network.nodes.filter(
          (n) =>
            n.kind === "artifact" ||
            lens.value === "all" ||
            n.kind === lens.value,
        ),
        valid = new Set(allowed.map((n) => n.id));
      if (selected && !valid.has(selected)) {
        selected = null;
        scope.value = "all";
      }
      const allEdges = network.edges.filter(
        (e) =>
          valid.has(e.source) &&
          valid.has(e.target) &&
          (relation.value === "all" ||
            (e.kind || "membership") === relation.value),
      );
      let visible = new Set(valid);
      if (selected && scope.value !== "all") {
        visible = new Set([selected]);
        let frontier = new Set([selected]);
        for (let i = 0; i < Number(scope.value); i++) {
          const next = new Set();
          for (const e of allEdges) {
            if (frontier.has(e.source)) next.add(e.target);
            if (frontier.has(e.target)) next.add(e.source);
          }
          next.forEach((id) => visible.add(id));
          frontier = next;
        }
      }
      shown = allowed.filter((n) => visible.has(n.id));
      edges = allEdges.filter(
        (e) => visible.has(e.source) && visible.has(e.target),
      );
      const norm = (s) =>
          s
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .toLowerCase(),
        words = norm(search.value).trim().split(/\s+/).filter(Boolean),
        found = allowed.filter((n) =>
          words.every((w) =>
            norm(
              n.title +
                " " +
                (n.aliases || []).join(" ") +
                " " +
                (kindNames[n.kind] || ""),
            ).includes(w),
          ),
        );
      matches.replaceChildren();
      matches.hidden = !words.length;
      if (words.length) {
        matches.append(
          make("p", found.length + " coincidencias en el conjunto cargado"),
        );
        for (const n of found.slice(0, 30))
          matches.append(
            action(kindNames[n.kind] + " · " + n.title, () =>
              choose(n.id, true),
            ),
          );
        if (found.length > 30)
          matches.append(
            make("p", "Refina la búsqueda para ver las demás coincidencias."),
          );
      }
      status.textContent =
        `${shown.filter((n) => n.kind === "artifact").length} de ${data.total} artefactos · ${shown.filter((n) => n.kind !== "artifact").length} grupos · ${edges.length} conexiones visibles` +
        (data.truncated
          ? " · conjunto limitado a los 120 artefactos más recientes; usa los filtros de biblioteca."
          : ".") +
        (network.entity_truncated
          ? " Algunos grupos se omitieron por el límite de 300."
          : "");
      if (!shown.length) {
        sidebar.append(
          make("h2", "No hay piezas para este mapa."),
          make("p", "Ajusta los filtros de la biblioteca."),
        );
        return;
      }
      // Deterministic bounded layout, calculated once per scope. No perpetual animation.
      positions = new Map(
        shown.map((n, i) => {
          const a = i * 2.399963,
            r = 35 * Math.sqrt(i);
          return [n.id, { x: 500 + Math.cos(a) * r, y: 340 + Math.sin(a) * r }];
        }),
      );
      for (let step = 0; step < 120; step++) {
        const force = new Map(shown.map((n) => [n.id, { x: 0, y: 0 }]));
        for (let i = 0; i < shown.length; i++)
          for (let j = i + 1; j < shown.length; j++) {
            const a = positions.get(shown[i].id),
              b = positions.get(shown[j].id),
              dx = a.x - b.x,
              dy = a.y - b.y,
              d = Math.max(16, Math.hypot(dx, dy)),
              power =
                (8500 *
                  (shown[i].kind !== "artifact" && shown[j].kind !== "artifact"
                    ? 6
                    : 1)) /
                (d * d * d);
            force.get(shown[i].id).x += dx * power;
            force.get(shown[i].id).y += dy * power;
            force.get(shown[j].id).x -= dx * power;
            force.get(shown[j].id).y -= dy * power;
          }
        for (const e of edges) {
          const a = positions.get(e.source),
            b = positions.get(e.target),
            dx = b.x - a.x,
            dy = b.y - a.y,
            d = Math.max(1, Math.hypot(dx, dy)),
            f = (d - 100) * 0.045;
          force.get(e.source).x += (dx / d) * f;
          force.get(e.source).y += (dy / d) * f;
          force.get(e.target).x -= (dx / d) * f;
          force.get(e.target).y -= (dy / d) * f;
        }
        for (const n of shown) {
          const p = positions.get(n.id),
            f = force.get(n.id);
          p.x += Math.max(-12, Math.min(12, f.x)) + (500 - p.x) * 0.006;
          p.y += Math.max(-12, Math.min(12, f.y)) + (320 - p.y) * 0.006;
        }
      }
      const points = [...positions.values()],
        minX = Math.min(...points.map((p) => p.x)),
        maxX = Math.max(...points.map((p) => p.x)),
        minY = Math.min(...points.map((p) => p.y)),
        maxY = Math.max(...points.map((p) => p.y)),
        fit = Math.min(
          840 / Math.max(1, maxX - minX),
          510 / Math.max(1, maxY - minY),
          2,
        );
      for (const p of points) {
        p.x = 500 + (p.x - (minX + maxX) / 2) * fit;
        p.y = 320 + (p.y - (minY + maxY) / 2) * fit;
      }
      for (const [id, p] of Object.entries(savedPositions))
        if (positions.has(id) && Number.isFinite(p.x) && Number.isFinite(p.y))
          positions.set(id, { x: p.x, y: p.y });
      const near = new Set(
        selected
          ? [
              selected,
              ...edges
                .filter((e) => e.source === selected || e.target === selected)
                .flatMap((e) => [e.source, e.target]),
            ]
          : shown.map((n) => n.id),
      );
      for (const e of edges) {
        const line = document.createElementNS(ns, "line");
        line.dataset.source = e.source;
        line.dataset.target = e.target;
        line.setAttribute(
          "class",
          "atlas-edge" +
            (selected && (e.source === selected || e.target === selected)
              ? " lit"
              : ""),
        );
        const title = document.createElementNS(ns, "title");
        title.textContent = e.reason;
        line.append(title);
        if (e.kind && e.kind !== "membership") {
          line.style.strokeDasharray = "6 4";
          line.setAttribute("tabindex", "0");
          line.setAttribute("role", "button");
          line.setAttribute("aria-label", e.reason);
          const inspect = () => {
            sidebar.replaceChildren(
              make("h2", "Evidencia de la conexión"),
              make("p", e.reason),
              make("p", "Versión: " + (e.version || "no registrada")),
            );
            if (options.related)
              sidebar.append(
                action("Revisar referencias", () => options.related(e.source)),
              );
          };
          line.addEventListener("click", inspect, {
            signal: renderAbort.signal,
          });
          line.addEventListener(
            "keydown",
            (event) => {
              if (event.key === "Enter") inspect();
            },
            { signal: renderAbort.signal },
          );
        }
        layer.append(line);
      }
      for (const n of shown) {
        const g = document.createElementNS(ns, "g"),
          circle = document.createElementNS(ns, "circle"),
          title = document.createElementNS(ns, "title");
        g.dataset.node = n.id;
        g.setAttribute(
          "class",
          "atlas-node kind-" +
            n.kind +
            (selected === n.id ? " selected" : "") +
            (!near.has(n.id) ? " dim" : ""),
        );
        g.setAttribute("tabindex", "0");
        g.setAttribute("role", "button");
        g.setAttribute("aria-label", kindNames[n.kind] + ": " + n.title);
        g.setAttribute("aria-pressed", String(n.id === selected));
        circle.setAttribute(
          "r",
          n.kind === "artifact"
            ? 6
            : Math.min(21, 11 + Math.sqrt(n.count || 1)),
        );
        title.textContent = n.title;
        g.append(circle, title);
        const text = document.createElementNS(ns, "text");
        text.setAttribute("class", "atlas-label");
        text.setAttribute("x", "12");
        text.setAttribute("y", "-12");
        text.textContent =
          n.title.length > 44 ? n.title.slice(0, 41) + "…" : n.title;
        text.setAttribute("data-label", "");
        text.style.display =
          labels.checked || n.kind !== "artifact" || selected === n.id
            ? ""
            : "none";
        g.append(text);
        g.addEventListener(
          "click",
          () => {
            if (!g.dataset.dragged) choose(n.id);
            delete g.dataset.dragged;
          },
          { signal: renderAbort.signal },
        );
        g.addEventListener(
          "keydown",
          (e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              choose(n.id);
            }
          },
          { signal: renderAbort.signal },
        );
        g.addEventListener(
          "pointerenter",
          () => {
            text.style.display = "";
            for (const line of layer.querySelectorAll("line"))
              line.classList.toggle(
                "hovered",
                line.dataset.source === n.id || line.dataset.target === n.id,
              );
          },
          { signal: renderAbort.signal },
        );
        g.addEventListener(
          "pointerleave",
          () => {
            for (const line of layer.querySelectorAll(".hovered"))
              line.classList.remove("hovered");
            text.style.display =
              labels.checked || n.kind !== "artifact" || selected === n.id
                ? ""
                : "none";
          },
          { signal: renderAbort.signal },
        );
        layer.append(g);
      }
      locate();
      reset();
      const node = nodes.get(selected);
      if (node) {
        const title = make("h2", node.title);
        title.tabIndex = -1;
        sidebar.append(make("p", kindNames[node.kind], "eyebrow"), title);
        if (node.kind === "artifact") {
          const record = records.get(node.artifact);
          sidebar.append(
            make("p", record.space + " · " + record.category, "muted"),
            action("Vista previa", () => peek(record), "primary"),
          );
        } else
          sidebar.append(
            make(
              "p",
              (node.count || 0) + " artefactos en este conjunto.",
              "muted",
            ),
          );
        sidebar.append(
          action("Explorar conexiones", () => choose(node.id, true)),
          make("h3", "Por qué están conectados"),
        );
        const related = allEdges.filter(
          (e) => e.source === node.id || e.target === node.id,
        );
        if (!related.length)
          sidebar.append(make("p", "Sin conexiones para esta vista."));
        for (const e of related) {
          const other = nodes.get(e.source === node.id ? e.target : e.source),
            b = action("", () => choose(other.id), "atlas-related");
          b.append(make("strong", other.title), make("span", e.reason));
          sidebar.append(b);
        }
      } else
        sidebar.append(
          make("p", "Tu mapa de conocimiento", "eyebrow"),
          make("h2", "Empresas, temas y trabajo conectado."),
          make(
            "p",
            "Selecciona una empresa o tema para ver sus artefactos. Un mismo tema puede conectar espacios distintos.",
            "muted",
          ),
          make(
            "p",
            "Los espacios y colecciones son asignados. Los temas pueden ser manuales o sugeridos por reglas; cada vínculo muestra su origen.",
            "meta",
          ),
        );
      const directory = make("details", undefined, "atlas-directory");
      directory.append(make("summary", "Explorar en lista · " + shown.length));
      for (const n of shown)
        directory.append(
          action(kindNames[n.kind] + " · " + n.title, () => choose(n.id)),
        );
      sidebar.append(directory);
    }
    function locate() {
      for (const line of layer.querySelectorAll("line")) {
        const a = positions.get(line.dataset.source),
          b = positions.get(line.dataset.target);
        for (const [k, v] of Object.entries({
          x1: a.x,
          y1: a.y,
          x2: b.x,
          y2: b.y,
        }))
          line.setAttribute(k, v);
      }
      for (const n of layer.querySelectorAll("[data-node]")) {
        const p = positions.get(n.dataset.node);
        n.setAttribute("transform", `translate(${p.x} ${p.y})`);
      }
    }
    listen(svg, "pointerdown", (e) => {
      if (e.button !== 0) return;
      const node = e.target.closest("[data-node]");
      drag = {
        x: e.clientX,
        y: e.clientY,
        tx,
        ty,
        node: node?.dataset.node,
        element: node,
      };
      (node || svg).setPointerCapture(e.pointerId);
    });
    if (options.save)
      controls.append(
        button("Guardar disposición", async () => {
          savedPositions = Object.fromEntries(positions);
          try {
            await options.save(savedPositions);
            status.textContent = "Disposición guardada en tu cuenta.";
          } catch (e) {
            status.textContent = e.message;
          }
        }),
      );
    listen(svg, "pointermove", (e) => {
      if (!drag) return;
      const scale = 1000 / svg.getBoundingClientRect().width,
        dx = (e.clientX - drag.x) * scale,
        dy = (e.clientY - drag.y) * scale;
      if (drag.node) {
        if (Math.abs(dx) + Math.abs(dy) > 4) drag.element.dataset.dragged = "1";
        const pos = positions.get(drag.node);
        pos.x += dx / zoom;
        pos.y += dy / zoom;
        drag.x = e.clientX;
        drag.y = e.clientY;
        locate();
      } else {
        tx = drag.tx + dx;
        ty = drag.ty + dy;
        transform();
      }
    });
    for (const name of ["pointerup", "pointercancel"])
      listen(svg, name, () => (drag = null));
    svg.addEventListener(
      "wheel",
      (e) => {
        e.preventDefault();
        zoom = Math.max(0.4, Math.min(4, zoom * (e.deltaY < 0 ? 1.1 : 0.9)));
        transform();
      },
      { passive: false, signal: abort.signal },
    );
    listen(svg, "keydown", (e) => {
      if (e.target !== svg) return;
      const delta = e.shiftKey ? 70 : 30;
      if (e.key === "ArrowLeft") tx += delta;
      else if (e.key === "ArrowRight") tx -= delta;
      else if (e.key === "ArrowUp") ty += delta;
      else if (e.key === "ArrowDown") ty -= delta;
      else if (e.key === "+") zoom = Math.min(4, zoom * 1.2);
      else if (e.key === "-") zoom = Math.max(0.4, zoom / 1.2);
      else return;
      e.preventDefault();
      transform();
    });
    listen(lens, "change", () => {
      selected = null;
      history = [];
      scope.value = "all";
      render();
    });
    for (const c of [scope, labels, relation]) listen(c, "change", render);
    listen(search, "input", render);
    render();
    return {
      destroy() {
        abort.abort();
        renderAbort.abort();
      },
    };
  }
  return { icon, graph };
})();
