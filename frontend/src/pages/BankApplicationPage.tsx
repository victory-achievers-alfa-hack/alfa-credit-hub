
import { NextActions } from '../components/NextActions';
import { useState } from 'react';
import { Button } from '@alfalab/core-components/button';
import { Input } from '@alfalab/core-components/input';
import { Typography } from '@alfalab/core-components/typography';
import { useNavigate, useParams } from 'react-router-dom';
import { ApplicationStatusBadge } from '../components/ApplicationStatusBadge';
import { useCredit } from '../context/CreditContext';
import { PURPOSE_LABELS } from '../constants';
import type { BankDecisionKind } from '../types/credit';
import { formatDate, formatDateTime, formatMoney, formatPercent } from '../utils/format';

export function BankApplicationPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { getCompany, applications, decideApplication } = useCredit();
  const application = applications.find((candidate) => candidate.id === id);
  const company = getCompany(application?.companyId);
  const [decision, setDecision] = useState<BankDecisionKind>(() => application?.status === 'offer' ? 'reject' : 'approve');
  const [amount, setAmount] = useState(() => Math.min(application?.requestedAmount ?? 150_000, 150_000));
  const [termMonths, setTermMonths] = useState(() => application?.requestedTermMonths ?? 24);
  const [rate, setRate] = useState(() => application?.requestedRate ?? 24);
  const [comment, setComment] = useState('');
  const [error, setError] = useState('');

  if (!application || !company) {
    return (
      <div className="page-shell">
        <div className="surface-card empty-state empty-state--large">
          <span className="empty-state__icon">?</span>
          <strong>Заявка не найдена</strong>
          <Button view="accent" size={48} onClick={() => navigate('/bank')}>Вернуться в очередь</Button>
        </div>
      </div>
    );
  }

  const canDecide = application.status === 'review' || application.status === 'offer';
  const revokingOffer = application.status === 'offer';
  const effectiveDecision: BankDecisionKind = revokingOffer ? 'reject' : decision;
  const decisionOptions: ReadonlyArray<readonly [BankDecisionKind, string, string]> = revokingOffer
    ? [['reject', 'Отозвать предложение', 'Завершить заявку с объяснением']]
    : [
        ['approve', 'Одобрить', 'Запрошенные условия'],
        ['alternative', 'Предложить альтернативу', 'Другая сумма или срок'],
        ['need_info', 'Запросить сведения', 'Вернуть клиенту'],
        ['reject', 'Отказать', 'Завершить заявку'],
      ];

  const handleDecision = async () => {
    if (['alternative', 'need_info', 'reject'].includes(effectiveDecision) && !comment.trim()) {
      setError('Укажите причину решения');
      return;
    }
    if (effectiveDecision === 'alternative' && (
      !Number.isFinite(amount) || !Number.isFinite(termMonths) || !Number.isFinite(rate)
      || amount <= 0 || termMonths <= 0 || termMonths > 120 || rate < 0 || rate > 100
    )) {
      setError('Проверьте сумму, срок до 120 месяцев и ставку от 0 до 100%');
      return;
    }

    if (company.scoringScore >= 50 && company.scoringScore < 70
      && ['approve', 'alternative'].includes(effectiveDecision) && comment.trim().length < 20) {
      setError('Для балла 50–69 укажите обоснование решения: не менее 20 символов');
      return;
    }
    const result = await decideApplication(application.id, {
      kind: effectiveDecision,
      ...(effectiveDecision === 'alternative' ? { amount, termMonths, rate } : {}),
      comment: comment.trim() || (effectiveDecision === 'approve' ? 'Заявка соответствует правилам и одобрена на запрошенных условиях.' : 'Альтернативные условия снижают долговую нагрузку.'),
    });
    setError(result.success ? '' : result.error ?? 'Не удалось сохранить решение');
  };

  return (
    <div className="page-shell page-shell--bank">
      <button type="button" className="back-link" onClick={() => navigate('/bank')}>← Очередь заявок</button>

      <section className="bank-application-header surface-card">
        <div>
          <div className="eyebrow">Заявка {application.id}</div>
          <Typography.Title tag="h1" view="large" weight="bold">{company.name}</Typography.Title>
          <p>ИНН {company.inn} · создана {formatDate(application.createdAt)}</p>
        </div>
        <div className="bank-application-header__status">
          <ApplicationStatusBadge status={application.status} />
          <small>Обновлено {formatDateTime(application.updatedAt)}</small>
        </div>
      </section>

      <div className="underwriting-grid">
        <div className="underwriting-main">
          <section className="surface-card detail-section">
            <div className="section-heading section-heading--compact">
              <div>
                <div className="eyebrow">Запрос</div>
                <Typography.Title tag="h2" view="small" weight="bold">Параметры финансирования</Typography.Title>
              </div>
              <span className="soft-tag">{PURPOSE_LABELS[application.purpose]}</span>
            </div>
            <div className="request-summary">
              <div><small>Продукт</small><strong>{application.productName}</strong></div>
              <div><small>Сумма</small><strong>{formatMoney(application.requestedAmount)}</strong></div>
              <div><small>Срок</small><strong>{application.requestedTermMonths} мес.</strong></div>
              <div><small>Ставка</small><strong>{formatPercent(application.requestedRate)}</strong></div>
              <div><small>Новый платёж</small><strong>{formatMoney(application.requestedMonthlyPayment)}</strong></div>
              <div><small>Покрытие</small><strong className={application.coverage >= (application.requiredCoverage ?? 1.25) ? 'positive-text' : 'warning-text'}>{application.coverage.toFixed(2)}×</strong></div>
            </div>
          </section>

          <section className="surface-card scoring-section">
            <div className="scoring-hero">
              <div className={`score-ring score-ring--${application.scoring.riskLevel}`}>
                <strong>{application.scoring.score}</strong><small>из 100</small>
              </div>
              <div>
                <div className="eyebrow">Оценка на момент подачи</div>
                <Typography.Title tag="h2" view="small" weight="bold">
                  {application.scoring.riskLevel === 'low' ? 'Допустимый риск' : application.scoring.riskLevel === 'medium' ? 'Нужно внимание' : 'Высокий риск'}
                </Typography.Title>
                <p>{application.scoring.summary}</p>
                {application.scoring.calculatedAt && (
                  <small className="scoring-calculated-at">
                    Исходная оценка рассчитана {formatDateTime(application.scoring.calculatedAt)}
                  </small>
                )}
                <NextActions actions={application.actions} />

                {company.scoringScore >= 50 && company.scoringScore < 70 && <p>Текущий профиль требует рассмотрения: покрытие от 1,5×, сумма до 50% месячной выручки и обязательное обоснование сотрудника. Ограничения проверяет сервер.</p>}
              </div>
            </div>
            <div className="scoring-factors">
              {application.scoring.factors.map((factor) => (
                <div key={factor.label}>
                  <span className={factor.positive ? 'factor-icon factor-icon--positive' : 'factor-icon factor-icon--negative'}>{factor.positive ? '↗' : '↘'}</span>
                  <span><small>{factor.label}</small><strong>{factor.value}</strong>{factor.points !== undefined && <small>Баллы: {factor.points} из {factor.maxPoints}</small>}</span>
                </div>
              ))}
            </div>
          </section>

          <section className="surface-card detail-section">
            <div className="section-heading section-heading--compact">
              <div>
                <div className="eyebrow">Моки внешних систем</div>
                <Typography.Title tag="h2" view="small" weight="bold">Результаты проверок</Typography.Title>
              </div>
            </div>
            <div className="check-list check-list--bank">
              {application.checks.map((check) => (
                <div className="check-row" key={check.id}>
                  <span className={`check-row__icon check-row__icon--${check.state}`}>{check.state === 'success' ? '✓' : check.state === 'warning' ? '!' : '×'}</span>
                  <span><strong>{check.label}</strong><small>{check.description}</small></span>
                  <b>{check.value}</b>
                </div>
              ))}
            </div>
          </section>

          <section className="surface-card detail-section">
            <div className="section-heading section-heading--compact">
              <div>
                <div className="eyebrow">Профиль</div>
                <Typography.Title tag="h2" view="small" weight="bold">Компания и финансы</Typography.Title>
              </div>
            </div>
            <dl className="detail-list detail-list--two-columns">
              <div><dt>Юридическое лицо</dt><dd>{company.legalName}</dd></div>
              <div><dt>ОКВЭД</dt><dd>{company.okved}</dd></div>
              <div><dt>Выручка / месяц</dt><dd>{formatMoney(company.monthlyRevenue)}</dd></div>
              <div><dt>Расходы / месяц</dt><dd>{formatMoney(company.monthlyExpenses)}</dd></div>
              <div><dt>Старые платежи</dt><dd>{formatMoney(company.existingPayments)}</dd></div>
              <div><dt>Просрочки</dt><dd>{company.hasOverdue ? 'Есть' : 'Нет'}</dd></div>
            </dl>
          </section>
        </div>

        <aside className="underwriting-side">
          {canDecide ? (
            <section className="surface-card decision-card">
              <div className="eyebrow">Решение банка</div>
              <Typography.Title tag="h2" view="small" weight="bold">
                {revokingOffer ? 'Управление предложением' : 'Выберите действие'}
              </Typography.Title>
              {revokingOffer && <p className="decision-card__hint">Backend разрешает отозвать активное предложение до решения клиента.</p>}
              <div className="decision-options">
                {decisionOptions.map(([value, label, hint]) => (
                  <button
                    type="button"
                    className={`decision-option decision-option--${value}${effectiveDecision === value ? ' decision-option--active' : ''}`}
                    key={value}
                    onClick={() => { setDecision(value); setError(''); }}
                  >
                    <span>{effectiveDecision === value ? '●' : '○'}</span>
                    <span><strong>{label}</strong><small>{hint}</small></span>
                  </button>
                ))}
              </div>

              {effectiveDecision === 'alternative' && (
                <div className="decision-fields">
                  <Input label="Предложенная сумма" labelView="outer" type="number" size={48} block value={String(amount)} rightAddons="₽" onChange={(_, payload) => setAmount(Number(payload.value))} />
                  <div className="decision-fields__row">
                    <Input label="Срок" labelView="outer" type="number" size={48} block value={String(termMonths)} rightAddons="мес." onChange={(_, payload) => setTermMonths(Number(payload.value))} />
                    <Input label="Ставка" labelView="outer" type="number" size={48} block value={String(rate)} rightAddons="%" onChange={(_, payload) => setRate(Number(payload.value))} />
                  </div>
                </div>
              )}

              <Input
                label={company.scoringScore >= 50 && company.scoringScore < 70 && ['approve', 'alternative'].includes(effectiveDecision) ? 'Обоснование решения (обязательно, от 20 символов)' : effectiveDecision === 'approve' ? 'Комментарий клиенту (необязательно)' : 'Причина решения'}
                labelView="outer"
                size={56}
                block
                value={comment}
                onChange={(_, payload) => { setComment(payload.value); setError(''); }}
                error={error || false}
                placeholder={effectiveDecision === 'alternative' ? 'Например, снижение суммы из-за нагрузки' : 'Краткое объяснение'}
              />
              <Button view="accent" size={56} block onClick={() => void handleDecision()}>
                {revokingOffer ? 'Отозвать предложение' : 'Зафиксировать решение'}
              </Button>
              <p className="decision-card__hint">Статус изменится у клиента сразу после сохранения.</p>
            </section>
          ) : (
            <section className="surface-card decision-card decision-card--result">
              <ApplicationStatusBadge status={application.status} />
              <Typography.Title tag="h2" view="small" weight="bold">Решение зафиксировано</Typography.Title>
              <p>{application.bankComment ?? 'Заявка находится на следующем этапе процесса.'}</p>
              {application.offer && (
                <div className="decision-result-offer">
                  <span><small>Предложено</small><strong>{formatMoney(application.offer.amount)}</strong></span>
                  <span><small>Платёж</small><strong>{formatMoney(application.offer.monthlyPayment)}</strong></span>
                </div>
              )}
              <Button view="secondary" size={48} block onClick={() => navigate('/bank')}>Вернуться в очередь</Button>
            </section>
          )}

          <section className="surface-card mini-timeline">
            <div className="eyebrow">История</div>
            {([...application.events].reverse()).map((item, index) => (
              <div className="mini-timeline__item" key={item.id}>
                <span className={index === 0 ? 'mini-timeline__dot mini-timeline__dot--active' : 'mini-timeline__dot'} />
                <div>
                  <strong>{item.title}</strong>
                  <p>{item.description}</p>
                  <small>{formatDateTime(item.createdAt)} · {item.actor}</small>
                </div>
              </div>
            ))}
          </section>
        </aside>
      </div>
    </div>
  );
}
