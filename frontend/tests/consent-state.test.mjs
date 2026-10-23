import test from 'node:test';
import assert from 'node:assert/strict';
import { consentReducer } from '../src/features/ideas/consent-state.ts';
test('AI consent starts absent and is scoped to one creation', () => {
  const state = consentReducer(null, {type:'accept', key:'creation-one'});
  assert.equal(state, 'creation-one');
  assert.notEqual(state, 'creation-two');
});
test('save handoff preserves accepted consent for the saved idea only', () => {
  assert.equal(consentReducer('creation-one',{type:'handoff',from:'creation-one',to:'saved-one'}),'saved-one');
  assert.equal(consentReducer(null,{type:'handoff',from:'creation-one',to:'saved-one'}),null);
  assert.equal(consentReducer('another',{type:'handoff',from:'creation-one',to:'saved-one'}),'another');
});
test('revocation removes consent before further AI calls', () => {
  assert.equal(consentReducer('saved-one',{type:'revoke'}),null);
  assert.equal(consentReducer(null,{type:'revoke'}),null);
});
