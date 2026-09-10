/** Right pane — Properties/Details with vis_app pane-header. */

import { useEditorStore } from "../../store/useEditorStore";
import { Properties } from "../Properties/Properties";

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
          title={collapsed ? "Expand details" : "Collapse details"}
          aria-label={collapsed ? "Expand details" : "Collapse details"}
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
          Details
        </span>

        {/* Selected type badge */}
        {selectedElement && selectedBbox?.type && (
          <span className="badge badge-type">{selectedBbox.type}</span>
        )}

        {/* Vertical title (visible only when collapsed via CSS) */}
        <span className="panel-title">
          <i className="fas fa-sliders-h" />
          Details
        </span>
      </div>

      {/* Pane content */}
      <div className="pane-content">
        <Properties />
      </div>
    </>
  );
}
