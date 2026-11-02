import React from "react";
import { createRoot } from "react-dom/client";
import { DataTable } from "@scitex/sdk/ui/react/app/data-table/DataTable.tsx";
import {applyColumnHighlight,renderedColumnNodes} from "../src/components/DataTablePane/dataTableDom";
import "@scitex/sdk/ui/css/app/data-table.css";
import "../src/styles/panels/datatable.css";
const data={columns:["x","y"],rows:[{x:2,y:4},{x:1,y:3}]};
const root=createRoot(document.querySelector("#root")!);
(window as any).axisFixture={
  apply(words={x:"X axis",y:"Y axis"}) {applyColumnHighlight(renderedColumnNodes(document),[{index:0,name:"x",role:"x",preview:false},{index:1,name:"y",role:"y",preview:false}],words);},
  clear() {applyColumnHighlight(renderedColumnNodes(document),[]);},
  changes:[],
};
root.render(<DataTable data={data} onDataChange={(value)=>(window as any).axisFixture.changes.push(value)}/>);
