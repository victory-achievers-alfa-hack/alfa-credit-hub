import { useMemo, useRef, useState, type ComponentProps } from 'react';
import { Button } from '@alfalab/core-components/button';
import { Input } from '@alfalab/core-components/input';
import { SelectDesktop as Select } from '@alfalab/core-components/select/desktop';
import { Typography } from '@alfalab/core-components/typography';
import { useNavigate, type NavigateFunction } from 'react-router-dom';
import { NextActions } from '../components/NextActions';
import { PageHeader } from '../components/PageHeader';
import { SegmentedControl } from '../components/SegmentedControl';
import { StressPanel } from '../components/StressPanel';
import { useAuth } from '../context/AutoContext';
import { useCredit } from '../context/CreditContext';
import { PURPOSE_LABELS } from '../constants';
import type {
  CreditPurpose,
  Recommendation,
  RecommendationAssessment,
  RecommendationGroup,
  RecommendationResponse,
  RequestSummaryStatus,
} from '../types/credit';
import { formatDateTime, formatMoney } from '../utils/format';

const purposes: CreditPurpose[] = ['goods', 'equipment', 'cash_gap'];
const APPLICATION_MIN_AMOUNT = 50_000;
const APPLICATION_MAX_AMOUNT = 5_000_000;
const recommendationGroups: RecommendationGroup[] = [
  'requested',
  'other_terms',
  'reduced_amount',
  'requires_action',
  'unavailable',
];
const preferenceOptions = [
  { key: 'min_interest', content: 'Минимальная переплата' },
  { key: 'min_payment', content: 'Минимальный платёж' },
];
const groupCopy: Record<RecommendationGroup, { title: string; description: string }> = {
  requested: {
    title: 'Запрошенные сумма и срок',
    description: 'Параметры совпадают с исходным запросом.',
  },
  other_terms: {
    title: 'Полная сумма на другой срок',
    description: 'Сумма сохранена, но срок отличается от исходного запроса.',
  },
  reduced_amount: {
    title: 'Альтернативы с меньшей суммой',
    description: 'Исходный запрос не изменён: ниже показаны отдельные доступные альтернативы.',
  },
  requires_action: {
    title: 'Требуются проверка или действия',
    description: 'Эти варианты нельзя считать предварительно одобренными.',
  },
  unavailable: {
    title: 'Недоступные условия',
    description: 'Причины недоступности показаны по каждому продукту.',
  },
};
const summaryTitles: Record<RequestSummaryStatus, string> = {
  exact_available: 'Точные условия предварительно проходят',
  exact_review: 'Точные условия требуют рассмотрения',
  alternatives_available: 'Доступны только изменённые условия',
  information_required: 'Нужно уточнить сведения',
  unavailable: 'Подходящих условий нет',
};
const assessmentCopy: Record<RecommendationAssessment, { label: string; tone: string }> = {
  eligible: { label: 'Предварительно проходит', tone: 'positive' },
  alternative: { label: 'Изменённые условия', tone: 'warning' },
  need_info: { label: 'Нужны сведения', tone: 'warning' },
  manual_review: { label: 'Рассмотрение банка', tone: 'warning' },
  blocked: { label: 'Подача заблокирована', tone: 'negative' },
  unavailable: { label: 'Недоступно', tone: 'negative' },
};

type ButtonView = ComponentProps<typeof Button>['view'];

function uniqueReasons(reasons: Recommendation['evaluation']['reasons']) {
  return reasons.filter(
    (reason, index) => reasons.findIndex((candidate) => candidate.message === reason.message) === index,
  );
}

function getAssessmentCopy(assessment: string) {
  return assessmentCopy[assessment as RecommendationAssessment]
    ?? { label: 'Требует проверки', tone: 'warning' };
}

