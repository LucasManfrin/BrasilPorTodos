import test from 'node:test';
import assert from 'node:assert/strict';
import {formatCompact, formatExact, getTrend, selectCalendarPeriod, referenceLabel} from '../src/lib/data-format.ts';
for (const [value, unit, expected] of [
 ['201463204827.03','R$','R$ 201,5 bi'], ['3425727670000','R$','R$ 3,43 tri'],
 ['187878259768.46','R$','R$ 187,9 bi'], ['-13584945058.57','R$','−R$ 13,6 bi'],
 ['82.8619','% do PIB','82,86 % do PIB'], ['114.40189','índice','114,4 índice'],
 ['0','R$','R$ 0,00'], ['-0.001','%','0 %'], ['9007199254740993.99','R$','R$ 9.007,2 tri'],
 ['NaN','R$','Sem dado'], ['1e9','R$','R$ 1 bi']
]) test(`compact ${value} ${unit}`, () => assert.equal(formatCompact(value,unit),expected));
test('exact money retains cents above Number safe integer',()=>assert.equal(formatExact('9007199254740993.99','R$'),'R$ 9.007.199.254.740.993,99'));
const indicator = (current, previous, unit='R$', code='test') => ({code,unit,frequency:'MONTHLY',latest:{value:current,reference_date:'2026-09-01'},series:[{value:previous,reference_date:'2026-08-01'}]});
for (const [name,a,b,kind,direction] of [
 ['two negatives','-20','-10','absolute','down'], ['zero baseline','20','0','absolute','up'],
 ['current zero','0','10','absolute','down'], ['sign change','-20','10','absolute','down'],
 ['near zero','10','0.01','absolute','up'], ['positive money','120','100','percent','up'],
 ['same','10','10','percent','flat']
]) test(name,()=>{const trend=getTrend(indicator(a,b));assert.equal(trend.kind,kind);assert.equal(trend.direction,direction);assert.doesNotMatch(trend.label,/pior|melhor/);});
test('monthly inflation compares negative month in points',()=>assert.equal(getTrend(indicator('0.82','-0.32','%')).label,'Subiu 1,14 p.p. vs. ago/26'));
test('positive rates use points rather than relative percent',()=>assert.match(getTrend(indicator('13.75','13.25','% a.a.')).label,/0,5 p.p./));
test('near-zero index uses absolute units',()=>assert.equal(getTrend(indicator('1','0.001','índice')).kind,'absolute'));
test('missing comparison stays missing',()=>assert.equal(getTrend({...indicator('1','1'),series:[]}).kind,'unavailable'));
test('seasonal comparison uses year earlier',()=>{const item=indicator('5.3','5.1','%','desocupacao');item.series.push({value:'6.2',reference_date:'2025-09-01'});assert.match(getTrend(item).label,/Caiu 0,9 p.p. vs. set\/25/);});
test('calendar year does not count quarterly observations',()=>{const points=['2025-04-01','2025-07-01','2025-10-01','2026-01-01','2026-04-01'].map(reference_date=>({reference_date,value:'1'}));assert.equal(selectCalendarPeriod(points,'1y').length,4);});
test('latest revision wins',()=>assert.equal(selectCalendarPeriod([{reference_date:'2026-01-01',value:'1',revision:1},{reference_date:'2026-01-01',value:'2',revision:2}],'max')[0].value,'2'));
test('daily reference distinguishes observations inside a month',()=>assert.equal(referenceLabel('2026-10-09','DAILY'),'09/10/2026'));
test('tiny absolute index change is never shown as a zero change',()=>assert.match(getTrend(indicator('0.002','0.001','índice')).label,/Subiu menos de 0,01 índice/));
test('tiny rate change preserves direction without false zero',()=>assert.match(getTrend(indicator('0.001','0.002','%')).label,/Caiu menos de 0,01 p.p./));
for(const code of ['renda-trabalho-real','informalidade','participacao-forca-trabalho']) test(code+' uses the same rolling quarter last year',()=>{
 const item=indicator('62.2','61.8',code==='renda-trabalho-real'?'R$':'%',code);
 item.series.push({value:'60.2',reference_date:'2025-09-01'});
 assert.match(getTrend(item).label,/vs\. set\/25/);
 assert.equal(getTrend(item).kind,code==='renda-trabalho-real'?'percent':'points');
});
