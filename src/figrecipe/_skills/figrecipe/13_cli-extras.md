---
description: |
  [TOPIC] Cli Extras
  [DETAILS] diagram, style, fonts, MCP, skills, completion.
tags: [figrecipe-cli-extras, figrecipe]
---


# CLI Extras

Companion to [11_cli-reference.md](11_cli-reference.md).

## Diagram

### figrecipe diagram

```bash
figrecipe diagram render flow.mmd -o flow.png
figrecipe diagram create --preset WORKFLOW
figrecipe diagram --help
```

## Style & Appearance

### figrecipe style

```bash
figrecipe style list              # list all presets
figrecipe style show SCITEX       # show preset details
figrecipe style apply SCITEX      # apply globally
figrecipe style reset             # reset to matplotlib defaults
```

### figrecipe fonts

```bash
figrecipe fonts list              # list available fonts
```

## Integration

### figrecipe mcp

```bash
figrecipe mcp start               # start MCP server
figrecipe mcp run                 # run MCP server (alias)
figrecipe mcp install             # install MCP configuration
```

### figrecipe skills

```bash
figrecipe skills list             # list available skills
figrecipe skills get SKILL        # show a specific skill
figrecipe skills get plot-types   # example: show plot-types skill
```

### figrecipe list-python-apis

```bash
figrecipe list-python-apis        # list all public Python API functions
```

## Utility

### figrecipe completion

```bash
figrecipe completion bash         # generate bash completion
figrecipe completion zsh          # generate zsh completion
```

### figrecipe show-version

```bash
figrecipe show-version
```
