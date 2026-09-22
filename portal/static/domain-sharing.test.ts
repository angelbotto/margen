import { beforeEach, it, expect, vi } from "vitest";
import { readFileSync } from "node:fs";
beforeEach(() => {
  document.body.innerHTML = new DOMParser().parseFromString(
    readFileSync("portal/static/index.html", "utf8"),
    "text/html",
  ).body.innerHTML;
  window.eval(readFileSync("portal/static/access.js", "utf8"));
  window.eval(readFileSync("portal/static/domain-sharing.js", "utf8"));
});
it("adds canonical domains, prevents duplicates and removes only local pending grants", () => {
  const root = document.querySelector("#domain-sharing")!,
    change = vi.fn();
  const editor = (window as any).MargenDomainSharing.create(root, change);
  const input = root.querySelector<HTMLInputElement>("[data-domain-input]")!;
  const add = root.querySelector<HTMLButtonElement>("[data-add-domain]")!;
  input.value = " @TIKIN.IS ";
  add.click();
  expect(editor.get()).toEqual([{ domain: "tikin.is", role: "commenter" }]);
  expect(change).toHaveBeenCalledOnce();
  input.value = "tikin.is";
  add.click();
  expect(editor.get()).toHaveLength(1);
  expect(root.querySelector("[role=alert]")!.textContent).toContain("ya está");
  root.querySelector<HTMLButtonElement>(".domain-remove")!.click();
  expect(editor.get()).toEqual([]);
  expect(document.activeElement).toBe(input);
});
it("rejects unsafe audience strings and prevents Enter from submitting the access form", () => {
  const root = document.querySelector("#domain-sharing")!;
  const editor = (window as any).MargenDomainSharing.create(root, vi.fn());
  const input = root.querySelector<HTMLInputElement>("[data-domain-input]")!;
  for (const value of [
    "*.tikin.is",
    "https://tikin.is",
    "tikin.is/",
    "person@tikin.is",
    "tíkin.is",
    "127.0.0.1",
  ]) {
    input.value = value;
    const event = new KeyboardEvent("keydown", {
      key: "Enter",
      cancelable: true,
    });
    input.dispatchEvent(event);
    expect(event.defaultPrevented).toBe(true);
    expect(editor.get()).toEqual([]);
  }
});
it("does not mutate server-owned grants until saved and has no domain-wide edit option", () => {
  const root = document.querySelector("#domain-sharing")!,
    original = [{ domain: "tikin.is", role: "commenter" }];
  const editor = (window as any).MargenDomainSharing.create(root, vi.fn());
  editor.set(original);
  const select = root.querySelector<HTMLSelectElement>(".domain-grant select")!;
  expect([...select.options].map((o) => o.value)).toEqual([
    "viewer",
    "commenter",
  ]);
  select.value = "viewer";
  select.dispatchEvent(new Event("change"));
  expect(original[0].role).toBe("commenter");
  expect(editor.get()[0].role).toBe("viewer");
});
