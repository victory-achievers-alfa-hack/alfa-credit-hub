import type { ReactNode } from 'react';
import { Typography } from '@alfalab/core-components/typography';

interface PageHeaderProps {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}

export function PageHeader({ eyebrow, title, description, actions }: PageHeaderProps) {
  return (
    <div className="page-header">
      <div className="page-header__copy">
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <Typography.Title tag="h1" view="large" weight="bold" className="page-header__title">
          {title}
        </Typography.Title>
        {description && (
          <Typography.Text tag="p" view="primary-medium" color="secondary" className="page-header__description">
            {description}
          </Typography.Text>
        )}
      </div>
      {actions && <div className="page-header__actions">{actions}</div>}
    </div>
  );
}
