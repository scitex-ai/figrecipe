# Quickstart diagram provenance

The two previously missing quickstart diagrams are generated demonstration
images, not experimental results. They were rendered from
`docs/sphinx/generate_images.py::generate_quickstart_images` at commit
`85ef57de130c81b15ad6943bd5a985f1a06513c0`. Only the absent LR and TB PNGs were
copied into `docs/sphinx/generate_images_out`; the thirteen existing targets
were preserved. All fifteen `_static` links must point to tracked regular PNGs.

The source generator requires `scitex` for its session wrapper in addition to
FigRecipe's documentation/scitex extras. The qualified isolated install was:

```bash
pip install -e '.[docs,scitex]' scitex
```

To render into disposable output without rewriting the source `_static` links:

```python
import importlib.util
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "documentation_images", Path("docs/sphinx/generate_images.py")
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
output = Path(tempfile.mkdtemp(prefix="figrecipe-doc-images-"))
module.generate_quickstart_images(output)
```

This calls the existing generator directly; its session `main` and
`symlink_to_static` functions are not invoked. The normal CLI intentionally
updates source symlinks and is a different operation.

The recorded rendering environment used `numpy==2.5.4`, `matplotlib==3.11.2`, `scitex==2.29.3`, `scitex-sdk==0.3.17`, `scitex-logging==0.2.4`.
Matplotlib selected Liberation Sans because Arial was unavailable. These exact
PNG bytes are tracked; regeneration with different fonts or versions can differ.

| Image | Dimensions | SHA256 |
| --- | --- | --- |
| `quickstart_diagram_lr.png` | 2149 × 1274 | `3cf2d77b0f9c611c167a83706f79728624ae551bf6cddc865842f44140b5abea` |
| `quickstart_diagram_tb.png` | 1795 × 2976 | `a2c536e1c0fd736551354cb8bfb006f1ff6f4381ea851a08890ab1ce56bf72e1` |
