(() => {
  "use strict";
  // Keep this allowlist aligned with portal.auth.target. Never accept an external return URL.
  function target(value) {
    if (
      typeof value !== "string" ||
      !value.startsWith("/") ||
      value.startsWith("//") ||
      value.includes("\\")
    )
      return "/";
    const match = value.match(
      /^(\/(?:a\/[a-f0-9]{32})?)(?:\?([^#]*))?(?:#.*)?$/,
    );
    if (!match) return "/";
    const fields = new URLSearchParams(match[2] || ""),
      query = new URLSearchParams();
    for (const key of ["thread", "version"]) {
      const val = fields.get(key);
      if (val && /^[a-zA-Z0-9_-]{1,120}$/.test(val)) query.set(key, val);
    }
    const view = fields.get("view");
    if (
      match[1] === "/" &&
      [
        "mine",
        "all",
        "shared",
        "inbox",
        "notifications",
        "admin",
        "archived",
        "public",
        "connections",
        "brain",
        "insights",
        "work",
      ].includes(view)
    )
      query.set("view", view);
    return match[1] + (query.size ? "?" + query : "");
  }
  function icon(name) {
    const paths = {
      close: '<path d="m6 6 12 12M6 18 18 6"/>',
      lock: '<rect x="5" y="10" width="14" height="11" rx="3"/><path d="M8 10V7a4 4 0 0 1 8 0v3m-4 5v2"/>',
      mail: '<rect x="3" y="5" width="18" height="14" rx="3"/><path d="m4 7 8 6 8-6"/>',
      arrow: '<path d="M5 12h14m-6-6 6 6-6 6"/>',
      retry: '<path d="M3 11a9 9 0 1 1 2 7M3 4v7h7"/>',
      cube: '<path d="m12 2 9 5v10l-9 5-9-5V7Z" stroke-dasharray=".5 2.4"/><path d="m3 7 9 5 9-5m-9 5v10"/>',
      google:
        '<path fill="currentColor" stroke="none" d="M21.6 12.2c0-.7-.1-1.4-.2-2.1H12v4h5.4a4.6 4.6 0 0 1-2 3v2.5h3.3c1.9-1.8 2.9-4.3 2.9-7.4ZM12 22c2.7 0 5-.9 6.7-2.4l-3.3-2.5c-.9.6-2 .9-3.4.9-2.6 0-4.8-1.7-5.6-4H3v2.6A10 10 0 0 0 12 22ZM6.4 14a6 6 0 0 1 0-4V7.4H3a10 10 0 0 0 0 9.2L6.4 14ZM12 6c1.5 0 2.8.5 3.8 1.5l2.9-2.8A9.6 9.6 0 0 0 12 2a10 10 0 0 0-9 5.4L6.4 10c.8-2.3 3-4 5.6-4Z"/>',
    };
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    for (const [key, value] of Object.entries({
      viewBox: "0 0 24 24",
      width: "20",
      height: "20",
      fill: "none",
      stroke: "currentColor",
      "stroke-width": "1.5",
      "stroke-linecap": "round",
      "stroke-linejoin": "round",
      "aria-hidden": "true",
    }))
      svg.setAttribute(key, value);
    svg.innerHTML = paths[name] || paths.cube;
    return svg;
  }
  function gate({ user, options = {}, status, next, changeAccount, retry }) {
    const el = (tag, text, cls) => {
      const node = document.createElement(tag);
      if (text) node.textContent = text;
      if (cls) node.className = cls;
      return node;
    };
    const page = el("section", null, "access-gate-page");
    const home = el("a", null, "access-home");
    home.href = "/";
    home.setAttribute("aria-label", "Margen · Inicio");
    home.append(icon("cube"));
    const card = el("div", null, "login-card access-gate-card"),
      symbol = el("div", null, "access-symbol");
    const denied = [401, 403, 404].includes(status);
    symbol.append(icon(denied ? "lock" : "retry"));
    const title = el(
      "h1",
      denied
        ? user?.verified
          ? "Esta cuenta no tiene acceso."
          : "Un espacio compartido contigo."
        : "No pudimos abrir el documento.",
    );
    title.id = "access-gate-title";
    page.setAttribute("aria-labelledby", title.id);
    card.append(
      symbol,
      el(
        "p",
        denied ? "Acceso al documento" : "Conexión interrumpida",
        "eyebrow",
      ),
      title,
      el(
        "p",
        denied
          ? user?.verified
            ? "Usa un correo invitado o del dominio autorizado. Si es esta cuenta, pide al creador que revise tu acceso y el enlace."
            : "Entra con una cuenta que tenga acceso al documento. Al entrar, volverás a este enlace."
          : "Comprueba tu conexión y vuelve a intentarlo en un momento.",
        "muted",
      ),
    );
    const actions = el("div", null, "access-actions"),
      message = el("p", null, "access-error");
    message.setAttribute("role", "status");
    function action(text, fn, cls) {
      const button = el("button", text, cls);
      button.type = "button";
      button.onclick = async () => {
        button.disabled = true;
        message.textContent = "";
        try {
          await fn();
        } catch {
          message.textContent = "No se pudo completar. Intenta de nuevo.";
        } finally {
          button.disabled = false;
        }
      };
      return button;
    }
    if (!denied) actions.append(action("Volver a intentar", retry, "primary"));
    else if (user?.verified) {
      const account = el("div", null, "access-account");
      account.append(icon("mail"), el("span", user.email));
      card.append(account);
      actions.append(
        action("Entrar con otra cuenta", changeAccount, "primary"),
      );
    } else {
      const destination = target(next);
      if (options.google) {
        const google = el("a", "Continuar con Google", "button google-button");
        google.prepend(icon("google"));
        google.href = "/auth/google?next=" + encodeURIComponent(destination);
        actions.append(google);
      }
      const email = el(
        "a",
        options.email ? "Continuar con correo" : "Ver opciones de acceso",
        "button" + (options.google ? "" : " primary"),
      );
      email.prepend(icon("mail"));
      email.href = "/login?next=" + encodeURIComponent(destination);
      actions.append(email);
    }
    const back = el(
      "a",
      user?.verified ? "Ir a mi biblioteca" : "Volver al inicio",
      "access-back",
    );
    back.href = "/";
    card.append(actions, message, back);
    page.append(
      home,
      card,
      el(
        "p",
        "Margen · Ideas y conversaciones, en el mismo lugar.",
        "access-gate-footer",
      ),
    );
    return page;
  }
  window.MargenAccess = { target, icon, gate };
})();
