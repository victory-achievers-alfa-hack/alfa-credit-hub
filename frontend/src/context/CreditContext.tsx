import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from 'react';
import { useAuth } from './AutoContext';
import { api, allItems, ApiError, realtimeUrl } from '../services/api';
import { RealtimeClient, type RealtimeConnectionStatus } from '../services/realtime';
import type {
  BankDecisionInput,
  ClientNotification,
  CompanyProfile,
  CreateApplicationInput,
  CreditApplication,
  CreditProduct,
  Recommendation,
  RecommendationAssessment,
  RecommendationGroup,
  RecommendationInput,
} from '../types/credit';

const RECOMMENDATION_GROUPS: RecommendationGroup[] = [
  'requested',
  'other_terms',
  'reduced_amount',
  'requires_action',
  'unavailable',
];

type RecommendationOfferDto = {
  amount: number;
  termMonths: number;
  rate: number;
  monthlyPayment: number;
  interestAmount: number;
  coverage: number;
  eligible: boolean;
};

type RankedRecommendationDto = {
  product: CreditProduct;
  offer: RecommendationOfferDto;
  evaluation: {
    assessment: RecommendationAssessment;
    reasons: Array<{ code: string; message: string }>;
    recommendedAmount: number | null;
  };
  group: RecommendationGroup;
  rankingReason: string;
};

type RecommendationResponseDto = {
  evaluationId: string;
  rankingVersion: string;
  groups: Record<RecommendationGroup, RankedRecommendationDto[]>;
};

export interface AdditionalInfoInput {
  comment: string;
  documentIds: string[];
}

export interface ActionResult {
  success: boolean;
  error?: string;
  code?: string;
  fieldErrors?: Record<string, string>;
}

interface CreditContextValue {
  applications: CreditApplication[];
  notifications: ClientNotification[];
  products: CreditProduct[];
  realtimeStatus: RealtimeConnectionStatus;
  getCompany: (id?: string | null) => CompanyProfile | undefined;
  getProduct: (id: string) => CreditProduct | undefined;
  recommend: (input: RecommendationInput) => Promise<Recommendation[]>;
  createApplication: (input: CreateApplicationInput) => Promise<CreditApplication>;
  decideApplication: (id: string, decision: BankDecisionInput) => Promise<ActionResult>;
  respondToInfoRequest: (id: string, input: AdditionalInfoInput) => Promise<ActionResult>;
  acceptOffer: (id: string, accepted: boolean) => Promise<ActionResult>;
  signApplication: (id: string) => Promise<ActionResult>;
  disburseApplication: (id: string) => Promise<ActionResult>;
  markNotificationRead: (id: string) => Promise<ActionResult>;
  markAllNotificationsRead: (companyId: string) => Promise<void>;
  resetDemo: () => void;
}

const CreditContext = createContext<CreditContextValue | undefined>(undefined);

function errorResult(error: unknown): ActionResult {
  if (error instanceof ApiError) {
    return {
      success: false,
      error: error.message,
      code: error.code,
      fieldErrors: error.fieldErrors,
    };
  }
  return {
    success: false,
    error: error instanceof Error ? error.message : 'Не удалось выполнить действие',
  };
}

function sortApplications(applications: CreditApplication[]): CreditApplication[] {
  return applications.sort((first, second) =>
    second.updatedAt.localeCompare(first.updatedAt) || first.id.localeCompare(second.id));
}

