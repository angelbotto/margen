/* Tabla local: filtros, selección, grupos, paginación y CSV. Conserva la fuente. */
(() => {
  "use strict";
  const instances = new WeakMap(),
    normal = (s) =>
      s
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase();
  function init(root = document) {
    return [
      ...(root.matches?.("[data-explorador]") ? [root] : []),
      ...root.querySelectorAll("[data-explorador]"),
    ].map((el) => {
      if (instances.has(el)) return instances.get(el);
      const form = el.querySelector("form"),
        table = el.querySelector("table"),
        status = el.querySelector("[data-explorador-estado]"),
        initial = table?.tBodies[0],
        rows = [...(initial?.rows || [])],
        headers = [...(table?.tHead?.rows[0]?.cells || [])];
      if (
        !form ||
        !status ||
        !rows.length ||
        !headers.length ||
        headers.length > 16 ||
        rows.length > 2000 ||
        rows.some((r) => r.cells.length !== headers.length)
      )
        return null;
      const abort = new AbortController(),
        listen = (node, type, fn) =>
          node.addEventListener(type, fn, { signal: abort.signal }),
        make = (tag, text) => {
          const e = document.createElement(tag);
          if (text !== undefined) e.textContent = text;
          return e;
        },
        button = (label, fn) => {
          const b = make("button", label);
          b.type = "button";
          listen(b, "click", fn);
          return b;
        };
      const cells = rows.map(row => [...row.cells]);
      let columnOrder = headers.map((_, index) => index);
      const names = headers.map((h) =>
          (h.querySelector("summary") || h).textContent
            .replace(/[↕↑↓]/g, "")
            .trim(),
        ),
        values = cells.map(row => row.map(c => c.dataset.valor ?? c.textContent.trim())),
        raw = rows.map((r) =>
          [...r.cells].map((c) => c.dataset.valor ?? c.textContent.trim()),
        );
      const originalCellStyles = cells.map(row => row.map(cell => cell.getAttribute("style")));
      const originalHeaderStyles = headers.map(h => h.getAttribute("style"));
      const types = headers.map(
        (h, c) =>
          h.dataset.tipo ||
          (rows.every((r) => r.cells[c].hasAttribute("data-valor"))
            ? "numero"
            : "texto"),
      );
      if (
        types.some((t) => !["texto", "numero", "fecha"].includes(t)) ||
        raw.some((row) =>
          row.some(
            (v, c) =>
              (types[c] === "numero" &&
                v !== "" &&
                (!Number.isFinite(Number(v)) || Math.abs(Number(v)) > 1e12)) ||
              (types[c] === "fecha" &&
                v !== "" &&
                (!/^\d{4}-\d{2}-\d{2}$/.test(v) ||
                  !Number.isFinite(Date.parse(v)) ||
                  new Date(v).toISOString().slice(0, 10) !== v)),
          ),
        )
      )
        return null;
      rows.forEach((r, i) => {
        r.dataset.rowId ||= el.id + "-record-" + (i + 1);
        if (!r.id) r.id = r.dataset.rowId;
        [...r.cells].forEach((c, j) => {
          c.dataset.cellId = r.dataset.rowId + ":" + j;
          if (!c.id) c.id = r.dataset.rowId + "-cell-" + j;
        });
      });
      const originalFormNodes = [...form.childNodes];
      const originalTabStops = [
        ...table.tHead.querySelectorAll("button,summary"),
      ].map((node) => [node, node.getAttribute("tabindex")]);
      const previous = {
          status: status.textContent,
          sort: headers.map((h) => h.getAttribute("aria-sort")),
          hidden: rows.map((r) => [...r.cells].map((c) => c.hidden)),
          headers: headers.map((h) => h.hidden),
        },
        parts = [],
        selected = new Set(),
        collapsed = new Set();
      let sorts = [{ col: 0, dir: 1 }],
        page = 0,
        visible = [],
        pageRows = [],
        destroyed = false,
        renderAbort = new AbortController();
      const tools = make("div");
      tools.className = "explorador-utilidades";
      const advanced = make("details"),
        summary = make("summary", "Filtrar columna");
      advanced.className = "control-menu";
      const panel = make("div");
      panel.className = "control-panel";
      panel.tabIndex = 0;
      panel.setAttribute("role", "region");
      panel.setAttribute("aria-label", "Filtro por columna");
      const field = make("select"),
        match = make("input"),
        min = make("input"),
        max = make("input");
      field.setAttribute("aria-label", "Columna a filtrar");
      field.append(make("option", "Todas"));
      field.firstChild.value = "";
      names.forEach((n, c) => {
        const o = make("option", n);
        o.value = c;
        field.append(o);
      });
      match.placeholder = "Contiene…";
      match.setAttribute("aria-label", "Texto del filtro");
      min.type = max.type = "number";
      min.placeholder = "Desde";
      max.placeholder = "Hasta";
      min.setAttribute("aria-label", "Valor mínimo");
      max.setAttribute("aria-label", "Valor máximo");
      min.hidden = max.hidden = true;
      panel.append(field, match, min, max);
      advanced.append(summary, panel);
      const density = make("select");
      density.setAttribute("aria-label", "Densidad de filas");
      for (const [v, n] of [
        ["normal", "Espaciado cómodo"],
        ["compacta", "Espaciado compacto"],
      ]) {
        const o = make("option", n);
        o.value = v;
        density.append(o);
      }
      const selectAll = make("input");
      selectAll.type = "checkbox";
      selectAll.setAttribute("aria-label", "Seleccionar filas de esta página");
      const selectionLabel = make("label", "Seleccionar página ");
      selectionLabel.prepend(selectAll);
      const selectedCount = make("span", ""),
        csv = button("Exportar CSV", () => downloadCSV()),
        clear = button("Limpiar selección", () => {
          selected.clear();
          update();
        });
      tools.append(
        advanced,
        density,
        selectionLabel,
        selectedCount,
        clear,
        csv,
      );
      form.after(tools);

      const footer = make("div");
      footer.className = "explorador-paginacion";
      const prev = button("←", () => {
          page--;
          update();
        }),
        next = button("→", () => {
          page++;
          update();
        }),
        pageStatus = make("span"),
        size = make("select");
      prev.setAttribute("aria-label", "Página anterior de tabla");
      next.setAttribute("aria-label", "Página siguiente de tabla");
      size.setAttribute("aria-label", "Filas por página");
      for (const n of [10, 25, 50, 100]) {
        const o = make("option", n + " filas");
        o.value = n;
        size.append(o);
      }
      size.value = String(
        [10, 25, 50, 100].includes(Number(el.dataset.paginaTamano))
          ? Number(el.dataset.paginaTamano)
          : 25,
      );
      footer.append(pageStatus, prev, next, size);
      el.querySelector(".tabla-caja").after(footer);
      const model = window.BottifactTableModel;
      let query = model?.empty(),
        viewState = [],
        pinned = new Set();
      const key =
        "bottifact-table:" +
        (document.querySelector('meta[name="nota-documento"]')?.content ||
          location.pathname) +
        ":" +
        (el.id ||
          [...document.querySelectorAll("[data-explorador]")].indexOf(el));
      const filters = make("details"),
        filterBody = make("div"),
        join = make("select");
      filters.className = "control-menu";
      filterBody.className = "control-panel";
      filters.append(make("summary", "Filtros"), filterBody);
      filters.dataset.panelWidth = "400";
      join.append(
        new Option("Todas las condiciones", "and"),
        new Option("Cualquier condición", "or"),
      );
      join.setAttribute("aria-label", "Combinar condiciones");
      filterBody.append(join);
      listen(join, "change", () => {
        query.join = join.value;
        resetPage();
      });
      function drawRules() {
        filterBody.querySelectorAll("[data-rule]").forEach((n) => n.remove());
        query.rules.forEach((rule, index) => {
          if (rule.facet) return;
          const row = make("div");
          row.dataset.rule = "";
          row.style.cssText =
            "display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-block:12px";
          const col = make("select"),
            op = make("select"),
            value = make("input"),
            upper = make("input");
          names.forEach((n, c) => col.append(new Option(n, String(c))));
          col.value = rule.column;
          col.setAttribute("aria-label", "Columna de condición " + (index + 1));
          for (const [v, n] of [
            ["contains", "Contiene"],
            ["eq", "Igual a"],
            ["in", "Uno de"],
            ["gte", "Desde"],
            ["lte", "Hasta"],
            ["between", "Entre"],
            ["empty", "Sin valor"],
          ])
            op.append(new Option(n, v));
          op.value = rule.operator;
          op.setAttribute("aria-label", "Operador de condición " + (index + 1));
          value.setAttribute("aria-label", "Valor de condición " + (index + 1));
          value.style.width = "130px";
          value.type =
            op.value === "in"
              ? "text"
              : types[Number(col.value)] === "numero"
                ? "number"
                : types[Number(col.value)] === "fecha"
                  ? "date"
                  : "text";
          value.value = Array.isArray(rule.value)
            ? rule.value.join(",")
            : (rule.value ?? "");
          value.hidden = op.value === "empty";
          upper.type = value.type;
          upper.style.width = "130px";
          upper.value = rule.upper ?? "";
          upper.hidden = op.value !== "between";
          upper.setAttribute("aria-label", "Límite superior " + (index + 1));
          listen(col, "change", () => {
            rule.column = col.value;
            rule.value = "";
            drawRules();
            resetPage();
          });
          listen(op, "change", () => {
            rule.operator = op.value;
            rule.value = "";
            drawRules();
            resetPage();
          });
          listen(value, "input", () => {
            rule.value =
              op.value === "in"
                ? value.value.split(",").map((v) => v.trim())
                : value.value;
            resetPage();
          });
          listen(upper, "input", () => {
            rule.upper = upper.value;
            resetPage();
          });
          row.append(
            col,
            op,
            value,
            upper,
            button("Quitar condición", () => {
              query.rules.splice(index, 1);
              drawRules();
              resetPage();
            }),
          );
          filterBody.append(row);
        });
      }
      filterBody.append(
        button("Añadir condición", () => {
          if (query.rules.length < 12) {
            query.rules.push({ column: "0", operator: "contains", value: "" });
            drawRules();
          }
        }),
      );
      if (model) tools.prepend(filters);
      const views = make("details"),
        viewBody = make("div"),
        viewSelect = make("select"),
        viewName = make("input"),
        viewMessage = make("p");
      views.className = "control-menu";
      viewBody.className = "control-panel";
      viewName.placeholder = "Nombre de la vista";
      viewName.setAttribute("aria-label", "Nombre de la vista");
      viewSelect.setAttribute("aria-label", "Vista guardada");
      views.append(make("summary", "Vistas"), viewBody);
      viewBody.append(viewSelect, viewName);
      try {
        viewState = JSON.parse(localStorage.getItem(key) || "[]");
        if (!Array.isArray(viewState)) viewState = [];
      } catch {
        viewState = [];
      }
      function viewOptions() {
        viewSelect.replaceChildren(
          new Option("Vistas en este dispositivo", ""),
        );
        viewState.forEach((v, i) =>
          viewSelect.append(new Option(v.name, String(i))),
        );
      }
      viewOptions();
      viewBody.append(
        button("Guardar vista", () => {
          const name = viewName.value.trim().slice(0, 80);
          if (!name) return;
          const view = {
            name,
            query,
            sorts,
            columnOrder,
            pinned: [...pinned],
            widths: headers.map(h => h.style.width),
            group: form.elements.grupo?.value || "",
            search: form.elements.buscar?.value || "",
            state: form.elements.estado?.value || "",
            hidden: [
              ...form.querySelectorAll("[data-columna]:not(:checked)"),
            ].map((c) => c.dataset.columna),
            density: density.value,
            presentation: presentation.value,
            field: field.value,
            match: match.value,
            min: min.value,
            max: max.value,
          };
          try {
            const next = [
              ...viewState.filter((v) => v.name !== name),
              view,
            ].slice(-20);
            localStorage.setItem(key, JSON.stringify(next));
            viewState = JSON.parse(JSON.stringify(next));
            viewOptions();
            viewMessage.textContent =
              "Vista guardada sólo en este dispositivo.";
          } catch {
            viewMessage.textContent = "No se pudo guardar en este navegador.";
          }
        }),
        button("Eliminar vista", () => {
          if (viewSelect.value === "") return;
          const next = viewState.filter(
            (_, i) => i !== Number(viewSelect.value),
          );
          try {
            localStorage.setItem(key, JSON.stringify(next));
            viewState = next;
            viewOptions();
          } catch {
            viewMessage.textContent = "No se pudo eliminar.";
          }
        }),
        viewMessage,
      );
      listen(viewSelect, "change", () => {
        const v = viewState[Number(viewSelect.value)];
        if (viewSelect.value === "" || !v) return;
        query = JSON.parse(JSON.stringify(v.query || model.empty()));
        join.value = query.join;
        sorts = v.sorts || [];
        const order = Array.isArray(v.columnOrder) ? [...new Set(v.columnOrder.filter(c => Number.isInteger(c) && c >= 0 && c < headers.length))] : [];
        columnOrder = [...order, ...headers.map((_, c) => c).filter(c => !order.includes(c))];
        pinned = new Set((v.pinned || []).filter(c => Number.isInteger(c) && c >= 0 && c < headers.length));
        headers.forEach((h, c) => {
          const width = /^\d+px$/.test(v.widths?.[c] || "") ? Math.max(100, Math.min(480, parseInt(v.widths[c]))) + "px" : "";
          [h, ...cells.map(row => row[c])].forEach(cell => { cell.style.width = width; cell.style.minWidth = width; });
          const control = layoutBody.querySelector('[data-column-control="' + c + '"]');
          control.querySelector("[data-column-pin]").checked = pinned.has(c);
          control.querySelector('[type=range]').value = parseInt(width) || 180;
        });
        applyColumnOrder();
        for (const [name, value] of [
          ["grupo", v.group],
          ["buscar", v.search],
          ["estado", v.state],
        ])
          if (form.elements[name]) form.elements[name].value = value || "";
        for (const c of form.querySelectorAll("[data-columna]"))
          c.checked = !(v.hidden || []).includes(c.dataset.columna);
        density.value = v.density || "normal";
        el.dataset.densidad = density.value;
        presentation.value = ["auto", "table", "cards", "list", "board"].includes(v.presentation)
          ? v.presentation
          : "auto";
        setPresentation();
        field.value = v.field || "";
        match.value = v.match || "";
        min.value = v.min || "";
        max.value = v.max || "";
        drawRules();
        resetPage();
      });
      if (model) tools.append(views);
      const layout = make("details"),
        layoutBody = make("div");
      layout.className = "control-menu";
      layoutBody.className = "control-panel";
      layout.append(make("summary", "Diseño"), layoutBody);
      layout.dataset.panelWidth = "340";
      const columnList = make("div");
      columnList.className = "explorer-column-list";
      layoutBody.append(columnList);
      headers.forEach((h, c) => {
        const line = make("div"),
          pin = make("input"),
          width = make("input");
        pin.type = "checkbox";
        pin.dataset.columnPin = String(c);
        pin.setAttribute("aria-label", "Fijar " + names[c]);
        width.type = "range";
        width.min = "100";
        width.max = "480";
        width.value = "180";
        width.setAttribute("aria-label", "Ancho de " + names[c]);
        listen(width, "input", () => {
          [h, ...cells.map(row => row[c])].forEach((cell) => {
            cell.style.minWidth = width.value + "px";
            cell.style.width = width.value + "px";
          });
          positionColumns();
        });
        listen(pin, "change", () => {
          pin.checked ? pinned.add(c) : pinned.delete(c);
          positionColumns();
        });
        line.className = "explorer-column";
        line.dataset.columnControl = String(c);
        const name = make("span", names[c]);
        name.className = "explorer-column-name";
        const pinLabel = make("label", "Fijar");
        pinLabel.prepend(pin);
        const resize = make("details");
        resize.append(make("summary", "Ancho"), width);
        const moves = make("div");
        moves.className = "explorer-column-moves";
        for (const [step, text] of [[-1, "↑"], [1, "↓"]]) {
          const action = button(text, () => {
            const index = columnOrder.indexOf(c), target = columnOrder[index + step];
            if (target !== undefined) reorderColumn(c, target);
          });
          action.dataset.move = String(step);
          action.setAttribute("aria-label", "Mover " + names[c] + (step === -1 ? " antes" : " después"));
          action.title = action.getAttribute("aria-label");
          moves.append(action);
        }
        line.draggable = true;
        listen(line, "dragstart", event => { event.dataTransfer.setData("application/x-margen-column", String(c)); event.dataTransfer.effectAllowed = "move"; });
        listen(line, "dragover", event => event.preventDefault());
        listen(line, "drop", event => {
          event.preventDefault();
          const source = event.dataTransfer.getData("application/x-margen-column");
          if (/^\d+$/.test(source)) reorderColumn(Number(source), c);
        });
        line.append(name, moves, pinLabel, resize);
        columnList.append(line);
      });
      const columnSearch = make("input");
      columnSearch.type = "search";
      columnSearch.placeholder = "Buscar columna…";
      columnSearch.setAttribute("aria-label", "Buscar columna");
      listen(columnSearch, "input", () => {
        [...columnList.children].forEach(line => { line.hidden = !normal(names[Number(line.dataset.columnControl)]).includes(normal(columnSearch.value)); });
      });
      layoutBody.insertBefore(columnSearch, columnList);
      const orderHint = make("p", "Arrastra las columnas o usa las flechas para cambiar su orden.");
      layoutBody.insertBefore(orderHint, columnList);
      const orderStatus = make("span");
      orderStatus.className = "sr-only";
      orderStatus.setAttribute("role", "status");
      layoutBody.append(orderStatus);
      function applyColumnOrder() {
        for (const c of columnOrder) {
          table.tHead.rows[0].append(headers[c]);
          rows.forEach((row, i) => row.append(cells[i][c]));
          columnList.append(layoutBody.querySelector('[data-column-control="' + c + '"]'));
        }
        [...columnList.children].forEach((line, index) => {
          line.querySelector('[data-move="-1"]').disabled = index === 0;
          line.querySelector('[data-move="1"]').disabled = index === columnOrder.length - 1;
        });
        positionColumns();
      }
      function reorderColumn(from, to) {
        const a = columnOrder.indexOf(from), b = columnOrder.indexOf(to);
        if (a < 0 || b < 0 || a === b) return;
        columnOrder.splice(a, 1); columnOrder.splice(b, 0, from);
        applyColumnOrder();
        orderStatus.textContent = names[from] + " en posición " + (b + 1);
      }
      tools.append(layout);
      // One toolbar, progressively disclosed options, and the same DOM records in both layouts.
      const moved = [],
        wrappers = [];
      const move = (node, target) => {
        if (!node) return;
        moved.push([node, node.parentNode, node.nextSibling]);
        target.append(node);
      };
      const searchInput = form.elements.buscar;
      let searchLabel = searchInput?.closest("label");
      if (searchLabel) {
        searchLabel.classList.add("explorer-search");
        [...searchLabel.childNodes]
          .filter((n) => n.nodeType === 3)
          .forEach((n) => {
            const label = make("span", n.textContent);
            label.className = "control-etiqueta";
            n.replaceWith(label);
          });
        searchInput.placeholder = "Buscar en todos los registros…";
        searchInput.setAttribute("aria-label", "Buscar en todos los registros");
      }
      for (const name of ["estado", "grupo"]) {
        const input = form.elements[name];
        if (input)
          move(
            input.closest("label") || input,
            name === "estado" ? filterBody : layoutBody,
          );
      }
      const legacyState = form.elements.estado?.closest("label");
      if (
        model &&
        legacyState &&
        new Set(values.map((row) => row[Number(el.dataset.columnaEstado ?? 2)]))
          .size <= 12
      )
        legacyState.classList.add("explorer-legacy-state");
      const columnsTitle = make("p", "Columnas visibles");
      columnsTitle.className = "explorer-panel-title";
      layoutBody.prepend(columnsTitle);
      form.querySelectorAll("[data-columna]").forEach((input) => {
        const line = layoutBody.querySelector(
          '[data-column-control="' + input.dataset.columna + '"]',
        );
        if (line) {
          line.querySelector(".explorer-column-name").hidden = true;
          move(input.closest("label") || input, line);
        } else move(input.closest("label") || input, layoutBody);
      });
      // Empty legacy disclosures are kept for destroy(), not shown as duplicate menus.
      for (const node of originalFormNodes) {
        if (
          node.nodeType === 1 &&
          node !== searchLabel &&
          node.parentNode === form
        ) {
          wrappers.push([node, node.hidden]);
          node.hidden = true;
        }
      }
      const presentation = make("select");
      presentation.setAttribute("aria-label", "Presentación de registros");
      presentation.append(
        new Option("Automática · fichas en móvil", "auto"),
        new Option("Tabla · comparar columnas", "table"),
        new Option("Fichas · leer registros", "cards"),
        new Option("Lista · recorrer rápido", "list"),
        new Option("Tablero · comparar grupos", "board"),
      );
      const presentLabel = make("label", "Presentación");
      presentLabel.append(presentation);
      const densityLabel = make("label", "Espaciado");
      densityLabel.append(density);
      const mobileSort = make("select");
      mobileSort.setAttribute("aria-label", "Ordenar registros");
      mobileSort.append(new Option("Orden original", ""));
      names.forEach((name, c) => {
        mobileSort.append(
          new Option(name + " ↑", c + ":1"),
          new Option(name + " ↓", c + ":-1"),
        );
      });
      const sortLabel = make("label", "Ordenar");
      sortLabel.append(mobileSort);
      layoutBody.prepend(presentLabel, sortLabel, densityLabel);
      const reset = button("Limpiar filtros", () => form.reset());
      reset.className = "explorer-reset";
      const chips = make("div");
      chips.className = "explorer-filter-chips";
      chips.setAttribute("aria-label", "Filtros activos");
      const batch = make("div");
      batch.className = "explorer-batch";
      batch.append(selectedCount, clear);
      const selectionTools = make("details"),
        selectionBody = make("div");
      selectionTools.className = "control-menu";
      selectionBody.className = "control-panel";
      selectionTools.append(make("summary", "Exportar"), selectionBody);
      selectionBody.append(selectionLabel, csv);
      if (!model) advanced.append(panel);
      advanced.remove();
      tools.replaceChildren(
        ...(model ? [filters] : [advanced]),
        layout,
        ...(model ? [views] : []),
        selectionTools,
      );
      tools.setAttribute("role", "group");
      tools.setAttribute("aria-label", "Herramientas de tabla");
      form.append(tools);
      form.after(chips, batch);
      el.classList.add("explorer-ready");
      el.dataset.presentation = "auto";
      const box = el.querySelector(".tabla-caja");
      const scrollHint = make("p", "Desliza la tabla para ver más columnas →");
      scrollHint.className = "explorer-scroll-hint";
      box.before(scrollHint);
      const overview = make("div");
      overview.className = "explorer-overview";
      status.before(overview);
      overview.append(status);
      const switcher = make("div");
      switcher.className = "explorer-presentation";
      switcher.setAttribute("aria-label", "Vista de registros");
      switcher.setAttribute("role", "group");
      const layoutButtons = ["table", "list", "cards", "board"].map((value) => {
        const b = button({table:"Tabla",list:"Lista",cards:"Fichas",board:"Tablero"}[value], () => {
          presentation.value = value;
          setPresentation();
          update();
        });
        b.dataset.layout = value;
        switcher.append(b);
        return b;
      });
      overview.append(switcher);
      const media = window.matchMedia?.("(max-width: 640px)");
      function setPresentation() {
        if(presentation.value==="board" && form.elements.grupo && form.elements.grupo.value===""){
          const choices=[...form.elements.grupo.options].filter(o=>o.value!=="" && types[Number(o.value)]!=="numero");
          const preferred=choices.find(o=>/estado|status|equipo|team|categor/i.test(o.textContent))||choices[0];
          if(preferred)form.elements.grupo.value=preferred.value;
        }
        el.dataset.presentation = presentation.value;
        el.dataset.layout =
          presentation.value === "auto"
            ? media?.matches
              ? "cards"
              : "table"
            : presentation.value;
        scrollHint.textContent=el.dataset.layout==="board"?"Desliza para ver más grupos →":"Desliza la tabla para ver más columnas →";
        originalTabStops.forEach(([node, previous]) => {
          if (["cards","list"].includes(el.dataset.layout)) node.tabIndex = -1;
          else if (previous === null) node.removeAttribute("tabindex");
          else node.setAttribute("tabindex", previous);
        });
        layoutButtons.forEach((b) =>
          b.setAttribute(
            "aria-pressed",
            String(b.dataset.layout === el.dataset.layout),
          ),
        );
        positionColumns();
      }
      listen(presentation, "change", () => {setPresentation();update();});
      listen(window, "resize", positionColumns);
      if (media?.addEventListener) listen(media, "change", setPresentation);
      listen(mobileSort, "change", () => {
        sorts = mobileSort.value
          ? [
              {
                col: Number(mobileSort.value.split(":")[0]),
                dir: Number(mobileSort.value.split(":")[1]),
              },
            ]
          : [];
        resetPage();
      });
      // Explicit table roles retain navigation when the visual rows become cards.
      table.setAttribute("role", "table");
      table.tHead.setAttribute("role", "rowgroup");
      table.tHead.rows[0].setAttribute("role", "row");
      headers.forEach((h) => h.setAttribute("role", "columnheader"));
      rows.forEach((row, r) => {
        row.setAttribute("role", "row");
        [...row.cells].forEach((cell, c) => {
          cell.setAttribute(
            "role",
            cell.tagName === "TH" ? "rowheader" : "cell",
          );
          cell.dataset.label = names[c];
          cell.dataset.primary = String(c === 0);
          cell.dataset.valueType = types[c];
          cell.dataset.narrative = String(types[c] === "texto" && values[r][c].length >= 140 && /\s/.test(values[r][c]));
        });
      });
      // Facets expose distinct source values with counts, without guessing business semantics.
      if (model)
        names.forEach((name, c) => {
          const choices = [...new Set(values.map((row) => row[c]))];
          if (c === 0 || types[c] !== "texto" || choices.length > 12) return;
          const facet = make("fieldset"),
            legend = make("legend", name);
          facet.className = "explorer-facet";
          facet.append(legend);
          choices.forEach((value) => {
            const label = make("label"),
              check = make("input"),
              count = make(
                "small",
                String(values.filter((row) => row[c] === value).length),
              );
            check.type = "checkbox";
            check.dataset.facetColumn = String(c);
            check.dataset.facetValue = value;
            label.append(check, make("span", value || "Sin valor"), count);
            facet.append(label);
            listen(check, "change", () => {
              const rule = query.rules.find(
                (r) => r.column === String(c) && r.operator === "in" && r.facet,
              );
              const picked = new Set(rule?.value || []);
              check.checked ? picked.add(value) : picked.delete(value);
              query.rules = query.rules.filter((r) => r !== rule);
              if (picked.size)
                query.rules.push({
                  column: String(c),
                  operator: "in",
                  value: [...picked],
                  facet: true,
                });
              drawRules();
              resetPage();
            });
          });
          filterBody.prepend(facet);
        });
      filterBody.prepend(
        make("p", "Los conteos corresponden al registro completo."),
      );
      window.NotaControles?.init(form);
      function paintChips() {
        chips.replaceChildren();
        const add = (label, clear) => {
          const b = make("button", label + " ×");
          b.type = "button";
          b.setAttribute("aria-label", "Quitar filtro: " + label);
          b.addEventListener("click", clear, { signal: renderAbort.signal });
          chips.append(b);
        };
        if (searchInput?.value)
          add("Búsqueda: " + searchInput.value, () => {
            searchInput.value = "";
            resetPage();
          });
        if (form.elements.estado?.value)
          add(form.elements.estado.value, () => {
            form.elements.estado.value = "";
            resetPage();
          });
        query?.rules.forEach((rule, i) =>
          add(
            names[Number(rule.column)] +
              ": " +
              ({
                contains: "contiene ",
                gte: "≥ ",
                lte: "≤ ",
                empty: "sin valor",
                between: "entre ",
              }[rule.operator] || "") +
              (Array.isArray(rule.value)
                ? rule.value.join(", ")
                : rule.value || "") +
              (rule.operator === "between" ? " – " + rule.upper : ""),
            () => {
              query.rules.splice(i, 1);
              drawRules();
              resetPage();
            },
          ),
        );
        if (chips.children.length) chips.append(reset);
        chips.hidden = !chips.children.length;
        filterBody.querySelectorAll("[data-facet-column]").forEach((check) => {
          check.checked = !!query?.rules.some(
            (r) =>
              r.facet &&
              r.column === check.dataset.facetColumn &&
              r.value.includes(check.dataset.facetValue),
          );
        });
        filters.querySelector("summary").textContent =
          "Filtros" + (query?.rules.length ? " · " + query.rules.length : "");
      }
      function positionColumns() {
        let left = 0;
        columnOrder.forEach(c => {
          const h = headers[c];
          const fixed = pinned.has(c) && el.dataset.layout === "table";
          for (const cell of [h, ...cells.map(row => row[c])]) {
            cell.style.position = fixed ? "sticky" : "";
            cell.style.left = fixed ? left + "px" : "";
            cell.style.zIndex = fixed ? "2" : "";
            cell.style.background = fixed ? "var(--papel)" : "";
          }
          if (fixed && !h.hidden) left += h.getBoundingClientRect().width;
        });
      }
      const detail = make("dialog");
      detail.className = "explorador-detalle";

      detail.setAttribute("aria-label", "Detalle del registro");
      document.body.append(detail);
      rows.forEach((row, i) => {
        const inspect = button("↗", () => {
          detail.replaceChildren(
            make("h3", values[i][0]),
            button("Cerrar", () => detail.close()),
          );
          const dl = make("dl");
          names.forEach((name, c) =>
            dl.append(make("dt", name), make("dd", values[i][c])),
          );
          detail.append(dl);
          detail.showModal();
        });
        inspect.setAttribute("aria-label", "Ver detalle de " + values[i][0]);
        inspect.className = "explorador-inspeccionar";
        row.cells[0].append(inspect);
      });
      const boxes = rows.map((r, i) => {
        const c = make("input");
        c.type = "checkbox";
        c.className = "explorador-seleccion";
        c.setAttribute("aria-label", "Seleccionar " + values[i][0]);
        r.cells[0].prepend(c);
        listen(c, "change", () => {
          c.checked ? selected.add(i) : selected.delete(i);
          update();
        });
        return c;
      });
      const colValue = (i, c) =>
        raw[i][c] === ""
          ? null
          : types[c] === "numero"
            ? Number(raw[i][c])
            : types[c] === "fecha"
              ? Date.parse(raw[i][c])
              : values[i][c];
      function update() {
        if (destroyed) return;
        renderAbort.abort();
        renderAbort = new AbortController();
        parts.splice(0).forEach((p) => p.remove());
        initial.remove();
        rows.forEach((r) => (r.hidden = false));
        const words = normal(form.elements.buscar?.value || "")
            .trim()
            .split(/\s+/),
          state = form.elements.estado?.value || "",
          group = form.elements.grupo?.value || "",
          fc = field.value === "" ? null : Number(field.value),
          numeric = fc !== null && types[fc] !== "texto";
        min.hidden = max.hidden = !numeric;
        match.hidden = numeric;
        min.type = max.type =
          fc !== null && types[fc] === "fecha" ? "date" : "number";
        const stateCol = Number(el.dataset.columnaEstado ?? 2),
          groupCol = group === "" ? null : Number(group);
        visible = rows
          .map((r, i) => i)
          .filter(
            (i) =>
              (!state || values[i][stateCol] === state) &&
              words.every((w) => normal(values[i].join(" ")).includes(w)) &&
              (numeric
                ? (raw[i][fc] !== "" ||
                    (min.value === "" && max.value === "")) &&
                  (min.value === "" ||
                    colValue(i, fc) >=
                      (types[fc] === "fecha"
                        ? Date.parse(min.value)
                        : Number(min.value))) &&
                  (max.value === "" ||
                    colValue(i, fc) <=
                      (types[fc] === "fecha"
                        ? Date.parse(max.value)
                        : Number(max.value)))
                : normal(
                    fc === null ? values[i].join(" ") : values[i][fc],
                  ).includes(normal(match.value))),
          );
        if (model && query)
          visible = model.query(
            visible,
            {
              ...query,
              sort: sorts.map((s) => ({
                column: String(s.col),
                direction: s.dir === 1 ? "asc" : "desc",
              })),
            },
            (i) =>
              Object.fromEntries(
                values[i].map((v, c) => [
                  String(c),
                  raw[i][c] === ""
                    ? null
                    : types[c] === "numero"
                      ? Number(raw[i][c])
                      : types[c] === "fecha"
                        ? raw[i][c]
                        : v,
                ]),
              ),
          );
        if (!model)
          visible.sort((a, b) => {
            for (const s of sorts) {
              const av = colValue(a, s.col),
                bv = colValue(b, s.col),
                c =
                  types[s.col] === "texto"
                    ? av.localeCompare(bv, "es", {
                        numeric: true,
                        sensitivity: "base",
                      })
                    : av - bv;
              if (c) return s.dir * c;
            }
            return a - b;
          });
        const pages = Math.max(
          1,
          Math.ceil(visible.length / Number(size.value)),
        );
        page = Math.max(0, Math.min(page, pages - 1));
        pageRows = visible.slice(
          page * Number(size.value),
          (page + 1) * Number(size.value),
        );
        const hidden = new Set(
          [...form.querySelectorAll("[data-columna]:not(:checked)")].map((e) =>
            Number(e.dataset.columna),
          ),
        );
        // A record's primary identifier remains available for selection and comments.
        hidden.delete(0);
        const identityBox = form.querySelector('[data-columna="0"]');
        if (identityBox) {
          identityBox.checked = true;
          identityBox.disabled = true;
        }
        if (hidden.size >= headers.length) {
          hidden.delete(0);
          const box = form.querySelector('[data-columna="0"]');
          if (box) box.checked = true;
        }
        headers.forEach((h, c) => (h.hidden = hidden.has(c)));
        rows.forEach((r, i) => {
          cells[i].forEach((c, j) => (c.hidden = hidden.has(j)));
          r.setAttribute("aria-selected", String(selected.has(i)));
          boxes[i].checked = selected.has(i);
        });
        const groups = new Map();
        pageRows.forEach((i) => {
          const key = groupCol === null ? "" : (values[i][groupCol] ?? "");
          if (!groups.has(key)) groups.set(key, []);
          groups.get(key).push(i);
        });
        if (!visible.length) {
          const body = make("tbody"),
            tr = body.insertRow(),
            td = tr.insertCell();
          td.colSpan = headers.length - hidden.size;
          td.append(
            make("strong", "No encontramos registros"),
            make("p", "Prueba otra búsqueda o quita los filtros."),
            button("Ver todos los registros", () => form.reset()),
          );
          tr.className = "explorer-empty";
          table.append(body);
          parts.push(body);
        }
        for (const [name, items] of groups) {
          const body = make("tbody");
          body.setAttribute("role", "rowgroup");
          if (groupCol !== null) {
            const tr = body.insertRow(),
              th = make("th");
            th.scope = "rowgroup";
            th.colSpan = headers.length - hidden.size;
            th.className = "tabla-grupo";
            const b = make(
              "button",
              (collapsed.has(name) ? "▸ " : "▾ ") +
                name +
                " · " +
                items.length +
                " en esta página",
            );
            b.type = "button";
            b.addEventListener(
              "click",
              () => {
                collapsed.has(name)
                  ? collapsed.delete(name)
                  : collapsed.add(name);
                update();
              },
              { signal: renderAbort.signal },
            );
            b.setAttribute("aria-expanded", String(!collapsed.has(name)));
            th.append(b);
            tr.append(th);
          }
          items.forEach((i) => {
            rows[i].hidden = groupCol !== null && collapsed.has(name);
            body.append(rows[i]);
          });
          table.append(body);
          parts.push(body);
        }
        const totalCol = Number(el.dataset.columnaTotal ?? 3),
          hasTotal = types[totalCol] === "numero",
          total = hasTotal
            ? visible.reduce((n, i) => n + Number(raw[i][totalCol]), 0)
            : 0;
        status.textContent =
          visible.length +
          " de " +
          rows.length +
          " registros" +
          (hasTotal
            ? " · " +
              total.toLocaleString("es-CO") +
              " " +
              (el.dataset.unidad || "COP") +
              " en la vista filtrada."
            : ".") +
          (sorts.length > 1
            ? " Orden: " + sorts.map((s) => names[s.col]).join(" → ")
            : "");
        headers.forEach((h, c) => {
          const s = sorts.find((s) => s.col === c);
          h.setAttribute(
            "aria-sort",
            sorts[0]?.col === c
              ? sorts[0].dir === 1
                ? "ascending"
                : "descending"
              : "none",
          );
          const hint = h.querySelector("[data-indicador-orden]");
          if (hint) hint.textContent = s ? (s.dir === 1 ? "↑" : "↓") : "↕";
        });
        positionColumns();
        paintChips();
        const ui = window.BottifactUI;
        for(const [menu, icon] of [[filters,"filter"],[layout,"columns"],[views,"bookmark"],[selectionTools,"download"]]) ui?.decorate(menu.querySelector("summary"),icon);
        layoutButtons.forEach(b => ui?.decorate(b,({table:"table",list:"review",cards:"cards",board:"columns"}[b.dataset.layout])));
        ui?.decorate(prev,"back",true); ui?.decorate(next,"arrow",true);
        mobileSort.value = sorts[0] ? sorts[0].col + ":" + sorts[0].dir : "";
        batch.hidden = !selected.size;
        selectedCount.textContent =
          selected.size +
          " seleccionados · " +
          [...selected].filter((i) => !visible.includes(i)).length +
          " fuera del filtro";
        clear.disabled = !selected.size;
        csv.textContent = selected.size
          ? "Exportar selección (" + selected.size + ")"
          : "Exportar vista";
        window.BottifactUI?.decorate(csv, "download");
        selectAll.checked =
          !!pageRows.length && pageRows.every((i) => selected.has(i));
        selectAll.indeterminate =
          pageRows.some((i) => selected.has(i)) && !selectAll.checked;
        pageStatus.textContent = "Página " + (page + 1) + " de " + pages;
        prev.disabled = page === 0;
        next.disabled = page === pages - 1;
        const count = form.querySelector("[data-filtros-cuenta]");
        if (count) count.textContent = state ? "1 · " : "";
      }
      function exportCSV() {
        const indices = selected.size
          ? rows.map((_, i) => i).filter((i) => selected.has(i))
          : visible;
        const columns = columnOrder.filter(c => !headers[c].hidden);
        const safe = (v, numeric = false) =>
          '"' +
          (!numeric && /^[\s]*[=+@\-]/.test(v) ? "'" + v : v).replaceAll(
            '"',
            '""',
          ) +
          '"';
        return [
          columns.map((c) => safe(names[c])).join(","),
          ...indices.map((i) =>
            columns
              .map((c) =>
                safe(
                  types[c] === "numero"
                    ? raw[i][c] === ""
                      ? ""
                      : String(Number(raw[i][c]))
                    : values[i][c],
                  types[c] === "numero",
                ),
              )
              .join(","),
          ),
        ].join("\r\n");
      }
      function downloadCSV() {
        const url = URL.createObjectURL(
            new Blob(["\ufeff" + exportCSV()], {
              type: "text/csv;charset=utf-8",
            }),
          ),
          a = make("a");
        a.href = url;
        a.download = "tabla.csv";
        a.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      }
      const resetPage = () => {
        page = 0;
        collapsed.clear();
        update();
      };
      listen(form, "input", (e) => {
        if (
          e.target.matches(
            "[name=buscar],[name=estado],[name=grupo],[data-columna]",
          )
        )
          resetPage();
      });
      listen(form, "change", (e) => {
        if (e.target.matches("[name=estado],[name=grupo],[data-columna]"))
          resetPage();
      });
      listen(form, "submit", (e) => e.preventDefault());
      listen(form, "reset", () =>
        queueMicrotask(() => {
          if (destroyed) return;
          sorts = [{ col: 0, dir: 1 }];
          if (model) {
            query = model.empty();
            join.value = "and";
            drawRules();
          }
          field.value = match.value = min.value = max.value = "";
          resetPage();
        }),
      );
      for (const input of [field, match, min, max, size])
        listen(input, "input", resetPage);
      listen(field, "change", () => {
        match.value = min.value = max.value = "";
        resetPage();
      });
      listen(density, "change", () => (el.dataset.densidad = density.value));
      listen(selectAll, "change", () => {
        pageRows.forEach((i) =>
          selectAll.checked ? selected.add(i) : selected.delete(i),
        );
        update();
      });
      el.querySelectorAll("[data-orden-col]").forEach((b) =>
        listen(b, "click", (e) => {
          const c = Number(b.dataset.ordenCol),
            requested = Number(b.dataset.direccion) || 0,
            dir =
              b.parentElement === headers[c] && sorts[0]?.col === c
                ? -sorts[0].dir
                : requested;
          if (c < 0 || c >= headers.length) return;
          sorts =
            dir === 0
              ? []
              : e.shiftKey
                ? [...sorts.filter((s) => s.col !== c), { col: c, dir }]
                : [{ col: c, dir }];
          resetPage();
        }),
      );
      listen(window, "beforeprint", () => {
        parts.splice(0).forEach((p) => p.remove());
        headers.forEach((h) => (h.hidden = false));
        rows.forEach((r) => {
          r.hidden = false;
          [...r.cells].forEach((c) => (c.hidden = false));
          initial.append(r);
        });
        table.append(initial);
      });
      listen(window, "afterprint", update);
      const instance = {
        update,
        exportCSV,
        get selected() {
          return [...selected].map((i) => values[i]);
        },
        get visible() {
          return visible.map((i) => values[i]);
        },
        destroy() {
          destroyed = true;
          detail.remove();
          el.querySelectorAll(".explorador-inspeccionar").forEach((b) =>
            b.remove(),
          );
          abort.abort();
          renderAbort.abort();
          parts.forEach((p) => p.remove());
          boxes.forEach((b) => b.remove());
          rows.forEach((r, i) => {
            r.hidden = false;
            r.removeAttribute("aria-selected");
            cells[i].forEach((c, j) => {
              r.append(c); c.hidden = previous.hidden[i][j];
              originalCellStyles[i][j] === null ? c.removeAttribute("style") : c.setAttribute("style", originalCellStyles[i][j]);
            });
            initial.append(r);
          });
          headers.forEach((h, i) => {
            table.tHead.rows[0].append(h);
            originalHeaderStyles[i] === null ? h.removeAttribute("style") : h.setAttribute("style", originalHeaderStyles[i]);
            h.hidden = previous.headers[i];
            previous.sort[i] === null
              ? h.removeAttribute("aria-sort")
              : h.setAttribute("aria-sort", previous.sort[i]);
          });
          table.append(initial);
          scrollHint.textContent=el.dataset.layout==="board"?"Desliza para ver más grupos →":"Desliza la tabla para ver más columnas →";
        originalTabStops.forEach(([node, previous]) => {
            if (previous === null) node.removeAttribute("tabindex");
            else node.setAttribute("tabindex", previous);
          });
          const identityBox = form.querySelector('[data-columna="0"]');
          if (identityBox) identityBox.disabled = false;
          tools
            .querySelectorAll(".control-menu")
            .forEach((m) => window.NotaControles?.get(m)?.destroy());
          moved
            .reverse()
            .forEach(([node, parent, next]) =>
              parent.insertBefore(
                node,
                next?.parentNode === parent ? next : null,
              ),
            );
          wrappers.forEach(([node, hidden]) => (node.hidden = hidden));
          chips.remove();
          batch.remove();
          scrollHint.remove();
          overview.before(status);
          overview.remove();
          el.classList.remove("explorer-ready");
          delete el.dataset.layout;
          delete el.dataset.presentation;
          searchLabel?.classList.remove("explorer-search");
          legacyState?.classList.remove("explorer-legacy-state");
          tools.remove();
          footer.remove();
          delete el.dataset.densidad;
          status.textContent = previous.status;
          instances.delete(el);
        },
      };
      instances.set(el, instance);
      applyColumnOrder();
      setPresentation();
      update();
      return instance;
    });
  }
  window.NotaExplorador = { init, get: (el) => instances.get(el) };
  init();
})();
