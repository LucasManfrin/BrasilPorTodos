import test from 'node:test';
import assert from 'node:assert/strict';
import { interestCents, interestState, interestBalanceLabel } from '../src/lib/fiscal-interest.ts';

const scope = 'Governo Central: Tesouro Nacional, Previdência Social e Banco Central; exclui estados e municípios';
// Invented observations; deliberately different from the RTN above-the-line balance.
const fiscal = { status: 'AVAILABLE', year: 2025, scope, amounts: { published_primary_balance: '-99999.00' } };
const codes = ['rtn-primario-abaixo-linha', 'rtn-juros-nominais', 'rtn-resultado-nominal'];
function cohort() {
 return { status: 'AVAILABLE', year: 2025, period_start: '2025-01-01', period_end: '2025-12-31', scope, currency: 'BRL', accounting_basis: 'mixed', methodology_basis: 'below_line', component_bases: { primary: 'cash', interest: 'accrual' }, price_basis: 'nominal', source: { title: 'Fonte fictícia de teste', attribution: 'Fixture' }, totals: { primary_balance: '120.00', interest: '-1200.00', nominal_balance: '-1080.00' }, reconciliation: { monthly_tolerance: '0.03', annual_difference: '0.00' }, months: Array.from({length:12}, (_,i) => ({ reference_date:`2025-${String(i+1).padStart(2,'0')}-01`, observations:codes.map((code,j) => ({code,value:['10.00','-100.00','-90.00'][j]})) })) };
}
test('cent parsing preserves signs, decimal normalization and unsafe Number magnitudes', () => {
 assert.equal(interestCents('9007199254740993.01'),900719925474099301n);
 assert.equal(interestCents('-12.3'),-1230n);
 assert.equal(interestCents('+12'),1200n);
 assert.equal(interestCents('-0.00'),0n);
});
test('missing and invalid money remain absent', () => {
 for(const value of [undefined,null,'','NaN','Infinity','1e3','1.001','1,00',true,0]) assert.equal(interestCents(value),null);
});
test('below-line primary may differ from RTN without becoming incompatible', () => {
 assert.equal(interestState(fiscal,cohort()),'READY');
 assert.equal(interestState({...fiscal,amounts:{published_primary_balance:'123456.00'}},cohort()),'READY');
});
for(const [key,value] of [['year',2024],['scope','Governo Geral']]) {
 test(`different ${key} blocks a mixed reading`, () => assert.equal(interestState(fiscal,{...cohort(),[key]:value}),'MISMATCH'));
}
for(const [key,value] of [['currency','USD'],['accounting_basis','cash'],['methodology_basis','above_line'],['price_basis','constant'],['period_start','2025-02-01'],['period_end','2025-12-01'],['component_bases',{primary:'accrual',interest:'cash'}]]) {
 test(`wrong ${key} does not display the account`, () => assert.equal(interestState(fiscal,{...cohort(),[key]:value}),'UNAVAILABLE'));
}
test('each month must contain all three signed components exactly once', () => {
 for(const mutate of [c=>c.months.pop(), c=>c.months[1].reference_date=c.months[0].reference_date, c=>c.months[0].reference_date='2024-01-01', c=>c.months[0].observations.pop(), c=>c.months[0].observations[1].code=codes[0], c=>c.months[0].observations[1].value=null]) {
  const c=cohort();mutate(c);assert.equal(interestState(fiscal,c),'UNAVAILABLE');
 }
});
test('annual totals must equal sums of the twelve months in exact cents', () => {
 const c=cohort();c.totals.nominal_balance='-1079.99';c.reconciliation.annual_difference='-0.01';
 assert.equal(interestState(fiscal,c),'UNAVAILABLE');
});
test('small published rounding residual survives into the annual difference', () => {
 const c=cohort();c.months[3].observations[2].value='-89.99';c.totals.nominal_balance='-1079.99';c.reconciliation.annual_difference='-0.01';
 assert.equal(interestState(fiscal,c),'READY');
 c.reconciliation.annual_difference='0.00';
 assert.equal(interestState(fiscal,c),'UNAVAILABLE');
});
test('opposite monthly errors cannot cancel into an apparently valid year', () => {
 const c=cohort();c.months[0].observations[2].value='-89.96';c.months[1].observations[2].value='-90.04';
 assert.equal(interestState(fiscal,c),'UNAVAILABLE');
});
test('the source monthly tolerance cannot be expanded by response metadata', () => {
 const c=cohort();c.reconciliation.monthly_tolerance='1.00';
 assert.equal(interestState(fiscal,c),'UNAVAILABLE');
});
test('positive signed interest is preserved rather than subtracted again', () => {
 const c=cohort();for(const month of c.months){month.observations[1].value='20.00';month.observations[2].value='30.00';}c.totals.interest='240.00';c.totals.nominal_balance='360.00';
 assert.equal(interestState(fiscal,c),'READY');
 assert.equal(interestBalanceLabel('20.00','interest'),'Juros líquidos · sinal positivo');
 assert.equal(interestBalanceLabel('-20.00','interest'),'Juros líquidos · sinal negativo');
});
test('explicit zero is valid and has its own label; incomplete is never zero', () => {
 const c=cohort();for(const month of c.months)for(const row of month.observations)row.value='0.00';for(const key of Object.keys(c.totals))c.totals[key]='0.00';
 assert.equal(interestState(fiscal,c),'READY');
 assert.equal(interestBalanceLabel('-0.00','interest'),'Juros líquidos nulos');
 assert.equal(interestBalanceLabel('0.00','nominal'),'Equilíbrio nominal');
 for(const invalid of [null,undefined,{...c,status:'INCOMPLETE'},{...c,status:'EMPTY'},{...c,totals:null},{...c,reconciliation:null},{...c,source:null}])assert.equal(interestState(fiscal,invalid),'UNAVAILABLE');
 assert.equal(interestState(null,c),'UNAVAILABLE');
});
test('balance labels explain deficits and surpluses without a direction colour judgement', () => {
 assert.equal(interestBalanceLabel('-1.00','primary'),'Déficit primário');
 assert.equal(interestBalanceLabel('1.00','nominal'),'Superávit nominal');
 assert.equal(interestBalanceLabel('NaN','primary'),'Valor indisponível');
});
test('annual reconciliation remains exact above safe Number cents', () => {
 const c=cohort();for(const month of c.months){month.observations[0].value='90071992547409.91';month.observations[1].value='-90071992547409.90';month.observations[2].value='0.01';}c.totals={primary_balance:'1080863910568918.92',interest:'-1080863910568918.80',nominal_balance:'0.12'};
 assert.equal(interestState(fiscal,c),'READY');
});

