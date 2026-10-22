import { STATUS_LABELS } from '../data/mockData';
import type { ApplicationStatus } from '../types/credit';

interface ApplicationStatusBadgeProps {
  status: ApplicationStatus;
  compact?: boolean;
}

const STATUS_ICONS: Record<ApplicationStatus, string> = {
  review: '•',
  need_info: '!',
  offer: '₽',
  sign: '✎',
  ready: '✓',
  disbursed: '✓',
  rejected: '×',
};

export function ApplicationStatusBadge({ status, compact = false }: ApplicationStatusBadgeProps) {
  return (
    <span className={`status-badge status-badge--${status}${compact ? ' status-badge--compact' : ''}`}>
      <span className="status-badge__icon" aria-hidden="true">{STATUS_ICONS[status]}</span>
      {STATUS_LABELS[status]}
    </span>
  );
}
