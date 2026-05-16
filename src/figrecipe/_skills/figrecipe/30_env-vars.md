---
description: |
  [TOPIC] Env Vars
  [DETAILS] see general/10_arch-environment-variables.md.
tags: [figrecipe-env-vars, figrecipe]
---


# figrecipe — Environment Variables

| Variable | Purpose | Default | Type |
|---|---|---|---|
| `SCITEX_DARK` | Enable dark-mode palette for figures. | `false` | bool |
| `SCITEX_RGB` | Force RGB (vs RGBA) output channel count. | `false` | bool |
| `SCITEX_STATS_AVAILABLE` | Presence flag: set when `scitex_stats` importable; gates stats overlays. | unset | bool (presence) |
| `SCITEX_UI_STATIC` | Static-asset dir (shared with scitex-ui) for embedded CSS / logos. | bundled | path |

## Feature flags

- **opt-in:** `SCITEX_DARK=true` switches the palette to dark mode (off by
  default to match publication defaults).
- **opt-in:** `SCITEX_RGB=true` drops the alpha channel (useful for journals
  that reject RGBA).

## Notes

figrecipe is a third-party-compatible package (stands alone from the SciTeX
namespace). The `SCITEX_*` vars above are honored for ecosystem integration
but are not required — figrecipe has matching `FIGRECIPE_*` synonyms for
each, which take precedence when set.

## Audit

```bash
grep -rhoE 'SCITEX_[A-Z0-9_]+' $HOME/proj/figrecipe/src/ | sort -u
```
