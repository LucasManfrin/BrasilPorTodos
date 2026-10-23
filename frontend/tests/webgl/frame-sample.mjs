/** Renderer-submission cadence, never GPU completion or a device guarantee. */
export function createFrameSample({warmupFrames = 30, sampleIntervals = 240} = {}) {
  if (!Number.isSafeInteger(warmupFrames) || warmupFrames < 0 || !Number.isSafeInteger(sampleIntervals) || sampleIntervals < 1) {
    throw new RangeError('Use nonnegative warmup frames and at least one sample interval.');
  }
  let warmup = warmupFrames, previous = null, state = 'measuring', result = null;
  const intervals = [];
  const snapshot = () => result ?? {state, warmupRemaining: warmup, collectedIntervals: intervals.length, targetIntervals: sampleIntervals};
  function cancel(reason) {
    if (state === 'measuring') {
      state = 'invalidated';
      result = {state, reason, collectedIntervals: intervals.length, targetIntervals: sampleIntervals};
    }
    return snapshot();
  }
  function frame(time) {
    if (state !== 'measuring') return snapshot();
    if (!Number.isFinite(time) || previous !== null && time <= previous) return cancel('Invalid or non-increasing renderer timestamp.');
    if (warmup > 0) { warmup--; return snapshot(); }
    if (previous === null) { previous = time; return snapshot(); }
    intervals.push(time - previous); previous = time;
    if (intervals.length < sampleIntervals) return snapshot();
    const sorted = [...intervals].sort((a, b) => a - b);
    const duration = intervals.reduce((sum, value) => sum + value, 0);
    const round = value => +value.toFixed(2);
    state = 'complete';
    result = {state, rendererIntervals: intervals.length, durationMs: round(duration), averageFps: round(intervals.length * 1000 / duration), medianFrameMs: round(sorted[Math.floor(sorted.length * .5)]), p95FrameMs: round(sorted[Math.min(sorted.length - 1, Math.ceil(sorted.length * .95) - 1)]), longFramesAbove25ms: intervals.filter(value => value > 25).length, maximumFrameMs: round(sorted.at(-1)), note: 'Cadence of actual renderer submissions; not GPU completion, presentation time or a guarantee for other hardware.'};
    return snapshot();
  }
  return {frame, cancel, snapshot};
}
