// TODO(SL-27): the real My reports page replaces the placeholder at this path
export const DEFAULT_AFTER_LOGIN = "/my-reports";

// ProtectedRoute leaves the page the user asked for in the router state
export function destinationFrom(state: unknown): string {
  const from = (state as { from?: { pathname?: string; search?: string } } | null)?.from;
  return from?.pathname ? `${from.pathname}${from.search ?? ""}` : DEFAULT_AFTER_LOGIN;
}
