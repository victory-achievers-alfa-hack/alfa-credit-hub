import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import {
  buildChecks,
  buildScoring,
  calculateCoverage,
  calculateMonthlyPayment,
  createSeedApplications,
  createSeedNotifications,
  getCompany,
  getProduct,
  getRecommendations,
} from '../data/mockData';
import { realtimeClient } from '../services/realtime';
import type {
  ApplicationEvent,
  BankDecisionInput,
  ClientNotification,
  CreateApplicationInput,
  CreditApplication,
  NotificationTone,
  Recommendation,
  RecommendationInput,
} from '../types/credit';

interface CreditContextValue {
  applications: CreditApplication[];
  notifications: ClientNotification[];
  recommend: (input: RecommendationInput) => Recommendation[];
  createApplication: (input: CreateApplicationInput) => CreditApplication;
  decideApplication: (applicationId: string, decision: BankDecisionInput) => void;
  respondToInfoRequest: (applicationId: string) => void;
  acceptOffer: (applicationId: string, accepted: boolean) => void;
  signApplication: (applicationId: string) => void;
  disburseApplication: (applicationId: string) => void;
  markNotificationRead: (notificationId: string) => void;
  markAllNotificationsRead: (companyId: string) => void;
  resetDemo: () => void;
}

const APPLICATIONS_STORAGE_KEY = 'alfa_stream_applications_v2';
const NOTIFICATIONS_STORAGE_KEY = 'alfa_stream_notifications_v1';
const CreditContext = createContext<CreditContextValue | undefined>(undefined);

function readApplications(): CreditApplication[] {
  const saved = localStorage.getItem(APPLICATIONS_STORAGE_KEY);
  if (!saved) return createSeedApplications();

  try {
    return JSON.parse(saved) as CreditApplication[];
  } catch {
    return createSeedApplications();
  }
}

function readNotifications(): ClientNotification[] {
  const saved = localStorage.getItem(NOTIFICATIONS_STORAGE_KEY);
  if (!saved) return createSeedNotifications();

  try {
    return JSON.parse(saved) as ClientNotification[];
  } catch {
    return createSeedNotifications();
  }
}

function createClientNotification(
  companyId: string,
  applicationId: string,
  title: string,
  message: string,
  tone: NotificationTone,
): ClientNotification {
  return {
    id: `NOTIFICATION-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    companyId,
    applicationId,
    title,
    message,
    tone,
    createdAt: new Date().toISOString(),
    read: false,
  };
}

function createEvent(
  status: CreditApplication['status'],
  title: string,
  description: string,
  actor: string,
): ApplicationEvent {
  return {
    id: `EV-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    status,
    title,
    description,
    actor,
    createdAt: new Date().toISOString(),
  };
}

function upsertApplication(current: CreditApplication[], application: CreditApplication): CreditApplication[] {
  const exists = current.some((candidate) => candidate.id === application.id);
  return exists
    ? current.map((candidate) => candidate.id === application.id ? application : candidate)
    : [application, ...current];
}

function upsertNotification(current: ClientNotification[], notification: ClientNotification): ClientNotification[] {
  const exists = current.some((candidate) => candidate.id === notification.id);
  return exists
    ? current.map((candidate) => candidate.id === notification.id ? notification : candidate)
    : [notification, ...current];
}

function publishApplication(application: CreditApplication): void {
  realtimeClient.publish({ type: 'application.updated', payload: { application } });
}

function publishNotification(notification: ClientNotification): void {
  realtimeClient.publish({ type: 'notification.created', payload: { notification } });
}

