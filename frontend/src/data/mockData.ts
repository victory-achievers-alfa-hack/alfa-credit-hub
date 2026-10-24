import type {
  ApplicationCheck,
  ApplicationEvent,
  ClientNotification,
  CompanyProfile,
  CreditApplication,
  CreditProduct,
  CreditPurpose,
  Recommendation,
  ScoringResult,
  UserProfile,
} from '../types/credit';

export const PURPOSE_LABELS: Record<CreditPurpose, string> = {
  goods: 'Закупка товаров',
  equipment: 'Покупка оборудования',
  cash_gap: 'Закрытие кассового разрыва',
};

export const STATUS_LABELS = {
  review: 'На рассмотрении',
  need_info: 'Нужны сведения',
  offer: 'Есть предложение',
  sign: 'Ожидает подписания',
  ready: 'Готово к выдаче',
  disbursed: 'Кредит выдан',
  rejected: 'Заявка отклонена',
} as const;

export const DEMO_USERS: UserProfile[] = [
  {
    id: 'client-city',
    email: 'client@demo.ru',
    password: '123456',
    role: 'client',
    name: 'Алексей Соколов',
    companyId: 'city',
    companyName: 'Магазин «Город»',
    inn: '7701234567',
    avatarText: 'АС',
  },
  {
    id: 'client-cafe',
    email: 'cafe@demo.ru',
    password: '123456',
    role: 'client',
    name: 'Марина Орлова',
    companyId: 'cafe',
    companyName: 'Кофейня «Зёрна»',
    inn: '7702345678',
    avatarText: 'МО',
  },
  {
    id: 'client-vector',
    email: 'vector@demo.ru',
    password: '123456',
    role: 'client',
    name: 'Дмитрий Векторов',
    companyId: 'vector',
    companyName: 'ООО «Вектор»',
    inn: '7703456789',
    avatarText: 'ДВ',
  },
  {
    id: 'bank-underwriter',
    email: 'bank@demo.ru',
    password: '123456',
    role: 'bank',
    name: 'Анна Белова',
    companyName: 'Кредитный департамент',
    avatarText: 'АБ',
  },
];

const commonDocuments = [
  {
    id: 'registry',
    name: 'Выписка ЕГРЮЛ / ЕГРИП',
    description: 'Сведения о регистрации и видах деятельности',
    status: 'ready' as const,
    updatedAt: '21 октября 2026',
  },
  {
    id: 'statement',
    name: 'Выписка по расчётному счёту',
    description: 'Операции за последние 12 месяцев',
    status: 'ready' as const,
    updatedAt: '21 октября 2026',
  },
  {
    id: 'reporting',
    name: 'Финансовая отчётность',
    description: 'Синтетический комплект для демонстрации',
    status: 'ready' as const,
    updatedAt: '20 октября 2026',
  },
  {
    id: 'bki',
    name: 'Сведения БКИ',
    description: 'Кредитная история компании',
    status: 'ready' as const,
    updatedAt: '21 октября 2026',
  },
];

export const COMPANIES: CompanyProfile[] = [
  {
    id: 'city',
    name: 'Магазин «Город»',
    legalName: 'ООО «Магазин Город»',
    inn: '7701234567',
    okved: '47.11 — Розничная торговля продуктами',
    registrationDate: '2019-03-18',
    account: '40702 •••• •••• 1842',
    representative: 'Соколов Алексей Игоревич',
    monthlyRevenue: 900_000,
    monthlyExpenses: 740_000,
    existingPayments: 120_000,
    hasOverdue: false,
    active: true,
    scoringScore: 75,
    documents: commonDocuments,
  },
  {
    id: 'cafe',
    name: 'Кофейня «Зёрна»',
    legalName: 'ООО «Зёрна»',
    inn: '7702345678',
    okved: '56.10 — Деятельность ресторанов и кафе',
    registrationDate: '2018-07-04',
    account: '40702 •••• •••• 5721',
    representative: 'Орлова Марина Сергеевна',
    monthlyRevenue: 1_200_000,
    monthlyExpenses: 850_000,
    existingPayments: 70_000,
    hasOverdue: false,
    active: true,
    scoringScore: 88,
    documents: commonDocuments,
  },
  {
    id: 'vector',
    name: 'ООО «Вектор»',
    legalName: 'ООО «Вектор»',
    inn: '7703456789',
    okved: '46.69 — Оптовая торговля оборудованием',
    registrationDate: '2025-05-12',
    account: '40702 •••• •••• 9015',
    representative: 'Векторов Дмитрий Олегович',
    monthlyRevenue: 500_000,
    monthlyExpenses: 490_000,
    existingPayments: 90_000,
    hasOverdue: true,
    active: true,
    scoringScore: 38,
    documents: commonDocuments.map((document) =>
      document.id === 'bki'
        ? { ...document, status: 'attention' as const, description: 'Зафиксированы просрочки в кредитной истории' }
        : document,
    ),
  },
];

