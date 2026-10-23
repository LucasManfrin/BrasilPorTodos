import test from 'node:test';
import assert from 'node:assert/strict';
import {createFrameSample} from './webgl/frame-sample.mjs';

test('sampling uses actual supplied render frames after warmup, with no implicit frames', () => {
  const sample = createFrameSample({warmupFrames: 2, sampleIntervals: 4});
  sample.frame(0); sample.frame(10); sample.frame(20);
  assert.equal(sample.snapshot().collectedIntervals, 0);
  sample.frame(30); sample.frame(40); sample.frame(50);
  assert.equal(sample.snapshot().state, 'measuring');
  const result = sample.frame(60);
  assert.equal(result.state, 'complete');
  assert.equal(result.rendererIntervals, 4);
  assert.equal(result.durationMs, 40);
  assert.equal(result.averageFps, 100);
  assert.equal(result.p95FrameMs, 10);
});

test('slow render submissions are reported, never discarded as bad samples', () => {
  const sample = createFrameSample({warmupFrames: 0, sampleIntervals: 4});
  [0, 10, 30, 70, 1070].forEach(time => sample.frame(time));
  const result = sample.snapshot();
  assert.equal(result.durationMs, 1070);
  assert.equal(result.averageFps, 3.74);
  assert.equal(result.medianFrameMs, 40);
  assert.equal(result.p95FrameMs, 1000);
  assert.equal(result.maximumFrameMs, 1000);
  assert.equal(result.longFramesAbove25ms, 2);
});

test('interaction or environment invalidation does not publish partial FPS', () => {
  for (const reason of ['pointer', 'wheel', 'resize', 'scroll', 'hidden', 'offscreen', 'dispose', 'timeout']) {
    const sample = createFrameSample({warmupFrames: 0, sampleIntervals: 3});
    sample.frame(0); sample.frame(10);
    sample.cancel(reason); sample.frame(20); sample.frame(30);
    assert.deepEqual(sample.snapshot(), {state:'invalidated', reason, collectedIntervals:1, targetIntervals:3});
    assert.equal('averageFps' in sample.snapshot(), false);
  }
});

test('completed reports stay unchanged if later rendering or cancellation occurs', () => {
  const sample = createFrameSample({warmupFrames: 0, sampleIntervals: 1});
  sample.frame(0); const result = sample.frame(20);
  assert.deepEqual(sample.frame(80), result);
  assert.deepEqual(sample.cancel('dispose'), result);
});

test('invalid timestamp order cannot produce negative or infinite FPS', () => {
  for (const time of [NaN, Infinity, 0, -10]) {
    const sample = createFrameSample({warmupFrames: 0, sampleIntervals: 2});
    sample.frame(0);
    assert.equal(sample.frame(time).state, 'invalidated');
  }
});

test('sample bounds reject invalid configuration', () => {
  for (const options of [{warmupFrames:-1}, {warmupFrames:1.5}, {sampleIntervals:0}, {sampleIntervals:NaN}]) assert.throws(() => createFrameSample(options), RangeError);
});
