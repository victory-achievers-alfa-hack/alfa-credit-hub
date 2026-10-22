import type { ReactNode } from 'react';

interface MetricCardProps {
  label: string;
  value: string;
  description?: string;
  icon?: ReactNode;
  tone?: 'default' | 'accent' | 'positive' | 'warning';
}

export function MetricCard({ label, value, description, icon, tone = 'default' }: MetricCardProps) {
  return (
    <article className={`metric-card metric-card--${tone}`}>
      <div className="metric-card__top">
        <span className="metric-card__label">{label}</span>
        {icon && <span className="metric-card__icon" aria-hidden="true">{icon}</span>}
      </div>
      <strong className="metric-card__value">{value}</strong>
      {description && <span className="metric-card__description">{description}</span>}
    </article>
  );
}
