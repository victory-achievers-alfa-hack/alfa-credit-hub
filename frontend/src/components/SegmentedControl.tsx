type SegmentValue = string | number;

interface SegmentOption<T extends SegmentValue> {
  value: T;
  label: string;
}

interface SegmentedControlProps<T extends SegmentValue> {
  value: T;
  options: readonly SegmentOption<T>[];
  onChange: (value: T) => void;
  ariaLabel: string;
  className?: string;
}

export function SegmentedControl<T extends SegmentValue>({
  value,
  options,
  onChange,
  ariaLabel,
  className = '',
}: SegmentedControlProps<T>) {
  const activeIndex = Math.max(0, options.findIndex((option) => option.value === value));

  return (
    <div
      className={`segmented-control ${className}`.trim()}
      role="tablist"
      aria-label={ariaLabel}
      style={{ gridTemplateColumns: `repeat(${options.length}, minmax(0, 1fr))` }}
    >
      <span
        className="segmented-control__indicator"
        style={{
          width: `calc((100% - 8px) / ${options.length})`,
          transform: `translateX(${activeIndex * 100}%)`,
        }}
        aria-hidden="true"
      />
      {options.map((option) => (
        <button
          type="button"
          role="tab"
          aria-selected={option.value === value}
          className={`segmented-control__item${option.value === value ? ' segmented-control__item--active' : ''}`}
          key={option.value}
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
