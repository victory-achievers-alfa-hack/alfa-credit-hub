import { useState } from 'react';
import { Button } from '@alfalab/core-components/button';
import { Typography } from '@alfalab/core-components/typography';
import { useNavigate } from 'react-router-dom';
import { ApplicationStatusBadge } from '../components/ApplicationStatusBadge';
import { PageHeader } from '../components/PageHeader';
import { SegmentedControl } from '../components/SegmentedControl';
import { useAuth } from '../context/AutoContext';
import { useCredit } from '../context/CreditContext';
import { getCompany, PURPOSE_LABELS } from '../data/mockData';
import { formatDateTime, formatMoney } from '../utils/format';

type ListFilter = 'all' | 'active' | 'completed';

const listFilterOptions = [
  { value: 'all', label: 'Все' },
  { value: 'active', label: 'Активные' },
  { value: 'completed', label: 'Завершённые' },
] as const;

export function ClientApplicationsPage() {
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  const { applications } = useCredit();
  const [filter, setFilter] = useState<ListFilter>('all');
  const company = getCompany(currentUser?.companyId);

  if (!company) return null;

  const companyApplications = applications
    .filter((application) => application.companyId === company.id)
    .filter((application) => {
      if (filter === 'active') return !['disbursed', 'rejected'].includes(application.status);
      if (filter === 'completed') return ['disbursed', 'rejected'].includes(application.status);
      return true;
    })
    .sort((first, second) => new Date(second.updatedAt).getTime() - new Date(first.updatedAt).getTime());

  return (
    <div className="page-shell">
      <PageHeader
        eyebrow="Кредитный процесс"
        title="Мои заявки"
        description="Следите за решением банка, принимайте предложения и подписывайте договор."
        actions={<Button view="accent" size={48} onClick={() => navigate('/client/financing')}>Новая заявка</Button>}
      />

      <div className="list-toolbar">
        <SegmentedControl<ListFilter>
          value={filter}
          options={listFilterOptions}
          onChange={setFilter}
          ariaLabel="Фильтр заявок"
        />
        <span className="list-toolbar__count">{companyApplications.length} заявок</span>
      </div>

      {companyApplications.length === 0 ? (
        <div className="surface-card empty-state empty-state--large">
          <span className="empty-state__icon">＋</span>
          <Typography.Title tag="h2" view="small" weight="bold">Здесь пока ничего нет</Typography.Title>
          <p>Создайте заявку или измените выбранный фильтр.</p>
          <Button view="accent" size={48} onClick={() => navigate('/client/financing')}>Подобрать кредит</Button>
        </div>
      ) : (
        <div className="applications-cards">
          {companyApplications.map((application) => (
            <button
              type="button"
              className="application-card"
              key={application.id}
              onClick={() => navigate(`/client/applications/${application.id}`)}
            >
              <div className="application-card__head">
                <span>
                  <small>{application.id}</small>
                  <strong>{application.productName}</strong>
                </span>
                <ApplicationStatusBadge status={application.status} />
              </div>
              <div className="application-card__body">
                <div><small>Сумма</small><strong>{formatMoney(application.requestedAmount)}</strong></div>
                <div><small>Срок</small><strong>{application.requestedTermMonths} мес.</strong></div>
                <div><small>Цель</small><strong>{PURPOSE_LABELS[application.purpose]}</strong></div>
                <div><small>Обновлено</small><strong>{formatDateTime(application.updatedAt)}</strong></div>
              </div>
              <div className="application-card__footer">
                <span>{application.status === 'offer' ? 'Банк ждёт вашего решения' : 'Открыть подробности'}</span>
                <span>→</span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
