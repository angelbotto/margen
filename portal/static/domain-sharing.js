(() => {
  "use strict";
  function normalize(value) {
    const domain = value.trim().toLowerCase().replace(/^@/, "");
    if (
      domain.length > 253 ||
      !/^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z](?:[a-z0-9-]{0,61}[a-z0-9])?$/.test(
        domain,
      )
    )
      throw Error(
        "Escribe un dominio como empresa.com, sin enlaces ni comodines.",
      );
    return domain;
  }
  function create(root, onChange) {
    let grants = [];
    const input = root.querySelector("[data-domain-input]"),
      role = root.querySelector("[data-domain-role]"),
      rows = root.querySelector("[data-domain-grants]"),
      error = root.querySelector("[data-domain-error]");
    function render() {
      rows.replaceChildren();
      for (const grant of grants) {
        const row = document.createElement("div");
        row.className = "grant domain-grant";
        const text = document.createElement("span");
        text.textContent = "@" + grant.domain;
        const select = document.createElement("select");
        select.setAttribute("aria-label", "Permiso de @" + grant.domain);
        for (const [value, label] of [
          ["viewer", "Ver"],
          ["commenter", "Comentar"],
        ]) {
          const option = document.createElement("option");
          option.value = value;
          option.textContent = label;
          select.append(option);
        }
        select.value = grant.role;
        select.onchange = () => {
          grant.role = select.value;
          onChange();
        };
        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "domain-remove";
        remove.setAttribute("aria-label", "Quitar acceso de @" + grant.domain);
        remove.title = "Quitar dominio";
        remove.append(window.MargenAccess.icon("close"));
        remove.onclick = () => {
          grants = grants.filter((g) => g !== grant);
          render();
          onChange();
          input.focus();
        };
        row.append(text, select, remove);
        rows.append(row);
      }
    }
    function add() {
      try {
        const domain = normalize(input.value);
        if (grants.some((g) => g.domain === domain))
          throw Error(
            "Este dominio ya está en la lista. Puedes cambiar su permiso aquí.",
          );
        if (grants.length >= 25)
          throw Error("Puedes añadir hasta 25 dominios.");
        grants.push({ domain, role: role.value });
        input.value = "";
        error.textContent = "";
        render();
        onChange();
        input.focus();
      } catch (e) {
        error.textContent = e.message;
        input.focus();
      }
    }
    root.querySelector("[data-add-domain]").onclick = add;
    input.onkeydown = (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        add();
      }
    };
    input.oninput = () => {
      error.textContent = "";
    };
    return {
      get: () => grants.map((g) => ({ ...g })),
      set: (value) => {
        grants = (value || []).map((g) => ({ ...g }));
        input.value = "";
        error.textContent = "";
        render();
      },
    };
  }
  window.MargenDomainSharing = { normalize, create };
})();
