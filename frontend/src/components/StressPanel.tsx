import type { StressSummary } from '../types/credit';
import { formatMoney } from '../utils/format';

export function StressPanel({ stress, snapshot = false }: { stress?: StressSummary | null; snapshot?: boolean }) {
  if (!stress) return null;
  return <details className="explanation-box stress-panel"><summary>Что будет при снижении выручки</summary>
    {snapshot && <p>Исходный запрос на момент подачи. Предложение банка может иметь другие условия.</p>}
    <p>{formatMoney(stress.amount)} · {stress.termMonths} мес. · {stress.rate}% годовых</p>
    <p>{stress.headroomMessage ?? (stress.maxRevenueDeclinePercent === null
      ? 'Исходное покрытие уже ниже требуемого порога.'
      : stress.maxRevenueDeclinePercent === 0 ? 'Запас до исходного порога покрытия отсутствует.'
      : stress.maxRevenueDeclinePercent < 0.1 ? 'Запас снижения выручки менее 0,1% — практически отсутствует.'
      : `Запас снижения выручки до исходного порога покрытия: около ${stress.maxRevenueDeclinePercent.toFixed(1)}%.`)}</p>
    <p>{stress.coverageDefinition ?? 'Покрытие = (выручка − операционные расходы) / (существующие платежи + новый платёж).'}</p>
    <p>Исходный порог покрытия: {stress.coverageThreshold.toFixed(2)}×</p>
    <dl className="stress-rows">{stress.scenarios.map(row => <div className="stress-row" key={row.revenueDeclinePercent}>
      <dt>{row.revenueDeclinePercent === 0 ? 'Без снижения' : `Выручка −${row.revenueDeclinePercent}%`}</dt>
      <dd><strong>{row.coverage.toFixed(2)}×</strong> · {row.coveragePasses ? 'исходный порог пройден' : 'ниже исходного порога'}
        {(row.operatingDeficit ?? 0) > 0 && <span>{row.coverageExplanation}</span>}
        {row.operatingDeficit == null && row.coverage < 0 && <span>Операционные расходы превышают выручку ещё до платежей по кредитам.</span>}
        {row.monthlyCashFlow === 0 && <span>{row.coverageExplanation}</span>}
        <span>{row.policyPasses ? row.reviewRequired ? 'Требуется рассмотрение банка' : 'Условия проходят правила' : 'Условия не проходят правила'}</span>
      </dd>
    </div>)}</dl>
    <p>При ухудшении профиля требование к покрытию может вырасти до 1,5×. Прохождение исходного порога само по себе не означает доступность кредита.</p>
    {stress.assumptions.map(text => <p key={text}>{text}</p>)}
  </details>;
}
