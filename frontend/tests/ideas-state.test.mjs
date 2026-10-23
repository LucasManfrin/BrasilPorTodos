import test from 'node:test';
import assert from 'node:assert/strict';
import { emptyIdea, confirmAnswer, readAnswer, normalizedIdea, normalizedMoney, canSave, ideaInput, reviewGuidance, guidanceContext, confirmedGuidanceText } from '../src/features/ideas/state.ts';

test('manual and confirmed guidance share one object and preserve fields', () => {
  const manual = confirmAnswer(confirmAnswer(emptyIdea(), 'title', 'Ideia', false), 'summary', 'Uma frase.', false);
  const guided = confirmAnswer(confirmAnswer(emptyIdea(), 'title', 'Ideia', false), 'summary', 'Uma frase.', false);
  assert.deepEqual(normalizedIdea(manual), normalizedIdea(guided));
  assert.equal(readAnswer(manual, 'title'), 'Ideia');
  assert.equal(canSave(manual), true);
});
test('unknown preserves confirmed content instead of clearing or inventing it', () => {
  const input = confirmAnswer(emptyIdea(), 'problem', 'Meu problema', false);
  assert.equal(confirmAnswer(input, 'problem', '', false, true), input);
  assert.equal(confirmAnswer(input, 'sources', 'fonte inventada', true), input);
});
test('AI assistance provenance survives manual changes and does not duplicate', () => {
  let input = confirmAnswer(emptyIdea(), 'risks', 'Pode falhar.', true);
  input = confirmAnswer(input, 'risks', 'Pode haver atraso.', true);
  input = confirmAnswer(input, 'risks', 'Risco revisto.', false);
  assert.deepEqual(input.assisted_fields, ['risks']);
  assert.equal(input.risks, 'Risco revisto.');
});
test('save requires only title and a sentence; missing money and years stay absent', () => {
  const input = emptyIdea();
  assert.equal(canSave(input), false);
  input.title = 'Título'; input.summary = 'Uma frase.';
  const saved = normalizedIdea(input);
  assert.equal(canSave(saved), true);
  assert.equal(saved.content.implementation_start, null);
  assert.equal(saved.content.financial_impact_status, 'NOT_ESTIMATED');
  assert.deepEqual(saved.content.impacts, []);
});
test('money normalization preserves large exact decimal strings and rejects malformed input', () => {
  assert.equal(normalizedMoney('9.999.999.999.999.999,99'), '9999999999999999.99');
  assert.equal(normalizedMoney('100.25'), '100.25');
  for (const value of ['-1', '', '1.234', 'NaN', '1e6']) assert.throws(() => normalizedMoney(value));
});
test('resuming a server record retains the common fields without response metadata', () => {
  const input = confirmAnswer(emptyIdea(), 'beneficiaries', 'Trabalhadores.', false);
  const record = { ...input, id: 'example', status: 'PRIVATE', checklist: [] };
  assert.deepEqual(ideaInput(record), input);
  assert.equal(Object.hasOwn(ideaInput(record), 'id'), false);
});

test('AI revision compares original and suggestion without filling the idea before confirmation', () => {
  const input = emptyIdea();
  const result = { original_text: 'quero que o texto fique mais facil', organized_text: 'Quero que o texto fique mais fácil.', assisted_by_ai: true, unknown: false };
  const review = reviewGuidance(result, 'outro valor');
  assert.equal(review.kind, 'rewritten');
  assert.equal(review.original, result.original_text);
  assert.equal(input.title, '');
  assert.deepEqual(input.assisted_fields, []);
  const confirmed = confirmAnswer(input, 'title', review.suggestion, true);
  assert.equal(confirmed.title, result.organized_text);
  assert.equal(input.title, '');
  assert.deepEqual(confirmed.assisted_fields, ['title']);
});
test('unchanged model output is explicit, including whitespace-only changes and misleading metadata', () => {
  assert.equal(reviewGuidance({ organized_text: 'Meu texto', original_text: 'Meu  texto', assisted_by_ai: true, rewritten: true, unknown: false }, '').kind, 'unchanged');
  assert.equal(reviewGuidance({ organized_text: 'Meu texto.', assisted_by_ai: true, rewritten: false, unknown: false }, 'meu texto').kind, 'rewritten');
});
test('manual words and unknown never claim an AI revision', () => {
  assert.equal(reviewGuidance({ organized_text: 'Meu texto', assisted_by_ai: false, unknown: false }, 'Meu texto').kind, 'literal');
  assert.equal(reviewGuidance({ organized_text: '', original_text: 'Não sei', assisted_by_ai: false, unknown: true }, '').kind, 'unknown');
});

test('enrichment is opt-in, labeled, deduplicated and does not incorporate unanswered questions', () => {
  const result = { organized_text: 'Proposta inicial.', suggestions: ['Avaliar implantação gradual.', 'Examinar custos.'], open_questions: ['Quem paga?'] };
  assert.equal(confirmedGuidanceText(result, [], 'proposal'), 'Proposta inicial.');
  assert.equal(confirmedGuidanceText(result, [0, 0, -1, 99, 0.5], 'proposal'), 'Proposta inicial.\n\nSugestão de IA a avaliar: Avaliar implantação gradual.');
  assert.ok(!confirmedGuidanceText(result, [1], 'proposal').includes('Quem paga?'));
  assert.throws(() => confirmedGuidanceText({ organized_text: 'x'.repeat(200), suggestions: ['Outra sugestão'] }, [0], 'title'));
});
test('Gemini receives only bounded confirmed text excerpts, with no money or unconfirmed suggestion', () => {
  const input = emptyIdea(); input.title = 'Título'; input.content.problem = 'p'.repeat(4000);
  input.content.impacts = [{ amount: '999', year: 2026, description: 'Privado' }];
  const context = guidanceContext(input);
  assert.deepEqual(Object.keys(context), ['title', 'problem']);
  assert.equal(context.problem.length, 1500);
  assert.equal(JSON.stringify(context).includes('999'), false);
});
