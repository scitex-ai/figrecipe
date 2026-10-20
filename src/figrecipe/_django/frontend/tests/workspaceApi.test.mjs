/** Execute leaf mount configuration and the public stats bridge with real API URL construction. */
import assert from "node:assert/strict";
import { build } from "esbuild";
import { fileURLToPath } from "node:url";
const source=fileURLToPath(new URL("../src/",import.meta.url));
const bundle=await build({
  stdin:{contents:'export { FigrecipeEditor } from "./FigrecipeEditor"; export {apiUrl,setApiBase,setRecipe,setWorkingDir} from "./api/client"; export {runStatAndRenderBracket} from "./bridge/WorkspaceIntegration";',resolveDir:source,loader:"ts"},
  bundle:true,write:false,format:"esm",platform:"node",define:{"import.meta.env.VITE_API_BASE":'""'},
  plugins:[{name:"render-fixture",setup(build){
    build.onResolve({filter:/^react$|^react\/jsx-runtime$|InnerEditor$|store\/useEditorStore$|EventBus$|MountPoint$/},args=>({path:args.path,namespace:"fixture"}));
    build.onLoad({filter:/.*/,namespace:"fixture"},args=>({contents:
      args.path==="react" ? "export const useMemo=fn=>fn(); export const useEffect=()=>{};" :
      args.path==="react/jsx-runtime" ? "export const jsx=(type,props)=>({type,props}); export const jsxs=jsx;" :
      args.path.endsWith("InnerEditor") ? "export const InnerEditor=()=>{};" :
      args.path.endsWith("useEditorStore") ? "export const useEditorStore={setState: state=>globalThis.editorState=state};" :
      args.path.endsWith("EventBus") ? "export const onEvent=()=>()=>{};" : "export const switchRecipeFile=()=>{};",loader:"js"}));
  }}]
});
globalThis.window={location:{search:"?project=alpha",pathname:"/host/workspace/"}};
globalThis.document={cookie:"csrftoken=synthetic-token"};
const calls=[];
globalThis.fetch=async (url,options)=>{calls.push({url,options}); return {ok:true,json:async()=>url.includes("stats/run")?{result:{p:0.01},annotation:{stars:"*"}}:{bracket_id:"b1",preview:"synthetic"}};};
const leaf=await import("data:text/javascript;base64,"+Buffer.from(bundle.outputFiles[0].text).toString("base64"));
leaf.FigrecipeEditor({apiBaseUrl:"/custom/plot",workingDir:"/synthetic/alpha",recipe:"initial.yaml"});
assert.equal(new URL(leaf.apiUrl("preview"),"https://fixture.invalid").pathname,"/custom/plot/preview");
assert.equal(globalThis.editorState.currentFile,"initial.yaml");
const result=await leaf.runStatAndRenderBracket("t_test",[{label:"a",values:[1,2]},{label:"b",values:[3,4]}]);
assert.equal(result.bracket_id,"b1");
assert.deepEqual(calls.map(c=>new URL(c.url,"https://fixture.invalid").pathname),["/custom/plot/stats/run","/custom/plot/stats/add_bracket"]);
assert.ok(calls.every(c=>c.url.includes("project=alpha")&&c.options.headers["X-CSRFToken"]==="synthetic-token"));
leaf.FigrecipeEditor({apiBaseUrl:"",workingDir:"",recipe:""});
const root=new URL(leaf.apiUrl("preview"),"https://fixture.invalid");
assert.equal(root.pathname,"/preview");
assert.equal(root.searchParams.has("working_dir"),false);
assert.equal(root.searchParams.has("recipe"),false);
console.log("workspaceApi: custom stats routing/project/CSRF; remount at explicit root clears previous routing and selectors");
