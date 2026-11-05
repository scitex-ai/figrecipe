/** A queued CSV is owned by the recipe/tab/session that accepted the edit. */
export interface TableWriteContext {session: number; recipe: string | null; tabId: string | null;}
export interface TableWriteJob extends TableWriteContext {csv: string;}
export function tableWriteMatches(job: TableWriteContext, current: TableWriteContext): boolean {
  return job.session === current.session && job.recipe === current.recipe && job.tabId === current.tabId;
}
