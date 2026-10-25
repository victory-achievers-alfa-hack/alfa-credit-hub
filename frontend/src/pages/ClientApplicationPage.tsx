import { StressPanel } from '../components/StressPanel';
import { NextActions } from '../components/NextActions';
import { useState } from 'react';
import { Button } from '@alfalab/core-components/button';
import { Checkbox } from '@alfalab/core-components/checkbox';
import { Typography } from '@alfalab/core-components/typography';
import { useNavigate, useParams } from 'react-router-dom';
import { ApplicationStatusBadge } from '../components/ApplicationStatusBadge';
import { useAuth } from '../context/AutoContext';
import { useCredit } from '../context/CreditContext';
import { PURPOSE_LABELS } from '../data/mockData';
import type { ApplicationStatus } from '../types/credit';
import { formatDateTime, formatMoney, formatPercent } from '../utils/format';

const progressStatuses: ApplicationStatus[] = ['review', 'offer', 'sign', 'ready', 'disbursed'];

export function ClientApplicationPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  const { getCompany, applications, respondToInfoRequest, acceptOffer, signApplication, disburseApplication } = useCredit();
  const [signConfirmed, setSignConfirmed] = useState(false);
  const application = applications.find((candidate) => candidate.id === id && candidate.companyId === currentUser?.companyId);
  const company = getCompany(application?.companyId);

  if (!application || !company) {
    return (
      <div className="page-shell">
        <div className="surface-card empty-state empty-state--large">
          <span className="empty-state__icon">?</span>
          <strong>Заявка не найдена</strong>
          <p>Возможно, она относится к другому профилю или была удалена.</p>
          <Button view="accent" size={48} onClick={() => navigate('/client/applications')}>К моим заявкам</Button>
        </div>
      </div>
    );
  }

  const currentProgressIndex = progressStatuses.indexOf(application.status);

  return (
    <div className="page-shell page-shell--narrow">
      <button type="button" className="back-link" onClick={() => navigate('/client/applications')}>← Все заявки</button>

      <section className={`application-status-hero application-status-hero--${application.status}`}>
        <div>
          <div className="eyebrow">Заявка {application.id}</div>
          <Typography.Title tag="h1" view="large" weight="bold">{application.productName}</Typography.Title>
          <p>{PURPOSE_LABELS[application.purpose]} · обновлено {formatDateTime(application.updatedAt)}</p>
        </div>
        <ApplicationStatusBadge status={application.status} />
      </section>

      {!['rejected', 'need_info'].includes(application.status) && (
        <div className="progress-track surface-card">
          {progressStatuses.map((status, index) => (
            <div className={`progress-track__item${index <= currentProgressIndex ? ' progress-track__item--done' : ''}`} key={status}>
              <span>{index < currentProgressIndex ? '✓' : index + 1}</span>
              <small>{status === 'review' ? 'Рассмотрение' : status === 'offer' ? 'Предложение' : status === 'sign' ? 'Подписание' : status === 'ready' ? 'Готово' : 'Выдача'}</small>
            </div>
          ))}
        </div>
      )}

      {application.status === 'need_info' && (
        <section className="action-panel action-panel--warning">
          <div>
            <div className="eyebrow">Нужно ваше действие</div>
            <Typography.Title tag="h2" view="small" weight="bold">Банк запросил сведения</Typography.Title>
            <p>{application.infoRequest}</p>
          </div>
          <Button view="accent" size={48} onClick={() => respondToInfoRequest(application.id)}>Подтвердить сведения</Button>
        </section>
      )}

      {application.status === 'offer' && application.offer && (
        <section className="offer-hero">
          <div className="offer-hero__copy">
            <div className="eyebrow eyebrow--light">Персональное предложение</div>
            <Typography.Title tag="h2" view="large" weight="bold">Банк готов предоставить кредит</Typography.Title>
            <p>{application.offer.reason}</p>
          </div>
          <div className="offer-hero__numbers">
            <div><small>Сумма</small><strong>{formatMoney(application.offer.amount)}</strong></div>
            <div><small>Срок</small><strong>{application.offer.termMonths} мес.</strong></div>
            <div><small>Ставка</small><strong>{formatPercent(application.offer.rate)}</strong></div>
            <div><small>Платёж</small><strong>{formatMoney(application.offer.monthlyPayment)}</strong></div>
          </div>
          <div className="offer-hero__actions">
            <Button view="accent" size={56} onClick={() => acceptOffer(application.id, true)}>Принять предложение</Button>
            <Button view="transparent" colors="inverted" size={56} onClick={() => acceptOffer(application.id, false)}>Отказаться</Button>
          </div>
        </section>
      )}

      {application.status === 'sign' && application.offer && (
        <section className="action-panel">
          <div className="action-panel__icon">✎</div>
          <div className="action-panel__content">
            <div className="eyebrow">Демоподписание</div>
            <Typography.Title tag="h2" view="small" weight="bold">Подпишите кредитный договор</Typography.Title>
            <p>В демонстрационном контуре электронная подпись заменена подтверждением. Реальный договор не создаётся.</p>
            <Checkbox
              checked={signConfirmed}
              onChange={(_, payload) => setSignConfirmed(payload.checked)}
              label={`Подтверждаю условия: ${formatMoney(application.offer.amount)} на ${application.offer.termMonths} месяцев`}
              size={24}
            />
          </div>
          <Button view="accent" size={48} disabled={!signConfirmed} onClick={() => signApplication(application.id)}>Подписать</Button>
        </section>
      )}

      {application.status === 'ready' && (
        <section className="action-panel action-panel--positive">
          <div className="action-panel__icon">✓</div>
          <div className="action-panel__content">
            <div className="eyebrow">Договор подписан</div>
            <Typography.Title tag="h2" view="small" weight="bold">Всё готово к выдаче</Typography.Title>
            <p>Подтвердите моделируемую выдачу, чтобы завершить сквозной сценарий.</p>
          </div>
          <Button view="accent" size={48} onClick={() => disburseApplication(application.id)}>Подтвердить выдачу</Button>
        </section>
      )}

      {application.status === 'disbursed' && (
        <section className="success-panel">
          <span>✓</span>
          <div>
            <div className="eyebrow">Сценарий завершён</div>
            <Typography.Title tag="h2" view="medium" weight="bold">Кредит выдан</Typography.Title>
            <p>Моделируемая выдача завершена. Все события сохранены в истории заявки.</p>
          </div>
        </section>
      )}

      {application.status === 'rejected' && (
        <section className="action-panel action-panel--negative">
          <div className="action-panel__icon">×</div>
          <div className="action-panel__content">
            <div className="eyebrow">Заявка завершена</div>
            <Typography.Title tag="h2" view="small" weight="bold">Предложение отклонено</Typography.Title>
            <p>{application.bankComment ?? 'По заявке принято отрицательное решение.'}</p>
          </div>
          <Button view="secondary" size={48} onClick={() => navigate('/client/financing')}>Новый расчёт</Button>
        </section>
      )}

      <div className="application-detail-grid">
        <section className="surface-card detail-section">
          <div className="section-heading section-heading--compact">
            <div>
              <div className="eyebrow">Параметры</div>
              <Typography.Title tag="h2" view="small" weight="bold">Запрос клиента</Typography.Title>
            </div>
          </div>
          <dl className="detail-list">
            <div><dt>Компания</dt><dd>{company.name}</dd></div>
            <div><dt>Цель</dt><dd>{PURPOSE_LABELS[application.purpose]}</dd></div>
            <div><dt>Сумма</dt><dd>{formatMoney(application.requestedAmount)}</dd></div>
            <div><dt>Срок</dt><dd>{application.requestedTermMonths} мес.</dd></div>
            <div><dt>Ориентировочная ставка</dt><dd>{formatPercent(application.requestedRate)}</dd></div>
            <div><dt>Расчётный платёж</dt><dd>{formatMoney(application.requestedMonthlyPayment)}</dd></div>
          </dl>
        </section>

        <section className="surface-card detail-section">
          <div className="section-heading section-heading--compact">
            <div>
              <div className="eyebrow">Автоматические проверки</div>
              <Typography.Title tag="h2" view="small" weight="bold">Финансовая оценка</Typography.Title>
            </div>
            <span className="score-chip">{application.scoring.score}/100</span>
          </div>
          <NextActions actions={application.actions} />
                <StressPanel stress={application.stress} snapshot />
          <div className="check-list">
            {application.checks.map((check) => (
              <div className="check-row" key={check.id}>
                <span className={`check-row__icon check-row__icon--${check.state}`}>{check.state === 'success' ? '✓' : check.state === 'warning' ? '!' : '×'}</span>
                <span><strong>{check.label}</strong><small>{check.description}</small></span>
                <b>{check.value}</b>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="surface-card detail-section">
        <div className="section-heading section-heading--compact">
          <div>
            <div className="eyebrow">Аудит процесса</div>
            <Typography.Title tag="h2" view="small" weight="bold">История заявки</Typography.Title>
          </div>
        </div>
        <div className="timeline">
          {[...application.events].reverse().map((item, index) => (
            <div className="timeline__item" key={item.id}>
              <span className={`timeline__dot${index === 0 ? ' timeline__dot--active' : ''}`} />
              <div>
                <strong>{item.title}</strong>
                <p>{item.description}</p>
                <small>{item.actor} · {formatDateTime(item.createdAt)}</small>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
