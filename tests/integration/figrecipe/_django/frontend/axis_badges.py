"""Local SDK React regression; no application, server, credentials or requests.

Build tests/axisBadges.fixture.tsx with the existing frontend esbuild binary;
pass --bundle-root for those JS/CSS bytes and --chromium for an installed browser.
"""

import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-root", type=Path, required=True)
    parser.add_argument("--chromium", type=Path, required=True)
    arguments = parser.parse_args()
    root = arguments.bundle_root.resolve()
    result = {
        "actual_sdk_react_table": True,
        "local_synthetic_fixture_only": True,
        "app_requests": [],
        "errors": [],
    }
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=str(arguments.chromium), headless=True
        )
        context = browser.new_context(
            viewport={"width": 800, "height": 500}, service_workers="block"
        )
        context.route(
            "**/*",
            lambda route: (
                result["app_requests"].append(route.request.method),
                route.abort(),
            ),
        )
        page = context.new_page()
        page.on(
            "pageerror", lambda error: result["errors"].append(type(error).__name__)
        )
        page.set_content(
            "<html><head><style>:root{--stx-app-accent:transparent;--accent-primary:#7c5cbf;--status-success:#6ba89a;--text-primary:#222;--workspace-bg-elevated:#eee;--workspace-border-default:#bbb;--workspace-border-subtle:#ddd}[data-theme=dark]{--text-primary:#eee;--workspace-bg-elevated:#222}body{font-family:sans-serif}#root{height:320px;width:500px}</style><style>"
            + (root / "axis-fixture.css").read_text()
            + '</style></head><body><div class="data-pane__content"><div id="root"></div></div><script>'
            + (root / "axis-fixture.js").read_text()
            + "</script></body></html>"
        )
        page.locator('th[data-col="1"]').wait_for(timeout=5000)
        page.evaluate("axisFixture.apply()")
        metrics = page.evaluate(
            """()=>[...document.querySelectorAll('th[data-col]')].map(n=>({name:n.textContent,label:n.dataset.colAxisLabel,aria:n.getAttribute('aria-label'),content:getComputedStyle(n,'::after').content,border:getComputedStyle(n,'::after').borderTopWidth,margin:getComputedStyle(n,'::after').marginInlineStart,children:n.children.length}))"""
        )
        assert [m["name"] for m in metrics] == ["x", "y"], metrics
        assert [m["content"] for m in metrics] == ['"X axis"', '"Y axis"'], metrics
        assert all(m["border"] == "1px" and m["children"] == 2 for m in metrics), (
            metrics
        )
        result["initial"] = metrics
        page.screenshot(path=str(root / "axis-badges-desktop.png"))
        page.set_viewport_size({"width": 390, "height": 500})
        page.screenshot(path=str(root / "axis-badges-phone.png"))
        page.locator('th[data-col="0"] > span').click()
        assert page.locator('td[data-row="0"][data-col="0"]').inner_text() == "1"
        result["sorting"] = True
        visible_foregrounds = []
        for theme in ["light", "dark"]:
            page.evaluate(
                "theme => document.documentElement.dataset.theme = theme", theme
            )
            for width in [800, 390]:
                page.set_viewport_size({"width": width, "height": 500})
                color = page.locator('th[data-col="0"] > span').evaluate(
                    "n => getComputedStyle(n).color"
                )
                assert color not in ["transparent", "rgba(0, 0, 0, 0)"], color
                visible_foregrounds.append(
                    {"theme": theme, "width": width, "color": color}
                )
        result["sorted_foregrounds"] = visible_foregrounds
        page.evaluate("document.documentElement.dataset.theme = 'light'")
        handle = page.locator('th[data-col="0"] .stx-app-data-table__resize-handle')
        before = page.locator('th[data-col="0"]').bounding_box()["width"]
        box = handle.bounding_box()
        page.mouse.move(box["x"] + 0.5, box["y"] + box["height"] / 2)
        page.mouse.down()
        page.mouse.move(box["x"] + 55, box["y"] + box["height"] / 2, steps=5)
        page.mouse.up()
        page.wait_for_timeout(50)
        after = page.locator('th[data-col="0"]').bounding_box()["width"]
        assert after > before, (before, after)
        result["resizing"] = {"before": before, "after": after}
        cell = page.locator('td[data-row="0"][data-col="0"]')
        cell.click()
        assert "selected" in cell.get_attribute("class")
        result["selection"] = True
        cell.dblclick()
        edit = page.locator("input.stx-app-data-table__edit-input")
        edit.fill("7")
        edit.press("Enter")
        page.wait_for_function("axisFixture.changes.length > 0", timeout=5000)
        assert page.evaluate("axisFixture.changes.at(-1).rows.some(r=>r.x===7)")
        result["editing"] = True
        page.evaluate('axisFixture.apply({x:"横軸",y:"縦軸"})')
        assert (
            page.locator('th[data-col="0"]').get_attribute("data-col-axis-label")
            == "横軸"
        )
        result["localized"] = True
        page.evaluate("axisFixture.longNames()")
        page.wait_for_function(
            "document.querySelector('th[data-col=\"0\"] span')?.textContent==='measurement_time_seconds'",
            timeout=5000,
        )
        page.evaluate('axisFixture.apply({x:"横軸",y:"縦軸"})')
        page.locator('th[data-col="0"] > span').click()
        long_span = page.locator('th[data-col="0"] > span')
        assert long_span.text_content() == "measurement_time_seconds"
        assert (
            long_span.evaluate("n => getComputedStyle(n).color") != "rgba(0, 0, 0, 0)"
        )
        result["long_sorted_name_preserved"] = True
        page.evaluate("axisFixture.clear()")
        assert page.locator("[data-col-axis-label]").count() == 0
        assert page.locator('th[data-col="0"]').get_attribute("aria-label") is None
        result["clear_restores_labels"] = True
        assert not result["errors"] and not result["app_requests"], result
        context.close()
        browser.close()
    result["passed"] = True
    (root / "browser-proof.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
