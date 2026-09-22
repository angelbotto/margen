(() => {
  "use strict";
  const $ = (selector) => document.querySelector(selector);
  const params = new URLSearchParams(location.search);
  const next = window.MargenAccess.target(params.get("next"));
  const shared = next.startsWith("/a/");
  let challenge = "",
    deliveryTimer,
    resendTimer,
    epoch = 0,
    email = "",
    resendAt = 0,
    busy = false;
  try {
    const saved = localStorage.getItem("bottifact-portal-dark");
    document.documentElement.toggleAttribute(
      "data-dark",
      saved === "true" ||
        (saved === null && matchMedia("(prefers-color-scheme:dark)").matches),
    );
  } catch {}
  $("#appearance").onclick = () => {
    const dark = document.documentElement.toggleAttribute("data-dark");
    try {
      localStorage.setItem("bottifact-portal-dark", String(dark));
    } catch {}
  };
  $("#access-symbol").append(
    window.MargenAccess.icon(shared ? "lock" : "cube"),
  );
  function heading(verifying = false) {
    $("#access-kicker").textContent = verifying
      ? "Un paso más"
      : shared
        ? "Acceso al documento"
        : "Tu espacio en Margen";
    $("#login-title").textContent = verifying
      ? "Revisa tu correo."
      : shared
        ? "Continúa la conversación."
        : "Qué bueno verte.";
    $("#login-description").textContent = verifying
      ? "Escribe el código que te enviamos. Es válido durante 10 minutos."
      : shared
        ? "Entra con un correo invitado o del dominio autorizado. Volverás aquí después de entrar."
        : "Entra para continuar con tus ideas y las de tu equipo.";
    $("#access-fine").textContent = verifying
      ? "Si no encuentras el mensaje, revisa también spam."
      : shared
        ? "El creador elige qué personas y dominios pueden entrar."
        : "Sin contraseña. Tu biblioteca es privada.";
    $("#google").hidden = verifying || !authOptions.google;
    $("#divider").hidden =
      verifying || !authOptions.google || !authOptions.email;
  }
  let authOptions = {};
  heading();
  async function api(path, body) {
    const response = await fetch(path, {
      method: body ? "POST" : "GET",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });
    let data;
    try {
      data = await response.json();
    } catch {
      throw Error("No pudimos conectar. Intenta de nuevo.");
    }
    if (!response.ok)
      throw Error(
        typeof data.detail === "string"
          ? data.detail
          : "No pudimos completar el acceso. Intenta de nuevo.",
      );
    return data;
  }
  async function submit(form, work, loading) {
    const button = form.querySelector("[type=submit]");
    if (button.disabled || busy) return;
    busy = true;
    const label = [...button.childNodes];
    button.disabled = true;
    if (form.id === "verify-form") {
      $("#retry").disabled = true;
      $("#resend").disabled = true;
    }
    button.textContent = loading;
    form.setAttribute("aria-busy", "true");
    $("#message").textContent = "";
    try {
      await work();
    } catch (error) {
      $("#message").textContent = error.message;
    } finally {
      busy = false;
      button.disabled = false;
      if (form.id === "verify-form") {
        $("#retry").disabled = false;
        clearTimeout(resendTimer);
        cooldown();
      }
      button.replaceChildren(...label);
      form.removeAttribute("aria-busy");
    }
  }
  function stopDelivery() {
    epoch++;
    clearTimeout(deliveryTimer);
    clearTimeout(resendTimer);
  }
  function cooldown() {
    const seconds = Math.max(0, Math.ceil((resendAt - Date.now()) / 1000));
    $("#resend").disabled = seconds > 0 || busy;
    $("#resend").textContent = seconds
      ? `Reenviar en ${seconds} s`
      : "Reenviar código";
    if (seconds) resendTimer = setTimeout(cooldown, 1000);
  }
  async function requestCode() {
    const data = await api("/api/auth/email", {
      email: $("#email").value.trim(),
      next,
    });
    stopDelivery();
    email = $("#email").value.trim();
    challenge = data.challenge;
    resendAt = Date.now() + 60000;
    $("#code").value = "";
    $("#email-form").hidden = true;
    $("#verify-form").hidden = false;
    $("#sent-to").textContent = "Preparando el envío a " + email + ".";
    heading(true);
    $("#code").focus();
    cooldown();
    watchDelivery();
  }
  $("#email-form").onsubmit = (event) => {
    event.preventDefault();
    submit(event.target, requestCode, "Enviando código…");
  };
  $("#verify-form").onsubmit = (event) => {
    event.preventDefault();
    submit(
      event.target,
      async () => {
        const data = await api("/api/auth/email/verify", {
          challenge,
          code: $("#code").value,
        });
        location.replace(window.MargenAccess.target(data.next));
      },
      "Verificando…",
    );
  };
  $("#retry").onclick = () => {
    if (busy) return;
    stopDelivery();
    challenge = "";
    $("#verify-form").hidden = true;
    $("#email-form").hidden = false;
    $("#code").value = "";
    $("#message").textContent = "";
    heading();
    $("#email").focus();
  };
  $("#resend").onclick = async () => {
    if (Date.now() < resendAt || busy) return;
    busy = true;
    $("#resend").disabled = true;
    $("#message").textContent = "";
    // Keep verification and changing email unavailable while replacing the challenge.
    $("#retry").disabled = true;
    $("#verify-form [type=submit]").disabled = true;
    try {
      await requestCode();
    } catch (error) {
      $("#message").textContent = error.message;
      cooldown();
    } finally {
      busy = false;
      clearTimeout(resendTimer);
      cooldown();
      $("#retry").disabled = false;
      $("#verify-form [type=submit]").disabled = false;
    }
  };
  function watchDelivery() {
    const generation = epoch,
      id = challenge,
      recipient = email;
    let count = 0;
    const check = async () => {
      try {
        const data = await api(
          "/api/auth/email/status?challenge=" + encodeURIComponent(id),
        );
        if (generation !== epoch) return;
        const messages = {
          queued: "Preparando el envío a " + recipient + ".",
          sent: "Código enviado a " + recipient + ".",
          delivered: "El mensaje llegó a " + recipient + ".",
          failed:
            "No pudimos entregar el código. Revisa el correo o vuelve a intentarlo con Google.",
        };
        $("#sent-to").textContent =
          messages[data.status] || "Revisa tu correo para encontrar el código.";
        if (!["delivered", "failed"].includes(data.status) && ++count < 12)
          deliveryTimer = setTimeout(check, 5000);
      } catch {
        /* Delivery polling must never block entering an already received code. */
      }
    };
    deliveryTimer = setTimeout(check, 1200);
  }
  addEventListener("beforeunload", stopDelivery);
  if (params.has("error"))
    $("#message").textContent =
      "No se completó el acceso con Google. Intenta de nuevo o usa tu correo.";
  api("/api/auth/options")
    .then((options) => {
      authOptions = options;
      $("#access-loading").hidden = true;
      $("#email-form").hidden = !options.email;
      $("#google").href = "/auth/google?next=" + encodeURIComponent(next);
      heading();
      if (!options.google && !options.email) {
        $("#message").textContent =
          "El acceso no está disponible en este momento. Vuelve a intentarlo más tarde.";
        $("#access-reload").hidden = false;
      }
    })
    .catch(() => {
      $("#access-loading").hidden = true;
      $("#message").textContent =
        "No pudimos cargar las opciones de acceso. Vuelve a intentarlo.";
      $("#access-reload").hidden = false;
    });
  api("/api/session")
    .then(({ user }) => {
      if (user?.verified) location.replace(next);
    })
    .catch(() => {});
})();
