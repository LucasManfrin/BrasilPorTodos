import test from 'node:test';
import assert from 'node:assert/strict';
import { createTapTracker } from '../src/features/graphs/interaction.ts';

const pointer = (pointerId, clientX = 0, clientY = 0, button) => ({ pointerId, clientX, clientY, ...(button === undefined ? {} : { button }) });

test('mouse and touch taps tolerate up to eight CSS pixels of movement', () => {
  for (const button of [0, undefined]) {
    const tracker = createTapTracker();
    tracker.down(pointer(1, 20, 30, button));
    tracker.move(pointer(1, 23, 34));
    assert.equal(tracker.up(pointer(1, 28, 30, button)), true);
    assert.equal(tracker.up(pointer(1, 28, 30, button)), false);
  }
});

test('dragging past the threshold cannot select even after returning to the origin', () => {
  const tracker = createTapTracker();
  tracker.down(pointer(1, 10, 20));
  tracker.move(pointer(1, 17, 27));
  tracker.move(pointer(1, 10, 20));
  assert.equal(tracker.up(pointer(1, 10, 20)), false);
  tracker.down(pointer(2));
  assert.equal(tracker.up(pointer(2)), true);
});

test('final release checks displacement even when no move event arrived', () => {
  const tracker = createTapTracker();
  tracker.down(pointer(1));
  assert.equal(tracker.up(pointer(1, 0, 8.01)), false);
});

test('non-primary mouse buttons never start or finish a tap', () => {
  const tracker = createTapTracker();
  for (const button of [1, 2, -1]) {
    tracker.down(pointer(1, 0, 0, button));
    assert.equal(tracker.up(pointer(1, 0, 0, button)), false);
    assert.equal(tracker.up(pointer(1, 0, 0, 0)), false);
  }
  tracker.down(pointer(1, 0, 0, 0));
  tracker.down(pointer(1, 0, 0, 2));
  assert.equal(tracker.up(pointer(1, 0, 0, 2)), false);
  assert.equal(tracker.up(pointer(1, 0, 0, 0)), true);
});

test('a pinch never selects in either release order', () => {
  for (const releaseOrder of [[1, 2], [2, 1]]) {
    const tracker = createTapTracker();
    tracker.down(pointer(1));
    tracker.down(pointer(2, 100, 0));
    tracker.move(pointer(1, -20, 0));
    tracker.move(pointer(2, 120, 0));
    for (const id of releaseOrder) assert.equal(tracker.up(pointer(id)), false);
    tracker.down(pointer(3));
    assert.equal(tracker.up(pointer(3)), true);
  }
});

test('multitouch remains blocked when primary leaves and another finger enters', () => {
  const tracker = createTapTracker();
  tracker.down(pointer(1));
  tracker.down(pointer(2));
  assert.equal(tracker.up(pointer(1)), false);
  tracker.down(pointer(3));
  assert.equal(tracker.up(pointer(2)), false);
  assert.equal(tracker.up(pointer(3)), false);
  tracker.down(pointer(1));
  assert.equal(tracker.up(pointer(1)), true);
});

test('pointer cancellation invalidates the gesture and releases the pointer', () => {
  const tracker = createTapTracker();
  tracker.down(pointer(1));
  tracker.cancel(1);
  assert.equal(tracker.up(pointer(1)), false);
  tracker.down(pointer(1));
  assert.equal(tracker.up(pointer(1)), true);
});

test('cancelling one finger does not turn the remaining pinch into a tap', () => {
  for (const cancelled of [1, 2]) {
    const tracker = createTapTracker();
    tracker.down(pointer(1));
    tracker.down(pointer(2));
    tracker.cancel(cancelled);
    tracker.down(pointer(3));
    assert.equal(tracker.up(pointer(3)), false);
    assert.equal(tracker.up(pointer(cancelled === 1 ? 2 : 1)), false);
    tracker.down(pointer(4));
    assert.equal(tracker.up(pointer(4)), true);
  }
});

test('untracked events cannot complete or disrupt an active tap', () => {
  const tracker = createTapTracker();
  assert.equal(tracker.up(pointer(5)), false);
  tracker.down(pointer(1));
  tracker.move(pointer(5, 100, 100));
  tracker.cancel(5);
  assert.equal(tracker.up(pointer(5)), false);
  assert.equal(tracker.up(pointer(1)), true);
});

test('duplicate down cannot reset a drag or create a tap', () => {
  const tracker = createTapTracker();
  tracker.down(pointer(1));
  tracker.move(pointer(1, 20));
  tracker.down(pointer(1, 20));
  assert.equal(tracker.up(pointer(1, 20)), false);
});

test('event objects are snapshots and independent trackers do not share state', () => {
  const first = createTapTracker();
  const second = createTapTracker();
  const event = pointer(1);
  first.down(event);
  second.down(pointer(1));
  event.clientX = 100;
  assert.equal(first.up(event), false);
  assert.equal(second.up(pointer(1)), true);
});

test('nonfinite coordinates never create a tap', () => {
  for (const bad of [NaN, Infinity, -Infinity]) {
    const tracker = createTapTracker();
    tracker.down(pointer(1, bad));
    assert.equal(tracker.up(pointer(1, bad)), false);
    tracker.down(pointer(2));
    tracker.move(pointer(2, bad));
    assert.equal(tracker.up(pointer(2)), false);
  }
});