export const CREDIT_PRODUCTS: CreditProduct[] = [
  {
    id: 'working-capital',
    name: 'Оборотный кредит',
    shortName: 'Оборотный',
    description: 'На закупку товаров и пополнение оборотных средств',
    purposes: ['goods', 'cash_gap'],
    minAmount: 100_000,
    maxAmount: 3_000_000,
    terms: [12, 24, 36],
    rate: 24,
    accent: 'red',
  },
  {
    id: 'investment',
    name: 'Инвестиционный кредит',
    shortName: 'Инвестиционный',
    description: 'На оборудование, модернизацию и развитие бизнеса',
    purposes: ['equipment'],
    minAmount: 300_000,
    maxAmount: 5_000_000,
    terms: [12, 24, 36, 48, 60],
    rate: 22,
    accent: 'purple',
  },
  {
    id: 'express',
    name: 'Экспресс-кредит',
    shortName: 'Экспресс',
    description: 'Быстрое решение для любой из бизнес-задач',
    purposes: ['goods', 'equipment', 'cash_gap'],
    minAmount: 50_000,
    maxAmount: 1_000_000,
    terms: [12, 24],
    rate: 29,
    accent: 'blue',
  },
];

export const MOCK_NEWS = [
  {
    id: 'support',
    tag: 'Господдержка',
    title: 'Новые меры поддержки малого бизнеса',
    description: 'Собрали программы субсидирования и льготного финансирования для предпринимателей.',
  },
  {
    id: 'retail',
    tag: 'Аналитика',
    title: 'Как ритейл готовится к высокому сезону',
    description: 'Практические рекомендации по управлению запасами и оборотным капиталом.',
  },
];

export function getCompany(companyId?: string): CompanyProfile | undefined {
  return COMPANIES.find((company) => company.id === companyId);
}

export function getProduct(productId: string): CreditProduct | undefined {
  return CREDIT_PRODUCTS.find((product) => product.id === productId);
}

export function calculateMonthlyPayment(amount: number, annualRate: number, termMonths: number): number {
  const monthlyRate = annualRate / 12 / 100;
  const payment = (amount * monthlyRate) / (1 - (1 + monthlyRate) ** -termMonths);
  return Math.round(payment);
}

export function calculateCoverage(company: CompanyProfile, monthlyPayment: number): number {
  const operatingFlow = company.monthlyRevenue - company.monthlyExpenses;
  const allPayments = company.existingPayments + monthlyPayment;
  return allPayments > 0 ? operatingFlow / allPayments : 0;
}

function calculateAffordableAmount(company: CompanyProfile, product: CreditProduct, termMonths: number): number {
  const operatingFlow = company.monthlyRevenue - company.monthlyExpenses;
  const affordablePayment = operatingFlow / 1.25 - company.existingPayments;
  if (affordablePayment <= 0) return 0;

  const monthlyRate = product.rate / 12 / 100;
  const amount = affordablePayment * (1 - (1 + monthlyRate) ** -termMonths) / monthlyRate;
  return Math.max(0, Math.floor(Math.min(amount, product.maxAmount) / 10_000) * 10_000);
}

