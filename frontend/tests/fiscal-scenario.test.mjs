import test from 'node:test';
import assert from 'node:assert/strict';
import {
  normalizeScenarioMoney, fiscalScenarioBody, reconcileScenarioYears,
  invalidateScenarioReview, scenarioIsReviewed, scenarioHorizon,
  createFiscalScenario, scenarioYearsMatch, scenarioAmountState,
  planEditResetsScenarioReview,
} from '../src/lib/fiscal-scenario.ts';

const scenario = {
  title: 'Premissas declaradas', explanation: 'Não inclui as propostas do plano.',
  reference_baseline_id: 'baseline-reviewed',
  years: [{year: 2027, net_revenue: '9999999999999999.99', primary_expenditure: '0.00',
    justification: 'Valores declarados.', source_urls: ['https://www.tesouro.gov.br/']}],
  excludes_plan_impacts: true, review_input_hash: 'hash-a', reviewed_input_hash: 'hash-a', reviewed_at: '2026-10-14T12:00:00Z',
};
test('money keeps all eighteen decimal digits and explicit zero', () => {
  assert.equal(normalizeScenarioMoney('9999999999999999.99'), '9999999999999999.99');
  assert.equal(normalizeScenarioMoney('9.999.999.999.999.999,99'), '9999999999999999.99');
  assert.equal(normalizeScenarioMoney('0'), '0.00');
  assert.equal(normalizeScenarioMoney('000001,2'), '1.20');
});
test('empty amount is missing rather than zero', () => {
  for (const value of [null, undefined, '', '   ']) assert.equal(normalizeScenarioMoney(value), null);
  assert.deepEqual(scenarioAmountState(null), {available: false, value: null});
  assert.deepEqual(scenarioAmountState(undefined), {available: false, value: null});
  assert.deepEqual(scenarioAmountState('0.00'), {available: true, value: '0.00'});
});
for (const value of ['-1', '1e12', '1.123', '10000000000000000', '1.23,45', '1,', 'abc', 'Infinity']) {
  test('reject ambiguous, negative or oversized money: ' + value, () => assert.throws(() => normalizeScenarioMoney(value), Error));
}
test('create/PATCH/duplicate never transport readonly confirmation fields', () => {
  const body = fiscalScenarioBody(scenario);
  assert.deepEqual(Object.keys(body).sort(), ['explanation', 'reference_baseline_id', 'title', 'years']);
  assert.equal('excludes_plan_impacts' in body, false);
  assert.equal('review_input_hash' in body, false);
  assert.equal('reviewed_input_hash' in body, false);
  assert.equal('reviewed_at' in body, false);
  assert.equal(body.years[0].net_revenue, scenario.years[0].net_revenue);
  assert.deepEqual(fiscalScenarioBody(body), body);
});
test('missing baseline can be saved as an empty reference, without inventing one', () => {
  const created = createFiscalScenario(null, 2027, 2028);
  assert.equal(fiscalScenarioBody(created).reference_baseline_id, '');
  assert.deepEqual(created.years.map(row => row.net_revenue), [null, null]);
});
test('explicit removal and legacy absence produce null in payload', () => {
  assert.equal(fiscalScenarioBody(null), null);
  assert.equal(fiscalScenarioBody(undefined), null);
});
test('rows reconciled explicitly preserve retained values and leave added years empty', () => {
  const changed = reconcileScenarioYears(scenario, 2027, 2029);
  assert.equal(changed.years[0].net_revenue, '9999999999999999.99');
  assert.equal(changed.years[0].primary_expenditure, '0.00');
  assert.equal(changed.years[1].net_revenue, null);
  assert.equal(changed.years[2].primary_expenditure, null);
  assert.equal(changed.reference_baseline_id, 'baseline-reviewed');
  assert.equal(scenarioIsReviewed(changed), false);
  assert.equal(scenarioIsReviewed(scenario), true);
});
test('shrinking the horizon removes only years outside it', () => {
  const expanded = reconcileScenarioYears(scenario, 2026, 2028);
  const shrunk = reconcileScenarioYears(expanded, 2027, 2027);
  assert.deepEqual(shrunk.years, scenario.years);
});
test('horizon change is detectable without silently changing the configuration', () => {
  assert.equal(scenarioYearsMatch(scenario, 2027, 2027), true);
  assert.equal(scenarioYearsMatch(scenario, 2027, 2028), false);
  assert.deepEqual(scenario.years.map(row => row.year), [2027]);
  assert.equal(scenarioYearsMatch({...scenario, years: [scenario.years[0], scenario.years[0]]}, 2027, 2028), false);
});
test('one through thirty years are bounded before generating rows', () => {
  assert.equal(scenarioHorizon(2027, 2056).length, 30);
  for (const [start,end] of [[2027,2057],[2028,2027],[1899,1900],[2200,2201],[2027.5,2029],[NaN,2029]])
    assert.throws(() => scenarioHorizon(start,end), Error);
});
test('confirmation requires exact matching server hash and confirmed flag', () => {
  assert.equal(scenarioIsReviewed(scenario), true);
  for (const altered of [
    {...scenario, review_input_hash: 'other'}, {...scenario, reviewed_at: null},
    {...scenario, excludes_plan_impacts: false}, invalidateScenarioReview(scenario),
  ]) assert.equal(scenarioIsReviewed(altered), false);
  assert.equal(invalidateScenarioReview(null), null);
});
test('fiscal edits reset review, while descriptive plan edits preserve it', () => {
  for (const field of ['policies','start_year','end_year','baseline_snapshot','fiscal_scenario'])
    assert.equal(planEditResetsScenarioReview(field), true);
  for (const field of ['title','summary','vision','change_summary'])
    assert.equal(planEditResetsScenarioReview(field), false);
});
test('serialization trims source lines without mutating saved input', () => {
  const original = {...scenario, years: [{...scenario.years[0], source_urls: [' ', ' https://ibge.gov.br/ ']}]};
  assert.deepEqual(fiscalScenarioBody(original).years[0].source_urls, ['https://ibge.gov.br/']);
  assert.deepEqual(original.years[0].source_urls, [' ', ' https://ibge.gov.br/ ']);
});
