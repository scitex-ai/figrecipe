/** Canvas-level caption — "Figure N. Caption text" below each placed figure.
 * Double-click to edit inline. Press Enter or blur to save.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import { useEditorStore } from "../../store/useEditorStore";
import { gettext } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/_base/gettext.ts";

interface Props {
  figureId: string;
  figureIndex: number;
  width: number;
}

export function CaptionOverlay({ figureId, figureIndex, width }: Props) {
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState("");
  const [savedText, setSavedText] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  // Load caption from backend
  useEffect(() => {
    api
      .get<{ figure_caption: string }>("get_captions")
      .then((data) => {
        const caption = data.figure_caption || "";
        setText(caption);
        setSavedText(caption);
      })
      .catch(() => {});
  }, [figureId]);

  const handleSave = useCallback(() => {
    setEditing(false);
    if (text !== savedText) {
      setSavedText(text);
      api
        .post("update_caption", {
          type: "figure",
          figure_number: figureIndex + 1,
          text,
        })
        .catch((e) => {
          console.error("[Caption] save failed:", e);
          useEditorStore.getState().showToast(gettext("Caption save failed"), "error");
        });
    }
  }, [text, savedText, figureIndex]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter") {
        e.preventDefault();
        handleSave();
      }
      if (e.key === "Escape") {
        setText(savedText);
        setEditing(false);
      }
    },
    [handleSave, savedText],
  );

  const handleDoubleClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setEditing(true);
    setTimeout(() => inputRef.current?.focus(), 0);
  }, []);

  const displayText =
    text || `Figure ${figureIndex + 1}. (double-click to add caption)`;
  const isEmpty = !text;

  return (
    <div
      className="caption-overlay"
      style={{ width, maxWidth: width }}
      onDoubleClick={handleDoubleClick}
    >
      {editing ? (
        <input
          ref={inputRef}
          className="caption-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onBlur={handleSave}
          onKeyDown={handleKeyDown}
          placeholder={`Figure ${figureIndex + 1}. Caption text...`}
        />
      ) : (
        <span
          className={`caption-text${isEmpty ? " caption-text--empty" : ""}`}
        >
          {isEmpty ? displayText : `Figure ${figureIndex + 1}. ${text}`}
        </span>
      )}
    </div>
  );
}
