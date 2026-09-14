/** Legend sub-panel — visibility toggle and location dropdown. */

import { useCallback, useEffect, useState } from "react";
import { api } from "../../api/client";
import { useEditorStore } from "../../store/useEditorStore";
import { PropRow } from "./PropRow";
import { PropSection } from "./PropSection";
import { gettext, gettext_noop, interpolate } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/_base/gettext.ts";

interface LegendInfo {
  has_legend: boolean;
  visible: boolean;
  loc: string;
}

const LEGEND_LOCATIONS = [
  { label: gettext_noop("Best"), value: "best" },
  { label: gettext_noop("Upper Right"), value: "upper right" },
  { label: gettext_noop("Upper Left"), value: "upper left" },
  { label: gettext_noop("Lower Left"), value: "lower left" },
  { label: gettext_noop("Lower Right"), value: "lower right" },
  { label: gettext_noop("Right"), value: "right" },
  { label: gettext_noop("Center Left"), value: "center left" },
  { label: gettext_noop("Center Right"), value: "center right" },
  { label: gettext_noop("Lower Center"), value: "lower center" },
  { label: gettext_noop("Upper Center"), value: "upper center" },
  { label: gettext_noop("Center"), value: "center" },
];

export function LegendSection({ axIndex }: { axIndex: number }) {
  const [info, setInfo] = useState<LegendInfo | null>(null);
  const { showToast, loadPreview } = useEditorStore();

  useEffect(() => {
    api
      .get<LegendInfo>(`get_legend_info?ax_index=${axIndex}`)
      .then(setInfo)
      .catch(() => setInfo(null));
  }, [axIndex]);

  const updateLegend = useCallback(
    async (updates: Record<string, unknown>) => {
      try {
        await api.post("update_legend_position", {
          ax_index: axIndex,
          ...updates,
        });
        loadPreview();
      } catch (e) {
        showToast(interpolate(gettext("Legend update failed: %s"), [e]), "error");
      }
    },
    [axIndex, loadPreview, showToast],
  );

  if (!info?.has_legend) return null;

  return (
    <PropSection title={gettext("Legend")} defaultOpen={false}>
      <PropRow
        label={gettext("Visible")}
        value={info.visible}
        editable
        type="checkbox"
        onChange={(v) => updateLegend({ visible: v })}
      />
      <PropRow
        label={gettext("Location")}
        value={info.loc}
        editable
        type="select"
        options={LEGEND_LOCATIONS.map((option) => ({ ...option, label: gettext(option.label) }))}
        onChange={(v) => updateLegend({ loc: v })}
      />
    </PropSection>
  );
}
