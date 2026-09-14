/** Export dialog — modal with format, filename, and DPI selection. */

import { useCallback, useEffect, useState } from "react";
import { api } from "../../api/client";
import { buildExportPayload } from "../../store/persistActions";
import { useEditorStore } from "../../store/useEditorStore";
import { gettext, gettext_noop, interpolate } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/_base/gettext.ts";

interface Props {
  onClose: () => void;
}

const FORMATS = [
  {
    id: "png",
    label: "PNG",
    icon: "fas fa-file-image",
    hint: gettext_noop("Raster (300 DPI)"),
  },
  { id: "svg", label: "SVG", icon: "fas fa-file-code", hint: gettext_noop("Vector") },
  { id: "pdf", label: "PDF", icon: "fas fa-file-pdf", hint: gettext_noop("Print-ready") },
];

export function ExportDialog({ onClose }: Props) {
  const showToast = useEditorStore((s) => s.showToast);
  const placedFigures = useEditorStore((s) => s.placedFigures);
  const workingDir = useEditorStore((s) => s.workingDir);
  const darkMode = useEditorStore((s) => s.darkMode);
  const [format, setFormat] = useState("png");
  const [filename, setFilename] = useState("composed");
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [onClose]);

  const handleExport = useCallback(async () => {
    setExporting(true);
    try {
      let blob: Blob;
      if (placedFigures.length > 0) {
        const payload = buildExportPayload(
          placedFigures,
          workingDir,
          darkMode,
          filename,
        );
        blob = await api.postBlob(`api/compose/export/${format}`, payload);
      } else {
        blob = await api.getBlob(`download/${format}`);
      }
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${filename}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
      showToast(interpolate(gettext("Exported %s"), [filename + "." + format]), "success");
      onClose();
    } catch (e) {
      showToast(interpolate(gettext("Export failed: %s"), [e]), "error");
    } finally {
      setExporting(false);
    }
  }, [
    format,
    filename,
    showToast,
    onClose,
    placedFigures,
    workingDir,
    darkMode,
  ]);

  return (
    <div className="gallery-overlay" onMouseDown={onClose}>
      <div className="export-dialog" onMouseDown={(e) => e.stopPropagation()}>
        <div className="gallery-header">
          <h3>
            <i className="fas fa-download" /> {gettext("Export Figure")}
          </h3>
          <button className="gallery-close" onClick={onClose} type="button" aria-label={gettext("Close")}>
            <i className="fas fa-times" />
          </button>
        </div>

        <div className="export-body">
          <label className="export-field">
            <span className="export-label">{gettext("Filename")}</span>
            <input
              type="text"
              className="export-input"
              value={filename}
              onChange={(e) => setFilename(e.target.value)}
              placeholder="figure"
            />
          </label>

          <div className="export-field">
            <span className="export-label">{gettext("Format")}</span>
            <div className="export-formats">
              {FORMATS.map((fmt) => (
                <button
                  key={fmt.id}
                  className={`export-format-btn${format === fmt.id ? " active" : ""}`}
                  onClick={() => setFormat(fmt.id)}
                  type="button"
                >
                  <i className={fmt.icon} />
                  <span className="export-format-label">{fmt.label}</span>
                  <span className="export-format-hint">{gettext(fmt.hint)}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="export-footer">
          <button className="export-cancel-btn" onClick={onClose} type="button">
            {gettext("Cancel")}
          </button>
          <button
            className="export-confirm-btn"
            onClick={handleExport}
            disabled={exporting || !filename.trim()}
            type="button"
          >
            {exporting ? (
              <>
                <i className="fas fa-spinner fa-spin" /> {gettext("Exporting…")}
              </>
            ) : (
              <>
                <i className="fas fa-download" /> {interpolate(gettext("Export %s"), [format.toUpperCase()])}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
