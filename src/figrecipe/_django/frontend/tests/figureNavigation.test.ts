import { act, createElement } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, beforeEach, expect, it } from "vitest";
import { NavigationTab } from "../src/components/NavigationTab";
import { useEditorStore } from "../src/store/useEditorStore";
import { closeDataTab } from "../src/store/editorNavigation";
import { initUndoHistory, undo, redo, canUndo } from "../src/hooks/useUndoRedo";
import type { PlacedFigure, TabData } from "../src/types/editor";
(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;
const figures = [
 {id:"a",path:"a.yaml",canvasKey:"first",x:0,y:0},
 {id:"b",path:"b.yaml",canvasKey:"first",x:10,y:0},
 {id:"c",path:"c.yaml",canvasKey:"second",x:0,y:0},
] as PlacedFigure[];
const data: TabData = {id:"main",label:"fixture.csv",columns:[{name:"x",dtype:"numeric"}],rows:[[42]],source:"project"};
beforeEach(() => {
 useEditorStore.setState({placedFigures:structuredClone(figures),selectedFigureId:"a", selectedFigureIds:["a"],datatableTabs:{main:structuredClone(data)},activeTabId:"main",datatableRevision:"r1"});
 initUndoHistory();
});
afterEach(() => {document.body.innerHTML="";});
it("removes a complete Figure atomically; undo restores its panels and selection", () => {
 useEditorStore.getState().removeFigure(["a","b"]);
 expect(useEditorStore.getState().placedFigures.map(f=>f.id)).toEqual(["c"]);
 expect(useEditorStore.getState().selectedFigureId).toBe("c");
 expect(undo()).toBe(true);
 expect(useEditorStore.getState().placedFigures.map(f=>f.id)).toEqual(["a","b","c"]);
 expect(useEditorStore.getState().selectedFigureId).toBe("a");
 expect(redo()).toBe(true);
 expect(useEditorStore.getState().placedFigures.map(f=>f.id)).toEqual(["c"]);
});
it("closing data never deletes its selected panel and supports undo/redo", () => {
 expect(closeDataTab("main")).toBe(true);
 expect(useEditorStore.getState().placedFigures).toHaveLength(3);
 expect(useEditorStore.getState().datatableTabs.main).toBeUndefined();
 expect(undo()).toBe(true);
 expect(useEditorStore.getState().datatableTabs.main.rows).toEqual([[42]]);
 expect(redo()).toBe(true);
 expect(useEditorStore.getState().datatableTabs.main).toBeUndefined();
});
it("refuses removal of locked recorded data, including direct action calls", () => {
 useEditorStore.setState({datatableTabs:{main:{...data,source:"record"}}});
 expect(closeDataTab("main")).toBe(false);
 expect(useEditorStore.getState().datatableTabs.main.source).toBe("record");
 expect(canUndo()).toBe(false);
});
it("undo never overwrites a newer server revision", () => {
 closeDataTab("main");
 useEditorStore.setState({datatableTabs:{main:{...data,rows:[[99]]}},datatableRevision:"r2"});
 undo();
 expect(useEditorStore.getState().datatableTabs.main.rows).toEqual([[99]]);
 expect(useEditorStore.getState().datatableRevision).toBe("r2");
});
it("right-click and Shift+F10 expose the same removal action; Escape restores focus", () => {
 const mount=document.createElement("div");document.body.append(mount);const root=createRoot(mount);
 let removed=0;
 act(()=>root.render(createElement(NavigationTab,{onRemove:()=>removed++,removeLabel:"Remove panel"},"Panel A")));
 const tab=mount.querySelector("button")!;
 act(()=>tab.dispatchEvent(new MouseEvent("contextmenu",{bubbles:true,clientX:30,clientY:40})));
 expect(document.querySelector("[role=menuitem]")?.textContent).toBe("Remove panel");
 act(()=>document.dispatchEvent(new KeyboardEvent("keydown",{key:"Escape",bubbles:true})));
 expect(document.querySelector("[role=menu]")).toBeNull();expect(document.activeElement).toBe(tab);
 act(()=>tab.dispatchEvent(new KeyboardEvent("keydown",{key:"F10",shiftKey:true,bubbles:true})));
 act(()=>(document.querySelector("[role=menuitem]") as HTMLButtonElement).click());
 expect(removed).toBe(1);
 act(()=>root.unmount());
});

it("canvas undo preserves newly locked data rather than reviving an editable copy", () => {
 useEditorStore.getState().removeFigure("a");
 useEditorStore.setState({datatableTabs:{main:{...data,source:"record"}}});
 undo();
 expect(useEditorStore.getState().datatableTabs.main.source).toBe("record");
});

it("background data reads retain all panel sources without changing active selection", async () => {
 const {api} = await import("../src/api/client");
 const original = api.getForRecipe;
 try {
  api.getForRecipe = async <T>(_endpoint: string, recipe: string) => ({
    columns:[{name:"x",dtype:"numeric"}],rows:[[1]],source:"record",
    chunks:[{id:recipe+"::inline",label:recipe+" · inline",kind:"inline",panel_path:recipe,source_ref:recipe,columns:[{name:"x",dtype:"numeric"}],rows:[[1]],source:"record",revision:null}],
  } as T);
  await useEditorStore.getState().loadDatatable({recipe:"a.yaml",activate:false});
  await useEditorStore.getState().loadDatatable({recipe:"b.yaml",activate:false});
  expect(Object.values(useEditorStore.getState().datatableTabs).map(t=>t.panelPath)).toContain("a.yaml");
  expect(Object.values(useEditorStore.getState().datatableTabs).map(t=>t.panelPath)).toContain("b.yaml");
  expect(useEditorStore.getState().activeTabId).toBe("main");
  expect(useEditorStore.getState().selectedFigureId).toBe("a");
  const {selectDataTab}=await import("../src/store/editorNavigation");
  selectDataTab("b.yaml::inline");
  expect(useEditorStore.getState().selectedFigureId).toBe("b");
  expect(useEditorStore.getState().currentFile).toBe("b.yaml");
 } finally {api.getForRecipe=original;}
});

it("queued table writes refuse changed sessions, recipes, and tabs", async () => {
 const {tableWriteMatches}=await import("../src/components/DataTablePane/tableWriteContext");
 const owner={session:3,recipe:"a.yaml",tabId:"a::inline"};
 expect(tableWriteMatches(owner,{...owner})).toBe(true);
 expect(tableWriteMatches(owner,{...owner,recipe:"b.yaml"})).toBe(false);
 expect(tableWriteMatches(owner,{...owner,tabId:"a::linked"})).toBe(false);
 expect(tableWriteMatches(owner,{...owner,session:4})).toBe(false);
});
