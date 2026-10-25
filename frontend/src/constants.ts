import type { CreditPurpose, UserProfile } from './types/credit';

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
    role: 'bank',
    name: 'Анна Белова',
    companyName: 'Кредитный департамент',
    avatarText: 'АБ',
  },
];

export const NEWS_ITEMS = [
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
