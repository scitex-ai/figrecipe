"""Bundled documentation must resolve its local assets from the real wheel."""

import posixpath
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from hatchling.builders.wheel import WheelBuilder


class _LocalHTMLReferences(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in {"href", "src"} and value:
                self.references.append(value)


def test_generated_docs_assets_resolve_inside_real_wheel(tmp_path):
    # Arrange
    project = Path(__file__).resolve().parents[2]
    prefix = "figrecipe/_sphinx_html/"
    missing = []
    # Act
    wheel = next(WheelBuilder(str(project)).build(directory=str(tmp_path)))
    with zipfile.ZipFile(wheel) as archive:
        members = set(archive.namelist())
        for name in sorted(members):
            if not name.startswith(prefix) or not name.endswith((".html", ".css")):
                continue
            text = archive.read(name).decode("utf-8")
            if name.endswith(".html"):
                parser = _LocalHTMLReferences()
                parser.feed(text)
                references = parser.references
            else:
                references = re.findall(r"url\(\s*['\"]?([^'\")\s]+)", text)
            for reference in references:
                parts = urlsplit(reference)
                if parts.scheme or parts.netloc or not parts.path:
                    continue
                target = posixpath.normpath(
                    posixpath.join(posixpath.dirname(name), unquote(parts.path))
                )
                if parts.path.endswith("/"):
                    target = posixpath.join(target, "index.html")
                if target.startswith(prefix) and target not in members:
                    missing.append((name, reference, target))
    # Assert
    assert missing == [], missing
