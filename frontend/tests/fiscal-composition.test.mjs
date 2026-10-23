import test from 'node:test';
import assert from 'node:assert/strict';
import { compositionCents, compositionState, compositionShare } from '../src/lib/fiscal-composition.ts';

const baseline = {status:'AVAILABLE',year:2025,period_start:'2025-01-01',period_end:'2025-12-01',scope:'Governo Central',currency:'BRL',accounting_basis:'cash',price_basis:'nominal',amounts:{net_revenue:'9007199254740993.01',primary_expenditure:'9007199254740994.00',published_primary_balance:'-0.99'}};
const items = ['0.01','20.00','30.00','-1.00'].map((amount, index) => ({code:`test-${index}`,series:`10.test.${index}`,label:`Fictício ${index}`,amount}));
const composition = {...baseline,reference_amounts:{...baseline.amounts},totals:{gross_revenue:'1000.00',transfers:'100.00',net_revenue:baseline.amounts.net_revenue,primary_expenditure:baseline.amounts.primary_expenditure},revenue:items,expenditure:items,reconciliation:{revenue_components_difference:'0.00',net_revenue_difference:'0.00',expenditure_difference:'0.01',monthly_tolerance:'0.03'}};

test('money parser preserves signed cents beyond safe Number range', () => {
 assert.equal(compositionCents('9007199254740993.01'),900719925474099301n);
 assert.equal(compositionCents('-12.3'),-1230n);
 assert.equal(compositionCents('+12'),1200n);
 assert.equal(compositionCents('-0.00'),0n);
});
test('invalid or missing money never means zero', () => {
 for(const input of [undefined,null,'','NaN','1e3','1.001','1,00',100,true]) assert.equal(compositionCents(input),null);
});
test('same annual anchors permit composition with negative official adjustments', () => assert.equal(compositionState(baseline,composition),'READY'));
test('decimal string normalization preserves identical references', () => {
 const c=structuredClone(composition); c.reference_amounts.primary_expenditure='9007199254740994';
 assert.equal(compositionState(baseline,c),'READY');
});
for(const key of ['net_revenue','primary_expenditure','published_primary_balance']) {
 test('one-cent revision of '+key+' blocks mixed collections', () => {
  const c=structuredClone(composition); c.reference_amounts[key]=c.reference_amounts[key].replace(/\d$/,digit=>digit==='9'?'8':'9');
  assert.equal(compositionState(baseline,c),'MISMATCH');
 });
}
for(const [key,value] of [['year',2024],['period_start','2025-02-01'],['period_end','2025-11-01'],['scope','Governo Geral'],['currency','USD'],['accounting_basis','accrual'],['price_basis','constant']]) {
 test('different '+key+' is not silently combined', () => assert.equal(compositionState(baseline,{...composition,[key]:value}),'MISMATCH'));
}
test('absent and partial composition preserve unavailable state', () => {
 for(const c of [null,undefined,{...composition,status:'EMPTY'},{...composition,status:'INCOMPLETE'},{...composition,totals:null},{...composition,reference_amounts:null},{...composition,reconciliation:null},{...composition,revenue:items.slice(0,3)}]) assert.equal(compositionState(baseline,c),'UNAVAILABLE');
 assert.equal(compositionState(null,composition),'UNAVAILABLE');
 assert.equal(compositionState({...baseline,amounts:null},composition),'UNAVAILABLE');
});
test('missing component and missing anchor never receive zero', () => {
 const c=structuredClone(composition); c.revenue[0].amount=null;
 assert.equal(compositionState(baseline,c),'UNAVAILABLE');
 c.reference_amounts.net_revenue=null;
 assert.equal(compositionState(baseline,c),'UNAVAILABLE');
});
test('signed share distinguishes negative adjustments and tiny nonzero values', () => {
 assert.deepEqual(compositionShare('-1.00','1000.00'),{label:'−0,10%',width:0});
 assert.deepEqual(compositionShare('-0.01','1000.00'),{label:'−menos de 0,01%',width:0});
 assert.deepEqual(compositionShare('0.00','1000.00'),{label:'0,00%',width:0});
 assert.deepEqual(compositionShare('1.00','4.00'),{label:'25,00%',width:25});
});
test('share arithmetic stays exact and geometry alone is bounded', () => {
 assert.deepEqual(compositionShare('9007199254740993.00','18014398509481986.00'),{label:'50,00%',width:50});
 assert.deepEqual(compositionShare('200.00','100.00'),{label:'200,00%',width:100});
 assert.equal(compositionShare('10.00','0.00'),null);
 assert.equal(compositionShare('10.00','-10.00'),null);
 assert.equal(compositionShare('no-data','100.00'),null);
});
