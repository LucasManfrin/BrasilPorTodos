import assert from 'node:assert/strict';
import test from 'node:test';
import {initialGraphState} from '../src/features/graphs/state.ts';
import {DEMO_GRAPH} from '../src/features/graphs/demo.ts';

const record={...DEMO_GRAPH,id:'10000000-0000-4000-8000-000000000001',revision:7};
test('exact published record opens even when no directory was requested',()=>{
  const state=initialGraphState(null,record,record.id,7);
  assert.equal(state.mode,'published');assert.equal(state.record,record);assert.equal(state.error,'');assert.equal(state.busy,false);
  assert.deepEqual(state.target,{id:record.id,revision:7});
});
test('a valid record is not replaced by a demonstration when the directory is empty',()=>{
  const state=initialGraphState({data:[]},record);
  assert.equal(state.mode,'published');assert.equal(state.record.revision,7);
});
test('missing exact version loads its requested target, without a demo or assumed latest revision',()=>{
  const state=initialGraphState({data:[]},null,record.id,3);
  assert.equal(state.mode,'published');assert.equal(state.record,null);assert.equal(state.busy,true);assert.deepEqual(state.target,{id:record.id,revision:3});
});
test('network failure is not an empty public catalog or a demonstration',()=>{
  const state=initialGraphState(null,null);
  assert.equal(state.mode,'published');assert.equal(state.busy,false);assert.ok(state.error);assert.equal(state.record,null);
});
test('a confirmed empty catalog may open the clearly labeled teaching scene',()=>{
  const state=initialGraphState({data:[]},null);
  assert.equal(state.mode,'demo');assert.equal(state.busy,false);assert.equal(state.error,'');assert.equal(state.target,null);
});
test('catalog boot pins the revision displayed, rather than implicit latest',()=>{
  const state=initialGraphState({data:[record]},null);
  assert.equal(state.mode,'published');assert.equal(state.busy,true);assert.deepEqual(state.target,{id:record.id,revision:7});
});