test('negative primary and sign changes remain explicit signed arithmetic', () => {
 const c=cohort();for(const month of c.months){month.observations[0].value='-10.00';month.observations[2].value='-110.00';}c.totals.primary_balance='-120.00';c.totals.nominal_balance='-1320.00';
 assert.equal(interestState(fiscal,c),'READY');
 c.months[0].observations[0].value='10.00';c.months[0].observations[2].value='-90.00';c.totals.primary_balance='-100.00';c.totals.nominal_balance='-1300.00';
 assert.equal(interestState(fiscal,c),'READY');
 const malformed=cohort();malformed.months[0]=null;assert.equal(interestState(fiscal,malformed),'UNAVAILABLE');
 const missing=cohort();missing.months[0].observations[0]=null;assert.equal(interestState(fiscal,missing),'UNAVAILABLE');
});

test('PostgreSQL six-place cent-exact observations normalize without rounding', () => {
 assert.equal(interestCents('83149894449.290000'),8314989444929n);
 assert.equal(interestCents('-100.000000'),-10000n);
 assert.equal(interestCents('12.300000'),1230n);
 assert.equal(interestCents('0.000000'),0n);
 for(const invalid of ['0.000001','12.340001','-12.340001','1.001000','1.000010','1.0000000'])assert.equal(interestCents(invalid),null);
 const c=cohort();for(const month of c.months)for(const row of month.observations){const [whole,fraction]=row.value.split('.');row.value=whole+'.'+fraction.padEnd(6,'0');}
 assert.equal(interestState(fiscal,c),'READY');
 c.months[0].observations[1].value='-100.000001';assert.equal(interestState(fiscal,c),'UNAVAILABLE');
});
