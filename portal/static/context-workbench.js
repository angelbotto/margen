/* Explicit context tools: personal by default, permission-checked on every API request. */
window.BottifactContextWorkbench = {
  create({ api, user, current, peek, load, params, applyParams, bundle }) {
    const el = (tag, text, cls) => {
      const e = document.createElement(tag);
      if (text !== undefined) e.textContent = text;
      if (cls) e.className = cls;
      return e;
    };
    const button = (text, fn) => {
      const b = el("button", text);
      b.type = "button";
      const icons = {
        Cerrar: "close",
        Guardar: "check",
        "Guardar entidad": "check",
        "Guardar mesa": "check",
        "Añadir nota": "note",
        "Crear entidad": "plus",
        "Nueva mesa de trabajo": "plus",
        "Nuevo tablero": "plus",
        "Referencias y conexiones": "graph",
        "Preparar contexto": "copy",
        "Conectar otro artefacto": "plus",
        "Confirmar conexión": "check",
        "Añadir condición": "plus",
        "Aplicar al conjunto completo": "check",
      };
      if (icons[text])
        window.BottifactUI?.decorate(b, icons[text], text === "Cerrar");
      b.onclick = async () => {
        b.disabled = true;
        try {
          await fn();
        } catch (e) {
          const status = b.closest("dialog")?.querySelector("[role=status]");
          if (status) status.textContent = e.message;
        } finally {
          b.disabled = false;
        }
      };
      return b;
    };
    function dialog(title) {
      const d = el("dialog", undefined, "workbench-dialog"),
        head = el("header"),
        body = el("div", undefined, "workbench-body"),
        status = el("p"),
        trigger = document.activeElement;
      status.setAttribute("role", "status");
      head.append(
        el("h2", title),
        button("Cerrar", () => d.close()),
      );
      d.append(head, body, status);
      document.body.append(d);
      d.onclose = () => {
        d.remove();
        trigger?.focus();
      };
      d.showModal();
      return { d, body, status };
    }
    const input = (label, value = "", type = "text") => {
      const wrap = el("label", label),
        field = el("input");
      field.value = value;
      field.type = type;
      wrap.append(field);
      return { wrap, field };
    };
    const select = (label, options) => {
      const wrap = el("label", label),
        field = el("select");
      for (const [v, t] of options) field.append(new Option(t, v));
      wrap.append(field);
      return { wrap, field };
    };
    const post = (url, body, method = "POST") =>
      api(url, { method, body: JSON.stringify(body) });
    async function inspect(a) {
      const { body } = dialog("Detalle del artefacto"),
        detail = await api("/api/artifacts/" + a.id);
      body.append(el("h3", detail.title), el("p", detail.space));
      const frame = el("iframe");
      frame.title = "Vista previa de " + detail.title;
      frame.setAttribute("sandbox", "");
      frame.src = "/api/artifacts/" + a.id + "/preview";
      frame.style =
        "width:100%;height:320px;border:1px solid var(--line);border-radius:8px";
      body.append(frame);
      const open = el("a", "Abrir artefacto");
      open.href = "/a/" + a.id;
      body.append(
        open,
        button("Referencias y conexiones", () => related(a.id)),
        button("Preparar contexto", () => bundle(a.id)),
      );
    }
    async function pickArtifact(root, onPick) {
      const { wrap, field } = input("Buscar artefacto"),
        list = el("div");
      field.type = "search";
      root.append(wrap, list);
      let timer,
        seq = 0;
      field.oninput = () => {
        clearTimeout(timer);
        const n = ++seq;
        timer = setTimeout(async () => {
          try {
            const r = await api(
              "/api/artifacts?view=all&limit=12&q=" +
                encodeURIComponent(field.value),
            );
            if (seq !== n || !list.isConnected) return;
            list.replaceChildren();
            for (const a of r.artifacts.filter((a) => !a.external))
              list.append(button(a.title + " · " + a.space, () => onPick(a)));
            if (!r.artifacts.length) list.append(el("p", "Sin coincidencias."));
          } catch (e) {
            if (seq === n) list.textContent = e.message;
          }
        }, 180);
      };
      field.oninput();
      return field;
    }
    async function search() {
      const { d, body } = dialog("Buscar y actuar · ⌘/Ctrl K");
      const actions = el("div", undefined, "context-actions");
      actions.append(
        button("Empresas, proyectos y temas", () => {
          d.close();
          entities();
        }),
        button("Mesas de trabajo", () => {
          d.close();
          views();
        }),
        button("Sesiones de origen", () => {
          d.close();
          sessions();
        }),
        button("Preparar contexto para IA", () => {
          d.close();
          bundle(current()?.id || null);
        }),
      );
      body.append(actions);
      const field = await pickArtifact(body, (a) => {
        d.close();
        peek(a);
      });
      const found = el("section");
      body.append(found);
      const records = (await api("/api/context/entities")).items;
      const norm = (v) =>
        v
          .normalize("NFD")
          .replace(/[\u0300-\u036f]/g, "")
          .toLowerCase();
      function findEntities() {
        found.replaceChildren();
        const q = norm(field.value.trim());
        if (!q) return;
        for (const entity of records
          .filter((e) => norm([e.name, ...e.aliases].join(" ")).includes(q))
          .slice(0, 12))
          found.append(
            button(entity.kind + " · " + entity.name, () => {
              d.close();
              entities(entity.id);
            }),
          );
      }
      field.addEventListener("input", findEntities);
      field.focus();
    }
    async function entities(focusId) {
      const { body, status } = dialog("Empresas, proyectos y temas"),
        list = el("div"),
        actions = el("div");
      actions.append(button("Crear entidad", () => editEntity()));
      body.append(
        el(
          "p",
          "Tus entidades organizan conocimiento sin fusionar nombres automáticamente. Los alias no otorgan acceso a documentos.",
        ),
        actions,
        list,
      );
      const r = await api("/api/context/entities");
      for (const entity of r.items) {
        const row = el("section", undefined, "context-card");
        row.append(
          el("h3", entity.name),
          el("p", entity.kind + " · " + entity.aliases.join(" / ")),
          button("Editar propiedades y documentos", () => editEntity(entity)),
        );
        const dl = el("dl");
        for (const [k, v] of Object.entries(entity.properties))
          dl.append(el("dt", k), el("dd", v));
        row.append(dl);
        for (const a of entity.artifacts)
          row.append(button(a.title, () => inspect(a)));
        list.append(row);
        if (entity.id === focusId) {
          row.tabIndex = -1;
          row.focus();
          row.scrollIntoView({ block: "center" });
        }
      }
      status.textContent = r.items.length + " entidades personales.";
    }
    async function editEntity(entity) {
      const { d, body, status } = dialog(
          entity ? "Editar entidad" : "Nueva entidad",
        ),
        name = input("Nombre", entity?.name),
        kind = select("Tipo", [
          ["company", "Empresa"],
          ["project", "Proyecto"],
          ["topic", "Tema"],
        ]),
        aliases = input(
          "Alias, separados por coma",
          entity?.aliases.join(", "),
        ),
        props = input(
          "Propiedades JSON",
          JSON.stringify(entity?.properties || {}),
        ),
        members = new Map((entity?.artifacts || []).map((a) => [a.id, a])),
        selected = el("div");
      kind.field.value = entity?.kind || "company";
      body.append(name.wrap, kind.wrap, aliases.wrap, props.wrap, selected);
      function render() {
        selected.replaceChildren();
        for (const a of members.values())
          selected.append(
            button("Quitar · " + a.title, () => {
              members.delete(a.id);
              render();
            }),
          );
      }
      render();
      await pickArtifact(body, (a) => {
        if (a.owner !== user()?.id) {
          status.textContent = "Sólo puedes asignar tus propios artefactos.";
          return;
        }
        members.set(a.id, a);
        render();
      });
      body.append(
        button("Guardar entidad", async () => {
          await post("/api/context/entities", {
            id: entity?.id,
            name: name.field.value,
            kind: kind.field.value,
            aliases: aliases.field.value
              .split(",")
              .map((s) => s.trim())
              .filter(Boolean),
            properties: JSON.parse(props.field.value),
            artifacts: [...members.keys()],
          });
          d.close();
          await load();
        }),
      );
    }
    async function related(aid = current()?.id) {
      if (!aid) return;
      const { body, status } = dialog("Referencias y conexiones"),
        a = await api("/api/artifacts/" + aid),
        r = await api("/api/context/links?artifact=" + aid);
      body.append(el("p", a.title));
      if (a.owner === user()?.id)
        body.append(button("Conectar otro artefacto", () => editLink(a)));
      for (const link of r.items) {
        const other = link.source === aid ? link.target : link.source,
          row = el("article", undefined, "context-card");
        row.append(
          el(
            "small",
            (link.source === aid ? "Saliente" : "Referencia entrante") +
              " · " +
              link.kind +
              " · " +
              link.state,
          ),
          button(
            link.source === aid ? link.target_title : link.source_title,
            () => inspect({ id: other }),
          ),
          el("blockquote", link.quote),
        );
        const source = el("a", "Abrir versión de la evidencia");
        source.href = link.url;
        row.append(
          source,
          el(
            "p",
            "Versión " + link.version + " · #" + (link.anchor || "documento"),
          ),
        );
        if (link.owner === user()?.id)
          row.append(
            button(
              link.state === "proposed"
                ? "Confirmar relación"
                : "Retirar relación",
              async () => {
                await post(
                  "/api/context/links/" + link.id,
                  {
                    state:
                      link.state === "proposed" ? "confirmed" : "dismissed",
                  },
                  "PATCH",
                );
                row.remove();
                status.textContent = "Relación actualizada.";
              },
            ),
          );
        body.append(row);
      }
      if (!r.items.length)
        body.append(
          el(
            "p",
            "Todavía no hay referencias explícitas. Compartir temas es una conexión distinta.",
          ),
        );
      if (a.owner === user()?.id) {
        const suggestions = await api(
          "/api/context/suggestions?artifact=" + aid,
        );
        if (suggestions.items.length)
          body.append(el("h3", "Menciones por revisar"));
        for (const s of suggestions.items) {
          const row = el("article", undefined, "context-card");
          row.append(
            el("strong", s.title),
            el("blockquote", s.evidence),
            el("p", s.reason),
            button("Revisar y conectar", () =>
              editLink(a, { id: s.target, title: s.title }, s.evidence),
            ),
            button("Descartar sugerencia", async () => {
              await post("/api/context/suggestions/dismiss", {
                source: aid,
                target: s.target,
              });
              row.remove();
            }),
          );
          body.append(row);
        }
      }
    }
    async function editLink(source, target = null, evidence = "") {
      const { d, body, status } = dialog("Conexión con evidencia"),
        chosen = el("p", target?.title || "Elige el destino"),
        kind = select("Relación", [
          ["cites", "Cita"],
          ["updates", "Actualiza"],
          ["contradicts", "Contradice"],
          ["depends_on", "Depende de"],
          ["resolves", "Resuelve"],
        ]),
        anchor = input("ID de sección (opcional)"),
        quote = input("Fragmento literal de la versión publicada", evidence);
      body.append(chosen, kind.wrap, anchor.wrap, quote.wrap);
      await pickArtifact(body, (a) => {
        target = a;
        chosen.textContent = a.title;
      });
      body.append(
        button("Confirmar conexión", async () => {
          if (!target) throw Error("Elige un destino.");
          await post("/api/context/links", {
            source: source.id,
            target: target.id,
            version: source.current_version,
            kind: kind.field.value,
            anchor: anchor.field.value,
            quote: quote.field.value,
            state: "confirmed",
          });
          status.textContent = "Conexión guardada.";
          d.close();
          await load();
        }),
      );
    }
    async function sessions() {
      const { body } = dialog("Sesiones y dispositivos"),
        r = await api("/api/context/sessions");
      body.append(
        el(
          "p",
          "Salidas registradas por tus agentes. No se importan conversaciones ni se reanuda una sesión automáticamente.",
        ),
      );
      for (const session of r.items) {
        const row = el("section", undefined, "context-card");
        row.append(
          el("h3", session.agent || "Agente no registrado"),
          el(
            "p",
            session.session +
              " · " +
              (session.device || "Dispositivo no registrado"),
          ),
        );
        for (const a of session.outputs) {
          const link = el("a", a.title + " · " + a.version.slice(0, 8));
          link.href = "/a/" + a.artifact + "?version=" + a.version;
          row.append(link);
        }
        body.append(row);
      }
      if (!r.items.length)
        body.append(
          el(
            "p",
            "Las próximas publicaciones deben registrar agente, sesión y dispositivo.",
          ),
        );
    }
    async function views() {
      const { body } = dialog("Mesas de trabajo y vistas"),
        r = await api("/api/context/views");
      body.append(
        el(
          "p",
          "Las mesas y tableros son privados. Puedes compartir una vista de filtros por correo; cada persona sólo verá los documentos que ya puede leer.",
        ),
        button("Nueva mesa de trabajo", () => editView()),
        button("Nuevo tablero", () =>
          editView({ kind: "board", body: { items: [] } }),
        ),
        button("Guardar filtros actuales", () => saveTable()),
      );
      for (const v of r.items) {
        const row = el("section", undefined, "context-card");
        row.append(
          el("h3", v.name),
          el("small", v.kind + " · " + v.body.items.length + " piezas"),
        );
        row.append(
          button("Abrir", () =>
            v.kind === "table" ? applyParams(v.body.params) : editView(v),
          ),
          button("Eliminar vista", async () => {
            await api("/api/context/views/" + v.id, { method: "DELETE" });
            row.remove();
          }),
        );
        if(v.kind==='table' && v.can_manage){row.append(button('Compartir filtros',()=>{const m=dialog('Compartir esta vista');const emails=input('Correos separados por coma',(v.grants||[]).join(', '));m.body.append(emails.wrap,el('p','Compartes el nombre y los filtros de búsqueda. No concede acceso a documentos ni comparte notas.'),button('Guardar acceso',async()=>{await post('/api/context/views/'+v.id+'/access',{emails:emails.field.value.split(',').map(x=>x.trim()).filter(Boolean)},'PUT');m.d.close();}));}));}
        if(!v.can_manage)row.querySelectorAll('button').forEach(b=>{if(b.textContent==='Eliminar vista')b.remove();});
        body.append(row);
      }
    }
    async function saveTable() {
      const { d, body } = dialog("Guardar vista de biblioteca"),
        name = input("Nombre");
      body.append(
        name.wrap,
        button("Guardar", async () => {
          await post(
            "/api/context/views/" + crypto.randomUUID(),
            {
              name: name.field.value,
              kind: "table",
              body: { params: Object.fromEntries(params()), items: [] },
            },
            "PUT",
          );
          d.close();
        }),
      );
    }
    async function editView(
      view = { kind: "working_set", body: { items: [] } },
    ) {
      const { body, status } = dialog(
          view.kind === "board" ? "Tablero privado" : "Mesa de trabajo",
        ),
        name = input("Nombre", view.name || ""),
        items = structuredClone(view.body.items),
        canvas = el(
          "div",
          undefined,
          view.kind === "board" ? "context-board" : "context-set",
        ),
        note = input("Nota propia para esta mesa"),
        key = view.id || crypto.randomUUID();
      body.append(
        name.wrap,
        el(
          "p",
          "Incluye documentos o notas propias. La posición visual no establece relaciones.",
        ),
        canvas,
        note.wrap,
        button("Añadir nota", () => {
          if (note.field.value.trim()) {
            items.push({
              text: note.field.value.trim(),
              x: 20 + items.length * 20,
              y: 20 + items.length * 20,
            });
            note.field.value = "";
            render();
          }
        }),
      );
      let edges = [];
      if (view.kind === "board")
        edges = (await api("/api/context/links")).items.filter(
          (e) => e.state === "confirmed",
        );
      function drawEdges() {
        canvas.querySelector("svg")?.remove();
        const ns = "http://www.w3.org/2000/svg",
          svg = document.createElementNS(ns, "svg");
        svg.setAttribute("width", "2100");
        svg.setAttribute("height", "1450");
        svg.style = "position:absolute;inset:0;pointer-events:none";
        svg.setAttribute("aria-label", "Conexiones verificadas entre tarjetas");
        for (const e of edges) {
          const a = items.find((i) => i.artifact === e.source),
            b = items.find((i) => i.artifact === e.target);
          if (!a || !b) continue;
          const line = document.createElementNS(ns, "line");
          for (const [k, v] of Object.entries({
            x1: a.x + 110,
            y1: a.y + 60,
            x2: b.x + 110,
            y2: b.y + 60,
            stroke: "var(--accent)",
            "stroke-width": 2,
          }))
            line.setAttribute(k, v);
          const text = document.createElementNS(ns, "text");
          text.setAttribute("x", (a.x + b.x) / 2 + 110);
          text.setAttribute("y", (a.y + b.y) / 2 + 60);
          text.setAttribute("fill", "var(--ink)");
          text.textContent = "→ " + e.kind;
          svg.append(line, text);
        }
        canvas.prepend(svg);
      }
      function render() {
        canvas.replaceChildren();
        if (view.kind === "board") drawEdges();
        items.forEach((item, i) => {
          const card = el("article", undefined, "context-card");
          if (view.kind === "board") {
            card.style.left = item.x + "px";
            card.style.top = item.y + "px";
            card.tabIndex = 0;
            card.setAttribute(
              "aria-label",
              "Mover " + (item.title || item.text) + " con flechas",
            );
            const handle = el("button", "⠿");
            handle.title = "Arrastrar tarjeta";
            handle.setAttribute("aria-label", "Arrastrar tarjeta");
            card.append(handle);
            let start;
            handle.onpointerdown = (e) => {
              start = { x: e.clientX, y: e.clientY, left: item.x, top: item.y };
              handle.setPointerCapture(e.pointerId);
            };
            handle.onpointermove = (e) => {
              if (!start) return;
              item.x = Math.max(
                0,
                Math.min(1800, start.left + e.clientX - start.x),
              );
              item.y = Math.max(
                0,
                Math.min(1200, start.top + e.clientY - start.y),
              );
              card.style.left = item.x + "px";
              card.style.top = item.y + "px";
              drawEdges();
            };
            handle.onpointerup = handle.onpointercancel = () => (start = null);
            card.onkeydown = (e) => {
              if (
                e.target !== card ||
                !["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(
                  e.key,
                )
              )
                return;
              e.preventDefault();
              item.x = Math.max(
                0,
                Math.min(
                  1800,
                  item.x +
                    (e.key === "ArrowRight"
                      ? 20
                      : e.key === "ArrowLeft"
                        ? -20
                        : 0),
                ),
              );
              item.y = Math.max(
                0,
                Math.min(
                  1200,
                  item.y +
                    (e.key === "ArrowDown"
                      ? 20
                      : e.key === "ArrowUp"
                        ? -20
                        : 0),
                ),
              );
              card.style.left = item.x + "px";
              card.style.top = item.y + "px";
              drawEdges();
            };
          }
          card.append(
            item.artifact
              ? button(item.title || "Abrir artefacto", () =>
                  inspect({ id: item.artifact }),
                )
              : el("p", item.text),
            button("Quitar", () => {
              items.splice(i, 1);
              render();
            }),
          );
          canvas.append(card);
        });
      }
      render();
      await pickArtifact(body, (a) => {
        if (!items.some((i) => i.artifact === a.id)) {
          items.push({
            artifact: a.id,
            title: a.title,
            text: "",
            x: 20 + items.length * 30,
            y: 20 + items.length * 30,
          });
          render();
        }
      });
      if (view.kind === "board")
        body.append(
          button("Conectar tarjetas con evidencia", () => {
            const { body: form } = dialog("Elegir tarjetas"),
              choices = items
                .filter((i) => i.artifact)
                .map((i) => [i.artifact, i.title || i.artifact]),
              from = select("Origen", choices),
              to = select("Destino", choices);
            form.append(
              from.wrap,
              to.wrap,
              button("Añadir evidencia", async () => {
                if (from.field.value === to.field.value)
                  throw Error("Elige dos documentos distintos.");
                const a = await api("/api/artifacts/" + from.field.value);
                await editLink(a, {
                  id: to.field.value,
                  title: to.field.selectedOptions[0].textContent,
                });
              }),
            );
          }),
        );
      body.append(
        button("Guardar mesa", async () => {
          await post(
            "/api/context/views/" + key,
            { kind: view.kind, name: name.field.value, body: { items } },
            "PUT",
          );
          status.textContent = "Guardado en tu cuenta.";
        }),
      );
    }
    async function filters() {
      const { body } = dialog("Filtros avanzados"),
        q = JSON.parse(params().get("filters") || '{"join":"and","rules":[]}'),
        join = select("Combinar", [
          ["and", "Todas las condiciones"],
          ["or", "Cualquier condición"],
        ]),
        list = el("div");
      join.field.value = q.join;
      body.append(join.wrap, list);
      const columns = [
        ["title", "Título"],
        ["space", "Empresa"],
        ["category", "Categoría"],
        ["visibility", "Acceso"],
        ["comments", "Comentarios pendientes"],
        ["updated", "Fecha UTC"],
        ["agent", "Agente"],
      ];
      function render() {
        list.replaceChildren();
        q.rules.forEach((rule, i) => {
          const row = el("div", undefined, "context-rule"),
            col = select("Campo", columns),
            op = select("Condición", [
              ["contains", "Contiene"],
              ["eq", "Igual a"],
              ["in", "Uno de"],
              ["gte", "Desde"],
              ["lte", "Hasta"],
              ["between", "Entre"],
              ["empty", "Sin valor"],
            ]),
            value = input(
              "Valor",
              Array.isArray(rule.value)
                ? rule.value.join(",")
                : rule.value || "",
            ),
            upper = input("Hasta", rule.upper || "");
          col.field.value = rule.column;
          op.field.value = rule.operator;
          value.field.type =
            rule.operator === "in"
              ? "text"
              : rule.column === "comments"
                ? "number"
                : rule.column === "updated"
                  ? "date"
                  : "text";
          upper.field.type = value.field.type;
          value.wrap.hidden = rule.operator === "empty";
          upper.wrap.hidden = rule.operator !== "between";
          col.field.onchange = () => {
            rule.column = col.field.value;
            rule.value = "";
            render();
          };
          op.field.onchange = () => {
            rule.operator = op.field.value;
            rule.value = "";
            render();
          };
          value.field.oninput = () =>
            (rule.value =
              rule.operator === "in"
                ? value.field.value.split(",").map((v) => v.trim())
                : value.field.value);
          upper.field.oninput = () => (rule.upper = upper.field.value);
          row.append(
            col.wrap,
            op.wrap,
            value.wrap,
            upper.wrap,
            button("Quitar", () => {
              q.rules.splice(i, 1);
              render();
            }),
          );
          list.append(row);
        });
      }
      render();
      body.append(
        button("Añadir condición", () => {
          if (q.rules.length < 12) {
            q.rules.push({ column: "title", operator: "contains", value: "" });
            render();
          }
        }),
        button("Aplicar al conjunto completo", () => {
          q.join = join.field.value;
          const p = Object.fromEntries(params());
          p.filters = JSON.stringify(q);
          applyParams(p);
          body.closest("dialog").close();
        }),
        button("Limpiar condiciones", () => {
          const p = Object.fromEntries(params());
          p.filters = "";
          applyParams(p);
          body.closest("dialog").close();
        }),
      );
    }
    addEventListener("keydown", (e) => {
      if (
        (e.metaKey || e.ctrlKey) &&
        e.key.toLowerCase() === "k" &&
        !document.querySelector("dialog[open]") &&
        !e.target.closest?.("input,textarea,select,[contenteditable=true]")
      ) {
        e.preventDefault();
        search().catch(() => {});
      }
    });
    return {
      search,
      entities,
      related,
      sessions,
      views,
      filters,
      saveTable,
      editView,
    };
  },
};
