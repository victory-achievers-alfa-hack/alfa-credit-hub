import assert from 'node:assert/strict';
import { test } from 'node:test';
import { getRankingNote, getRecommendationCounts, getRecommendationInfo, recommendationGroups } from '../src/utils/financing.ts';
import { formatMoney } from '../src/utils/format.ts';

const coverage = { code: 'INSUFFICIENT_COVERAGE', message: 'Длинное пояснение об округлении', minimum: 1.25 };
const lowerAmount = { code: 'LOWER_AMOUNT_AVAILABLE', message: 'Доступна меньшая сумма на том же сроке; требуется согласие клиента.' };
const prequalified = { code: 'PREQUALIFIED', message: 'Не окончательное одобрение.' };

function offer(amount, termMonths, reasons = [coverage, lowerAmount]) {
  return {
    offer: { amount, termMonths },
    evaluation: { reasons },
    selectedEvaluation: { reasons: [prequalified], policyPasses: true },
  };
}

function response(summary = {}, groups = {}) {
  return {
    requestSummary: { exactMatchCount: 0, exactReviewCount: 0, otherTermCount: 0, reducedAmountCount: 0, ...summary },
    groups: Object.fromEntries(recommendationGroups.map((group) => [group, groups[group] ?? []])),
  };
}

function total(result) {
  const counts = getRecommendationCounts(result);
  assert.equal(counts.reduce((sum, item) => sum + item.count, 0), Object.values(result.groups).flat().length);
  return counts.map(({ count }) => count);
}

test('city: all six considered variants include four alternatives and two unavailable', () => {
  const result = response({ reducedAmountCount: 4 }, {
    reduced_amount: [offer(200000, 36), offer(150000, 24), offer(140000, 24), offer(80000, 12)],
    unavailable: [offer(800000, 12), offer(800000, 24)],
  });
  assert.deepEqual(total(result), [0, 0, 0, 4, 0, 2]);
});

test('exact and full-amount other-term variants remain separate', () => {
  const result = response({ exactMatchCount: 2, otherTermCount: 3 }, {
    requested: [offer(800000, 24), offer(800000, 24)],
    other_terms: [offer(800000, 12), offer(800000, 12), offer(800000, 36)],
    unavailable: [offer(800000, 24)],
  });
  assert.deepEqual(total(result), [2, 0, 3, 0, 0, 1]);
});

test('review alternatives are not double-counted as exact review or pending actions', () => {
  const review = (amount, term) => ({ ...offer(amount, term), selectedEvaluation: { policyPasses: true, reviewRequired: true } });
  const result = response({ exactReviewCount: 1, otherTermCount: 1, reducedAmountCount: 1 }, {
    requires_action: [review(800000, 24), review(800000, 36), review(200000, 36), { selectedEvaluation: { policyPasses: false } }],
  });
  assert.deepEqual(total(result), [0, 1, 1, 1, 1, 0]);
});

test('empty groups have zero counters', () => {
  assert.deepEqual(total(response()), [0, 0, 0, 0, 0, 0]);
});

test('exact conditions have no invented differences', () => {
  const info = getRecommendationInfo(offer(800000, 24, [prequalified]), 800000, 24);
  assert.deepEqual(info.changes, []);
  assert.deepEqual(info.reasons, []);
});

test('a full-amount alternative changes only the term', () => {
  const info = getRecommendationInfo(offer(800000, 36, []), 800000, 24);
  assert.deepEqual(info.changes, ['Срок: 24 → 36 мес.']);
  assert.deepEqual(info.reasons, []);
});

test('a smaller amount on the original term changes only the amount', () => {
  const info = getRecommendationInfo(offer(150000, 24), 800000, 24);
  assert.deepEqual(info.changes, [`Сумма: ${formatMoney(800000)} → ${formatMoney(150000)}.`]);
  assert.deepEqual(info.reasons, ['Исходный запрос (24 мес.): Недостаточно покрытия платежей (минимум 1,25×).']);
});

test('both actual changes are shown without the misleading same-term reason', () => {
  const item = offer(200000, 36);
  // Presentation uses actual request/offer values, not potentially stale convenience flags.
  item.termChanged = false;
  item.amountShortfall = 0;
  const info = getRecommendationInfo(item, 800000, 24);
  assert.deepEqual(info.changes, [
    `Сумма: ${formatMoney(800000)} → ${formatMoney(200000)}.`,
    'Срок: 24 → 36 мес.',
  ]);
  assert.equal(info.reasons.length, 1);
  assert.doesNotMatch(JSON.stringify(info), /на том же сроке/);
  assert.match(info.notice, /Запрос не изменён/);
  assert.match(info.notice, /с согласия клиента/);
});

