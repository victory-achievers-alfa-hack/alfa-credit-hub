export type UserRole = 'client' | 'bank';

export type CreditPurpose = 'goods' | 'equipment' | 'cash_gap';

export type ApplicationStatus =
  | 'review'
  | 'need_info'
  | 'offer'
  | 'sign'
  | 'ready'
  | 'disbursed'
  | 'rejected';

export type CheckState = 'success' | 'warning' | 'error';

export interface UserProfile {
  id: string;
  email: string;
  role: UserRole;
  name: string;
  companyId?: string | null;
  companyName?: string;
  inn?: string;
  avatarText: string;
}

export type NotificationTone = 'info' | 'warning' | 'positive' | 'negative';

export interface ClientNotification {
  id: string;
  companyId: string | null;
  applicationId: string | null;
  title: string;
  message: string;
  tone: NotificationTone;
  createdAt: string;
  read: boolean;
}

export interface CompanyDocument {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'ready' | 'attention' | 'verified' | 'rejected';
  updatedAt: string;
}

export interface CompanyProfile {
  id: string;
  name: string;
  legalName: string;
  inn: string;
  okved: string;
  registrationDate: string;
  account: string;
  representative: string;
  monthlyRevenue: number;
  monthlyExpenses: number;
  existingPayments: number;
  hasOverdue: boolean;
  active: boolean;
  scoringScore: number;
  documents: CompanyDocument[];
}

export interface CreditProduct {
  id: string;
  name: string;
  shortName: string;
  description: string;
  purposes: CreditPurpose[];
  minAmount: number;
  maxAmount: number;
  terms: number[];
  rate: number;
  accent: string;
}

export type RecommendationGroup =
  | 'requested'
  | 'other_terms'
  | 'reduced_amount'
  | 'requires_action'
  | 'unavailable';

export type RecommendationAssessment =
  | 'eligible'
  | 'alternative'
  | 'need_info'
  | 'manual_review'
  | 'blocked'
  | 'unavailable';

export interface Recommendation {
  evaluationId?: string;
  rankingVersion?: string;
  amount: number;
  termMonths: number;
  rate: number;
  interestAmount: number;
  group: RecommendationGroup;
  assessment?: RecommendationAssessment;
  rankingReason: string;
  product: CreditProduct;
  monthlyPayment: number;
  coverage: number;
  eligible: boolean;
  reason: string;
  warning?: string;
  recommendedAmount?: number;
}

export interface ApplicationCheck {
  id: string;
  label: string;
  value: string;
  description: string;
  state: CheckState;
}

export interface ScoringResult {
  score: number;
  riskLevel: 'low' | 'medium' | 'high';
  summary: string;
  modelVersion?: string;
  featureVersion?: string;
  calculatedAt?: string;
  eventProbability?: number | null;
  factors: Array<{
    label: string;
    value: string;
    positive: boolean;
    code?: string;
    points?: number;
    maxPoints?: number;
  }>;
}

export interface LoanOffer {
  id: string;
  amount: number;
  termMonths: number;
  rate: number;
  monthlyPayment: number;
  reason: string;
  createdAt: string;
}

export interface ApplicationEvent {
  id: string;
  status: ApplicationStatus;
  title: string;
  description: string;
  actor: string;
  createdAt: string;
}

export interface CreditApplication {
  id: string;
  companyId: string;
  productId: string;
  productName: string;
  purpose: CreditPurpose;
  requestedAmount: number;
  requestedTermMonths: number;
  requestedRate: number;
  requestedMonthlyPayment: number;
  coverage: number;
  status: ApplicationStatus;
  scoring: ScoringResult;
  checks: ApplicationCheck[];
  offer?: LoanOffer | null;
  bankComment?: string | null;
  infoRequest?: string | null;
  createdAt: string;
  updatedAt: string;
  events: ApplicationEvent[];
}

export interface RecommendationInput {
  preference?: 'min_interest' | 'min_payment';
  companyId: string;
  purpose: CreditPurpose;
  amount: number;
  termMonths: number;
}

export interface CreateApplicationInput extends RecommendationInput {
  productId: string;
}

export type BankDecisionKind = 'approve' | 'alternative' | 'need_info' | 'reject';

export interface BankDecisionInput {
  kind: BankDecisionKind;
  amount?: number;
  termMonths?: number;
  rate?: number;
  comment: string;
}
