import type { StressSummary } from '../types/credit';
import { formatMoney } from '../utils/format';

export function StressPanel({ stress, snapshot = false }: { stress?: StressSummary | null; snapshot?: boolean }) {
  if (!stress) return null;
  return <details className="explanation-box stress-panel"><summary>Что будет при снижении выручки</summary>
    {snapshot && <p>Исходный запрос на момент подачи. Предложение банка может иметь другие условия.</p>}
    <p>{formatMoney(stress.amount)} · {stress.termMonths} мес. · {stress.rate}% годовых</p>
    <p>{stress.maxRevenueDeclinePercent === null
      ? 'Исходное покрытие уже ниже требуемого порога.'
      : `Запас снижения выручки до исходного порога покрытия: около ${stress.maxRevenueDeclinePercent.toFixed(1)}%.`}</p>
    <p>Исходный порог покрытия: {stress.coverageThreshold.toFixed(2)}×</p>
    <dl className="stress-rows">{stress.scenarios.map(row => <div className="stress-row" key={row.revenueDeclinePercent}>
      <dt>{row.revenueDeclinePercent === 0 ? 'Без снижения' : `Выручка −${row.revenueDeclinePercent}%`}</dt>
      <dd><strong>{row.coverage.toFixed(2)}×</strong> · {row.coveragePasses ? 'исходный порог пройден' : 'ниже исходного порога'}
        <span>{row.policyPasses ? row.reviewRequired ? 'Требуется рассмотрение банка' : 'Условия проходят правила' : 'Условия не проходят правила'}</span>
      </dd>
    </div>)}</dl>
    <p>При ухудшении профиля требование к покрытию может вырасти до 1,5×. Прохождение исходного порога само по себе не означает доступность кредита.</p>
    {stress.assumptions.map(text => <p key={text}>{text}</p>)}
  </details>;
}
