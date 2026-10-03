/** The actual public SDK export, Python floor, lock and symbol contract.
 * Run node --experimental-strip-types tests/scitexSdkContract.test.ts.
 * Source and installed-wheel consumers use the same package exports, never
 * an alias exposing internal checkout paths. Actual strict/Vite builds follow.
 */
import assert from "node:assert/strict";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
let passed=0;
function ok(name:string,fn:()=>void){fn();passed++;console.log("  ok - "+name);}
const FRONTEND=resolve(dirname(fileURLToPath(import.meta.url)),"..");
const REPO=resolve(FRONTEND,"../../../..");
const read=(p:string)=>readFileSync(join(FRONTEND,p),"utf8");
const pkg=JSON.parse(read("package.json"));
const lock=JSON.parse(read("package-lock.json"));
const OWNER=join(FRONTEND,"node_modules/@scitex/sdk");
const OWNER_PREFIX="@scitex/sdk/";
function resolveOwnerModule(specifier:string):string|null{
  try{
    const file=fileURLToPath(import.meta.resolve(specifier));
    return existsSync(file)&&statSync(file).isFile()?file:null;
  }catch{return null;}
}
/** Every export a module offers, following re-exports (bounded, cycle-safe). */
function exportsOf(file: string, seen = new Set<string>()): Set<string> {
  const names = new Set<string>();
  if (seen.has(file) || !existsSync(file)) return names;
  seen.add(file);
  const source = readFileSync(file, "utf8");
  const directory = dirname(file);

  for (const match of source.matchAll(/export\s+(?:type\s+)?\{([^}]*)\}/g)) {
    for (const entry of match[1].split(",")) {
      const name = entry.trim().split(/\s+as\s+/).pop()?.trim();
      if (name) names.add(name);
    }
  }
  for (const match of source.matchAll(
    /export\s+(?:declare\s+)?(?:const|let|var|function|class|enum|interface|type|namespace|abstract\s+class)\s+([A-Za-z_$][\w$]*)/g,
  )) {
    names.add(match[1]);
  }
  if (/export\s+default\b/.test(source)) names.add("default");
  for (const match of source.matchAll(
    /export\s+\*\s+as\s+([A-Za-z_$][\w$]*)\s+from\s+["']([^"']+)["']/g,
  )) {
    names.add(match[1]);
  }
  for (const match of source.matchAll(/export\s+\*\s+from\s+["']([^"']+)["']/g)) {
    const target = resolveSpecifierFrom(directory, match[1]);
    if (target) for (const name of exportsOf(target, seen)) names.add(name);
  }
  for (const match of source.matchAll(
    /export\s+(?:type\s+)?\{(?:[^}]*)\}\s+from\s+["']([^"']+)["']/g,
  )) {
    // Named re-exports are already collected above; following the module keeps
    // `export { X } from "./y"` honest when X is itself re-exported there.
    const target = resolveSpecifierFrom(directory, match[1]);
    if (target) for (const name of exportsOf(target, seen)) names.add(name);
  }
  return names;
}

/** Follow ordinary relative re-exports inside the SDK source. */
function resolveSpecifierFrom(directory: string, specifier: string): string | null {
  if (specifier.startsWith(OWNER_PREFIX)) return resolveOwnerModule(specifier);
  const base = resolve(directory, specifier);
  for (const file of [base, `${base}.ts`, `${base}.tsx`, `${base}.js`, join(base, "index.ts"), join(base, "index.tsx")]) {
    if (existsSync(file) && statSync(file).isFile()) return file;
  }
  return null;
}

/** Every .ts/.tsx file under src/, minus the tests. */
function sourceFiles(): string[] {
  const out: string[] = [];
  const walk = (dir: string) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const full = join(dir, entry.name);
      if (entry.isDirectory()) walk(full);
      else if (/\.tsx?$/.test(entry.name)) out.push(full);
    }
  };
  walk(join(FRONTEND, "src"));
  return out;
}

interface ImportSite {
  file: string;
  specifier: string;
  names: string[];
  typeOnly: boolean;
  sideEffectOnly: boolean;
}

