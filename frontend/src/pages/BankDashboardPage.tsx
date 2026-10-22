import { useMemo, useState } from 'react';
import { Button } from '@alfalab/core-components/button';
import { Input } from '@alfalab/core-components/input';
import { Typography } from '@alfalab/core-components/typography';
import { useNavigate } from 'react-router-dom';
import { ApplicationStatusBadge } from '../components/ApplicationStatusBadge';
import { MetricCard } from '../components/MetricCard';
import { PageHeader } from '../components/PageHeader';
import { SegmentedControl } from '../components/SegmentedControl';
import { useCredit } from '../context/CreditContext';
import { getCompany, PURPOSE_LABELS } from '../data/mockData';
import type { ApplicationStatus } from '../types/credit';
import { formatDateTime, formatMoney } from '../utils/format';

type BankFilter = 'all' | ApplicationStatus;

const bankFilterOptions = [
  { value: 'all', label: 'Все' },
  { value: 'review', label: 'Новые' },
  { value: 'need_info', label: 'Сведения' },
  { value: 'offer', label: 'Предложения' },
  { value: 'ready', label: 'К выдаче' },
  { value: 'rejected', label: 'Отказы' },
] as const;

export function BankDashboardPage() {
  const navigate = useNavigate();
  const { applications, resetDemo } = useCredit();
  const [filter, setFilter] = useState<BankFilter>('all');
  const [query, setQuery] = useState('');

  const filteredApplications = useMemo(() => applications
    .filter((application) => filter === 'all' || application.status === filter)
    .filter((application) => {
      const company = getCompany(application.companyId);
      const haystack = `${application.id} ${company?.name ?? ''} ${company?.inn ?? ''}`.toLowerCase();
      return haystack.includes(query.trim().toLowerCase());
    })
    .sort((first, second) => new Date(second.updatedAt).getTime() - new Date(first.updatedAt).getTime()), [applications, filter, query]);

  const reviewCount = applications.filter((application) => application.status === 'review').length;
  const actionCount = applications.filter((application) => ['need_info', 'offer', 'sign', 'ready'].includes(application.status)).length;
  const completedCount = applications.filter((application) => ['disbursed', 'rejected'].includes(application.status)).length;
  const requestedTotal = applications.reduce((sum, application) => sum + application.requestedAmount, 0);

  return (
    <div className="page-shell page-shell--bank">
      <PageHeader
        eyebrow="Рабочее место андеррайтера"
        title="Очередь заявок"
        description="Проверяйте расчёты, фиксируйте решение и управляйте кредитным процессом."
        actions={<Button view="secondary" size={48} onClick={resetDemo}>Сбросить демо</Button>}
      />

      <div className="metrics-grid metrics-grid--four">
        <MetricCard label="Новые на рассмотрении" value={String(reviewCount)} description="Требуют решения банка" tone={reviewCount ? 'accent' : 'default'} />
        <MetricCard label="Ожидают действия" value={String(actionCount)} description="Клиент или сотрудник" tone="warning" />
        <MetricCard label="Завершено" value={String(completedCount)} description="Выдано или отклонено" tone="positive" />
        <MetricCard label="Запрошено всего" value={formatMoney(requestedTotal)} description="По текущей очереди" />
      </div>

      <section className="surface-card bank-queue">
        <div className="bank-queue__toolbar">
          <SegmentedControl<BankFilter>
            value={filter}
            options={bankFilterOptions}
            onChange={setFilter}
            ariaLabel="Фильтр банковской очереди"
            className="segmented-control--bank"
          />
          <Input
            className="bank-search"
            size={48}
            clear="auto"
            placeholder="Компания, ИНН или номер"
            value={query}
            onChange={(_, payload) => setQuery(payload.value)}
            onClear={() => setQuery('')}
          />
        </div>

        <div className="bank-table-wrap">
          <table className="bank-table">
            <thead>
              <tr>
                <th>Заявка</th>
                <th>Компания</th>
                <th>Запрос</th>
                <th>Скоринг</th>
                <th>Статус</th>
                <th>Обновлено</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {filteredApplications.map((application) => {
                const company = getCompany(application.companyId);
                return (
                  <tr key={application.id} onClick={() => navigate(`/bank/applications/${application.id}`)}>
                    <td><strong>{application.id}</strong><small>{application.productName}</small></td>
                    <td><strong>{company?.name}</strong><small>ИНН {company?.inn}</small></td>
                    <td><strong>{formatMoney(application.requestedAmount)}</strong><small>{PURPOSE_LABELS[application.purpose]} · {application.requestedTermMonths} мес.</small></td>
                    <td>
                      <span className={`risk-score risk-score--${application.scoring.riskLevel}`}>{application.scoring.score}</span>
                      <small>{application.scoring.riskLevel === 'low' ? 'Низкий риск' : application.scoring.riskLevel === 'medium' ? 'Средний риск' : 'Высокий риск'}</small>
                    </td>
                    <td><ApplicationStatusBadge status={application.status} compact /></td>
                    <td><span>{formatDateTime(application.updatedAt)}</span></td>
                    <td><span className="table-arrow">→</span></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {filteredApplications.length === 0 && (
          <div className="empty-state">
            <span className="empty-state__icon">⌕</span>
            <Typography.Title tag="h3" view="xsmall" weight="bold">Ничего не найдено</Typography.Title>
            <p>Измените фильтр или поисковый запрос.</p>
          </div>
        )}
      </section>
    </div>
  );
}
