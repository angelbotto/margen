import { beforeEach, afterEach, it, expect, vi } from "vitest";
import { readFileSync } from "node:fs";
const source = readFileSync("portal/static/login.js", "utf8");
const html = readFileSync("portal/static/login.html", "utf8");
const flush = async () => {
  for (let i = 0; i < 12; i++) await Promise.resolve();
};
const input = (id: string) => document.querySelector<HTMLInputElement>(id)!;
const form = (id: string) => document.querySelector<HTMLFormElement>(id)!;
const reply = (data: unknown) =>
  Promise.resolve({ ok: true, json: async () => data });
beforeEach(() => {
  vi.useFakeTimers();
  document.body.innerHTML = new DOMParser().parseFromString(
    html,
    "text/html",
  ).body.innerHTML;
  history.replaceState(
    {},
    "",
    "/login?next=" +
      encodeURIComponent("/a/" + "a".repeat(32) + "?thread=note-1"),
  );
  window.eval(readFileSync("portal/static/access.js", "utf8"));
  vi.stubGlobal("matchMedia", () => ({ matches: false }));
});
afterEach(() => {
  window.dispatchEvent(new Event("beforeunload"));
  document.body.replaceChildren();
  vi.useRealTimers();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  history.replaceState({}, "", "/");
});
it("preserves the document thread for email and Google, and avoids stale delivery updates after switching email", async () => {
  let deliver: (value: any) => void;
  const fetch = vi.fn((url: string) => {
    if (url === "/api/auth/options")
      return reply({ google: true, email: true });
    if (url === "/api/session") return reply({ user: null });
    if (url === "/api/auth/email") return reply({ challenge: "first" });
    return new Promise((resolve) => {
      deliver = resolve;
    });
  });
  vi.stubGlobal("fetch", fetch);
  window.eval(source);
  await flush();
  expect(document.querySelector("#google")!.getAttribute("href")).toContain(
    "thread%3Dnote-1",
  );
  input("#email").value = "reader@example.com";
  form("#email-form").dispatchEvent(new Event("submit", { cancelable: true }));
  await flush();
  expect(
    JSON.parse(
      fetch.mock.calls.find(([url]) => url === "/api/auth/email")![1].body,
    ).next,
  ).toContain("?thread=note-1");
  expect(form("#verify-form").hidden).toBe(false);
  expect(document.querySelector<HTMLButtonElement>("#resend")!.disabled).toBe(
    true,
  );
  await vi.advanceTimersByTimeAsync(1200);
  document.querySelector<HTMLButtonElement>("#retry")!.click();
  deliver!({ ok: true, json: async () => ({ status: "failed" }) });
  await flush();
  expect(form("#email-form").hidden).toBe(false);
  expect(document.querySelector("#sent-to")!.textContent).not.toContain(
    "No pudimos",
  );
  expect(document.querySelector("#message")!.textContent).toBe("");
});
it("shows only available methods and provides recovery when options cannot load", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) =>
      url === "/api/session"
        ? reply({ user: null })
        : Promise.reject(new Error("offline")),
    ),
  );
  window.eval(source);
  await flush();
  expect(form("#email-form").hidden).toBe(true);
  expect(document.querySelector<HTMLElement>("#access-reload")!.hidden).toBe(
    false,
  );
  expect(document.querySelector("#message")!.textContent).toContain(
    "No pudimos cargar",
  );
});
it("keeps a Google-only entry usable without a misleading email divider", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) =>
      reply(
        url === "/api/session"
          ? { user: null }
          : { google: true, email: false },
      ),
    ),
  );
  window.eval(source);
  await flush();
  expect(document.querySelector<HTMLElement>("#google")!.hidden).toBe(false);
  expect(form("#email-form").hidden).toBe(true);
  expect(document.querySelector<HTMLElement>("#divider")!.hidden).toBe(true);
  expect(document.querySelector("#message")!.textContent).toBe("");
});
