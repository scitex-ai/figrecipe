import React from "react";
import { createRoot } from "react-dom/client";
import { DataTable } from "@scitex/sdk/ui/react/app/data-table/DataTable.tsx";
import {applyColumnHighlight,renderedColumnNodes} from "../src/components/DataTablePane/dataTableDom";
import "@scitex/sdk/ui/css/app/data-table.css";
import "../src/styles/panels/datatable.css";
let columns=["x","y"];
function render() { const data={columns,rows:[{[columns[0]]:2,[columns[1]]:4},{[columns[0]]:1,[columns[1]]:3}]}; root.render(<DataTable key={columns.join()} data={data} onDataChange={(value)=>(window as any).axisFixture.changes.push(value)}/>); }
const root=createRoot(document.querySelector("#root")!);
(window as any).axisFixture={
  apply(words={x:"X axis",y:"Y axis"}) {applyColumnHighlight(renderedColumnNodes(document),[{index:0,name:columns[0],role:"x",preview:false},{index:1,name:columns[1],role:"y",preview:false}],words);},
  clear() {applyColumnHighlight(renderedColumnNodes(document),[]);},
  changes:[],
  longNames() { columns=["measurement_time_seconds","recorded_amplitude_volts"]; render(); },
};
render();
