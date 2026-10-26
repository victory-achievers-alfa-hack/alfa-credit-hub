import type {
  Recommendation,
  RecommendationReason,
  RecommendationResponse,
  RequestedProductCheck,
} from '../types/credit';
import { formatMoney } from './format.ts';

export const recommendationGroups = [
  'requested',
  'other_terms',
  'reduced_amount',
  'requires_action',
  'unavailable',
] as const;

export function getRecommendationCounts(result: RecommendationResponse) {
  // Review alternatives already belong to the amount/term counters, not to exact review.
  const actions = result.groups.requires_action.filter((item) => !item.selectedEvaluation.policyPasses).length;
  return [
    { key: 'exact', label: 'Точные варианты', count: result.requestSummary.exactMatchCount },
    { key: 'review', label: 'Точные на рассмотрение', count: result.requestSummary.exactReviewCount },
    { key: 'term', label: 'Полная сумма, другой срок', count: result.requestSummary.otherTermCount },
    { key: 'amount', label: 'Меньшая сумма', count: result.requestSummary.reducedAmountCount },
    { key: 'actions', label: 'Нужны действия', count: actions },
    { key: 'unavailable', label: 'Недоступны', count: result.groups.unavailable.length },
  ];
}

export function getRankingNote(reason: string): string {
  return reason.replace(/\s*Предварительная оценка, не одобрение банка\.$/, '');
}

function compactReason(reason: RecommendationReason): string | null {
  switch (reason.code) {
    case 'PREQUALIFIED':
    case 'LOWER_AMOUNT_AVAILABLE':
      // The shared notice and actual differences replace these generic messages.
      return null;
    case 'INSUFFICIENT_COVERAGE':
      return typeof reason.minimum === 'number'
        ? `Недостаточно покрытия платежей (минимум ${reason.minimum.toLocaleString('ru-RU')}×).`
        : reason.message;
    case 'TERM_UNSUPPORTED':
      return reason.allowedValues?.length
        ? `Исходный срок недоступен. Допустимо: ${reason.allowedValues.join(', ')} мес.`
        : reason.message;
    case 'REVIEW_AMOUNT_LIMIT':
      return typeof reason.maximum === 'number'
        ? `Лимит по профилю: ${formatMoney(reason.maximum)}.`
        : reason.message;
    case 'NO_AFFORDABLE_AMOUNT':
      return 'Нет доступной суммы в пределах продукта.';
    default:
      return reason.message;
  }
}

export function getRecommendationInfo(
  item: Recommendation,
  requestedAmount: number,
  requestedTermMonths: number,
  originalCheck?: RequestedProductCheck,
) {
  const changes: string[] = [];
  if (item.offer.amount !== requestedAmount) {
    changes.push(`Сумма: ${formatMoney(requestedAmount)} → ${formatMoney(item.offer.amount)}.`);
  }
  if (item.offer.termMonths !== requestedTermMonths) {
    changes.push(`Срок: ${requestedTermMonths} → ${item.offer.termMonths} мес.`);
  }

  // evaluation is calculated at the offer's term, which may differ from the original request.
  const reasons: string[] = [];
  const seen = new Set<string>();
  const addReasons = (items: RecommendationReason[], context: string) => {
    for (const reason of items) {
      const message = compactReason(reason);
      if (message && !seen.has(message)) {
        reasons.push(`${context}: ${message}`);
        seen.add(message);
      }
    }
  };
  const originalContext = `Исходный запрос (${requestedTermMonths} мес.)`;
  const offerTermContext = `При исходной сумме на ${item.offer.termMonths} мес.`;
  if (originalCheck) addReasons(originalCheck.reasons, originalContext);
  addReasons(item.evaluation.reasons, item.offer.termMonths === requestedTermMonths ? originalContext : offerTermContext);
  addReasons(item.selectedEvaluation.reasons, 'Условия альтернативы');

  return {
    changes,
    reasons,
    notice: 'Запрос не изменён. Выбор альтернативы — с согласия клиента.',
  };
}
