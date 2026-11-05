/** Yield to a server-declared SDK header, or use the SDK React binding in the SPA. */
import { useLayoutEffect, useState } from "react";
import type { ReactNode } from "react";
import { createPortal } from "react-dom";
import { AppHeader } from "@scitex/sdk/ui/react/app/app-header";
import { mountAppHeader } from "@scitex/sdk/ui/ts/app/app-header/mount.ts";

interface Props { title: string; version?: string; projectSelector: ReactNode }

export function EditorAppHeader({ title, version, projectSelector }: Props) {
  const serverRoot = document.querySelector<HTMLElement>("[data-figrecipe-header]");
  const legacySlot = document.querySelector<HTMLElement>(
    "header[data-ssot] .stx-app-header__slot--project-selector",
  );
  const [slot, setSlot] = useState<HTMLElement | null>(legacySlot);
  useLayoutEffect(() => {
    if (!serverRoot) return;
    // The server owns this row's lifetime. Never destroy it on a React unmount.
    // Idempotent if host auto-mount or a StrictMode effect already mounted it.
    const region = serverRoot.closest("[data-figrecipe-header-region]");
    if (region) mountAppHeader(region, { projectSlot: true });
    setSlot(serverRoot.querySelector<HTMLElement>(".stx-app-header__slot--project-selector"));
  }, [serverRoot]);
  if (serverRoot || legacySlot) return slot ? createPortal(projectSelector, slot) : null;
  return <AppHeader title={title} version={version} projectSelector={projectSelector} />;
}