test('the original product check is retained even when evaluation uses another term', () => {
  const originalCheck = { reasons: [{ code: 'TERM_UNSUPPORTED', message: 'Длинный текст', allowedValues: [12, 24] }] };
  const info = getRecommendationInfo(offer(200000, 24), 800000, 60, originalCheck);
  assert.deepEqual(info.changes.at(-1), 'Срок: 60 → 24 мес.');
  assert.deepEqual(info.reasons, [
    'Исходный запрос (60 мес.): Исходный срок недоступен. Допустимо: 12, 24 мес.',
    'При исходной сумме на 24 мес.: Недостаточно покрытия платежей (минимум 1,25×).',
  ]);
});

test('thresholds and limits come from each reason rather than fixed UI policy', () => {
  const info = getRecommendationInfo(offer(200000, 24, [
    { ...coverage, minimum: 1.5 },
    { code: 'REVIEW_AMOUNT_LIMIT', maximum: 450000, message: 'Длинное пояснение' },
  ]), 800000, 24);
  assert.deepEqual(info.reasons, [
    'Исходный запрос (24 мес.): Недостаточно покрытия платежей (минимум 1,5×).',
    `Исходный запрос (24 мес.): Лимит по профилю: ${formatMoney(450000)}.`,
  ]);
});

test('selected-offer restrictions and unknown reason codes are preserved and deduplicated', () => {
  const reason = { code: 'FUTURE_REASON', message: 'Важное ограничение API' };
  const item = offer(200000, 36, [reason, coverage]);
  item.selectedEvaluation.reasons = [reason];
  const info = getRecommendationInfo(item, 800000, 24, { reasons: [reason, coverage] });
  assert.deepEqual(info.reasons, [
    'Исходный запрос (24 мес.): Важное ограничение API',
    'Исходный запрос (24 мес.): Недостаточно покрытия платежей (минимум 1,25×).',
  ]);
});

test('missing optional reason details fall back to the API message', () => {
  const reason = { code: 'INSUFFICIENT_COVERAGE', minimum: null, message: 'Пояснение сервера' };
  const info = getRecommendationInfo(offer(200000, 24, [reason]), 800000, 24);
  assert.deepEqual(info.reasons, ['Исходный запрос (24 мес.): Пояснение сервера']);
});

test('an unavailable original term does not label a passing alternative as unavailable', () => {
  const originalCheck = { reasons: [coverage, { code: 'NO_AFFORDABLE_AMOUNT', message: 'Нет доступной суммы на выбранном сроке.' }] };
  const info = getRecommendationInfo(offer(200000, 36), 800000, 12, originalCheck);
  assert.deepEqual(info.reasons, [
    'Исходный запрос (12 мес.): Недостаточно покрытия платежей (минимум 1,25×).',
    'Исходный запрос (12 мес.): Нет доступной суммы в пределах продукта.',
  ]);
});

test('new limitations at the alternative term keep their own context', () => {
  const info = getRecommendationInfo(offer(200000, 12), 800000, 36, { reasons: [prequalified] });
  assert.deepEqual(info.reasons, ['При исходной сумме на 12 мес.: Недостаточно покрытия платежей (минимум 1,25×).']);
});

test('selected evaluation limitations are identified as alternative conditions', () => {
  const item = offer(200000, 36, []);
  item.selectedEvaluation.reasons = [{ code: 'SCORE_REVIEW', message: 'Нужно рассмотрение банка.' }];
  const info = getRecommendationInfo(item, 800000, 24, { reasons: [] });
  assert.deepEqual(info.reasons, ['Условия альтернативы: Нужно рассмотрение банка.']);
});

test('kopecks are not rounded away in actual differences', () => {
  const info = getRecommendationInfo(offer(150000.25, 24, []), 800000.50, 24);
  assert.deepEqual(info.changes, [`Сумма: ${formatMoney(800000.50)} → ${formatMoney(150000.25)}.`]);
});

test('only the shared disclaimer is removed from ranking copy', () => {
  assert.equal(getRankingNote('Сначала большая сумма. Предварительная оценка, не одобрение банка.'), 'Сначала большая сумма.');
  const custom = 'Нужны действия; порядок не означает рекомендацию.';
  assert.equal(getRankingNote(custom), custom);
});