export function buildChecks(company: CompanyProfile, coverage: number): ApplicationCheck[] {
  return [
    {
      id: 'registry',
      label: 'Реестр компаний',
      value: company.active ? 'Компания действует' : 'Есть ограничения',
      description: 'Статус и реквизиты сверены с синтетическим реестром',
      state: company.active ? 'success' : 'error',
    },
    {
      id: 'bki',
      label: 'Кредитная история',
      value: company.hasOverdue ? 'Есть просрочки' : 'Без просрочек',
      description: 'Результат локального симулятора БКИ',
      state: company.hasOverdue ? 'error' : 'success',
    },
    {
      id: 'documents',
      label: 'Комплект документов',
      value: company.documents.every((document) => document.status === 'ready') ? 'Полный комплект' : 'Нужно уточнение',
      description: 'Проверены синтетические документы компании',
      state: company.documents.every((document) => document.status === 'ready') ? 'success' : 'warning',
    },
    {
      id: 'coverage',
      label: 'Покрытие платежей',
      value: `${coverage.toFixed(2)}×`,
      description: 'Порог автоматического предварительного прохождения — 1,25×',
      state: coverage >= 1.25 ? 'success' : 'warning',
    },
  ];
}

export function buildScoring(company: CompanyProfile): ScoringResult {
  const riskLevel = company.scoringScore >= 70 ? 'low' : company.scoringScore >= 50 ? 'medium' : 'high';
  const operatingFlow = company.monthlyRevenue - company.monthlyExpenses;

  return {
    score: company.scoringScore,
    riskLevel,
    summary:
      riskLevel === 'low'
        ? 'Профиль устойчивый. Итог зависит от покрытия платежей по выбранной сумме.'
        : riskLevel === 'medium'
          ? 'Есть факторы риска — требуется решение сотрудника банка.'
          : 'Высокая нагрузка или просрочки требуют отказа либо ручного рассмотрения.',
    factors: [
      {
        label: 'История платежей',
        value: company.hasOverdue ? 'Есть просрочки' : 'Без просрочек',
        positive: !company.hasOverdue,
      },
      {
        label: 'Операционный поток',
        value: `${operatingFlow.toLocaleString('ru-RU')} ₽/мес.`,
        positive: operatingFlow > company.existingPayments,
      },
      {
        label: 'Возраст бизнеса',
        value: new Date(company.registrationDate).getFullYear() <= 2023 ? 'Более 3 лет' : 'Менее 3 лет',
        positive: new Date(company.registrationDate).getFullYear() <= 2023,
      },
    ],
  };
}

export function getRecommendations(
  company: CompanyProfile,
  purpose: CreditPurpose,
  amount: number,
  termMonths: number,
): Recommendation[] {
  return CREDIT_PRODUCTS.filter(
    (product) =>
      product.purposes.includes(purpose) &&
      product.terms.includes(termMonths) &&
      amount >= product.minAmount &&
      amount <= product.maxAmount,
  )
    .map((product) => {
      const monthlyPayment = calculateMonthlyPayment(amount, product.rate, termMonths);
      const coverage = calculateCoverage(company, monthlyPayment);
      const eligible = !company.hasOverdue && company.scoringScore >= 70 && coverage >= 1.25;
      const recommendedAmount = eligible ? undefined : calculateAffordableAmount(company, product, termMonths);

      return {
        product,
        monthlyPayment,
        coverage,
        eligible,
        reason: eligible
          ? 'Подходит по цели, сумме и сроку. Финансовая нагрузка укладывается в правила.'
          : 'Подходит по параметрам каталога, но требует решения сотрудника банка.',
        warning: company.hasOverdue
          ? 'В кредитной истории есть просрочки.'
          : coverage < 1.25
            ? 'Расчётная нагрузка выше автоматического порога.'
            : undefined,
        recommendedAmount:
          recommendedAmount && recommendedAmount >= product.minAmount ? recommendedAmount : undefined,
      };
    })
    .sort((first, second) => Number(second.eligible) - Number(first.eligible) || first.product.rate - second.product.rate);
}

function event(
  id: string,
  status: CreditApplication['status'],
  title: string,
  description: string,
  actor: string,
  createdAt: string,
): ApplicationEvent {
  return { id, status, title, description, actor, createdAt };
}

