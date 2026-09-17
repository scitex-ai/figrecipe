/** Whether the example figure may be seeded — and by whom
 * (card figrecipe-data-column-and-plot-variant-ux-20260916 / scitex-hub PR 923).
 *
 * The Private Beta spec is explicit: "Create or import a project explicitly;
 * never silently select an example" and "Real users never receive a silently
 * created or selected example project". figrecipe's empty-canvas surface broke
 * that rule on mounting: it POSTed `api/gallery/demo` by itself, and the server
 * seeds a demo recipe plus its data directory into the workspace, so simply
 * opening a project wrote example artifacts the user never asked for (measured:
 * `demo_first_figure.yaml` + `demo_first_figure_data/` appearing in a project
 * that had none).
 *
 * The surface still wants to open on a FIGURE rather than a menu — that was the
 * point of the automatic seed. Both hold only if the seed becomes an explicit
 * action: the offer renders immediately, the click does the seeding. This module
 * is that rule as a transition table, so "nothing seeds on its own" is a tested
 * property rather than a comment:
 *
 *   from `idle`, ONLY `user-request` can start a seed. Every other event —
 *   including a successful seed arriving unbidden — is a no-op.
 *
 * Pure and dependency-free (no React, no DOM, no @scitex/ui), so it runs under
 * `node --experimental-strip-types` like the other decision modules here.
 */

export type SeedState = "idle" | "seeding" | "open" | "unavailable";

export type SeedEvent =
  /** The user pressed the offer's button. */
  | "user-request"
  /** The seed succeeded (a figure is now on the canvas). */
  | "seed-opened"
  /** The seed declined: the project already holds the user's own recipes. */
  | "seed-declined"
  /** The seed failed (no templates installed, write refused). */
  | "seed-failed";

/** The state after an event. */
export function nextSeedState(state: SeedState, event: SeedEvent): SeedState {
  if (event === "user-request") {
    // Only from rest: a second click while seeding must not fire a second write.
    return state === "idle" ? "seeding" : state;
  }
  if (state !== "seeding") return state;
  switch (event) {
    case "seed-opened":
      return "open";
    case "seed-declined":
    case "seed-failed":
      return "unavailable";
    default:
      return state;
  }
}

/** Whether the surface should show its spinner: a seed is running BECAUSE the
 * user asked for it. */
export function isSeeding(state: SeedState): boolean {
  return state === "seeding";
}

/** Whether to offer the explicit action. Once the seed has run (opened or
 * declined) the offer is spent — the example tiles replace it. */
export function offersExampleSeed(state: SeedState): boolean {
  return state === "idle";
}
