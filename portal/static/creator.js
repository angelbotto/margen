/* Creator workspace: explicit decisions and assignments, never inferred authority. */
window.MargenCreator = {
  create({ api, copy, peek, bundle }) {
    const el = (tag, text, cls) => {
      const n = document.createElement(tag);
      if (text !== undefined) n.textContent = text;
      if (cls) n.className = cls;
      return n;
    };
    const post = (url, data) =>
      api(url, { method: "POST", body: JSON.stringify(data) });
    const labels = {
      prepared: "Preparado",
      queued: "En cola",
      received: "Recibido",
      working: "En curso",
      waiting: "Necesita información",
      proposed: "Propuesta lista",
      accepted: "Aceptado",
      cancelled: "Cancelado en el portal",
      stopped: "Proceso local detenido",
      failed: "Requiere atención",
    };
    let project = "",
      tab = "attention",
      data,
      dialog,
      body,
      message,
      graphView;
    function btn(text, fn, icon) {
      const b = el("button", text);
      b.type = "button";
      if (icon) window.BottifactUI?.decorate(b, icon);
      b.onclick = async () => {
        b.disabled = true;
        try {
          await fn();
        } catch (e) {
          message.textContent = e.message;
        } finally {
          b.disabled = false;
        }
      };
      return b;
    }
    function field(label, value = "", type = "text") {
      const wrap = el("label", label),
        input = el(type === "textarea" ? "textarea" : "input");
      if (type !== "textarea") input.type = type;
      input.value = value;
      wrap.append(input);
      return { wrap, input };
    }
    function select(label, options, value = "") {
      const wrap = el("label", label),
        input = el("select");
      for (const [v, t] of options) input.add(new Option(t, v));
      input.value = options.some(([v]) => v === value)
        ? value
        : options[0]?.[0] || "";
      wrap.append(input);
      return { wrap, input };
    }
    function link(title, url) {
      const a = el("a", title);
      a.href = url;
      return a;
    }
    function badge(text) {
      return el("span", text, "creator-badge");
    }
    function modal(title) {
      const d = el("dialog", undefined, "creator-form"),
        h = el("header"),
        content = el("div", undefined, "creator-form-body"),
        status = el("p");
      status.setAttribute("role", "status");
      h.append(
        el("h2", title),
        btn("Cerrar", () => d.close(), "close"),
      );
      d.append(h, content, status);
      document.body.append(d);
      d.onclose = () => d.remove();
      d.showModal();
      return { d, content, status };
    }
    function submit(m, label, fn) {
      m.content.append(
        btn(
          label,
          async () => {
            try {
              await fn();
              m.d.close();
              await refresh();
            } catch (e) {
              m.status.textContent = e.message;
            }
          },
          "check",
        ),
      );
    }
    function empty(text) {
      body.append(el("p", text, "creator-empty"));
    }
    async function refresh() {
      const target = dialog;
      const next = await api(
        "/api/creator?project=" + encodeURIComponent(project),
      );
      if (dialog === target && target?.isConnected) {
        data = next;
        render();
      }
    }
    let embedded = false;
    function unmount() {
      if (embedded) {
        graphView?.destroy();
        dialog = null;
        embedded = false;
      }
    }
    async function mount(root) {
      unmount();
      embedded = true;
      dialog = root;
      const requested = new URLSearchParams(location.search).get("section");
      if (
        [
          "attention",
          "brief",
          "evidence",
          "claims",
          "contradictions",
          "decisions",
          "outcomes",
          "jobs",
          "sessions",
          "rules",
          "connectors",
        ].includes(requested)
      )
        tab = requested;
      await refresh();
    }
    async function open() {
      embedded = false;
      if (dialog?.open) return;
      dialog = el("dialog", undefined, "creator-workspace");
      dialog.setAttribute("aria-label", "Mi trabajo");
      document.body.append(dialog);
      dialog.addEventListener("close", () => {
        graphView?.destroy();
        dialog.remove();
      });
      dialog.showModal();
      await refresh();
    }
    function render() {
      graphView?.destroy();
      graphView = null;
      dialog.replaceChildren();
      message = el("p", undefined, "creator-status");
      message.setAttribute("role", "status");
      const head = el("header", undefined, "creator-heading"),
        intro = el("div");
      intro.append(
        el("p", "MARGEN / ESPACIO DEL CREADOR", "creator-kicker"),
        el("h1", "De lo que sabes a lo que decides."),
        el("p", "Evidencia, conversaciones y próximos pasos con contexto."),
      );
      head.append(
        intro,
        btn("Cerrar", () => dialog.close(), "close"),
      );
      if (!embedded) dialog.append(head);
      const tools = el("div", undefined, "creator-projects"),
        scope = select(
          "Proyecto",
          [
            ["", "Todos los proyectos"],
            ...data.projects.map((p) => [p.name, p.name + " · " + p.artifacts]),
          ],
          project,
        );
      scope.input.onchange = async () => {
        project = scope.input.value;
        await refresh();
      };
      tools.append(
        scope.wrap,
        btn("Copiar resumen del proyecto", projectBrief, "copy"),
        btn("Nueva decisión", () => decisionForm(), "plus"),
        btn("Preparar encargo", () => jobForm(), "comment"),
      );
      dialog.append(tools);
      const stats = el("div", undefined, "creator-stats");
      for (const [n, label] of [
        [
          data.decisions.filter((d) => d.needs_review && d.state === "accepted")
            .length,
          "Decisiones por revisar",
        ],
        [
          data.jobs.filter((j) => j.status === "proposed").length,
          "Propuestas listas",
        ],
        [
          data.jobs.filter((j) =>
            ["queued", "received", "working"].includes(j.status),
          ).length,
          "Encargos activos",
        ],
      ]) {
        const cell = el("div");
        cell.append(el("strong", String(n)), el("span", label));
        stats.append(cell);
      }
      dialog.append(stats);
      const tabs = el("nav", undefined, "creator-tabs");
      tabs.setAttribute("aria-label", "Secciones de Mi trabajo");
      const sections = [
        [
          "Priorizar",
          [
            ["attention", "Atención"],
            ["brief", "Continuidad"],
          ],
        ],
        [
          "Comprender",
          [
            ["evidence", "Evidencia"],
            ["context", "Grafo"],
            ["claims", "Supuestos"],
            ["contradictions", "Contrastes"],
          ],
        ],
        [
          "Actuar",
          [
            ["decisions", "Decisiones"],
            ["outcomes", "Resultados"],
            ["jobs", "Encargos"],
            ["sessions", "Sesiones"],
          ],
        ],
        [
          "Administrar",
          [
            ["analytics", "Visitas"],
            ["rules", "Criterio personal"],
            ["connectors", "Agentes"],
          ],
        ],
      ];
      const mobile = el("label", "Sección", "creator-mobile-nav"),
        picker = el("select");
      for (const [group, groupItems] of sections) {
        const items = groupItems.filter(
          ([key]) => !embedded || !["context", "analytics"].includes(key),
        );
        const heading = el("p", group, "creator-nav-group");
        tabs.append(heading);
        const optionGroup = document.createElement("optgroup");
        optionGroup.label = group;
        picker.append(optionGroup);
        for (const [key, label] of items) {
          const b = btn(label, () => {
            tab = key;
            render();
          });
          b.setAttribute("aria-pressed", String(tab === key));
          tabs.append(b);
          optionGroup.append(new Option(label, key));
        }
      }
      picker.value = tab;
      picker.onchange = () => {
        tab = picker.value;
        render();
      };
      mobile.append(picker);
      dialog.append(mobile);
      body = el("section", undefined, "creator-body");
      const layout = el("div", undefined, "creator-layout");
      layout.append(tabs, body);
      dialog.append(layout, message);
      if (
        [
          "brief",
          "claims",
          "evidence",
          "contradictions",
          "sessions",
          "outcomes",
          "analytics",
        ].includes(tab)
      )
        window.MargenMemory.render({
          api,
          root: body,
          mode: tab,
          project,
          artifacts: data.artifacts,
          copy,
          decisionForm,
          refresh,
        }).catch((e) => (message.textContent = e.message));
      if (tab === "attention") attention();
      if (tab === "decisions") decisions();
      if (tab === "jobs") jobs();
      if (tab === "context")
        context().catch((e) => (message.textContent = e.message));
      if (tab === "rules") rules();
      if (tab === "connectors") connectors();
    }
    async function attention() {
      const target = body;
      target.append(el("h2", "Qué merece tu atención"));
      for (const d of data.decisions.filter(
        (d) => d.needs_review && d.state === "accepted",
      )) {
        const row = el("article", undefined, "creator-row");
        row.append(
          badge("Revisar evidencia"),
          el("h3", d.title),
          el(
            "p",
            d.evidence.some((e) => e.changed)
              ? "Cambió un documento que sustenta esta decisión."
              : "Llegó la fecha de revisión.",
          ),
          btn("Revisar decisión", () => decisionForm(d), "arrow"),
        );
        target.append(row);
      }
      try {
        const inbox = await api("/api/inbox");
        if (body !== target) return;
        const owned = new Set(data.artifacts.map((a) => a.id));
        const items = inbox.items.filter(
          (i) => owned.has(i.artifact) && !i.thread.resolved,
        );
        const filter = select("Conversación", [
          ["all", "Comentarios y mis notas"],
          ["comment", "Comentarios"],
          ["note", "Sólo mis notas"],
        ]);
        target.append(filter.wrap);
        const list = el("div");
        target.append(list);
        function show() {
          list.replaceChildren();
          for (const i of items.filter(
            (i) =>
              filter.input.value === "all" ||
              (i.thread.entry_type || "comment") === filter.input.value,
          )) {
            const row = el("article", undefined, "creator-row"),
              an = i.thread.anchor;
            row.append(
              badge(
                i.thread.entry_type === "note"
                  ? "Privado · sólo tú"
                  : i.thread.author,
              ),
              link(i.title, i.context.url),
              el("blockquote", an.quote || an.text || "Punto del artefacto"),
              el("p", i.thread.text),
              el(
                "small",
                "Ancla: " +
                  i.context.anchor_status +
                  " · Versión " +
                  i.thread.version.slice(0, 8),
              ),
            );
            const actions = el("div", undefined, "creator-actions");
            actions.append(
              btn(
                "Preparar ajuste",
                () => jobForm(i.artifact, [i.thread.thread]),
                "arrow",
              ),
              btn("Copiar contexto", () => bundle(i.artifact), "copy"),
            );
            row.append(actions);
            list.append(row);
          }
          if (!list.children.length)
            list.append(
              el(
                "p",
                "No hay hilos pendientes en esta selección.",
                "creator-empty",
              ),
            );
        }
        show();
        filter.input.onchange = show;
      } catch (e) {
        message.textContent = e.message;
      }
    }
    async function projectBrief() {
      const inbox = await api("/api/inbox"),
        ids = new Set(data.artifacts.map((a) => a.id));
      const lines = [
        "# Revisión · " + (project || "Todos los proyectos"),
        "Corte: " + new Date().toISOString(),
        "Alcance: artefactos propios visibles en Mi trabajo. Las notas privadas están excluidas.",
        "",
        "## Decisiones por revisar",
      ];
      for (const d of data.decisions.filter(
        (d) => d.needs_review && d.state === "accepted",
      )) {
        lines.push("- " + d.title + ": " + d.rationale);
        for (const e of d.evidence)
          lines.push(
            "  Evidencia" + (e.changed ? " modificada" : "") + ": " + e.url,
          );
      }
      lines.push("", "## Feedback pendiente");
      for (const i of inbox.items.filter(
        (i) =>
          ids.has(i.artifact) &&
          !i.thread.resolved &&
          i.thread.entry_type !== "note",
      ))
        lines.push(
          "- " + i.title + " · " + i.context.url,
          "  Hilo: " + i.thread.thread + " · Versión: " + i.thread.version,
          "  Contexto: " +
            (i.thread.anchor.quote || i.thread.anchor.text || ""),
          "  Comentario: " + i.thread.text,
        );
      lines.push("", "## Encargos");
      for (const j of data.jobs.filter(
        (j) => !["accepted", "cancelled"].includes(j.status),
      ))
        lines.push(
          "- " +
            j.title +
            " · " +
            labels[j.status] +
            " · " +
            [j.target.agent, j.target.device, j.target.session]
              .filter(Boolean)
              .join(" / "),
        );
      lines.push(
        "",
        "## Próxima revisión",
        "Prioriza los riesgos sustentados por estas fuentes, identifica información faltante y propone alternativas. No inventes cifras ni acuerdos. Cualquier cambio requiere una propuesta revisable.",
      );
      await copy(lines.join("\n"));
    }
    function decisions() {
      body.append(el("h2", "Un registro de lo que decidimos y por qué"));
      if (!data.decisions.length)
        empty(
          "Registra una decisión con alternativas, evidencia y una fecha para comprobar el resultado.",
        );
      for (const d of data.decisions) {
        const row = el("article", undefined, "creator-row");
        row.append(
          badge(
            {
              proposed: "Propuesta",
              accepted: "Aceptada",
              superseded: "Sustituida",
              rejected: "Descartada",
            }[d.state],
          ),
          el("h3", d.title),
          el("p", d.rationale),
          el(
            "small",
            d.project + (d.review_on ? " · Revisar " + d.review_on : ""),
          ),
        );
        for (const e of d.evidence)
          row.append(
            link((e.changed ? "Cambió · " : "Evidencia · ") + e.title, e.url),
          );
        row.append(btn("Abrir decisión", () => decisionForm(d), "arrow"));
        body.append(row);
      }
    }
    function decisionForm(d = {}) {
      const m = modal(d.id ? "Revisar decisión" : "Nueva decisión"),
        fields = {};
      for (const [key, label, type] of [
        ["title", "Decisión", "text"],
        ["rationale", "Por qué", "textarea"],
        ["alternatives", "Alternativas consideradas", "textarea"],
        ["expected", "Resultado esperado / cómo comprobarlo", "textarea"],
        ["uncertainty", "Qué falta saber", "textarea"],
        ["outcome", "Resultado observado", "textarea"],
        ["review_on", "Revisar el", "date"],
      ]) {
        fields[key] = field(label, d[key] || "", type);
        m.content.append(fields[key].wrap);
      }
      const p = field("Proyecto", d.project || project || "Personal"),
        state = select(
          "Estado",
          [
            ["proposed", "Propuesta"],
            ["accepted", "Aceptada"],
            ["superseded", "Sustituida"],
            ["rejected", "Descartada"],
          ],
          d.state || "proposed",
        );
      m.content.append(p.wrap, state.wrap);
      if (d.id)
        m.content.append(
          btn(
            "Ver historial",
            async () => {
              const h = await api(
                "/api/creator/decisions/" + d.id + "/history",
              );
              const details = el("details");
              details.open = true;
              details.append(el("summary", "Historial de decisiones"));
              for (const v of h.items) {
                const r = JSON.parse(v.record),
                  b = JSON.parse(r.body);
                details.append(
                  el(
                    "p",
                    new Date(v.at * 1000).toLocaleString() + " · " + r.state,
                  ),
                  el(
                    "blockquote",
                    b.rationale + "\nResultado: " + (b.outcome || "Pendiente"),
                  ),
                );
              }
              m.content.append(details);
            },
            "history",
          ),
        );
      const refs = [];
      for (const a of data.artifacts) {
        const f = field(a.title, "", "checkbox");
        f.input.checked = !!d.evidence?.some((e) => e.artifact === a.id);
        refs.push([a, f.input]);
        m.content.append(f.wrap);
      }
      const update = field(
        "Actualizar las referencias seleccionadas a su versión publicada actual",
        "",
        "checkbox",
      );
      m.content.append(update.wrap);
      submit(m, "Guardar decisión", () =>
        post("/api/creator/decisions", {
          id: d.id,
          project: p.input.value,
          state: state.input.value,
          ...Object.fromEntries(
            Object.entries(fields).map(([k, v]) => [k, v.input.value]),
          ),
          evidence: refs
            .filter(([, c]) => c.checked)
            .map(
              ([a]) =>
                (!update.input.checked &&
                  d.evidence?.find((e) => e.artifact === a.id)) || {
                  artifact: a.id,
                  version: a.current_version,
                },
            ),
        }),
      );
    }
    function jobs() {
      body.append(el("h2", "Del comentario a una propuesta verificable"));
      if (!data.jobs.length)
        empty(
          "Prepara un encargo con el feedback que quieres atender. Tú decides cuándo enviarlo.",
        );
      for (const j of data.jobs) {
        const row = el("article", undefined, "creator-row");
        row.append(
          badge(labels[j.status]),
          el("h3", j.title),
          el(
            "p",
            [j.target.agent, j.target.device, j.target.session]
              .filter(Boolean)
              .join(" · ") || "Destino por definir",
          ),
          btn("Ver contexto y entrega", () => jobDetail(j.id), "arrow"),
        );
        body.append(row);
      }
    }
    async function jobForm(aid = "", selected = []) {
      const m = modal("Preparar encargo"),
        artifact = select(
          "Artefacto",
          data.artifacts.map((a) => [a.id, a.title]),
          aid || data.artifacts[0]?.id || "",
        ),
        target = select("Conector", [
          ["", "Sólo preparar / copiar"],
          ...data.connectors
            .filter((c) => !c.revoked)
            .map((c) => [c.id, c.label + " · " + c.agent + " / " + c.device]),
        ]),
        session = field("Sesión de destino (opcional; vacía inicia una nueva)"),
        instructions = field("Qué quieres conseguir", "", "textarea"),
        notes = field(
          "Incluir mis notas privadas seleccionadas",
          "",
          "checkbox",
        ),
        threadsBox = el("div");
      m.content.append(
        artifact.wrap,
        target.wrap,
        session.wrap,
        instructions.wrap,
        notes.wrap,
        threadsBox,
      );
      let choices = [];
      async function feedback() {
        threadsBox.replaceChildren();
        choices = [];
        if (!artifact.input.value) return;
        const items = (
          await api(
            "/api/review/export?artifact=" +
              encodeURIComponent(artifact.input.value) +
              "&scope=open",
          )
        ).items;
        for (const i of items) {
          const f = field(
            (i.thread.entry_type === "note" ? "Privado · " : "") +
              i.thread.text,
            "",
            "checkbox",
          );
          f.input.checked = selected.includes(i.thread.thread);
          choices.push([i, f.input]);
          threadsBox.append(f.wrap);
        }
      }
      artifact.input.onchange = () =>
        feedback().catch((e) => (m.status.textContent = e.message));
      await feedback();
      submit(m, "Preparar para revisar", () =>
        post("/api/creator/jobs", {
          artifact: artifact.input.value,
          threads: choices
            .filter(([, f]) => f.checked)
            .map(([i]) => i.thread.thread),
          include_notes: notes.input.checked,
          instructions: instructions.input.value,
          target: {
            connector: target.input.value,
            session: session.input.value,
          },
        }),
      );
    }
    async function jobDetail(id) {
      const j = await api("/api/creator/jobs/" + id),
        m = modal(j.title);
      m.content.append(
        badge(labels[j.status]),
        el(
          "p",
          "Base: " +
            j.base_version +
            " · El encargo no publica ni resuelve comentarios.",
        ),
      );
      if (j.execution)
        m.content.append(
          el(
            "p",
            j.execution.stopped
              ? "El receptor confirmó la detención del proceso."
              : j.status === "cancelled"
                ? "Detención local pendiente de confirmación; el portal ya bloqueó resultados."
                : "Última señal: " +
                  new Date(j.execution.heartbeat * 1000).toLocaleString(),
          ),
        );
      const packet = el("details");
      packet.append(
        el("summary", "Revisar contexto exacto"),
        el("pre", JSON.stringify(j.packet, null, 2)),
      );
      m.content.append(
        packet,
        btn(
          "Copiar encargo",
          () => copy(JSON.stringify(j.packet, null, 2)),
          "copy",
        ),
      );
      for (const r of j.receipts)
        m.content.append(
          el(
            "p",
            (labels[r.state] || r.state) +
              " · " +
              new Date(r.at * 1000).toLocaleString() +
              " · " +
              r.detail,
          ),
        );
      if (j.result.version) {
        m.content.append(
          link(
            "Abrir propuesta",
            "/a/" + j.artifact + "?version=" + j.result.version,
          ),
        );
        const diff = await api("/api/creator/jobs/" + id + "/comparison");
        if (diff.current_changed)
          m.content.append(
            el(
              "p",
              "La versión publicada cambió desde que se preparó este encargo. Revisa antes de publicar.",
            ),
          );
        const visuals = el("details");
        visuals.append(el("summary", "Comparar las dos versiones visualmente"));
        visuals.addEventListener("toggle", () => {
          if (!visuals.open || visuals.querySelector("iframe")) return;
          const grid = el("div", undefined, "creator-compare");
          for (const [label, vid] of [
            ["Base", j.base_version],
            ["Propuesta", j.result.version],
          ]) {
            const cell = el("section");
            cell.append(
              el("h4", label),
              link(
                "Abrir " + label.toLowerCase(),
                "/a/" + j.artifact + "?version=" + vid,
              ),
            );
            const frame = el("iframe");
            frame.title = label + " del encargo";
            frame.setAttribute("sandbox", "allow-scripts allow-downloads");
            frame.loading = "lazy";
            frame.src =
              "/api/artifacts/" + j.artifact + "/render?version=" + vid;
            cell.append(frame);
            grid.append(cell);
          }
          visuals.append(grid);
        });
        m.content.append(visuals);
        for (const t of diff.threads)
          m.content.append(el("p", t.status + " · " + t.explanation));
        for (const c of diff.changes) {
          const item = el("div", undefined, "creator-diff");
          item.append(
            el("del", c.before.join("\n")),
            el("ins", c.after.join("\n")),
          );
          m.content.append(item);
        }
      }
      const allowed =
        {
          prepared: ["queued", "cancelled"],
          queued: ["cancelled"],
          received: ["cancelled"],
          working: ["cancelled"],
          waiting: ["queued", "cancelled"],
          failed: ["queued", "cancelled"],
          proposed: ["accepted", "queued", "cancelled"],
        }[j.status] || [];
      for (const state of allowed) {
        if (state === "queued" && !j.target.connector) continue;
        submit(
          m,
          {
            queued: "Enviar al conector",
            accepted: "Aceptar propuesta (sin publicar)",
            cancelled: "Cancelar encargo",
          }[state],
          () =>
            post("/api/creator/jobs/" + id + "/state", {
              status: state,
              revision: j.revision,
            }),
        );
      }
    }
    async function context() {
      const target = body;
      target.append(
        el("h2", "Qué sostiene el trabajo"),
        el(
          "p",
          "Las conexiones confirmadas conservan su evidencia; compartir un tema no demuestra dependencia.",
        ),
      );
      const network = await api(
        "/api/creator/graph?project=" + encodeURIComponent(project),
      );
      if (target !== body) return;
      const graph = el("div");
      target.append(graph);
      graphView = window.BottifactKnowledge.graph(graph, network, peek);
      target.append(el("small", network.scope));
      const sessions = await api("/api/context/sessions");
      if (target !== body) return;
      const ids = new Set(data.artifacts.map((a) => a.id));
      for (const s of sessions.items) {
        const outputs = s.outputs.filter((o) => ids.has(o.artifact));
        if (!outputs.length) continue;
        const row = el("article", undefined, "creator-row");
        row.append(
          badge(s.agent + " · " + s.device),
          el("h3", "Sesión " + s.session),
          el("p", outputs.length + " versiones registradas"),
        );
        for (const o of outputs)
          row.append(
            link(o.title, "/a/" + o.artifact + "?version=" + o.version),
          );
        target.append(row);
      }
      for (const a of data.artifacts) {
        const details = el("details", undefined, "creator-row");
        details.append(el("summary", a.title));
        details.addEventListener("toggle", async () => {
          if (!details.open || details.dataset.loaded) return;
          try {
            const r = await api("/api/context/links?artifact=" + a.id);
            const links = r.items || r.links || [];
            for (const l of links)
              details.append(
                el(
                  "p",
                  l.kind + " · " + l.source_title + " → " + l.target_title,
                ),
                el("blockquote", l.quote),
              );
            if (!links.length)
              details.append(el("p", "Sin conexiones confirmadas."));
            details.dataset.loaded = "1";
          } catch (e) {
            message.textContent = e.message;
          }
        });
        target.append(details);
      }
    }
    function rules() {
      body.append(
        el("h2", "Tu criterio, explícito y editable"),
        el(
          "p",
          "Sólo se aplican las reglas que apruebas. Puedes desactivarlas, borrarlas o exportarlas; no entrenan un modelo compartido.",
        ),
        btn("Añadir criterio", () => ruleForm(), "plus"),
        btn(
          "Exportar criterios",
          () => copy(JSON.stringify(data.rules, null, 2)),
          "copy",
        ),
      );
      for (const r of data.rules) {
        const row = el("article", undefined, "creator-row");
        row.append(
          badge(r.active ? "Aprobado" : "Inactivo"),
          el("p", r.rule),
          el("small", r.project || "Todos los proyectos"),
          btn("Editar", () => ruleForm(r), "note"),
          btn(
            "Eliminar",
            async () => {
              await api("/api/creator/rules/" + r.id, { method: "DELETE" });
              await refresh();
            },
            "close",
          ),
        );
        body.append(row);
      }
    }
    function ruleForm(r = {}) {
      const m = modal("Criterio de trabajo"),
        text = field("Regla que quieres aplicar", r.rule || "", "textarea"),
        p = field("Proyecto (vacío: todos)", r.project || project),
        active = field("Aplicar a nuevos encargos", "", "checkbox");
      active.input.checked = r.active !== 0;
      m.content.append(text.wrap, p.wrap, active.wrap);
      const refs = [];
      for (const a of data.artifacts) {
        const f = field("Fuente · " + a.title, "", "checkbox");
        f.input.checked = !!(r.source ? JSON.parse(r.source) : []).find(
          (e) => e.artifact === a.id,
        );
        refs.push([a, f.input]);
        m.content.append(f.wrap);
      }
      submit(m, "Aprobar criterio", () =>
        post("/api/creator/rules", {
          id: r.id,
          rule: text.input.value,
          project: p.input.value,
          active: active.input.checked,
          source: refs
            .filter(([, f]) => f.checked)
            .map(
              ([a]) =>
                (r.source ? JSON.parse(r.source) : []).find(
                  (e) => e.artifact === a.id,
                ) || { artifact: a.id, version: a.current_version },
            ),
        }),
      );
    }
    function connectors() {
      body.append(
        el("h2", "Tus agentes y dispositivos"),
        el(
          "p",
          "Cada conector sólo recibe los encargos que le envías. Su credencial no permite consultar toda tu biblioteca ni publicar versiones.",
        ),
        btn("Conectar dispositivo", connectorForm, "plus"),
      );
      for (const c of data.connectors) {
        const row = el("article", undefined, "creator-row");
        row.append(
          badge(
            c.revoked
              ? "Revocado"
              : c.seen
                ? "Última conexión " + new Date(c.seen * 1000).toLocaleString()
                : "Sin conectar",
          ),
          el("h3", c.label),
          el("p", c.agent + " · " + c.device),
        );
        if (!c.revoked)
          row.append(
            btn(
              "Revocar acceso",
              async () => {
                await api("/api/creator/connectors/" + c.id, {
                  method: "DELETE",
                });
                await refresh();
              },
              "close",
            ),
          );
        body.append(row);
      }
    }
    function connectorForm() {
      const m = modal("Conectar un agente"),
        label = field("Nombre del conector"),
        agent = select("Agente", [
          ["Codex", "Codex"],
          ["Claude", "Claude"],
          ["Hermes", "Hermes"],
        ]),
        device = field("Dispositivo");
      m.content.append(label.wrap, agent.wrap, device.wrap);
      m.content.append(
        btn(
          "Crear credencial",
          async () => {
            try {
              const r = await post("/api/creator/connectors", {
                label: label.input.value,
                agent: agent.input.value,
                device: device.input.value,
              });
              m.content.replaceChildren(
                el(
                  "p",
                  "Guarda esta credencial en el conector local. Se muestra una sola vez.",
                ),
                el("pre", JSON.stringify(r, null, 2)),
                btn(
                  "Copiar conexión",
                  () => copy(JSON.stringify(r, null, 2)),
                  "copy",
                ),
                el(
                  "p",
                  "Ejecuta: margen-agent connect. Después: margen-agent listen. El modo de recepción guarda contexto; la ejecución requiere --run y un directorio de trabajo elegido en ese equipo.",
                ),
              );
              await refresh();
            } catch (e) {
              m.status.textContent = e.message;
            }
          },
          "check",
        ),
      );
    }
    return { open, mount, unmount, jobForm };
  },
};