export function createSeedNotifications(): ClientNotification[] {
  return [
    {
      id: 'NOTIFICATION-2026-001',
      companyId: 'city',
      applicationId: 'APP-2026-001',
      title: 'Банк предложил новые условия',
      message: 'По заявке APP-2026-001 доступно предложение на 150 000 ₽.',
      tone: 'warning',
      createdAt: '2026-10-22T10:25:00.000Z',
      read: false,
    },
  ];
}

export function createSeedApplications(): CreditApplication[] {
  const city = COMPANIES[0];
  const cafe = COMPANIES[1];
  const vector = COMPANIES[2];
  const workingCapital = CREDIT_PRODUCTS[0];
  const investment = CREDIT_PRODUCTS[1];
  const express = CREDIT_PRODUCTS[2];

  const cityPayment = calculateMonthlyPayment(800_000, workingCapital.rate, 24);
  const cityCoverage = calculateCoverage(city, cityPayment);
  const cafePayment = calculateMonthlyPayment(1_000_000, investment.rate, 36);
  const cafeCoverage = calculateCoverage(cafe, cafePayment);
  const vectorPayment = calculateMonthlyPayment(500_000, express.rate, 12);
  const vectorCoverage = calculateCoverage(vector, vectorPayment);

  return [
    {
      id: 'APP-2026-001',
      companyId: city.id,
      productId: workingCapital.id,
      productName: workingCapital.name,
      purpose: 'goods',
      requestedAmount: 800_000,
      requestedTermMonths: 24,
      requestedRate: workingCapital.rate,
      requestedMonthlyPayment: cityPayment,
      coverage: cityCoverage,
      status: 'offer',
      scoring: buildScoring(city),
      checks: buildChecks(city, cityCoverage),
      offer: {
        id: 'OFF-2026-001',
        amount: 150_000,
        termMonths: 24,
        rate: 24,
        monthlyPayment: calculateMonthlyPayment(150_000, 24, 24),
        reason: 'Сумма снижена, чтобы коэффициент покрытия достиг безопасного уровня 1,25×.',
        createdAt: '2026-10-22T10:25:00.000Z',
      },
      bankComment: 'Предлагаем начать с меньшей суммы и сохранить комфортную долговую нагрузку.',
      createdAt: '2026-10-21T09:15:00.000Z',
      updatedAt: '2026-10-22T10:25:00.000Z',
      events: [
        event('EV-001', 'review', 'Заявка отправлена', 'Данные переданы на рассмотрение в банк.', city.name, '2026-10-21T09:15:00.000Z'),
        event('EV-002', 'offer', 'Банк предложил другие условия', 'Доступно предложение на 150 000 ₽.', 'Анна Белова', '2026-10-22T10:25:00.000Z'),
      ],
    },
    {
      id: 'APP-2026-002',
      companyId: cafe.id,
      productId: investment.id,
      productName: investment.name,
      purpose: 'equipment',
      requestedAmount: 1_000_000,
      requestedTermMonths: 36,
      requestedRate: investment.rate,
      requestedMonthlyPayment: cafePayment,
      coverage: cafeCoverage,
      status: 'review',
      scoring: buildScoring(cafe),
      checks: buildChecks(cafe, cafeCoverage),
      createdAt: '2026-10-22T08:40:00.000Z',
      updatedAt: '2026-10-22T08:40:00.000Z',
      events: [
        event('EV-003', 'review', 'Заявка отправлена', 'Проверки выполнены, заявка ожидает решения.', cafe.name, '2026-10-22T08:40:00.000Z'),
      ],
    },
    {
      id: 'APP-2026-003',
      companyId: vector.id,
      productId: express.id,
      productName: express.name,
      purpose: 'cash_gap',
      requestedAmount: 500_000,
      requestedTermMonths: 12,
      requestedRate: express.rate,
      requestedMonthlyPayment: vectorPayment,
      coverage: vectorCoverage,
      status: 'review',
      scoring: buildScoring(vector),
      checks: buildChecks(vector, vectorCoverage),
      createdAt: '2026-10-22T11:05:00.000Z',
      updatedAt: '2026-10-22T11:05:00.000Z',
      events: [
        event('EV-004', 'review', 'Заявка отправлена', 'Обнаружены факторы, требующие ручного решения.', vector.name, '2026-10-22T11:05:00.000Z'),
      ],
    },
  ];
}
