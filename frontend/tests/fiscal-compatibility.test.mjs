import test from 'node:test';
import assert from 'node:assert/strict';
import { historicalFiscalIssueMessage, fiscalAggregateState, fiscalMetadataBody, fiscalMetadataText, unspecifiedFiscalMetadata } from '../src/lib/fiscal-compatibility.ts';
const nominal = { fiscal_scope: 'CENTRAL_GOVERNMENT', accounting_basis: 'CASH', price_basis: 'NOMINAL', price_base_year: null, component: 'PRIMARY', period_basis: 'FULL_YEAR' };
test('legacy metadata stays explicitly unknown in copying and public text', () => {
  assert.deepEqual(fiscalMetadataBody({}), unspecifiedFiscalMetadata);
  assert.deepEqual(fiscalMetadataText({}), Array(5).fill('Não informado'));
  assert.equal(fiscalAggregateState([{}]), 'INCOMPLETE');
});
test('empty rows do not imply a known zero', () => assert.equal(fiscalAggregateState([]), 'EMPTY'));
test('same declared units can be aggregated locally without proving baseline compatibility', () => assert.equal(fiscalAggregateState([nominal, nominal]), 'HOMOGENEOUS'));
for (const [field, value] of [['fiscal_scope', 'STATE'], ['accounting_basis', 'ACCRUAL'], ['price_basis', 'CONSTANT'], ['component', 'INTEREST'], ['period_basis', 'PARTIAL_YEAR']]) {
  test('different ' + field + ' blocks a comparable preview', () => assert.equal(fiscalAggregateState([nominal, {...nominal, [field]: value}]), 'HETEROGENEOUS'));
  test('missing ' + field + ' blocks a comparable preview', () => assert.equal(fiscalAggregateState([{...nominal, [field]: undefined}]), 'INCOMPLETE'));
}
test('constant prices require a year and distinguish different price years', () => {
  const real = {...nominal, price_basis: 'CONSTANT', price_base_year: 2024};
  assert.equal(fiscalAggregateState([real, {...real, price_base_year: 2025}]), 'HETEROGENEOUS');
  assert.equal(fiscalAggregateState([real, {...real, price_base_year: null}]), 'INCOMPLETE');
  assert.equal(fiscalAggregateState([real, {...real, price_base_year: 1800}]), 'HETEROGENEOUS');
  assert.equal(fiscalAggregateState([real, real]), 'HOMOGENEOUS');
});
test('changing prices to nominal removes the stale price-base year', () => assert.equal(fiscalMetadataBody({...nominal, price_base_year: 2024}).price_base_year, null));
test('metadata normalization preserves a reviewed constant price year', () => assert.equal(fiscalMetadataBody({...nominal, price_basis: 'CONSTANT', price_base_year: 2023}).price_base_year, 2023));
test('invalid enum values are not treated as complete declarations', () => assert.equal(fiscalAggregateState([{...nominal, component: 'toString'}]), 'INCOMPLETE'));

test('future historical reason points to the separately declared scenario without changing snapshot', () => {
  const preserved = { code: 'FUTURE_ASSUMPTIONS_REQUIRED', message: 'anos futuros exigem premissas de cenário ainda não modeladas.' };
  const original = structuredClone(preserved);
  assert.equal(historicalFiscalIssueMessage(preserved), 'O ano da parcela é posterior à referência observada. Compare anos futuros no cenário declarado, separadamente.');
  assert.deepEqual(preserved, original);
});
test('past-year historical difference does not claim a future scenario or adjusted history', () => {
  const preserved = { code: 'YEAR_DIFFERS', message: 'Mensagem histórica.' };
  assert.equal(historicalFiscalIssueMessage(preserved), 'O ano da parcela difere do ano observado. A referência histórica não foi ajustada para esse ano.');
});
test('other historical reasons preserve their captured wording', () => {
  for (const code of ['METADATA_DIFFERS', 'BASELINE_UNAVAILABLE', 'UNRECOGNIZED_REASON']) {
    const preserved = { code, message: 'Texto preservado na execução: ' + code };
    assert.equal(historicalFiscalIssueMessage(preserved), preserved.message);
  }
});
