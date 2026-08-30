/**
 * Plain, environment-agnostic helper — no "use client" directive, so it's
 * safe to import from both client components and server-side API routes.
 * (initialsFromName used to live in member.ts, but that file is "use client"
 * for its localStorage helpers, which broke calling it from a Route Handler.)
 */
export function initialsFromName(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "??";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}
