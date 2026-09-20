/* Portal-only actions. All content is rendered as text; authorization stays on the API. */
window.BottifactReaderWorkspace = {
  create({
    api,
    current,
    user,
    copy,
    share,
    manage,
    comment,
    refresh,
    related,
    search,
  }) {
    const el = (tag, text, cls) => {
      const n = document.createElement(tag);
      if (text) n.textContent = text;
      if (cls) n.className = cls;
      return n;
    };
    const button = (text, fn) => {
      const b = el("button", text);
      b.type = "button";
      b.onclick = async () => {
        b.disabled = true;
        try {
          await fn();
        } catch (e) {
          b.closest("dialog")
            ?.querySelector("[role=status]")
            ?.replaceChildren(document.createTextNode(e.message));
        } finally {
          b.disabled = false;
        }
      };
      return b;
    };
    function dialog(title) {
      const d = el("dialog", null, "workbench-dialog"),
        head = el("header"),
        body = el("div", null, "workbench-body"),
        status = el("p");
      status.setAttribute("role", "status");
      const trigger = document.activeElement;
      head.append(
        el("h2", title),
        button("Cerrar", () => d.close()),
      );
      d.append(head, body, status);
      document.body.append(d);
      d.addEventListener("close", () => {
        d.remove();
        trigger?.focus();
      });
      d.showModal();
      return { d, body, status };
    }
    const key = () =>
      "bottifact-reader:" + (user()?.id || "anonymous") + ":" + current().id;
    function settings() {
      let preferences = {};
      try {
        preferences = JSON.parse(localStorage.getItem(key()) || "{}");
      } catch {}
      return { manage: user()?.id === current().owner, preferences };
    }
    function preferences(value) {
      const next = {};
      if (!value || typeof value !== "object")
        throw Error("Preferencias inválidas.");
      for (const k of ["theme", "typography"])
        if (typeof value[k] === "string" && /^[a-z-]{1,40}$/.test(value[k]))
          next[k] = value[k];
      if (["light", "dark", "system"].includes(value.mode))
        next.mode = value.mode;
      if (typeof value.sound === "boolean") next.sound = value.sound;
      if (
        Number.isFinite(value.volume) &&
        value.volume >= 0 &&
        value.volume <= 1
      )
        next.volume = value.volume;
      if (Array.isArray(value.favorites))
        next.favorites = value.favorites
          .filter((s) => typeof s === "string" && /^[a-z-]{1,40}$/.test(s))
          .slice(0, 40);
      try {
        localStorage.setItem(key(), JSON.stringify(next));
      } catch {
        throw Error(
          "La preferencia se aplica en esta lectura, pero el navegador no permite guardarla.",
        );
      }
      return { ok: true };
    }
    async function bundle(aid = current()?.id) {
      if (!user()?.verified)
        throw Error("Entra con tu cuenta para preparar el contexto.");
      const { d, body, status } = dialog("Preparar contexto para IA"),
        hint = el(
          "p",
          "Selecciona qué vas a compartir. Las notas personales se incluyen sólo si las eliges.",
        ),
        notes = el("input"),
        label = el("label", "Incluir mis notas personales"),
        list = el("div", null, "bundle-threads"),
        preview = el("textarea"),
        actions = el("footer"),
        selectionCount = el("p", "0 hilos seleccionados", "bundle-count");
      d.classList.add("context-composer");
      notes.type = "checkbox";
      label.prepend(notes);
      preview.readOnly = true;
      preview.rows = 12;
      preview.setAttribute("aria-label", "Vista previa del contexto");
      let selected = new Set(),
        selectedEvidence = new Set(),
        items = [],
        bundleData = null,
        request = 0,
        selectionRevision = 0;
      const invalidate = () => {
        selectionRevision++;
        bundleData = null;
        preview.value = "";
        download.disabled = true;
        selectionCount.textContent = selected.size + (selected.size === 1 ? " hilo seleccionado" : " hilos seleccionados");
      };
      async function load() {
        const n = ++request;
        selected.clear();
        copyButton.disabled = true;
        invalidate();
        list.replaceChildren(el("p", "Cargando revisión…"));
        const q = new URLSearchParams({
          kind: notes.checked ? "all" : "comment",
        });
        if (aid) q.set("artifact", aid);
        const result = await api("/api/review/export?" + q);
        if (n !== request || !d.isConnected) return;
        items = result.items;
        selected = new Set(
          items
            .filter((i) => !i.thread.resolved && i.thread.entry_type !== "note")
            .map((i) => i.thread.thread),
        );
        invalidate();
        copyButton.disabled = false;
        render();
      }
      function render() {
        list.replaceChildren();
        for (const item of items) {
          const row = el("label", null, "bundle-thread"),
            check = el("input"),
            text = el("span");
          check.type = "checkbox";
          check.checked = selected.has(item.thread.thread);
          check.onchange = () => {
            check.checked
              ? selected.add(item.thread.thread)
              : selected.delete(item.thread.thread);
            invalidate();
          };
          text.append(
            el("strong", item.title),
            el(
              "small",
              (item.thread.entry_type === "note"
                ? "Nota personal"
                : "Comentario") +
                " · " +
                item.thread.author,
            ),
            el("p", item.thread.text),
            el("blockquote", item.thread.anchor.quote),
          );
          row.append(check, text);
          list.append(row);
        }
        if (!items.length)
          list.append(
            el(
              "p",
              "No hay hilos en esta selección. Puedes preparar el contexto del documento sin comentarios.",
            ),
          );
      }
      async function buildContext() {
        const revision = selectionRevision;
        const result = await api("/api/review/bundle", {
          method: "POST",
          body: JSON.stringify({
            artifact: aid || null,
            threads: [...selected],
            include_notes: notes.checked,
            evidence: [...selectedEvidence],
            version:
              aid === current()?.id
                ? document.querySelector("#version")?.value
                : undefined,
          }),
        });
        if (revision !== selectionRevision || !d.isConnected || !d.open)
          throw Error("La selección cambió. Revisa los hilos y vuelve a copiar.");
        bundleData = result;
        preview.value = bundleData.text;
        copyButton.disabled = download.disabled = false;
        status.textContent =
          bundleData.count +
          " hilos incluidos. Revisa el texto antes de copiar.";
      }
      const build = button("Revisar prompt", async () => {
        await buildContext();
        disclosure.open = true;
      });
      const copyButton = button("Copiar para IA", async () => {
          if (!bundleData) await buildContext();
          if (bundleData) {
            await copy(bundleData.text);
            status.textContent =
              "Contexto copiado. No se envió a ningún agente.";
          }
        }),
        download = button("Descargar contexto", () => {
          if (!bundleData) return;
          const url = URL.createObjectURL(
              new Blob([JSON.stringify(bundleData, null, 2)], {
                type: "application/json",
              }),
            ),
            a = el("a");
          a.href = url;
          a.download = "bottifact-context.json";
          a.click();
          setTimeout(() => URL.revokeObjectURL(url), 1000);
        });
      download.disabled = true;
      copyButton.classList.add("primary");
      window.BottifactUI?.decorate(copyButton, "copy");
      window.BottifactUI?.decorate(download, "download");
      const disclosure = el("details", null, "bundle-preview");
      disclosure.append(
        el("summary", "Contenido del prompt"),
        preview,
        download,
      );
      const selection = el("div", null, "bundle-selection");
      selection.append(
        selectionCount,
        button("Pendientes", () => {
          selected = new Set(
            items
              .filter(
                (i) => !i.thread.resolved && i.thread.entry_type !== "note",
              )
              .map((i) => i.thread.thread),
          );
          invalidate();
          render();
        }),
        button("Limpiar", () => {
          selected.clear();
          invalidate();
          render();
        }),
      );
      actions.append(build, copyButton);
      body.append(hint, label, selection, list, disclosure, actions);
      notes.onchange = () =>
        load().catch((e) => (status.textContent = e.message));
      await load();
      if (aid) {
        const links = await api("/api/context/links?artifact=" + aid);
        if (links.items.length) {
          const section = el("section");
          section.append(el("h3", "Referencias para incluir"));
          for (const link of links.items.filter(
            (l) => l.state === "confirmed",
          )) {
            const label = el(
                "label",
                link.kind +
                  " · " +
                  link.source_title +
                  " → " +
                  link.target_title,
              ),
              check = el("input");
            check.type = "checkbox";
            check.onchange = () => {
              check.checked
                ? selectedEvidence.add(link.id)
                : selectedEvidence.delete(link.id);
              invalidate();
            };
            label.prepend(check);
            section.append(label);
          }
          body.insertBefore(section, actions);
        }
      }
    }
    async function fallbackReview() {
      const { body, status } = dialog("Comentarios y notas");
      const data = await refresh();
      const threads = new Map();
      for (const e of data.snapshot.events) {
        if (e.kind === "create" && !threads.has(e.thread))
          threads.set(e.thread, { ...e, replies: [] });
        const t = threads.get(e.thread);
        if (!t) continue;
        if (e.kind === "edit") t.text = e.text;
        if (e.kind === "reply") t.replies.push(e);
        if (e.kind === "resolve") t.resolved = e.resolved;
        if (e.kind === "delete") t.deleted = true;
      }
      for (const t of threads.values()) {
        if (t.deleted) continue;
        const row = el("article");
        row.append(
          el(
            "small",
            (t.entry_type === "note" ? "Nota personal" : "Comentario") +
              " · " +
              t.author,
          ),
          el("p", t.text),
          el("blockquote", t.anchor.quote),
        );
        for (const r of t.replies)
          row.append(el("p", r.author + ": " + r.text));
        body.append(row);
      }
      if (!body.children.length)
        body.append(el("p", "Todavía no hay comentarios visibles."));
      if (data.permissions.comment)
        body.append(
          button("Añadir comentario", () => {
            body.closest("dialog").close();
            comment("comment");
          }),
        );
      if (data.verified)
        body.append(
          button("Añadir nota personal", () => {
            body.closest("dialog").close();
            comment("note");
          }),
        );
      status.textContent = "";
    }
    async function handle(op, data) {
      if (op === "controls-ready") {
        document.querySelector("#reader-dock").hidden = true;
        return { ok: true };
      }
      if (op === "preferences") return preferences(data);
      if (op !== "action") throw Error("Acción desconocida.");
      switch (data?.name) {
        case "share":
          if (current().permissions.manage) {
            await share(current().id);
          } else {
            const { body, status } = dialog("Compartir enlace");
            body.append(
              el(
                "p",
                "Copiar este enlace conserva los permisos actuales. La otra persona necesitará el acceso correspondiente.",
              ),
              button("Copiar enlace", async () => {
                await copy(location.origin + "/a/" + current().id);
                status.textContent = "Enlace copiado.";
              }),
            );
          }
          break;
        case "manage":
          if (user()?.id !== current().owner)
            throw Error("Sólo el creador puede gestionar este artefacto.");
          manage();
          break;
        case "bundle":
          await bundle();
          break;
        case "related":
          await related();
          break;
        case "search":
          await search();
          break;
        case "review":
          await fallbackReview();
          break;
        case "comment":
        case "note":
          comment(data.name);
          break;
        default:
          throw Error("Acción no disponible.");
      }
      return { ok: true };
    }
    return { handle, settings, bundle };
  },
};
