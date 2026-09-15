/** Axes position sub-panel — X, Y, Width, Height in mm. */

import { useCallback, useEffect, useState } from "react";
import { api } from "../../api/client";
import { useEditorStore } from "../../store/useEditorStore";
import { PropSection } from "./PropSection";
import { gettext, interpolate } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/_base/gettext.ts";

interface AxesPosition {
  left: number;
  top: number;
  width: number;
  height: number;
}

export function AxesPositionSection({ axIndex }: { axIndex: number }) {
  const [pos, setPos] = useState<AxesPosition | null>(null);
  const { showToast, loadPreview } = useEditorStore();

  useEffect(() => {
    api
      .get<Record<string, AxesPosition>>("get_axes_positions")
      .then((data) => {
        const key = `ax_${axIndex}`;
        if (data[key]) setPos(data[key]);
      })
      .catch(() => setPos(null));
  }, [axIndex]);

  const updatePosition = useCallback(
    async (field: string, value: number) => {
      if (!pos) return;
      const updated = { ...pos, [field]: value };
      setPos(updated);
      try {
        await api.post("update_axes_position", {
          ax_index: axIndex,
          ...updated,
        });
        loadPreview();
      } catch (e) {
        showToast(interpolate(gettext("Position update failed: %s"), [e]), "error");
      }
    },
    [axIndex, pos, loadPreview, showToast],
  );

  if (!pos) return null;

  return (
    <PropSection title={gettext("Position (mm)")}>
      <div className="property-row">
        <div className="property-group">
          <span className="property-label">X</span>
          <input
            className="property-input"
            type="number"
            step="0.5"
            value={pos.left.toFixed(1)}
            onChange={(e) => updatePosition("left", Number(e.target.value))}
          />
        </div>
        <div className="property-group">
          <span className="property-label">Y</span>
          <input
            className="property-input"
            type="number"
            step="0.5"
            value={pos.top.toFixed(1)}
            onChange={(e) => updatePosition("top", Number(e.target.value))}
          />
        </div>
      </div>
      <div className="property-row">
        <div className="property-group">
          <span className="property-label">{gettext("W")}</span>
          <input
            className="property-input"
            type="number"
            step="0.5"
            value={pos.width.toFixed(1)}
            onChange={(e) => updatePosition("width", Number(e.target.value))}
          />
        </div>
        <div className="property-group">
          <span className="property-label">{gettext("H")}</span>
          <input
            className="property-input"
            type="number"
            step="0.5"
            value={pos.height.toFixed(1)}
            onChange={(e) => updatePosition("height", Number(e.target.value))}
          />
        </div>
      </div>
    </PropSection>
  );
}
