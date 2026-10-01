---
description: |
  [TOPIC] Installation
  [DETAILS] pip install figrecipe. Pulls matplotlib, pandas, scipy, click, rich. Many optional extras (imaging, seaborn, graph, mcp, …).
tags: [figrecipe-installation]
---

# Installation

## Standard

```bash
pip install figrecipe
```

The coordinated source candidate declares `matplotlib>=3.5`, `numpy>=1.20`,
`pandas>=1.3`, `PyYAML>=6`, `ruamel.yaml>=0.17`, `scipy>=1.7`, `click>=8`,
`rich>=13`, `scitex-sdk>=0.3.0`, `scitex-config>=0.3.0` and
`scitex-dev>=0.60.1`. SDK 0.3 is pending publication: install its reviewed
wheel or checkout before installing this candidate. The registry command
above installs the currently published FigRecipe.

## Optional extras

| Extra | Purpose |
|---|---|
| `seaborn` | `figrecipe.sns` integration |
| `imaging` | Pillow-based image processing helpers |
| `graph` | Mermaid / Graphviz diagram backends |
| `graph-interactive` | Web-rendered diagram preview |
| `editor` | GUI editor (`figrecipe gui open`) |
| `app` | Workspace-app integration (scitex-cloud) |
| `desktop` | Native desktop launcher |
| `mcp` | MCP server (`figrecipe mcp serve`) |
| `demo` | Bundled demo data + recipes |
| `dev` / `docs` | Test + docs tooling |
| `all` | Everything above |

```bash
pip install 'figrecipe[seaborn,graph,mcp]'
```

## Verify

```bash
python -c "import figrecipe; print(figrecipe.__version__)"
figrecipe --version
figrecipe --help
```

## Editable install (development)

```bash
git clone https://github.com/scitex-ai/figrecipe
cd figrecipe
pip install -e '.[dev,all]'
```

## See also

- `scitex-plt` — `sys.modules` alias of figrecipe under the `scitex_*` name
- `scitex-io` — `stx.io.save(fig, ...)` is the canonical save entry-point
