/** Left pane — Data table with vis_app pane-header.
 * Uses scitex-ui's shared DataTable component (no figrecipe-original table).
 *
 * The pane also owns two things the shared table cannot: the X/Y badge ↔ table
 * column highlight, and row/column CRUD with an undo stack (deletions must never
 * be irreversible). Both policies live in the React-free sibling modules so they
 * are testable under `node --experimental-strip-types`. */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { DataTable } from "@scitex/ui/src/scitex_ui/static/scitex_ui/react/app/data-table/DataTable";
import { api } from "../../api/client";
import { useEditorStore } from "../../store/useEditorStore";
import { getPanelColor } from "../../utils/panelColors";
import { PlotFromColumns } from "./PlotFromColumns";
import {
  badgeColumnHighlights,
  columnNameAt,
  sameBadge,
  selectionAfterColumnClick,
  type HoverBadge,
} from "./dataColumnHighlight";
import type { ColumnSelection } from "./columnPlotSelection";
import {
  addColumn,
  affectedAssignmentLabel,
  applyRedo,
  applyUndo,
  assignmentImpact,
  cloneSelection,
  cloneTable,
  datasetFromTable,
  deleteColumnAt,
  deleteRowsAt,
  diffTable,
  duplicateColumnAt,
  findRowIndexByValues,
  insertRowAt,
  planColumnDelete,
  pushUndo,
  renameColumnAt,
  rowValuesAt,
  serializeTableToCsv,
  tableFromDataset,
  type RedoEntry,
  type TableDataset,
  type TableModel,
  type TableOp,
  type UndoEntry,
} from "./dataTableEdit";
import {
  applyColumnHighlight,
  readRowValues,
  readSelectedCells,
  renderedColumnNodes,
  type ColumnRoleWords,
} from "./dataTableDom";
import {
  createTableSaveQueue,
  type TableSaveQueue,
} from "./tableSaveQueue";
import { gettext, ngettext, interpolate } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/_base/gettext.ts";

interface DataTablePaneProps {
  onToggleCollapse?: () => void;
  collapsed?: boolean;
}

/** User-facing name of an edit. Doubles as the undo entry's label and as the
 * confirmation toast, so an undone change reads back in the same words. */
function opLabel(op: TableOp): string {
  switch (op.kind) {
    case "delete-rows":
      return op.rowNumbers.length === 1
        ? interpolate(gettext("Delete row %s"), [op.rowNumbers[0]])
        : interpolate(
            ngettext("Delete %s row", "Delete %s rows", op.rowNumbers.length),
            [op.rowNumbers.length],
          );
    case "delete-column":
      return interpolate(gettext("Delete column '%s'"), [op.columnName]);
    case "insert-row":
      return interpolate(gettext("Add row %s"), [op.rowNumber]);
    case "add-column":
      return interpolate(gettext("Add column '%s'"), [op.columnName]);
    case "duplicate-column":
      return interpolate(gettext("Duplicate column '%s' as '%s'"), [
        op.columnName,
        op.newName,
      ]);
    case "clear-cells":
      return interpolate(
        ngettext("Clear %s cell", "Clear %s cells", op.count),
        [op.count],
      );
    case "edit-cells":
      return op.count === 1 && op.columnName && op.rowNumber !== null
        ? interpolate(gettext("Edit %s in row %s"), [op.columnName, op.rowNumber])
        : interpolate(ngettext("Edit %s cell", "Edit %s cells", op.count), [
            op.count,
          ]);
    case "rename-column":
      return interpolate(gettext("Rename column '%s' to '%s'"), [
        op.from,
        op.to,
      ]);
    case "set-table":
      return gettext("Edit table");
  }
}

/** The badge under the pointer, whatever element inside it the pointer hit.
 *  Badges tag themselves with data-column/data-role (see PlotFromColumns). */
function badgeFromTarget(target: EventTarget | null): HoverBadge | null {
  if (!(target instanceof Element)) return null;
  const badge = target.closest("[data-column][data-role]");
  if (!badge) return null;
  const name = badge.getAttribute("data-column");
  const role = badge.getAttribute("data-role");
  if (!name || (role !== "x" && role !== "y")) return null;
  return { name, role };
}

