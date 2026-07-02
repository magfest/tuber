/* Helpers for working with times in the event's time zone.
 *
 * The backend stores all datetimes as UTC. Staff can be anywhere, so UIs
 * render times in the event's IANA time zone (event.timezone) rather than
 * the browser's — everyone sees the same wall time.
 *
 * "Wall space" below means a fake-UTC millisecond timestamp whose UTC parts
 * equal the wall-clock reading in the target zone. It gives a linear scale
 * that is convenient for formatting and for laying out timelines.
 */

// Wall-clock reading of a UTC instant in a time zone, in wall space.
function wallTimeInZone (ts: number, timeZone: string): number {
  const dtf = new Intl.DateTimeFormat('en-US', {
    timeZone,
    hourCycle: 'h23',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
  const p: { [key: string]: string } = {}
  for (const part of dtf.formatToParts(new Date(ts))) {
    p[part.type] = part.value
  }
  return Date.UTC(+p.year, +p.month - 1, +p.day, +p.hour, +p.minute, +p.second)
}

// Validate an IANA zone name, falling back to the browser's zone.
function resolveTimeZone (timeZone?: string | null): string {
  if (timeZone) {
    try {
      Intl.DateTimeFormat('en-US', { timeZone })
      return timeZone
    } catch (e) {
      // fall through
    }
  }
  return Intl.DateTimeFormat().resolvedOptions().timeZone
}

// Convert a UTC value from the backend into the "YYYY-MM-DDTHH:mm" string
// expected by <input type="datetime-local">, rendered in the given zone.
function utcToZoneInput (value: string | null, timeZone: string): string {
  if (!value) {
    return ''
  }
  const d = new Date(value)
  if (isNaN(d.getTime())) {
    return ''
  }
  const wall = new Date(wallTimeInZone(d.getTime(), timeZone))
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${wall.getUTCFullYear()}-${pad(wall.getUTCMonth() + 1)}-${pad(wall.getUTCDate())}T${pad(wall.getUTCHours())}:${pad(wall.getUTCMinutes())}`
}

// Convert a "YYYY-MM-DDTHH:mm" picker value (zone wall time) into a UTC ISO
// string for the backend (which expects a trailing "Z").
function zoneInputToUtc (value: string | null, timeZone: string): string | null {
  if (!value) {
    return null
  }
  const m = value.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/)
  if (!m) {
    return null
  }
  const wallAsUtc = Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5])
  // The zone offset depends on the instant (DST), which is what we are
  // solving for — iterate once to converge across DST boundaries.
  let ts = wallAsUtc - (wallTimeInZone(wallAsUtc, timeZone) - wallAsUtc)
  ts = wallAsUtc - (wallTimeInZone(ts, timeZone) - ts)
  return new Date(ts).toISOString()
}

// Human-readable label for a UTC value in the given zone, e.g. "Wed, Aug 12, 9:00 PM".
function formatInZone (value: string | number | null, timeZone: string, options?: Intl.DateTimeFormatOptions): string {
  if (!value && value !== 0) {
    return ''
  }
  const d = new Date(value)
  if (isNaN(d.getTime())) {
    return ''
  }
  return new Intl.DateTimeFormat('en-US', Object.assign({
    timeZone,
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit'
  }, options)).format(d)
}

export {
  wallTimeInZone,
  resolveTimeZone,
  utcToZoneInput,
  zoneInputToUtc,
  formatInZone
}
