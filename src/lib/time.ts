export function minutesToKickoff(kickoffAt: string): number {
  return Math.round((new Date(kickoffAt).getTime() - Date.now()) / 60000);
}

export function hasKickedOff(kickoffAt: string): boolean {
  return new Date(kickoffAt).getTime() <= Date.now();
}

export function formatKickoff(kickoffAt: string): string {
  const d = new Date(kickoffAt);
  const now = new Date();
  const sameDay = d.toDateString() === now.toDateString();
  const time = d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
  if (sameDay) return `${time} KO`;
  return `${d.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" })}, ${time}`;
}

export function formatClock(status: string, minute: number): string {
  if (status === "scheduled") return "";
  if (status === "ht") return "HT";
  if (status === "finished") return "FT";
  return `${minute}'`;
}

export function timeAgo(iso: string): string {
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}
