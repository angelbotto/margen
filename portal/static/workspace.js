/* First-class creator surfaces. Data and permissions come from the account API. */
window.MargenWorkspace = {
  create({ api, peek, copy, creator, related, user }) {
    const el = (tag, text, cls) => {
      const n = document.createElement(tag);
      if (text !== undefined) n.textContent = text;
      if (cls) n.className = cls;
      return n;
    };
    const button = (text, fn, icon) => {
      const b = el("button", text);
      b.type = "button";
      if (icon) window.BottifactUI?.decorate(b, icon);
      b.onclick = fn;
      return b;
    };
    let epoch = 0,
      graph,
      project = "",
      period = 30;
    function destroy() {
      epoch++;
      graph?.destroy();
      graph = null;
      creator.unmount?.();
    }
    function link(text, url) {
      const a = el("a", text);
      a.href = url;
      return a;
    }
    function select(label, values, value, change) {
      const w = el("label", label),
        s = el("select");
      for (const [k, v] of values) s.add(new Option(v, k));
      s.value = value;
      s.onchange = () => change(s.value);
      w.append(s);
      return w;
    }
    async function render(root, view) {
      destroy();
      const ticket = epoch;
      root.className = "workspace-surface";
      root.replaceChildren();
      const status = el("p", "Cargando tu espacio…", "workspace-status");
      status.setAttribute("role", "status");
      root.append(status);
      try {
        if (view === "work") {
          await creator.mount(root);
          return;
        }
        const d = await api(
          "/api/creator/analytics/summary?days=" +
            period +
            "&project=" +
            encodeURIComponent(project),
        );
        if (ticket !== epoch || !root.isConnected) return;
        root.replaceChildren();
        const tools = el("div", undefined, "workspace-scope");
        tools.append(
          select(
            "Empresa o proyecto",
            [
              ["", "Todos tus espacios"],
              ...d.spaces.map((s) => [s.space, s.space + " · " + s.artifacts]),
            ],
            project,
            (v) => {
              project = v;
              render(root, view);
            },
          ),
        );
        root.append(tools);
        if (view === "insights") {
          tools.append(
            select(
              "Período",
              [
                [7, "7 días"],
                [30, "30 días"],
                [90, "90 días"],
                [365, "Un año"],
              ],
              String(period),
              (v) => {
                period = Number(v);
                render(root, view);
              },
            ),
          );
          const settings = el("details", undefined, "workspace-measurement");
          settings.append(
            el("summary", "Medición · " + (d.enabled ? "activa" : "pausada")),
          );
          const toggle = button(
            d.enabled ? "Pausar medición" : "Activar medición",
            async () => {
              toggle.disabled = true;
              try {
                await api("/api/creator/analytics", {
                  method: "PUT",
                  body: JSON.stringify({ enabled: !d.enabled }),
                });
                await render(root, view);
              } catch (e) {
                status.textContent = e.message;
                root.append(status);
                toggle.disabled = false;
              }
            },
            "settings",
          );
          settings.append(
            el(
              "p",
              "Sólo aperturas de versiones publicadas. Tus propias visitas, vistas previas y señales de no rastreo quedan excluidas.",
            ),
            toggle,
          );
          tools.append(settings);
          if (d.umami)
            tools.append(
              link(
                "Abrir Umami ↗",
                d.umami.origin + "/websites/" + d.umami.website,
              ),
            );
          const summary = el("dl", undefined, "workspace-summary");
          for (const [label, value] of [
            ["Aperturas registradas", d.total],
            ["Artefactos visitados", d.active_artifacts],
            ["Días con actividad", d.daily.filter((x) => x.views > 0).length],
          ]) {
            const item = el("div");
            item.append(
              el("dt", label),
              el("dd", Number(value).toLocaleString("es")),
            );
            summary.append(item);
          }
          root.append(summary);
          const chart = el("section", undefined, "visits-chart");
          chart.append(
            el("h2", "Lecturas a lo largo del tiempo"),
            el(
              "p",
              d.since +
                " → " +
                d.until +
                " · días UTC · aperturas, no personas únicas",
              "muted",
            ),
          );
          const values = new Map(d.daily.map((r) => [r.day, r.views])),
            days = [];
          for (let i = 0; i < period; i++) {
            const date = new Date(d.since + "T00:00:00Z");
            date.setUTCDate(date.getUTCDate() + i);
            const day = date.toISOString().slice(0, 10);
            days.push({ day, views: values.get(day) || 0 });
          }
          const ns = "http://www.w3.org/2000/svg",
            svg = document.createElementNS(ns, "svg");
          svg.setAttribute("viewBox", "0 0 900 210");
          svg.setAttribute("role", "img");
          svg.setAttribute(
            "aria-label",
            d.total +
              " aperturas registradas en " +
              period +
              " días. Datos completos disponibles debajo.",
          );
          const max = Math.max(1, ...days.map((x) => x.views));
          for (let i = 0; i < days.length; i++) {
            const r = document.createElementNS(ns, "rect");
            r.setAttribute("x", String((i * 900) / period + 1));
            r.setAttribute("y", String(200 - (days[i].views / max) * 180));
            r.setAttribute("width", String(Math.max(1, 900 / period - 2)));
            r.setAttribute("height", String((days[i].views / max) * 180));
            r.setAttribute("rx", "2");
            const title = document.createElementNS(ns, "title");
            title.textContent =
              days[i].day + ": " + days[i].views + " aperturas";
            r.append(title);
            svg.append(r);
          }
          if (d.total) chart.append(svg);
          if (!d.total)
            chart.append(
              el(
                "p",
                d.enabled
                  ? "Todavía no hay aperturas registradas en este período. Comparte un artefacto para empezar a medir."
                  : "Activa la medición para registrar próximas aperturas. El historial anterior no se reconstruye.",
                "workspace-empty",
              ),
            );
          const details = el("details");
          details.append(el("summary", "Consultar datos diarios"));
          const list = el("div", undefined, "visits-days");
          for (const r of days)
            list.append(el("span", r.day), el("strong", String(r.views)));
          details.append(list);
          chart.append(details);
          root.append(chart);
          const ranking = el("section", undefined, "visits-ranking");
          ranking.append(
            el("h2", "Qué están leyendo"),
            el(
              "p",
              "Hasta " +
                d.ranking_limit +
                " documentos, ordenados por aperturas. Los totales incluyen todos.",
              "muted",
            ),
          );
          for (const a of d.ranking) {
            const row = el("div", undefined, "visits-row"),
              title = el("div");
            title.append(
              link(a.title, "/a/" + a.id),
              el("small", a.space + " · última apertura " + a.last_day),
            );
            const bar = el("progress");
            bar.max = d.ranking[0].views;
            bar.value = a.views;
            bar.setAttribute("aria-label", a.views + " aperturas");
            row.append(title, bar, el("strong", a.views.toLocaleString("es")));
            ranking.append(row);
          }
          if (!d.ranking.length)
            ranking.append(
              el(
                "p",
                "Los documentos aparecerán aquí cuando reciban visitas.",
                "muted",
              ),
            );
          root.append(ranking);
          return;
        }
        const data = await api(
          "/api/creator/graph?project=" + encodeURIComponent(project),
        );
        if (ticket !== epoch) return;
        const header = el("div", undefined, "brain-intro");
        header.append(
          el(
            "p",
            "Explora empresas y temas; sigue las fuentes hasta sus decisiones y sesiones. Cada conexión explica su origen.",
          ),
        );
        const actions = el("div", undefined, "brain-lenses");
        actions.setAttribute("role", "group");
        actions.setAttribute("aria-label", "Enfoque del grafo");
        header.append(actions);
        root.append(header);
        const mount = el("section", undefined, "brain-map");
        root.append(mount);
        const key = "brain-" + user().id;
        const saved =
          (await api("/api/context/views")).items.find((v) => v.id === key)
            ?.body || {};
        if (ticket !== epoch) return;
        graph = window.BottifactKnowledge.graph(mount, data, peek, {
          positions: saved.positions,
          preferences: saved.preferences,
          related,
          save: (positions, preferences) =>
            api("/api/context/views/" + key, {
              method: "PUT",
              body: JSON.stringify({
                kind: "graph",
                name: "Mi grafo de conocimiento",
                body: { positions, preferences, items: [] },
              }),
            }),
        });
        for (const [label, lens] of [
          ["Todo", "all"],
          ["Empresas", "space"],
          ["Temas", "topic"],
          ["Decisiones", "decision"],
          ["Supuestos", "claim"],
          ["Sesiones", "session"],
        ]) {
          const b = button(label, () => {
            graph?.setLens(lens);
            syncLens();
          });
          b.dataset.lens = lens;
          actions.append(b);
        }
        function syncLens() {
          for (const b of actions.children)
            b.setAttribute(
              "aria-pressed",
              String(b.dataset.lens === graph?.getLens()),
            );
        }
        mount.addEventListener("margen:graph-change", syncLens);
        syncLens();
        tools.append(
          button(
            "Copiar continuidad",
            async () => {
              try {
                const b = await api(
                  "/api/creator/brief?project=" + encodeURIComponent(project),
                );
                await copy(b.text);
                status.textContent =
                  "Resumen con fuentes copiado. No se envió a ningún agente.";
              } catch (e) {
                status.textContent = e.message;
              }
              root.append(status);
            },
            "copy",
          ),
        );
      } catch (e) {
        if (ticket === epoch) {
          status.textContent = e.message;
          root.append(
            status,
            button("Volver a intentar", () => render(root, view), "refresh"),
          );
        }
      }
    }
    return { render, destroy };
  },
};