function RecommendationCard({
  item,
  purpose,
  requestedTermMonths,
  navigate,
}: {
  item: Recommendation;
  purpose: CreditPurpose;
  requestedTermMonths: number;
  navigate: NavigateFunction;
}) {
  const assessment = getAssessmentCopy(item.selectedEvaluation.assessment);
  const reasons = uniqueReasons(item.selectedEvaluation.reasons);
  const originalReasons = uniqueReasons(item.evaluation.reasons).filter(
    (reason) => !reasons.some((selectedReason) => selectedReason.message === reason.message),
  );
  const canApply = item.group !== 'unavailable' && item.selectedEvaluation.policyPasses;
  const changedTerms = item.termChanged || item.amountShortfall > 0;
  const isAlternative = item.group === 'other_terms' || item.group === 'reduced_amount';
  const buttonView: ButtonView = item.group === 'requested' && item.rankInGroup === 1 ? 'accent' : 'secondary';
  const buttonLabel = !canApply
    ? item.selectedEvaluation.assessment === 'need_info'
      ? 'Сначала уточните сведения'
      : item.selectedEvaluation.assessment === 'blocked'
        ? 'Подача недоступна'
        : 'Условия недоступны'
    : item.selectedEvaluation.reviewRequired
      ? 'Отправить на рассмотрение'
      : isAlternative
        ? 'Выбрать альтернативу'
        : 'Выбрать продукт';

  return (
    <article
      className={`recommendation-card${item.selectedEvaluation.policyPasses ? ' recommendation-card--best' : ''}`}
    >
      <div className="recommendation-card__top">
        <span className={`product-accent product-accent--${item.product.accent}`}>{item.rankInGroup}</span>
        <span className={`soft-tag soft-tag--${assessment.tone}`}>
          {isAlternative && item.selectedEvaluation.assessment === 'eligible'
            ? 'Альтернатива проходит'
            : assessment.label}
        </span>
      </div>

      <div>
        <Typography.Title tag="h3" view="small" weight="bold">{item.product.name}</Typography.Title>
        <p className="recommendation-card__description">{item.product.description}</p>
      </div>

      {changedTerms ? (
        <div className="offer-differences" aria-label="Отличия от исходного запроса">
          {item.termChanged && (
            <span>Срок изменён: <b>{requestedTermMonths} → {item.offer.termMonths} мес.</b></span>
          )}
          {item.amountShortfall > 0 && (
            <span>Сумма уменьшена на <b>{formatMoney(item.amountShortfall)}</b></span>
          )}
          {originalReasons.length > 0 && (
            <div className="offer-differences__reasons">
              <strong>Почему исходные условия изменены</strong>
              <ul>{originalReasons.map((reason) => <li key={reason.code}>{reason.message}</li>)}</ul>
            </div>
          )}
          <small>Исходный запрос сохранён без автоматической подмены.</small>
        </div>
      ) : (
        <p className="exact-request-note">Сумма и срок точно соответствуют запросу.</p>
      )}

      <div className="offer-numbers">
        <div><small>Сумма</small><strong>{formatMoney(item.offer.amount)}</strong></div>
        <div><small>Срок</small><strong>{item.offer.termMonths} мес.</strong></div>
        <div><small>Переплата</small><strong>{formatMoney(item.offer.interestAmount)}</strong></div>
        <div><small>Ставка</small><strong>{item.offer.rate}%</strong></div>
        <div><small>Платёж</small><strong>{formatMoney(item.offer.monthlyPayment)}</strong></div>
        <div>
          <small>Покрытие</small>
          <strong className={item.selectedEvaluation.coveragePasses ? 'positive-text' : 'warning-text'}>
            {item.offer.coverage.toFixed(2)}×
          </strong>
        </div>
      </div>

      {item.comparisonCount >= 2 && item.comparisonAmount !== null && (
        <div className="comparison-context">
          <strong>Сравнение {item.comparisonCount} вариантов на {formatMoney(item.comparisonAmount)}</strong>
          {item.highlights.length > 0 && <p>{item.highlights.join(' · ')}</p>}
        </div>
      )}

      {reasons.length > 0 && (
        <div className={`recommendation-reasons${item.selectedEvaluation.policyPasses ? '' : ' recommendation-reasons--warning'}`}>
          <strong>{item.selectedEvaluation.policyPasses ? 'Условия и ограничения' : 'Почему вариант не проходит'}</strong>
          <ul>{reasons.map((reason) => <li key={reason.code}>{reason.message}</li>)}</ul>
          {item.evaluation.recommendedAmount !== null && item.evaluation.recommendedAmount !== item.offer.amount && (
            <p>Расчётная доступная сумма: <b>{formatMoney(item.evaluation.recommendedAmount)}</b></p>
          )}
        </div>
      )}

      {(item.group === 'requires_action' || item.group === 'unavailable') && (
        <details className="recommendation-constraints">
          <summary>Точные ограничения продукта</summary>
          <dl>
            <div><dt>Сумма продукта</dt><dd>{formatMoney(item.selectedEvaluation.constraints.productMinAmount)} — {formatMoney(item.selectedEvaluation.constraints.productMaxAmount)}</dd></div>
            <div><dt>Допустимые сроки</dt><dd>{item.selectedEvaluation.constraints.allowedTerms.join(', ')} мес.</dd></div>
            <div><dt>Лимит по профилю</dt><dd>{formatMoney(item.selectedEvaluation.constraints.appliedAmountLimit)}</dd></div>
            <div><dt>Требуемое покрытие</dt><dd>{item.selectedEvaluation.constraints.requiredCoverage.toFixed(2)}×</dd></div>
          </dl>
        </details>
      )}

      <NextActions actions={item.selectedEvaluation.actions} />
      {item.group !== 'unavailable' && <StressPanel stress={item.stress} />}

      <Button
        view={buttonView}
        size={48}
        block
        disabled={!canApply}
        onClick={() => navigate(`/client/apply?product=${encodeURIComponent(item.product.id)}&purpose=${purpose}&amount=${item.offer.amount}&term=${item.offer.termMonths}`)}
      >
        {buttonLabel}
      </Button>
    </article>
  );
}