export function DataTablePane({ onToggleCollapse, collapsed }: DataTablePaneProps) {
  const {
    datatableTabs,
    activeTabId,
    highlightedDataRows: _highlightedDataRows,
    placedFigures,
    removeFigure,
    showToast,
    loadDatatable,
    refreshAfterMutation,
  } = useEditorStore();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  /** Whether the last interaction landed in this pane — see the Ctrl+Z effect. */
  const paneInteractionRef = useRef(false);

  /** Badge state mirrored up from PlotFromColumns: which table columns the pane
   *  has to highlight. */
  const [badgeSelection, setBadgeSelection] = useState<ColumnSelection>({
    x: null,
    ys: [],
  });
  /** A click on a table column, handed down to the badges. */
  const [columnCommand, setColumnCommand] = useState<{
    name: string;
    nonce: number;
  } | null>(null);
  /** A binding restored from history, handed down to the badges. Undo/redo move
   *  the table and its X/Y binding in one transition, so the form is given the
   *  whole binding and applies it in the same commit as the table. */
  const [selectionCommand, setSelectionCommand] = useState<{
    selection: ColumnSelection;
    nonce: number;
  } | null>(null);
  const [hoverBadge, setHoverBadge] = useState<HoverBadge | null>(null);
  /** The table's own selection: the row numbers are the order the table
   *  currently shows, which is not the model's order once it is sorted. */
  const [selectedCell, setSelectedCell] = useState<{
    row: number;
    col: number;
  } | null>(null);
  const [undoStack, setUndoStack] = useState<UndoEntry[]>([]);
  /** The forward half of the history: every undo parks the state it undid here
   *  so it can be redone (operator acceptance 7692 requires undo AND redo). */
  const [redoStack, setRedoStack] = useState<RedoEntry[]>([]);
  const [renameDraft, setRenameDraft] = useState<string | null>(null);
  /** A delete that needs the user's word first: the last column, or one that is
   *  currently bound to the plot (the binding is cleared with it, so the user is
   *  told which assignment the delete affects — operator acceptance 7692). */
  const [confirmColumnDelete, setConfirmColumnDelete] = useState<{
    name: string;
    /** "X", "Y", "X and Y", or null when the delete touches no assignment. */
    assignment: string | null;
    /** Deleting would leave the table with no columns at all. */
    last: boolean;
  } | null>(null);

  const tabs = Object.values(datatableTabs);
  const activeTab = activeTabId ? datatableTabs[activeTabId] : null;

  console.log(
    "[DataTablePane] tabs:",
    tabs.length,
    "activeTabId:",
    activeTabId,
    "activeTab:",
    activeTab
      ? { cols: activeTab.columns?.length, rows: activeTab.rows?.length }
      : null,
  );

  /** The pane's table-model reads: an import, a plot or a tab switch replaces
   *  the tab object, and a captured one would edit a table that is no longer on
   *  screen. */
  const currentTable = useCallback((): TableModel | null => {
    const state = useEditorStore.getState();
    const tab = state.activeTabId
      ? state.datatableTabs[state.activeTabId]
      : null;
    return tab ? { columns: tab.columns, rows: tab.rows } : null;
  }, []);

  /** The write path for every table edit: one save in flight, edits coalesced to
   *  the newest, and a revision gate on adopting the server's state. The queue is
   *  created once per pane (see tableSaveQueue.ts). */
  const saveQueue = useRef<TableSaveQueue>(
    createTableSaveQueue(async (csv: string) => {
      await api.post("datatable/import", { content: csv, format: "csv" });
    }),
  ).current;

  /** Write the pane's model back into the store — the table, the badges and the
   *  plot form all read the same tab. */
  const writeTable = useCallback((next: TableModel) => {
    useEditorStore.setState((state) => {
      const id = state.activeTabId;
      const tab = id ? state.datatableTabs[id] : null;
      if (!id || !tab) return {};
      return {
        datatableTabs: {
          ...state.datatableTabs,
          [id]: { ...tab, columns: next.columns, rows: next.rows },
        },
      };
    });
  }, []);

  /** Persist through the leaf's own write path: datatable/import replaces the
   *  stored table, then the reload shows what the backend actually kept.
   *
   *  Every edit goes through the save queue, which keeps ONE write in flight and
   *  coalesces the edits that arrive meanwhile to the newest one — overlapping
   *  POSTs used to let a stale response decide the stored table. A completion
   *  may only be adopted (reload + toast) when no newer edit has been handed
   *  over; a superseded save stays silent because the newer edit speaks for the
   *  table. */
  const persistTable = useCallback(
    async (table: TableModel, message: string) => {
      const outcome = await saveQueue.enqueue(serializeTableToCsv(table));
      if (outcome.status === "failed") {
        // The edit stays on screen: a failed save must not also throw away what
        // the user just changed. The error toast is the fail-loud signal.
        showToast(interpolate(gettext("Save failed: %s"), [outcome.error]), "error");
        return;
      }
      // A newer edit is already queued, and ITS completion is what may adopt the
      // server's state. Reloading here would put the older table back on screen.
      if (outcome.status !== "applied") return;
      const revision = outcome.revision;
      try {
        // `isCurrent` covers the read itself: an edit that lands while this
        // reload is in flight must not be overwritten by the older server copy.
        await loadDatatable({ isCurrent: () => saveQueue.revision === revision });
        await refreshAfterMutation();
        showToast(message, "success");
      } catch (e) {
        showToast(interpolate(gettext("Save failed: %s"), [e]), "error");
      }
    },
    [loadDatatable, refreshAfterMutation, saveQueue, showToast],
  );

  /** The single write path for every edit: snapshot for undo, update the model,
   *  then persist. The snapshot carries the plot assignment too, so undoing a
   *  delete that cleared an X/Y binding brings the binding back with the table. */
  const applyEdit = useCallback(
    (next: TableModel, op: TableOp) => {
      const table = currentTable();
      if (!table) {
        showToast(gettext("No data table to edit"), "error");
        return;
      }
      const label = opLabel(op);
      setUndoStack((stack) =>
        pushUndo(stack, {
          label,
          op,
          snapshot: cloneTable(table),
          assignment: cloneSelection(badgeSelection),
        }),
      );
      // A fresh edit invalidates the redo branch: the states parked there no
      // longer follow from what is on screen, so offering them would apply an
      // edit the user cannot predict.
      setRedoStack([]);
      writeTable(next);
      void persistTable(next, label);
    },
    [badgeSelection, currentTable, persistTable, showToast, writeTable],
  );

  /** The shared table edits itself (double-click a cell, rename a header, paste,
   *  its own context-menu clear); adopt what it reports as an edit like any
   *  other, undo entry included. */
  const handleDataChange = useCallback(
    (dataset: TableDataset) => {
      const table = currentTable();
      // With no tab the table is showing its own starter grid, which is not the
      // user's data and must never be adopted.
      if (!table) return;
      const next = tableFromDataset(dataset, table);
      const op = diffTable(table, next);
      // Echo of a write the pane just made: adopting it would stack a second
      // undo entry for one change.
      if (!op) return;
      applyEdit(next, op);
    },
    [applyEdit, currentTable],
  );

  /** Clicking a table column pushes the badge state into the form. */
  const selectColumn = useCallback((name: string) => {
    setBadgeSelection((s) => selectionAfterColumnClick(s, name));
    setColumnCommand((c) => ({ name, nonce: (c?.nonce ?? 0) + 1 }));
  }, []);

  const handleCellSelect = useCallback(
    (position: { row: number; col: number }) => {
      setSelectedCell(position);
      const table = currentTable();
      const name = table ? columnNameAt(table.columns, position.col) : null;
      if (name) selectColumn(name);
    },
    [currentTable, selectColumn],
  );

  /** Header clicks reach the pane by delegation: the shared table keeps the
   *  header's own handler to itself (it sorts), and exposes no callback. */
  const handleContentClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!(e.target instanceof Element)) return;
      const header = e.target.closest("th[data-col]");
      if (!header) return;
      const table = currentTable();
      if (!table) return;
      const rawIndex = header.getAttribute("data-col");
      const name = columnNameAt(
        table.columns,
        rawIndex === null ? NaN : Number(rawIndex),
      );
      if (name) selectColumn(name);
    },
    [currentTable, selectColumn],
  );

  /** Hovering a badge previews its column; leaving clears the preview. */
  const handlePointerOver = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const next = badgeFromTarget(e.target);
      // Same badge, same render: the pointer moves across a chip's text and
      // padding many times per second.
      setHoverBadge((prev) => (sameBadge(prev, next) ? prev : next));
    },
    [],
  );

  const handlePointerOut = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const next = badgeFromTarget(e.relatedTarget);
      setHoverBadge((prev) => (sameBadge(prev, next) ? prev : next));
    },
    [],
  );

  const highlights = useMemo(
    () => badgeColumnHighlights(activeTab?.columns ?? [], badgeSelection, hoverBadge),
    [activeTab?.columns, badgeSelection, hoverBadge],
  );

  /** The X/Y role words the highlighted columns announce. Built here, not in
   *  dataTableDom: the copy belongs with the rest of the pane's gettext text,
   *  and the module stays free of the i18n layer (accessibility was previously
   *  the CSS `::after` letter alone, which no screen reader reads out). */
  const roleWords = useMemo<ColumnRoleWords>(
    () => ({ x: gettext("X column"), y: gettext("Y column") }),
    [],
  );

  // The shared table re-renders its own className, which drops anything stamped
  // on it, so the highlight is re-applied after every commit here and whenever
  // the table's DOM changes underneath (sorting, virtual scrolling).
  useEffect(() => {
    const root = contentRef.current;
    if (!root) return;
    const sync = () =>
      applyColumnHighlight(renderedColumnNodes(root), highlights, roleWords);
    sync();
    const observer = new MutationObserver(sync);
    // childList only: the applier writes classes/attributes, and observing those
    // would make it trigger itself.
    observer.observe(root, { childList: true, subtree: true });
    return () => observer.disconnect();
  }, [highlights, roleWords]);

  // A different tab is a different table: the old selection and the undo
  // history no longer describe what is on screen.
  useEffect(() => {
    setSelectedCell(null);
    setUndoStack([]);
    setRedoStack([]);
    setRenameDraft(null);
    setConfirmColumnDelete(null);
  }, [activeTabId]);

  /** Model rows the table currently has selected, resolved by value: a sorted
   *  table's row numbers are its own view order. Refuses as a whole ([]) when a
   *  row cannot be identified, because a partial delete is worse than none. */
  const selectedModelRows = useCallback((): number[] => {
    const table = currentTable();
    const root = contentRef.current;
    if (!table || !root) return [];
    const nodes = renderedColumnNodes(root);
    const domRows = Array.from(
      new Set(readSelectedCells(nodes).map((cell) => cell.row)),
    );
    const rowIndexes = domRows.length > 0 ? domRows : selectedCell ? [selectedCell.row] : [];
    const resolved: number[] = [];
    for (const domRow of rowIndexes) {
      const rendered = readRowValues(nodes, domRow);
      const values =
        rendered.length > 0 ? rendered : rowValuesAt(table, domRow);
      const index = findRowIndexByValues(table, values, domRow);
      if (index < 0) return [];
      resolved.push(index);
    }
    return resolved;
  }, [currentTable, selectedCell]);

  const handleAddRow = useCallback(() => {
    const table = currentTable();
    if (!table) {
      showToast(gettext("No data table to edit"), "error");
      return;
    }
    // Insert below the row in play so "add" lands where the user is looking;
    // with nothing selected it appends.
    const rows = selectedModelRows();
    const at = rows.length > 0 ? Math.max(...rows) + 1 : table.rows.length;
    applyEdit(insertRowAt(table, at), { kind: "insert-row", rowNumber: at + 1 });
  }, [applyEdit, currentTable, selectedModelRows, showToast]);

  const handleDeleteRow = useCallback(() => {
    const table = currentTable();
    if (!table) {
      showToast(gettext("No data table to edit"), "error");
      return;
    }
    const rows = selectedModelRows();
    if (rows.length === 0) {
      showToast(gettext("Select a row to delete"), "error");
      return;
    }
    setSelectedCell(null);
    applyEdit(deleteRowsAt(table, rows), {
      kind: "delete-rows",
      rowNumbers: rows.map((row) => row + 1).sort((a, b) => a - b),
    });
  }, [applyEdit, currentTable, selectedModelRows, showToast]);

  const handleAddColumn = useCallback(() => {
    const table = currentTable();
    if (!table) {
      showToast(gettext("No data table to edit"), "error");
      return;
    }
    // "column" is a default name, not copy: it is saved into the table as data.
    const next = addColumn(table, "column");
    const added = next.columns[next.columns.length - 1];
    if (!added) return;
    applyEdit(next, { kind: "add-column", columnName: added.name });
  }, [applyEdit, currentTable, showToast]);

  /** The column the column-actions work on: the table cell in play, else the
   *  column the badges already point at. */
  const activeColumnName = useMemo(() => {
    if (!activeTab) return null;
    const fromCell = selectedCell
      ? columnNameAt(activeTab.columns, selectedCell.col)
      : null;
    return fromCell ?? badgeSelection.x ?? badgeSelection.ys[0] ?? null;
  }, [activeTab, selectedCell, badgeSelection]);

  /** Copy the selected column (definition + every cell) in right after itself. */
  const handleDuplicateColumn = useCallback(() => {
    const table = currentTable();
    if (!table) {
      showToast(gettext("No data table to edit"), "error");
      return;
    }
    const index = activeColumnName
      ? table.columns.findIndex((c) => c.name === activeColumnName)
      : -1;
    if (index < 0) {
      showToast(gettext("Select a column to duplicate"), "error");
      return;
    }
    const next = duplicateColumnAt(table, index);
    const copy = next.columns[index + 1];
    applyEdit(next, {
      kind: "duplicate-column",
      columnName: table.columns[index].name,
      newName: copy ? copy.name : table.columns[index].name,
    });
  }, [activeColumnName, applyEdit, currentTable, showToast]);

  const handleDeleteColumn = useCallback(() => {
    const table = currentTable();
    if (!table) {
      showToast(gettext("No data table to edit"), "error");
      return;
    }
    const index = activeColumnName
      ? table.columns.findIndex((c) => c.name === activeColumnName)
      : -1;
    if (index < 0) {
      showToast(gettext("Select a column to delete"), "error");
      return;
    }
    const plan = planColumnDelete(table, index);
    // What the delete does to the plot assignment, decided BEFORE the edit so
    // it can be shown and then cleared in the same step (never a stale chip).
    const impact = assignmentImpact(badgeSelection, plan.columnName);
    if (!plan.allowed) {
      // The last remaining column is asked about, never deleted silently.
      if (plan.needsConfirm) {
        setConfirmColumnDelete({
          name: plan.columnName ?? "",
          assignment: impact.affected
            ? affectedAssignmentLabel(impact)
            : null,
          last: true,
        });
      }
      return;
    }
    if (impact.affected) {
      // Destructive beyond the cells: the plot's binding goes with it.
      setConfirmColumnDelete({
        name: plan.columnName ?? "",
        assignment: affectedAssignmentLabel(impact),
        last: false,
      });
      return;
    }
    setConfirmColumnDelete(null);
    applyEdit(deleteColumnAt(table, index), {
      kind: "delete-column",
      columnName: plan.columnName ?? "",
    });
  }, [activeColumnName, applyEdit, badgeSelection, currentTable, showToast]);

  const handleConfirmColumnDelete = useCallback(() => {
    const table = currentTable();
    const name = confirmColumnDelete?.name ?? null;
    setConfirmColumnDelete(null);
    if (!table || !name) return;
    const index = table.columns.findIndex((c) => c.name === name);
    if (index < 0) return;
    applyEdit(deleteColumnAt(table, index), {
      kind: "delete-column",
      columnName: name,
    });
  }, [applyEdit, confirmColumnDelete, currentTable]);

  const handleRenameSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      const table = currentTable();
      const draft = renameDraft;
      setRenameDraft(null);
      if (!table || draft === null) return;
      const index = activeColumnName
        ? table.columns.findIndex((c) => c.name === activeColumnName)
        : -1;
      if (index < 0) return;
      const next = renameColumnAt(table, index, draft);
      const to = next.columns[index].name;
      if (to === table.columns[index].name) return;
      applyEdit(next, {
        kind: "rename-column",
        from: table.columns[index].name,
        to,
      });
    },
    [activeColumnName, applyEdit, currentTable, renameDraft],
  );

  const handleUndo = useCallback(() => {
    const table = currentTable();
    if (!table) {
      showToast(gettext("No data table to edit"), "error");
      return;
    }
    // One transition: the table AND the X/Y binding it was made with come back
    // together, and the state being undone is parked as a pair for redo.
    const next = applyUndo({
      table,
      assignment: cloneSelection(badgeSelection),
      undoStack,
      redoStack,
    });
    // Empty stack: nothing to undo is not an error worth a toast.
    if (!next) return;
    setUndoStack(next.undoStack);
    setRedoStack(next.redoStack);
    writeTable(next.table);
    setSelectionCommand((c) => ({ selection: next.assignment, nonce: (c?.nonce ?? 0) + 1 }));
    void persistTable(next.table, interpolate(gettext("Undid: %s"), [next.label]));
  }, [badgeSelection, currentTable, persistTable, redoStack, showToast, undoStack, writeTable]);

  /** Put back the edit the last undo reversed — table and binding together. */
  const handleRedo = useCallback(() => {
    const table = currentTable();
    if (!table) {
      showToast(gettext("No data table to edit"), "error");
      return;
    }
    const next = applyRedo({
      table,
      assignment: cloneSelection(badgeSelection),
      undoStack,
      redoStack,
    });
    // Nothing to redo is a silent no-op, like an empty undo stack.
    if (!next) return;
    setUndoStack(next.undoStack);
    setRedoStack(next.redoStack);
    writeTable(next.table);
    setSelectionCommand((c) => ({ selection: next.assignment, nonce: (c?.nonce ?? 0) + 1 }));
    void persistTable(next.table, interpolate(gettext("Redid: %s"), [next.label]));
  }, [badgeSelection, currentTable, persistTable, redoStack, showToast, undoStack, writeTable]);

  // The editor already binds Ctrl+Z globally to the canvas undo, so the table's
  // undo only takes the keystroke when the interaction was in this pane, and
  // then stops the event from reaching the canvas handler.
  useEffect(() => {
    const inPane = (target: EventTarget | null) =>
      target instanceof Node &&
      contentRef.current !== null &&
      contentRef.current.contains(target);
    const markContext = (e: Event) => {
      paneInteractionRef.current = inPane(e.target);
    };
    document.addEventListener("mousedown", markContext, true);
    document.addEventListener("focusin", markContext, true);
    return () => {
      document.removeEventListener("mousedown", markContext, true);
      document.removeEventListener("focusin", markContext, true);
    };
  }, []);

  // Capture phase: it runs before the window-level listeners, which is the only
  // way to keep one Ctrl+Z from undoing the canvas as well.
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (!(e.ctrlKey || e.metaKey)) return;
      if (e.key.toLowerCase() !== "z") return;
      // Shift+Ctrl/Cmd+Z is the redo half of the pair. Both are the table's
      // while this pane holds the interaction context, and both are stopped
      // here so the canvas' own Ctrl+Z handler never sees the same keystroke.
      const redo = e.shiftKey;
      if (!paneInteractionRef.current) return;
      // Typing targets keep the browser's own undo: the cell editor's text is
      // not the table yet.
      const target = e.target as HTMLElement | null;
      if (
        target &&
        (target.isContentEditable ||
          /^(input|textarea|select)$/i.test(target.tagName))
      )
        return;
      e.preventDefault();
      e.stopPropagation();
      if (redo) handleRedo();
      else handleUndo();
    };
    document.addEventListener("keydown", onKeyDown, true);
    return () => document.removeEventListener("keydown", onKeyDown, true);
  }, [handleRedo, handleUndo]);

  /** Close a tab and remove the corresponding figure from canvas. */
  const handleCloseTab = useCallback(
    (tabId: string) => {
      // Find figure that matches this tab by path, id, or fall back to selected/first
      const figure =
        placedFigures.find((f) => f.path === tabId || f.id === tabId) ??
        placedFigures.find(
          (f) => f.id === useEditorStore.getState().selectedFigureId,
        ) ??
        (placedFigures.length === 1 ? placedFigures[0] : null);
      if (figure) {
        removeFigure(figure.id);
      }
      // Always remove the tab
      useEditorStore.setState((s) => {
        const updated = { ...s.datatableTabs };
        delete updated[tabId];
        const remaining = Object.keys(updated);
        return {
          datatableTabs: updated,
          activeTabId: remaining.length > 0 ? remaining[0] : null,
        };
      });
    },
    [placedFigures, removeFigure],
  );

  const handleExportCsv = useCallback(async () => {
    try {
      const blob = await api.getBlob("download/csv");
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "data.csv";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      showToast(interpolate(gettext("Export failed: %s"), [e]), "error");
    }
  }, [showToast]);

  const handleImportCsv = useCallback(
    async (file: File) => {
      try {
        const content = await file.text();
        const ext = file.name.split(".").pop()?.toLowerCase();
        const format = ext === "tsv" ? "tsv" : ext === "json" ? "json" : "csv";
        // An import REPLACES the same stored table the save queue writes, so a
        // pending edit must land first — otherwise it would overwrite the file
        // the user just chose.
        await saveQueue.idle();
        await api.post("datatable/import", { content, format });
        showToast(gettext("Imported data"), "success");
        loadDatatable();
        refreshAfterMutation();
      } catch (e) {
        showToast(interpolate(gettext("Import failed: %s"), [e]), "error");
      }
    },
    [showToast, loadDatatable, refreshAfterMutation, saveQueue],
  );

  const dataset = useMemo(
    () =>
      activeTab
        ? datasetFromTable({ columns: activeTab.columns, rows: activeTab.rows })
        : undefined,
    [activeTab?.columns, activeTab?.rows], // eslint-disable-line react-hooks/exhaustive-deps
  );

  return (
    <>
      {/* vis_app .pane-header */}
      <div className="pane-header">
        {/* Explicit collapse/expand control — a visible button, not a
            double-click gesture. Left panel: chevron points out when
            expanded (collapse), in when collapsed (expand). */}
        <button
          className="pane-header-btn panel-toggle-btn"
          type="button"
          onClick={onToggleCollapse}
          title={collapsed ? gettext("Expand data table") : gettext("Collapse data table")}
          aria-label={collapsed ? gettext("Expand data table") : gettext("Collapse data table")}
        >
          <i
            className={`fas ${
              collapsed ? "fa-chevron-right" : "fa-chevron-left"
            }`}
          />
        </button>
        {/* Data dropdown */}
        <div className="data-dropdown-container">
          <button className="data-dropdown-toggle" type="button">
            <i className="fas fa-table" />
            <span className="data-dropdown-label">
              {tabs.length > 0
                ? interpolate(ngettext("%s table", "%s tables", tabs.length), [tabs.length])
                : gettext("No tables")}
            </span>
            <i className="fas fa-chevron-down" />
          </button>
          <button
            className="pane-header-btn data-new-btn"
            type="button"
            onClick={() => fileInputRef.current?.click()}
            title={gettext("Import data")}
          >
            <i className="fas fa-plus" />
          </button>
        </div>

        {/* Action buttons */}
        <div className="pane-header-buttons">
          <button
            className="pane-header-btn"
            onClick={handleUndo}
            title={
              undoStack.length > 0
                ? interpolate(gettext("Undo %s"), [undoStack[undoStack.length - 1].label])
                : gettext("Undo (Ctrl+Z)")
            }
            aria-label={gettext("Undo last table change")}
            disabled={undoStack.length === 0}
            type="button"
          >
            <i className="fas fa-undo" />
          </button>
          <button
            className="pane-header-btn"
            onClick={handleRedo}
            title={
              redoStack.length > 0
                ? interpolate(gettext("Redo %s"), [redoStack[redoStack.length - 1].label])
                : gettext("Redo (Ctrl+Shift+Z)")
            }
            aria-label={gettext("Redo the last undone table change")}
            disabled={redoStack.length === 0}
            type="button"
          >
            <i className="fas fa-redo" />
          </button>
          <button
            className="pane-header-btn"
            onClick={handleExportCsv}
            title={gettext("Export CSV")}
            disabled={tabs.length === 0}
            type="button"
          >
            <i className="fas fa-file-export" />
          </button>
          <button
            className="pane-header-btn"
            title={gettext("Sort (WIP)")}
            type="button"
            disabled
          >
            <i className="fas fa-sort" />
          </button>
          <button
            className="pane-header-btn"
            title={gettext("Filter (WIP)")}
            type="button"
            disabled
          >
            <i className="fas fa-filter" />
          </button>
          <button
            className="pane-header-btn"
            title={gettext("Keyboard shortcuts")}
            type="button"
          >
            <i className="fas fa-keyboard" />
          </button>
        </div>

        {/* Vertical title with icon (visible only when collapsed via CSS) */}
        <span className="panel-title">
          <i className="fas fa-table" />
          {gettext("Table")}
        </span>
      </div>

      {/* Hidden file input for CSV import */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv,.tsv,.json,.xlsx"
        style={{ display: "none" }}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleImportCsv(file);
          e.target.value = "";
        }}
      />

      {/* Pane content — uses shared scitex-ui DataTable.
          The handlers live here rather than on a wrapper element: the table is
          sized by its own height:100%, which a wrapper would break, and the
          pane still needs one node to delegate clicks and hover on. */}
      <div
        className="pane-content data-pane__content"
        ref={contentRef}
        onClick={handleContentClick}
        onMouseOver={handlePointerOver}
        onMouseOut={handlePointerOut}
      >
        {tabs.length >= 1 && (
          <div className="datatable-panel__tabs">
            {tabs.map((tab, idx) => (
              <button
                key={tab.id}
                className={`datatable-panel__tab${tab.id === activeTabId ? " active" : ""}`}
                style={{
                  borderLeft: `3px solid ${getPanelColor(idx)}`,
                }}
                onClick={() => useEditorStore.setState({ activeTabId: tab.id })}
                type="button"
              >
                {tab.label}
                <span
                  className="datatable-panel__tab-close"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCloseTab(tab.id);
                  }}
                  title={gettext("Close tab and remove figure")}
                >
                  &times;
                </span>
              </button>
            ))}
          </div>
        )}
        {activeTab && (
          <PlotFromColumns
            key={activeTab.id}
            tab={activeTab}
            columnCommand={columnCommand}
            selectionCommand={selectionCommand}
            onSelectionChange={setBadgeSelection}
          />
        )}

        {/* Row/column CRUD — the shared table has none, and every edit made
            here is persisted through datatable/import and undoable. */}
        <div
          className="data-pane__toolbar"
          role="toolbar"
          aria-label={gettext("Table editing")}
        >
          <button
            type="button"
            className="data-pane__btn"
            onClick={handleAddRow}
            disabled={!activeTab}
            title={gettext("Add a row below the selected one")}
          >
            <i className="fas fa-plus" aria-hidden="true" />
            {gettext("Add row")}
          </button>
          <button
            type="button"
            className="data-pane__btn"
            onClick={handleDeleteRow}
            disabled={!activeTab}
            title={gettext("Delete the selected row")}
          >
            <i className="fas fa-minus" aria-hidden="true" />
            {gettext("Delete row")}
          </button>
          <span className="data-pane__toolbar-sep" aria-hidden="true" />
          <button
            type="button"
            className="data-pane__btn"
            onClick={handleAddColumn}
            disabled={!activeTab}
            title={gettext("Add a column at the end of the table")}
          >
            <i className="fas fa-plus" aria-hidden="true" />
            {gettext("Add column")}
          </button>
          <button
            type="button"
            className="data-pane__btn"
            onClick={() => setRenameDraft(activeColumnName ?? "")}
            disabled={!activeTab || !activeColumnName}
            title={gettext("Rename the selected column")}
          >
            <i className="fas fa-pen" aria-hidden="true" />
            {gettext("Rename column")}
          </button>
          <button
            type="button"
            className="data-pane__btn"
            onClick={handleDuplicateColumn}
            disabled={!activeTab || !activeColumnName}
            title={gettext("Duplicate the selected column beside itself")}
          >
            <i className="fas fa-clone" aria-hidden="true" />
            {gettext("Duplicate column")}
          </button>
          <button
            type="button"
            className="data-pane__btn"
            onClick={handleDeleteColumn}
            disabled={!activeTab || !activeColumnName}
            title={gettext("Delete the selected column")}
          >
            <i className="fas fa-trash-alt" aria-hidden="true" />
            {gettext("Delete column")}
          </button>
        </div>

        {renameDraft !== null && (
          <form className="data-pane__prompt" onSubmit={handleRenameSubmit}>
            <label className="data-pane__prompt-label" htmlFor="data-pane-rename">
              {interpolate(gettext("Rename column '%s'"), [activeColumnName ?? ""])}
            </label>
            <input
              id="data-pane-rename"
              className="data-pane__prompt-input"
              value={renameDraft}
              onChange={(e) => setRenameDraft(e.target.value)}
              autoFocus
            />
            <button type="submit" className="data-pane__btn">
              {gettext("Rename")}
            </button>
            <button
              type="button"
              className="data-pane__btn"
              onClick={() => setRenameDraft(null)}
            >
              {gettext("Cancel")}
            </button>
          </form>
        )}

        {confirmColumnDelete !== null && (
          <div
            className="data-pane__prompt data-pane__prompt--danger"
            role="alertdialog"
            aria-label={
              confirmColumnDelete.last
                ? gettext("Confirm deleting the last column")
                : gettext("Confirm deleting an assigned column")
            }
          >
            <span className="data-pane__prompt-label">
              {confirmColumnDelete.last
                ? interpolate(gettext("Delete the last column '%s'?"), [
                    confirmColumnDelete.name,
                  ])
                : interpolate(
                    gettext(
                      "Delete column '%s'? It is the %s column — that assignment will be cleared.",
                    ),
                    [confirmColumnDelete.name, confirmColumnDelete.assignment ?? ""],
                  )}
            </span>
            <button
              type="button"
              className="data-pane__btn data-pane__btn--danger"
              onClick={handleConfirmColumnDelete}
            >
              {gettext("Delete column")}
            </button>
            <button
              type="button"
              className="data-pane__btn"
              onClick={() => setConfirmColumnDelete(null)}
            >
              {gettext("Cancel")}
            </button>
          </div>
        )}

        <DataTable
          data={dataset}
          style={{ flex: 1 }}
          onCellSelect={handleCellSelect}
          onDataChange={handleDataChange}
        />
      </div>
    </>
  );
}
