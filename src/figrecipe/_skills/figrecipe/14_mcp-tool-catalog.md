---
description: |
  [TOPIC] Mcp Tool Catalog
  [DETAILS] Per-type plot tools, SciTeX scientific plot tools, diagram tools, and MCP resource URIs.
tags: [figrecipe-mcp-tool-catalog, figrecipe]
---


# MCP Tool Catalog

Companion to [12_mcp-tools.md](12_mcp-tools.md).

## Per-type plot tools

Individual tools for each standard matplotlib plot type. Accept `data_file` + column names or inline arrays.

| Tool | Plot type |
|------|-----------|
| `plt_line` / `plt_plot` | Line plot |
| `plt_scatter` | Scatter plot |
| `plt_bar` | Vertical bar chart |
| `plt_barh` | Horizontal bar chart |
| `plt_hist` | Histogram |
| `plt_hist2d` | 2D histogram |
| `plt_boxplot` | Box plot |
| `plt_violinplot` | Violin plot |
| `plt_errorbar` | Error bar plot |
| `plt_fill_between` | Filled band |
| `plt_fill_betweenx` | Horizontal filled band |
| `plt_stackplot` | Stacked area |
| `plt_contour` | Contour lines |
| `plt_contourf` | Filled contours |
| `plt_imshow` | Image / heatmap |
| `plt_pcolormesh` | 2D grid mesh |
| `plt_pie` | Pie chart |
| `plt_stem` | Stem plot |
| `plt_stairs` | Stair/step plot |
| `plt_hexbin` | Hexbin density |
| `plt_quiver` | Vector field |
| `plt_streamplot` | Flow streamlines |
| `plt_ecdf` | Empirical CDF |
| `plt_acorr` | Autocorrelation |
| `plt_xcorr` | Cross-correlation |
| `plt_psd` | Power spectral density |
| `plt_csd` | Cross spectral density |
| `plt_specgram` | Spectrogram |
| `plt_cohere` | Coherence |

## SciTeX scientific plot tools

| Tool | Plot type |
|------|-----------|
| `plt_stx_line` | Styled line |
| `plt_stx_shaded_line` | Line with error band |
| `plt_stx_mean_std` | Mean +/- std |
| `plt_stx_mean_ci` | Mean with CI |
| `plt_stx_median_iqr` | Median with IQR |
| `plt_stx_violin` | Violin with points |
| `plt_stx_scatter_hist` | Scatter + marginal histograms |
| `plt_stx_heatmap` | Annotated heatmap |
| `plt_stx_conf_mat` | Confusion matrix |
| `plt_stx_raster` | Spike raster |
| `plt_stx_ecdf` | ECDF (styled) |
| `plt_stx_fillv` | Vertical fill regions |
| `plt_stx_image` | Image with scale bar |
| `plt_stx_rectangle` | Annotated rectangle |

## Diagram tools

| Tool | Purpose |
|------|---------|
| `plt_diagram_create` | Create from spec dict |
| `plt_diagram_render` | Render to image |
| `plt_diagram_compile_mermaid` | Compile Mermaid text |
| `plt_diagram_compile_graphviz` | Compile Graphviz DOT |
| `plt_diagram_list_presets` | List presets |
| `plt_diagram_get_preset` | Get preset config |
| `plt_diagram_get_backends` | List backends |
| `plt_diagram_get_paper_modes` | List paper modes |
| `plt_diagram_split` | Split across pages |

## MCP Resources

| Resource URI | Contents |
|-------------|---------|
| `figrecipe://spec-schema` | Full declarative spec format documentation |
| `figrecipe://cheatsheet` | Quick reference |
| `figrecipe://mcp-spec` | MCP tool specification format |
| `figrecipe://api/core` | Full API documentation |
