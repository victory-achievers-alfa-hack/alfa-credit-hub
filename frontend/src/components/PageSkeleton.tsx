import { Skeleton } from '@alfalab/core-components/skeleton';

interface PageSkeletonProps {
  label?: string;
}

export function PageSkeleton({ label = 'Загружаем данные…' }: PageSkeletonProps) {
  return (
    <>
      <span className="visually-hidden" role="status" aria-live="polite">{label}</span>
      <div className="page-shell page-skeleton" aria-busy="true">
        <div className="page-skeleton__header" aria-hidden="true">
          <Skeleton visible className="page-skeleton__eyebrow">&nbsp;</Skeleton>
          <Skeleton visible className="page-skeleton__title">&nbsp;</Skeleton>
          <Skeleton visible className="page-skeleton__description">&nbsp;</Skeleton>
        </div>
        <div className="page-skeleton__metrics" aria-hidden="true">
          {[0, 1, 2, 3].map((item) => (
            <Skeleton visible className="page-skeleton__metric" borderRadius={20} key={item}>
              &nbsp;
            </Skeleton>
          ))}
        </div>
        <div aria-hidden="true">
          <Skeleton visible className="page-skeleton__content" borderRadius={24}>
            &nbsp;
          </Skeleton>
        </div>
      </div>
    </>
  );
}
