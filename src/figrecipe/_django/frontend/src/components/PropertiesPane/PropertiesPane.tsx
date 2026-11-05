/** Right pane — Objects tree above Details, with vis_app pane-header. */

import { useEditorStore } from "../../store/useEditorStore";
import { ObjectTree } from "../ObjectTree/ObjectTree";
import { Properties } from "../Properties/Properties";
import { gettext } from "@scitex/sdk/ui/ts/_base/gettext.ts";

interface PropertiesPaneProps {
  onToggleCollapse?: () => void;
  collapsed?: boolean;
}

export function PropertiesPane({
  onToggleCollapse,
  collapsed,
}: PropertiesPaneProps) {
  const { selectedElement, selectedBbox } = useEditorStore();

  return (
    <>
      {/* vis_app .pane-header */}
      <div className="pane-header">
        {/* Explicit collapse/expand control — a visible button, not a
            double-click gesture. Right panel: chevron points out when
            expanded (collapse), in when collapsed (expand). */}
        <button
          className="pane-header-btn panel-toggle-btn"
          type="button"
          onClick={onToggleCollapse}
          title={collapsed ? gettext("Expand details") : gettext("Collapse details")}
          aria-label={collapsed ? gettext("Expand details") : gettext("Collapse details")}
        >
          <i
            className={`fas ${
              collapsed ? "fa-chevron-left" : "fa-chevron-right"
            }`}
          />
        </button>

        {/* Details title */}
        <span className="pane-header-title">
          <i className="fas fa-sliders-h" />
          {gettext("Details")}
        </span>

        {/* Selected type badge */}
        {selectedElement && selectedBbox?.type && (
          <span className="badge badge-type">{selectedBbox.type}</span>
        )}

        {/* Vertical title (visible only when collapsed via CSS) */}
        <span className="panel-title">
          <i className="fas fa-sliders-h" />
          {gettext("Details")}
        </span>
      </div>

      {/* Pane content — the tree stays visible so Details never opens on a
          dead "select from the tree" with no tree on screen. The tree
          itself carries no Data door (operator checklist 2026-10-24):
          the model rows above own the one canonical way in. */}
      <div className="pane-content">
        <ObjectTree />
        <Properties />
      </div>
    </>
  );
}
