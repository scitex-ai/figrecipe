/** Figure/Panel/Data tab actions share keyboard and pointer behavior. */
import { useEffect, useRef, useState } from "react";
import type { ButtonHTMLAttributes } from "react";
import { createPortal } from "react-dom";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  onRemove: () => void;
  removeLabel: string;
  removalDisabled?: boolean;
}
export function NavigationTab({ onRemove, removeLabel, removalDisabled, children, ...props }: Props) {
  const tab = useRef<HTMLButtonElement>(null);
  const menu = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState<{x: number; y: number} | null>(null);
  useEffect(() => {
    if (!position) return;
    menu.current?.querySelector<HTMLButtonElement>("button")?.focus();
    const dismiss = (event: PointerEvent) => {
      if (!menu.current?.contains(event.target as Node)) setPosition(null);
    };
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape") { event.preventDefault(); setPosition(null); tab.current?.focus(); }
    };
    document.addEventListener("pointerdown", dismiss);
    document.addEventListener("keydown", escape);
    return () => { document.removeEventListener("pointerdown", dismiss); document.removeEventListener("keydown", escape); };
  }, [position]);
  const remove = () => { if (!removalDisabled) onRemove(); setPosition(null); };
  return <span className="editor-nav-item">
    <button {...props} ref={tab} onContextMenu={event => {
      event.preventDefault(); setPosition({x: event.clientX, y: event.clientY});
    }} onKeyDown={event => {
      props.onKeyDown?.(event);
      if (event.key === "ContextMenu" || (event.shiftKey && event.key === "F10")) {
        event.preventDefault(); const rect = event.currentTarget.getBoundingClientRect();
        setPosition({x: rect.left, y: rect.bottom});
      }
    }}>{children}</button>
    <button type="button" className="editor-nav-item__remove" title={removeLabel}
      aria-label={removeLabel} disabled={removalDisabled} onClick={remove}>×</button>
    {position && createPortal(<div ref={menu} role="menu" className="editor-nav-menu"
      style={{left: Math.max(8, Math.min(position.x, window.innerWidth - 240)), top: Math.max(8, Math.min(position.y, window.innerHeight - 60))}}>
      <button type="button" role="menuitem" disabled={removalDisabled} onClick={remove}>{removeLabel}</button>
    </div>, document.body)}
  </span>;
}
