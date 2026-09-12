/**
 * Forwards the browser's Authorization header through a Next.js API
 * route to the FastAPI backend, so RBAC enforced there (see auth.py /
 * api.py) actually applies end-to-end instead of the proxy silently
 * calling the backend unauthenticated.
 */
export function forwardAuthHeader(request: Request): Record<string, string> {
  const authHeader = request.headers.get("authorization");
  return authHeader ? { Authorization: authHeader } : {};
}
