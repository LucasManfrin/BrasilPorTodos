/**
 * Balance rows rather than leaving a final orphan: five cards at capacity four
 * become three plus two. Twelve tracks divide exactly by each supported row size.
 * The breakpoint is chosen in CSS, so server render and hydration share spans.
 */
export function balancedCardSpans(count: number, capacity: number): number[] {
  if (!Number.isInteger(count) || count < 0) throw new RangeError("Card count must be a non-negative integer.");
  if (!Number.isInteger(capacity) || capacity < 1 || capacity > 4) throw new RangeError("Grid capacity must be between one and four.");
  if (count === 0) return [];
  const rows = Math.ceil(count / capacity);
  const base = Math.floor(count / rows);
  const extra = count % rows;
  return Array.from({ length: rows }, (_, row) => {
    const size = base + (row < extra ? 1 : 0);
    return Array<number>(size).fill(12 / size);
  }).flat();
}

export function responsiveCardSpans(count: number, index: number) {
  if (!Number.isInteger(index) || index < 0 || index >= count) throw new RangeError("Card index is outside the grid.");
  return {
    mobile: balancedCardSpans(count, 1)[index],
    tablet: balancedCardSpans(count, 2)[index],
    desktop: balancedCardSpans(count, 3)[index],
    wide: balancedCardSpans(count, 4)[index],
  };
}
