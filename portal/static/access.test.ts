import { beforeEach, afterEach, it, expect, vi } from "vitest";
import { readFileSync } from "node:fs";
const source = readFileSync("portal/static/access.js", "utf8");
beforeEach(() => {
  window.eval(source);
});
afterEach(() => {
  document.body.replaceChildren();
  vi.restoreAllMocks();
});
const access = () => (window as any).MargenAccess;
it("keeps document review context but rejects external or malformed return destinations", () => {
  const path = "/a/" + "a".repeat(32);
  expect(
    access().target(
      path + "?thread=review-1&version=v_2&email=private%40example.com",
    ),
  ).toBe(path + "?thread=review-1&version=v_2");
  expect(access().target("/?view=brain")).toBe("/?view=brain");
  for (const value of [
    "https://evil.test",
    "//evil.test",
    "/\\evil.test",
    "/%2f%2fevil.test",
    "/a/invalid",
    "/\n?view=brain",
    null,
  ])
    expect(access().target(value)).toBe("/");
});
it("offers auth with preserved context, without fabricating protected metadata", () => {
  const next = "/a/" + "b".repeat(32) + "?thread=one";
  const card = access().gate({
    user: null,
    status: 404,
    next,
    options: { google: true, email: true },
  });
  expect(
    card.querySelector('a[href^="/auth/google"]').getAttribute("href"),
  ).toBe("/auth/google?next=" + encodeURIComponent(next));
  expect(card.querySelector('a[href^="/login"]').getAttribute("href")).toBe(
    "/login?next=" + encodeURIComponent(next),
  );
  expect(card.textContent).not.toContain("contraseña");
});
it("shows the current account and does not offer fake access requests to denied readers", async () => {
  const change = vi.fn().mockResolvedValue(undefined);
  const card = access().gate({
    user: { verified: true, email: "reader@example.com" },
    status: 404,
    changeAccount: change,
  });
  expect(card.textContent).toContain("reader@example.com");
  expect(card.querySelector('a[href^="/auth/google"]')).toBeNull();
  card.querySelector("button").click();
  await Promise.resolve();
  expect(change).toHaveBeenCalledOnce();
});
it("does not mistake server failures for missing permission", async () => {
  const retry = vi.fn().mockResolvedValue(undefined);
  const card = access().gate({ user: null, status: 503, retry });
  expect(card.querySelector('a[href^="/login"]')).toBeNull();
  expect(card.textContent).toContain("No pudimos abrir");
  card.querySelector("button").click();
  await Promise.resolve();
  expect(retry).toHaveBeenCalledOnce();
});
