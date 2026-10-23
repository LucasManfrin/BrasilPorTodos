export type TapPointer = {
  pointerId: number;
  clientX: number;
  clientY: number;
  button?: number;
};

/**
 * Recognizes primary-button taps without DOM state. A gesture that travels more
 * than 8 CSS pixels, is cancelled, or overlaps another pointer cannot select.
 * After overlapping pointers, every tracked pointer must leave before a new tap.
 * `cancel(pointerId)` releases that pointer and invalidates the entire gesture.
 */
export function createTapTracker() {
  const active = new Map<number, { x: number; y: number }>();
  let candidate: number | null = null;
  let blocked = false;

  function resetWhenEmpty() {
    if (active.size !== 0) return;
    candidate = null;
    blocked = false;
  }

  function move(event: TapPointer) {
    const origin = active.get(event.pointerId);
    if (!origin) return;
    if (!Number.isFinite(event.clientX) || !Number.isFinite(event.clientY)
      || Math.hypot(event.clientX - origin.x, event.clientY - origin.y) > 8) {
      blocked = true;
    }
  }

  function down(event: TapPointer) {
    if (event.button !== undefined && event.button !== 0) return;
    if (active.size === 0) {
      candidate = event.pointerId;
      blocked = false;
    } else {
      blocked = true;
    }
    active.set(event.pointerId, { x: event.clientX, y: event.clientY });
    if (!Number.isFinite(event.clientX) || !Number.isFinite(event.clientY)) blocked = true;
  }

  function up(event: TapPointer): boolean {
    if (event.button !== undefined && event.button !== 0) return false;
    if (!active.has(event.pointerId)) return false;
    move(event);
    const tapped = !blocked && active.size === 1 && candidate === event.pointerId;
    active.delete(event.pointerId);
    resetWhenEmpty();
    return tapped;
  }

  function cancel(pointerId: number) {
    if (!active.has(pointerId)) return;
    blocked = true;
    active.delete(pointerId);
    resetWhenEmpty();
  }

  return { down, move, up, cancel };
}
