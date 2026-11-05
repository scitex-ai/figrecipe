import { act, createElement, StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, expect, it } from "vitest";
import { EditorAppHeader } from "../src/components/EditorAppHeader";

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;
afterEach(() => { document.body.innerHTML = ""; });

for (const server of [false, true]) {
  it(`keeps one picker and canonical header in ${server ? "server" : "SPA"} mode`, () => {
    if (server) {
      const declaration = document.createElement("div");
      declaration.dataset.stxAppHeader = "";
      declaration.dataset.figrecipeHeader = "";
      declaration.dataset.appTitle = "Server FigRecipe";
      declaration.dataset.appVersion = "1.2";
      const region = document.createElement("div");
      region.dataset.figrecipeHeaderRegion = "";
      region.append(declaration);
      document.body.append(region);
    }
    const mount = document.createElement("div");
    document.body.append(mount);
    const root = createRoot(mount);
    const render = (version: string) => act(() => root.render(createElement(StrictMode, null,
      createElement(EditorAppHeader, {title: "FigRecipe", version,
        projectSelector: createElement("button", {id: "picker"}, "Project")}),
    )));
    render("1.0");
    expect(document.querySelectorAll("header.stx-app-header")).toHaveLength(1);
    expect(document.querySelectorAll("#picker")).toHaveLength(1);
    const picker = document.querySelector("#picker");
    const header = document.querySelector("header.stx-app-header");
    const slot = header?.querySelector(".stx-app-header__slot--project-selector");
    expect(slot).not.toBeNull();
    expect(picker?.parentElement).toBe(slot);
    expect(header?.querySelector(".stx-app-header__title")?.textContent)
      .toBe(server ? "Server FigRecipe" : "FigRecipe");
    render("2.0");
    expect(document.querySelector("#picker")).toBe(picker);
    expect(document.querySelector("header.stx-app-header")).toBe(header);
    expect(picker?.parentElement).toBe(slot);
    expect(document.querySelectorAll("header.stx-app-header")).toHaveLength(1);
    expect(document.querySelector(".stx-app-header__version")?.textContent)
      .toBe(server ? "v1.2" : "v2.0");
    act(() => root.unmount());
    expect(document.querySelectorAll("#picker")).toHaveLength(0);
    expect(document.querySelectorAll("header.stx-app-header")).toHaveLength(server ? 1 : 0);
  });
}