export function CreditProvider({ children }: { children: ReactNode }) {
  const [applications, setApplications] = useState<CreditApplication[]>(readApplications);
  const [notifications, setNotifications] = useState<ClientNotification[]>(readNotifications);

  useEffect(() => {
    localStorage.setItem(APPLICATIONS_STORAGE_KEY, JSON.stringify(applications));
  }, [applications]);

  useEffect(() => {
    localStorage.setItem(NOTIFICATIONS_STORAGE_KEY, JSON.stringify(notifications));
  }, [notifications]);

  useEffect(() => {
    const handleStorage = (event: StorageEvent) => {
      if (!event.newValue) return;

      try {
        if (event.key === APPLICATIONS_STORAGE_KEY) {
          setApplications(JSON.parse(event.newValue) as CreditApplication[]);
        }
        if (event.key === NOTIFICATIONS_STORAGE_KEY) {
          setNotifications(JSON.parse(event.newValue) as ClientNotification[]);
        }
      } catch {
        // Ignore malformed data written by another tab and keep the current state.
      }
    };

    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  useEffect(() => {
    const unsubscribe = realtimeClient.subscribe((message) => {
      if (message.type === 'application.updated') {
        setApplications((current) => upsertApplication(current, message.payload.application));
      }
      if (message.type === 'notification.created') {
        setNotifications((current) => upsertNotification(current, message.payload.notification));
      }
      if (message.type === 'notification.read') {
        setNotifications((current) => current.map((notification) =>
          notification.id === message.payload.notificationId ? { ...notification, read: true } : notification));
      }
    });

    realtimeClient.connect();
    return unsubscribe;
  }, []);

  const value = useMemo<CreditContextValue>(() => ({
    applications,
    notifications,
    recommend: ({ companyId, purpose, amount, termMonths }) => {
      const company = getCompany(companyId);
      return company ? getRecommendations(company, purpose, amount, termMonths) : [];
    },
    createApplication: ({ companyId, productId, purpose, amount, termMonths }) => {
      const company = getCompany(companyId);
      const product = getProduct(productId);
      if (!company || !product) throw new Error('Не удалось найти компанию или кредитный продукт');

      const monthlyPayment = calculateMonthlyPayment(amount, product.rate, termMonths);
      const coverage = calculateCoverage(company, monthlyPayment);
      const now = new Date().toISOString();
      const application: CreditApplication = {
        id: `APP-${new Date().getFullYear()}-${String(Date.now()).slice(-6)}`,
        companyId,
        productId,
        productName: product.name,
        purpose,
        requestedAmount: amount,
        requestedTermMonths: termMonths,
        requestedRate: product.rate,
        requestedMonthlyPayment: monthlyPayment,
        coverage,
        status: 'review',
        scoring: buildScoring(company),
        checks: buildChecks(company, coverage),
        createdAt: now,
        updatedAt: now,
        events: [createEvent('review', 'Заявка отправлена', 'Данные переданы сотруднику банка.', company.name)],
      };

      setApplications((current) => [application, ...current]);
      publishApplication(application);
      return application;
    },
    decideApplication: (applicationId, decision) => {
      const application = applications.find((candidate) => candidate.id === applicationId);
      if (!application || !['review', 'need_info'].includes(application.status)) return;

      const now = new Date().toISOString();
      let nextApplication: CreditApplication;
      let notification: ClientNotification;

      if (decision.kind === 'need_info') {
        nextApplication = {
          ...application,
          status: 'need_info',
          infoRequest: decision.comment,
          bankComment: decision.comment,
          updatedAt: now,
          events: [...application.events, createEvent('need_info', 'Банк запросил сведения', decision.comment, 'Сотрудник банка')],
        };
        notification = createClientNotification(
          application.companyId,
          application.id,
          'Банк запросил сведения',
          decision.comment,
          'warning',
        );
      } else if (decision.kind === 'reject') {
        nextApplication = {
          ...application,
          status: 'rejected',
          bankComment: decision.comment,
          updatedAt: now,
          events: [...application.events, createEvent('rejected', 'Банк отказал в заявке', decision.comment, 'Сотрудник банка')],
        };
        notification = createClientNotification(
          application.companyId,
          application.id,
          'По заявке принято отрицательное решение',
          decision.comment,
          'negative',
        );
      } else {
        const amount = decision.kind === 'approve' ? application.requestedAmount : decision.amount ?? application.requestedAmount;
        const termMonths = decision.kind === 'approve' ? application.requestedTermMonths : decision.termMonths ?? application.requestedTermMonths;
        const rate = decision.kind === 'approve' ? application.requestedRate : decision.rate ?? application.requestedRate;
        const title = decision.kind === 'approve' ? 'Банк одобрил заявку' : 'Банк предложил другие условия';
        const message = decision.comment || 'Предложение готово.';

        nextApplication = {
          ...application,
          status: 'offer',
          offer: {
            id: `OFF-${Date.now()}`,
            amount,
            termMonths,
            rate,
            monthlyPayment: calculateMonthlyPayment(amount, rate, termMonths),
            reason: message,
            createdAt: now,
          },
          bankComment: decision.comment,
          infoRequest: undefined,
          updatedAt: now,
          events: [...application.events, createEvent('offer', title, message, 'Сотрудник банка')],
        };
        notification = createClientNotification(
          application.companyId,
          application.id,
          decision.kind === 'approve' ? 'Заявка одобрена' : 'Банк предложил новые условия',
          `${message} Доступная сумма: ${amount.toLocaleString('ru-RU')} ₽.`,
          decision.kind === 'approve' ? 'positive' : 'warning',
        );
      }

      setApplications((current) => upsertApplication(current, nextApplication));
      setNotifications((current) => upsertNotification(current, notification));
      publishApplication(nextApplication);
      publishNotification(notification);
    },
    respondToInfoRequest: (applicationId) => {
      const application = applications.find((candidate) => candidate.id === applicationId && candidate.status === 'need_info');
      if (!application) return;

      const nextApplication: CreditApplication = {
        ...application,
        status: 'review',
        infoRequest: undefined,
        updatedAt: new Date().toISOString(),
        events: [...application.events, createEvent('review', 'Сведения подтверждены', 'Заявка возвращена на рассмотрение.', 'Клиент')],
      };
      setApplications((current) => upsertApplication(current, nextApplication));
      publishApplication(nextApplication);
    },
    acceptOffer: (applicationId, accepted) => {
      const application = applications.find((candidate) => candidate.id === applicationId && candidate.status === 'offer');
      if (!application) return;

      const nextApplication: CreditApplication = {
        ...application,
        status: accepted ? 'sign' : 'rejected',
        updatedAt: new Date().toISOString(),
        events: [
          ...application.events,
          createEvent(
            accepted ? 'sign' : 'rejected',
            accepted ? 'Предложение принято' : 'Предложение отклонено',
            accepted ? 'Можно перейти к демоподписанию договора.' : 'Клиент отказался от условий банка.',
            'Клиент',
          ),
        ],
      };
      setApplications((current) => upsertApplication(current, nextApplication));
      publishApplication(nextApplication);
    },
    signApplication: (applicationId) => {
      const application = applications.find((candidate) => candidate.id === applicationId && candidate.status === 'sign');
      if (!application) return;

      const nextApplication: CreditApplication = {
        ...application,
        status: 'ready',
        updatedAt: new Date().toISOString(),
        events: [...application.events, createEvent('ready', 'Договор подписан', 'Демодоговор подтверждён кодом.', 'Клиент')],
      };
      setApplications((current) => upsertApplication(current, nextApplication));
      publishApplication(nextApplication);
    },
    disburseApplication: (applicationId) => {
      const application = applications.find((candidate) => candidate.id === applicationId && candidate.status === 'ready');
      if (!application) return;

      const nextApplication: CreditApplication = {
        ...application,
        status: 'disbursed',
        updatedAt: new Date().toISOString(),
        events: [...application.events, createEvent('disbursed', 'Кредит выдан', 'Моделируемая выдача успешно завершена.', 'Система')],
      };
      setApplications((current) => upsertApplication(current, nextApplication));
      publishApplication(nextApplication);
    },
    markNotificationRead: (notificationId) => {
      setNotifications((current) => current.map((notification) =>
        notification.id === notificationId ? { ...notification, read: true } : notification));
      realtimeClient.publish({ type: 'notification.read', payload: { notificationId } });
    },
    markAllNotificationsRead: (companyId) => {
      const unreadNotifications = notifications.filter((notification) =>
        notification.companyId === companyId && !notification.read);
      setNotifications((current) => current.map((notification) =>
        notification.companyId === companyId ? { ...notification, read: true } : notification));
      unreadNotifications.forEach((notification) => {
        realtimeClient.publish({ type: 'notification.read', payload: { notificationId: notification.id } });
      });
    },
    resetDemo: () => {
      setApplications(createSeedApplications());
      setNotifications(createSeedNotifications());
    },
  }), [applications, notifications]);

  return <CreditContext.Provider value={value}>{children}</CreditContext.Provider>;
}

// oxlint-disable-next-line react/only-export-components -- Provider and hook intentionally share one context module.
export function useCredit(): CreditContextValue {
  const context = useContext(CreditContext);
  if (!context) throw new Error('useCredit must be used within CreditProvider');
  return context;
}
