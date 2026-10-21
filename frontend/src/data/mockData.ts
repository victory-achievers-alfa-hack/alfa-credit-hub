import type { CreditApplication, CreditProduct } from '../types/credit';

export const MOCK_PRODUCTS: CreditProduct[] = [
  {
    id: 'revolving',
    name: 'Оборотный кредит',
    minAmount: 500000,
    maxAmount: 15000000,
    minTermMonths: 3,
    maxTermMonths: 24,
    baseRate: 14.5,
  },
  {
    id: 'investment',
    name: 'Инвестиционный (на оборудование)',
    minAmount: 1000000,
    maxAmount: 50000000,
    minTermMonths: 12,
    maxTermMonths: 60,
    baseRate: 13.0,
  },
  {
    id: 'overdraft',
    name: 'Экспресс-Овердрафт',
    minAmount: 100000,
    maxAmount: 3000000,
    minTermMonths: 1,
    maxTermMonths: 12,
    baseRate: 16.0,
  },
];

export const INITIAL_APPLICATIONS: CreditApplication[] = [
  {
    id: 'APP-101',
    createdAt: '2026-10-20 14:30',
    status: 'APPROVED',
    requestedProduct: 'Оборотный кредит',
    requestedAmount: 3000000,
    requestedTermMonths: 12,
    purpose: 'Закупка сезонного сырья и комплектующих',
    company: {
      inn: '7701234567',
      name: 'ООО «ЛогистикПро»',
      okved: '49.41 Деятельность грузового автотранспорта',
      registrationDate: '2021-04-12',
      annualRevenue: 45000000,
      currentDebtLoad: 2000000,
      hasOverdue: false,
    },
    scoring: {
      score: 840,
      riskLevel: 'LOW',
      probabilityOfDefault: 2.1,
      factors: [
        { name: 'Возраст бизнеса > 3 лет', impact: 40, type: 'positive' },
        { name: 'Отсутствие просрочек в БКИ', impact: 60, type: 'positive' },
        { name: 'Высокая ликвидность активов', impact: 30, type: 'positive' }
      ]
    },
    offers: [
      {
        id: 'OFF-1',
        title: 'Одобрено на запрошенных условиях',
        approvedAmount: 3000000,
        termMonths: 12,
        interestRate: 14.5,
        monthlyPayment: 270100,
      }
    ]
  },
  {
    id: 'APP-102',
    createdAt: '2026-10-21 09:15',
    status: 'COUNTER_OFFER',
    requestedProduct: 'Инвестиционный (на оборудование)',
    requestedAmount: 10000000,
    requestedTermMonths: 36,
    purpose: 'Приобретение ЧПУ станков',
    company: {
      inn: '7812987654',
      name: 'ООО «БалтТехПром»',
      okved: '25.62 Обработка металлических изделий',
      registrationDate: '2023-01-15',
      annualRevenue: 28000000,
      currentDebtLoad: 8000000,
      hasOverdue: false,
    },
    scoring: {
      score: 610,
      riskLevel: 'MEDIUM',
      probabilityOfDefault: 6.8,
      factors: [
        { name: 'Высокая долговая нагрузка', impact: -50, type: 'negative' },
        { name: 'Рост выручки год к году +18%', impact: 35, type: 'positive' }
      ]
    },
    offers: [
      {
        id: 'OFF-2',
        title: 'Снижен лимит ввиду долговой нагрузки',
        approvedAmount: 6500000,
        termMonths: 36,
        interestRate: 15.5,
        monthlyPayment: 226900,
        conditions: 'Поручительство генерального директора'
      }
    ]
  },
  {
    id: 'APP-103',
    createdAt: '2026-10-21 11:00',
    status: 'MANUAL_REVIEW',
    requestedProduct: 'Экспресс-Овердрафт',
    requestedAmount: 1500000,
    requestedTermMonths: 6,
    purpose: 'Закрытие кассового разрыва перед расчетом с поставщиком',
    company: {
      inn: '5024112233',
      name: 'ИП Смирнов А.В.',
      okved: '56.10 Деятельность ресторанов и услуг по доставке продуктов питания',
      registrationDate: '2024-05-10',
      annualRevenue: 12000000,
      currentDebtLoad: 500000,
      hasOverdue: false,
    },
    scoring: {
      score: 540,
      riskLevel: 'MEDIUM',
      probabilityOfDefault: 9.5,
      factors: [
        { name: 'Срок регистрации менее 2 лет', impact: -30, type: 'negative' },
        { name: 'Отрасль с повышенной волатильностью', impact: -20, type: 'negative' }
      ],
      aiSummary: 'Бизнес молодой, но среднемесячные обороты стабильны. Требуется ручная сверка выписки с расчетного счета.'
    }
  }
];

export const MOCK_NEWS = [
  {
    id: 1,
    tag: 'Господдержка',
    title: 'Субсидии на покупку отечественного оборудования',
    date: 'Сегодня',
    desc: 'Минпромторг компенсирует до 50% затрат на лизинг и кредитование промышленным предприятиям.'
  },
  {
    id: 2,
    tag: 'Аналитика Альфа-Банка',
    title: 'Индекс настроений МСП в 4 квартале 2026',
    date: 'Вчера',
    desc: 'Оборотные кредиты остаются самым востребованным инструментом у компаний сферы ритейла и логистики.'
  }
];
export interface UserProfile {
  id: string;
  role: 'client' | 'bank';
  name: string;
  companyName?: string;
  inn?: string;
  avatarText: string;
}

export const SYNTHETIC_CLIENTS: UserProfile[] = [
  {
    id: 'client-1',
    role: 'client',
    name: 'Соколов Алексей Игоревич',
    companyName: 'ООО «ЛогистикПро»',
    inn: '7701234567',
    avatarText: 'АС',
  },
  {
    id: 'client-2',
    role: 'client',
    name: 'Балтина Марина Сергеевна',
    companyName: 'ООО «БалтТехПром»',
    inn: '7812987654',
    avatarText: 'МБ',
  },
  {
    id: 'client-3',
    role: 'client',
    name: 'Смирнов Андрей Васильевич',
    companyName: 'ИП Смирнов А.В.',
    inn: '5024112233',
    avatarText: 'АС',
  },
  {
    id: 'client-4',
    role: 'client',
    name: 'Векторов Дмитрий Олегович',
    companyName: 'ООО «Вектор-М»',
    inn: '7709887766',
    avatarText: 'ДВ',
  },
];
