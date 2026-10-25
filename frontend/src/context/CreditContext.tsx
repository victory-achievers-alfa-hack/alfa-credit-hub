import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from 'react';
import { useAuth } from './AutoContext';
import { api, allItems, ApiError, realtimeUrl } from '../services/api';
import { RealtimeClient, type RealtimeConnectionStatus } from '../services/realtime';
import { PageSkeleton } from '../components/PageSkeleton';
import type {
  BankDecisionInput,
  ClientNotification,
  CompanyProfile,
  CreateApplicationInput,
  CreditApplication,
  CreditProduct,
  RecommendationInput,
  RecommendationResponse,
} from '../types/credit';

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
  recommend: (input: RecommendationInput) => Promise<RecommendationResponse>;
  createApplication: (input: CreateApplicationInput) => Promise<CreditApplication>;
  decideApplication: (id: string, decision: BankDecisionInput) => Promise<ActionResult>;
  respondToInfoRequest: (id: string, input: AdditionalInfoInput) => Promise<ActionResult>;
  acceptOffer: (id: string, accepted: boolean) => Promise<ActionResult>;
  signApplication: (id: string) => Promise<ActionResult>;
  disburseApplication: (id: string) => Promise<ActionResult>;
  markNotificationRead: (id: string) => Promise<ActionResult>;
  markAllNotificationsRead: (companyId: string) => Promise<void>;
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
  const [serviceUnavailable, setServiceUnavailable] = useState(false);
  const [busy, setBusy] = useState(false);
  const [realtimeStatus, setRealtimeStatus] = useState<RealtimeConnectionStatus>('idle');
  const readyRef = useRef(false);
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
        readyRef.current = true;
        setReady(true);
      }
    } catch (requestError) {
      if (!controller.signal.aborted && request === refreshSequence.current && !readyRef.current) {
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
      const initialLoadPending = !readyRef.current;
      generation.current++;
      refreshController.current?.abort();
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
      if (initialLoadPending) void refresh();
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
    const markServiceUnavailable = () => setServiceUnavailable(true);
    const markServiceAvailable = () => setServiceUnavailable(false);
    document.addEventListener('visibilitychange', synchronizeVisibleTab);
    window.addEventListener('service-unavailable', markServiceUnavailable);
    window.addEventListener('service-available', markServiceAvailable);

    return () => {
      refreshController.current?.abort();
      realtime.disconnect();
      unsubscribeMessages();
      unsubscribeStatus();
      window.clearInterval(timer);
      document.removeEventListener('visibilitychange', synchronizeVisibleTab);
      window.removeEventListener('service-unavailable', markServiceUnavailable);
      window.removeEventListener('service-available', markServiceAvailable);
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

  const recommend = useCallback((input: RecommendationInput): Promise<RecommendationResponse> => (
    api<RecommendationResponse>('/recommendations', {
      method: 'POST',
      body: input,
    })
  ), []);

  if (!currentUser) return <>{children}</>;
  if (!ready && error) {
    return (
      <div className="page-shell">
        <div className="surface-card loading-error" role="alert">
          <strong>Не удалось загрузить данные</strong>
          <p>{error}</p>
          <button className="text-link" type="button" onClick={() => void refresh()}>Повторить</button>
        </div>
      </div>
    );
  }
  if (!ready) return <PageSkeleton />;

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
    }}>
      {(serviceUnavailable || realtimeStatus === 'reconnecting') && (
        <p className="realtime-notice realtime-notice--error" role="alert">
          Сервис временно недоступен. Пытаемся восстановить соединение.
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
