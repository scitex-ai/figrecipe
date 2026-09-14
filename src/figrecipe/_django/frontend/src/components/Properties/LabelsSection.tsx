/** Labels sub-panel — editable title, xlabel, ylabel for an axes. */

import { useCallback } from "react";
import { api } from "../../api/client";
import { useEditorStore } from "../../store/useEditorStore";
import { DebouncedInput } from "./DebouncedInput";
import { PropSection } from "./PropSection";
import { gettext, interpolate } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/_base/gettext.ts";

export function LabelsSection({ axIndex }: { axIndex: number }) {
  const labelsMap = useEditorStore((s) => s.labels);
  const showToast = useEditorStore((s) => s.showToast);
  const refreshAfterMutation = useEditorStore((s) => s.refreshAfterMutation);
  const loadLabels = useEditorStore((s) => s.loadLabels);

  const labels = labelsMap[String(axIndex)] ?? null;

  const updateLabel = useCallback(
    async (labelType: string, text: string) => {
      try {
        await api.post("update_label", {
          label_type: labelType,
          text,
          ax_index: axIndex,
        });
        refreshAfterMutation();
        loadLabels(axIndex);
      } catch (e) {
        showToast(interpolate(gettext("Label update failed: %s"), [e]), "error");
      }
    },
    [axIndex, refreshAfterMutation, loadLabels, showToast],
  );

  if (!labels) return null;

  return (
    <PropSection title={gettext("Labels")}>
      <DebouncedInput
        label={gettext("Title")}
        value={labels.title}
        onCommit={(v) => updateLabel("title", v)}
      />
      <DebouncedInput
        label={gettext("X Label")}
        value={labels.xlabel}
        onCommit={(v) => updateLabel("xlabel", v)}
      />
      <DebouncedInput
        label={gettext("Y Label")}
        value={labels.ylabel}
        onCommit={(v) => updateLabel("ylabel", v)}
      />
    </PropSection>
  );
}