export function CreditProvider({ children }: { children: ReactNode }) {
  const { currentUser } = useAuth();
  const [applications, setApplications] = useState<CreditApplication[]>([]);
  const [notifications, setNotifications] = useState<ClientNotification[]>([]);
  const [companies, setCompanies] = useState<CompanyProfile[]>([]);
  const [products, setProducts] = useState<CreditProduct[]>([]);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [realtimeStatus, setRealtimeStatus] = useState<RealtimeConnectionStatus>('idle');
  const refreshSequence = useRef(0);
  const refreshController = useRef<AbortController | null>(null);
  const mutating = useRef(false);
  const generation = useRef(0);

  const upsertApplication = useCallback((application: CreditApplication) => {
    setApplications((current) => sortApplications([
      application,
      ...current.filter((item) => item.id !== application.id),
    ]));
  }, []);

  const refresh = useCallback(async () => {
    if (!currentUser) return;
    refreshController.current?.abort();
    const controller = new AbortController();
    refreshController.current = controller;
    const request = ++refreshSequence.current;
    const version = generation.current;

    try {
      const bank = currentUser.role === 'bank';
      const [rows, catalogue, ownProfile, notices] = await Promise.all([
        allItems<{ id: string }>(bank ? '/bank/applications' : '/applications', controller.signal),
        api<CreditProduct[]>('/credit-products', { signal: controller.signal }),
        bank ? Promise.resolve<CompanyProfile | undefined>(undefined) : api<CompanyProfile>('/companies/me', { signal: controller.signal }),
        bank ? Promise.resolve<ClientNotification[]>([]) : allItems<ClientNotification>('/notifications', controller.signal),
      ]);
      const details: CreditApplication[] = [];
      const profiles: CompanyProfile[] = ownProfile ? [ownProfile] : [];

      for (let start = 0; start < rows.length; start += 8) {
        const batch = await Promise.all(rows.slice(start, start + 8).map(async (row) => {
          try {
            if (bank) {
              return await api<{ application: CreditApplication; company: CompanyProfile }>(
                `/bank/applications/${encodeURIComponent(row.id)}`,
                { signal: controller.signal },
              );
            }
            return {
              application: await api<CreditApplication>(
                `/applications/${encodeURIComponent(row.id)}`,
                { signal: controller.signal },
              ),
              company: undefined,
            };
          } catch (requestError) {
            if (requestError instanceof ApiError && requestError.status === 404) return undefined;
            throw requestError;
          }
        }));
        batch.forEach((detail) => {
          if (!detail) return;
          details.push(detail.application);
          if (detail.company) profiles.push(detail.company);
        });
      }

      if (!controller.signal.aborted && version === generation.current && request === refreshSequence.current) {
        const uniqueProfiles = [...new Map(profiles.map((profile) => [profile.id, profile])).values()];
        setApplications(sortApplications(details));
        setCompanies(uniqueProfiles);
        setProducts(catalogue);
        setNotifications(notices);
        setError('');
        setReady(true);
      }
    } catch (requestError) {
      if (!controller.signal.aborted && request === refreshSequence.current) {
        setError(requestError instanceof Error ? requestError.message : 'Не удалось загрузить данные');
      }
    }
  }, [currentUser]);

  useEffect(() => {
    if (!currentUser) return;
    // Initial loading synchronizes the provider with the authenticated API.
    // oxlint-disable-next-line react/set-state-in-effect
    void refresh();
    const realtime = new RealtimeClient(realtimeUrl());
    let connectedOnce = false;
    const unsubscribeMessages = realtime.subscribe((message) => {
      if (message.type === 'application.updated') {
        upsertApplication(message.payload.application);
      } else if (message.type === 'notification.created') {
        const notification = message.payload.notification;
        setNotifications((current) => [
          notification,
          ...current.filter((item) => item.id !== notification.id),
        ]);
      } else if (message.type === 'notification.read') {
        setNotifications((current) => current.map((notification) =>
          notification.id === message.payload.notificationId
            ? { ...notification, read: true }
            : notification));
      }
    });
    const unsubscribeStatus = realtime.subscribeStatus((status) => {
      setRealtimeStatus(status);
      if (status === 'connected') {
        if (connectedOnce) void refresh();
        connectedOnce = true;
      }
    });
    realtime.connect();

    const timer = window.setInterval(() => {
      if (!document.hidden) void refresh();
    }, 15_000);
    const synchronizeVisibleTab = () => {
      if (!document.hidden) void refresh();
    };
    document.addEventListener('visibilitychange', synchronizeVisibleTab);

    return () => {
      refreshController.current?.abort();
      realtime.disconnect();
      unsubscribeMessages();
      unsubscribeStatus();
      window.clearInterval(timer);
      document.removeEventListener('visibilitychange', synchronizeVisibleTab);
    };
  }, [currentUser, refresh, upsertApplication]);

  const action = async (path: string, body?: unknown): Promise<ActionResult> => {
    if (mutating.current) return { success: false, error: 'Дождитесь завершения текущего действия' };
    mutating.current = true;
    setBusy(true);
    generation.current++;
    try {
      const result = await api<CreditApplication>(path, { method: 'POST', body });
      upsertApplication(result);
      setError('');
      return { success: true };
    } catch (actionError) {
      const result = errorResult(actionError);
      setError(result.error ?? 'Не удалось выполнить действие');
      return result;
    } finally {
      mutating.current = false;
      setBusy(false);
    }
  };

  const recommend = useCallback(async (input: RecommendationInput): Promise<Recommendation[]> => {
    const response = await api<RecommendationResponseDto>('/recommendations', {
      method: 'POST',
      body: input,
    });
    return RECOMMENDATION_GROUPS.flatMap((group) => response.groups[group].map((item) => {
      const explanation = item.evaluation.reasons.map((reason) => reason.message).join(' ');
      return {
        product: item.product,
        ...item.offer,
        evaluationId: response.evaluationId,
        rankingVersion: response.rankingVersion,
        group: item.group,
        assessment: item.evaluation.assessment,
        reason: explanation,
        rankingReason: item.rankingReason,
        warning: item.offer.eligible ? undefined : explanation,
        recommendedAmount: item.evaluation.recommendedAmount ?? undefined,
      };
    }));
  }, []);

  if (!currentUser) return <>{children}</>;
  if (!ready) {
    return (
      <div className="page-shell" role="status">
        {error || 'Загружаем данные…'}
        {error && <button type="button" onClick={() => void refresh()}>Повторить</button>}
      </div>
    );
  }

  return (
    <CreditContext.Provider value={{
      applications,
      notifications,
      products,
      realtimeStatus,
      getCompany: (id) => companies.find((company) => company.id === id),
      getProduct: (id) => products.find((product) => product.id === id),
      recommend,
      createApplication: async ({ companyId: _companyId, preference: _preference, ...input }) => {
        const result = await api<CreditApplication>('/applications', { method: 'POST', body: input });
        generation.current++;
        upsertApplication(result);
        return result;
      },
      decideApplication: (id, decision) => action(`/bank/applications/${encodeURIComponent(id)}/decision`, decision),
      respondToInfoRequest: (id, input) => action(`/applications/${encodeURIComponent(id)}/additional-info`, input),
      acceptOffer: (id, accepted) => action(`/applications/${encodeURIComponent(id)}/accept`, { accepted }),
      signApplication: (id) => action(`/applications/${encodeURIComponent(id)}/sign`),
      disburseApplication: (id) => action(`/applications/${encodeURIComponent(id)}/disburse`),
      markNotificationRead: async (id) => {
        try {
          const updated = await api<ClientNotification>(`/notifications/${encodeURIComponent(id)}/read`, { method: 'POST' });
          setNotifications((current) => current.map((notification) =>
            notification.id === updated.id ? updated : notification));
          setError('');
          return { success: true };
        } catch (actionError) {
          const result = errorResult(actionError);
          setError(result.error ?? 'Не удалось прочитать уведомление');
          return result;
        }
      },
      markAllNotificationsRead: async (companyId) => {
        for (const notification of notifications.filter((item) => !item.read && item.companyId === companyId)) {
          const successful = await api<ClientNotification>(
            `/notifications/${encodeURIComponent(notification.id)}/read`,
            { method: 'POST' },
          ).then((updated) => {
            setNotifications((current) => current.map((item) => item.id === updated.id ? updated : item));
            return true;
          }).catch((actionError) => {
            const result = errorResult(actionError);
            setError(result.error ?? 'Не удалось прочитать уведомления');
            return false;
          });
          if (!successful) break;
        }
      },
      resetDemo: () => { void refresh(); },
    }}>
      {error && <p className="page-shell" role="alert">{error}</p>}
      {realtimeStatus === 'reconnecting' && (
        <p className="realtime-notice" role="status">
          Соединение с обновлениями восстанавливается. Данные временно синхронизируются опросом сервера.
        </p>
      )}
      <fieldset disabled={busy} style={{ border: 0, padding: 0, margin: 0, minWidth: 0 }}>
        {children}
      </fieldset>
    </CreditContext.Provider>
  );
}

// oxlint-disable-next-line react/only-export-components
export function useCredit(): CreditContextValue {
  const value = useContext(CreditContext);
  if (!value) throw new Error('CreditProvider is missing');
  return value;
}
