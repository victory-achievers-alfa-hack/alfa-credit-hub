import { NextActions } from '../components/NextActions';
import { useMemo, useState, useRef } from 'react';
import { Button } from '@alfalab/core-components/button';
import { Input } from '@alfalab/core-components/input';
import { Typography } from '@alfalab/core-components/typography';
import { useNavigate } from 'react-router-dom';
import { PageHeader } from '../components/PageHeader';
import { SegmentedControl } from '../components/SegmentedControl';
import { useAuth } from '../context/AutoContext';
import { useCredit } from '../context/CreditContext';
import { PURPOSE_LABELS } from '../data/mockData';
import type { CreditPurpose, Recommendation } from '../types/credit';
import { formatMoney } from '../utils/format';

const purposes: CreditPurpose[] = ['goods', 'equipment', 'cash_gap'];

export function FinancingPage() {
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  const { recommend, getCompany, products } = useCredit();
  const company = getCompany(currentUser?.companyId);
  const [purpose, setPurpose] = useState<CreditPurpose>('goods');
  const [amount, setAmount] = useState(800_000);
  const [termMonths, setTermMonths] = useState(24);
  const [calculated, setCalculated] = useState(false);

  const availableTerms = useMemo(() => Array.from(new Set(
    products.filter((product) => product.purposes.includes(purpose)).flatMap((product) => product.terms),
  )).sort((first, second) => first - second), [purpose, products]);

  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [preference, setPreference] = useState<'min_interest' | 'min_payment'>('min_interest');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const requestVersion = useRef(0);
  const invalidate = () => { requestVersion.current++; setCalculated(false); setLoading(false); };
  const calculate = async () => {
    if (!company) return;
    const version = ++requestVersion.current;
    setLoading(true); setError(''); setCalculated(false);
    try {
      const result = await recommend({ companyId: company.id, purpose, amount, termMonths, preference });
      if (version === requestVersion.current) { setRecommendations(result); setCalculated(true); }
    } catch (e) { if (version === requestVersion.current) setError(e instanceof Error ? e.message : 'Ошибка расчёта'); }
    finally { if (version === requestVersion.current) setLoading(false); }
  };
  const groupLabels: Record<string, string> = {
    requested: 'Запрошенные сумма и срок', other_terms: 'Полная сумма на другой срок',
    reduced_amount: 'Меньшая сумма', requires_action: 'Требуются дополнительные действия', unavailable: 'Недоступные условия',
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

          <label>Приоритет
            <select value={preference} onChange={e => { setPreference(e.target.value as typeof preference); invalidate(); }}>
              <option value="min_interest">Меньше переплата</option><option value="min_payment">Меньше платёж</option>
            </select>
          </label>
          {error && <p role="alert">{error}</p>}
          <Button view="accent" size={56} block onClick={() => void calculate()} disabled={loading || amount <= 0 || !Number.isFinite(amount)}>

            {loading ? 'Рассчитываем…' : 'Рассчитать предложения'}
          </Button>
        </section>

        <aside className="financing-side-note">
          <span className="financing-side-note__icon">i</span>
          <strong>Расчёт прозрачный</strong>
          <p>Подбор выполняется по правилам каталога. ИИ не меняет ставку и не принимает кредитное решение.</p>
        </aside>
      </div>

      {calculated && (
        <section className="recommendations-section">
          <div className="section-heading">
            <div>
              <div className="eyebrow">Результат расчёта</div>
              <Typography.Title tag="h2" view="medium" weight="bold">
                {recommendations.length > 0 ? `Рассмотрено вариантов: ${recommendations.length}` : 'Подходящих вариантов нет'}
              </Typography.Title>
            </div>
          </div>

          {recommendations.length === 0 ? (
            <div className="surface-card empty-state empty-state--large">
              <span className="empty-state__icon">↙</span>
              <strong>Измените сумму или срок</strong>
              <p>В каталоге нет продукта, который одновременно подходит по цели, диапазону суммы и сроку.</p>
            </div>
          ) : (
            <div className="recommendation-grid">
              {recommendations.map((item, index) => (
                <article className={`recommendation-card${item.eligible ? ' recommendation-card--best' : ''}`} key={`${item.group}-${item.product.id}-${item.termMonths}-${item.amount}`}>
                  <p>{groupLabels[item.group ?? 'requested']}</p><div className="recommendation-card__top">
                    <span className={`product-accent product-accent--${item.product.accent}`}>{index + 1}</span>
                    <span className={`soft-tag${item.eligible ? ' soft-tag--positive' : ' soft-tag--warning'}`}>
                      {item.eligible ? 'Проходит правила' : 'Решение банка'}
                    </span>
                  </div>
                  <div>
                    <Typography.Title tag="h3" view="small" weight="bold">{item.product.name}</Typography.Title>
                    <p className="recommendation-card__description">{item.product.description}</p>
                    <p>{item.highlights?.join(' · ')}</p>
                  </div>
                  <div className="offer-numbers">
                    <div><small>Сумма</small><strong>{formatMoney(item.amount ?? amount)}</strong></div>
                    <div><small>Срок</small><strong>{item.termMonths} мес.</strong></div>
                    <div><small>Переплата по процентам</small><strong>{formatMoney(item.interestAmount ?? 0)}</strong></div>
                    <div><small>Ставка</small><strong>{item.product.rate}%</strong></div>
                    <div><small>Платёж</small><strong>{formatMoney(item.monthlyPayment)}</strong></div>
                    <div><small>Покрытие</small><strong className={item.coverage >= (item.requiredCoverage ?? 1.25) ? 'positive-text' : 'warning-text'}>{item.coverage.toFixed(2)}×</strong></div>
                  </div>
                  <div className={`explanation-box${item.warning ? ' explanation-box--warning' : ''}`}>
                    <strong>{item.warning ? 'На что обратить внимание' : 'Почему подходит'}</strong>
                    <p>{item.warning ?? item.reason}</p><p>{item.rankingReason}</p>
                    {item.recommendedAmount && (
                      <span>Комфортная сумма по расчёту: <b>{formatMoney(item.recommendedAmount)}</b></span>
                    )}
                  </div>
                  <NextActions actions={item.actions} />
                  <Button
                    view={index === 0 ? 'accent' : 'secondary'}
                    size={48}
                    block
                    disabled={!item.eligible && item.group !== 'requires_action'}
                    onClick={() => navigate(`/client/apply?product=${encodeURIComponent(item.product.id)}&purpose=${purpose}&amount=${item.amount ?? amount}&term=${item.termMonths ?? termMonths}`)}
                  >
                    {item.reviewRequired ? 'На рассмотрение банка' : 'Выбрать продукт'}
                  </Button>
                </article>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
