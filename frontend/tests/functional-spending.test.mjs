import test from 'node:test';
import assert from 'node:assert/strict';
import {functionalSpendingState, spendingCents, spendingFunctionIdentity, orderedSpendingFunctions} from '../src/lib/functional-spending.ts';

const money=(paid,rap=0)=>({PAID:paid.toFixed(2),RAP_PAID:rap.toFixed(2),TOTAL_PAID:(paid+rap).toFixed(2)});
const source={title:'Despesas oficiais',institution:'Secretaria do Tesouro Nacional',url:'https://www.tesourotransparente.gov.br/ckan/dataset/despesas-e-transferencias-totais',license:'ODbL 1.0',license_url:'https://opendatacommons.org/licenses/odbl/1-0/'};
const fiscal={status:'AVAILABLE',year:2025,scope:'Outro critério: RTN',amounts:{primary_expenditure:'999999999.00'}};
const group=(nature,key,code,label,paid,rap=0,classification='BUDGET_FUNCTION')=>({nature,nature_label:nature,function_key:key,function_code:code.padStart(2,'0'),source_function_code:code,function_label:label,classification,row_count:1,amounts:money(paid,rap)});
function cohort(){
 const primary=group('PRIMARY','FUNCTION_10','10','SAUDE',100,10),financial=group('FINANCIAL','FUNCTION_10','10','SAUDE',20,2),reserve=group('PRIMARY','FUNCTION_99','99','RESERVA DE CONTINGENCIA',0),na=group('EXTRA_SIAFI','UNCLASSIFIED_NA','99','N/A',-5,0,'UNCLASSIFIED'),other=group('EXTRA_SIAFI','UNCLASSIFIED_OTHER','99','OUTRAS',-1,0,'UNCLASSIFIED');
 const groups=[primary,financial,reserve,na,other];
 const months=Array.from({length:12},(_,i)=>({month:i+1,row_count:5,totals:money(114,12),groups:structuredClone(groups)}));
 const observed=months.map(m=>m.month);
 const functions=groups.map(row=>({...structuredClone(row),row_count:12,amounts:money(Number(row.amounts.PAID)*12,Number(row.amounts.RAP_PAID)*12),observed_months:observed}));
 const natures=[{nature:'PRIMARY',nature_label:'Primária',row_count:24,amounts:money(1200,120),observed_months:observed},{nature:'FINANCIAL',nature_label:'Despesa Financeira',row_count:12,amounts:money(240,24),observed_months:observed},{nature:'EXTRA_SIAFI',nature_label:'Extra-Siafi',row_count:24,amounts:money(-72),observed_months:observed}];
 const payload={year:2025,scope:'GOVERNMENT_CENTRAL_OFSS_SOURCE',currency:'BRL',price_basis:'CURRENT',accounting_basis:'OB_ISSUANCE_VALUE_PAID',periodicity:'MONTHLY_MOVEMENT',parser_version:'1.0.0',precision_version:'row-half-even-cent-v1',source,resource:{id:'official-resource',url:'https://www.tesourotransparente.gov.br/ckan/resource.xlsx',last_modified:'2026-02-25T14:41:36',size:34500062,sha256:'b'.repeat(64)},row_count:60,stages:['PAID','RAP_PAID','TOTAL_PAID'],months,totals:money(1368,144),natures,functions,reconciliation:{row_payment_difference_max:'0.00',group_total_differences:money(0),raw_minus_rounded_totals:{PAID:'-0.0036943647371717',RAP_PAID:'-0.00000178664206316',TOTAL_PAID:'-0.00369615137923486'},published_subset:{scope:'Subconjunto da tabela dinâmica, não todas as funções',labels:['categoria'],months:observed.map(month=>({month,published_total:'10.00',calculated_total:'10.00',difference:'0.00'})),annual_published_total:'119.99',annual_calculated_total:'120.00',annual_difference:'0.01'}},absence_policy:'Grupos ausentes não são zero',fingerprint:'a'.repeat(64)};
 return {status:'AVAILABLE',year:2025,period_start:'2025-01-01',period_end:'2025-12-31',collected_at:'2026-10-11T12:00:00Z',revision:1,cohort_fingerprint:payload.fingerprint,source,payload,methodology:'Execução por valor pago',limitations:[],missing:[]};
}
const state=value=>functionalSpendingState(fiscal,value);
test('cent parser accepts real NUMERIC scale without rounding source fractions',()=>{
 assert.equal(spendingCents('994386075.610000'),99438607561n);
 assert.equal(spendingCents('-4840104733.160000'),-484010473316n);
 assert.equal(spendingCents('0.000000'),0n);
 for(const value of ['-0.0036943647371717','1.000001','1.001','1e5',1,null,'Infinity','1,00'])assert.equal(spendingCents(value),null);
});
test('whole cohort reconciles independently of RTN scope or amounts',()=>{const c=cohort();assert.equal(state(c),'READY');assert.equal(c.payload.reconciliation.published_subset.annual_difference,'0.01');});
test('the reference year alone must match RTN',()=>{const c=cohort();assert.equal(functionalSpendingState({...fiscal,year:2024},c),'MISMATCH');c.payload.year=2024;assert.equal(state(c),'MISMATCH');});
test('unavailable data or fiscal anchor cannot become zeros',()=>{assert.equal(state(null),'UNAVAILABLE');assert.equal(state({...cohort(),status:'INCOMPLETE'}),'UNAVAILABLE');assert.equal(functionalSpendingState({...fiscal,status:'EMPTY'},cohort()),'UNAVAILABLE');});
test('all 12 global months required with exact coverage, count and annual aggregates',()=>{
 for(const mutate of [c=>c.payload.months.pop(),c=>c.payload.months[11].month=1,c=>c.payload.months[0].row_count=4,c=>c.payload.row_count=59,c=>c.payload.totals=money(1369,144),c=>c.period_end='2025-12-01']){const c=cohort();mutate(c);assert.equal(state(c),'UNAVAILABLE');}
});
test('paid plus RAP must reconcile at group, month, nature and annual levels',()=>{
 for(const mutate of [c=>c.payload.months[0].groups[0].amounts.TOTAL_PAID='111.00',c=>c.payload.months[0].totals=money(115,12),c=>c.payload.natures[0].amounts=money(1199,120),c=>c.payload.functions[0].amounts=money(1199,120),c=>c.payload.reconciliation.group_total_differences.PAID='0.01']){const c=cohort();mutate(c);assert.equal(state(c),'UNAVAILABLE');}
});
test('explicit signed Extra-Siafi remains signed while reserve zero remains observed',()=>{const c=cohort();assert.equal(state(c),'READY');assert.equal(c.payload.natures[2].amounts.TOTAL_PAID,'-72.00');assert.equal(c.payload.functions[2].amounts.TOTAL_PAID,'0.00');assert.equal(c.payload.functions[2].observed_months.length,12);});
test('unobserved function month remains absent, not a zero invented in coverage',()=>{
 const c=cohort();c.payload.months[0].groups.splice(2,1);c.payload.months[0].row_count--;c.payload.row_count--;c.payload.functions[2].row_count--;c.payload.functions[2].observed_months=c.payload.functions[2].observed_months.slice(1);c.payload.natures[0].row_count--;
 assert.equal(state(c),'READY');c.payload.functions[2].observed_months.unshift(1);assert.equal(state(c),'UNAVAILABLE');
});
test('missing annual group and duplicate entries cannot hide zero or truncated data',()=>{
 for(const mutate of [c=>c.payload.functions.splice(2,1),c=>c.payload.functions[2]=c.payload.functions[0],c=>c.payload.natures[2]=c.payload.natures[0],c=>c.payload.months[0].groups[2]=c.payload.months[0].groups[0]]){const c=cohort();mutate(c);assert.equal(state(c),'UNAVAILABLE');}
});
test('code 99 reserve, N/A and OUTRAS retain separate source identities',()=>{
 const rows=cohort().payload.functions;for(const row of rows)assert.equal(spendingFunctionIdentity(row),true);
 assert.equal(spendingFunctionIdentity({...rows[3],function_key:'FUNCTION_99',classification:'BUDGET_FUNCTION'}),false);
 assert.equal(spendingFunctionIdentity({...rows[4],function_key:'UNCLASSIFIED_NA'}),false);
 assert.equal(spendingFunctionIdentity({...rows[0],source_function_code:'99'}),false);
 assert.equal(spendingFunctionIdentity({...rows[0],nature:'UNKNOWN'}),false);
});
test('sort uses fixed codes, preserves original code and does not mutate input',()=>{
 const rows=cohort().payload.functions.filter(row=>row.nature==='PRIMARY').reverse();const original=rows.map(row=>row.function_key);const sorted=orderedSpendingFunctions(rows);assert.deepEqual(sorted.map(row=>row.function_key),['FUNCTION_10','FUNCTION_99']);assert.deepEqual(rows.map(row=>row.function_key),original);
 const first=group('PRIMARY','FUNCTION_01','1','LEGISLATIVA',1);assert.equal(spendingFunctionIdentity(first),true);assert.equal(first.source_function_code,'1');
});
test('revision fingerprint, checksum, source metadata and accounting semantics cannot drift',()=>{
 for(const mutate of [c=>c.cohort_fingerprint='c'.repeat(64),c=>c.payload.resource.sha256='bad',c=>c.source={...c.source,license:'Unknown'},c=>c.payload.accounting_basis='cash',c=>c.payload.stages=['PAID','TOTAL_PAID','RAP_PAID'],c=>c.payload.price_basis='CONSTANT']){const c=cohort();mutate(c);assert.equal(state(c),'UNAVAILABLE');}
});
test('published subset remains separate and its preserved difference reconciles',()=>{
 for(const mutate of [c=>c.payload.reconciliation.published_subset.annual_difference='0.00',c=>c.payload.reconciliation.published_subset.months[0].difference='0.01',c=>c.payload.reconciliation.published_subset.months[11].month=1]){const c=cohort();mutate(c);assert.equal(state(c),'UNAVAILABLE');}
});

test('source subset cannot exceed published rounding tolerance even if equation balances',()=>{const c=cohort();c.payload.reconciliation.published_subset.annual_published_total='119.90';c.payload.reconciliation.published_subset.annual_difference='0.10';assert.equal(state(c),'UNAVAILABLE');const monthly=cohort();monthly.payload.reconciliation.published_subset.months[0].published_total='9.99';monthly.payload.reconciliation.published_subset.months[0].difference='0.01';assert.equal(state(monthly),'UNAVAILABLE');});
test('parser precision revision and recorded collection are part of the display contract',()=>{for(const mutate of [c=>c.payload.parser_version='2.0.0',c=>c.payload.precision_version='unknown',c=>c.revision=0,c=>c.collected_at=null]){const c=cohort();mutate(c);assert.equal(state(c),'UNAVAILABLE');}});
