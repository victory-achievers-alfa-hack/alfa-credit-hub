import type { NextAction } from '../types/credit';
export function NextActions({ actions = [] }: { actions?: NextAction[] }) {
  if (!actions.length) return null;
  return (
    <div className="next-actions">
      <strong>Что нужно сделать</strong>
      <ul>
        {actions.map((action, index) => (
          <li key={`${action.code}-${action.documentKind ?? index}`}>
            <strong>{action.title}</strong>
            <p>{action.message}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
