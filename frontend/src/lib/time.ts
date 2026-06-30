export function formatRelativeTime(value: string): string {
  const ts = new Date(value).getTime()
  const now = Date.now()
  const deltaMinutes = Math.max(1, Math.floor((now - ts) / 60_000))

  if (deltaMinutes < 60) return `${deltaMinutes} minute${deltaMinutes > 1 ? "s" : ""} ago`
  const deltaHours = Math.floor(deltaMinutes / 60)
  if (deltaHours < 24) return `${deltaHours} hour${deltaHours > 1 ? "s" : ""} ago`
  if (deltaHours < 48) return "yesterday"
  const deltaDays = Math.floor(deltaHours / 24)
  return `${deltaDays} days ago`
}
