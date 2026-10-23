import test from 'node:test';
import assert from 'node:assert/strict';
import { defaultPercentages, percentageMultiplier, sensitivityAssumptions } from '../src/features/ideas/impact-state.ts';

test('declared sensitivity starts with identical multipliers and no invented band', () => {
  assert.deepEqual(sensitivityAssumptions(defaultPercentages), { cost_low:'1.0000',cost_high:'1.0000',gain_low:'1.0000',gain_high:'1.0000' });
});
test('percentage strings convert exactly without floating point', () => {
  assert.equal(percentageMultiplier('80,55'), '0.8055');
  assert.equal(percentageMultiplier('100.01'), '1.0001');
  assert.equal(percentageMultiplier('0'), '0.0000');
  assert.equal(percentageMultiplier('200'), '2.0000');
});
test('invalid percentages, exponent notation, excessive precision and signs are rejected', () => {
  for (const input of ['', '-1', '201', '200,01', '1e2', '100.001', 'Infinity']) assert.throws(() => percentageMultiplier(input));
});
test('lower and upper limits contain the declared values', () => {
  assert.throws(() => sensitivityAssumptions({ ...defaultPercentages, cost_low:'100.01' }));
  assert.throws(() => sensitivityAssumptions({ ...defaultPercentages, gain_high:'99.99' }));
  assert.deepEqual(sensitivityAssumptions({ cost_low:'80',cost_high:'120',gain_low:'50',gain_high:'150' }), { cost_low:'0.8000',cost_high:'1.2000',gain_low:'0.5000',gain_high:'1.5000' });
});
