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

Pulls `matplotlib>=3.5`, `numpy>=1.20`, `pandas>=1.3`, `PyYAML`,
`ruamel.yaml`, `scipy>=1.7`, `click`, `rich`, `scitex-app`,
`scitex-linter`, and `scitex` (umbrella, for `stx.io`).

## Optional extras

| Extra | Purpose |
|---|---|
| `seaborn` | `figrecipe.sns` integration |
| `imaging` | Pillow-based image processing helpers |
| `graph` | Mermaid / Graphviz diagram backends |
| `graph-interactive` | Web-rendered diagram preview |
| `editor` | GUI editor (`figrecipe gui`) |
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
git clone https://github.com/ywatanabe1989/figrecipe
cd figrecipe
pip install -e '.[dev,all]'
```

## See also

- `scitex-plt` — `sys.modules` alias of figrecipe under the `scitex_*` name
- `scitex-io` — `stx.io.save(fig, ...)` is the canonical save entry-point
