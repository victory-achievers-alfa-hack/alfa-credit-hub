// Статусы заявки на конвейере
export type ApplicationStatus =
  | 'DRAFT'                 // Черновик
  | 'SUBMITTED'             // Отправлена в банк
  | 'ENRICHMENT'            // Обогащение данными (ФНС, БКИ)
  | 'SCORING'               // Оценка рисков (ML)
  | 'MANUAL_REVIEW'         // Ручной разбор сотрудником банка
  | 'ADDITIONAL_INFO_REQ'   // Банк запросил доп. документы
  | 'COUNTER_OFFER'         // Банк предложил альтернативные условия
  | 'APPROVED'              // Одобрено
  | 'REJECTED'              // Отказ
  | 'SIGNED_AND_ISSUED';    // Договор подписан, деньги выданы

// Кредитный продукт
export interface CreditProduct {
  id: string;
  name: string;             // Например: "Оборотный кредит"
  minAmount: number;
  maxAmount: number;
  minTermMonths: number;
  maxTermMonths: number;
  baseRate: number;         // Базовая ставка %
}

// Профиль компании (из мока ФНС/ЕГРЮЛ)
export interface CompanyProfile {
  inn: string;
  name: string;
  okved: string;            // Отрасль бизнеса
  registrationDate: string;
  annualRevenue: number;
  currentDebtLoad: number;
  hasOverdue: boolean;
}

// Фактор скоринга (для XAI)
export interface ScoringFactor {
  name: string;
  impact: number;
  type: 'positive' | 'negative' | 'neutral';
}

// Оффер банка (включая альтернативные условия)
export interface LoanOffer {
  id: string;
  title: string;
  approvedAmount: number;
  termMonths: number;
  interestRate: number;
  monthlyPayment: number;
  conditions?: string;
}

// Заявка на кредит
export interface CreditApplication {
  id: string;
  createdAt: string;
  status: ApplicationStatus;
  requestedProduct: string;
  requestedAmount: number;
  requestedTermMonths: number;
  purpose: string;
  company: CompanyProfile;
  scoring?: {
    score: number;
    riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
    probabilityOfDefault: number;
    factors: ScoringFactor[];
    aiSummary?: string;
  };
  offers?: LoanOffer[];
  bankComment?: string;
}
