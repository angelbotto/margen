import { beforeEach, afterEach, it, expect, vi } from "vitest";
import { readFileSync } from "node:fs";
const graphSource = readFileSync("portal/static/knowledge.js", "utf8");
const workspaceSource = readFileSync("portal/static/workspace.js", "utf8");
const data = {
  nodes: [
    {
      id: "a",
      title: "Source A",
      space: "Example",
      category: "Research",
      artifact: "a",
    },
  ],
  total: 1,
  network: {
    nodes: [
      { id: "a", title: "Source A", kind: "artifact", artifact: "a" },
      { id: "topic", title: "Capacity", kind: "topic", count: 1 },
      { id: "decision", title: "Pilot decision", kind: "decision", count: 1 },
    ],
    edges: [
      { source: "a", target: "topic", kind: "topic", reason: "Manual topic" },
      {
        source: "decision",
        target: "a",
        kind: "evidence",
        reason: "Exact source",
      },
    ],
  },
};
let root: HTMLElement, instance: any;
beforeEach(() => {
  document.body.innerHTML = '<section id="fixture"></section>';
  root = document.querySelector("#fixture")!;
  window.eval(graphSource);
  window.eval(workspaceSource);
});
afterEach(() => {
  instance?.destroy();
  instance = null;
  document.body.replaceChildren();
  vi.restoreAllMocks();
});
const click = (text: string) => {
  const b = [...root.querySelectorAll("button")].find(
    (b) => b.textContent === text,
  );
  expect(b).toBeTruthy();
  b!.click();
};
it("keeps viewport while inspecting evidence and separates backlinks from grouping", () => {
  instance = (window as any).BottifactKnowledge.graph(root, data, vi.fn());
  root
    .querySelector<HTMLElement>('[data-node="a"]')!
    .dispatchEvent(new Event("click"));
  expect(root.querySelector(".atlas-inspector")!.textContent).toContain(
    "Recibe referencias · 1",
  );
  expect(root.querySelector(".atlas-inspector")!.textContent).toContain(
    "Organización y temas · 1",
  );
  root.querySelector<HTMLButtonElement>('[aria-label="Acercar"]')!.click();
  const transform = root.querySelector("svg>g")!.getAttribute("transform");
  const search = root.querySelector<HTMLInputElement>("input[type=search]")!;
  search.value = "source";
  search.dispatchEvent(new Event("input"));
  expect(root.querySelector("svg>g")!.getAttribute("transform")).toBe(
    transform,
  );
  const orphan = [
    ...root.querySelectorAll<HTMLInputElement>("input[type=checkbox]"),
  ].at(-1)!;
  orphan.checked = true;
  orphan.dispatchEvent(new Event("change"));
  expect(root.querySelectorAll("[data-node]")).toHaveLength(0);
});
it("restores a graph lens and saves inspectable view state", async () => {
  const save = vi.fn().mockResolvedValue({});
  instance = (window as any).BottifactKnowledge.graph(root, data, vi.fn(), {
    preferences: { lens: "topic", labels: true },
    save,
  });
  expect(instance.getLens()).toBe("topic");
  expect(root.querySelector('[data-node="decision"]')).toBeNull();
  instance.setLens("decision");
  click("Guardar esta vista");
  await Promise.resolve();
  expect(save.mock.calls[0][1]).toMatchObject({
    lens: "decision",
    scope: "all",
    orphans: false,
  });
});
it("discards stale workspace responses after navigation", async () => {
  let resolve: any;
  const api = vi.fn(
    () =>
      new Promise((r) => {
        resolve = r;
      }),
  );
  instance = (window as any).MargenWorkspace.create({
    api,
    creator: { unmount: vi.fn() },
    user: () => ({ id: "owner" }),
  });
  const pending = instance.render(root, "insights");
  instance.destroy();
  root.replaceChildren(document.createTextNode("New page"));
  resolve({ spaces: [], daily: [], ranking: [], total: 0 });
  await pending;
  expect(root.textContent).toBe("New page");
});

it('does not fill an empty knowledge lens with unrelated artifacts',()=>{
 instance=(window as any).BottifactKnowledge.graph(root,data,vi.fn());
 instance.setLens('session');
 expect(root.querySelectorAll('[data-node]')).toHaveLength(0);
 expect(root.querySelector('.atlas-inspector')!.textContent).toContain('No hay sesiones');
 instance.setLens('all');expect(root.querySelectorAll('[data-node]')).toHaveLength(3);
});
