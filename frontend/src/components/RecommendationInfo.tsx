import { useEffect, useId, useRef, useState } from 'react';
import { Popover } from '@alfalab/core-components/popover';

type RecommendationInfoProps = {
  productName: string;
  changes: string[];
  reasons: string[];
  notice: string;
};

export function RecommendationInfo({ productName, changes, reasons, notice }: RecommendationInfoProps) {
  const [open, setOpen] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);
  const contentId = useId();

  useEffect(() => {
    if (!open) return;
    const isInside = (target: EventTarget | null) => target instanceof Node
      && (buttonRef.current?.contains(target) || popoverRef.current?.contains(target));
    const closeOutside = (event: Event) => {
      if (!isInside(event.target)) setOpen(false);
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setOpen(false);
        buttonRef.current?.focus();
      }
    };
    document.addEventListener('pointerdown', closeOutside);
    document.addEventListener('focusin', closeOutside);
    document.addEventListener('keydown', closeOnEscape);
    return () => {
      document.removeEventListener('pointerdown', closeOutside);
      document.removeEventListener('focusin', closeOutside);
      document.removeEventListener('keydown', closeOnEscape);
    };
  }, [open]);

  return (
    <>
      <button
        type="button"
        className="recommendation-info-button"
        aria-label={`Изменения условий: ${productName}`}
        aria-expanded={open}
        aria-controls={open ? contentId : undefined}
        aria-describedby={open ? contentId : undefined}
        ref={buttonRef}
        onClick={() => setOpen((value) => !value)}
      >
        <span aria-hidden="true">ⓘ</span>
      </button>
      <Popover
        open={open}
        anchorElement={buttonRef.current}
        position="bottom-end"
        offset={[0, 8]}
        withTransition={false}
        ref={popoverRef}
      >
        <div className="recommendation-info" id={contentId} role="note" aria-label="Отличия и причины">
          {changes.map((change) => <p key={change}><strong>{change}</strong></p>)}
          {reasons.length > 0 && <ul>{reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul>}
          <p className="recommendation-info__notice">{notice}</p>
        </div>
      </Popover>
    </>
  );
}
