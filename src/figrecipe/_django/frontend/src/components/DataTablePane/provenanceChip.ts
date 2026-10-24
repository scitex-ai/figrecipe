/** Provenance chip for figure-recorded (locked) tables.
 *
 * A locked table teaches its own lineage with zero new backend and zero new
 * copy: the recipe filename plus the recording call ids, both parsed from
 * what the table already shows. Filenames and ids are language-neutral, so
 * no gettext is involved and the i18n gate is untouched.
 *
 * Kept free of React and the @scitex/sdk/ui alias so it runs under
 * `node --experimental-strip-types` -- the JSX only renders what this
 * module decides.
 */

/** Suffixes the backend's _call_table_columns convention puts on recorded data. */
const RECORDED_SUFFIXES = ["_x", "_y"] as const;

/** Recording call ids behind the given table columns, first-appearance order.
 *
 * Only `{call_id}_x` / `{call_id}_y` columns count -- anything else is user
 * data (imported/project tables), not provenance.
 */
export function recordingCalls(columns: readonly string[]): string[] {
  const calls: string[] = [];
  const seen = new Set<string>();
  for (const name of columns) {
    const suffix = RECORDED_SUFFIXES.find((s) => name.endsWith(s));
    if (!suffix || name.length <= suffix.length) continue;
    const call = name.slice(0, -suffix.length);
    if (seen.has(call)) continue;
    seen.add(call);
    calls.push(call);
  }
  return calls;
}

/** The recipe filename of the figure that recorded a locked table.
 *
 * The session recipe -- the same value the API layer pins to every call --
 * so the chip names the file the record was read from. Null when unknown
 * (embedded mode without a recipe param): the chip then shows calls only.
 */
export function recordingRecipe(): string | null {
  const raw =
    typeof window === "undefined"
      ? ""
      : (new URLSearchParams(window.location.search).get("recipe") ?? "");
  const file = raw.split("/").pop() ?? "";
  return file ? file : null;
}
