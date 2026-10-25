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

export interface NextAction {
  code: string;
  title: string;
  message: string;
  amount?: number | null;
  termMonths?: number | null;
  documentKind?: string | null;
  minimumAmount?: number | null;
  maximumAmount?: number | null;
  allowedTerms?: number[] | null;
}

export interface RecommendationOffer {
  amount: number;
  termMonths: number;
  rate: number;
  monthlyPayment: number;
  lastPayment: number;
  totalRepayment: number;
  interestAmount: number;
  coverage: number;
  eligible: boolean;
  reviewRequired: boolean;
}

export interface RecommendationReason {
  code: string;
  message: string;
  field?: string | null;
  actual?: number | string | null;
  minimum?: number | null;
  maximum?: number | null;
  allowedValues?: Array<number | string> | null;
}

export interface FinancingConstraints {
  productMinAmount: number;
  productMaxAmount: number;
  allowedTerms: number[];
  allowedPurposes: CreditPurpose[];
  appliedAmountLimit: number;
  requiredCoverage: number;
  maxNewMonthlyPayment: number;
  monthlyCashFlow: number;
  totalMonthlyDebtPayment: number;
  requiredMonthlyRevenue: number;
  monthlyCoverageShortfall: number;
}

export interface RecommendationEvaluation extends RecommendationOffer {
  coveragePasses: boolean;
  constraints: FinancingConstraints;
  actions: NextAction[];
  policyPasses: boolean;
  requiredCoverage: number;
  amountLimit: number;
  productId: string;
  purpose: CreditPurpose;
  assessment: RecommendationAssessment;
  reasons: RecommendationReason[];
  checks: ApplicationCheck[];
  alternative: RecommendationOffer | null;
  recommendedAmount: number | null;
  scoring: ScoringResult;
  policyVersion: string;
  calculatedAt: string;
}

export interface Recommendation {
  product: CreditProduct;
  evaluation: RecommendationEvaluation;
  selectedEvaluation: RecommendationEvaluation;
  stress: StressSummary;
  highlights: string[];
  comparisonAmount: number | null;
  comparisonCount: number;
  offer: RecommendationOffer;
  termChanged: boolean;
  amountShortfall: number;
  group: RecommendationGroup;
  rankInGroup: number;
  rankingReason: string;
}

export type RequestSummaryStatus =
  | 'exact_available'
  | 'exact_review'
  | 'alternatives_available'
  | 'information_required'
  | 'unavailable';

export interface RecommendationRequestSummary {
  status: RequestSummaryStatus;
  message: string;
  exactMatchCount: number;
  exactReviewCount: number;
  otherTermCount: number;
  reducedAmountCount: number;
}

export interface RequestedProductCheck {
  productId: string;
  productName: string;
  assessment: string;
  policyPasses: boolean;
  reviewRequired: boolean;
  reasons: RecommendationReason[];
  constraints: FinancingConstraints;
}

export interface RecommendationResponse {
  requestSummary: RecommendationRequestSummary;
  requestChecks: RequestedProductCheck[];
  evaluationId: string;
  companyId: string;
  rankingVersion: string;
  preference: 'min_interest' | 'min_payment';
  requestedAmount: number;
  requestedTermMonths: number;
  calculatedAt: string;
  groups: Record<RecommendationGroup, Recommendation[]>;
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
  stress?: StressSummary | null;
  actions?: NextAction[];
  requiredCoverage?: number;
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


export interface StressSummary {
  baselineMonthlyRevenue?: number | null;
  monthlyExpenses?: number | null;
  existingMonthlyPayments?: number | null;
  newMonthlyPayment?: number | null;
  coverageDefinition?: string | null;
  headroomMessage?: string | null;
  headroomStatus?: 'below_threshold' | 'at_threshold' | 'negligible' | 'positive' | null;
  stressVersion: string;
  calculatedAt: string;
  policyVersion: string;
  amount: number;
  termMonths: number;
  rate: number;
  assumptions: string[];
  coverageThreshold: number;
  requiredMonthlyRevenue: number;
  revenueHeadroom: number;
  maxRevenueDeclinePercent: number | null;
  coverageStatus: 'passes' | 'below_threshold';
  thresholdExplanation: string;
  scenarios: Array<{
    coverageExplanation?: string | null;
    operatingDeficit?: number | null;
    monthlyCashFlow?: number | null;
    debtServiceShortfall?: number | null;
    revenueDeclinePercent: number;
    monthlyRevenue: number;
    coverage: number;
    coveragePasses: boolean;
    score: number;
    policyPasses: boolean;
    requiredCoverage: number;
    reviewRequired: boolean;
    assessment: string;
  }>;
}
