import test from 'node:test';
import assert from 'node:assert/strict';
import { balancedCardSpans, responsiveCardSpans } from '../src/features/data-explorer/balanced-grid.ts';

for (const count of [1, 2, 3, 4, 5, 7]) {
  for (const capacity of [1, 2, 3, 4]) {
    test(`${count} cards fill every row at capacity ${capacity}`, () => {
      const spans = balancedCardSpans(count, capacity);
      assert.equal(spans.length, count);
      let rowTracks = 0;
      let rowCards = 0;
      for (const span of spans) {
        assert.ok(Number.isInteger(span) && span > 0);
        rowTracks += span;
        rowCards++;
        assert.ok(rowCards <= capacity);
        assert.ok(rowTracks <= 12);
        if (rowTracks === 12) { rowTracks = 0; rowCards = 0; }
      }
      assert.equal(rowTracks, 0, 'the final row consumes all twelve tracks');
    });
  }
}
test('five cards at capacity four balance as three plus two', () => assert.deepEqual(balancedCardSpans(5, 4), [4, 4, 4, 6, 6]));
test('seven cards at capacity four balance as four plus three', () => assert.deepEqual(balancedCardSpans(7, 4), [3, 3, 3, 3, 4, 4, 4]));
test('one card fills every breakpoint', () => assert.deepEqual(responsiveCardSpans(1, 0), { mobile: 12, tablet: 12, desktop: 12, wide: 12 }));
test('zero cards produce no rows', () => assert.deepEqual(balancedCardSpans(0, 4), []));
test('reject invalid counts, capacity and index', () => {
  assert.throws(() => balancedCardSpans(-1, 4), RangeError);
  assert.throws(() => balancedCardSpans(1.5, 4), RangeError);
  assert.throws(() => balancedCardSpans(2, 5), RangeError);
  assert.throws(() => responsiveCardSpans(2, 2), RangeError);
});
