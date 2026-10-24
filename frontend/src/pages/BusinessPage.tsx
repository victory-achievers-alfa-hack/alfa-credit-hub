import { Typography } from '@alfalab/core-components/typography';
import { MetricCard } from '../components/MetricCard';
import { PageHeader } from '../components/PageHeader';
import { useAuth } from '../context/AutoContext';
import { useCredit } from '../context/CreditContext';
import { formatDate, formatMoney } from '../utils/format';

export function BusinessPage() {
  const { currentUser } = useAuth();
  const { getCompany } = useCredit();
  const company = getCompany(currentUser?.companyId);

  if (!company) return null;

  const operatingFlow = company.monthlyRevenue - company.monthlyExpenses;

  return (
    <div className="page-shell">
      <PageHeader
        eyebrow="Профиль действующего клиента"
        title="Мой бизнес"
        description="Данные уже есть в банке — повторно заполнять реквизиты и финансовую историю не нужно."
      />

      <div className="business-summary surface-card">
        <div className="business-summary__avatar">{company.name.slice(0, 1)}</div>
        <div className="business-summary__copy">
          <Typography.Title tag="h2" view="medium" weight="bold">{company.legalName}</Typography.Title>
          <p>{company.okved}</p>
          <div className="business-summary__tags">
            <span className="soft-tag soft-tag--positive">Компания действует</span>
            <span className={`soft-tag${company.hasOverdue ? ' soft-tag--negative' : ' soft-tag--positive'}`}>
              {company.hasOverdue ? 'Есть просрочки' : 'Без просрочек'}
            </span>
          </div>
        </div>
        <div className="business-summary__score">
          <small>Предварительный балл</small>
          <strong>{company.scoringScore}<span>/100</span></strong>
        </div>
      </div>

      <div className="metrics-grid metrics-grid--four">
        <MetricCard label="Выручка" value={formatMoney(company.monthlyRevenue)} description="В среднем за месяц" />
        <MetricCard label="Расходы" value={formatMoney(company.monthlyExpenses)} description="Без кредитных платежей" />
        <MetricCard label="Поток до долгов" value={formatMoney(operatingFlow)} description="Выручка минус расходы" tone="positive" />
        <MetricCard label="Действующие платежи" value={formatMoney(company.existingPayments)} description="В месяц" tone="warning" />
      </div>

      <div className="two-column-layout">
        <section className="surface-card detail-section">
          <div className="section-heading section-heading--compact">
            <div>
              <div className="eyebrow">Реквизиты</div>
              <Typography.Title tag="h2" view="small" weight="bold">Данные компании</Typography.Title>
            </div>
            <span className="source-label">Источник: профиль банка</span>
          </div>
          <dl className="detail-list">
            <div><dt>Краткое название</dt><dd>{company.name}</dd></div>
            <div><dt>ИНН</dt><dd>{company.inn}</dd></div>
            <div><dt>Дата регистрации</dt><dd>{formatDate(company.registrationDate)}</dd></div>
            <div><dt>Расчётный счёт</dt><dd>{company.account}</dd></div>
            <div><dt>Представитель</dt><dd>{company.representative}</dd></div>
            <div><dt>Основной ОКВЭД</dt><dd>{company.okved}</dd></div>
          </dl>
        </section>

        <section className="surface-card detail-section">
          <div className="section-heading section-heading--compact">
            <div>
              <div className="eyebrow">Синтетические данные</div>
              <Typography.Title tag="h2" view="small" weight="bold">Документы</Typography.Title>
            </div>
            <span className="source-label">{company.documents.length} файла</span>
          </div>
          <div className="document-list">
            {company.documents.map((document) => (
              <div className="document-row" key={document.id}>
                <span className={`document-row__icon${document.status === 'attention' ? ' document-row__icon--attention' : ''}`}>
                  {document.status === 'ready' ? '✓' : '!'}
                </span>
                <span className="document-row__copy">
                  <strong>{document.name}</strong>
                  <small>{document.description}</small>
                </span>
                <time>{document.updatedAt}</time>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