/** All `@scitex/sdk` / bare `scitex-ui` imports in figrecipe's own sources. */
function importSites(): ImportSite[] {
  const sites: ImportSite[] = [];
  for (const file of sourceFiles()) {
    const source = readFileSync(file, "utf8");
    const pattern = /import\s+(type\s+)?([^;]*?)\s*from\s*["']([^"']+)["']|import\s*["']([^"']+)["']/g;
    for (const match of source.matchAll(pattern)) {
      const specifier = match[3] ?? match[4];
      if (!specifier.startsWith(OWNER_PREFIX) && !specifier.startsWith("scitex-ui") && !specifier.startsWith("@scitex/ui")) {
        continue;
      }
      const clause = match[2] ?? "";
      const names: string[] = [];
      const braced = clause.match(/\{([^}]*)\}/);
      if (braced) {
        for (const entry of braced[1].split(",")) {
          const name = entry.trim().split(/\s+as\s+/)[0]?.trim();
          if (name) names.push(name);
        }
      }
      sites.push({
        file: file.slice(FRONTEND.length + 1),
        specifier,
        names,
        typeOnly: Boolean(match[1]),
        sideEffectOnly: !match[3] && Boolean(match[4]),
      });
    }
  }
  return sites;
}

const SITES=importSites();
console.log("scitexSdkContract:");
ok("declared owner is one actual SDK source/version contract",()=>{
 assert.match(pkg.scitexSdk.version,/^\d+\.\d+\.\d+$/);
 assert.match(pkg.scitexSdk.commit,/^[0-9a-f]{40}$/);
 assert.match(pkg.dependencies["@scitex/sdk"],/^file:/);
 assert.ok(!pkg.dependencies["@scitex/ui"]);
});
ok("normal npm packs the SDK owner instead of an external peer-less symlink",()=>{
 assert.match(read(".npmrc"),/^install-links=true$/m);
 assert.equal(lock.lockfileVersion,3);
 const entry=lock.packages["node_modules/@scitex/sdk"];
 assert.ok(entry,"lock must contain the SDK owner");
 assert.equal(entry.version,pkg.scitexSdk.version);
 assert.notEqual(entry.link,true);
 assert.match(entry.resolved,/^file:/);
});
ok("installed frontend SDK owner and Python accessor floor remain explicit",()=>{
 const owner=JSON.parse(readFileSync(join(OWNER,"package.json"),"utf8"));
 assert.equal(owner.name,"@scitex/sdk");
 assert.equal(owner.version,pkg.scitexSdk.version);
 const pyproject=readFileSync(join(REPO,"pyproject.toml"),"utf8");
 const floors=[...pyproject.matchAll(/"scitex-sdk(?:\[[^\]]+\])?([^"]*)"/g)].map(m=>m[1]);
 // The Python leaf_declarations minimum is separate from the immutable JS pin.
 assert.equal(floors.length,6,"required and GUI/test extras must declare the owner");
 assert.deepEqual([...new Set(floors)],[">=0.3.2"]);
 assert.doesNotMatch(pyproject,/"scitex-(?:app|ui)(?:[>=\[]|" )/);
});
ok("import scanning covers actual TS/React/CSS surfaces",()=>{
 assert.ok(SITES.length>=20,`only ${SITES.length} imports scanned`);
 for(const surface of ["ts/","react/","css/"])assert.ok(SITES.some(s=>s.specifier.startsWith(OWNER_PREFIX+"ui/"+surface)),surface);
});
ok("retired import forms and internal source paths stay forbidden",()=>{
 assert.deepEqual(SITES.filter(s=>!s.specifier.startsWith(OWNER_PREFIX)||s.specifier.includes("/src/")).map(s=>`${s.file}: ${s.specifier}`),[]);
});
ok("every canonical SDK import resolves through its actual exports map",()=>{
 assert.deepEqual(SITES.filter(s=>!resolveOwnerModule(s.specifier)).map(s=>`${s.file}: ${s.specifier}`),[]);
 assert.equal(resolveOwnerModule("@scitex/sdk/ui/react/not-a-public-directory"),null);
});
ok("named imports remain exported by their owning modules",()=>{
 const missing:string[]=[];
 for(const site of SITES){const mod=resolveOwnerModule(site.specifier);if(!mod||!/\.(ts|tsx)$/.test(mod))continue;const exported=exportsOf(mod);for(const name of site.names)if(!exported.has(name))missing.push(`${site.file}: ${name} from ${site.specifier}`);}
 assert.deepEqual(missing,[]);
});
ok("strict compiler and both bundlers consume the public package unchanged",()=>{
 const ts=JSON.parse(read("tsconfig.json"));
 assert.equal(ts.compilerOptions.strict,true);
 assert.equal(ts.compilerOptions.moduleResolution,"bundler");
 assert.ok(!Object.keys(ts.compilerOptions.paths??{}).some(p=>p.startsWith("@scitex/")));
 for(const config of ["vite.config.ts","vite.config.lib.ts"]){const text=read(config);assert.doesNotMatch(text,/alias\s*:|execSync|SCITEX_UI_STATIC/);assert.match(text,/dedupe:\s*\["react", "react-dom"\]/);}
});
console.log(`${passed} passed; ${SITES.length} real SDK imports checked`);