export function FinancingPage() {
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  const { recommend, getCompany, products } = useCredit();
  const company = getCompany(currentUser?.companyId);
  const [purpose, setPurpose] = useState<CreditPurpose>('goods');
  const [amount, setAmount] = useState(800_000);
  const [termMonths, setTermMonths] = useState(24);
  const [result, setResult] = useState<RecommendationResponse>();
  const [calculated, setCalculated] = useState(false);
  const [preference, setPreference] = useState<'min_interest' | 'min_payment'>('min_interest');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const requestVersion = useRef(0);

  const availableTerms = useMemo(() => Array.from(new Set(
    products.filter((product) => product.purposes.includes(purpose)).flatMap((product) => product.terms),
  )).sort((first, second) => first - second), [purpose, products]);

  const invalidate = () => {
    requestVersion.current++;
    setCalculated(false);
    setLoading(false);
  };
  const calculate = async () => {
    if (!company) return;
    const version = ++requestVersion.current;
    setLoading(true);
    setError('');
    setCalculated(false);
    try {
      const response = await recommend({ companyId: company.id, purpose, amount, termMonths, preference });
      if (version === requestVersion.current) {
        setResult(response);
        setCalculated(true);
      }
    } catch (calculationError) {
      if (version === requestVersion.current) {
        setError(calculationError instanceof Error ? calculationError.message : 'Ошибка расчёта');
      }
    } finally {
      if (version === requestVersion.current) setLoading(false);
    }
  };

  if (!company) return null;

  const changePurpose = (nextPurpose: CreditPurpose) => {
    setPurpose(nextPurpose);
    const terms = Array.from(new Set(
      products.filter((product) => product.purposes.includes(nextPurpose)).flatMap((product) => product.terms),
    ));
    if (!terms.includes(termMonths)) setTermMonths(terms[0] ?? 12);
    invalidate();
  };
  const recommendationCount = result
    ? recommendationGroups.reduce((count, group) => count + result.groups[group].length, 0)
    : 0;

  return (
    <div className="page-shell">
      <PageHeader
        eyebrow="Умный подбор"
        title="Подберём финансирование"
        description="Укажите задачу бизнеса. Мы сопоставим запрос с каталогом и финансовым профилем компании."
      />

      <div className="financing-layout">
        <section className="surface-card financing-form-card">
          <div className="form-step">
            <span className="form-step__number">1</span>
            <div>
              <strong>Для чего нужны деньги?</strong>
              <p>Цель определяет доступные продукты.</p>
            </div>
          </div>
          <div className="choice-grid">
            {purposes.map((item) => (
              <button
                type="button"
                className={`choice-card${purpose === item ? ' choice-card--active' : ''}`}
                key={item}
                onClick={() => changePurpose(item)}
              >
                <span className="choice-card__icon">{item === 'goods' ? '▦' : item === 'equipment' ? '⚙' : '↔'}</span>
                <strong>{PURPOSE_LABELS[item]}</strong>
                <small>{item === 'goods' ? 'Запасы и оборот' : item === 'equipment' ? 'Рост и модернизация' : 'Текущие обязательства'}</small>
              </button>
            ))}
          </div>

          <div className="form-step">
            <span className="form-step__number">2</span>
            <div>
              <strong>Сумма и срок</strong>
              <p>Покажем платёж и влияние на нагрузку.</p>
            </div>
          </div>
          <div className="financing-fields">
            <Input
              label="Сумма кредита"
              labelView="outer"
              type="number"
              size={56}
              block
              value={String(amount)}
              rightAddons="₽"
              onChange={(_, payload) => { setAmount(Number(payload.value)); invalidate(); }}
              hint="От 50 000 до 5 000 000 ₽"
            />
            <div className="field-group">
              <label>Срок кредита</label>
              <SegmentedControl<number>
                value={termMonths}
                options={availableTerms.map((term) => ({ value: term, label: `${term} мес.` }))}
                onChange={(term) => { setTermMonths(term); invalidate(); }}
                ariaLabel="Срок кредита"
                className="segmented-control--terms"
              />
            </div>
          </div>

          <div className="company-context">
            <span className="company-context__icon">A</span>
            <span><small>Расчёт для</small><strong>{company.name}</strong></span>
            <span><small>Поток до долгов</small><strong>{formatMoney(company.monthlyRevenue - company.monthlyExpenses)}</strong></span>
            <span><small>Текущие платежи</small><strong>{formatMoney(company.existingPayments)}</strong></span>
          </div>

          <Select
            className="financing-priority"
            label="Приоритет подбора"
            labelView="outer"
            size={56}
            block
            options={preferenceOptions}
            optionsListWidth="field"
            selected={preference}
            onChange={({ selected }) => {
              if (selected?.key !== 'min_interest' && selected?.key !== 'min_payment') return;
              setPreference(selected.key);
              invalidate();
            }}
          />
          {error && <p role="alert">{error}</p>}
          <Button
            view="accent"
            size={56}
            block
            onClick={() => void calculate()}
            disabled={loading || !Number.isFinite(amount) || amount < APPLICATION_MIN_AMOUNT || amount > APPLICATION_MAX_AMOUNT}
          >
            {loading ? 'Рассчитываем…' : 'Рассчитать предложения'}
          </Button>
        </section>

        <aside className="financing-side-note">
          <span className="financing-side-note__icon">i</span>
          <strong>Расчёт прозрачный</strong>
          <p>Подбор выполняется по правилам каталога. ИИ не меняет ставку и не принимает кредитное решение.</p>
        </aside>
      </div>

      {calculated && result && (
        <section className="recommendations-section">
          <div className="section-heading">
            <div>
              <div className="eyebrow">Результат расчёта</div>
              <Typography.Title tag="h2" view="medium" weight="bold">
                {recommendationCount > 0 ? `Рассмотрено вариантов: ${recommendationCount}` : 'Подходящих вариантов нет'}
              </Typography.Title>
            </div>
            <small>Рассчитано {formatDateTime(result.calculatedAt)}</small>
          </div>

          <div className={`request-result request-result--${result.requestSummary.status}`}>
            <div>
              <strong>{summaryTitles[result.requestSummary.status]}</strong>
              <p>{result.requestSummary.message}</p>
              <small>Исходный запрос: {formatMoney(result.requestedAmount)} на {result.requestedTermMonths} мес. Он не меняется автоматически.</small>
            </div>
            <dl>
              <div><dt>Точные варианты</dt><dd>{result.requestSummary.exactMatchCount}</dd></div>
              <div><dt>На рассмотрение</dt><dd>{result.requestSummary.exactReviewCount}</dd></div>
              <div><dt>Другой срок</dt><dd>{result.requestSummary.otherTermCount}</dd></div>
              <div><dt>Меньшая сумма</dt><dd>{result.requestSummary.reducedAmountCount}</dd></div>
            </dl>
          </div>

          <details className="surface-card request-checks">
            <summary>Проверки исходного запроса по продуктам</summary>
            <div className="request-checks__list">
              {result.requestChecks.map((check) => {
                const copy = getAssessmentCopy(check.assessment);
                return (
                  <div className="request-check" key={check.productId}>
                    <div>
                      <strong>{check.productName}</strong>
                      <span className={`soft-tag soft-tag--${copy.tone}`}>{copy.label}</span>
                    </div>
                    {check.reasons.length > 0
                      ? <ul>{check.reasons.map((reason) => <li key={reason.code}>{reason.message}</li>)}</ul>
                      : <p>Ограничения исходного запроса пройдены.</p>}
                  </div>
                );
              })}
            </div>
          </details>

          {recommendationCount === 0 ? (
            <div className="surface-card empty-state empty-state--large">
              <span className="empty-state__icon">↙</span>
              <strong>Измените сумму или срок</strong>
              <p>В каталоге нет продукта, который подходит по цели, диапазону суммы, сроку и финансовым ограничениям.</p>
            </div>
          ) : recommendationGroups.map((group) => {
            const items = result.groups[group];
            if (items.length === 0) return null;
            return (
              <section className={`recommendation-group recommendation-group--${group}`} key={group}>
                <div className="recommendation-group__heading">
                  <div>
                    <Typography.Title tag="h3" view="small" weight="bold">{groupCopy[group].title}</Typography.Title>
                    <p>{groupCopy[group].description}</p>
                  </div>
                  <span>{items.length}</span>
                </div>
                <p className="ranking-note">{items[0].rankingReason}</p>
                <div className="recommendation-grid">
                  {items.map((item) => (
                    <RecommendationCard
                      item={item}
                      purpose={purpose}
                      requestedTermMonths={result.requestedTermMonths}
                      navigate={navigate}
                      key={`${item.group}-${item.product.id}-${item.offer.termMonths}-${item.offer.amount}`}
                    />
                  ))}
                </div>
              </section>
            );
          })}
        </section>
      )}
    </div>
  );
}
