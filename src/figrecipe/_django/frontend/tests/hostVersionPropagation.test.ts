/** Host-consumer version propagation gate.
 *
 * Reproduces the Hub consumer build, where __FIGRECIPE_VERSION__ is not
 * defined because the host compiles FigRecipe's source with its own Vite
 * config. The host stamps its stable leaf version on #app-mount as
 * data-app-version; the bridge must carry that value all the way to the
 * FigRecipe-owned header.
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/hostVersionPropagation.test.ts
 */

import {
  existsSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";

const here = dirname(fileURLToPath(import.meta.url));
const FRONTEND = join(here, "..");
const SRC = join(FRONTEND, "src");
const read = (rel: string) => readFileSync(join(SRC, rel), "utf8");

let failures = 0;
function check(name: string, condition: boolean) {
  if (condition) console.log(`  ok   ${name}`);
  else {
    failures++;
    console.error(`  FAIL ${name}`);
  }
}

const bridgeInit = read("bridge/bridge-init.ts");
const mountPoint = read("bridge/MountPoint.ts");

check(
  "bridge reads the stable data-app-version mount metadata",
  /const\s+appVersion\s*=\s*mount\.dataset\.appVersion/.test(bridgeInit),
);
check(
  "embedded host mount passes appVersion into MountPoint",
  /if\s*\(isEmbedded\)[\s\S]*?mountFigrecipeEditor\(\{[\s\S]*?appVersion[\s\S]*?\}\)/.test(
    bridgeInit,
  ),
);
check(
  "on-demand host mount passes appVersion into MountPoint",
  /function\s+openInFigrecipe[\s\S]*?mountFigrecipeEditor\(\{[\s\S]*?appVersion[\s\S]*?\}\)/.test(
    bridgeInit,
  ),
);
check(
  "MountPoint accepts an optional host appVersion",
  /interface\s+FigrecipeBridgeMountOptions\s+extends\s+BridgeMountOptions\s*\{[\s\S]*?appVersion\?:\s*string/.test(
    mountPoint,
  ),
);
check(
  "MountPoint forwards the host value to FigrecipeEditor",
  /appVersion:\s*options\.appVersion/.test(mountPoint),
);
check(
  "host bridge does not depend on the leaf-only build constant",
  !mountPoint.includes("__FIGRECIPE_VERSION__") &&
    !bridgeInit.includes("__FIGRECIPE_VERSION__"),
);

// Runtime rendering proof. Keep the header small and dependency-light so this
// executes it with ReactDOMServer rather than merely matching JSX source.
const badgePath = join(SRC, "components", "FigrecipeVersionBadge.tsx");
check("FigrecipeVersionBadge runtime module exists", existsSync(badgePath));

if (existsSync(badgePath)) {
  const source = readFileSync(badgePath, "utf8");
  const { outputText } = ts.transpileModule(source, {
    compilerOptions: {
      esModuleInterop: true,
      jsx: ts.JsxEmit.ReactJSX,
      module: ts.ModuleKind.ESNext,
      target: ts.ScriptTarget.ES2020,
    },
    fileName: badgePath,
  });

  const tempDir = mkdtempSync(join(FRONTEND, ".host-version-test-"));
  let moduleSequence = 0;

  async function loadBadge(buildVersion?: string) {
    const modulePath = join(tempDir, `badge-${moduleSequence++}.mjs`);
    const buildConstant =
      buildVersion === undefined
        ? ""
        : `const __FIGRECIPE_VERSION__ = ${JSON.stringify(buildVersion)};\n`;
    writeFileSync(modulePath, buildConstant + outputText);
    return (await import(pathToFileURL(modulePath).href)) as {
      FigrecipeVersionBadge: React.ComponentType<{
        appVersion?: string;
      }>;
    };
  }

  const originalDocument = globalThis.document;
  try {
    // Host-consumer case: there is no leaf build constant and no standalone
    // #root. The supplied mount metadata must still produce the badge.
    Object.defineProperty(globalThis, "document", {
      configurable: true,
      value: { getElementById: () => null },
    });
    const hostBadge = (await loadBadge()).FigrecipeVersionBadge;
    const hostHtml = renderToStaticMarkup(
      React.createElement(hostBadge, {
        appVersion: "0.34.7-host",
      }),
    );
    check(
      "host build without __FIGRECIPE_VERSION__ renders supplied version",
      hostHtml.includes('class="stx-app-header__version"') &&
        hostHtml.includes("v0.34.7-host"),
    );

    // Standalone Django fallback remains supported when no explicit prop is
    // supplied.
    Object.defineProperty(globalThis, "document", {
      configurable: true,
      value: {
        getElementById: (id: string) =>
          id === "root" ? { getAttribute: () => "0.34.7-root" } : null,
      },
    });
    const rootHtml = renderToStaticMarkup(
      React.createElement(hostBadge),
    );
    check(
      "standalone #root data-version fallback still renders",
      rootHtml.includes("v0.34.7-root"),
    );

    // Leaf-owned Vite build fallback remains supported when neither the host
    // nor standalone root supplies metadata.
    Object.defineProperty(globalThis, "document", {
      configurable: true,
      value: { getElementById: () => null },
    });
    const builtBadge = (await loadBadge("0.34.7-build"))
      .FigrecipeVersionBadge;
    const buildHtml = renderToStaticMarkup(
      React.createElement(builtBadge),
    );
    check(
      "standalone build constant fallback still renders",
      buildHtml.includes("v0.34.7-build"),
    );
  } finally {
    rmSync(tempDir, { force: true, recursive: true });
    if (originalDocument === undefined) {
      Reflect.deleteProperty(globalThis, "document");
    } else {
      Object.defineProperty(globalThis, "document", {
        configurable: true,
        value: originalDocument,
      });
    }
  }
}

if (failures > 0) {
  console.error(`\n${failures} check(s) FAILED`);
  process.exit(1);
}
console.log("\nAll host version propagation checks passed.");
